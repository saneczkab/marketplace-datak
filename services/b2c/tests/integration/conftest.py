import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.base import Category


@pytest.fixture()
def uuids() -> dict[str, uuid.UUID]:
	"""
	UUIDs for test data.
	"""
	return {
		"root": uuid.uuid4(),
		"child": uuid.uuid4(),
		"grandchild": uuid.uuid4(),
		"orphan": uuid.uuid4(),
		"missing_parent": uuid.uuid4(),
	}


@pytest.fixture()
async def categories_tree(
	db_session: AsyncSession, uuids: dict[str, uuid.UUID]
) -> dict[str, uuid.UUID]:
	"""
	Create categories tree test data.
	"""
	db_session.add_all(
		[
			Category(
				id=uuids["root"], parent_id=None, name="Электроника", slug="electronics"
			),
			Category(
				id=uuids["child"],
				parent_id=uuids["root"],
				name="Смартфоны",
				slug="smartphones",
			),
			Category(
				id=uuids["grandchild"],
				parent_id=uuids["child"],
				name="Android",
				slug="android",
			),
		]
	)
	await db_session.commit()
	return uuids


@pytest.fixture()
async def orphan_category(
	db_session: AsyncSession, uuids: dict[str, uuid.UUID]
) -> dict[str, uuid.UUID]:
	"""
	Create orphan category test data.
	Sets session replication role to replica to avoid foreign key constraints errors. Needs for orphan category.
	"""
	await db_session.execute(text("SET session_replication_role = replica"))
	db_session.add(
		Category(
			id=uuids["orphan"],
			parent_id=uuids["missing_parent"],
			name="Orphan",
			slug="orphan",
		)
	)
	await db_session.commit()
	await db_session.execute(text("SET session_replication_role = DEFAULT"))
	await db_session.commit()
	return uuids
