from dependency_injector import containers, providers
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi import HTTPException
from passlib.context import CryptContext
from redis import Redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import orm
from uuid import UUID

from core.some_service import SomeService
from core.security_service import SecurityService
from core.user_service import UserService

from database.crud_service import CRUDService
from database.database_service import DatabaseService
from session.redis_backend import RedisBackend
from session.session_verifier import BasicVerifier, SessionData


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[], packages=["tests", "routers"]
    )
    config = providers.Configuration(yaml_files=["config.yml"])

    some_service_factory = providers.FactoryAggregate(
        s=providers.Singleton(SomeService),
    )

    config.jwt_private_key.from_env("JWT_PRIVATE_KEY")
    config.jwt_public_key.from_env("JWT_PUBLIC_KEY")

    some_service = providers.Singleton(some_service_factory, config.some_service.name)

    db_engine = providers.Singleton(create_async_engine, config.db.url, echo=False)

    db_session_maker = providers.Singleton(
        orm.sessionmaker,
        autocommit=False,
        autoflush=False,
        bind=db_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    db_service = providers.Singleton(DatabaseService, db_engine, db_session_maker)

    crud_service = providers.Singleton(CRUDService, db_service=db_service)

    security_service = providers.Singleton(
        SecurityService,
        private_key=config.jwt_private_key,
        algorithm=config.security_service.algorithm,
        rt_key=config.security_service.rt_key,
        access_token_expire_minutes=config.security_service.access_token_expire_minutes,
        pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto"),
    )

    user_service = providers.Singleton(
        UserService,
        crud_service=crud_service,
        security_service=security_service,
    )

    redis = providers.Singleton(Redis, host=config.redis.url)

    session_backend = providers.Singleton(
        RedisBackend[UUID, SessionData], redis=redis, identifier="auth_app"
    )

    auth_http_exception = providers.Singleton(
        HTTPException, status_code=403, detail="invalid session"
    )

    # session
    verifier = providers.Factory(
        BasicVerifier,
        identifier="auth-app",
        auto_error=True,
        backend=session_backend,
        auth_http_exception=auth_http_exception,
    )

    cookie_params = providers.Factory(CookieParameters)

    cookie = providers.Factory(
        SessionCookie,
        cookie_name="a_session_id",
        identifier="auth-app",
        auto_error=True,
        secret_key="DONOTUSE",
        cookie_params=cookie_params,
    )
