from fastapi import APIRouter, Depends, Response, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from models.user import User
from schemas.user import UserLogin, AuthorizedUser, AuthorizedUserInternal, UserSchema
from core.security import create_access_token
from auth.dependencies import get_current_user, blacklist_current_token
from db.dependencies import get_session
from repositories.user import login_user
from core.config import settings

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

router = APIRouter(tags=["auth"])

@router.post("/login")
async def login_route(
    response: Response,
    UserLogin: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> AuthorizedUserInternal | AuthorizedUser:
    logged_in_user: User | None = await login_user(
        session,
        UserLogin.email,
        UserLogin.password,
    )

    if not logged_in_user:
        raise CREDENTIALS_EXCEPTION

    user_token = create_access_token(subject=str(logged_in_user.id))

    is_internal = UserLogin.internal
    if is_internal:
        internal_auth_user = AuthorizedUserInternal(
            id=str(logged_in_user.id),
            username=logged_in_user.email,
            is_admin=logged_in_user.is_admin,
            token=user_token if UserLogin.internal else None
        )
        return internal_auth_user

    auth_user = AuthorizedUser(
        username=logged_in_user.email,
    )

    if not is_internal:
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


@router.api_route("/me", methods=["GET", "POST"])
async def read_me_route(
    request: Request,
    current_user: UserSchema = Depends(get_current_user),
) -> AuthorizedUserInternal | AuthorizedUser:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Forbidden")

    if request.method == "POST":
        return AuthorizedUserInternal(
            id=str(current_user.id),
            username=current_user.email,
            is_admin=current_user.is_admin,
            token=current_user.token
        )
    elif request.method == "GET":
        return AuthorizedUser(
            username=current_user.email,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Method not allowed",
        )


@router.get("/token-check")
async def token_check_route(
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    return {"is_admin": current_user.is_admin}
