---
title: Multi-Tenancy
description: How PanBot isolates data and operations per business.
---

## Business-Centric Identity

Every operational entity in PanBot is scoped by `business_id`. A single `businesses` table row represents one operational location.

## Current State

| Aspect | Implementation | Status |
|--------|---------------|--------|
| Data isolation | All queries filtered by `business_id` | Working |
| JWT claims | `business_id`, `role`, `permissions` in token | Working |
| Phone routing | SIP headers → business lookup | Working |
| User-business mapping | `UserDB.business_id` (single business) | Needs migration |
| Role per business | Global role only | Needs migration |

## Target State (Sprint 21)

| Aspect | Implementation | Status |
|--------|---------------|--------|
| User-business mapping | `UserBusinessDB` join table (one-to-many) | Planned (#29) |
| Role per business | `UserBusinessDB.role` per business | Planned (#29) |
| Business selection | Post-login business picker | Planned (#31) |
| Logto IAM | Unified OAuth with social login | Planned (#30) |

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
