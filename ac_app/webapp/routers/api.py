from collections import defaultdict
from dependency_injector.wiring import inject, Provide, Provider, providers
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import json
from logging import getLogger
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Iterable, Union

from async_service.async_service import AsyncService
from container import Container
from core.models.chapter import Chapter
from core.models.anime import AnimeBase, AnimeSimple
from core.models.episode import Episode
from core.models.manga import MangaBase, MangaSimple
from core.models.manga_index_type_enum import MangaIndexTypeEnum, m_types
from core.models.manga_site_enum import MangaSiteEnum
from core.models.meta import Meta
from core.scraping_service.anime_site_scraping_service import AnimeSiteScrapingService as ASSService
from core.scraping_service.anime1_scraping_service import Anime1ScrapingService
from core.scraping_service.manga_site_scraping_service import MangaSiteScrapingService as MSSService
from database.crud_service import CRUDService
from database.models import MangaSite, Manga, Chapter as DBChapter, Page, History, Anime, Episode as DBEpisode, AHistory
from download_service.download_service import DownloadService
from routers.user import get_user_id_from_session_data
from routers.utils import get_db_session
from sqlalchemy.exc import NoResultFound

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
async def _get_db_anime_from_id(
        anime_id: int,
        session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    db_anime = await crud_service.get_item_by_id(session, Anime, anime_id)
    if db_anime is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Anime does not exist"
        )
    return db_anime


@inject
async def _get_manga_site_from_manga(
        session: AsyncSession = Depends(get_db_session),
        db_manga: Manga = Depends(_get_db_manga_from_id),
        crud_service: CRUDService = Depends(
        Provide[Container.crud_service])) -> str:
    return await crud_service.get_attr_of_item_by_id(session, MangaSite, db_manga.manga_site_id, "name")


@inject
async def _get_manga_site_from_anime(
        session: AsyncSession = Depends(get_db_session),
        db_anime: Anime = Depends(_get_db_anime_from_id),
        crud_service: CRUDService = Depends(
        Provide[Container.crud_service])) -> str:
    return await crud_service.get_attr_of_item_by_id(session, MangaSite, db_anime.manga_site_id, "name")


@inject
def _get_scraping_service_from_site(
        site: MangaSiteEnum,
        ss_factory: FactoryAggregate[MSSService] = Depends(
        Provider[Container.scraping_service_factory])) -> Union[MSSService, ASSService]:
    return ss_factory(
        site)


@inject
def _get_scraping_service_from_manga(
        manga_site_name: str = Depends(_get_manga_site_from_manga)) -> MSSService:
    return _get_scraping_service_from_site(manga_site_name)


@inject
def _get_scraping_service_from_anime(
        manga_site_name: str = Depends(_get_manga_site_from_anime)) -> ASSService:
    return _get_scraping_service_from_site(manga_site_name)


@inject
async def _get_chapter_from_id(
        chapter_id: int,
        crud_service: CRUDService = Depends(
            Provide[Container.crud_service]),
        session: AsyncSession = Depends(get_db_session),):
    db_chapter = await crud_service.get_item_by_id(session, DBChapter, chapter_id)
    if not db_chapter:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Chapter does not exist"
        )
    return db_chapter


@inject
async def _get_episode_from_id(
        episode_id: int,
        crud_service: CRUDService = Depends(
            Provide[Container.crud_service]),
        session: AsyncSession = Depends(get_db_session),):
    db_episode = await crud_service.get_item_by_id(session, DBEpisode, episode_id)
    if not db_episode:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Episode does not exist"
        )
    return db_episode


@inject
async def _get_manga_from_chapter_id(db_chapter: DBChapter = Depends(_get_chapter_from_id),
                                     session: AsyncSession = Depends(get_db_session),) -> Manga:
    return await _get_db_manga_from_id(db_chapter.manga_id, session)


@inject
async def _get_anime_from_episode_id(db_episode: DBEpisode = Depends(_get_episode_from_id),
                                     session: AsyncSession = Depends(get_db_session),) -> Anime:
    return await _get_db_anime_from_id(db_episode.anime_id, session)


@inject
async def _get_scraping_service_from_chapter(
        db_manga: Manga = Depends(_get_manga_from_chapter_id),
        session: AsyncSession = Depends(get_db_session),) -> MSSService:
    manga_site_name = await _get_manga_site_from_manga(session, db_manga)
    return _get_scraping_service_from_manga(manga_site_name)


@inject
async def _get_scraping_service_from_episode(
        db_anime: Anime = Depends(_get_anime_from_episode_id),
        session: AsyncSession = Depends(get_db_session),) -> MSSService:
    manga_site_name = await _get_manga_site_from_anime(session, db_anime)
    return _get_scraping_service_from_manga(manga_site_name)


@inject
async def _search_manga(keyword: str,
                        crud_service: CRUDService = Depends(
                            Provide[Container.crud_service]),
                        manga_site_id: int = Depends(_get_manga_site_id),
                        session: AsyncSession = Depends(get_db_session),
                        scraping_service: MSSService = Depends(_get_scraping_service_from_site)):
    mangas = await scraping_service.search_manga(keyword)

    mangas = [{"name": manga.name, "url": str(manga.url), "manga_site_id": manga_site_id}
              for manga in mangas]
    mangas = await crud_service.bulk_create_objs_with_unique_key(session, Manga, mangas, "url")
    return [MangaBase.from_orm(manga) for manga in mangas]


@inject
async def _search_anime(keyword: str,
                        crud_service: CRUDService = Depends(
                            Provide[Container.crud_service]),
                        manga_site_id: int = Depends(_get_manga_site_id),
                        session: AsyncSession = Depends(get_db_session),
                        scraping_service: ASSService = Depends(_get_scraping_service_from_site)):
    animes = await scraping_service.search_anime(keyword)

    animes = [{"name": anime.name, "url": str(anime.url), "manga_site_id": manga_site_id,
               "eps": anime.eps, "year": anime.year, "season": anime.season, "sub": anime.season}
              for anime in animes]
    animes = await crud_service.bulk_create_objs_with_unique_key(session, Anime, animes, "url")
    return [AnimeBase.from_orm(anime) for anime in animes]


@router.get("/search",)
@inject
async def search(
        keyword: str,
        manga_site_id: int = Depends(_get_manga_site_id),
        session: AsyncSession = Depends(get_db_session),
        scraping_service: MSSService = Depends(_get_scraping_service_from_site)):

    if not isinstance(scraping_service, Anime1ScrapingService):
        return await _search_manga(keyword, manga_site_id=manga_site_id, session=session, scraping_service=scraping_service)
    else:
        return await _search_anime(keyword, manga_site_id=manga_site_id, session=session, scraping_service=scraping_service)


@router.get('/manga', response_model=MangaSimple)
@inject
async def get_manga(
        user_id: int = Depends(get_user_id_from_session_data),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),
        db_session: AsyncSession = Depends(get_db_session),
        db_manga: Manga = Depends(_get_db_manga_from_id),):
    manga = MangaSimple.from_orm(db_manga)
    q = select(History).where(History.manga_id ==
                              db_manga.id).where(History.user_id == user_id)
    try:
        history = (await db_session.execute(q)).one()[0]
        db_chapter = await crud_service.get_item_by_id(db_session, DBChapter, history.chapter_id)
        manga.last_read_chapter = Chapter.from_orm(db_chapter)
    except NoResultFound:
        logger.warning("no history is found")
    return manga


@router.get('/anime', response_model=AnimeSimple)
@inject
async def get_anime(
        user_id: int = Depends(get_user_id_from_session_data),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),
        db_session: AsyncSession = Depends(get_db_session),
        db_anime: Manga = Depends(_get_db_anime_from_id),):
    anime = AnimeSimple.from_orm(db_anime)
    q = select(AHistory).where(AHistory.anime_id ==
                               db_anime.id).where(AHistory.user_id == user_id)
    try:
        history = (await db_session.execute(q)).one()[0]
        db_episode = await crud_service.get_item_by_id(db_session, DBEpisode, history.episode_id)
        anime.last_read_episode = Episode.from_orm(db_episode)
    except NoResultFound:
        logger.warning("no history is found")
    return anime


@router.get('/episodes', response_model=List[Episode])
@inject
async def get_episodes(
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),
        session: AsyncSession = Depends(get_db_session),
        db_anime: Anime = Depends(_get_db_anime_from_id),
        scraping_service: ASSService = Depends(_get_scraping_service_from_anime)) -> List[Episode]:

    episodes = await scraping_service.get_index_page(db_anime)

    episodes_to_insert = [{"title": ep.title, "last_update": ep.last_update,
                           "data": ep.data, "anime_id": db_anime.id,
                           "manual_key": f"{db_anime.id}:{ep.title}"} for ep in episodes]

    db_episodes = await crud_service.bulk_create_objs_with_unique_key(
        session,
        DBEpisode,
        episodes_to_insert,
        "manual_key",
        update_attrs=["data"])
    return db_episodes


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
        download_path: str = Depends(
            Provide[Container.config.api.download_path]),
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


@router.get("/episode")
@inject
async def get_episode(
        db_episode: DBEpisode = Depends(_get_episode_from_id),
        db_anime: Anime = Depends(_get_anime_from_episode_id),
        scraping_service: ASSService = Depends(
            _get_scraping_service_from_episode),
        download_path: str = Depends(Provide[Container.config.api.download_path])):

    download_path = Path(download_path) / \
        scraping_service.site.name / db_anime.name / db_anime.season

    vid_url = await scraping_service.get_video_url(db_episode)

    download_service: DownloadService = scraping_service.download_service
    logger.info(f"{download_service.client.cookies=}")
    result = await download_service.download_vid(url=vid_url, download_path=download_path, filename=db_episode.title)
    return result


@router.get("/pages")
@inject
async def get_pages(
        db_chapter: DBChapter = Depends(_get_chapter_from_id),
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
