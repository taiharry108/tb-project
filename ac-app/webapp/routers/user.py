from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Form
from kink import di
from logging import getLogger
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

from typing import List

from core.admin_service import update_meta, get_all_mangas_in_history, update_chapters
from core.models.anime import AnimeSimple
from core.models.chapter import Chapter
from core.models.episode import Episode
from core.models.manga import MangaSimple
from core.scraping_service import ScrapingServiceFactory
from database import CRUDService
from database.models import (
    User,
    Manga,
    History,
    Chapter as DBChapter,
    AHistory,
    Anime,
    Episode as DBEpisode,
)
from download_service import DownloadService
from routers.auth import get_session_data
from routers.utils import get_db_session, get_redirect_response
from session import SessionData

router = APIRouter()

logger = getLogger(__name__)


async def get_user_id_from_session_data(
    session_data: SessionData = Depends(get_session_data),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        user_id = await crud_service.get_id_by_attr(
            db_session, User, "email", session_data.username
        )
    except AttributeError:
        user_id = None
    return user_id


async def get_is_active_from_session_data(
    session_data: SessionData = Depends(get_session_data),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        is_active = (
            await crud_service.get_item_by_attrs(
                db_session, User, email=session_data.username
            )
        ).is_active

    except AttributeError:
        is_active = None
    return is_active


@router.get("/a_history", response_model=List[AnimeSimple])
async def get_a_history(
    user_id: int = Depends(get_user_id_from_session_data),
    redirect_response=Depends(get_redirect_response),
    db_session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
):
    if not user_id:
        return redirect_response
    history = await crud_service.get_attr_of_item_by_id(
        db_session, User, user_id, "history_animes", "history_animes"
    )
    history = sorted(history, key=lambda item: item.last_added, reverse=True)

    animes = await crud_service.get_items_by_ids(
        db_session, Anime, [h.anime_id for h in history]
    )
    anime_ids = [item.anime_id for item in history]
    episodes = await crud_service.get_items_by_ids(
        db_session, DBEpisode, [h.episode_id for h in history]
    )
    simple_animes = {anime.id: AnimeSimple.model_validate(anime) for anime in animes}
    for episode, hist in zip(episodes, history):
        anime_id = episode.anime_id
        simple_animes[anime_id].last_read_episode = Episode.model_validate(episode)
        simple_animes[anime_id].last_added = hist.last_added

    return [simple_animes[anime_id] for anime_id in anime_ids]


@router.get("/history", response_model=List[MangaSimple])
async def get_history(
    time_sort: bool = False,
    user_id: int = Depends(get_user_id_from_session_data),    
    redirect_response=Depends(get_redirect_response),
    db_session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
):
    if not user_id:
        return redirect_response
    history = await crud_service.get_attr_of_item_by_id(
        db_session, User, user_id, "history_mangas", "history_mangas"
    )
    history = sorted(history, key=lambda item: item.last_added, reverse=True)

    mangas = await crud_service.get_items_by_ids(
        db_session, Manga, [h.manga_id for h in history]
    )
    manga_ids = [item.manga_id for item in history]
    chapters = await crud_service.get_items_by_ids(
        db_session, DBChapter, [h.chapter_id for h in history]
    )
    simple_mangas = {manga.id: MangaSimple.model_validate(manga) for manga in mangas}
    for chapter, hist in zip(chapters, history):
        manga_id = chapter.manga_id
        simple_mangas[manga_id].last_read_chapter = Chapter.model_validate(chapter)
        simple_mangas[manga_id].last_added = hist.last_added

    logger.info("going to return")

    if not time_sort:
        return [simple_mangas[manga_id] for manga_id in manga_ids]
    else:
        return list(sorted(simple_mangas.values(), key=lambda item: item.last_update, reverse=True))


@router.post(
    "/a_history",
)
async def add_a_history(
    anime_id: int = Form(),
    user_id: int = Depends(get_user_id_from_session_data),
    redirect_response=Depends(get_redirect_response),
    db_session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
):
    if not user_id:
        return redirect_response

    async def work(session, db_user, db_anime):
        q = (
            select(AHistory)
            .where(AHistory.anime_id == anime_id)
            .where(AHistory.user_id == user_id)
        )
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
        except NoResultFound:
            db_hist = None
        if db_hist is None:
            db_hist = AHistory(last_added=datetime.now(), user=db_user, anime=db_anime)
            session.add(db_hist)
        else:
            db_hist.last_added = datetime.now()
        await session.commit()
        return db_hist

    history = await crud_service.item_obj_iteraction(
        db_session, User, Anime, user_id, anime_id, work
    )
    if history:
        return {"user_id": user_id, "anime_id": anime_id}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Anime does not exist"
    )


@router.post(
    "/history",
)
async def add_history(
    manga_id: int = Form(),
    user_id: int = Depends(get_user_id_from_session_data),
    redirect_response=Depends(get_redirect_response),
    db_session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
):
    if not user_id:
        return redirect_response

    async def work(session, db_user, db_manga):
        q = (
            select(History)
            .where(History.manga_id == manga_id)
            .where(History.user_id == user_id)
        )
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
        except NoResultFound:
            db_hist = None
        if db_hist is None:
            db_hist = History(last_added=datetime.now(), user=db_user, manga=db_manga)
            session.add(db_hist)
        else:
            db_hist.last_added = datetime.now()
        await session.commit()
        return db_hist

    history = await crud_service.item_obj_iteraction(
        db_session, User, Manga, user_id, manga_id, work
    )
    if history:
        return {"user_id": user_id, "manga_id": manga_id}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Manga does not exist"
    )


@router.put(
    "/a_history",
)
async def update_a_history(
    anime_id: int = Form(),
    episode_id: int = Form(),
    user_id: int = Depends(get_user_id_from_session_data),
    redirect_response=Depends(get_redirect_response),
    db_session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
):
    if not user_id:
        return redirect_response

    async def work(session, db_user, db_anime):
        q = (
            select(AHistory)
            .where(AHistory.anime_id == anime_id)
            .where(AHistory.user_id == user_id)
        )
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
            db_hist.episode_id = episode_id
            await session.commit()
        except (NoResultFound, IntegrityError):
            db_hist = None

        return db_hist

    history = await crud_service.item_obj_iteraction(
        db_session, User, Anime, user_id, anime_id, work
    )
    if history:
        return {"user_id": user_id, "anime_id": anime_id, "episode_id": episode_id}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Anime does not exist"
    )


@router.put(
    "/history",
)
async def update_history(
    manga_id: int = Form(),
    chapter_id: int = Form(),
    user_id: int = Depends(get_user_id_from_session_data),
    redirect_response=Depends(get_redirect_response),
    db_session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
):
    if not user_id:
        return redirect_response

    async def work(session, db_user, db_manga):
        q = (
            select(History)
            .where(History.manga_id == manga_id)
            .where(History.user_id == user_id)
        )
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
            db_hist.chapter_id = chapter_id
            await session.commit()
        except (NoResultFound, IntegrityError):
            db_hist = None
        return db_hist

    history = await crud_service.item_obj_iteraction(
        db_session, User, Manga, user_id, manga_id, work
    )
    if history:
        return {"user_id": user_id, "manga_id": manga_id, "chapter_id": chapter_id}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Manga does not exist"
    )


@router.delete(
    "/a_history",
)
async def del_a_history(
    anime_id: int = Form(),
    user_id: int = Depends(get_user_id_from_session_data),
    redirect_response=Depends(get_redirect_response),
    db_session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
):
    if not user_id:
        return redirect_response

    async def work(session, db_user, db_anime):
        q = (
            select(AHistory)
            .where(AHistory.anime_id == anime_id)
            .where(AHistory.user_id == user_id)
        )
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
        except NoResultFound:
            db_hist = None
        if db_hist is not None:
            await session.delete(db_hist)
            await session.commit()
            return True
        else:
            return False

    result = await crud_service.item_obj_iteraction(
        db_session, User, Anime, user_id, anime_id, work
    )
    if result:
        return {"success": True}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Anime does not exist"
    )


@router.delete(
    "/history",
)
async def del_history(
    manga_id: int = Form(),
    user_id: int = Depends(get_user_id_from_session_data),
    redirect_response=Depends(get_redirect_response),
    db_session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
):
    if not user_id:
        return redirect_response

    async def work(session, db_user, db_manga):
        q = (
            select(History)
            .where(History.manga_id == manga_id)
            .where(History.user_id == user_id)
        )
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
        except NoResultFound:
            db_hist = None
        if db_hist is not None:
            await session.delete(db_hist)
            await session.commit()
            return True
        else:
            return False

    result = await crud_service.item_obj_iteraction(
        db_session, User, Manga, user_id, manga_id, work
    )
    if result:
        return {"success": True}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Manga does not exist"
    )


@router.get(
    "/admin-update",
)
async def admin_update(
    is_active: bool = Depends(get_is_active_from_session_data),
    redirect_response=Depends(get_redirect_response),
    db_engine: AsyncEngine = Depends(lambda: di[AsyncEngine]),
    download_service: DownloadService = Depends(lambda: di[DownloadService]),
    download_path: str = Depends(lambda: di["api"]["download_path"]),
    ss_factory: ScrapingServiceFactory = Depends(lambda: di[ScrapingServiceFactory]),
):
    if not is_active:
        return redirect_response

    mangas = await get_all_mangas_in_history(db_engine)
    metas = await update_meta(
        mangas, ss_factory, download_service, download_path, db_engine
    )
    chapters = await update_chapters(mangas, ss_factory, db_engine)
    return True
