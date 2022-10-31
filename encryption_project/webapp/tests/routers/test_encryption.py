from dependency_injector.wiring import inject
from httpx import AsyncClient
import pytest
from sqlalchemy import delete
from pathlib import Path

from core.store_service import StoreService
from database.database_service import DatabaseService

from database.models import User, File, PrivateKey
from routers.auth import get_session_data
from session.session_verifier import SessionData


@pytest.fixture(scope="module")
async def username(): return "test_user"


@pytest.fixture(scope="module")
async def file_path(): return Path("tmp/test.txt")


@pytest.fixture(scope="module")
async def encrypt_path(): return "/api/encrypt"


@pytest.fixture(scope="module")
async def all_files_path(): return "/api/files"


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: DatabaseService, username: str):
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
    main.app.dependency_overrides = {}


@pytest.mark.anyio
@inject
async def test_encrypt(client: AsyncClient, file_path: Path, encrypt_path: str, username: str, store_service: StoreService):
    resp = await client.post(encrypt_path, files={"file": open(file_path)})

    json_resp = resp.json()

    assert await store_service.file_exists(f"uploaded/{username}/{json_resp['filename']}")
    assert "file_id" in json_resp


@pytest.mark.anyio
@inject
async def test_all_files(client: AsyncClient, all_files_path: str, username: str):
    resp = await client.get(all_files_path)
    assert len(resp.json()) > 0


@pytest.mark.anyio
@inject
async def test_delete_all_files(client: AsyncClient, all_files_path: str, username: str):
    resp = await client.get(all_files_path)
    assert len(resp.json()) > 0

    await client.delete(all_files_path)

    resp = await client.get(all_files_path)
    assert len(resp.json()) == 0

