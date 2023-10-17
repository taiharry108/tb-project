from typing import AsyncGenerator
import pytest
from dependency_injector.wiring import inject, Provide
from dependency_injector import providers
from container import Container

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from logging import getLogger
from logging import config

from core.security_service import SecurityService
from core.user_service import UserService
from database import DatabaseService
from database.models import User as DBUser, File, PrivateKey


config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = getLogger(__name__)


@pytest.fixture(scope="module")
@inject
def db_service(
    db_service: DatabaseService = Provide[Container.db_service],
) -> DatabaseService:
    return db_service


@pytest.fixture
@inject
def user_service(
    user_service: providers.Singleton[UserService] = Provide[Container.user_service],
) -> UserService:
    return user_service


@pytest.fixture
@inject
def security_service(
    security_service: providers.Singleton[SecurityService] = Provide[
        Container.security_service
    ],
) -> SecurityService:
    return security_service


@pytest.fixture(scope="module")
def username() -> str:
    return "test_user1"


@pytest.fixture(scope="module")
def password() -> str:
    return "123456"


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(
    db_service: DatabaseService, username: str, password: str
):
    async with db_service.session() as session:
        async with session.begin():
            await session.execute(delete(PrivateKey))
            await session.execute(delete(File))
            await session.execute(delete(DBUser))
            db_user = DBUser(email=username, hashed_password=password)
            session.add(db_user)
            await session.commit()

    yield


@pytest.fixture
async def session(db_service: DatabaseService) -> AsyncGenerator[AsyncSession, None]:
    async with db_service.session() as session:
        async with session.begin():
            yield session


async def test_get_user(
    user_service: UserService, username: str, session: AsyncSession
):
    db_user = await user_service.get_user(session, username)
    if db_user is None:
        assert False

    assert db_user.email == username


async def test_create_user(
    user_service: UserService,
    security_service: SecurityService,
    password: str,
    session: AsyncSession,
):
    username = "test_user2"
    db_user = await user_service.create_user(session, username, password)
    assert db_user.email == username
    assert security_service.verify_password(password, db_user.hashed_password)


async def test_create_user_twice(
    user_service: UserService, username: str, password: str, session: AsyncSession
):
    db_user = await user_service.create_user(session, username, password)
    assert db_user is None
