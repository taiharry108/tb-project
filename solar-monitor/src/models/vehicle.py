# Create a pydantic class Vehicle
# Fields:
# - id: int
# - display_name: str
# - vin: str
# - state: str

# Path: jobs/solar-monitor/src/models/vehicle.py
from pydantic import BaseModel

class Vehicle(BaseModel):
    id: int
    display_name: str
    vin: str
    state: str

class VehicleData(BaseModel):
    battery_level: int
    charge_amps: int
    charging_state: str
    minutes_to_full_charge: int
