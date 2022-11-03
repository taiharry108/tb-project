from concurrent.futures import ProcessPoolExecutor
from dependency_injector import containers, providers

from fastapi import HTTPException
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.backends.implementations import InMemoryBackend
from logging import config as log_config, getLogger
from redis import Redis
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from uuid import UUID

from core.fernet_encrypt_service import FernetEncryptService
from core.security_service import SecurityService
from core.key_management_service import KeyManagementService
from database.database_service import DatabaseService
from database.crud_service import CRUDService

from queue_service.redis_queue_service import RedisQueueService
from queue_service.messages import EncryptMessage
from session.redis_backend import RedisBackend
from session.session_verifier import BasicVerifier, SessionData
from store_service.fs_store_service import FSStoreService


def init_process_pool(max_workers: int):
    process_pool = ProcessPoolExecutor(max_workers=max_workers)
    getLogger(__name__).info(process_pool)
    yield process_pool
    process_pool.shutdown(wait=True)


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(packages=["routers"])
    config = providers.Configuration(yaml_files=["config.yml"])


    store_service_factory = providers.FactoryAggregate(
        fs=providers.Singleton(
            FSStoreService
        ),
    )

    store_service = providers.Singleton(
        store_service_factory, config.store_service.name)

    encrypt_service_factory = providers.FactoryAggregate(
        fernet=providers.Singleton(
            FernetEncryptService,
            store_service_factory.fs
        )
    )

    encrypt_service = providers.Factory(
        encrypt_service_factory, config.encrypt_service.name
    )

    config.jwt_public_key.from_env("JWT_PUBLIC_KEY")

    security_service = providers.Singleton(
        SecurityService,
        public_key=config.jwt_public_key,
        algorithm=config.security_service.algorithm,
    )

    key_management_servcice = providers.Singleton(
        KeyManagementService,
        source=config.key_management_service.source,
        encrypt_service=encrypt_service_factory.fernet
    )

    process_pool = providers.Resource(
        init_process_pool,
        max_workers=5,
    )

    logging = providers.Resource(
        log_config.fileConfig,
        'logging.conf',
        disable_existing_loggers=False
    )

    db_engine = providers.Singleton(
        create_async_engine, config.db.url, echo=False)

    db_session_maker = providers.Singleton(
        orm.sessionmaker,
        autocommit=False,
        autoflush=False,
        bind=db_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )

    db_service = providers.Singleton(
        DatabaseService, db_engine, db_session_maker)

    crud_service = providers.Singleton(
        CRUDService,
        db_service
    )

    redis = providers.Singleton(Redis,
        host=config.redis.url
    )

    redis_queue_service = providers.Singleton(
        RedisQueueService,
        redis,
        EncryptMessage,
        0
    )
    
    session_backend = providers.Singleton(
        RedisBackend[UUID, SessionData],
        redis=redis,
        identifier="encryption_app"
    )

    auth_http_exception = providers.Singleton(
        HTTPException,
        status_code=403,
        detail="invalid session"
    )

    # session
    verifier = providers.Factory(
        BasicVerifier,
        identifier="encryption_app",
        auto_error=True,
        backend=session_backend,
        auth_http_exception=auth_http_exception,
    )

    cookie_params = providers.Factory(CookieParameters)

    cookie = providers.Factory(
        SessionCookie,
        cookie_name="e_session_id",
        identifier="encryption_app",
        auto_error=True,
        secret_key="DONOTUSE",
        cookie_params=cookie_params,
    )
