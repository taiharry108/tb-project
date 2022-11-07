from collections import defaultdict
from dependency_injector.wiring import inject, Provide, Provider, providers
from fastapi import APIRouter, Depends, HTTPException, status
from logging import getLogger
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any

from container import Container
from core.models.chapter import Chapter
from core.models.manga import MangaBase
from core.models.manga_index_type_enum import MangaIndexTypeEnum, m_types
from core.models.manga_site_enum import MangaSiteEnum
from core.models.meta import Meta
from core.scraping_service.manga_site_scraping_service import MangaSiteScrapingService as MSSService
from database.crud_service import CRUDService
from database.models import MangaSite, Manga, Chapter as DBChapter
from download_service.download_service import DownloadService
from routers.utils import get_db_session

router = APIRouter()

logger = getLogger(__name__)

FactoryAggregate = providers.FactoryAggregate


@inject
async def _get_manga_site_id(site: MangaSiteEnum, crud_service: CRUDService = Depends(
        Provide[Container.crud_service]), session: AsyncSession = Depends(
            get_db_session)):
    return await crud_service.get_id_by_attr(
        session,
        MangaSite,
        "name",
        site.value
    )


@inject
async def _get_db_manga_from_id(
        manga_id: int,
        session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    db_manga = await crud_service.get_item_by_id(session, Manga, manga_id)
    if db_manga is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Manga does not exist"
        )
    return db_manga


@inject
async def _get_manga_site_from_manga(
        session: AsyncSession = Depends(get_db_session),
        db_manga: Manga = Depends(_get_db_manga_from_id),
        crud_service: CRUDService = Depends(
        Provide[Container.crud_service])) -> str:
    return await crud_service.get_attr_of_item_by_id(session, MangaSite, db_manga.manga_site_id, "name")


@inject
def _get_scraping_service_from_site(
        site: MangaSiteEnum,
        ss_factory: FactoryAggregate[MSSService] = Depends(
        Provider[Container.scraping_service_factory])) -> MSSService:
    return ss_factory(
        site)


@inject
def _get_scraping_service_from_manga(
    manga_site_name: str = Depends(_get_manga_site_from_manga),
    ss_factory: FactoryAggregate[MSSService] = Depends(
        Provider[Container.scraping_service_factory])) -> MSSService:
    return ss_factory(manga_site_name)


@router.get("/search", response_model=list[MangaBase])
@inject
async def search_manga(
        keyword: str,
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),
        manga_site_id: int = Depends(_get_manga_site_id),
        session: AsyncSession = Depends(get_db_session),
        scraping_service: MSSService = Depends(_get_scraping_service_from_site)):
    mangas = await scraping_service.search_manga(keyword)

    mangas = [{"name": manga.name, "url": str(manga.url), "manga_site_id": manga_site_id}
              for manga in mangas]
    return await crud_service.bulk_create_objs_with_unique_key(session, Manga, mangas, "url")


@router.get('/chapters', response_model=Dict[MangaIndexTypeEnum, List[Chapter]])
@inject
async def get_chapters(
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),
        session: AsyncSession = Depends(get_db_session),
        db_manga: Manga = Depends(_get_db_manga_from_id),
        scraping_service: MSSService = Depends(_get_scraping_service_from_manga)) -> list[Chapter]:

    chapters = await scraping_service.get_chapters(db_manga.url)
    chapters_to_insert = []

    for m_type, chap_list in chapters.items():
        for chap in chap_list:
            chapters_to_insert.append({
                "title": chap.title,
                "page_url": chap.page_url,
                "manga_id": db_manga.id,
                "type": m_types.index(m_type)
            })
    db_chapters = await crud_service.bulk_create_objs_with_unique_key(session, DBChapter, chapters_to_insert, "page_url")
    result = defaultdict(list)
    for db_chapter in db_chapters:
        m_type = m_types[db_chapter.type]
        result[m_type].append(db_chapter)
    return result


@router.get('/meta', response_model=Meta)
@inject
async def get_meta(
        db_manga: Manga = Depends(_get_db_manga_from_id),
        scraping_service: MSSService = Depends(_get_scraping_service_from_manga),
        download_service: DownloadService = Depends(Provide[Container.download_service]),
        download_path: str = Depends(Provide[Container.config.api.download_path])):
    
    meta = await scraping_service.get_meta(db_manga.url)

    download_path = Path(download_path) / scraping_service.site.name / db_manga.name

    download_result = await download_service.download_img(url=meta.thum_img, download_path=download_path, filename="thum_img")
    meta.thum_img = download_result['pic_path']

    return meta
