---
title: Data Flows
description: Key data flows through the PanBot system.
---

## Phone Call → Order Flow

```
Customer dials restaurant → Telnyx SIP → LiveKit Agent
    → Agent identifies restaurant (SIP headers)
    → Agent loads menu + customer data (via services)
    → Agent takes order (voice conversation)
    → Order created via service layer → PostgreSQL
    → Event published → Centrifugo → Desktop app
    → Desktop app prints receipt (ESC/POS or IPP)
    → Post-call processing → Langfuse traces
```

## Authentication Flows

### Desktop App (Staff)
```
Login form → POST /api/v1/auth/login → JWT (access + refresh)
    → Stored in localStorage
    → Auto-refresh via GenericTokenManager
    → Business data from JWT claims (business_id)
    → Realtime token via POST /api/v1/realtime/token
```

### Web Dashboard (Owner)
```
OAuth button → NextAuth → Google/Microsoft/Apple
    → JWT session (NextAuth)
    → Backend token exchange (TODO: not yet wired)
    → Business list via GET /api/v1/businesses/my
```

### Target State: Logto
```
OAuth → Logto SDK → OIDC tokens
    → Backend validates OIDC token
    → UserBusinessDB lookup → business list
    → Per-business role (STAFF/OWNER/ADMIN)
```

## Real-time Event Flow

```
Backend service → HTTP API → Centrifugo server
    → WebSocket push → Desktop/Web clients
    → Channel: business:{business_id}
```

| Event Type | Published By | Consumed By |
|-----------|-------------|-------------|
| `order.created` | Order service | Desktop (auto-print) |
| `order.updated` | Order service | Desktop + Web |
| `printer.status` | Printer service | Desktop |
| `job.progress` | Temporal workflow | Web onboarding UI |

## Printer Data Flow

```
Order event → Printing orchestrator (TS)
    → Mustache template rendering
    → Print queue (Rust) → ESC/POS or IPP
    → Retry with exponential backoff (max 3)
```

### Printer Cache Sync

```
Desktop save → Local JSON store (Tauri)
    → Per-key 2-minute debounce timer
    → Event emitted to JS layer
    → JS calls backend API (OpenAPI client)
    → Backend persists to PostgreSQL
```

## Menu Data Flow

```
Owner edits menu (Web or Desktop)
    → API update → PostgreSQL (menu_data JSONB)
    → Agent loads fresh menu on next call
    → Desktop syncs via local store (Tauri Store plugin)
    → Conflict resolution on version mismatch
```
