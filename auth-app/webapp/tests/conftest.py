import pytest
import asyncio

from httpx import AsyncClient
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession

from boostrap import bootstrap_di
from database import DatabaseService
from kink import di

bootstrap_di()
import main


@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="module")
async def db_service() -> DatabaseService:
    di.factories[orm.sessionmaker] = lambda di: orm.sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=di[AsyncEngine],
        expire_on_commit=False,
        class_=AsyncSession,
    )
    di.factories[DatabaseService] = lambda di: DatabaseService(
        di[AsyncEngine], di[orm.sessionmaker], "test"
    )
    await di[DatabaseService].create_database()
    return di[DatabaseService]


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=main.app, base_url="http://localhost:8000") as client:
        yield client
