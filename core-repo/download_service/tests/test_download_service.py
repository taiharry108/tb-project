from bs4 import BeautifulSoup
from pathlib import Path
import pytest

from async_service import AsyncService
from download_service import DownloadService
from store_service import FSStoreService
from logging import getLogger


logger = getLogger(__name__)


@pytest.fixture
def img_url() -> str:
    return "https://placeholder.com/wp-content/uploads/2018/10/placeholder-1.png"


@pytest.fixture
def download_path() -> str:
    return "test"


@pytest.fixture
def download_service() -> DownloadService:
    return DownloadService(
        max_connections=5,
        max_keepalive_connections=5,
        headers={},
        store_service=FSStoreService(),
        proxy={},
    )


@pytest.fixture
def async_service() -> AsyncService:
    return AsyncService(5, 1)


async def test_get_json(download_service: DownloadService):
    json_data = await download_service.get_json("http://ip.jsontest.com/")
    assert "ip" in json_data.keys()


async def test_get_bytes(download_service: DownloadService):
    b = await download_service.get_bytes("http://ip.jsontest.com/")


async def test_get_soup(download_service: DownloadService):
    soup: BeautifulSoup = await download_service.get_soup("https://www.example.com")
    assert soup.find("title").text == "Example Domain"


async def test_download_img(download_service: DownloadService, img_url: str):
    result = await download_service.download_img(
        img_url, download_path="test", filename="test.png"
    )
    assert "pic_path" in result


async def test_download_vid(download_service: DownloadService):
    url = "https://file-examples.com/storage/fe8c7eef0c6364f6c9504cc/2017/04/file_example_MP4_480_1_5MG.mp4"

    result = await download_service.download_vid(url, download_path="test")
    assert "vid_path" in result


async def test_download_imgs(
    download_service: DownloadService,
    async_service: AsyncService,
    download_path,
    img_url: str,
):
    n = 2
    img_list = [
        {"url": img_url, "filename": f"{idx}", "test_key": "test_val"}
        for idx in range(n)
    ]

    counter = 0
    async for result_dict in download_service.download_imgs(
        async_service, Path(download_path), img_list, headers={"Referer": ""}
    ):
        counter += 1
        assert "test_key" in result_dict
        assert result_dict["test_key"] == "test_val"
    assert counter == n
