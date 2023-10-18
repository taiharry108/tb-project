import asyncio
import pytest

from httpx import AsyncClient
from kink import di, inject as kink_inject

from sqlalchemy import orm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine

import main

from boostrap import bootstrap_di
from core.scraping_service import ScrapingServiceFactory
from database import DatabaseService, CRUDService
from download_service import DownloadService


from boostrap import bootstrap_di

bootstrap_di()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()

    yield loop
    loop.close()


# @pytest.fixture(autouse=True, scope="module")
# @inject
# async def container() -> Container:
#     return Container()


# @pytest.fixture(autouse=True, scope="module")
# @inject
# async def database(container: Container) -> DatabaseService:
#     container.db_engine.override(
#         providers.Singleton(
#             create_async_engine, container.config.db.test_url, echo=False
#         )
#     )
#     db = container.db_service()
#     await db.create_database()
#     return db


@pytest.fixture(autouse=True, scope="module")
def db_engine() -> AsyncEngine:
    di.factories[AsyncEngine] = lambda di: create_async_engine(
        di["db"]["test_url"], echo=False
    )
    return di[AsyncEngine]


@pytest.fixture(autouse=True, scope="module")
async def database() -> DatabaseService:
    di.factories[AsyncEngine] = lambda di: create_async_engine(
        di["db"]["test_url"], echo=False
    )
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
async def crud_service(database: DatabaseService) -> CRUDService:
    di.factories[CRUDService] = lambda di: CRUDService(database)
    return di[CRUDService]


# @pytest.fixture(scope="module")
# def anyio_backend():
#     return "asyncio"


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


@pytest.fixture()
async def scraping_service_factory() -> ScrapingServiceFactory:
    return di[ScrapingServiceFactory]


@pytest.fixture
async def download_service() -> DownloadService:
    return di[DownloadService]
