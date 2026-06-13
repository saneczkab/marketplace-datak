import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import crud.session as session_crud
from core.security import create_access_token
from crud import catalog as catalog_crud
from database.models.blocking_reason import BlockingReason
from database.models.identity.moderator import Moderator, Session
from database.models.tickets.ticket import Ticket, TicketStatus
from schemas.catalog_event import CategoryPayload, ProductUpdatePayload, SkuPayload
from tests.factories.blocking_reason import BlockingReasonFactory
from tests.factories.moderator import ModeratorFactory
from tests.factories.ticket import TicketFactory

B2B_SERVICE_KEY_HEADERS = {"X-Service-Key": "test-b2b-service-key"}


@dataclass(frozen=True, slots=True)
class TicketFixtureData:
	product_id: uuid.UUID
	seller_id: uuid.UUID
	moderator_id: uuid.UUID


def sample_product_snapshot(
	product_id: uuid.UUID,
	seller_id: uuid.UUID,
	title: str = "Test product",
	active_quantity: int = 5,
) -> dict:
	sku_id = uuid.uuid4()
	category_id = uuid.uuid4()
	return {
		"id": str(product_id),
		"seller_id": str(seller_id),
		"category_id": str(category_id),
		"category": {"id": str(category_id), "name": "Test category"},
		"title": title,
		"description": "Test description",
		"slug": "test-product",
		"status": "ON_MODERATION",
		"deleted": False,
		"images": [],
		"characteristics": [],
		"skus": [
			{
				"id": str(sku_id),
				"product_id": str(product_id),
				"name": "Default SKU",
				"price": 100000,
				"discount": 0,
				"active_quantity": active_quantity,
				"article": None,
				"images": [],
				"characteristics": [],
			}
		],
		"blocked": False,
		"blocking_reason": None,
		"field_reports": [],
	}


def product_created_body(
	product_id: uuid.UUID,
	seller_id: uuid.UUID,
	idempotency_key: uuid.UUID | None = None,
	json_after: dict | None = None,
) -> dict:
	snapshot = json_after or sample_product_snapshot(product_id, seller_id)
	return {
		"event_type": "PRODUCT_CREATED",
		"idempotency_key": str(idempotency_key or uuid.uuid4()),
		"occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
		"payload": {
			"product_id": str(product_id),
			"seller_id": str(seller_id),
			"category_id": snapshot.get("category_id"),
			"json_after": snapshot,
		},
	}


def product_edited_body(
	product_id: uuid.UUID,
	seller_id: uuid.UUID,
	idempotency_key: uuid.UUID | None = None,
	json_before: dict | None = None,
	json_after: dict | None = None,
) -> dict:
	before = json_before or sample_product_snapshot(
		product_id, seller_id, title="Before"
	)
	after = json_after or sample_product_snapshot(product_id, seller_id, title="After")
	return {
		"event_type": "PRODUCT_EDITED",
		"idempotency_key": str(idempotency_key or uuid.uuid4()),
		"occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
		"payload": {
			"product_id": str(product_id),
			"seller_id": str(seller_id),
			"category_id": after.get("category_id"),
			"json_before": before,
			"json_after": after,
		},
	}


def product_deleted_body(
	product_id: uuid.UUID,
	idempotency_key: uuid.UUID | None = None,
) -> dict:
	return {
		"event_type": "PRODUCT_DELETED",
		"idempotency_key": str(idempotency_key or uuid.uuid4()),
		"occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
		"payload": {"product_id": str(product_id)},
	}


async def seed_catalog_replica(
	db_session: AsyncSession,
	product_id: uuid.UUID,
	seller_id: uuid.UUID,
	title: str = "Test product",
	active_quantity: int = 5,
) -> ProductUpdatePayload:
	category_id = uuid.uuid4()
	sku_id = uuid.uuid4()
	payload = ProductUpdatePayload(
		id=product_id,
		seller_id=seller_id,
		category_id=category_id,
		category=CategoryPayload(id=category_id, name="Test category"),
		title=title,
		slug=f"product-{product_id}",
		description="Test description",
		status="ON_MODERATION",
		deleted=False,
		images=[],
		characteristics=[],
		skus=[
			SkuPayload(
				id=sku_id,
				product_id=product_id,
				name="Default SKU",
				price=100_000,
				discount=0,
				active_quantity=active_quantity,
			)
		],
	)
	await catalog_crud.upsert_product(db_session, payload)
	await db_session.commit()
	return payload


async def auth_headers(
	moderator_id: uuid.UUID, db_session: AsyncSession
) -> dict[str, str]:
	token = create_access_token(moderator_id)
	if not await session_crud.check_active_session(token, db_session):
		session = Session(
			user_id=moderator_id,
			access_token=token,
			refresh_token=secrets.token_hex(32),
			expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
		)
		db_session.add(session)
		await db_session.commit()
	return {"Authorization": f"Bearer {token}"}


async def persist_moderator(db_session: AsyncSession, **kwargs: object) -> Moderator:
	moderator = ModeratorFactory.build(**kwargs)
	db_session.add(moderator)
	await db_session.commit()
	await db_session.refresh(moderator)
	return moderator


async def persist_ticket(db_session: AsyncSession, **kwargs: object) -> Ticket:
	ticket = TicketFactory.build(**kwargs)
	db_session.add(ticket)
	await db_session.commit()
	await db_session.refresh(ticket)
	return ticket


async def persist_blocking_reason(
	db_session: AsyncSession, **kwargs: object
) -> BlockingReason:
	reason = BlockingReasonFactory.build(**kwargs)
	db_session.add(reason)
	await db_session.commit()
	await db_session.refresh(reason)
	return reason


@pytest.fixture
async def hard_block_reason(db_session: AsyncSession) -> BlockingReason:
	return await persist_blocking_reason(db_session, hard=True)


@pytest.fixture
async def ticket_fixture_data() -> TicketFixtureData:
	product_id = uuid.uuid4()
	seller_id = uuid.uuid4()
	moderator_id = uuid.uuid4()
	return TicketFixtureData(
		product_id=product_id,
		seller_id=seller_id,
		moderator_id=moderator_id,
	)


@pytest.fixture
async def moderator(
	db_session: AsyncSession, ticket_fixture_data: TicketFixtureData
) -> Moderator:
	return await persist_moderator(
		db_session,
		id=ticket_fixture_data.moderator_id,
	)


@pytest.fixture
async def other_moderator(db_session: AsyncSession) -> Moderator:
	return await persist_moderator(db_session)


@pytest.fixture
async def in_review_ticket(
	db_session: AsyncSession,
	ticket_fixture_data: TicketFixtureData,
	moderator: Moderator,
) -> Ticket:
	_ = moderator.id
	await seed_catalog_replica(
		db_session,
		ticket_fixture_data.product_id,
		ticket_fixture_data.seller_id,
	)
	return await persist_ticket(
		db_session,
		product_id=ticket_fixture_data.product_id,
		seller_id=ticket_fixture_data.seller_id,
		status=TicketStatus.IN_REVIEW,
		assigned_moderator_id=ticket_fixture_data.moderator_id,
		json_after=sample_product_snapshot(
			ticket_fixture_data.product_id,
			ticket_fixture_data.seller_id,
			title="In review snapshot",
		),
	)


@pytest.fixture
async def pending_ticket(
	db_session: AsyncSession,
	ticket_fixture_data: TicketFixtureData,
) -> Ticket:
	await seed_catalog_replica(
		db_session,
		ticket_fixture_data.product_id,
		ticket_fixture_data.seller_id,
	)
	return await persist_ticket(
		db_session,
		product_id=ticket_fixture_data.product_id,
		seller_id=ticket_fixture_data.seller_id,
		status=TicketStatus.PENDING,
		json_after=sample_product_snapshot(
			ticket_fixture_data.product_id,
			ticket_fixture_data.seller_id,
		),
	)
