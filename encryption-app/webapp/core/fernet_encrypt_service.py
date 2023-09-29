from pathlib import Path
from typing import Callable

from store_service.store_service import StoreService
from .encrypt_service import EncryptService
from cryptography.fernet import Fernet


class FernetEncryptService(EncryptService):
    def __init__(self, store_service: StoreService):
        self.store_service = store_service

    async def __process_file(
        self, src_file: Path, dest_file: Path, process_func: Callable
    ) -> bool:
        """"""
        try:
            # opening the original file to encrypt
            with open(src_file, "rb") as file:
                original = file.read()

            # encrypting the file
            encrypted = process_func(original)

            # opening the file in write mode and
            # writing the encrypted data
            async def byte_iter():
                yield encrypted

            await self.store_service.persist_file(dest_file, byte_iter())

            return True
        except Exception as ex:
            print(ex)
            return False

    def __process_file_sync(
        self, src_file: Path, dest_file: Path, process_func: Callable
    ) -> bool:
        """"""
        try:
            # opening the original file to encrypt
            with open(src_file, "rb") as file:
                original = file.read()

            # encrypting the file
            encrypted = process_func(original)

            # opening the file in write mode and
            # writing the encrypted data

            self.store_service.persist_file_sync(dest_file, encrypted)

            return True
        except Exception as ex:
            print(ex)
            return False

    def encrypt_file_sync(self, key: bytes, src_file: Path, dest_file: Path) -> bool:
        """"""
        fernet = Fernet(key)
        return self.__process_file_sync(src_file, dest_file, fernet.encrypt)

    def decrypt_file_sync(self, key: bytes, src_file: Path, dest_file: Path) -> bool:
        """"""
        fernet = Fernet(key)
        return self.__process_file_sync(src_file, dest_file, fernet.decrypt)

    async def encrypt_file(self, key: bytes, src_file: Path, dest_file: Path) -> bool:
        """"""
        fernet = Fernet(key)
        return await self.__process_file(src_file, dest_file, fernet.encrypt)

    async def decrypt_file(self, key: bytes, src_file: Path, dest_file: Path) -> bool:
        """"""
        fernet = Fernet(key)
        return await self.__process_file(src_file, dest_file, fernet.decrypt)

    def generate_key(self) -> bytes:
        """"""
        return Fernet.generate_key()

    async def save_key(self, key: bytes, key_file: Path) -> bool:
        """"""

        async def key_iter():
            yield key

        await self.store_service.persist_file(str(key_file), key_iter())
