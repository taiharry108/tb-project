import os
import pytest

from datetime import timedelta
from typing import AsyncGenerator
from jose import jwt, exceptions
from kink import di
from logging import getLogger
from sqlalchemy.ext.asyncio import AsyncSession


from core.security_service import SecurityService
from database import DatabaseService

logger = getLogger(__name__)


@pytest.fixture(scope="module")
def username() -> str:
    return "test_user1"


@pytest.fixture(scope="module")
def password() -> str:
    return "123456"


@pytest.fixture(scope="module")
def security_service(
    security_service: SecurityService = di[SecurityService],
) -> SecurityService:
    return security_service


@pytest.fixture
def public_key() -> str:
    return os.getenv("JWT_PUBLIC_KEY")


@pytest.fixture
def algo() -> str:
    return "RS256"


@pytest.fixture
async def session(db_service: DatabaseService) -> AsyncGenerator[AsyncSession, None]:
    async with db_service.session() as session:
        async with session.begin():
            yield session


async def test_verify_password(security_service: SecurityService, password: str):
    hashed_password = security_service.hash_password(password)
    hashed_password2 = security_service.hash_password(password)
    assert security_service.verify_password(password, hashed_password)
    assert security_service.verify_password(password, hashed_password2)


async def test_verify_password_failed(security_service: SecurityService, password: str):
    assert not security_service.verify_password(password, "12345")


async def test_create_access_token(
    security_service: SecurityService, username: str, public_key: str
):
    data = {"sub": username}
    token = security_service.create_access_token(data)
    decoded_data = jwt.decode(
        token, public_key, algorithms=[security_service.algorithm]
    )
    assert decoded_data["sub"] == data["sub"]


async def test_decode_access_token(
    security_service: SecurityService, username: str, public_key: str, algo: str
):
    data = {"sub": username}
    token = security_service.create_access_token(data)
    decoded_data = security_service.decode_jwt_token(token, public_key, algo)
    assert decoded_data["sub"] == data["sub"]


async def test_decode_expired_access_token(
    security_service: SecurityService, username: str, public_key: str, algo: str
):
    data = {"sub": username}
    token = security_service.create_access_token(
        data, expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(exceptions.ExpiredSignatureError):
        security_service.decode_jwt_token(token, public_key, algo)
