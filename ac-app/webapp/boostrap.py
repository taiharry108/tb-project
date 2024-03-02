import os
import yaml

from fastapi import HTTPException
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from kink import di
from redis import Redis
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from urllib.parse import urlparse

from async_service import AsyncService
from core.scraping_service import (
    ScrapingServiceFactory,
    Anime1ScrapingService,
    CopyMangaScrapingService,
    ManhuarenScrapingService,
    MangaBatScrapingService,
)
from database import DatabaseService, CRUDService
from download_service import DownloadService
from queue_service import EncryptMessage
from secret_service import SecretService
from security_service import SecurityService
from session import RedisBackend, BasicVerifier
from store_service import FSStoreService


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

    di["store_service"] = FSStoreService()
    di["algorithm"] = di["security_service"]["algorithm"]
    di[SecretService] = lambda di: SecretService()
    di["public_key"] = di[SecretService].get_secret("jwt.key.pub")
    di[SecurityService] = lambda di: SecurityService(di["public_key"], di["algorithm"])
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

    di["auth_server_url"] = di[SecretService].get_secret("AUTH_SERVER_URL")
    di["auth_server_redirect_url"] = di[SecretService].get_secret(
        "AUTH_SERVER_REDIRECT_URL"
    )

    di[Redis] = lambda di: create_redis(di[SecretService].get_secret("REDIS_URL"))
    di["message_cls"] = EncryptMessage

    di["identifier"] = "ac_app"

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
        cookie_name="ac_session_id",
        identifier=di["identifier"],
        auto_error=True,
        secret_key="DONOTUSE",
        cookie_params=di["cookie_params"],
    )

    di["max_connections"] = di["download_service"]["max_connections"]
    di["max_keepalive_connections"] = di["download_service"][
        "max_keepalive_connections"
    ]
    di["headers"] = di["download_service"]["headers"]
    # di["proxy"] = di["download_service"]["proxy"]

    di["num_workers"] = di["async_service"]["num_workers"]
    di["delay"] = di["async_service"]["delay"]

    di[AsyncService] = lambda di: AsyncService(di["num_workers"], di["delay"])

    di.factories[DownloadService] = lambda di: DownloadService(
        di["max_connections"],
        di["max_keepalive_connections"],
        di["headers"],
        di["store_service"],
    )
    di.factories[DatabaseService] = lambda di: DatabaseService(
        di[AsyncEngine], di[orm.sessionmaker]
    )
    di.factories[CRUDService] = lambda di: CRUDService(di[DatabaseService])

    di.factories[Anime1ScrapingService] = lambda di: Anime1ScrapingService(
        di[DownloadService]
    )
    di.factories[CopyMangaScrapingService] = lambda di: CopyMangaScrapingService(
        di[DownloadService]
    )
    di.factories[ManhuarenScrapingService] = lambda di: ManhuarenScrapingService(
        di[DownloadService]
    )
    di.factories[MangaBatScrapingService] = lambda di: MangaBatScrapingService(
        di[DownloadService]
    )

    di[ScrapingServiceFactory] = lambda di: ScrapingServiceFactory(
        anime1=di[Anime1ScrapingService],
        copymanga=di[CopyMangaScrapingService],
        manhuaren=di[ManhuarenScrapingService],
        mangabat=di[MangaBatScrapingService],
    )
