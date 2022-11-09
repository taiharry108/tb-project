from collections import defaultdict
from dependency_injector.wiring import inject, Provide, Provider, providers
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import json
from logging import getLogger
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Iterable

from async_service.async_service import AsyncService
from container import Container
from core.models.chapter import Chapter
from core.models.manga import MangaBase, MangaSimple
from core.models.manga_index_type_enum import MangaIndexTypeEnum, m_types
from core.models.manga_site_enum import MangaSiteEnum
from core.models.meta import Meta
from core.scraping_service.manga_site_scraping_service import MangaSiteScrapingService as MSSService
from database.crud_service import CRUDService
from database.models import MangaSite, Manga, Chapter as DBChapter, Page, User, History
from download_service.download_service import DownloadService
from routers.user import get_user_id_from_session_data
from routers.utils import get_db_session


router = APIRouter()

logger = getLogger(__name__)

FactoryAggregate = providers.FactoryAggregate


@inject
async def save_pages(pages: List[Dict], chapter_id: int,
                     session: AsyncSession,
                     crud_service: CRUDService = Depends(
                         Provide[Container.crud_service])
                     ) -> bool:
    num_pages = len(pages)

    pages = [{
        "pic_path": page["pic_path"],
        "idx": page["idx"],
        "chapter_id": chapter_id,
        "total": num_pages
    } for page in pages]
    return await crud_service.bulk_create_objs_with_unique_key(
        session, Page, pages, "pic_path")


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


@inject
async def _get_chapter_from_chapter_id(
        chapter_id: int,
        crud_service: CRUDService = Depends(
            Provide[Container.crud_service]),
        session: AsyncSession = Depends(get_db_session),):
    db_chapter = await crud_service.get_item_by_id(session, DBChapter, chapter_id)
    if not db_chapter:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Manga does not exist"
        )
    return db_chapter


@inject
async def _get_manga_from_chapter_id(db_chapter: DBChapter = Depends(_get_chapter_from_chapter_id),
                                     crud_service: CRUDService = Depends(
                                         Provide[Container.crud_service]),
                                     session: AsyncSession = Depends(get_db_session),):
    db_manga = await _get_db_manga_from_id(db_chapter.manga_id, session)
    return db_manga


@inject
async def _get_scraping_service_from_chapter(
        db_manga: Manga = Depends(_get_manga_from_chapter_id),
        session: AsyncSession = Depends(get_db_session),) -> MSSService:
    manga_site_name = await _get_manga_site_from_manga(session, db_manga)
    return _get_scraping_service_from_manga(manga_site_name)


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

@router.get('/manga', response_model=MangaSimple)
@inject
async def get_manga(
        user_id: int = Depends(get_user_id_from_session_data),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]), 
        db_session: AsyncSession = Depends(get_db_session),
        db_manga: Manga = Depends(_get_db_manga_from_id),):
    q = select(History).where(History.manga_id == db_manga.id).where(History.user_id == user_id)
    history = (await db_session.execute(q)).one()[0]
    db_chapter = await crud_service.get_item_by_id(db_session, DBChapter, history.chapter_id)
    manga = MangaSimple.from_orm(db_manga)
    manga.last_read_chapter = Chapter.from_orm(db_chapter)
    return manga


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
        scraping_service: MSSService = Depends(
            _get_scraping_service_from_manga),
        download_service: DownloadService = Depends(
            Provide[Container.download_service]),
        download_path: str = Depends(Provide[Container.config.api.download_path]),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),
        db_session: AsyncSession = Depends(get_db_session)):

    meta = await scraping_service.get_meta(db_manga.url)

    download_path = Path(download_path) / \
        scraping_service.site.name / db_manga.name

    download_result = await download_service.download_img(url=meta.thum_img, download_path=download_path, filename="thum_img")
    meta.thum_img = download_result['pic_path']

    await crud_service.update_object(
        db_session, Manga, db_manga.id,
        finished=meta.finished,
        thum_img=str(meta.thum_img),
        last_update=meta.last_update)

    return meta


async def _create_async_gen_from_pages(pages: Iterable[Page]):
    for db_page in pages:
        yield {
            "pic_path": db_page.pic_path,
            "idx": db_page.idx,
            "total": db_page.total
        }


@inject
async def _download_pages(
        download_path: Path,
        page_urls: List[str],
        db_chapter: DBChapter,
        session: AsyncSession,
        download_service: DownloadService = Depends(
        Provide[Container.download_service]),
        async_service: AsyncService = Depends(
        Provide[Container.async_service]),
):
    pages = []
    async for result in download_service.download_imgs(
        async_service,
        download_path=download_path,
        img_list=[{"url": url, "filename": str(
            idx), "idx": idx, "total": len(page_urls)} for idx, url in enumerate(page_urls)],
        headers={"Referer": db_chapter.page_url}
    ):
        pages.append(result)
        yield result
    await save_pages(pages, db_chapter.id, session)


async def _sse_img_gen(page_list):
    async for page in page_list:
        yield f'data: {json.dumps(page)}\n\n'
    yield 'data: {}\n\n'


@router.get("/pages")
@inject
async def get_pages(
        db_chapter: DBChapter = Depends(_get_chapter_from_chapter_id),
        db_manga: Manga = Depends(_get_manga_from_chapter_id),
        session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),
        scraping_service: MSSService = Depends(
            _get_scraping_service_from_chapter),
        download_path: str = Depends(Provide[Container.config.api.download_path])):

    pages = await crud_service.get_items_by_same_attr(session, Page, "chapter_id", db_chapter.id)
    if pages:
        page_gen = _create_async_gen_from_pages(pages)
    else:
        page_urls = await scraping_service.get_page_urls(db_chapter.page_url)

        download_path = Path(download_path) / \
            scraping_service.site.name / db_manga.name / db_chapter.title
        
        page_gen = _download_pages(
            download_path, page_urls, db_chapter, session)

    headers = {"Content-Type": "text/event-stream",
               "Crawled": "false" if pages else "true"}

    return StreamingResponse(_sse_img_gen(page_gen), 
            headers=headers)
