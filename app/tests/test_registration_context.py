import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from api.v1.endpoints.oauth import register_for_authorization, validate_authorization
from core.oauth import OAuthClientRegistry
from schemas.oauth import AuthorizationContext, AuthorizationRequest
from schemas.user import UserCreate


CLIENTS_JSON = """[
  {
    "client_id": "watchtower-web",
    "name": "The Watchtower",
    "redirect_uris": ["http://localhost:5174/auth/callback"]
  }
]"""


def valid_context(**overrides):
    values = {
        "client_id": "watchtower-web",
        "redirect_uri": "http://localhost:5174/auth/callback",
        "state": "state-from-watchtower",
        "code_challenge": "a" * 43,
        "code_challenge_method": "S256",
    }
    values.update(overrides)
    return AuthorizationContext(**values)


class AuthorizationContextTests(unittest.IsolatedAsyncioTestCase):
    async def test_validates_the_complete_registered_authorization_context(self) -> None:
        registry = OAuthClientRegistry.from_json(CLIENTS_JSON)

        result = await validate_authorization(valid_context(), registry)

        self.assertEqual(result.client_id, "watchtower-web")
        self.assertEqual(result.name, "The Watchtower")

    async def test_rejects_an_unregistered_redirect_before_registration(self) -> None:
        registry = OAuthClientRegistry.from_json(CLIENTS_JSON)

        with self.assertRaises(HTTPException) as raised:
            await validate_authorization(
                valid_context(redirect_uri="https://attacker.example/callback"),
                registry,
            )

        self.assertEqual(raised.exception.status_code, 400)

    def test_rejects_malformed_pkce_context(self) -> None:
        with self.assertRaises(ValidationError):
            valid_context(code_challenge="short", code_challenge_method="plain")

    async def test_rejects_an_unregistered_redirect_before_the_user_write(self) -> None:
        registry = OAuthClientRegistry.from_json(CLIENTS_JSON)
        payload = AuthorizationRequest(
            **valid_context(redirect_uri="https://attacker.example/callback").model_dump(),
            email="person@example.com",
            password="SecurePass1!",
        )

        with patch(
            "api.v1.endpoints.oauth.register_user",
            new_callable=AsyncMock,
        ) as register_user:
            with self.assertRaises(HTTPException):
                await register_for_authorization(payload, None, registry)

        register_user.assert_not_awaited()


class PasswordSemanticsTests(unittest.TestCase):
    def test_registration_preserves_password_whitespace(self) -> None:
        user = UserCreate(email="person@example.com", password=" SecurePass1! ")

        self.assertEqual(user.password, " SecurePass1! ")


if __name__ == "__main__":
    unittest.main()
