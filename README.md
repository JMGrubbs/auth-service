# Auth Service

A centralized FastAPI identity API with a React/Vite login experience that every registered application can use. Applications redirect users here, Auth Service validates credentials, and the browser returns with a short-lived one-time authorization code. The originating app exchanges that code with PKCE and stores the resulting access token in its own browser session.

Access tokens are **never placed in redirect URLs**.

## Architecture

- **Frontend:** React 19, TypeScript, Vite, and unprivileged Nginx on port `3000`.
- **API:** FastAPI on port `8000`.
- **Database:** PostgreSQL 17 for users and revocation records.
- **Cache:** Redis 7.4 for revocations and single-use authorization codes.
- **Login protocol:** OAuth 2.1-style authorization code flow with mandatory `state` and PKCE S256.

The Nginx frontend proxies `/api/*` to FastAPI, so the shared login page is same-origin. The public browser helper is served with cross-origin module headers. For compatibility with the existing browser API, CORS defaults to `*`; production deployments should set `CORS_ORIGINS_JSON` to an explicit list. Registered callback origins are always added automatically.

## Configure

Prerequisites: Docker Engine and Docker Compose v2.

```bash
cp .env.example .env
cp app/.env.example app/.env
```

Use strong production values for database and signing secrets. Register each app in `OAUTH_CLIENTS_JSON` with an exact callback allowlist:

```json
[
  {
    "client_id": "scrappy-web",
    "name": "Scrappy",
    "redirect_uris": ["https://scrappy.example.com/auth/callback"]
  }
]
```

Non-loopback callback URLs must use HTTPS. Wildcards, fragments, userinfo, host suffix matching, and unregistered paths are rejected.

## Run

```bash
docker compose config
docker compose up --build -d
docker compose ps
```

- Shared login UI: <http://localhost:3000>
- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/v1/health>
- Browser integration helper: <http://localhost:3000/auth-client.js>

Stop without deleting data:

```bash
docker compose down
```

`docker compose down -v` is destructive and removes database/cache volumes.

## Integrate an Application

The frontend serves a small browser helper at `/auth-client.js`. An originating SPA can import it, start login, then finish login on its registered callback route.

```js
import {
  beginLogin,
  completeLogin,
  getAccessToken,
} from "https://auth.example.com/auth-client.js";

// Sign-in button
await beginLogin({
  authUrl: "https://auth.example.com/",
  clientId: "scrappy-web",
  redirectUri: "https://scrappy.example.com/auth/callback",
});

// Registered /auth/callback route
const session = await completeLogin({
  callbackUrl: window.location.href,
  tokenEndpoint: "https://auth.example.com/api/v1/oauth/token",
  clientId: "scrappy-web",
  redirectUri: "https://scrappy.example.com/auth/callback",
});

console.log(session.expiresIn);
// The token is now available from getAccessToken() in sessionStorage
```

The helper:

1. Generates a cryptographically random `state` and PKCE verifier.
2. Redirects to Auth Service with the PKCE challenge.
3. Validates returned `state` on the callback route and rejects browser transactions older than five minutes.
4. Removes `code` and `state` from browser history before exchanging the one-time code.
5. Exchanges the one-time code; the code is client-bound, redirect-bound, expires after two minutes by default, and can only be consumed once.
6. Stores the access token and its absolute expiry in the originating app's browser `sessionStorage` as `auth:access_token`; `getAccessToken()` clears expired values.

Authorization logins use two throttling layers without trusting caller-supplied forwarding headers: Nginx limits the public authorize route by its direct client IP, while Redis limits hashed email identifiers and direct API peer addresses. Configure the Redis window and limits with `OAUTH_LOGIN_RATE_*` values.

JavaScript-accessible tokens can be stolen by an XSS vulnerability in the originating app. Keep that app's CSP and dependencies strict. For apps with a backend-for-frontend, prefer exchanging the code server-side and setting that app's own `HttpOnly`, `Secure`, `SameSite` session cookie instead of JavaScript token storage.

## Tests

```bash
docker compose run --rm --no-deps api python -m unittest discover -s tests -p 'test_*.py'
docker compose --profile test run --rm frontend-test
docker compose --profile test run --rm frontend-test sh -c "npm ci && npm run build"
```

## Existing API

Compatibility endpoints remain under `/api/v1/auth` and `/api/v1/users`. New browser-login endpoints are:

- `GET /api/v1/oauth/client` — validate a client/callback pair and return display metadata.
- `POST /api/v1/oauth/authorize` — authenticate credentials and issue a one-time code redirect.
- `POST /api/v1/oauth/token` — exchange a one-time code and PKCE verifier for a bearer access token.
