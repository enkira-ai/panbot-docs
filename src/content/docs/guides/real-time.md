---
title: Real-time Integration
description: Centrifugo WebSocket setup for real-time notifications.
---

## Overview

PanBot uses Centrifugo v6 for real-time WebSocket communication between the backend and client applications (desktop and web).

## Architecture

```
Backend services → HTTP API → Centrifugo server → WebSocket → Clients
```

**Key principle**: Backend publishes via HTTP API. Clients subscribe via WebSocket with JWT authentication.

## Namespace Configuration (Single Source of Truth)

All namespaces are defined in `infrastructure/centrifugo/config.json` and auto-generated as constants:

| Namespace | Channel Pattern | Purpose |
|-----------|----------------|---------|
| `business` | `business:{business_id}` | Orders, printer status, operational updates |
| `job` | `job:{job_id}` | Background job progress (onboarding, scraping) |
| `location` | `location:{location_id}` | Legacy location channels |
| `admin` | `admin:{entity_id}` | System admin notifications |

### Generated Constants

Run `make generate-centrifugo-namespaces` (or `make dev` which includes it):

**Backend** (`src/common/realtime/namespaces.py`):
```python
from src.common.realtime.namespaces import channel_for_business
channel = channel_for_business(business_id)  # "business:uuid"
```

**Frontend** (`apps/desktop/src/lib/realtimeNamespaces.ts`):
```typescript
import { channelForBusiness } from './realtimeNamespaces';
const channel = channelForBusiness(businessId);  // "business:uuid"
```

**Never hardcode channel names** — always use generated helpers.

## Authentication

JWT-based channel access:

1. Client requests realtime token via `POST /api/v1/realtime/token`
2. Backend generates JWT scoped to specific business channels
3. Client connects to Centrifugo with JWT token
4. Token auto-refreshes via `createRealtimeTokenManager(businessId)`

## Desktop App Integration

See `apps/desktop/src/lib/centrifugo.ts`:

- Connects on app initialization after auth
- Subscribes to `business:{businessId}` channel
- Order events auto-trigger printing orchestrator
- Reconnection handled automatically

## CORS & Desktop Apps

Desktop apps (Tauri) don't send `Origin` headers, so CORS doesn't apply. Centrifugo allows connections without Origin headers.

For web apps, allowed origins are configured in `infrastructure/centrifugo/config.json`.

See `dev_docs/CENTRIFUGO_CORS_AND_DESKTOP_APPS.md` for details.
