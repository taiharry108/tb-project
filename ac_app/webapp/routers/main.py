from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/{manga_id}")
def manga_page(request: Request, manga_id: int):
    return templates.TemplateResponse("manga.html", {"request": request, "manga_id": manga_id})
