from fastapi import Request, Depends, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from dependency_injector.wiring import inject, Provide

from container import Container
from routers.auth import get_session_data
from session.session_verifier import SessionData

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
@inject
async def root(request: Request,
               session_data: SessionData = Depends(get_session_data),
               auth_server_url: str = Depends(Provide[Container.config.auth_server.url]),
               redirect_url: str = Depends(
                   Provide[Container.config.auth_server.redirect_url]),
               ):
    if not session_data:
        return RedirectResponse(f"{auth_server_url}/user/auth?redirect_url={redirect_url}")
    return templates.TemplateResponse("encrypt.html", {"request": request})
