import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.base import Product, ProductStatusEnum
from database.models.outbox import OutboxEvent
from tests.integration.conftest import (
	MODERATION_SERVICE_KEY_HEADERS,
	ModerationEventData,
	auth_headers,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _occurred_at() -> str:
	return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _moderated_body(
	product_id: uuid.UUID, idempotency_key: uuid.UUID | None = None
) -> dict:
	return {
		"idempotency_key": str(idempotency_key or uuid.uuid4()),
		"product_id": str(product_id),
		"event_type": "MODERATED",
		"occurred_at": _occurred_at(),
	}


def _blocked_body(
	product_id: uuid.UUID,
	*,
	hard_block: bool = False,
	idempotency_key: uuid.UUID | None = None,
	field_reports: list[dict] | None = None,
) -> dict:
	return {
		"idempotency_key": str(idempotency_key or uuid.uuid4()),
		"product_id": str(product_id),
		"event_type": "BLOCKED",
		"blocking_reason_id": str(uuid.uuid4()),
		"moderator_comment": "Несоответствие описания и фотографий",
		"hard_block": hard_block,
		"field_reports": field_reports
		or [
			{
				"field_name": "description",
				"comment": "Текст описания скопирован с другого товара",
			}
		],
		"occurred_at": _occurred_at(),
	}


async def _post_moderation_event(
	client: AsyncClient,
	body: dict,
	headers: dict | None = None,
) -> int:
	response = await client.post(
		"/api/v1/moderation/events",
		headers=headers or MODERATION_SERVICE_KEY_HEADERS,
		json=body,
	)
	return response.status_code


async def _get_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
	result = await db.execute(
		select(Product)
		.where(Product.id == product_id)
		.execution_options(populate_existing=True)
	)
	return result.scalar_one()


async def _product_blocked_outbox_events(
	db: AsyncSession, product_id: uuid.UUID
) -> list[OutboxEvent]:
	result = await db.execute(
		select(OutboxEvent).where(OutboxEvent.event_type == "PRODUCT_BLOCKED")
	)
	return [
		event
		for event in result.scalars().all()
		if event.payload.get("payload", {}).get("product_id") == str(product_id)
	]


async def test_moderated_event_clears_blocking_data(
	client: AsyncClient,
	moderation_event_data: ModerationEventData,
	db_session: AsyncSession,
) -> None:
	product = moderation_event_data.blocked_product
	block_response = await _post_moderation_event(
		client,
		_blocked_body(
			product.id,
			field_reports=[
				{
					"field_name": "description",
					"comment": "Старое замечание",
				}
			],
		),
	)
	assert block_response == 204

	moderated_response = await _post_moderation_event(
		client, _moderated_body(product.id)
	)
	assert moderated_response == 204

	updated = await _get_product(db_session, product.id)
	assert updated.status == ProductStatusEnum.MODERATED
	assert updated.blocked_reason_id is None
	assert updated.blocking_reason_title is None
	assert updated.moderator_comment == ""
	assert updated.field_reports == []


async def test_blocked_soft_saves_field_reports(
	client: AsyncClient,
	moderation_event_data: ModerationEventData,
	db_session: AsyncSession,
) -> None:
	product = moderation_event_data.product
	sku = moderation_event_data.sku
	field_reports = [
		{
			"field_name": "description",
			"comment": "Текст описания скопирован с другого товара",
		},
		{
			"field_name": "sku_image",
			"sku_id": str(sku.id),
			"comment": "Фото SKU не соответствует указанному цвету",
		},
	]

	response = await _post_moderation_event(
		client,
		_blocked_body(product.id, hard_block=False, field_reports=field_reports),
	)
	assert response == 204

	updated = await _get_product(db_session, product.id)
	assert updated.status == ProductStatusEnum.BLOCKED
	assert updated.blocked_reason_id is not None
	assert updated.moderator_comment == "Несоответствие описания и фотографий"
	assert len(updated.field_reports) == 2
	assert updated.field_reports[0]["field_name"] == "description"
	assert updated.field_reports[1]["sku_id"] == str(sku.id)

	outbox_events = await _product_blocked_outbox_events(db_session, product.id)
	assert len(outbox_events) == 1
	assert outbox_events[0].payload["payload"]["sku_ids"] == [str(sku.id)]


async def test_blocked_hard_sets_terminal_status(
	client: AsyncClient,
	moderation_event_data: ModerationEventData,
	db_session: AsyncSession,
) -> None:
	product = moderation_event_data.product

	response = await _post_moderation_event(
		client, _blocked_body(product.id, hard_block=True)
	)
	assert response == 204

	updated = await _get_product(db_session, product.id)
	assert updated.status == ProductStatusEnum.HARD_BLOCKED
	assert updated.blocked_reason_id is not None

	outbox_events = await _product_blocked_outbox_events(db_session, product.id)
	assert len(outbox_events) == 1


async def test_hard_blocked_product_rejects_seller_edits(
	client: AsyncClient,
	moderation_event_data: ModerationEventData,
	db_session: AsyncSession,
) -> None:
	product = moderation_event_data.product
	headers = await auth_headers(moderation_event_data.seller.id, db_session)

	hard_block_response = await _post_moderation_event(
		client, _blocked_body(product.id, hard_block=True)
	)
	assert hard_block_response == 204

	product_response = await client.patch(
		f"/api/v1/products/{product.id}",
		headers=headers,
		json={"title": "Новое название"},
	)
	assert product_response.status_code == 403
	assert product_response.json()["code"] == "FORBIDDEN"

	sku_response = await client.patch(
		f"/api/v1/skus/{moderation_event_data.sku.id}",
		headers=headers,
		json={"name": "Новый SKU"},
	)
	assert sku_response.status_code == 403
	assert sku_response.json()["code"] == "FORBIDDEN"


async def test_duplicate_event_same_idempotency_key_no_side_effects(
	client: AsyncClient,
	moderation_event_data: ModerationEventData,
	db_session: AsyncSession,
) -> None:
	product = moderation_event_data.product
	idempotency_key = uuid.uuid4()
	body = _blocked_body(product.id, idempotency_key=idempotency_key)

	first = await _post_moderation_event(client, body)
	assert first == 204

	after_first = await _get_product(db_session, product.id)
	first_outbox = await _product_blocked_outbox_events(db_session, product.id)

	second = await _post_moderation_event(client, body)
	assert second == 204

	after_second = await _get_product(db_session, product.id)
	second_outbox = await _product_blocked_outbox_events(db_session, product.id)

	assert after_second.status == after_first.status
	assert after_second.blocked_reason_id == after_first.blocked_reason_id
	assert after_second.field_reports == after_first.field_reports
	assert len(second_outbox) == len(first_outbox) == 1


async def test_missing_service_key_returns_401(
	client: AsyncClient,
	moderation_event_data: ModerationEventData,
) -> None:
	response = await client.post(
		"/api/v1/moderation/events",
		json=_moderated_body(moderation_event_data.product.id),
	)
	assert response.status_code == 401
	assert response.json()["code"] == "UNAUTHORIZED"
