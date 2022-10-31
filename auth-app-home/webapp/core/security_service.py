from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from passlib.context import CryptContext
from jose import jwt


from logging import getLogger


logger = getLogger(__name__)


class SecurityService:
    def __init__(self,
                 private_key: str,
                 algorithm: str,
                 rt_key: str,
                 access_token_expire_minutes: int,
                 pwd_context: CryptContext):
        self.secret_key = private_key
        self.algorithm = algorithm
        self.rt_key = rt_key
        self.access_token_expire_minutes = access_token_expire_minutes
        self.pwd_context = pwd_context

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except ValueError:
            return False

    def hash_password(self, password: str) -> bool:
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_jwt_token(self, token: str, key: str, algo: str):

        return jwt.decode(token, key, algorithms=[algo])
