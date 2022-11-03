import pytest
from store_service.fs_store_service import FSStoreService

@pytest.fixture(scope="module")
def fs_store_service() -> FSStoreService:
    return FSStoreService()

@pytest.fixture(scope="module")
def test_filename() -> str:     
    name = "test_file.txt"
    with open(name, 'w') as f:
        f.write("test content")
    return name

def test_fs_store_service_remove_file_successful(fs_store_service: FSStoreService, test_filename: str):
    assert fs_store_service.remove_file(test_filename)
    assert fs_store_service.file_exists_sync(test_filename) == False

def test_fs_store_service_remove_file_fail(fs_store_service: FSStoreService):
    test_filename = "123"
    assert fs_store_service.file_exists_sync(test_filename) == False
    assert fs_store_service.remove_file(test_filename) == False
