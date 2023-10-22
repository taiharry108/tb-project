from fastapi import Depends
from kink import di
from logging import getLogger
from sqlalchemy.ext.asyncio import AsyncSession


from database import DatabaseService

logger = getLogger(__name__)


def get_database_service(
    database_service: DatabaseService = Depends(lambda: di[DatabaseService]),
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
