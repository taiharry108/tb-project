from typing import List
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, UploadFile
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import delete

from container import Container

from core.store_service import StoreService
from session.session_verifier import SessionData
from .auth import get_session_data
from database.crud_service import CRUDService
from database.database_service import DatabaseService
from database.models import User, File as DBFile

from core.models import File

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")


@router.post("/encrypt")
@inject
async def encrypt(file: UploadFile,
                  store_service: StoreService = Depends(
                      Provide[Container.store_service]),
                  db_service: DatabaseService = Depends(
                      Provide[Container.db_service]),
                  session_data: SessionData = Depends(get_session_data),
                  crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    async def byte_gen():
        data = await file.read(4 * 1024 * 1024)
        while data:
            yield data
            data = await file.read(4 * 1024 * 1024)
    username = session_data.username

    await store_service.persist_file(f"uploaded/{username}/{file.filename}", byte_gen())
    async with db_service.session() as session:
        async with session.begin():
            user_id = await crud_service.get_id_by_attr(session, User, "email", username)

            db_file = await crud_service.get_item_by_attrs(session, DBFile, user_id=user_id, filename=file.filename)

            if not db_file:
                db_file = await crud_service.create_obj(session, DBFile, user_id=user_id, filename=file.filename)
    return {
        "filename": file.filename,
        "file_id": db_file.id
    }


@router.get("/files", response_model=List[File])
@inject
async def files(session_data: SessionData = Depends(get_session_data),
                db_service: DatabaseService = Depends(
        Provide[Container.db_service]),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    async with db_service.session() as session:
        async with session.begin():
            user_id = await crud_service.get_id_by_attr(session, User, "email", session_data.username)
            files = await crud_service.get_items_of_obj(session, User, user_id, "files")

    return files


@router.delete("/files")
@inject
async def files(session_data: SessionData = Depends(get_session_data),
                    db_service: DatabaseService = Depends(
                        Provide[Container.db_service]),
                    crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    async with db_service.session() as session:
        async with session.begin():
            user_id = await crud_service.get_id_by_attr(session, User, "email", session_data.username)
            q = delete(DBFile).where(DBFile.user_id == user_id)
            await session.execute(q)

    return True
