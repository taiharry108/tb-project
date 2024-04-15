import json

from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from kink import di
from logging import getLogger

from bootstrap import bootstrap_di
from models import SessionData, TeslaCommand
from routers import auth_router
from routers.auth import verify_user
from services import TeslaService, RedisService, SolarMonitorService
from services.solar_monitor_service import CancellationToken

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
    session_data: SessionData | RedirectResponse = Depends(verify_user),
):
    if isinstance(session_data, RedirectResponse):
        return session_data
    vehicles = await tesla_service.get_vehicles(session_data)
    return templates.TemplateResponse(
        "index.jinja",
        {
            "request": request,
            "user_id": request.cookies.get("user_session_id"),
            "vehicles": vehicles,
            "vehicle_data": await tesla_service.get_vehicle_data(session_data, vehicles[0].id),
        },
    )

@app.get("/api/vehicles/{vehicle_id}/wakeup", dependencies=[Depends(verify_user)])
async def vehicles(
    vehicle_id: int,
    request: Request,
    redis_service: RedisService = Depends(lambda: di[RedisService]),
    tesla_service: TeslaService = Depends(lambda: di[TeslaService]),
    session_data: SessionData = Depends(verify_user),
):
    result = await tesla_service.wake_up(session_data, vehicle_id)
    return RedirectResponse("/")

@app.post("/api/vehicles/command/{command}")
async def command(command: TeslaCommand, params: dict, tesla_service: TeslaService = Depends(lambda: di[TeslaService])):
    return await tesla_service.send_command(command, params)


@app.get("/api/solar-monitor-start", dependencies=[Depends(verify_user)])
async def solar_monitor(
    background_task: BackgroundTasks,
    cookie: str = Depends(lambda: di["cookie"]),
    cancel_token: CancellationToken = Depends(lambda: di[CancellationToken]),
    solar_monitor_service: SolarMonitorService = Depends(lambda: di[SolarMonitorService]),
    tesla_service: TeslaService = Depends(lambda: di[TeslaService])
):
    # await tesla_service.send_command(TeslaCommand.CHARGING_STOP, {})
    tesla_service.is_charging = True
    tesla_service.charging_amps = 16
    background_task.add_task(solar_monitor_service.monitor_solar, cookie, [tesla_service.adjust_current], cancel_token)
    return {"message": "Solar monitor started"}


@app.get("/api/solar-monitor-stop", dependencies=[Depends(verify_user)])
async def solar_monitor_stop(
    cancel_token: CancellationToken = Depends(lambda: di[CancellationToken]),
):
    cancel_token.stop()
    return {"message": "Solar monitor stopped"}
