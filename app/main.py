import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from api.v1.api import api_router
from cache.redis import redis_manager
from core.config import settings
from core.oauth import OAuthClientRegistry
from middleware.request_id import RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.connect()
    yield
    await redis_manager.disconnect()


def _cors_origins() -> list[str]:
    try:
        configured = json.loads(settings.cors_origins_json)
        if not isinstance(configured, list) or not all(isinstance(item, str) for item in configured):
            raise ValueError
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError("CORS_ORIGINS_JSON must be a JSON list of origins") from exc
    oauth_origins = OAuthClientRegistry.from_json(settings.oauth_clients_json).allowed_origins()
    return sorted(set(configured + oauth_origins))


app = FastAPI(
    title="Auth Service",
    description="Central authentication and OAuth 2.1-style PKCE login service",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def prevent_oauth_response_caching(request: Request, call_next):
    response = await call_next(request)
    if request.url.path in {
        "/api/v1/oauth/authorize",
        "/api/v1/oauth/token",
    }:
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response


app.include_router(api_router, prefix="/api/v1")
