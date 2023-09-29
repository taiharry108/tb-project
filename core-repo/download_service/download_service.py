from bs4 import BeautifulSoup
from functools import wraps
from httpx import AsyncClient, Limits, Timeout, Response
from logging import getLogger
from pathlib import Path
from pydantic import HttpUrl
from typing import Callable, Dict, Union, List
import uuid

from store_service.store_service import StoreService
from async_service.async_service import AsyncService

logger = getLogger(__name__)


def request_resp(method: str = "GET"):
    def outter_wrapped(func: Callable) -> Callable:
        @wraps(func)
        async def wrapped(self, url: HttpUrl, *args, **kwargs):
            headers = {}
            headers.update(self.headers)
            follow_redirects = (
                kwargs.pop("follow_redirects")
                if "follow_redirects" in kwargs
                else False
            )
            data = kwargs.pop("data") if "data" in kwargs else {}

            logger.info(f"going to send a {method} request to {url}")

            client: AsyncClient = self.client
            resp = await client.request(
                method,
                url,
                headers=headers,
                follow_redirects=follow_redirects,
                data=data,
            )

            if resp.status_code == 200:
                return await func(self, resp, **kwargs)
            else:
                raise RuntimeError(f"response status code: {resp.status_code}")

        return wrapped

    return outter_wrapped


def stream_resp(method: str = "GET"):
    def outter_wrapped(func: Callable) -> Callable:
        @wraps(func)
        async def wrapped(self, url: HttpUrl, *args, **kwargs):
            headers = {}
            follow_redirects = (
                kwargs.pop("follow_redirects")
                if "follow_redirects" in kwargs
                else False
            )
            data = kwargs.pop("data") if "data" in kwargs else {}
            if "headers" in kwargs:
                headers.update(kwargs.pop("headers"))

            logger.info(f"going to send a {method} request to {url}")

            client: AsyncClient = self.client

            async with client.stream(
                method,
                url,
                headers=headers,
                follow_redirects=follow_redirects,
                data=data,
            ) as resp:
                if resp.status_code == 200:
                    return await func(self, resp, *args, **kwargs)
                else:
                    raise RuntimeError(f"response status code: {resp.status_code}")

        return wrapped

    return outter_wrapped


class DownloadService:
    """Handle all the http requests"""

    def __init__(
        self,
        max_connections: int,
        max_keepalive_connections: int,
        headers: Dict[str, str],
        store_service: StoreService,
        proxy: Dict[str, str],
    ) -> None:
        limits = Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        timeout = Timeout(100, read=None)
        # if not proxy:
        #     proxies = f"socks5://{proxy['username']}:{proxy['password']}@{proxy['server']}:{proxy['port']}"
        #     self.client = AsyncClient(
        #         limits=limits, timeout=timeout, verify=False, proxies=proxies)
        # else:
        self.client = AsyncClient(limits=limits, timeout=timeout, verify=False)

        self.headers = headers
        self.store_service = store_service

    @request_resp("POST")
    async def post_json(self, resp: Response) -> Union[List, Dict]:
        """Make a get request and return with json"""
        return resp.json()

    @request_resp("GET")
    async def get_json(self, resp: Response) -> Union[List, Dict]:
        """Make a get request and return with json"""
        return resp.json()

    @request_resp("GET")
    async def get_bytes(self, resp: Response) -> bytes:
        """Make a get request and return with bytes"""
        return resp.content

    @request_resp("GET")
    async def get_byte_soup(self, resp: Response) -> BeautifulSoup:
        """Make a get request and return with BeautifulSoup"""
        return BeautifulSoup(resp.content, features="html.parser")

    @request_resp("GET")
    async def get_soup(self, resp: Response) -> BeautifulSoup:
        """Make a get request and return with BeautifulSoup"""
        return BeautifulSoup(resp.text, features="html.parser")

    def generate_file_path(
        self, content_type: str, dir_path: Path, filename: str = None
    ) -> Path:
        if filename is None:
            filename = uuid.uuid4()
        file_path = Path("./") if dir_path is None else Path(dir_path)
        file_path /= f'{filename}.{content_type.split("/")[-1]}'

        return file_path

    async def _store_content_from_resp(
        self, resp: Response, file_path: str, path_key: str, **kwargs
    ) -> Dict:
        result_path = await self.store_service.persist_file(
            file_path, resp.aiter_bytes()
        )
        result = {path_key: result_path}
        result.update(kwargs)
        return result

    @stream_resp("GET")
    async def download_img(
        self, resp: Response, download_path: Path = None, filename: str = None, **kwargs
    ) -> Dict:
        content_type = resp.headers["content-type"]
        if not content_type.startswith("image"):
            raise RuntimeError("Response is not an image")

        file_path = self.generate_file_path(content_type, download_path, filename)

        return await self._store_content_from_resp(
            resp, str(file_path), "pic_path", **kwargs
        )

    @stream_resp("GET")
    async def _download_vid(self, resp: Response, file_path: str, **kwargs) -> Dict:
        return await self._store_content_from_resp(
            resp, file_path, "vid_path", **kwargs
        )

    @request_resp("HEAD")
    async def download_vid(
        self, resp: Response, download_path: Path = None, filename: str = None, **kwargs
    ) -> Dict:
        content_type = resp.headers["content-type"]
        if not content_type.startswith("video"):
            raise RuntimeError("Response is not a video")
        logger.info(f"{content_type=}")

        file_path = self.generate_file_path(content_type, download_path, filename)

        if await self.store_service.file_exists(file_path):
            result = {"vid_path": str(file_path)}
            result.update(kwargs)
            return result

        return await self._download_vid(resp.url, file_path=str(file_path), **kwargs)

    async def download_imgs(
        self,
        async_service: AsyncService,
        download_path: Path,
        img_list: List[Dict[str, int | str | None]],
        headers: Dict[str, str],
    ):
        """Download multiple images simultaneously"""
        async for item in async_service.work(
            img_list, self.download_img, headers=headers, download_path=download_path
        ):
            yield item
