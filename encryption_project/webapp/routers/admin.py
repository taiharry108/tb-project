from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, HTTPException, status

from container import Container
from core.encrypt_service import EncryptService
from database.crud_service import CRUDService
from database.database_service import DatabaseService
from database.models import PrivateKey, User

router = APIRouter()


async def check_host(request: Request):
    if request.client.host != "127.0.0.1":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized"
        )


async def get_encryption_key(db_service: DatabaseService,
                             crud_service: CRUDService,
                             username: str,
                             encrypt_service: EncryptService = None,
                             generate_if_not_exsists=False):
    async with db_service.session() as session:
        async with session.begin():
            user_id = await crud_service.get_id_by_attr(session, User, "email", username)
            db_private_key = await crud_service.get_item_by_attr(session, PrivateKey, "user_id", user_id)
            if db_private_key:
                return db_private_key.key

            if generate_if_not_exsists:
                key = encrypt_service.generate_key().decode("utf8")
                db_private_key = await crud_service.create_obj(session, PrivateKey, user_id=user_id, key=str(key))
                return db_private_key.key

            return None


@router.get("/key", dependencies=[Depends(check_host)])
@inject
async def key(username: str,
              db_service: DatabaseService = Depends(
        Provide[Container.db_service]),
        crud_service: CRUDService = Depends(
        Provide[Container.crud_service]),
        encrypt_service: EncryptService = Depends(Provide[Container.encrypt_service])):

    key = await get_encryption_key(db_service, crud_service, username, encrypt_service, generate_if_not_exsists=True)

    return {"key": key}
