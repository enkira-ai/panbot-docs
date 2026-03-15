---
title: Authentication System
description: Current authentication architecture for PanBot.
---

## Overview

PanBot uses a **hybrid auth system**: FastAPI-Users JWT for the backend core, Logto OIDC for the web dashboard, and device + PIN auth for the desktop app. All auth is claim-first (no DB lookups per request).

## Backend (FastAPI)

| Feature | Implementation |
|---------|---------------|
| Auth library | fastapi-users |
| Token type | JWT (access + refresh) |
| Claims | `user_id`, `primary_business_id`, `role`, `permissions` |
| Validation | Claim-first (no DB lookup per request) |
| Token revocation | `users.token_version` field |
| DB validation | Optional via `AUTH_VALIDATE_DB_ON_REQUEST` flag |
| OIDC | Logto token validation via `src/auth/oidc.py` |

### Auth Dependencies

| Dependency | Behavior |
|------------|----------|
| `get_current_user()` | Wraps fastapi-users, returns `business_id` (primary) and `business_ids` (all accessible) |
| `require_admin()` | Requires `is_superuser` or `business:admin` permission |
| `require_business_access()` | Checks `UserBusinessDB` membership; owner/admin bypass |
| `get_current_api_key()` | Validates `X-API-Key` header (prefix: `cfood_`) |

## Multi-Tenant Auth (UserBusinessDB)

- `UserBusinessDB` is the source of truth for user-to-business mappings
- `UserDB.business_id` column has been **removed** — all business access is resolved via `UserBusinessDB`
- Roles are stored per-business in `UserBusinessDB.role` (STAFF/OWNER/ADMIN)
- Realtime/Centrifugo token requests check against the full `business_ids` list

## Desktop App (JWT Login)

| Feature | Implementation |
|---------|---------------|
| Login | Email/phone → POST /api/v1/auth/login |
| Token storage | localStorage |
| Auto-refresh | `AutoRefreshTokenManager` with JWT config from backend |
| Business context | From JWT claims (`business_id`) |
| Realtime token | Separate JWT via POST /api/v1/realtime/token |

## Desktop App (Device + PIN Login)

| Feature | Implementation |
|---------|---------------|
| Device identity | One-time pairing code → permanent device token |
| Staff identity | 4-6 digit PIN per staff member per business |
| Token storage | `device_token` + `operator_session_token` in localStorage |
| Session lifetime | 8 hours (operator session JWT) |
| Brute-force protection | 5 attempts then 15-minute lockout |

See [Device Authentication guide](/guides/device-authentication/) for the complete flow.

## Web Dashboard (Logto OIDC)

| Feature | Implementation |
|---------|---------------|
| Auth provider | Logto Cloud (OIDC) |
| Frontend SDK | Logto React SDK (replaced NextAuth) |
| Social login | Google, Microsoft, Apple via Logto |
| Token exchange | `POST /auth/oidc/callback` exchanges Logto auth code for backend JWT |
| Business selection | Post-login business picker from `GET /businesses/accessible` |

See [Logto Auth guide](/guides/logto-auth/) for setup details.

## JWT Token Configuration

All token lifetimes are configured in backend settings:

| Setting | Purpose |
|---------|---------|
| `JWT_ACCESS_TOKEN_MINUTES` | Access token lifetime (default: 30 min) |
| `JWT_REFRESH_TOKEN_DAYS` | Refresh token lifetime (default: 30 days) |
| `JWT_ALGORITHM` | Signing algorithm (HS256) |
| `JWT_SECRET` | Token signing secret |

Desktop app fetches these settings from `/api/v1/realtime/status` for consistent token management.

## Roles & Permissions

| Role | Login Method | Access |
|------|-------------|--------|
| STAFF | PIN on paired device | Single business, desktop app |
| OWNER | Email/OAuth or PIN | Multiple businesses, web + desktop |
| ADMIN | Email/OAuth | All businesses, system settings |
