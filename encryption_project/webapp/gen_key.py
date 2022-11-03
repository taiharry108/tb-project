import asyncio
from pathlib import Path
from core.fernet_encrypt_service import FernetEncryptService
from store_service.fs_store_service import FSStoreService

async def main():
    fs_store_service = FSStoreService()
    encrypt_service = FernetEncryptService(fs_store_service)
    key = encrypt_service.generate_key()
    await encrypt_service.save_key(key, Path("private_key.txt"))


if __name__ == "__main__":
    asyncio.run(main())
