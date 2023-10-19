import asyncio
import json

from collections import defaultdict
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from kink import di, inject as kink_inject
from logging import getLogger
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Iterable

from async_service import AsyncService
from core.models.chapter import Chapter
from core.models.anime import AnimeBase, AnimeSimple
from core.models.episode import Episode
from core.models.manga import MangaBase, MangaSimple
from core.models.manga_index_type_enum import MangaIndexTypeEnum, m_types
from core.models.meta import Meta
from core.scraping_service.anime_site_scraping_service import (
    AnimeSiteScrapingService as ASSService,
)
from core.scraping_service.anime1_scraping_service import Anime1ScrapingService
from core.scraping_service.manga_site_scraping_service import (
    MangaSiteScrapingService as MSSService,
)
from database import CRUDService
from database.models import (
    Manga,
    Chapter as DBChapter,
    Page,
    History,
    Anime,
    Episode as DBEpisode,
    AHistory,
)
from download_service import DownloadService
from routers import db_utils
from routers.user import get_user_id_from_session_data
from routers.utils import get_db_session
from sqlalchemy.exc import NoResultFound

router = APIRouter()

logger = getLogger(__name__)


async def save_pages(
    pages: List[Dict],
    chapter_id: int,
    session: AsyncSession,
    crud_service: CRUDService,
) -> bool:
    num_pages = len(pages)

    pages = [
        {
            "pic_path": page["pic_path"],
            "idx": page["idx"],
            "chapter_id": chapter_id,
            "total": num_pages,
        }
        for page in pages
    ]

    return await crud_service.bulk_create_objs_with_unique_key(
        session, Page, pages, "pic_path"
    )


async def _search_manga(
    keyword: str,
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    manga_site_id: int = Depends(db_utils.get_manga_site_id),
    session: AsyncSession = Depends(get_db_session),
    scraping_service: MSSService = Depends(db_utils.get_scraping_service_from_site),
) -> list[MangaBase] | None:
    if isinstance(scraping_service, Anime1ScrapingService):
        return None
    mangas = await scraping_service.search_manga(keyword)
    mangas = [
        {"name": manga.name, "url": str(manga.url), "manga_site_id": manga_site_id}
        for manga in mangas
    ]
    mangas = await crud_service.bulk_create_objs_with_unique_key(
        session, Manga, mangas, "url"
    )
    return [MangaBase.model_validate(manga) for manga in mangas]


async def _search_anime(
    keyword: str,
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    manga_site_id: int = Depends(db_utils.get_manga_site_id),
    session: AsyncSession = Depends(get_db_session),
    scraping_service: ASSService = Depends(db_utils.get_scraping_service_from_site),
) -> list[AnimeBase] | None:
    if not isinstance(scraping_service, Anime1ScrapingService):
        return None
    animes = await scraping_service.search_anime(keyword)

    animes = [
        {
            "name": anime.name,
            "url": str(anime.url),
            "manga_site_id": manga_site_id,
            "eps": anime.eps,
            "year": anime.year,
            "season": anime.season,
            "sub": anime.season,
        }
        for anime in animes
    ]
    animes = await crud_service.bulk_create_objs_with_unique_key(
        session, Anime, animes, "url"
    )
    return [AnimeBase.model_validate(anime) for anime in animes]


@router.get(
    "/search",
)
async def search(
    manga_result: list[MangaBase] = Depends(_search_manga),
    anime_result: list[AnimeBase] = Depends(_search_anime),
):
    if manga_result:
        return manga_result
    if anime_result:
        return anime_result


@router.get("/manga", response_model=MangaSimple)
async def get_manga(
    user_id: int = Depends(get_user_id_from_session_data),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    db_session: AsyncSession = Depends(get_db_session),
    db_manga: Manga = Depends(db_utils.get_db_manga_from_id),
):
    manga = MangaSimple.model_validate(db_manga)
    q = (
        select(History)
        .where(History.manga_id == db_manga.id)
        .where(History.user_id == user_id)
    )
    try:
        history = (await db_session.execute(q)).one()[0]
        db_chapter = await crud_service.get_item_by_id(
            db_session, DBChapter, history.chapter_id
        )
        manga.last_read_chapter = Chapter.model_validate(db_chapter)
    except NoResultFound:
        logger.warning("no history is found")
    return manga


@router.get("/anime", response_model=AnimeSimple)
async def get_anime(
    user_id: int = Depends(get_user_id_from_session_data),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    db_session: AsyncSession = Depends(get_db_session),
    db_anime: Manga = Depends(db_utils.get_db_anime_from_id),
):
    anime = AnimeSimple.model_validate(db_anime)
    q = (
        select(AHistory)
        .where(AHistory.anime_id == db_anime.id)
        .where(AHistory.user_id == user_id)
    )
    try:
        history = (await db_session.execute(q)).one()[0]
        db_episode = await crud_service.get_item_by_id(
            db_session, DBEpisode, history.episode_id
        )
        anime.last_read_episode = Episode.model_validate(db_episode)
    except NoResultFound:
        logger.warning("no history is found")
    return anime


@router.get("/episodes", response_model=List[Episode])
async def get_episodes(
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    session: AsyncSession = Depends(get_db_session),
    db_anime: Anime = Depends(db_utils.get_db_anime_from_id),
    scraping_service: ASSService = Depends(db_utils.get_scraping_service_from_anime),
) -> List[Episode]:
    episodes = await scraping_service.get_index_page(db_anime)

    episodes_to_insert = [
        {
            "title": ep.title,
            "last_update": ep.last_update,
            "data": ep.data,
            "anime_id": db_anime.id,
            "manual_key": f"{db_anime.id}:{ep.title}",
        }
        for ep in episodes
    ]

    db_episodes = await crud_service.bulk_create_objs_with_unique_key(
        session, DBEpisode, episodes_to_insert, "manual_key", update_attrs=["data"]
    )
    return db_episodes


@router.get("/chapters", response_model=Dict[MangaIndexTypeEnum, List[Chapter]])
async def get_chapters(
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    session: AsyncSession = Depends(get_db_session),
    db_manga: Manga = Depends(db_utils.get_db_manga_from_id),
    scraping_service: MSSService = Depends(db_utils.get_scraping_service_from_manga),
) -> list[Chapter]:
    chapters = await scraping_service.get_chapters(db_manga.url)
    chapters_to_insert = []

    for m_type, chap_list in chapters.items():
        for chap in chap_list:
            chapters_to_insert.append(
                {
                    "title": chap.title,
                    "page_url": str(chap.page_url),
                    "manga_id": db_manga.id,
                    "type": m_types.index(m_type),
                }
            )
    db_chapters = await crud_service.bulk_create_objs_with_unique_key(
        session, DBChapter, chapters_to_insert, "page_url"
    )
    result = defaultdict(list)
    for db_chapter in db_chapters:
        m_type = m_types[db_chapter.type]
        result[m_type].append(db_chapter)
    return result


@router.get("/meta", response_model=Meta)
async def get_meta(
    db_manga: Manga = Depends(db_utils.get_db_manga_from_id),
    scraping_service: MSSService = Depends(db_utils.get_scraping_service_from_manga),
    download_service: DownloadService = Depends(lambda: di[DownloadService]),
    download_path: str = Depends(lambda: di["api"]["download_path"]),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    db_session: AsyncSession = Depends(get_db_session),
):
    meta = await scraping_service.get_meta(db_manga.url)

    download_path = Path(download_path) / scraping_service.site.name / db_manga.name

    download_result = await download_service.download_img(
        url=str(meta.thum_img), download_path=download_path, filename="thum_img"
    )
    meta.thum_img = download_result["pic_path"]

    await crud_service.update_object(
        db_session,
        Manga,
        db_manga.id,
        finished=meta.finished,
        thum_img=str(meta.thum_img),
        last_update=meta.last_update,
    )

    return meta


async def _create_async_gen_from_pages(pages: Iterable[Page]):
    for db_page in pages:
        yield {"pic_path": db_page.pic_path, "idx": db_page.idx, "total": db_page.total}


async def _download_pages(
    download_path: Path,
    page_urls: List[str],
    db_chapter: DBChapter,
    session: AsyncSession,
    download_service: DownloadService,
    async_service: AsyncService,
    crud_service: CRUDService,
):
    pages = []
    async for result in download_service.download_imgs(
        async_service,
        download_path=download_path,
        img_list=[
            {"url": url, "filename": str(idx), "idx": idx, "total": len(page_urls)}
            for idx, url in enumerate(page_urls)
        ],
        headers={"Referer": db_chapter.page_url},
    ):
        pages.append(result)
        yield result
    await save_pages(pages, db_chapter.id, session, crud_service)


async def _sse_img_gen(page_list):
    async for page in page_list:
        yield f"data: {json.dumps(page)}\n\n"
    yield "data: {}\n\n"


@router.get("/episode")
async def get_episode(
    db_episode: DBEpisode = Depends(db_utils.get_episode_from_id),
    db_anime: Anime = Depends(db_utils.get_anime_from_episode_id),
    scraping_service: ASSService = Depends(db_utils.get_scraping_service_from_episode),
    download_path: str = Depends(lambda: di["api"]["download_path"]),
):
    download_path = (
        Path(download_path)
        / scraping_service.site.name
        / db_anime.name
        / db_anime.season
    )

    vid_url = await scraping_service.get_video_url(db_episode)

    download_service: DownloadService = scraping_service.download_service
    logger.info(f"{download_service.client.cookies=}")
    result = await download_service.download_vid(
        url=vid_url, download_path=download_path, filename=db_episode.title
    )
    return result


def _check_pages_exist(pages: Page):
    if not pages:
        return False
    for db_page in pages:
        if not Path(db_page.pic_path).exists():
            return False
    return True


@router.get("/pages")
async def get_pages(
    db_chapter: DBChapter = Depends(db_utils.get_chapter_from_id),
    db_manga: Manga = Depends(db_utils.get_manga_from_chapter_id),
    session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    scraping_service: MSSService = Depends(db_utils.get_scraping_service_from_chapter),
    download_path: str = Depends(lambda: di["api"]["download_path"]),
    download_service: DownloadService = Depends(lambda: di[DownloadService]),
    async_service: AsyncService = Depends(lambda: di[AsyncService]),
):
    pages = await crud_service.get_items_by_same_attr(
        session, Page, "chapter_id", db_chapter.id
    )
    download_pages = not _check_pages_exist(pages)

    if download_pages:
        page_urls = await scraping_service.get_page_urls(db_chapter.page_url)

        download_path = (
            Path(download_path)
            / scraping_service.site.name
            / db_manga.name
            / db_chapter.title
        )
        page_gen = _download_pages(
            download_path,
            page_urls,
            db_chapter,
            session,
            download_service,
            async_service,
            crud_service,
        )
    else:
        page_gen = _create_async_gen_from_pages(pages)

    headers = {
        "Content-Type": "text/event-stream",
        "Crawled": "false" if pages else "true",
    }

    return StreamingResponse(_sse_img_gen(page_gen), headers=headers)
