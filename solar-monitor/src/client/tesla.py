import httpx
import json

from typing import Protocol

from models import (
    TeslaRefreshTokenRequest,
    TeslaAccessTokenResponse,
    TeslaAccessTokenRequest,
    TeslaCommand,
    Vehicle,
)


class TeslaClientProtocol(Protocol):
    async def refresh_token(
        self, tesla_refresh_token_request: TeslaRefreshTokenRequest
    ) -> TeslaAccessTokenResponse:
        """
        Refresh the Tesla access token

        :param tesla_refresh_token_request: TeslaRefreshTokenRequest
        :return: TeslaAccessTokenResponse
        """

    async def access_token(
        self, tesla_access_token_request: TeslaAccessTokenRequest
    ) -> TeslaAccessTokenResponse:
        """
        Get a Tesla access token

        :param tesla_access_token_request: TeslaAccessTokenRequest
        :return: TeslaAccessTokenResponse
        """

    async def wake_up(self, access_token: str, vehicle_id: int) -> bool:
        """
        Wake up the vehicle

        :param access_token: str
        :param vehicle_id: int
        """

    async def send_command(self, tesla_command: TeslaCommand, params: dict) -> dict:
        """
        Send a command to the vehicle

        :param tesla_command: TeslaCommand
        :param params: dict
        :return: dict
        """

    async def get_vehicles(self, access_token: str) -> list[Vehicle]:
        """
        Get a list of vehicles

        :param access_token: str
        :return: list[Vehicle]
        """

    async def get_vehicle_data(self, access_token: str, vehicle_id: int) -> dict:
        """
        Get vehicle data

        :param access_token: str
        :param vehicle_id: int
        :return: dict
        """


class TeslaClient(TeslaClientProtocol):
    def __init__(self, tesla_auth_api_domain: str, tesla_fleet_api_domain: str, tesla_ble_api_domain: str):
        self.tesla_auth_api_domain = tesla_auth_api_domain
        self.tesla_fleet_api_domain = tesla_fleet_api_domain
        self.tesla_ble_api_domain = tesla_ble_api_domain

    async def refresh_token(
        self, tesla_refresh_token_request: TeslaRefreshTokenRequest
    ) -> TeslaAccessTokenResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.tesla_auth_api_domain}/oauth2/v3/token",
                data=tesla_refresh_token_request.model_dump(),
            )
            json_resp = response.json()

            return TeslaAccessTokenResponse(
                access_token=json_resp["access_token"],
                refresh_token=json_resp["refresh_token"],
                expires_in=json_resp["expires_in"],
            )

    async def access_token(
        self, tesla_access_token_request: TeslaAccessTokenRequest
    ) -> TeslaAccessTokenResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.tesla_auth_api_domain}/oauth2/v3/token",
                data=tesla_access_token_request.model_dump(),
            )
            json_resp = response.json()

            return TeslaAccessTokenResponse(
                access_token=json_resp["access_token"],
                refresh_token=json_resp["refresh_token"],
                expires_in=json_resp["expires_in"],
            )

    async def wake_up(self, access_token: str, vehicle_id: int) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.tesla_fleet_api_domain}/api/1/vehicles/{vehicle_id}/wake_up",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return response.json()

    async def send_command(self, tesla_command: TeslaCommand, params: dict) -> dict:
        url = f"http://{self.tesla_ble_api_domain}:8000/api/tesla-control/"
        data = {"command": tesla_command.value, "params": params}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=data,
                follow_redirects=True,
                timeout=60
            )
            return response.json()

    async def get_vehicles(self, access_token: str) -> list[Vehicle]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://{self.tesla_fleet_api_domain}/api/1/vehicles",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp_json = response.json()["response"]
            vehicles = [
                Vehicle(
                    id=vehicle["id"],
                    display_name=vehicle["display_name"],
                    vin=vehicle["vin"],
                    state=vehicle["state"],
                )
                for vehicle in resp_json
            ]
            return vehicles

    async def get_vehicle_data(self, access_token: str, vehicle_id: int) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://{self.tesla_fleet_api_domain}/api/1/vehicles/{vehicle_id}/vehicle_data",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return response.json().get("response", {})


class MockTeslaClient(TeslaClientProtocol):
    async def refresh_token(
        self, tesla_refresh_token_request: TeslaRefreshTokenRequest
    ) -> TeslaAccessTokenResponse:
        return TeslaAccessTokenResponse(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=1000,
        )

    async def access_token(
        self, tesla_access_token_request: TeslaAccessTokenRequest
    ) -> TeslaAccessTokenResponse:
        return TeslaAccessTokenResponse(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=1000,
        )

    async def wake_up(self, access_token: str, vehicle_id: int) -> bool:
        return True

    async def send_command(self, tesla_command: TeslaCommand, params: dict) -> dict:
        return {
            "status": True
        }

    async def get_vehicles(self, access_token: str) -> list[Vehicle]:
        return [
            Vehicle(id=1, display_name="Mock Vehicle",
                    vin="123456789", state="online")
        ]

    async def get_vehicle_data(self, access_token: str, vehicle_id: int) -> dict:
        with open("./services/mock_data/vehicle_data.json") as f:
            data = json.load(f).get("response", {})
            return data
