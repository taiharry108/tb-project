from dependency_injector.wiring import inject, Provide
from fastapi import Depends
from logging import getLogger
from sqlalchemy.ext.asyncio import AsyncSession

from container import Container
from database.database_service import DatabaseService

logger = getLogger(__name__)


@inject
def get_database_service(
    database_service: DatabaseService = Depends(Provide[Container.db_service]),
) -> DatabaseService:
    return database_service


async def get_db_session(
    database_service: DatabaseService = Depends(get_database_service),
) -> AsyncSession:
    session = database_service.new_session()
    try:
        async with session.begin():
            yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
