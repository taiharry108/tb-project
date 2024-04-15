from enum import Enum

class TeslaCommand(Enum):
    UNLOCK = "unlock"
    LOCK = "lock"
    CLIMATE_ON = "climate-on"
    CLIMATE_OFF = "climate-off"
    CLIMATE_SET_TEMP = "climate-set-temp"
    HONK = "honk"
    PING = "ping"
    FLASH_LIGHTS = "flash-lights"
    CHARGING_START = "charging-start"
    CHARGING_STOP = "charging-stop"
    CHARGING_SET_LIMIT = "charging-set-limit"
    CHARGING_SET_AMPS = "charging-set-amps"
    PRODUCT_INFO = "product-info"
