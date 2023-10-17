import asyncio
from dependency_injector import providers
from dependency_injector.wiring import inject, Provide
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from container import Container
from database import CRUDService
from database import DatabaseService
import main


@pytest.fixture(scope="session")
def event_loop():
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
    container.db_engine.override(
        providers.Singleton(
            create_async_engine, container.config.db.test_url, echo=False
        )
    )
    db = container.db_service()
    await db.create_database()
    return db


@pytest.fixture(scope="module")
@inject
async def crud_service(crud_service=Provide[Container.crud_service]) -> CRUDService:
    return crud_service


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=main.app, base_url="http://localhost:60802") as client:
        yield client


@pytest.fixture()
async def db_session(database: DatabaseService) -> AsyncSession:
    session = database.new_session()
    try:
        async with session.begin():
            yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
