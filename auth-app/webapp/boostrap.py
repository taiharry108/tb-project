import os
import yaml

from fastapi import HTTPException
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from kink import di
from redis import Redis
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from urllib.parse import urlparse

from core.security_service import SecurityService
from core.user_service import UserService
from database import DatabaseService, CRUDService
from secret_service import SecretService
from session import RedisBackend, BasicVerifier


def _load_config_file() -> dict:
    with open("config.yml") as f:
        return yaml.safe_load(f)


def create_redis(url: str) -> Redis:
    parsed_url = urlparse(url)
    if parsed_url.hostname is None:
        return Redis(url)
    else:
        return Redis(
            host=parsed_url.hostname,
            port=parsed_url.port,
            password=parsed_url.password,
            ssl=True,
            username=parsed_url.username,
        )


def bootstrap_di() -> None:
    config_obj = _load_config_file()

    for key, value in config_obj.items():
        di[key] = value

    di[SecretService] = lambda di: SecretService()
    di["private_key"] = di[SecretService].get_secret("jwt.key")

    di["algorithm"] = di["security_service"]["algorithm"]
    di["access_token_expire_minutes"] = di["security_service"][
        "access_token_expire_minutes"
    ]

    di[SecurityService] = lambda di: SecurityService(
        private_key=di["private_key"],
        algorithm=di["algorithm"],
        access_token_expire_minutes=di["access_token_expire_minutes"],
    )
    di.factories[AsyncEngine] = lambda di: create_async_engine(
        di[SecretService].get_secret("DB_URL"), echo=False
    )
    di.factories[orm.sessionmaker] = lambda di: orm.sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=di[AsyncEngine],
        expire_on_commit=False,
        class_=AsyncSession,
    )

    di.factories[DatabaseService] = lambda di: DatabaseService(
        di[AsyncEngine], di[orm.sessionmaker]
    )
    di.factories[CRUDService] = lambda di: CRUDService(di[DatabaseService])

    di.factories[UserService] = lambda di: UserService(
        crud_service=di[CRUDService], security_service=di[SecurityService]
    )

    di[Redis] = lambda di: create_redis(di[SecretService].get_secret("REDIS_URL"))

    di["identifier"] = "auth_app"

    di["auth_http_exception"] = HTTPException(status_code=403, detail="invalid session")

    di.factories[RedisBackend] = di.factories[
        "session_backend"
    ] = lambda di: RedisBackend(redis=di[Redis], identifier=di["identifier"])

    di.factories["verifier"] = lambda di: BasicVerifier(
        identifier=di["identifier"],
        auto_error=True,
        backend=di[RedisBackend],
        auth_http_exception=di["auth_http_exception"],
    )

    di.factories["cookie_params"] = lambda _: CookieParameters()
    di.factories["cookie"] = lambda di: SessionCookie(
        cookie_name="a_session_id",
        identifier=di["identifier"],
        auto_error=True,
        secret_key="DONOTUSE",
        cookie_params=di["cookie_params"],
    )
