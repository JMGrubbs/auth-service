from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


PKCE_PATTERN = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")
CHALLENGE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43,128}$")


class OAuthRequestError(ValueError):
    """Raised when an OAuth browser request cannot be trusted."""


@dataclass(frozen=True, slots=True)
class OAuthClient:
    client_id: str
    name: str
    redirect_uris: tuple[str, ...]


class OAuthClientRegistry:
    def __init__(self, clients: list[OAuthClient]) -> None:
        self._clients = {client.client_id: client for client in clients}
        if len(self._clients) != len(clients):
            raise ValueError("OAuth client ids must be unique")

    @classmethod
    def from_json(cls, raw_clients: str) -> "OAuthClientRegistry":
        try:
            parsed = json.loads(raw_clients)
        except json.JSONDecodeError as exc:
            raise ValueError("OAUTH_CLIENTS_JSON must be valid JSON") from exc
        if not isinstance(parsed, list):
            raise ValueError("OAUTH_CLIENTS_JSON must contain a list")

        clients: list[OAuthClient] = []
        for item in parsed:
            if not isinstance(item, dict):
                raise ValueError("Each OAuth client must be an object")
            client_id = item.get("client_id")
            name = item.get("name")
            redirect_uris = item.get("redirect_uris")
            if not isinstance(client_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", client_id):
                raise ValueError("OAuth client_id is invalid")
            if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
                raise ValueError("OAuth client name is invalid")
            if not isinstance(redirect_uris, list) or not redirect_uris:
                raise ValueError("OAuth clients need at least one redirect URI")
            checked = tuple(_validate_registered_redirect_uri(uri) for uri in redirect_uris)
            if len(set(checked)) != len(checked):
                raise ValueError("OAuth redirect URIs must be unique per client")
            clients.append(OAuthClient(client_id, name.strip(), checked))
        return cls(clients)

    def require_redirect_uri(self, client_id: str, redirect_uri: str) -> OAuthClient:
        client = self._clients.get(client_id)
        if client is None or redirect_uri not in client.redirect_uris:
            raise OAuthRequestError("Unknown client or unregistered redirect URI")
        return client

    def allowed_origins(self) -> list[str]:
        origins: set[str] = set()
        for client in self._clients.values():
            for uri in client.redirect_uris:
                parts = urlsplit(uri)
                origins.add(f"{parts.scheme}://{parts.netloc}")
        return sorted(origins)


def _validate_registered_redirect_uri(value: object) -> str:
    if not isinstance(value, str) or value != value.strip() or any(ord(char) < 32 for char in value):
        raise ValueError("OAuth redirect URI is invalid")
    parts = urlsplit(value)
    if parts.fragment or parts.username is not None or parts.password is not None:
        raise ValueError("OAuth redirect URI cannot contain fragment or userinfo")
    if not parts.scheme or not parts.netloc or not parts.hostname:
        raise ValueError("OAuth redirect URI must be absolute")
    loopback = parts.hostname in {"localhost", "127.0.0.1", "::1"}
    if parts.scheme != "https" and not (loopback and parts.scheme == "http"):
        raise ValueError("OAuth redirect URI must use HTTPS except on loopback")
    return value


def verify_pkce(verifier: str, expected_challenge: str) -> bool:
    if not PKCE_PATTERN.fullmatch(verifier) or not CHALLENGE_PATTERN.fullmatch(expected_challenge):
        return False
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    actual = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return hmac.compare_digest(actual, expected_challenge)


def append_authorization_result(redirect_uri: str, *, code: str, state: str) -> str:
    parts = urlsplit(redirect_uri)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key not in {"code", "state"}]
    query.extend((("code", code), ("state", state)))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
