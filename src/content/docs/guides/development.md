---
title: Development Guide
---
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PanBot is an AI-powered restaurant phone assistant built on LiveKit Agents. It handles incoming SIP calls (via Telnyx), takes orders, manages reservations, and provides customer service for multiple restaurants (multi-tenant). The system includes a FastAPI backend, a React+Tauri desktop app, and a Next.js dashboard (separate repo at `../panbot-dashboard`).

## Common Commands

### Local Development
```bash
make dev                    # Start all services (API, Agent, Centrifugo) with hot reload
make stop-dev               # Stop all local services
make dev-status             # Check which services are running
make clean-dev              # Stop services and clean artifacts
```

### Testing
```bash
pytest tests/                       # Run all tests
pytest tests/ -m unit               # Unit tests only
pytest tests/ -m "not integration"  # Skip integration tests
pytest tests/ -m "not slow"         # Skip slow tests
pytest tests/test_menu_format.py    # Run a single test file
```

### Database Migrations
```bash
make migrate-upgrade                              # Apply pending migrations (dev)
make migrate-upgrade tenant=prod                  # Apply to production
make migrate-auto message="Add user table"        # Generate migration from model changes
make migrate-downgrade                            # Rollback one migration
make migrate-current                              # Show current revision
```

### Package Management
```bash
uv sync --extra scraper     # Install all dependencies including scraper extras
uv sync                     # Install without scraper extras
```

### Desktop App
```bash
make desktop-dev            # Start React+Tauri desktop app in dev mode (port 1420)
make desktop-build          # Production build (uses apps/desktop/prod.env)
make desktop-deps           # Install npm dependencies
```

### Chat Testing (text-only agent testing)
```bash
make chat-server                        # Start agent in text-only mode
make chat-client phone=+1555123456      # Connect chat client to specific restaurant
make chat-test                          # Start both server and client
```

### Deployment
```bash
make gcp-deploy tenant=prod     # Google Cloud Run
make azure-deploy tenant=prod   # Azure Container Apps
make aws-deploy tenant=prod     # AWS Fargate
```

## Architecture

### Dependency Flow
`agents / api / workers` -> `services` -> `common`

APIs and agents never access the database directly; they go through the services layer. `common/` never imports from higher layers.

### Key Entry Points
- **API Server**: `src/api/main.py` (FastAPI, port 8000)
- **Telephony Agent**: `src/agents/telephony/entrypoint.py` (LiveKit agent)
- **Scraper Worker**: `src/workers/scraper_worker.py` (background job processor)

### Layer Breakdown

**`src/agents/telephony/`** - LiveKit voice agent that handles SIP calls. `entrypoint.py` bootstraps the agent, `restaurant_agent.py` contains restaurant-specific conversation logic, `post_call_processor.py` runs analytics after calls end. Agent tools are decorated with `@function_tool()`.

**`src/api/v1/`** - REST endpoints organized by domain (businesses, menus, orders, calls, printers, onboarding). Uses FastAPI dependency injection for services.

**`src/services/`** - Business logic layer. Services own DB access, caching, and event publishing. Key services: `call_service.py`, `customer_service.py`, `rag_service.py`, `config_service/`.

**`src/models/`** - `database.py` has SQLModel ORM models (table=True), `api.py` has Pydantic request/response models. Keep these separate.

**`src/common/`** - Shared infrastructure: `config.py` (settings), `database.py` (DB connection), `cache.py` (Redis), `event_bus.py` (Kafka/MQTT events), `centrifugo.py` (WebSocket push).

**`src/workers/`** - Background workers. `scraper_worker.py` handles restaurant data scraping with Playwright.

**`migrations/`** - Alembic database migrations for PostgreSQL.

**`apps/desktop/`** - React 19 + Tauri 2 desktop application for restaurant management.

### Multi-Tenant Design
All data is scoped by `business_id`. JWT tokens carry claim-based authorization (no DB lookups per request). Restaurant detection on incoming calls uses SIP headers: `sip.h.diversion` in production (forwarded calls), `sip.h.to` in development.

### Environment System
Tenant-based env files: `dev.env` (default), `prod.env`, `staging.env`. Pass `tenant=name` to make targets to use `{name}.env`. Desktop app has its own env files in `apps/desktop/`.

### Real-time Communication
Centrifugo handles WebSocket push to connected clients. Namespace constants are auto-generated from `infrastructure/centrifugo/config.json` via `scripts/generate_centrifugo_namespaces.py`.

## Code Patterns

### Service Pattern
Services use FastAPI `Depends()` for DB sessions and Redis. They validate, persist, cache, and publish events.

### Event Publishing
Import events module (not individual publishers) for easier mocking:
```python
import src.common.events as events
await events.event_publisher.publish(event_type="order.created", ...)
```

### Database Models vs API Models
- SQLModel with `table=True` for DB models in `src/models/database.py`
- Pydantic BaseModel for API request/response in `src/models/api.py`

## Infrastructure
- **PostgreSQL 15+**: Primary data store
- **Redis 7+**: Caching and sessions
- **Centrifugo**: Real-time WebSocket messaging (port 8090)
- **Telnyx**: SIP telephony provider
- **LiveKit Cloud**: Voice agent infrastructure
- **Langfuse**: LLM observability (via OpenTelemetry)

## Key Reference Docs
- `architecture_design_doc.md` - Full system architecture and data models
- `sprints/` - Current sprint plans and tasks
- `prompts/` - AI prompt templates and versions
