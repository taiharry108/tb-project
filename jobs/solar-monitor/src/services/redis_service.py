import json

from redis import Redis

from models import SessionData


class RedisService:
    def __init__(self, app_name: str, redis: Redis):
        self.redis = redis
        self.app_name = app_name

    def set_session_data(self, user_session_id: str, session_data: SessionData):
        self.redis.hset(
            self.app_name, key=str(user_session_id), value=session_data.model_dump_json()
        )

    def get_session_data(self, user_session_id: str) -> SessionData | None:
        session_data = self.redis.hget(self.app_name, user_session_id)
        if session_data:
            return SessionData(**json.loads(session_data))
        else:
            return None
