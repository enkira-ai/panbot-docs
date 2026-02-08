---
title: Authentication System
description: Current and planned authentication architecture.
---

## Current State

### Backend (FastAPI)

| Feature | Implementation |
|---------|---------------|
| Auth library | fastapi-users |
| Token type | JWT (access + refresh) |
| Claims | `user_id`, `business_id`, `role`, `permissions` |
| Validation | Claim-first (no DB lookup per request) |
| Token revocation | `users.token_version` field |
| DB validation | Optional via `AUTH_VALIDATE_DB_ON_REQUEST` flag |

### Desktop App

| Feature | Implementation |
|---------|---------------|
| Login | Email/phone → POST /api/v1/auth/login |
| Token storage | localStorage |
| Auto-refresh | `AutoRefreshTokenManager` with JWT config from backend |
| Business context | From JWT claims (`business_id`) |
| Realtime token | Separate JWT via POST /api/v1/realtime/token |

### Web Dashboard

| Feature | Implementation |
|---------|---------------|
| Auth library | NextAuth v5 beta |
| Providers | Google, Microsoft Entra ID, Apple |
| Strategy | JWT sessions (no DB sessions) |
| Token exchange | Not yet wired to backend JWT |

## Target State: Logto Migration (Sprint 21 Phase 2)

| Feature | Planned |
|---------|---------|
| IAM provider | Logto (replaces NextAuth + fastapi-users) |
| Social login | Google, Apple via Logto |
| Token format | OIDC tokens validated by backend |
| Multi-business | UserBusinessDB with per-business roles |
| Desktop | Logto SDK (replaces direct JWT login) |
| Web | Logto SDK (replaces NextAuth) |

### Migration Checklist

- [ ] Set up Logto instance
- [ ] Replace NextAuth with Logto SDK in web app
- [ ] Update backend for OIDC token validation
- [ ] Create UserBusinessDB sync endpoint
- [ ] Handle Logto webhooks for user lifecycle
- [ ] Migrate existing users
- [ ] Update desktop app auth flow

## JWT Token Configuration

All token lifetimes are configured in backend settings:

| Setting | Purpose |
|---------|---------|
| `JWT_ACCESS_TOKEN_MINUTES` | Access token lifetime |
| `JWT_REFRESH_TOKEN_DAYS` | Refresh token lifetime |
| `JWT_ALGORITHM` | Signing algorithm (HS256) |
| `JWT_SECRET` | Token signing secret |

Desktop app fetches these settings from `/api/v1/realtime/status` for consistent token management.

## Roles & Permissions

| Role | Login Method | Access |
|------|-------------|--------|
| STAFF | Phone number | Single business, desktop app |
| OWNER | Email/OAuth | Multiple businesses, web + desktop |
| ADMIN | Email/OAuth | All businesses, system settings |

Target: Per-business roles via `UserBusinessDB.role`, with OWNER controlling staff access.
