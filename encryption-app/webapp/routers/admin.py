from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from container import Container
from core.encrypt_service import EncryptService
from database import CRUDService
from database.models import PrivateKey, User

from routers.utils import get_db_session

router = APIRouter()


async def check_host(request: Request):
    if request.client.host != "127.0.0.1":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized"
        )


@router.get("/key", dependencies=[Depends(check_host)])
@inject
async def key(
    username: str,
    crud_service: CRUDService = Depends(Provide[Container.crud_service]),
    encrypt_service: EncryptService = Depends(Provide[Container.encrypt_service]),
    session: AsyncSession = Depends(get_db_session),
):
    user_id = await crud_service.get_id_by_attr(session, User, "email", username)
    db_private_key = await crud_service.get_item_by_attr(
        session, PrivateKey, "user_id", user_id
    )
    if not db_private_key:
        key = encrypt_service.generate_key().decode("utf8")
        db_private_key = await crud_service.create_obj(
            session, PrivateKey, user_id=user_id, key=str(key)
        )
    key = db_private_key.key

    return {"key": key}
