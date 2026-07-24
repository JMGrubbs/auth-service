from __future__ import annotations

import hashlib


class LoginRateLimitError(ValueError):
    """Raised when an authorization login bucket is exhausted."""


class LoginRateLimiter:
    _INCREMENT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""

    def __init__(
        self,
        redis,
        *,
        window_seconds: int,
        email_limit: int,
        ip_limit: int,
    ) -> None:
        self.redis = redis
        self.window_seconds = window_seconds
        self.email_limit = email_limit
        self.ip_limit = ip_limit

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    async def _increment(self, bucket: str, value: str) -> int:
        key = f"oauth:login-limit:{bucket}:{self._digest(value)}"
        return int(
            await self.redis.eval(
                self._INCREMENT_SCRIPT,
                1,
                key,
                self.window_seconds,
            )
        )

    async def check(self, *, ip_address: str, email: str) -> None:
        ip_attempts = await self._increment("ip", ip_address)
        email_attempts = await self._increment("email", email.strip().lower())
        if ip_attempts > self.ip_limit or email_attempts > self.email_limit:
            raise LoginRateLimitError("Too many login attempts")
