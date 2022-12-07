from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from container import Container
from database.crud_service import CRUDService
from database.models import Manga, Anime, Chapter
from routers.auth import get_session_data
from routers.utils import get_db_session
from session.session_verifier import SessionData
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@inject
async def get_redirect_response(auth_server_url: str = Depends(
        Provide[Container.config.auth_server.url]),
        redirect_url: str = Depends(
        Provide[Container.config.auth_server.redirect_url]),):
    return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")


@router.get("/")
@inject
def main_page(request: Request,
              session_data: SessionData = Depends(get_session_data),
              redirect_response: RedirectResponse = Depends(get_redirect_response),):
    if not session_data:
        return redirect_response
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/manga")
@inject
async def manga_page(request: Request, manga_id: int,
                     session_data: SessionData = Depends(get_session_data),
                     redirect_response: RedirectResponse = Depends(
                         get_redirect_response),
                     crud_service: CRUDService = Depends(
                         Provide[Container.crud_service]),
                     db_session: AsyncSession = Depends(get_db_session)
                     ):
    if not session_data:
        return redirect_response

    manga_name = await crud_service.get_attr_of_item_by_id(db_session, Manga, manga_id, "name")

    return templates.TemplateResponse("manga.html", {"request": request, "manga_id": manga_id, "manga_name": manga_name})


@router.get("/history")
@inject
async def history_page(request: Request,
                       session_data: SessionData = Depends(get_session_data),
                       redirect_response: RedirectResponse = Depends(
                           get_redirect_response),
                       ):
    if not session_data:
        return redirect_response
    return templates.TemplateResponse("history.html", {"request": request, })


@router.get("/anime")
@inject
async def anime_page(request: Request, anime_id: int,
                     session_data: SessionData = Depends(get_session_data),
                     redirect_response: RedirectResponse = Depends(
                         get_redirect_response),
                     crud_service: CRUDService = Depends(
                         Provide[Container.crud_service]),
                     db_session: AsyncSession = Depends(get_db_session)
                     ):
    if not session_data:
        return redirect_response

    anime_name = await crud_service.get_attr_of_item_by_id(db_session, Anime, anime_id, "name")

    return templates.TemplateResponse("anime.html", {"request": request, "anime_id": anime_id, "anime_name": anime_name})


@router.get("/chapter")
@inject
async def chapter_page(request: Request, chapter_id: int,
                        session_data: SessionData = Depends(get_session_data),
                     redirect_response: RedirectResponse = Depends(
                         get_redirect_response),
                     crud_service: CRUDService = Depends(
                         Provide[Container.crud_service]),
                     db_session: AsyncSession = Depends(get_db_session)
                     ):
    if not session_data:
        return redirect_response

    chapter_title = await crud_service.get_attr_of_item_by_id(db_session, Chapter, chapter_id, "title")

    return templates.TemplateResponse("chapter.html", {"request": request, "chapter_title": chapter_title})