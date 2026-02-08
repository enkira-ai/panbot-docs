---
title: System Overview
description: High-level architecture of the PanBot restaurant phone agent system.
---

PanBot is an AI-powered restaurant phone assistant handling SIP calls via Telnyx + LiveKit Agents. It takes orders, manages reservations, and provides customer service for multiple restaurants (multi-tenant).

## System Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Server | FastAPI (Python) | REST endpoints, auth, business logic |
| Telephony Agent | LiveKit + Python | Voice AI for phone calls |
| Web Dashboard | Next.js 16 + React 19 | Owner/admin management UI |
| Desktop App | React 19 + Tauri 2 (Rust) | Restaurant staff operations + printing |
| Real-time | Centrifugo v6 | WebSocket push notifications |
| Database | PostgreSQL 15+ | Primary data store |
| Cache | Redis 7+ | Session/data caching |
| Telephony | Telnyx | SIP provider for phone calls |
| Observability | Langfuse | LLM tracing via OpenTelemetry |

## Dependency Flow

```
agents / api / workers  →  services  →  common
```

- APIs and agents never access the database directly — they go through the services layer
- `common/` never imports from higher layers
- Agent tools call service methods directly (in-process)

## Key Entry Points

| Entry Point | File | Port |
|-------------|------|------|
| API Server | `src/api/main.py` | 8000 |
| Telephony Agent | `src/agents/telephony/entrypoint.py` | LiveKit |
| Scraper Worker | `src/workers/scraper_worker.py` | Background |
| Desktop App | `apps/desktop/` | 1420 (dev) |
| Web Dashboard | `apps/web/` | 3000 (dev) |
| Centrifugo | `infrastructure/centrifugo/` | 8090 |

## Multi-Tenant Design

All data is scoped by `business_id`. JWT tokens carry claim-based authorization (no DB lookups per request).

**Call routing**: Incoming calls use SIP headers to identify the restaurant:
- **Production**: `sip.h.diversion` (forwarded calls from restaurant's real number)
- **Development**: `sip.h.to` (direct calls to Telnyx number)

## Client Architecture Comparison

| Aspect | Web Dashboard | Desktop App |
|--------|--------------|-------------|
| Framework | Next.js 16 + React 19 | Vite 7 + React 19 + Tauri 2 |
| API Client | Custom fetch-based | Shared OpenAPI Axios client |
| UI Components | shadcn/ui (Radix) | Custom component library |
| Auth | NextAuth v5 (OAuth) | Direct JWT + localStorage |
| Real-time | Not yet connected | Centrifugo WebSocket |
| Printing | N/A | Tauri Rust backend (ESC/POS + IPP) |

See [apps/web/ARCHITECTURE.md](https://github.com/StellarChiron/panbot/blob/main/apps/web/ARCHITECTURE.md) and [apps/desktop/ARCHITECTURE.md](https://github.com/StellarChiron/panbot/blob/main/apps/desktop/ARCHITECTURE.md) for detailed frontend architecture.
