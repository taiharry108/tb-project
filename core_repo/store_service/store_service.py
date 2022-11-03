from typing import AsyncIterator, Dict, Protocol


class StoreService(Protocol):

    async def persist_file(self, path: str, async_iter: AsyncIterator[bytes] = None, meta: Dict = None) -> str:
        """Save a file to store return path"""

    def persist_file_sync(self, path: str, data: bytes = None, meta: Dict = None) -> str:
        """Save a file to store return path"""

    async def stat_file(self, path) -> Dict[str, str]:
        """Return stat of a file"""

    async def file_exists(self, path: str) -> bool:
        """Check if a file exists"""
