import pytest

from kink import di
from logging import getLogger
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy import delete

from core.security_service import SecurityService
from core.user_service import UserService
from database import DatabaseService
from database.models import User as DBUser, File, PrivateKey


logger = getLogger(__name__)


@pytest.fixture
def user_service(user_service: UserService = di[UserService]) -> UserService:
    return user_service


@pytest.fixture
def security_service(
    security_service: SecurityService = di[SecurityService],
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
    db_service: DatabaseService,
    username: str,
    password: str,
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
