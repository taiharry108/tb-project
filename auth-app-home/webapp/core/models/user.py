from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    email: str
    is_active: bool


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
