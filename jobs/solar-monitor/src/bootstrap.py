import os

from dotenv import load_dotenv
from kink import di
from redis import Redis

from services import RedisService, TeslaService

load_dotenv()

class Controller:
    def __init__(self):
        self.is_stopped = False
    def stop(self):
        self.is_stopped = True
    def __repr__(self):
        return f"Control({id(self)}) {self.is_stopped}"

def bootstrap_di() -> None:
    di[Redis] = lambda di: Redis()
    di[RedisService] = lambda di: RedisService(os.getenv("APP_NAME"), di[Redis])
    di[TeslaService] = lambda di: TeslaService(
        os.getenv("CLIENT_ID"),
        os.getenv("CLIENT_SECRET"),
        os.getenv("REDIRECT_URI"),
        os.getenv("AUDIENCE"),
        os.getenv("TESLA_AUTH_API_DOMAIN"),
        os.getenv("TESLA_FLEET_API_DOMAIN"),
        os.getenv("TESLA_BLE_API_DOMAIN"),
    )
    di['cookie'] = os.getenv("COOKIE")
    di[Controller] = Controller()

