import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from api.v1.api import api_router
from cache.redis import redis_manager
from core.config import settings
from middleware.request_id import RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.connect()
    yield
    await redis_manager.disconnect()


# def _cors_origins() -> list[str]:
#     try:
#         configured = json.loads(settings.cors_origins_json)
#         print(configured, flush=True)
#         if not isinstance(configured, list) or not all(isinstance(item, str) for item in configured):
#             raise ValueError
#     except (json.JSONDecodeError, ValueError) as exc:
#         raise RuntimeError("CORS_ORIGINS_JSON must be a JSON list of origins") from exc

#     return sorted(set(configured))


app = FastAPI(
    title="Auth Service",
    description="Central authentication and OAuth 2.1-style PKCE login service",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dvaults.johnmgrubbs.io",
        "http://100.79.167.31:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
