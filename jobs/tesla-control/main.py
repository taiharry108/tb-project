import os

from fastapi import FastAPI
from pydantic import validator, BaseModel

from tesla_command import TeslaCommand

app = FastAPI()

# Define a route /api/tesla-control
# This route will be used to control the Tesla car
# The route should accept a POST request with a JSON body like the following:
# {"command": "unlock", "params": {}}

# Create a pydantic class TeslaControl that has two fields:
# command: str
# params: dict

# Use the TeslaCommand enum to validate the command field
# The command field should be a valid TeslaCommand
# The params field should be a dict
# If the command is not valid, return a 400 response with a JSON body like the following:
# {"error": "Invalid command"}
# If the params is not a dict, return a 400 response with a JSON body like the following:
# {"error": "Invalid params"}
# If the command is valid, return a 200 response with a JSON body like the following:
# {"status": "success"}
# If the command is valid and the command is "climate-set-temp", the params should have a key "temperature" with a value that is a number
# If the temperature is not a number, return a 400 response with a JSON body like the following:
# {"error": "Invalid temperature"}


class TeslaControl(BaseModel):
    command: str
    params: dict

    @validator("command")
    def command_must_be_valid(cls, value):
        try:
            TeslaCommand(value)
        except ValueError:
            raise ValueError("Invalid command")
        return value

    @validator("params")
    def params_must_be_dict(cls, value):
        if not isinstance(value, dict):
            raise ValueError("Invalid params")
        return value


@app.post("/api/tesla-control")
def tesla_control(tesla_control: TeslaControl):
    return {"status": "success"}
    