"""Database module."""

from contextlib import asynccontextmanager
import logging
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import Session

from database.models import Base

logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(
        self, engine: AsyncEngine, session_factory: orm.sessionmaker, url: str = None
    ) -> None:
        self._engine = engine
        self._session_factory = session_factory
        self.url = url

    async def create_database(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self):
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            logger.exception("Session rollback because of exception")
            await session.rollback()
            raise
        finally:
            await session.close()

    def new_session(self):
        return self._session_factory()
