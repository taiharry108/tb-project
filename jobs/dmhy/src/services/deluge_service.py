from logging import getLogger

from download_service import DownloadService

logger = getLogger(__name__)


class DelugeService:
    def __init__(self, url: str, download_service: DownloadService):
        self.url = url
        self.download_service = download_service
        self.is_auth = False

    def _create_json(self, method: str, params: list[any]):
        return {"id": 1, "method": method, "params": params}

    async def auth(self, password: str) -> bool:
        result = await self.download_service.post_json(
            f"{self.url}/json",
            json=self._create_json(method="auth.login", params=[password]),
        )
        return result["result"]

    async def add_torrent_magnet(self, magnet_url: str) -> str:
        result = await self.download_service.post_json(
            f"{self.url}/json",
            json=self._create_json(
                method="core.add_torrent_magnet", params=[magnet_url, {}]
            ),
        )
        return result["result"]

    async def get_torrent_status(self, torrent_id: str) -> dict:
        result = await self.download_service.post_json(
            f"{self.url}/json",
            json=self._create_json(
                method="web.get_torrent_status", params=[torrent_id]
            ),
        )
        return result["result"]
