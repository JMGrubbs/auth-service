import asyncio
import base64
import hashlib
import unittest

from services.authorization_codes import (
    AuthorizationCodeError,
    AuthorizationCodeStore,
    AuthorizationGrant,
)


class MemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def set(self, key: str, value: str, *, ex: int, nx: bool = False) -> bool:
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def getdel(self, key: str) -> str | None:
        return self.values.pop(key, None)


class AuthorizationCodeStoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.redis = MemoryRedis()
        self.store = AuthorizationCodeStore(self.redis, ttl_seconds=120)
        self.verifier = "v" * 64
        self.challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.grant = AuthorizationGrant(
            user_id="11111111-1111-1111-1111-111111111111",
            client_id="scrappy-web",
            redirect_uri="https://scrappy.example.com/auth/callback",
            code_challenge=self.challenge,
        )

    async def test_code_is_single_use_and_returns_the_bound_grant(self) -> None:
        code = await self.store.issue(self.grant)

        consumed = await self.store.consume(
            code=code,
            client_id=self.grant.client_id,
            redirect_uri=self.grant.redirect_uri,
            code_verifier=self.verifier,
        )
        self.assertEqual(consumed, self.grant)

        with self.assertRaises(AuthorizationCodeError):
            await self.store.consume(
                code=code,
                client_id=self.grant.client_id,
                redirect_uri=self.grant.redirect_uri,
                code_verifier=self.verifier,
            )

    async def test_wrong_pkce_verifier_or_binding_invalidates_the_code(self) -> None:
        code = await self.store.issue(self.grant)
        with self.assertRaises(AuthorizationCodeError):
            await self.store.consume(
                code=code,
                client_id="different-client",
                redirect_uri=self.grant.redirect_uri,
                code_verifier=self.verifier,
            )

        with self.assertRaises(AuthorizationCodeError):
            await self.store.consume(
                code=code,
                client_id=self.grant.client_id,
                redirect_uri=self.grant.redirect_uri,
                code_verifier=self.verifier,
            )


if __name__ == "__main__":
    unittest.main()
