from fastapi import FastAPI, Request, Response, Depends
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from kink import di
from logging import getLogger

from bootstrap import bootstrap_di
from models import SessionData
from routers import auth_router
from routers.auth import verify_user
from services import TeslaService, RedisService

bootstrap_di()

logger = getLogger(__name__)

app = FastAPI()

app.mount("/auth", auth_router)
templates = Jinja2Templates(directory="templates")


@app.get("/.well-known/appspecific/com.tesla.3p.public-key.pem")
async def well_known():
    with open("./static/public.pem") as f:
        return PlainTextResponse(f.read())


@app.get("/", dependencies=[Depends(verify_user)])
async def main_page(
    request: Request,
    redis_service: RedisService = Depends(lambda: di[RedisService]),
    tesla_service: TeslaService = Depends(lambda: di[TeslaService]),
    session_data: SessionData=Depends(verify_user),
):
    user_session_id = request.cookies.get("user_session_id")
    return templates.TemplateResponse(
        "index.jinja",
        {
            "request": request,
            "user_id": user_session_id,
            "vehicles": await tesla_service.get_vehicles(session_data),
        },
    )


@app.get("/api/vehicles/{vehicle_id}/wakeup")
async def vehicles(
    vehicle_id: int,
    request: Request,
    redis_service: RedisService = Depends(lambda: di[RedisService]),
    tesla_service: TeslaService = Depends(lambda: di[TeslaService]),
    session_data: SessionData = Depends(verify_user),
):
    user_session_id = request.cookies.get("user_session_id")

    if not user_session_id:
        return RedirectResponse("/auth/login")

    if session_data := redis_service.get_session_data(user_session_id):
        if session_data.is_expired:
            return RedirectResponse("/auth/refresh")
    else:
        return RedirectResponse("/auth/login")

    return vehicle_id
