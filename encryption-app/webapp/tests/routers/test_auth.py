from httpx import AsyncClient
from jose import JWTError
import pytest

from container import Container


@pytest.fixture(scope="module")
async def wrong_token():
    return "123"


@pytest.fixture(scope="module")
async def correct_token():
    return "abc"


@pytest.fixture(scope="module")
async def username():
    return "test_user"


@pytest.fixture(autouse=True, scope="module")
async def security_service(container: Container, correct_token: str, username: str):
    class MockSecurityService:
        def decode_access_token(self, token: str):
            if token == correct_token:
                return {"sub": username}
            else:
                raise JWTError()

    container.security_service.override(MockSecurityService())


@pytest.mark.anyio
async def test_auth_fail(client: AsyncClient, wrong_token: str):
    resp = await client.get("/auth", params={"token": wrong_token})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_auth_successful(client: AsyncClient, correct_token: str):
    resp = await client.get("/auth", params={"token": correct_token})
    assert resp.status_code == 307
    assert resp.headers["location"] == "/encrypt/"
    assert "set-cookie" in resp.headers
    assert "e_session_id" in resp.headers["set-cookie"]
