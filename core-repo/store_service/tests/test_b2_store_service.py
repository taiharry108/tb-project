from b2sdk.v2 import FileVersion
from dotenv import dotenv_values
import pytest


from store_service.b2_store_service import B2StoreService as StoreService


@pytest.fixture(scope="module")
def bucket_name() -> str:
    return "tb-project-app"


@pytest.fixture(scope="module")
def store_service(bucket_name: str) -> StoreService:
    config = dotenv_values(".env")
    return StoreService(
        bucket_name, config["application_key_id"], config["application_key"]
    )


@pytest.fixture(scope="module")
def test_filename() -> str:
    name = "test_file.txt"
    with open(name, "w") as f:
        f.write("test content")
    return name


@pytest.fixture(scope="module")
def large_test_filename() -> str:
    name = "test_large_file.txt"
    with open(name, "w") as f:
        for i in range(13 * 1024 * 1024):
            f.write("0")
    return name


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(store_service: StoreService):
    yield
    for file_version, _ in store_service.bucket.ls():
        store_service.bucket.delete_file_version(
            file_version.id_, file_version.file_name
        )


def test_persist_file_sync_successful(store_service: StoreService, test_filename: str):
    file_id = store_service.persist_file_sync(test_filename, b"test content")
    file_verison: FileVersion = store_service.bucket.get_file_info_by_id(file_id)
    assert file_verison.file_name == test_filename


async def test_persist_file_successful(store_service: StoreService, test_filename: str):
    async def get_aiter():
        with open(test_filename, "rb") as f:
            yield f.read(1)
            yield f.read()

    file_id = await store_service.persist_file(test_filename, get_aiter())
    file_verison: FileVersion = store_service.bucket.get_file_info_by_id(file_id)
    assert file_verison.file_name == test_filename


# async def test_persist_file_large_successful(store_service: StoreService, large_test_filename: str):
#     async def get_aiter():
#         with open(large_test_filename, 'rb') as f:
#             data = f.read(5 * 1024 * 1024)
#             while data:
#                 yield data
#                 data = f.read(5 * 1024 * 1024)

#     file_id = await store_service.persist_file(large_test_filename, get_aiter(), is_large=True)
#     file_verison: FileVersion = store_service.bucket.get_file_info_by_id(
#         file_id)
#     assert file_verison.file_name == large_test_filename


async def test_store_service_file_exists(
    store_service: StoreService, test_filename: str
):
    assert await store_service.file_exists(test_filename)


async def test_store_service_file_exists_not_exist(
    store_service: StoreService, test_filename: str
):
    assert await store_service.file_exists("abc") == False


async def test_store_service_remove_file_successful(
    store_service: StoreService, test_filename: str
):
    assert await store_service.remove_file(test_filename)
