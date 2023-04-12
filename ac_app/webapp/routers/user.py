from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import RedirectResponse
from logging import getLogger
from typing import List

from container import Container
from core.models.anime import AnimeSimple
from core.models.chapter import Chapter
from core.models.episode import Episode
from core.models.manga import MangaSimple
from database.crud_service import CRUDService
from database.models import User, Manga, History, Chapter as DBChapter, AHistory, Anime, Episode as DBEpisode
from datetime import datetime
from routers.auth import get_session_data
from routers.utils import get_db_session
from session.session_verifier import SessionData
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

logger = getLogger(__name__)


@inject
async def get_user_id_from_session_data(
    session_data: SessionData = Depends(get_session_data),
    crud_service: CRUDService = Depends(Provide[Container.crud_service]),
    db_session: AsyncSession = Depends(get_db_session)
):
    try:
        user_id = await crud_service.get_id_by_attr(db_session, User, "email", session_data.username)
    except AttributeError:
        user_id = None
    return user_id


@router.get("/a_history", response_model=List[AnimeSimple])
@inject
async def get_a_history(
        user_id: int = Depends(get_user_id_from_session_data),
        auth_server_url: str = Depends(
            Provide[Container.config.auth_server.url]),
        redirect_url: str = Depends(
            Provide[Container.config.auth_server.redirect_url]),
        db_session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    if not user_id:
        return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")
    history = await crud_service.get_attr_of_item_by_id(db_session, User, user_id, "history_animes", "history_animes")
    history = sorted(history, key=lambda item: item.last_added, reverse=True)

    animes = await crud_service.get_items_by_ids(db_session, Anime, [h.anime_id for h in history])
    anime_ids = [item.anime_id for item in history]
    episodes = await crud_service.get_items_by_ids(db_session, DBEpisode, [h.episode_id for h in history])
    simple_animes = {anime.id: AnimeSimple.from_orm(anime) for anime in animes}
    for episode, hist in zip(episodes, history):
        anime_id = episode.anime_id
        simple_animes[anime_id].last_read_episode = Episode.from_orm(episode)
        simple_animes[anime_id].last_added = hist.last_added

    return [simple_animes[anime_id] for anime_id in anime_ids]


@router.get("/history", response_model=List[MangaSimple])
@inject
async def get_history(
        user_id: int = Depends(get_user_id_from_session_data),
        auth_server_url: str = Depends(
            Provide[Container.config.auth_server.url]),
        redirect_url: str = Depends(
            Provide[Container.config.auth_server.redirect_url]),
        db_session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    if not user_id:
        return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")
    history = await crud_service.get_attr_of_item_by_id(db_session, User, user_id, "history_mangas", "history_mangas")
    history = sorted(history, key=lambda item: item.last_added, reverse=True)

    mangas = await crud_service.get_items_by_ids(db_session, Manga, [h.manga_id for h in history])
    manga_ids = [item.manga_id for item in history]
    chapters = await crud_service.get_items_by_ids(db_session, DBChapter, [h.chapter_id for h in history])
    simple_mangas = {manga.id: MangaSimple.from_orm(manga) for manga in mangas}
    for chapter, hist in zip(chapters, history):
        manga_id = chapter.manga_id
        simple_mangas[manga_id].last_read_chapter = Chapter.from_orm(chapter)
        simple_mangas[manga_id].last_added = hist.last_added

    logger.info("going to return")

    return [simple_mangas[manga_id] for manga_id in manga_ids]


@router.post("/a_history",)
@inject
async def add_a_history(
        anime_id: int = Form(),
        user_id: int = Depends(get_user_id_from_session_data),
        auth_server_url: str = Depends(
            Provide[Container.config.auth_server.url]),
        redirect_url: str = Depends(
            Provide[Container.config.auth_server.redirect_url]),
        db_session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    if not user_id:
        return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")

    async def work(session, db_user, db_anime):
        q = select(AHistory).where(AHistory.anime_id ==
                                   anime_id).where(AHistory.user_id == user_id)
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
        except NoResultFound:
            db_hist = None
        if db_hist is None:
            db_hist = AHistory(last_added=datetime.now(),
                               user=db_user, anime=db_anime)
            session.add(db_hist)
        else:
            db_hist.last_added = datetime.now()
        await session.commit()
        return db_hist

    history = await crud_service.item_obj_iteraction(db_session, User, Anime, user_id, anime_id, work)
    if history:
        return {"user_id": user_id, "anime_id": anime_id}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Anime does not exist"
    )


@router.post("/history",)
@inject
async def add_history(
        manga_id: int = Form(),
        user_id: int = Depends(get_user_id_from_session_data),
        auth_server_url: str = Depends(
            Provide[Container.config.auth_server.url]),
        redirect_url: str = Depends(
            Provide[Container.config.auth_server.redirect_url]),
        db_session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    if not user_id:
        return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")

    async def work(session, db_user, db_manga):
        q = select(History).where(History.manga_id ==
                                  manga_id).where(History.user_id == user_id)
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
        except NoResultFound:
            db_hist = None
        if db_hist is None:
            db_hist = History(last_added=datetime.now(),
                              user=db_user, manga=db_manga)
            session.add(db_hist)
        else:
            db_hist.last_added = datetime.now()
        await session.commit()
        return db_hist

    history = await crud_service.item_obj_iteraction(db_session, User, Manga, user_id, manga_id, work)
    if history:
        return {"user_id": user_id, "manga_id": manga_id}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Manga does not exist"
    )


@router.put("/a_history",)
@inject
async def update_a_history(
        anime_id: int = Form(),
        episode_id: int = Form(),
        user_id: int = Depends(get_user_id_from_session_data),
        auth_server_url: str = Depends(
            Provide[Container.config.auth_server.url]),
        redirect_url: str = Depends(
            Provide[Container.config.auth_server.redirect_url]),
        db_session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    if not user_id:
        return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")

    async def work(session, db_user, db_anime):
        q = select(AHistory).where(AHistory.anime_id ==
                                   anime_id).where(AHistory.user_id == user_id)
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
            db_hist.episode_id = episode_id
            await session.commit()
        except (NoResultFound, IntegrityError):
            db_hist = None

        return db_hist

    history = await crud_service.item_obj_iteraction(db_session, User, Anime, user_id, anime_id, work)
    if history:
        return {"user_id": user_id, "anime_id": anime_id, "episode_id": episode_id}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Anime does not exist"
    )


@router.put("/history",)
@inject
async def update_history(
        manga_id: int = Form(),
        chapter_id: int = Form(),
        user_id: int = Depends(get_user_id_from_session_data),
        auth_server_url: str = Depends(
            Provide[Container.config.auth_server.url]),
        redirect_url: str = Depends(
            Provide[Container.config.auth_server.redirect_url]),
        db_session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    if not user_id:
        return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")

    async def work(session, db_user, db_manga):
        q = select(History).where(History.manga_id ==
                                  manga_id).where(History.user_id == user_id)
        db_hist = await session.execute(q)
        try:
            db_hist = db_hist.one()[0]
            db_hist.chapter_id = chapter_id
            await session.commit()
        except (NoResultFound, IntegrityError):
            db_hist = None
        return db_hist

    history = await crud_service.item_obj_iteraction(db_session, User, Manga, user_id, manga_id, work)
    if history:
        return {"user_id": user_id, "manga_id": manga_id, "chapter_id": chapter_id}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Manga does not exist"
    )

@router.delete("/a_history",)
@inject
async def del_a_history(
        anime_id: int = Form(),
        user_id: int = Depends(get_user_id_from_session_data),
        auth_server_url: str = Depends(
            Provide[Container.config.auth_server.url]),
        redirect_url: str = Depends(
            Provide[Container.config.auth_server.redirect_url]),
        db_session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    if not user_id:
        return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")

    async def work(session, db_user, db_anime):
        q = select(AHistory).where(AHistory.anime_id ==
                                  anime_id).where(AHistory.user_id == user_id)
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

    result = await crud_service.item_obj_iteraction(db_session, User, Anime, user_id, anime_id, work)
    if result:
        return {"success": True}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Anime does not exist"
    )

@router.delete("/history",)
@inject
async def del_history(
        manga_id: int = Form(),
        user_id: int = Depends(get_user_id_from_session_data),
        auth_server_url: str = Depends(
            Provide[Container.config.auth_server.url]),
        redirect_url: str = Depends(
            Provide[Container.config.auth_server.redirect_url]),
        db_session: AsyncSession = Depends(get_db_session),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    if not user_id:
        return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")

    async def work(session, db_user, db_manga):
        q = select(History).where(History.manga_id ==
                                  manga_id).where(History.user_id == user_id)
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

    result = await crud_service.item_obj_iteraction(db_session, User, Manga, user_id, manga_id, work)
    if result:
        return {"success": True}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Manga does not exist"
    )
