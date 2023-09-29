from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud_service import CRUDService
from core.security_service import SecurityService
from core.models.user import UserInDB
from database.models import User as DBUser


class UserService:
    def __init__(self, crud_service: CRUDService, security_service: SecurityService):
        self.crud_service = crud_service
        self.security_service = security_service

    async def get_user(
        self, session: AsyncSession, username: str
    ) -> Optional[UserInDB]:
        db_user = await self.crud_service.get_item_by_attr(
            session, DBUser, "email", username
        )
        if db_user is None:
            return None
        return UserInDB(
            email=db_user.email,
            is_active=db_user.is_active,
            hashed_password=db_user.hashed_password,
        )

    async def get_user_id(self, session: AsyncSession, username: str) -> int:
        return await self.crud_service.get_id_by_attr(
            session, DBUser, "email", username
        )

    async def create_user(
        self, session: AsyncSession, username: str, password: str
    ) -> Optional[DBUser]:
        if await self.get_user(session, username):
            return None
        hashed_password = self.security_service.hash_password(password)
        db_user = await self.crud_service.create_obj(
            session, DBUser, email=username, hashed_password=hashed_password
        )
        return db_user

    def authenticate_user(self, db_user: DBUser, password: str) -> bool:
        return self.security_service.verify_password(password, db_user.hashed_password)
