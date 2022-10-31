from httpx import AsyncClient
from sqlalchemy import delete
import pytest

from database.models import User, File, PrivateKey
from database.database_service import DatabaseService
from routers.auth import get_session_data
from session.session_verifier import SessionData


@pytest.fixture(scope="module")
async def username(): return "test_user"


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: DatabaseService, username: str):
    async with database.session() as session:
        async with session.begin():
            await session.execute(delete(PrivateKey))
            await session.execute(delete(File))
            await session.execute(delete(User))
            db_user = User(email=username, hashed_password="123456")
            session.add(db_user)
            await session.commit()
    yield


@pytest.mark.anyio
async def test_root_without_session_data(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 307


@pytest.mark.anyio
async def test_root_with_wrong_session_data(client: AsyncClient):
    client.cookies.set(
        name="e_session_id",
        value="123",
        domain="localhost.local"
    )
    resp = await client.get("/")
    assert resp.status_code == 307


@pytest.mark.anyio
async def test_root_with_right_session_data(client: AsyncClient):
    import main

    async def get_fake_session_data() -> SessionData:
        return SessionData(username="test_user")

    main.app.dependency_overrides[get_session_data] = get_fake_session_data
    resp = await client.get("/")
    assert resp.status_code == 200

    main.app.dependency_overrides = {}
