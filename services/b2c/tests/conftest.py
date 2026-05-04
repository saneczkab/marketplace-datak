import os
import subprocess
from collections.abc import AsyncGenerator, AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
	AsyncEngine,
	AsyncSession,
	async_sessionmaker,
	create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from core import db as core_db
from main import app as fastapi_app


@pytest.fixture(scope="session")
async def test_engine() -> AsyncIterator[AsyncEngine]:
	"""
	Init test database and run migrations.
	"""
	with PostgresContainer("postgres:15") as pg:
		sync_url = pg.get_connection_url()
		async_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
		env = os.environ.copy()
		env["DATABASE_URL"] = async_url

		subprocess.run(
			["uv", "run", "alembic", "-c", "database/alembic.ini", "upgrade", "head"],
			check=True,
			env=env,
		)  # noqa: S607

		engine = create_async_engine(async_url, echo=False)
		try:
			yield engine
		finally:
			await engine.dispose()


@pytest.fixture()
def session_factory(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
	"""
	Create session for test database.
	"""
	return async_sessionmaker(
		bind=test_engine, expire_on_commit=False, class_=AsyncSession
	)


@pytest.fixture()
async def db_session(
	session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
	"""
	Create session for test database and truncate tables.
	"""
	async with session_factory() as session:
		try:
			yield session
		finally:
			await session.execute(text("TRUNCATE TABLE catalog.categories CASCADE"))
			await session.commit()


@pytest.fixture()
def app(session_factory: async_sessionmaker[AsyncSession]) -> FastAPI:
	"""
	Create FastAPI app with override get_db dependency.
	"""

	async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
		async with session_factory() as session:
			yield session

	fastapi_app.dependency_overrides[core_db.get_db] = override_get_db
	return fastapi_app


@pytest.fixture()
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
	"""
	Create client for test database.
	"""
	async with AsyncClient(
		transport=ASGITransport(app=app), base_url="http://test"
	) as client:
		yield client
