from fastapi import APIRouter, Depends, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from kink import di

from models import SessionData, TeslaCommand
from routers.auth import verify_user
from services import TeslaService, SolarMonitorService
from services.solar_monitor_service import CancellationToken


router = APIRouter()


@router.get("/vehicles/{vehicle_id}/wakeup", dependencies=[Depends(verify_user)])
async def vehicles(
    vehicle_id: int,
    request: Request,
    tesla_service: TeslaService = Depends(lambda: di[TeslaService]),
):
    session_data = request.state.session_data
    result = await tesla_service.wake_up(session_data, vehicle_id)
    return RedirectResponse("/")


@router.post("/vehicles/command/{command}", dependencies=[Depends(verify_user)])
async def command(
    command: TeslaCommand,
    params: dict,
    tesla_service: TeslaService = Depends(lambda: di[TeslaService]),
):
    return await tesla_service.send_command(command, params)


@router.get("/solar-monitor-start", dependencies=[Depends(verify_user)])
async def solar_monitor(
    background_task: BackgroundTasks,
    cookie: str = Depends(lambda: di["cookie"]),
    cancel_token: CancellationToken = Depends(lambda: di[CancellationToken]),
    solar_monitor_service: SolarMonitorService = Depends(
        lambda: di[SolarMonitorService]
    ),
    tesla_service: TeslaService = Depends(lambda: di[TeslaService]),
):
    # await tesla_service.send_command(TeslaCommand.CHARGING_STOP, {})
    tesla_service.is_charging = True
    tesla_service.charging_amps = 16
    # background_task.add_task(
    #     solar_monitor_service.monitor_solar,
    #     cookie,
    #     [tesla_service.adjust_current],
    #     cancel_token,
    # )
    return {"message": "Solar monitor started"}


@router.get("/solar-monitor-stop", dependencies=[Depends(verify_user)])
async def solar_monitor_stop(
    cancel_token: CancellationToken = Depends(lambda: di[CancellationToken]),
):
    cancel_token.stop()
    return {"message": "Solar monitor stopped"}
