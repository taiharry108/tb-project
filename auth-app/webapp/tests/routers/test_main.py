from httpx import AsyncClient
import pytest
from sqlalchemy import delete

from database import DatabaseService
from database.models import User as DBUser


@pytest.fixture
async def redirect_url() -> str:
    return "http://localhost:60889/auth"


@pytest.fixture(scope="module")
def username() -> str:
    return f"test_user@gmail.com"


@pytest.fixture(scope="module")
def password() -> str:
    return "123456"


@pytest.fixture(scope="module")
def signup_path() -> str:
    return "/user/signup"


@pytest.fixture(scope="module")
def login_path() -> str:
    return "/user/login"


@pytest.fixture(scope="module")
def logout_path() -> str:
    return "/user/logout"


@pytest.fixture(scope="module")
def auth_path() -> str:
    return "/user/auth"


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(db_service: DatabaseService):
    async with db_service.session() as session:
        async with session.begin():
            await session.execute(delete(DBUser))
        # db_user = DBUser(email=username, hashed_password=password)
        # session.add(db_user)
        # await session.commit()
    yield


@pytest.mark.anyio
async def test_signup(
    client: AsyncClient, username: str, password: str, signup_path: str
):
    resp = await client.post(
        signup_path, data={"username": username, "password": password}
    )

    resp_json = resp.json()
    assert resp.status_code == 200
    assert resp_json["email"] == username
    assert resp_json["is_active"]


@pytest.mark.anyio
async def test_signup_twice_fail(
    client: AsyncClient, username: str, password: str, signup_path: str
):
    await client.post(signup_path, data={"username": username, "password": password})
    resp = await client.post(
        signup_path, data={"username": username, "password": password}
    )
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_signup_non_email_fail(
    client: AsyncClient, password: str, signup_path: str
):
    resp = await client.post(
        signup_path, data={"username": "123", "password": password}
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_login_for_access_token(
    client: AsyncClient,
    username: str,
    password: str,
    redirect_url: str,
    login_path: str,
):
    resp = await client.post(
        login_path,
        data={"username": username, "password": password, "redirect_url": redirect_url},
    )
    assert resp.status_code == 302
    assert resp.headers["location"].startswith(f"{redirect_url}?token=")


@pytest.mark.anyio
async def test_login_for_access_token_wrong_creds(
    client: AsyncClient, login_path: str, redirect_url: str
):
    resp = await client.post(
        login_path,
        data={
            "username": "abc@gmail.com",
            "password": "123",
            "redirect_url": redirect_url,
        },
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_for_access_token_wrong_redirect_url(
    client: AsyncClient, login_path: str
):
    redirect_url = "test_url"
    resp = await client.post(
        login_path,
        data={
            "username": "abc@gmail.com",
            "password": "123",
            "redirect_url": redirect_url,
        },
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_auth_fail(client: AsyncClient, redirect_url: str, auth_path: str):
    client.cookies.clear()
    resp = await client.get(auth_path, params={"redirect_url": redirect_url})

    assert resp.headers["location"] == f"./?redirect_url={redirect_url}"


@pytest.mark.anyio
async def test_auth_successful(
    client: AsyncClient,
    username: str,
    password: str,
    redirect_url: str,
    login_path: str,
    auth_path: str,
):
    tmp = await client.post(
        login_path,
        data={"username": username, "password": password, "redirect_url": redirect_url},
    )
    resp = await client.get(auth_path, params={"redirect_url": redirect_url})
    assert resp.status_code == 307
    assert resp.headers["location"].startswith(redirect_url)
    assert client.cookies.get("a_session_id")


@pytest.mark.anyio
async def test_logout_successful(
    client: AsyncClient,
    logout_path: str,
):
    assert client.cookies.get("a_session_id")

    resp = await client.post(logout_path)

    assert resp.status_code == 200
    assert resp.json() == {"success": True}

    assert client.cookies.get("a_session_id") is None
