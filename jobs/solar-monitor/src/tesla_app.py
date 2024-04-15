import asyncio
import httpx

from fastapi import FastAPI, Request, Response, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from kink import di
from logging import getLogger

from bootstrap import bootstrap_di, Controller
from models import SessionData, SolarPower, TeslaCommand
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
    session_data: SessionData | RedirectResponse = Depends(verify_user),
    controller: Controller = Depends(lambda: di[Controller]),
):
    if isinstance(session_data, RedirectResponse):
        return session_data
    return templates.TemplateResponse(
        "index.jinja",
        {
            "request": request,
            "user_id": request.cookies.get("user_session_id"),
            "vehicles": await tesla_service.get_vehicles(session_data),
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

# send tesla control to 192.168.2.50:8000
@app.post("/api/vehicles/command/{command}")
async def command(command: str, params: dict, tesla_service: TeslaService = Depends(lambda: di[TeslaService])):
    for t_command in TeslaCommand:
        if command == t_command.value:
            return await tesla_service.send_command(t_command, params)


async def get_current_solar(cookie: str, controller: Controller) -> SolarPower:
    while True:
        print(f"{controller}")
        if controller.is_stopped:
            print(f"{controller} going to break loop")
            break
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://monitoring.solaredge.com/services/powerflow/site/4150036/latest",
                headers={"Cookie": cookie},
            )
            result = response.json()
            solar_power = SolarPower(
                current_production=result["pv"]["currentPower"],
                current_consumption=result["load"]["currentPower"],
            )
            await asyncio.sleep(5)


@app.get("/api/solar-monitor-start", dependencies=[Depends(verify_user)])
async def solar_monitor(
    background_task: BackgroundTasks,
    cookie: str = Depends(lambda: di["cookie"]),
    controller: Controller = Depends(lambda: di[Controller]),
):
    background_task.add_task(get_current_solar, cookie, controller)
    return {"message": "Solar monitor started"}


@app.get("/api/solar-monitor-stop", dependencies=[Depends(verify_user)])
async def solar_monitor_stop(
    controller: Controller = Depends(lambda: di[Controller]),
):
    controller.stop()
    return {"message": "Solar monitor stopped"}
