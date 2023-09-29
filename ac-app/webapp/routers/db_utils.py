from dependency_injector.wiring import inject, Provide, Provider, providers
from enum import Enum
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union

from container import Container

from core.models.manga_site_enum import MangaSiteEnum
from core.scraping_service.anime_site_scraping_service import (
    AnimeSiteScrapingService as ASSService,
)
from core.scraping_service.manga_site_scraping_service import (
    MangaSiteScrapingService as MSSService,
)
from database.crud_service import CRUDService
from database.models import MangaSite, Manga, Chapter, Anime, Episode
from routers.utils import get_db_session

FactoryAggregate = providers.FactoryAggregate


class DBItemType(Enum):
    Anime = "Anime"
    Manga = "Manga"
    Chapter = "Chapter"
    Episode = "Episode"


@inject
async def _get_db_item_from_id(
    item_id: int,
    db_item_type: DBItemType,
    session: AsyncSession,
    crud_service: CRUDService = Provide[Container.crud_service],
):
    if db_item_type == DBItemType.Anime:
        db_type = Anime
    elif db_item_type == DBItemType.Manga:
        db_type = Manga
    elif db_item_type == DBItemType.Chapter:
        db_type = Chapter
    elif db_item_type == DBItemType.Episode:
        db_type = Episode
    db_item = await crud_service.get_item_by_id(session, db_type, item_id)
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"{db_item_type.value} does not exist",
        )
    return db_item


@inject
async def get_db_manga_from_id(
    manga_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    return await _get_db_item_from_id(manga_id, DBItemType.Manga, session)


@inject
async def get_db_anime_from_id(
    anime_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    return await _get_db_item_from_id(anime_id, DBItemType.Anime, session)


@inject
async def get_chapter_from_id(
    chapter_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    return await _get_db_item_from_id(chapter_id, DBItemType.Chapter, session)


@inject
async def get_episode_from_id(
    episode_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    return await _get_db_item_from_id(episode_id, DBItemType.Episode, session)


@inject
async def get_manga_site_from_manga(
    session: AsyncSession = Depends(get_db_session),
    db_manga: Manga = Depends(get_db_manga_from_id),
    crud_service: CRUDService = Depends(Provide[Container.crud_service]),
) -> str:
    return await crud_service.get_attr_of_item_by_id(
        session, MangaSite, db_manga.manga_site_id, "name"
    )


@inject
async def get_manga_site_from_anime(
    session: AsyncSession = Depends(get_db_session),
    db_anime: Anime = Depends(get_db_anime_from_id),
    crud_service: CRUDService = Depends(Provide[Container.crud_service]),
) -> str:
    return await crud_service.get_attr_of_item_by_id(
        session, MangaSite, db_anime.manga_site_id, "name"
    )


@inject
async def get_manga_site_id(
    site: MangaSiteEnum,
    crud_service: CRUDService = Depends(Provide[Container.crud_service]),
    session: AsyncSession = Depends(get_db_session),
):
    return await crud_service.get_id_by_attr(session, MangaSite, "name", site.value)


@inject
def get_scraping_service_from_site(
    site: MangaSiteEnum, ss_factory=Provider[Container.scraping_service_factory]
) -> Union[MSSService, ASSService]:
    return ss_factory(site)


@inject
def get_scraping_service_from_manga(
    manga_site_name: str = Depends(get_manga_site_from_manga),
) -> MSSService:
    return get_scraping_service_from_site(manga_site_name)


@inject
def get_scraping_service_from_anime(
    manga_site_name: str = Depends(get_manga_site_from_anime),
) -> ASSService:
    return get_scraping_service_from_site(manga_site_name)


@inject
async def get_manga_from_chapter_id(
    db_chapter: Chapter = Depends(get_chapter_from_id),
    session: AsyncSession = Depends(get_db_session),
) -> Manga:
    return await get_db_manga_from_id(db_chapter.manga_id, session)


@inject
async def get_anime_from_episode_id(
    db_episode: Episode = Depends(get_episode_from_id),
    session: AsyncSession = Depends(get_db_session),
) -> Anime:
    return await get_db_anime_from_id(db_episode.anime_id, session)


@inject
async def get_scraping_service_from_chapter(
    db_manga: Manga = Depends(get_manga_from_chapter_id),
    session: AsyncSession = Depends(get_db_session),
) -> MSSService:
    manga_site_name = await get_manga_site_from_manga(session, db_manga)
    return get_scraping_service_from_manga(manga_site_name)


@inject
async def get_scraping_service_from_episode(
    db_anime: Anime = Depends(get_anime_from_episode_id),
    session: AsyncSession = Depends(get_db_session),
) -> ASSService:
    manga_site_name = await get_manga_site_from_anime(session, db_anime)
    return get_scraping_service_from_anime(manga_site_name)
