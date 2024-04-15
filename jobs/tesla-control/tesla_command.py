# Create a Enum that has the possible commands that can be sent to the Tesla:
# The name of the enum should be in Screaming snake-case
# The value of the enum should be the same as the name dash-case of the enum
# Here are the available commands:
# unlock, lock, climate-on, climate-off, climate-set-temp, honk, ping, flash-lights, charging-start, charging-stop, charging-set-limit, charging-set-amps

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
