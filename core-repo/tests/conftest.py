import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from database.database_service import DatabaseService

@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def db_url() -> str:
    return "postgresql+asyncpg://taiharry:123456@localhost:5432/testdb"

@pytest.fixture(scope="module")
def db_engine(db_url) -> AsyncEngine:
    return create_async_engine(db_url, echo=False)

@pytest.fixture(scope="module")
def db_session_maker(db_engine: AsyncEngine) -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False,
    bind=db_engine, expire_on_commit=False,
    class_=AsyncSession)


@pytest.fixture(scope="module", autouse=True)
async def database(db_engine: AsyncEngine, db_session_maker: sessionmaker):
    
    db_service = DatabaseService(db_engine, db_session_maker)
    await db_service.create_database()
    return db_service
