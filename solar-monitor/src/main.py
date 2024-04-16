import asyncio
import httpx
import os
import sys

from dataclasses import dataclass
from dotenv import load_dotenv
from logging import getLogger, config
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager
from meross_iot.device_factory import Mts100v3Valve

config.fileConfig("logging.conf", disable_existing_loggers=False)

logger = getLogger(__name__)

load_dotenv()

COOKIE = os.getenv("COOKIE")
MEROSS_USERNAME = os.getenv("MEROSS_USERNAME")
MEROSS_PASSWORD = os.getenv("MEROSS_PASSWORD")
MEROSS_DEVICE_NAME = os.getenv("MEROSS_DEVICE_NAME")
SLEEP_TIME = int(os.getenv("SLEEP_TIME")) or 5

@dataclass
class SolarPower:
    current_production: int
    current_consumption: int

    def __repr__(self):
        return f"Net: {self.net:.2f} ({self.current_production:.2f} - {self.current_consumption:.2f})"

    """A property for calculating the net power"""
    @property
    def net(self):
        return self.current_production - self.current_consumption


async def get_meross_device(name: str) -> Mts100v3Valve | None:
    http_api_client = await MerossHttpClient.async_from_user_password(
        api_base_url="https://iotx-us.meross.com",
        email=MEROSS_USERNAME,
        password=MEROSS_PASSWORD,
    )

    # Setup and start the device manager
    manager = MerossManager(http_client=http_api_client)
    await manager.async_init()

    # Retrieve all the MSS310 devices that are registered on this account
    await manager.async_device_discovery()
    plugs: list[Mts100v3Valve] = manager.find_devices(device_type="mss110")

    for plug in plugs:
        if plug.name == name:
            return plug
    return None


async def get_current_solar() -> SolarPower:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://monitoring.solaredge.com/services/powerflow/site/4150036/latest",
            headers={"Cookie": COOKIE},
        )
        result = response.json()
        return SolarPower(
            current_production=result["pv"]["currentPower"],
            current_consumption=result["load"]["currentPower"],
        )


async def main():
    device = await get_meross_device(MEROSS_DEVICE_NAME)

    if not device:
        logger.error(f"Device {MEROSS_DEVICE_NAME} not found")
        sys.exit(1)

    while True:
        await device.async_update()
        current_solar = await get_current_solar()

        # if datetime.now().hour >= EXIT_TIME:
        #     logger.info("It's late, exiting")
        #     sys.exit(0)

        logger.info(f"{current_solar}, {device.name} is on: {device.is_on()}")
        is_on = device.is_on()
        if is_on and current_solar.net < 0:
            await device.async_turn_off()
        elif not is_on and current_solar.net > 2:
            await device.async_turn_on()

        await asyncio.sleep(SLEEP_TIME)


asyncio.run(main())
