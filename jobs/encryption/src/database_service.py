from sqlalchemy.engine import Engine


class DatabaseService:
    def __init__(self, engine: Engine):
        self.engine = engine

    def _get_user_id_from_username(self, username: str) -> int:
        with self.engine.begin() as conn:
            query_str = f"SELECT id FROM users WHERE users.email = '{username}'"
            result = conn.execute(query_str).all()
            if not result:
                print("nothing")
                return None
            else:
                return result[0][0]

    def get_private_key_from_username(self, username: str) -> str:
        user_id = self._get_user_id_from_username(username)
        with self.engine.begin() as conn:
            query_str = (
                f"SELECT * FROM private_keys WHERE private_keys.user_id = {user_id}"
            )
            result = conn.execute(query_str).all()
            if not result:
                return None
            else:
                return result[0].key
