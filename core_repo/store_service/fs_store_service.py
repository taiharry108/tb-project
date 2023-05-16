import hashlib
from logging import getLogger
import os
from pathlib import Path
from typing import AsyncIterator, Dict

from .store_service import StoreService


logger = getLogger(__name__)


def md5sum(file):
    """Calculate the md5 checksum of a file-like object without reading its
    whole content in memory.
    >>> from io import BytesIO
    >>> md5sum(BytesIO(b'file content to hash'))
    '784406af91dd5a54fbb9c84c2236595a'
    """
    m = hashlib.md5()
    while True:
        d = file.read(8096)
        if not d:
            break
        m.update(d)
    return m.hexdigest()


class FSStoreService(StoreService):

    def persist_file_sync(self, path: str, data: bytes = None, meta: Dict = None) -> str:
        """Save a file to store return path"""
        absolute_path = Path(path)
        absolute_path.parent.mkdir(exist_ok=True, parents=True)
        with open(absolute_path, "wb") as f:
            f.write(data)
        return str(path)

    async def persist_file(self, path: str, async_iter: AsyncIterator[bytes] = None, is_large: bool = False, meta: Dict = None) -> str:
        """Save a file to store return path"""
        absolute_path = Path(path)
        absolute_path.parent.mkdir(exist_ok=True, parents=True)
        if async_iter is not None:
            with open(absolute_path, "wb") as f:
                async for chunk in async_iter:
                    f.write(chunk)
        return str(path)

    async def stat_file(self, path: str) -> Dict[str, str]:
        """Return stat of a file"""
        absolute_path = Path(path)
        try:
            last_modified = absolute_path.lstat().st_mtime
        except Exception as ex:
            logger.error(ex)
            return {}

        with open(absolute_path, 'rb') as f:
            checksum = md5sum(f)

        return {'last_modified': last_modified, 'checksum': checksum}

    async def file_exists(self, path: str) -> bool:
        """Return True if a file with a given path exists"""
        return self.file_exists_sync(path)
    
    def file_exists_sync(self, path: str) -> bool:
        """Return True if a file with a given path exists"""
        absolute_path = Path(path)
        return absolute_path.exists()
    
    def remove_file(self, path: str) -> bool:
        absolute_path = Path(path)
        try:
            os.remove(absolute_path)
        except Exception as ex:
            return False
        return True
