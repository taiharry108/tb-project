from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from container import Container

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
def main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
