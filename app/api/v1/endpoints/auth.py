from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from models.user import User
from schemas.user import UserLogin, AuthorizedUser
from core.security import create_access_token
from auth.dependencies import get_current_active_user, blacklist_current_token
from db.dependencies import get_session
from repositories.user import login_user
from core.config import settings

router = APIRouter(tags=["auth"])

@router.post("/login")
async def login_route(
    response: Response,
    UserLogin: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str] | AuthorizedUser:
    logged_in_user = await login_user(
        session,
        UserLogin.email,
        UserLogin.password,
    )
    if not logged_in_user:
        return {"message": "Invalid email or password"}

    user_token = create_access_token(subject=str(logged_in_user.id))

    auth_user = AuthorizedUser(
        id=str(logged_in_user.id),
        username=logged_in_user.email,
        is_admin=logged_in_user.is_admin,
    )

    response.set_cookie(
        key=settings.cookie_key,
        value=user_token,
        httponly=True,
        secure=True,      # True in production over HTTPS
        samesite="lax",    # often fine for same-site frontend/backend
        max_age=60 * 60,
        expires=60 * 60,
        path="/",
    )

    return auth_user


@router.get("/me")
async def read_me_route(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    print(f"Current user: {current_user.email}, ID: {current_user.id}, Admin: {current_user.is_admin}", flush=True)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "username": current_user.email,
    }


@router.get("/token-check")
async def token_check_route(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    return {
        "message": f"Token is valid for user {current_user.email}",
        "status": True,
    }


@router.post("/logout")
async def logout_route(
    revoked: bool = Depends(blacklist_current_token),
) -> dict[str, str]:
    return {"message": "Successfully logged out"}


@router.get("/is-admin")
async def is_admin_route(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, bool]:
    return {"is_admin": current_user.is_admin}
