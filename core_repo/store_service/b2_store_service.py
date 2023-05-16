import asyncio
from aiob2 import Client, File
from b2sdk.v2 import B2Api, Bucket, InMemoryAccountInfo, FileVersion, DownloadVersion
from b2sdk.exception import FileNotPresent
from pathlib import Path
from typing import AsyncIterator, Dict

from .store_service import StoreService


class B2StoreService(StoreService):

    __slots__ = [
        'b2_api',
        'bucket',
        '_application_key_id',
        '_application_key'
    ]

    def __init__(self, bucket_name: str, application_key_id: str, application_key: str):
        info = InMemoryAccountInfo()  # store credentials, tokens and cache in memory
        self.b2_api: B2Api = B2Api(info)
        self.b2_api.authorize_account(
            "production", application_key_id, application_key)
        self.bucket: Bucket = self.b2_api.get_bucket_by_name(bucket_name)
        self._application_key_id = application_key_id
        self._application_key = application_key
    
    async def _persist_large_file(self, client: Client, path: str, async_iter: AsyncIterator[bytes] = None, ) -> File:
        large_file = await client.upload_large_file(self.bucket.id_, path)
        async for byte in async_iter:
            await large_file.upload_part(byte)
        return await large_file.finish()

    async def _persist_file(self, client: Client, path: str, async_iter: AsyncIterator[bytes] = None, ) -> File:
        data = b''
        async for byte in async_iter:
            data += byte
        file = await client.upload_file(file_name=path, content_bytes=data, bucket_id=self.bucket.id_)
        return file


    async def persist_file(self, path: str, async_iter: AsyncIterator[bytes] = None, is_large: bool = False, meta: Dict = None) -> str:
        """Save a file to store return path"""
        async with Client(self._application_key_id, self._application_key) as client:
            if is_large:
                result = await self._persist_large_file(client, path, async_iter)
            else:
                result = await self._persist_file(client, path, async_iter)
        
            return result.id

    def persist_file_sync(self, path: str, data: bytes = None, meta: Dict = None) -> str:
        """Save a file to store return path"""
        result: FileVersion = self.bucket.upload_bytes(data, path)
        return result.id_

    async def stat_file(self, path) -> Dict[str, str]:
        """Return stat of a file"""

    async def file_exists(self, path: str) -> bool:
        """Check if a file exists"""
        loop = asyncio.get_running_loop()
        try:
            await self._get_file_info(path, loop)
            return True
        except FileNotPresent:
            return False

    async def _get_file_info(self, path: str, loop: asyncio.AbstractEventLoop) -> DownloadVersion:
        return await loop.run_in_executor(None, self.bucket.get_file_info_by_name, path)

    def file_exists_sync(self, path: str) -> bool:
        """Check if a file exists"""
        try:
            self.bucket.get_file_info_by_name(path)
            return True
        except FileNotPresent:
            return False

    async def remove_file(self, path: str) -> bool:
        """Remove a file if exsits"""
        loop = asyncio.get_running_loop()
        file = await self._get_file_info(path, loop)
        file_id_n_name = await loop.run_in_executor(None, self.bucket.delete_file_version, file.id_, file.file_name)
        return True
