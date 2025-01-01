from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from kink import di
from uuid import uuid4

from services import TeslaService, RedisService

router = APIRouter()


@router.get("/login")
async def login(tesla_service: TeslaService = Depends(lambda: di[TeslaService])):
    scope = "openid user_data vehicle_device_data vehicle_cmds vehicle_charging_cmds energy_device_data energy_cmds offline_access"
    redirect_uri = tesla_service.redirect_uri
    client_id = tesla_service.client_id
    response_type = "code"
    locale = "en-US"
    prompt = "login"
    tesla_auth_api_domain = tesla_service.tesla_auth_api_domain
    return RedirectResponse(
        f"https://{tesla_auth_api_domain}/oauth2/v3/authorize?client_id={client_id}&scope={scope}&redirect_uri={redirect_uri}&response_type={response_type}&locale={locale}&prompt={prompt}"
    )


@router.get("/redirect")
async def redirect(
    locale: str,
    code: str,
    issuer: str,
    tesla_service: TeslaService = Depends(lambda: di[TeslaService]),
    redis_service: RedisService = Depends(lambda: di[RedisService]),
):
    session_data = await tesla_service.fetch_access_token(code)

    user_session_id = str(uuid4())
    redis_service.set_session_data(user_session_id, session_data)
    resp = RedirectResponse("/")
    resp.set_cookie("user_session_id", user_session_id)
    return resp


@router.get("/refresh")
async def refresh(
    request: Request,
    redis_service: RedisService = Depends(lambda: di[RedisService]),
    tesla_service: TeslaService = Depends(lambda: di[TeslaService]),
):
    user_session_id = request.cookies.get("user_session_id")
    session_data = redis_service.get_session_data(user_session_id)
    try:
        new_session_data = await tesla_service.refresh_token(session_data.refresh_token)
    except:
        return RedirectResponse("/auth/login")

    redis_service.set_session_data(user_session_id, new_session_data)
    return RedirectResponse("/")


async def verify_user(
    request: Request, redis_service: RedisService = Depends(lambda: di[RedisService])
) -> bool:
    user_session_id = request.cookies.get("user_session_id")

    if not user_session_id:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/auth/login"},
        )
    if session_data := redis_service.get_session_data(user_session_id):
        if session_data.is_expired:
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": "/auth/refresh"},
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/auth/login"},
        )
    request.state.session_data = session_data
    return True
