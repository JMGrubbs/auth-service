import base64
import hashlib
import unittest
from urllib.parse import parse_qs, urlparse

from core.oauth import (
    OAuthClientRegistry,
    OAuthRequestError,
    append_authorization_result,
    verify_pkce,
)


CLIENTS_JSON = """[
  {
    "client_id": "scrappy-web",
    "name": "Scrappy",
    "redirect_uris": [
      "https://scrappy.example.com/auth/callback",
      "http://localhost:3000/auth/callback"
    ]
  }
]"""


class OAuthClientRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = OAuthClientRegistry.from_json(CLIENTS_JSON)

    def test_accepts_an_exact_registered_redirect_uri(self) -> None:
        client = self.registry.require_redirect_uri(
            "scrappy-web",
            "https://scrappy.example.com/auth/callback",
        )
        self.assertEqual(client.name, "Scrappy")

    def test_rejects_unknown_clients_and_near_match_redirects(self) -> None:
        rejected = (
            ("unknown", "https://scrappy.example.com/auth/callback"),
            ("scrappy-web", "https://evil.example.com/auth/callback"),
            ("scrappy-web", "https://scrappy.example.com.evil.test/auth/callback"),
            ("scrappy-web", "https://scrappy.example.com/auth/callback/extra"),
            ("scrappy-web", "https://scrappy.example.com/auth/callback#fragment"),
            ("scrappy-web", "//scrappy.example.com/auth/callback"),
        )
        for client_id, redirect_uri in rejected:
            with self.subTest(redirect_uri=redirect_uri):
                with self.assertRaises(OAuthRequestError):
                    self.registry.require_redirect_uri(client_id, redirect_uri)

    def test_rejects_registered_redirect_uris_with_fragments_or_userinfo(self) -> None:
        for redirect_uri in (
            "https://scrappy.example.com/auth/callback#fragment",
            "https://user@scrappy.example.com/auth/callback",
        ):
            with self.subTest(redirect_uri=redirect_uri):
                with self.assertRaises(ValueError):
                    OAuthClientRegistry.from_json(
                        '[{"client_id":"bad","name":"Bad","redirect_uris":["'
                        + redirect_uri
                        + '"]}]'
                    )


class PKCETests(unittest.TestCase):
    def test_s256_verifier_matches_its_challenge(self) -> None:
        verifier = "a" * 64
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertTrue(verify_pkce(verifier, challenge))
        self.assertFalse(verify_pkce("b" * 64, challenge))

    def test_rejects_malformed_verifier_or_challenge(self) -> None:
        self.assertFalse(verify_pkce("short", "invalid"))
        self.assertFalse(verify_pkce("a" * 64, "contains+unsafe/characters"))


class RedirectResultTests(unittest.TestCase):
    def test_redirect_contains_only_code_and_state(self) -> None:
        result = append_authorization_result(
            "https://scrappy.example.com/auth/callback?source=auth",
            code="opaque-code",
            state="caller-state",
        )
        parsed = urlparse(result)
        query = parse_qs(parsed.query)
        self.assertEqual(query["code"], ["opaque-code"])
        self.assertEqual(query["state"], ["caller-state"])
        self.assertEqual(query["source"], ["auth"])
        self.assertNotIn("token", result.lower())
        self.assertEqual(parsed.fragment, "")


if __name__ == "__main__":
    unittest.main()
