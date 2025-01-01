import asyncio
import httpx
import json

from datetime import datetime

from client import TeslaClientProtocol
from models import (
    SessionData,
    TeslaAccessTokenRequest,
    TeslaRefreshTokenRequest,
    Vehicle,
    VehicleData,
    TeslaCommand,
)


class TeslaService:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        audience: str,
        tesla_auth_api_domain: str,
        client: TeslaClientProtocol,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.audience = audience
        self.charging_amps = 0
        self.is_charging = False
        self.tesla_auth_api_domain = tesla_auth_api_domain
        self.client = client

    async def refresh_token(self, refresh_token: str) -> SessionData:
        refresh_token_request_data = self._create_refresh_token_request(refresh_token)
        access_token_response = await self.client.refresh_token(
            refresh_token_request_data
        )

        expires_in = access_token_response.expires_in
        expires_at = datetime.now().timestamp() + expires_in - 600

        return SessionData(
            access_token=access_token_response.access_token,
            refresh_token=access_token_response.refresh_token,
            expires_at=expires_at,
        )

    async def fetch_access_token(self, code: str) -> SessionData:
        access_token_request_data = self._create_access_token_request(code)
        access_token_response = await self.client.access_token(
            access_token_request_data
        )

        expires_in = access_token_response.expires_in
        expires_at = datetime.now().timestamp() + expires_in - 600

        return SessionData(
            access_token=access_token_response.access_token,
            refresh_token=access_token_response.refresh_token,
            expires_at=expires_at,
        )

    async def get_vehicles(self, session_data: SessionData) -> list[Vehicle]:
        return await self.client.get_vehicles(session_data.access_token)

    def create_vehicle_data(self, response: dict) -> VehicleData:
        if not response:
            return VehicleData(
                battery_level=0,
                charge_amps=0,
                charging_state="",
                minutes_to_full_charge=0,
            )
        charge_state = response.get("charge_state", {})
        battery_level = charge_state.get("battery_level", 0)
        charge_amps = charge_state.get("charge_amps", 0)
        charging_state = charge_state.get("charging_state", "")
        minutes_to_full_charge = charge_state.get("minutes_to_full_charge", 0)
        return VehicleData(
            battery_level=battery_level,
            charge_amps=charge_amps,
            charging_state=charging_state,
            minutes_to_full_charge=minutes_to_full_charge,
        )

    async def get_vehicle_data(
        self, session_data: SessionData, vehicle_id: int
    ) -> VehicleData:
        response = await self.client.get_vehicle_data(
            session_data.access_token, vehicle_id
        )
        return self.create_vehicle_data(response)

    async def wake_up(self, session_data: SessionData, vehicle_id: int):
        return await self.client.wake_up(session_data.access_token, vehicle_id)

    async def send_command(self, tesla_command: TeslaCommand, params: dict):
        print(f"Sending command: {tesla_command.value} with params: {params}")
        return await self.client.send_command(tesla_command, params)

    async def adjust_current(self, net_power: float):
        old_charge_amps = self.charging_amps
        new_charging_amps = self.charging_amps + net_power * 1000 / 220
        self.charging_amps = min(int(new_charging_amps), 24)

        print(
            f"{net_power=:.2f},{old_charge_amps=}, {self.charging_amps=}, {self.is_charging=}"
        )

        if self.charging_amps >= 5:
            if not self.is_charging:
                await self.send_command(TeslaCommand.CHARGING_START, {})
            if abs(old_charge_amps - self.charging_amps) > 1:
                await self.send_command(
                    TeslaCommand.CHARGING_SET_AMPS, {"value": self.charging_amps}
                )
                print("sleep for 10s")
                await asyncio.sleep(10)
            else:
                self.charging_amps = old_charge_amps
            self.is_charging = True
        else:
            if self.is_charging:
                await self.send_command(TeslaCommand.CHARGING_STOP, {})
            self.is_charging = False
            self.charging_amps = 0

    def _create_refresh_token_request(self, refresh_token: str):
        return TeslaRefreshTokenRequest(
            grant_type="refresh_token",
            client_id=self.client_id,
            refresh_token=refresh_token,
        )

    def _create_access_token_request(self, code: str):
        return TeslaAccessTokenRequest(
            grant_type="authorization_code",
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code,
            redirect_uri=self.redirect_uri,
            audience=self.audience,
        )
