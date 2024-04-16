import os

from dotenv import load_dotenv
from kink import di
from redis import Redis

from client import MockTeslaClient, TeslaClient
from services import RedisService, TeslaService, SolarMonitorService
from services.solar_monitor_service import CancellationToken

load_dotenv()


def bootstrap_di() -> None:
    di[Redis] = lambda di: Redis(os.getenv("REDIS_HOST"))
    di[RedisService] = lambda di: RedisService(os.getenv("APP_NAME"), di[Redis])
    di[MockTeslaClient] = MockTeslaClient()
    di[TeslaClient] = TeslaClient(
        os.getenv("TESLA_AUTH_API_DOMAIN"),
        os.getenv("TESLA_FLEET_API_DOMAIN"),
        os.getenv("TESLA_BLE_API_DOMAIN"),
    )
    client = (
        di[MockTeslaClient] if os.getenv("USE_MOCK_DATA") == "true" else di[TeslaClient]
    )

    di[TeslaService] = lambda di: TeslaService(
        os.getenv("CLIENT_ID"),
        os.getenv("CLIENT_SECRET"),
        os.getenv("REDIRECT_URI"),
        os.getenv("AUDIENCE"),
        os.getenv("TESLA_AUTH_API_DOMAIN"),
        client,
    )
    di["cookie"] = os.getenv("COOKIE")
    di[CancellationToken] = CancellationToken()
    di[SolarMonitorService] = lambda di: SolarMonitorService()
