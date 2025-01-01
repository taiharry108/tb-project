from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from kink import di
from logging import getLogger

from bootstrap import bootstrap_di
from routers import auth_router, api_router
from routers.auth import verify_user
from services import TeslaService

bootstrap_di()

logger = getLogger(__name__)

app = FastAPI()

app.mount("/auth", auth_router)
app.mount("/api", api_router)
templates = Jinja2Templates(directory="templates")


@app.get("/.well-known/appspecific/com.tesla.3p.public-key.pem")
async def well_known():
    with open("./static/public.pem") as f:
        return PlainTextResponse(f.read())


@app.get("/", dependencies=[Depends(verify_user)])
async def main_page(
    request: Request,
    tesla_service: TeslaService = Depends(lambda: di[TeslaService]),
):
    session_data = request.state.session_data
    vehicles = await tesla_service.get_vehicles(session_data)
    return templates.TemplateResponse(
        "index.jinja",
        {
            "request": request,
            "user_id": request.cookies.get("user_session_id"),
            "vehicles": vehicles,
            "vehicle_data": await tesla_service.get_vehicle_data(
                session_data, vehicles[0].id
            ),
        },
    )
