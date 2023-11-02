from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt


from logging import getLogger


logger = getLogger(__name__)


class SecurityService:
    def __init__(
        self,
        private_key: str,
        algorithm: str,
        access_token_expire_minutes: int,
    ):
        self.secret_key = private_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf8"), hashed_password.encode("utf8")
            )
        except ValueError:
            return False

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt(rounds=15)
        return bcrypt.hashpw(password.encode("utf8"), salt).decode("utf8")

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_jwt_token(self, token: str, key: str, algo: str):
        return jwt.decode(token, key, algorithms=[algo])
