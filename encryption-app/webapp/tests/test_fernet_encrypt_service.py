from pathlib import Path
import pytest
from core.fernet_encrypt_service import FernetEncryptService
from store_service.fs_store_service import FSStoreService


@pytest.fixture
def test_file() -> str:
    filename = "./tmp/test.txt"
    with open(filename, "w") as f:
        f.write("this is a test file\n")

    return filename


async def test_generate_key():
    store_service = FSStoreService()
    encrypter = FernetEncryptService(store_service)
    key = encrypter.generate_key()
    assert isinstance(key, bytes)
    assert len(key) != 0


async def test_save_key():
    fake_key = b"abc"
    key_file = Path("./tmp/test_key.txt")
    store_service = FSStoreService()
    encrypter = FernetEncryptService(store_service)
    await encrypter.save_key(fake_key, key_file)

    with open(key_file, "rb") as f:
        assert f.read() == fake_key


async def test_encrypt_file(test_file: str):
    src_file = Path(test_file)
    encrypted_file = Path("./tmp/test_encrypted.txt")
    store_service = FSStoreService()
    encrypter = FernetEncryptService(store_service)
    key = encrypter.generate_key()
    assert await encrypter.encrypt_file(key, src_file, encrypted_file)


async def test_decrypt_file(test_file: str):
    src_file = Path(test_file)
    encrypted_file = Path("./tmp/test_encrypted.txt")
    decryptd_file = Path("./tmp/test_decrypted.txt")
    store_service = FSStoreService()
    encrypter = FernetEncryptService(store_service)
    key = encrypter.generate_key()
    assert await encrypter.encrypt_file(key, src_file, encrypted_file)
    assert await encrypter.decrypt_file(key, encrypted_file, decryptd_file)
    with open(src_file) as f:
        src_str = f.read()

    with open(decryptd_file) as f:
        decrypted_str = f.read()

    assert src_str == decrypted_str
