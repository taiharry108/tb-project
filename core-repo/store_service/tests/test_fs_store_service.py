import pytest
from store_service.fs_store_service import FSStoreService as StoreService


@pytest.fixture(scope="module")
def store_service() -> StoreService:
    return StoreService()


@pytest.fixture(scope="module")
def test_filename() -> str:
    name = "test_file.txt"
    with open(name, 'w') as f:
        f.write("test content")
    return name


async def test_fs_store_read(store_service: StoreService, test_filename: str):
    assert await store_service.read(test_filename, 2) == b'te'


async def test_fs_store_read(store_service: StoreService, test_filename: str):
    assert await store_service.read(test_filename) == b'test content'


def test_fs_store_service_remove_file_successful(store_service: StoreService, test_filename: str):
    assert store_service.remove_file(test_filename)
    assert store_service.file_exists_sync(test_filename) == False


def test_fs_store_service_remove_file_fail(store_service: StoreService):
    test_filename = "123"
    assert store_service.file_exists_sync(test_filename) == False
    assert store_service.remove_file(test_filename) == False
