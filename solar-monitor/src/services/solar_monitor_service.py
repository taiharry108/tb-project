import asyncio
import httpx

from typing import Callable, Awaitable

from models import SolarPower

class CancellationToken:
    def __init__(self):
        self.is_stopped = False

    def stop(self):
        self.is_stopped = True

    def __repr__(self):
        return f"CancellationToken({id(self)}) {self.is_stopped}"



class SolarMonitorService:
    async def monitor_solar(self, cookie: str, callables: list[Callable[[float], Awaitable[None]]], cancel_token: CancellationToken = None):
        while True:
            if cancel_token and cancel_token.is_stopped:
                break
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        "https://monitoring.solaredge.com/services/powerflow/site/4150036/latest",
                        headers={"Cookie": cookie},
                    )
                    result = response.json()
                except Exception as e:
                    print(e)
                    await asyncio.sleep(5)
                    continue
                solar_power = SolarPower(
                    current_production=result["pv"]["currentPower"],
                    current_consumption=result["load"]["currentPower"],
                )
                net_power = solar_power.net
                for callback in callables:
                    await callback(net_power)

                await asyncio.sleep(5)
