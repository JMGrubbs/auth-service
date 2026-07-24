from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from cache.dependencies import get_redis
from core.config import settings
from core.oauth import OAuthClientRegistry, OAuthRequestError, append_authorization_result
from core.security import create_access_token
from db.dependencies import get_session
from repositories.user import login_user
from schemas.oauth import (
    AuthorizationRequest,
    AuthorizationResponse,
    ClientResponse,
    TokenRequest,
    TokenResponse,
)
from services.authorization_codes import (
    AuthorizationCodeError,
    AuthorizationCodeStore,
    AuthorizationGrant,
)
from services.login_rate_limit import LoginRateLimitError, LoginRateLimiter


router = APIRouter(tags=["oauth"])
NO_STORE_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
}


def get_client_registry() -> OAuthClientRegistry:
    return OAuthClientRegistry.from_json(settings.oauth_clients_json)


def get_code_store(redis: Redis = Depends(get_redis)) -> AuthorizationCodeStore:
    return AuthorizationCodeStore(redis, ttl_seconds=settings.authorization_code_expire_seconds)


def get_login_limiter(redis: Redis = Depends(get_redis)) -> LoginRateLimiter:
    return LoginRateLimiter(
        redis,
        window_seconds=settings.oauth_login_rate_window_seconds,
        email_limit=settings.oauth_login_email_limit,
        ip_limit=settings.oauth_login_ip_limit,
    )


@router.get("/client", response_model=ClientResponse)
async def client_details(
    client_id: str,
    redirect_uri: str,
    registry: OAuthClientRegistry = Depends(get_client_registry),
) -> ClientResponse:
    try:
        client = registry.require_redirect_uri(client_id, redirect_uri)
    except OAuthRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ClientResponse(client_id=client.client_id, name=client.name)


@router.post("/authorize", response_model=AuthorizationResponse)
async def authorize(
    payload: AuthorizationRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
    registry: OAuthClientRegistry = Depends(get_client_registry),
    code_store: AuthorizationCodeStore = Depends(get_code_store),
    login_limiter: LoginRateLimiter = Depends(get_login_limiter),
) -> AuthorizationResponse:
    try:
        registry.require_redirect_uri(payload.client_id, payload.redirect_uri)
    except OAuthRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        await login_limiter.check(
            ip_address=http_request.client.host if http_request.client else "unknown",
            email=str(payload.email),
        )
    except LoginRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(settings.oauth_login_rate_window_seconds)},
        ) from exc

    user = await login_user(session, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    code = await code_store.issue(
        AuthorizationGrant(
            user_id=str(user.id),
            client_id=payload.client_id,
            redirect_uri=payload.redirect_uri,
            code_challenge=payload.code_challenge,
        )
    )
    return AuthorizationResponse(
        redirect_url=append_authorization_result(
            payload.redirect_uri,
            code=code,
            state=payload.state,
        )
    )


@router.post("/token", response_model=TokenResponse)
async def exchange_token(
    payload: TokenRequest,
    response: Response,
    registry: OAuthClientRegistry = Depends(get_client_registry),
    code_store: AuthorizationCodeStore = Depends(get_code_store),
) -> TokenResponse:
    try:
        registry.require_redirect_uri(payload.client_id, payload.redirect_uri)
        grant = await code_store.consume(
            code=payload.code,
            client_id=payload.client_id,
            redirect_uri=payload.redirect_uri,
            code_verifier=payload.code_verifier,
        )
    except (OAuthRequestError, AuthorizationCodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization code",
            headers=NO_STORE_HEADERS,
        ) from exc

    response.headers.update(NO_STORE_HEADERS)
    return TokenResponse(
        access_token=create_access_token(subject=grant.user_id),
        expires_in=settings.access_token_expire_minutes * 60,
    )
