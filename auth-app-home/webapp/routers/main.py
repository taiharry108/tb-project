from datetime import timedelta
from typing import List
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, Form, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_sessions.backends.session_backend import SessionBackend
from fastapi_sessions.frontends.session_frontend import SessionFrontend
from fastapi_sessions.frontends.implementations import SessionCookie

from pydantic import EmailStr
from urllib.parse import quote
from uuid import uuid4

from container import Container
from core.user_service import UserService
from core.security_service import SecurityService
from core.models.user import User
from database.database_service import DatabaseService
from session.session_verifier import BasicVerifier, SessionData

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")


templates = Jinja2Templates(directory="templates")


@inject
async def create_session(username: str, response: Response,
                         backend: SessionBackend,
                         cookie: SessionFrontend):

    session = uuid4()
    data = SessionData(username=username)

    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    return session


@inject
async def get_session_data(request: Request, cookie: SessionCookie = Depends(Provide[Container.cookie]),
                           verifier: BasicVerifier = Depends(Provide[Container.verifier])):
    try:
        cookie(request)
        session_data = await verifier(request)
    except:
        return None
    return session_data


def create_access_token(sub: str, security_service: SecurityService) -> str:
    access_token_expires = timedelta(
        minutes=security_service.access_token_expire_minutes)
    access_token = security_service.create_access_token(
        data={"sub": sub}, expires_delta=access_token_expires
    )
    return access_token


@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request, redirect_url: str):
    return templates.TemplateResponse("login.html", {"request": request, "redirect_url": redirect_url})


@router.post("/signup")
@inject
async def signup(user_service: UserService = Depends(Provide[Container.user_service]),
                 username: EmailStr = Form(...), password: str = Form(...),
                 db_service: DatabaseService = Depends(
                     Provide[Container.db_service]),
                 ):
    db_user = None
    async with db_service.session() as session:
        async with session.begin():
            db_user = await user_service.create_user(session, username, password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )

    return User(email=username, is_active=db_user.is_active)


@router.post("/logout")
@inject
async def logout(response: Response,
                 request: Request,
                 cookie: SessionFrontend = Depends(Provide[Container.cookie]),
                 backend: SessionBackend = Depends(Provide[Container.session_backend])):    
    session_id = cookie(request)
    await backend.delete(session_id)

    cookie.delete_from_response(response)
    response.status_code = status.HTTP_200_OK
    return {"success": True}


@router.post("/login")
@inject
async def login_for_access_token(
        response: Response,
        username: str = Form(...), password: str = Form(...),
        redirect_url: str = Form(...),
        db_service: DatabaseService = Depends(Provide[Container.db_service]),
        user_service: UserService = Depends(Provide[Container.user_service]),
        security_service: SecurityService = Depends(
            Provide[Container.security_service]),
        backend: SessionBackend = Depends(Provide[Container.session_backend]),
        cookie: SessionFrontend = Depends(Provide[Container.cookie]),
        allowed_redirect: List[str] = Depends(Provide[Container.config.allowed_redirect])):
    if redirect_url not in allowed_redirect:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    db_user = None
    async with db_service.session() as session:
        async with session.begin():
            db_user = await user_service.get_user(session, username)
    if not db_user or not user_service.authenticate_user(db_user, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(db_user.email, security_service)
    await create_session(username, response, backend, cookie)
    response.status_code = status.HTTP_302_FOUND
    response.headers['location'] = quote(
        f"{redirect_url}?token={access_token}", safe=":/%#?=@[]!$&'()*+,;")
    return response


@router.get("/whoami")
@inject
async def whoami(session_data: SessionData = Depends(get_session_data)):
    return session_data


@router.get("/auth", response_class=RedirectResponse)
@inject
async def authenticate(request: Request,
                        redirect_url: str,
                       session_data: SessionData = Depends(get_session_data),
                       security_service: SecurityService = Depends(
                           Provide[Container.security_service]),
                       allowed_redirect: List[str] = Depends(Provide[Container.config.allowed_redirect])):
    if redirect_url not in allowed_redirect:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if session_data is None:
        return f"./?redirect_url={redirect_url}"
    access_token = create_access_token(session_data.username, security_service)
    return f"{redirect_url}?token=" + access_token
