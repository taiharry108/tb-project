from dependency_injector.wiring import inject
from httpx import AsyncClient
import pytest
from pathlib import Path
from redis import Redis
from sqlalchemy import delete

from container import Container
from database.database_service import DatabaseService
from database.crud_service import CRUDService
from database.models import User, File, PrivateKey
from routers.utils import get_session_data
from session.session_verifier import SessionData
from store_service.store_service import StoreService


@pytest.fixture(scope="module")
async def username():
    return "test_user"


@pytest.fixture(scope="module")
async def file_path():
    return Path("tmp/test.txt")


@pytest.fixture(scope="module")
async def encrypt_path():
    return "/api/file"


@pytest.fixture(scope="module")
async def api_file_path():
    return "/api/file"


@pytest.fixture(scope="module")
async def all_files_path():
    return "/api/files"


@pytest.fixture(scope="module")
async def test_file(
    database: DatabaseService, crud_service: CRUDService, username: str
) -> File:
    name = "test.txt"
    async with database.session() as session:
        async with session.begin():
            user_id = await crud_service.get_id_by_attr(
                session, User, "email", username
            )
            db_file = await crud_service.create_obj(
                session, File, filename=name, user_id=user_id
            )
            return db_file


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(
    database: DatabaseService, username: str, container: Container
):
    import main

    async def get_fake_session_data() -> SessionData:
        return SessionData(username=username)

    main.app.dependency_overrides[get_session_data] = get_fake_session_data
    async with database.session() as session:
        async with session.begin():
            await session.execute(delete(PrivateKey))
            await session.execute(delete(File))
            await session.execute(delete(User))
            db_user = User(email=username, hashed_password="123456")
            session.add(db_user)
            await session.commit()
    yield
    r: Redis = container.redis()
    r.delete(container.config.redis.encryption_job_in_queue())
    main.app.dependency_overrides = {}


@pytest.mark.anyio
@inject
async def test_encrypt(
    client: AsyncClient,
    file_path: Path,
    encrypt_path: str,
    username: str,
    store_service: StoreService,
):
    resp = await client.post(encrypt_path, files={"file": open(file_path)})

    json_resp = resp.json()

    assert await store_service.file_exists(
        f"uploaded/{username}/{json_resp['filename']}"
    )
    assert "file_id" in json_resp


@pytest.mark.anyio
@inject
async def test_all_files(client: AsyncClient, all_files_path: str, username: str):
    resp = await client.get(all_files_path)
    assert len(resp.json()) > 0


@pytest.mark.anyio
@inject
async def test_delete_all_files(
    client: AsyncClient, all_files_path: str, username: str
):
    resp = await client.get(all_files_path)
    assert len(resp.json()) > 0

    await client.delete(all_files_path)

    resp = await client.get(all_files_path)
    assert len(resp.json()) == 0


@pytest.mark.anyio
@inject
async def test_get_file_successful(
    client: AsyncClient, api_file_path: str, test_file: File
):
    resp = await client.get(api_file_path + f"/{test_file.id}")
    json_resp = resp.json()
    assert "filename" in json_resp
    assert json_resp["filename"] == test_file.filename
    assert json_resp["id"] == test_file.id


@pytest.mark.anyio
@inject
async def test_get_file_fail(client: AsyncClient, api_file_path: str):
    resp = await client.get(api_file_path + "/123456")
    assert resp.status_code == 422


@pytest.mark.anyio
@inject
async def test_delete_file_successful(
    client: AsyncClient, api_file_path, test_file: File
):
    resp = await client.get(api_file_path + f"/{test_file.id}")
    json_resp = resp.json()
    assert "filename" in json_resp
    assert json_resp["filename"] == test_file.filename
    assert json_resp["id"] == test_file.id

    resp = await client.delete(api_file_path + f"/{test_file.id}")

    assert resp.json() == {"success": True}

    resp = await client.get(api_file_path + f"/{test_file.id}")
    assert resp.status_code == 422
