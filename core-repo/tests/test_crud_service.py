import pytest

from database.database_service import DatabaseService
from database.crud_service import CRUDService
from database.models import User

@pytest.fixture
async def crud_service(database: DatabaseService) -> CRUDService:
    return CRUDService(database)


async def test_get_item_by_id(crud_service: CRUDService, database: DatabaseService):
    async with database.session() as session:
        async with session.begin():
            username = await crud_service.get_item_by_id(session, User, 44)
            print(username.email)


