from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from core.security import decode_access_token
from core.config import settings
from db.dependencies import get_session
from repositories.user import get_user_by_id
from repositories.jwt_token_blacklist import is_token_blacklisted_db, insert_blacklisted_token
from cache.helpers import CacheHelper
from cache.dependencies import get_cache_helper
from models.user import User

async def check_token_blacklist(
    token: str,
    session: AsyncSession,
    cache: CacheHelper,
) -> bool:
    try:
        payload = decode_access_token(token)
        token_jti = payload.get("jti")

        exp = payload.get("exp")
        exp = int(exp) if exp is not None else 0

        if not token_jti or exp <= int(datetime.utcnow().timestamp()):
            return True
    except Exception:
        return True

    blacklist_status = await is_token_blacklisted_db(
        session=session,
        jti=token_jti,
        cache=cache,
    )
    return blacklist_status


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
    cache: CacheHelper = Depends(get_cache_helper),
) -> User:
    token: str | None = request.cookies.get(settings.cookie_key) or None
    assert token is not None, "Token should not be None"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_blacklisted = await check_token_blacklist(token=token, session=session, cache=cache)
    if token_blacklisted:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception

        user_id: str = str(sub)
    except Exception:
        raise credentials_exception

    user = await get_user_by_id(session, str(user_id))
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    print(f"Current user: {current_user.email}, ID: {current_user.id}, Admin: {current_user.is_admin}", flush=True)
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def blacklist_current_token(
    request: Request,
    session: AsyncSession = Depends(get_session),
    cache: CacheHelper = Depends(get_cache_helper),
) -> bool:
    token: str | None = request.cookies.get(settings.cookie_key) or None
    assert token is not None, "Token should not be None"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        token_jti = payload.get("jti")
        if not token_jti:
            raise credentials_exception
    except Exception as e:
        raise credentials_exception

    insert_blacklisted_token_status = await insert_blacklisted_token(
        session=session,
        jti=token_jti,
        cache=cache,
    )
    return bool(insert_blacklisted_token_status)