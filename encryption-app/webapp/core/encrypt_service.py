from pathlib import Path
from typing import Protocol


class EncryptService(Protocol):
    async def encrypt_file(self, key: bytes, src_file: Path, dest_file: Path) -> bool:
        """"""

    def generate_key(self) -> bytes:
        """"""

    def save_key(self, key: bytes, key_file: Path) -> bool:
        """"""

    async def decrypt_file(self, key: bytes, src_file: Path, dest_file: Path) -> bool:
        """"""

    def encrypt_file_sync(self, key: bytes, src_file: Path, dest_file: Path) -> bool:
        """"""

    def decrypt_file_sync(self, key: bytes, src_file: Path, dest_file: Path) -> bool:
        """"""
