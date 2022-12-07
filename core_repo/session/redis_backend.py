from typing import Dict, Generic

from fastapi_sessions.backends.session_backend import (
    BackendError,
    SessionBackend,
    SessionModel,
)
from fastapi_sessions.frontends.session_frontend import ID

from redis import Redis

from session.session_verifier import SessionData

from logging import getLogger

logger = getLogger(__name__)

class RedisBackend(Generic[ID, SessionModel], SessionBackend[ID, SessionModel]):
    """Stores session data in a redis."""

    def __init__(self, redis: Redis, identifier: str) -> None:
        """Initialize a new in-memory database."""
        self.redis = redis
        self.identifier = identifier

    async def create(self, session_id: ID, data: SessionModel):
        """Create a new session entry."""
        if self.redis.hget(self.identifier, str(session_id)):
            raise BackendError("create can't overwrite an existing session")
        
        self.redis.hset(self.identifier, str(session_id), data.username)

    async def read(self, session_id: ID):
        """Read an existing session data."""
        data = self.redis.hget(self.identifier, str(session_id))
        if not data:
            return

        return SessionData(username=data.decode("utf8"))

    async def update(self, session_id: ID, data: SessionModel) -> None:
        """Update an existing session."""
        if self.redis.hexists(self.identifier, str(session_id)):
            self.redis.hset(self.identifier, str(session_id), data.username)
        else:
            raise BackendError("session does not exist, cannot update")

    async def delete(self, session_id: ID) -> None:
        """Delete an existing session"""
        self.redis.hdel(self.identifier, str(session_id))
