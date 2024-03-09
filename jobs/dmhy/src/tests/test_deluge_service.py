import json
import pytest

from logging import getLogger
from werkzeug import Request, Response

from download_service import DownloadService
from pytest_httpserver import HTTPServer
from services.deluge_service import DelugeService

logger = getLogger(__name__)


@pytest.fixture
def magnet_url() -> str:
    return "magnet:?xt=urn:btih:2UQDV4QHN7SFM5E3V7HK6ZM7U4TO"


@pytest.fixture
def torrent_id() -> str:
    return "123"


@pytest.fixture
def deluge_id() -> int:
    return 1


@pytest.fixture
def password() -> str:
    return "123456"


@pytest.fixture
def deluge_url(httpserver: HTTPServer) -> str:
    return httpserver.url_for("")


@pytest.fixture
def download_path() -> str:
    return "/downloads/test"


@pytest.fixture
def deluge_service(
    download_service: DownloadService,
    deluge_url: str,
) -> DelugeService:
    return DelugeService(deluge_url, download_service)


async def test_auth(
    password: str, deluge_service: DelugeService, httpserver: HTTPServer, deluge_id: int
):
    httpserver.expect_request(
        "/json",
        method="POST",
        json={"id": deluge_id, "method": "auth.login", "params": [password]},
    ).respond_with_json({"result": True, "error": None, "id": deluge_id})
    assert await deluge_service.auth(password) == True


async def test_auth_fail(
    password: str, deluge_service: DelugeService, httpserver: HTTPServer, deluge_id: int
):
    def handler(request: Request):
        is_auth = request.json["params"][0] == password
        response_json = {"result": is_auth, "error": None, "id": deluge_id}
        response_data = json.dumps(response_json, indent=4)
        return Response(response_data, 200, None, None, "application/json")

    httpserver.expect_request(
        "/json",
        method="POST",
    ).respond_with_handler(handler)
    assert await deluge_service.auth("123") == False


async def test_add_torrent_magnet(
    deluge_service: DelugeService,
    httpserver: HTTPServer,
    deluge_id: int,
    magnet_url: str,
    torrent_id: str,
    download_path: str,
):
    httpserver.expect_request(
        "/json",
        method="POST",
        json={
            "id": deluge_id,
            "method": "core.add_torrent_magnet",
            "params": [magnet_url, {"download_location": download_path}],
        },
    ).respond_with_json({"result": torrent_id, "error": None, "id": deluge_id})
    assert (
        await deluge_service.add_torrent_magnet(magnet_url, download_path) == torrent_id
    )


async def test_get_torrent_status(
    deluge_service: DelugeService,
    httpserver: HTTPServer,
    deluge_id: int,
    torrent_id: str,
):
    httpserver.expect_request(
        "/json",
        method="POST",
        json={
            "id": deluge_id,
            "method": "web.get_torrent_status",
            "params": [torrent_id],
        },
    ).respond_with_json(
        {"result": {"is_finished": True}, "error": None, "id": deluge_id}
    )
    assert "is_finished" in await deluge_service.get_torrent_status(torrent_id)
