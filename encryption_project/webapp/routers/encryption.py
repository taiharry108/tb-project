from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import delete
from time import time
from typing import List

from container import Container
from core.models import File

from database.crud_service import CRUDService
from database.database_service import DatabaseService
from database.models import User, File as DBFile
from queue_service.messages import EncryptMessage
from queue_service.redis_queue_service import RedisQueueService
from store_service.store_service import StoreService
from session.session_verifier import SessionData
from .auth import get_session_data


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")


def add_file_to_queue(redis_queue_service: RedisQueueService, username: str, filename: str, queue_name: str) -> int:
    message = EncryptMessage(
        start=time(), filename=f"{username}/{filename}", username=username)
    return redis_queue_service.add_message_to_queue(queue_name, message)


@router.post("/file")
@inject
async def post_file(file: UploadFile,
                    store_service: StoreService = Depends(
                        Provide[Container.store_service]),
                    db_service: DatabaseService = Depends(
                        Provide[Container.db_service]),
                    session_data: SessionData = Depends(get_session_data),
                    crud_service: CRUDService = Depends(Provide[Container.crud_service]),
                    redis_queue_service: RedisQueueService = Depends(Provide[Container.redis_queue_service]),
                    queue_name: str = Depends(Provide[Container.config.redis.encryption_job_in_queue])):
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

    add_file_to_queue(redis_queue_service, username, file.filename, queue_name)

    return {
        "filename": file.filename,
        "file_id": db_file.id
    }


@router.get("/file/{file_id}", response_model=File)
@inject
async def get_file(file_id: int,
                   session_data: SessionData = Depends(get_session_data),
                   db_service: DatabaseService = Depends(
        Provide[Container.db_service]),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    async with db_service.session() as session:
        async with session.begin():
            user_id = await crud_service.get_id_by_attr(session, User, "email", session_data.username)
            db_file = await crud_service.get_item_by_id(session, DBFile, file_id)
            if not db_file or db_file.user_id != user_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="file does not exist")

    return db_file


@router.delete("/file/{file_id}")
@inject
async def delete_file(file_id: int,
                      session_data: SessionData = Depends(get_session_data),
                      db_service: DatabaseService = Depends(
        Provide[Container.db_service]),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    async with db_service.session() as session:
        async with session.begin():
            user_id = await crud_service.get_id_by_attr(session, User, "email", session_data.username)
            db_user = await crud_service.remove_item_from_obj(session, User, DBFile, user_id, file_id, "files")
            if db_user:
                return {"success": True}
            else:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="Operation Failed")


@router.get("/files", response_model=List[File])
@inject
async def get_files(session_data: SessionData = Depends(get_session_data),
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
async def delete_files(session_data: SessionData = Depends(get_session_data),
                       db_service: DatabaseService = Depends(
        Provide[Container.db_service]),
        crud_service: CRUDService = Depends(Provide[Container.crud_service]),):
    async with db_service.session() as session:
        async with session.begin():
            user_id = await crud_service.get_id_by_attr(session, User, "email", session_data.username)
            q = delete(DBFile).where(DBFile.user_id == user_id)
            await session.execute(q)

    return True
