from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import RedirectResponse
from typing import List

from container import Container
from core.models.chapter import Chapter
from core.models.manga import MangaSimple
from database.crud_service import CRUDService
from database.models import User, Manga, History, Chapter as DBChapter
from datetime import datetime
from routers.auth import get_session_data
from routers.utils import get_db_session
from session.session_verifier import SessionData
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


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
    for chapter in chapters:
        manga_id = chapter.manga_id
        simple_mangas[manga_id].last_read_chapter = Chapter.from_orm(chapter)

    return [simple_mangas[manga_id] for manga_id in manga_ids]


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
        except NoResultFound:
            db_hist = None
        if db_hist is not None:
            db_hist.chapter_id = chapter_id
            await session.commit()
        return db_hist

    history = await crud_service.item_obj_iteraction(db_session, User, Manga, user_id, manga_id, work)
    if history:
        return {"user_id": user_id, "manga_id": manga_id, "chapter_id": chapter_id}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Manga does not exist"
    )


@router.delete("/history",)
@inject
async def del_history(
        manga_id: int,
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
