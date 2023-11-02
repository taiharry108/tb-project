from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from kink import di
from sqlalchemy.ext.asyncio import AsyncSession

from database import CRUDService
from database.models import Manga, Anime, Chapter, User
from routers.auth import get_session_data
from routers.utils import get_db_session, get_redirect_response
from session import SessionData


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def main_page(
    request: Request,
    session_data: SessionData = Depends(get_session_data),
    redirect_response=Depends(get_redirect_response),
):
    if not session_data:
        return redirect_response
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/manga")
async def manga_page(
    request: Request,
    manga_id: int,
    session_data: SessionData = Depends(get_session_data),
    redirect_response=Depends(get_redirect_response),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    db_session: AsyncSession = Depends(get_db_session),
):
    if not session_data:
        return redirect_response

    manga_name = await crud_service.get_attr_of_item_by_id(
        db_session, Manga, manga_id, "name"
    )

    return templates.TemplateResponse(
        "manga.html",
        {"request": request, "manga_id": manga_id, "manga_name": manga_name},
    )


@router.get("/history")
async def history_page(
    request: Request,
    session_data: SessionData = Depends(get_session_data),
    redirect_response=Depends(get_redirect_response),
):
    if not session_data:
        return redirect_response
    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
        },
    )


@router.get("/anime")
async def anime_page(
    request: Request,
    anime_id: int,
    session_data: SessionData = Depends(get_session_data),
    redirect_response=Depends(get_redirect_response),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    db_session: AsyncSession = Depends(get_db_session),
):
    if not session_data:
        return redirect_response

    anime_name = await crud_service.get_attr_of_item_by_id(
        db_session, Anime, anime_id, "name"
    )

    return templates.TemplateResponse(
        "anime.html",
        {"request": request, "anime_id": anime_id, "anime_name": anime_name},
    )


async def get_user_id_from_session_data(
    session_data: SessionData = Depends(get_session_data),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        user_id = await crud_service.get_id_by_attr(
            db_session, User, "email", session_data.username
        )
    except AttributeError as ex:
        logger.error(ex)
        user_id = None
    return user_id


@router.get("/chapter")
async def chapter_page(
    request: Request,
    chapter_id: int,
    session_data: SessionData = Depends(get_session_data),
    redirect_response=Depends(get_redirect_response),
    crud_service: CRUDService = Depends(lambda: di[CRUDService]),
    db_session: AsyncSession = Depends(get_db_session),
):
    if not session_data:
        return redirect_response

    chapter_title = await crud_service.get_attr_of_item_by_id(
        db_session, Chapter, chapter_id, "title"
    )
    manga_id = await crud_service.get_attr_of_item_by_id(
        db_session, Chapter, chapter_id, "manga_id"
    )

    return templates.TemplateResponse(
        "chapter.html",
        {
            "request": request,
            "chapter_title": chapter_title,
            "manga_id": manga_id,
            "chapter_id": chapter_id,
        },
    )
