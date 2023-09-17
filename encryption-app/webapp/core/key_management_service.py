from httpx import Client


class KeyManagementService:
    def __init__(self, key_url: str):
        self.client = Client()
        self.key_url = key_url

    def get_key(self, username: str) -> bytes:
        resp = self.client.get(self.key_url, params={"username": username})
        return resp.json()["key"]
