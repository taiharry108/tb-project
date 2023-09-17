from dependency_injector.wiring import inject
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud_service import CRUDService
from database.database_service import DatabaseService
from database.models import User, PrivateKey

@pytest.fixture(scope="module")
async def key_path(): return "/admin/key"


@pytest.fixture(scope="module")
async def username(): return "test_user"


@pytest.mark.anyio
@inject
async def test_get_key(client: AsyncClient, key_path: str, username: str, database: DatabaseService, crud_service: CRUDService):

    resp = await client.get(key_path, params={"username": username})
    assert resp.json()["key"]

    async with database.session() as session:
        async with session.begin():
            user_id = await crud_service.get_id_by_attr(session, User, "email", username)
            private_key = await crud_service.get_item_by_attr(session, PrivateKey, "user_id", user_id)
            assert private_key.key == resp.json()["key"]
