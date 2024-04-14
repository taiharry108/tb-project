import httpx

from datetime import datetime

from models import SessionData, TeslaAccessTokenRequest, TeslaRefreshTokenRequest, Vehicle


class TeslaService:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        audience: str,
        tesla_auth_api_domain: str,
        tesla_fleet_api_domain: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.audience = audience
        self.tesla_auth_api_domain = tesla_auth_api_domain
        self.tesla_fleet_api_domain = tesla_fleet_api_domain

    async def fresh_token(self, refresh_token: str) -> SessionData:
        refresh_token_request_data = self.create_refresh_token_request(refresh_token)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.tesla_auth_api_domain}/oauth2/v3/token",
                data=refresh_token_request_data.model_dump(),
            )
            json_resp = response.json()
            access_token = json_resp["access_token"]
            refresh_token = json_resp["refresh_token"]
            expires_in = json_resp["expires_in"]
            expires_at = datetime.now().timestamp() + expires_in - 600

            return SessionData(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )

    def create_refresh_token_request(self, refresh_token: str):
        return TeslaRefreshTokenRequest(
            grant_type="refresh_token",
            client_id=self.client_id,
            refresh_token=refresh_token,
        )

    def create_access_token_request(self, code: str):
        return TeslaAccessTokenRequest(
            grant_type="authorization_code",
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code,
            redirect_uri=self.redirect_uri,
            audience=self.audience,
        )

    async def fetch_access_token(self, code: str) -> SessionData:
        access_token_request_data = self.create_access_token_request(code)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.tesla_auth_api_domain}/oauth2/v3/token",
                data=access_token_request_data.model_dump(),
            )
            json_resp = response.json()
            access_token = json_resp["access_token"]
            refresh_token = json_resp["refresh_token"]
            expires_in = json_resp["expires_in"]
            expires_at = datetime.now().timestamp() + expires_in - 600

            return SessionData(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )

    async def get_vehicles(self, session_data: SessionData):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://{self.tesla_fleet_api_domain}/api/1/vehicles",
                headers={"Authorization": f"Bearer {session_data.access_token}"},
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
