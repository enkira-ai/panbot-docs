---
title: CI/CD & Secrets Management
description: GitHub Actions pipelines, Docker builds, Infisical secrets, and cloud deployment workflows.
---

## Overview

PanBot uses GitHub Actions for CI/CD, GHCR for Docker images, and Infisical Cloud for secrets management. Applications never fetch secrets at runtime — secrets are pulled once during build/deploy and injected as environment variables.

```
Developer:  Infisical Cloud → make sync-env → .env → config.py → app
CI/CD:      Infisical Cloud → infisical_export.py → cloud secret manager → container env → app
```

## Secrets Management (Infisical)

Secrets are stored in [Infisical Cloud](https://app.infisical.com) organized into 7 functional folders (`/database/`, `/auth/`, `/telephony/`, `/ai/`, `/messaging/`, `/cloud/`, `/app/`) with 6 deployment tags (`api`, `agent`, `worker`, `desktop`, `web`, `ci-cd`).

### Pulling Secrets

```bash
# Create infisical.env with your credentials first (get from team lead)
make sync-env                    # Backend (dev) → .env
make sync-env tenant=prod        # Backend (prod) → .env
make sync-env-desktop            # Desktop → apps/desktop/.env
make sync-env-web                # Web → apps/web/.env.local
```

### How config.py Loads Environment

`src/common/config.py` auto-loads env files at import time in this order:

1. Skip if `APP_NAME` + `ENVIRONMENT` are already set (container / Makefile)
2. `{TENANT}.env` if `TENANT` env var is set
3. `.env` — canonical output of `make sync-env`
4. `dev.env` — legacy fallback
5. `prod.env` — legacy fallback

All `src/` modules use this centralized loading — no scattered `load_dotenv()` calls.

## GitHub Actions

### CI Pipeline (`ci.yml`)

Runs on PRs, pushes to main, and daily at 3am UTC.

- **Unit tests**: Python 3.13, `pytest tests/unit`
- **Integration tests**: PostgreSQL 15 + Redis 7 service containers, `pytest tests/integration`

Integration tests are gated by `vars.RUN_INTEGRATION_TESTS` on PRs.

### Docker Image CI (`docker-image.yml`)

Builds and pushes 4 multi-platform images (`linux/amd64` + `linux/arm64`) to `ghcr.io`:

| Image | Dockerfile | Purpose |
|-------|-----------|---------|
| `panbot-api` | `Dockerfile.api` | FastAPI backend (port 8000) |
| `panbot-agent` | `Dockerfile.agent` | LiveKit telephony agent (port 8080) |
| `panbot-scraper` | `Dockerfile.scraper` | Scraper with Playwright (port 8080) |
| `panbot-centrifugo` | `Dockerfile.centrifugo` | Centrifugo real-time (port 8000) |

Tags include branch, PR number, short SHA, and `latest` (main only). Push only on non-PR events.

### OpenAPI Client Verification (`verify-openapi-client.yml`)

Ensures the TypeScript API client (`apps/shared/api-client/`) stays in sync with the backend OpenAPI spec. Fails if regenerated client differs from what's committed.

### Notification Workflows

Discord notifications for CI failure/success, PR merges, and issue assignments.

## Cloud Deployment

### 3-Step Workflow (All Platforms)

```bash
# 1. Build and push images
make push tenant=prod

# 2. Sync secrets to cloud
make [platform]-sync-env tenant=prod

# 3. Deploy
make [platform]-deploy tenant=prod
```

### Platform Commands

| Action | Azure | GCP | AWS |
|--------|-------|-----|-----|
| Sync env | `azure-sync-env` | `gcp-sync-env` | `aws-sync-env` |
| Deploy | `azure-deploy` | `gcp-deploy` | `aws-deploy` |
| Update | `azure-update` | `gcp-update` | `aws-update` |
| Status | `azure-status` | `gcp-status` | `aws-status` |
| Logs | `azure-logs-api` | `gcp-logs-api` | `aws-logs-api` |
| Health | `azure-test-api` | `gcp-test-api` | `aws-test-api` |
| Dry run | `azure-sync-env-dry-run` | `gcp-sync-env-dry-run` | `aws-sync-env-dry-run` |

All accept `tenant=prod` (default: `dev`).

### Secrets Flow

```
1. Edit secrets in Infisical Cloud console
2. make sync-env tenant=prod              → local .env
3. make [platform]-sync-env tenant=prod   → cloud secret store
4. make [platform]-deploy tenant=prod     → containers reference cloud secrets
```

## Custom Domains

Using custom domains decouples from cloud providers. To switch providers, update DNS CNAMEs only.

| Domain | Purpose |
|--------|---------|
| `api.novaserve.ai` | REST API |
| `realtime.novaserve.ai` | Centrifugo WebSocket |

Set in Infisical:
- `EXTERNAL_DOMAIN=api.novaserve.ai`
- `CENTRIFUGO_EXTERNAL_DOMAIN=realtime.novaserve.ai`

## Further Reading

- `README_ci_cd.md` — Full CI/CD reference (available in the feature branch; if missing on main, use dev_docs below)
- [`dev_docs/infisical_migration_guide.md`](https://github.com/StellarChiron/panbot/blob/main/dev_docs/infisical_migration_guide.md) — Infisical setup, troubleshooting, migration history
- [`dev_docs/cloud_deployment_architecture.md`](https://github.com/StellarChiron/panbot/blob/main/dev_docs/cloud_deployment_architecture.md) — Resource sizing and scaling
