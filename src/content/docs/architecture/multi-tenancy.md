---
title: Multi-Tenancy
description: How PanBot isolates data and operations per business.
---

## Business-Centric Identity

Every operational entity in PanBot is scoped by `business_id`. A single `businesses` table row represents one operational location.

## Current State (Post Sprint 21)

| Aspect | Implementation | Status |
|--------|---------------|--------|
| Data isolation | All queries filtered by `business_id` | Working |
| JWT claims | `user_id`, `role`, `primary_business_id`, `permissions` | Working |
| Phone routing | SIP headers → business lookup | Working |
| User-business mapping | `UserBusinessDB` join table (many-to-many) | Working |
| Role per business | `UserBusinessDB.role` per business | Working |
| Business selection | Post-login business picker (web dashboard) | Working |
| Auth | FastAPI-Users JWT + Logto OIDC (web) | Working |

### UserBusinessDB

```python
class UserBusinessDB(BaseDBModel, table=True):
    user_id: uuid.UUID       # FK → users.id
    business_id: uuid.UUID   # FK → businesses.id
    role: UserRole           # Per-business role (STAFF/OWNER/ADMIN)
    permissions: List[str]   # Per-business permissions (JSONB)
    is_primary: bool         # For business selection UI
```

- `UserDB.business_id` has been **removed** — all business access resolved via `UserBusinessDB`
- `require_business_access()` checks `UserBusinessDB` membership; owner/admin bypass
- `GET /businesses/accessible` returns all businesses a user has access to

## Roles

| Role | Scope | Access |
|------|-------|--------|
| `STAFF` | Single business | Desktop app, day-to-day operations |
| `OWNER` | Multiple businesses | Web dashboard + desktop, management |
| `ADMIN` | All businesses | System-level administration |

## Call Routing

Incoming calls identify the restaurant via SIP headers:

```
Production: sip.h.diversion = restaurant's real phone number
Development: sip.h.to = Telnyx number assigned to restaurant
```

Lookup checks both `businesses.phone_number` and `business_phone_numbers.phone_e164` for multi-line support.

## Channel Isolation (Centrifugo)

Each business subscribes only to `business:{business_id}` channels. JWT tokens scope channel access so businesses cannot see each other's events.
