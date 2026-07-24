from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import asdict, dataclass
from typing import Protocol

from core.oauth import verify_pkce


class RedisCodeClient(Protocol):
    async def set(self, key: str, value: str, *, ex: int, nx: bool = False) -> bool: ...
    async def getdel(self, key: str) -> str | None: ...


class AuthorizationCodeError(ValueError):
    """Raised when an authorization code is invalid, expired, or already used."""


@dataclass(frozen=True, slots=True)
class AuthorizationGrant:
    user_id: str
    client_id: str
    redirect_uri: str
    code_challenge: str


class AuthorizationCodeStore:
    def __init__(self, redis: RedisCodeClient, *, ttl_seconds: int = 120) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    async def issue(self, grant: AuthorizationGrant) -> str:
        for _ in range(3):
            code = secrets.token_urlsafe(32)
            created = await self.redis.set(
                self._key(code),
                json.dumps(asdict(grant)),
                ex=self.ttl_seconds,
                nx=True,
            )
            if created:
                return code
        raise RuntimeError("Could not allocate an authorization code")

    async def consume(
        self,
        *,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> AuthorizationGrant:
        if not 32 <= len(code) <= 256:
            raise AuthorizationCodeError("Invalid authorization code")
        raw_grant = await self.redis.getdel(self._key(code))
        if raw_grant is None:
            raise AuthorizationCodeError("Invalid or expired authorization code")
        try:
            grant = AuthorizationGrant(**json.loads(raw_grant))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise AuthorizationCodeError("Invalid authorization code") from exc
        if grant.client_id != client_id or grant.redirect_uri != redirect_uri:
            raise AuthorizationCodeError("Authorization code binding mismatch")
        if not verify_pkce(code_verifier, grant.code_challenge):
            raise AuthorizationCodeError("PKCE verification failed")
        return grant

    @staticmethod
    def _key(code: str) -> str:
        digest = hashlib.sha256(code.encode("ascii", errors="ignore")).hexdigest()
        return f"oauth:code:{digest}"
