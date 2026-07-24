# AGENTS.md

## Purpose

`auth-service` is the centralized identity service for the user's applications. It owns user credentials, authentication, bearer-token issuance and validation, logout/revocation, and the shared browser login journey that returns users to registered client applications.

## Architecture

- `app/`: Python FastAPI API.
- PostgreSQL: users and token-revocation records in the `auth` schema.
- Redis: revocation cache and short-lived browser authorization state.
- `frontend/`: React + TypeScript + Vite login UI (added as part of the shared-login work).
- `docker-compose.yaml`: local/container runtime for API, frontend, PostgreSQL, and Redis.
- Browser login uses an OAuth 2.1-style authorization-code flow with PKCE. Redirect URIs must match a configured client exactly. Access tokens must never be placed in redirect URLs.

## Important Paths

- `app/main.py`: FastAPI application and middleware.
- `app/api/v1/`: HTTP route registration and endpoint modules.
- `app/core/`: settings and cryptographic/token primitives.
- `app/repositories/`: persistence access.
- `app/schemas/`: request/response models.
- `app/alembic/`: database migrations.
- `tests/`: Python tests; legacy MCP/live-integration scripts remain here.
- `frontend/src/`: React application code.
- `frontend/src/**/*.test.*`: Vitest/Testing Library tests.

## Commands

Run all commands from `/home/lowery/auth-service` on `vm-work-dev-db`.

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail 120 api frontend
docker compose run --rm --no-deps api python -m unittest discover -s tests -p 'test_*.py'
docker compose --profile test run --rm frontend-test
docker compose --profile test run --rm frontend-test sh -c "npm ci && npm run build"
docker compose down
```

Use `docker compose down` only when stopping the project is intended. Never add `-v` unless destructive volume removal is explicitly authorized.

## Configuration

- Never read, print, commit, or copy values from `.env` or `app/.env` into tracked files.
- Document required keys with placeholders in `.env.example` files.
- Browser clients are registered through `OAUTH_CLIENTS_JSON`; each client has a stable `client_id`, display name, and exact redirect URI allowlist.
- Keep the public auth origin and CORS origins environment-driven.
- Secrets, signing keys, passwords, and issued tokens must not appear in logs or URLs.

## Code and Security Conventions

- Use strict test-driven development: add one failing behavioral test, observe the expected failure, implement the smallest passing change, and rerun the focused and full suites.
- Use typed Pydantic schemas and explicit HTTP status codes.
- Require `state` and PKCE (`S256`) for browser authorization.
- Authorization codes are opaque, short-lived, single-use, and bound to client, redirect URI, user, and PKCE challenge.
- Match redirect URIs exactly; do not use host suffixes, wildcards, partial matches, or arbitrary return URLs.
- Prefer HttpOnly/Secure/SameSite cookies for auth-service browser sessions. Calling apps should exchange codes and establish their own session; do not redirect bearer tokens.
- Preserve compatibility of existing API routes unless an intentional migration is documented.
- Keep React components accessible, responsive, keyboard-friendly, and explicit about loading/error states.

## Git and Delivery

- Inspect branch, remote, and worktree before every change.
- Keep changes isolated to the shared-login feature and do not stage unrelated files.
- Build, test, run, and browser-verify through Docker Compose before committing or pushing.
- Do not commit or push until the user requests it or the current task explicitly includes delivery to GitHub.
