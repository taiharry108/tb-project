import pytest
import asyncio

from dependency_injector import providers
from dependency_injector.wiring import inject
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import create_async_engine

from container import Container
import main


@pytest.fixture(scope="module")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    c = Container()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="module")
@inject
async def database():
    container = Container()
    container.db_engine.override(
        providers.Singleton(
            create_async_engine, container.config.db.test_url, echo=False
        )
    )
    db = container.db_service()
    await db.create_database()
    return db


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=main.app, base_url="http://localhost:8000") as client:
        yield client
