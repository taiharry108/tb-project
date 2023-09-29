from dependency_injector.wiring import inject, Provide
from fastapi import Depends, Request, HTTPException
from fastapi_sessions.frontends.implementations.cookie import SessionCookie
from logging import getLogger
from sqlalchemy.ext.asyncio import AsyncSession

from container import Container
from database.crud_service import CRUDService
from database.database_service import DatabaseService
from database.models import User
from session.session_verifier import BasicVerifier, SessionData

logger = getLogger(__name__)


@inject
def get_database_service(
    database_service: DatabaseService = Depends(Provide[Container.db_service]),
) -> DatabaseService:
    return database_service


async def get_db_session(
    database_service: DatabaseService = Depends(get_database_service),
) -> AsyncSession:
    session = database_service.new_session()
    try:
        async with session.begin():
            yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def _check_session(
    request: Request, cookie: SessionCookie, verifier: BasicVerifier
):
    cookie(request)
    return await verifier(request)


@inject
async def check_session(
    request: Request,
    cookie: SessionCookie = Depends(Provide[Container.cookie]),
    verifier: BasicVerifier = Depends(Provide[Container.verifier]),
):
    return await _check_session(request, cookie, verifier)


@inject
async def get_session_data(
    request: Request,
    cookie: SessionCookie = Depends(Provide[Container.cookie]),
    verifier: BasicVerifier = Depends(Provide[Container.verifier]),
):
    try:
        session_data = await _check_session(request, cookie, verifier)
    except HTTPException as ex:
        print(ex.detail)
        return None
    return session_data


async def get_user_name(session_data: SessionData = Depends(get_session_data)) -> str:
    return session_data.username


@inject
async def get_user_id(
    username: str = Depends(get_user_name),
    session: AsyncSession = Depends(get_db_session),
    crud_service: CRUDService = Depends(Provide[Container.crud_service]),
) -> int:
    return await crud_service.get_id_by_attr(session, User, "email", username)
