import asyncio

from dependency_injector import providers
from dependency_injector.wiring import inject
from httpx import AsyncClient
import pytest

from sqlalchemy.ext.asyncio import create_async_engine

from container import Container
from store_service.store_service import StoreService
from database.crud_service import CRUDService
from database.database_service import DatabaseService
import main


@pytest.fixture(scope="module")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="module")
@inject
async def container() -> Container:
    return Container()


@pytest.fixture(autouse=True, scope="module")
@inject
async def database(container: Container) -> DatabaseService:
    container.db_engine.override(providers.Singleton(
        create_async_engine, container.config.db.test_url,
        echo=False
    ))
    db = container.db_service()
    await db.create_database()
    return db


@pytest.fixture(autouse=True, scope="module")
@inject
async def crud_service(container: Container, database: DatabaseService):
    container.crud_service.override(providers.Singleton(
        CRUDService, database
    ))    
    return container.crud_service()


@pytest.fixture(autouse=True, scope="module")
@inject
async def store_service(container: Container) -> StoreService:
    return container.store_service()


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=main.app, base_url="http://localhost:60802") as client:
        yield client
