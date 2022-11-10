from dependency_injector import containers, providers

from fastapi import HTTPException
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from logging import config as log_config
from redis import Redis
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from uuid import UUID

from async_service.async_service import AsyncService
from download_service.download_service import DownloadService
from core.scraping_service.manhuaren_scraping_service import ManhuarenScrapingService
from core.scraping_service.copymanga_scraping_service import CopyMangaScrapingService
from core.scraping_service.anime1_scraping_service import Anime1ScrapingService

from database.database_service import DatabaseService
from database.crud_service import CRUDService

from queue_service.redis_queue_service import RedisQueueService
from queue_service.messages import EncryptMessage
from security_service.security_service import SecurityService
from session.redis_backend import RedisBackend
from session.session_verifier import BasicVerifier, SessionData
from store_service.fs_store_service import FSStoreService


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        packages=["routers", "tests"])
    config = providers.Configuration(yaml_files=["config.yml"])

    store_service_factory = providers.FactoryAggregate(
        fs=providers.Singleton(
            FSStoreService
        ),
    )

    store_service = providers.Singleton(
        store_service_factory, config.store_service.name)

    config.jwt_public_key.from_env("JWT_PUBLIC_KEY")

    security_service = providers.Singleton(
        SecurityService,
        public_key=config.jwt_public_key,
        algorithm=config.security_service.algorithm,
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
        identifier="ac_app",
        auto_error=True,
        backend=session_backend,
        auth_http_exception=auth_http_exception,
    )

    cookie_params = providers.Factory(CookieParameters)

    cookie = providers.Factory(
        SessionCookie,
        cookie_name="ac_session_id",
        identifier="ac_app",
        auto_error=True,
        secret_key="DONOTUSE",
        cookie_params=cookie_params,
    )

    download_service = providers.Factory(
        DownloadService,
        max_connections=config.download_service.max_connections,
        max_keepalive_connections=config.download_service.max_keepalive_connections,
        headers=config.download_service.headers,
        store_service=store_service,
        proxy=config.download_service.proxy
    )

    scraping_service_factory = providers.FactoryAggregate(
        manhuaren=providers.Singleton(
            ManhuarenScrapingService,
            download_service=download_service),
        copymanga=providers.Singleton(
            CopyMangaScrapingService,
            download_service=download_service
        ),
        anime1=providers.Singleton(
            Anime1ScrapingService,
            download_service=download_service
        )
    )

    async_service = providers.Singleton(
        AsyncService,
        num_workers=config.async_service.num_workers,
        delay=config.async_service.delay,
    )
