from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from fastapi.responses import RedirectResponse
from fastapi_sessions.frontends.implementations.cookie import SessionCookie, SessionFrontend
from fastapi_sessions.backends.session_backend import SessionBackend
from jose import JWTError
from uuid import uuid4

from container import Container
from core.security_service import SecurityService
from session.session_verifier import BasicVerifier, SessionData

router = APIRouter()


@inject
async def create_session(username: str, response: Response,
                         backend: SessionBackend,
                         cookie: SessionFrontend):

    session = uuid4()
    data = SessionData(username=username)

    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    return session


async def _check_session(request: Request, cookie: SessionCookie,
                         verifier: BasicVerifier):
    cookie(request)
    return await verifier(request)


@inject
async def check_session(request: Request, cookie: SessionCookie = Depends(Provide[Container.cookie]),
                        verifier: BasicVerifier = Depends(Provide[Container.verifier])):
    return await _check_session(request, cookie, verifier)


@inject
async def get_session_data(request: Request, cookie: SessionCookie = Depends(Provide[Container.cookie]),
                           verifier: BasicVerifier = Depends(Provide[Container.verifier])):
    try:
        session_data = await _check_session(request, cookie, verifier)
    except HTTPException as ex:
        print(ex.detail)
        return None
    return session_data


@router.post("/logout")
@inject
async def logout(response: RedirectResponse,
                 request: Request,
                 cookie: SessionFrontend = Depends(Provide[Container.cookie]),
                 backend: SessionBackend = Depends(Provide[Container.session_backend]),
                 auth_server_url: str = Depends(Provide[Container.config.auth_server.url])):
    session_id = cookie(request)
    await backend.delete(session_id)

    cookie.delete_from_response(response)
    return RedirectResponse(f"{auth_server_url}/user/logout")


@router.get("")
@inject
async def auth(token: str,
               response: Response,
               security_service: SecurityService = Depends(
                   Provide[Container.security_service]),
               backend: SessionBackend = Depends(
                   Provide[Container.session_backend]),
               cookie: SessionFrontend = Depends(Provide[Container.cookie])):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security_service.decode_access_token(
            token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    await create_session(username, response, backend, cookie)
    response.status_code = status.HTTP_307_TEMPORARY_REDIRECT
    response.headers["location"] = "/encrypt/"
    return response
