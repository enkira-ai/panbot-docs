---
title: Environment Setup
description: Local development, staging, and production environment configuration.
---

PanBot uses a 3-environment strategy: **local dev** (Docker Compose), **staging** (Azure, shared instance), and **production** (Azure). All secrets are managed via Infisical Cloud.

## Environment Overview

| Environment | PostgreSQL | Redis | Centrifugo | API Domain |
|-------------|-----------|-------|------------|------------|
| **Local Dev** | `localhost:5432` (Docker) | `localhost:6379` (Docker) | `localhost:8090` (Docker) | `localhost:8000` |
| **Staging** | `panbot.postgres.database.azure.com` / `panbot_staging` | Same Redis instance, DB 1 | `staging-realtime.novaserve.ai` | `staging-api.novaserve.ai` |
| **Production** | `panbot.postgres.database.azure.com` / `panbot` | `panbot.redis.cache.windows.net` | `realtime.novaserve.ai` | `api.novaserve.ai` |

Staging and production share the same Azure PostgreSQL server but use separate databases and users for isolation.

## Local Development

### Prerequisites

- Docker and Docker Compose
- Python 3.13+ with [uv](https://docs.astral.sh/uv/)
- Infisical CLI:
  ```bash
  curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo -E bash
  sudo apt-get install -y infisical
  ```

### Quick Start

```bash
# 1. Clone the repo and checkout the dev branch
#    (main is not kept up to date — always use dev)
git clone git@github.com:enkira-ai/panbot.git
cd panbot
git checkout dev
git submodule update --init

# 2. Install Python dependencies
uv sync --extra scraper

# 3. Create infisical.env with your credentials (get from team lead)
cat > infisical.env << 'EOF'
INFISICAL_CLIENT_ID=<your-client-id>
INFISICAL_CLIENT_SECRET=<your-client-secret>
INFISICAL_PROJECT_ID=<your-project-id>
EOF

# 4. Pull dev secrets (also authenticates Docker to ghcr.io/enkira-ai)
make sync-env                    # pulls dev secrets → .env

# 5. Create dev.env symlink (required by docker-compose)
ln -sf .env dev.env

# 6. Start everything (PostgreSQL, Redis, Centrifugo, API, Agent)
make dev
```

`make dev` starts Docker infrastructure (PostgreSQL, Redis, Centrifugo) and application services (API on `:8000`, telephony agent) with colored log output.

:::note
**Always work on the `dev` branch.** The `main` branch is not actively maintained and will be missing recent Makefile targets, migrations, and code changes.
:::

### Local Infrastructure Services

The `docker-compose.yml` provides:

| Service | Container | Port | Credentials |
|---------|-----------|------|-------------|
| PostgreSQL 15 | `panbot-db` | `5432` | `postgres` / `password` / `panbot` |
| Redis 7 | `panbot-redis` | `6379` | No auth |
| Centrifugo | `panbot-centrifugo` | `8090` | From `.env` |

### Seeding Local Database

To populate your local database with production data:

```bash
# Download and restore latest backup
make db-seed                     # Uses latest backup from Azure Blob Storage
make db-seed backup=file.sql     # Restore a specific backup file

# Then apply any pending migrations
make migrate-upgrade
```

### Useful Local Dev Commands

```bash
make dev-status                  # Check which services are running
make stop-dev                    # Stop all services
make clean-dev                   # Stop + clean logs and PID files
make dev-infra                   # Start only Docker infrastructure
```

## Staging Environment

Staging runs on Azure Container Apps alongside production but uses a separate database, Redis database index, and Centrifugo keys.

### Staging Isolation

| Resource | Staging | Production |
|----------|---------|------------|
| PostgreSQL DB | `panbot_staging` | `panbot` |
| PostgreSQL User | `panbot_staging` | `doadmin` |
| Redis DB Index | `1` | `0` |
| Container Apps Env | `panbot-staging-env` | `panbot-prod-env` |
| API DNS | `staging-api.novaserve.ai` | `api.novaserve.ai` |
| Realtime DNS | `staging-realtime.novaserve.ai` | `realtime.novaserve.ai` |

### Refresh Staging from Production

Staging data can be refreshed from production using an intra-instance `pg_dump | psql` (fast, no network transfer):

```bash
make db-refresh-staging          # Clone prod → staging (destructive!)
```

### Deploy to Staging

```bash
make sync-env tenant=staging     # Pull staging secrets
make azure-deploy tenant=staging # Deploy to staging Container Apps
```

### Run Migrations on Staging

```bash
make sync-env tenant=staging
make migrate-upgrade             # Applies to staging DB (from .env)
```

## Production Environment

### Deploy to Production

```bash
make sync-env tenant=prod        # Pull prod secrets
make azure-deploy tenant=prod    # Deploy to production
```

### Database Backups

Production database is backed up daily at 2 AM UTC via GitHub Actions (`.github/workflows/db-backup.yml`). Backups are stored in Azure Blob Storage (`panbotstorage/db-backups`).

```bash
make db-backup                   # Manual backup + upload to Azure Blob
make db-backup-local             # Backup locally only (no upload)
make db-backup-list              # List backups in Azure Blob Storage
```

### Run Migrations on Production

```bash
make sync-env tenant=prod
make migrate-upgrade             # Applies to prod DB (from .env)
```

## Secret Management (Infisical)

All secrets are stored in [Infisical Cloud](https://app.infisical.com) organized into functional folders (`/database/`, `/auth/`, `/telephony/`, `/ai/`, `/messaging/`, `/cloud/`, `/app/`) with deployment tags (`api`, `agent`, `worker`, `desktop`, `web`, `ci-cd`).

### Pulling Secrets

```bash
make sync-env                    # Backend dev → .env
make sync-env tenant=staging     # Backend staging → .env
make sync-env tenant=prod        # Backend prod → .env
make sync-env-desktop            # Desktop app → apps/desktop/.env
make sync-env-web                # Web dashboard → apps/web/.env.local
```

### How It Works

1. `infisical.env` stores your Infisical access credentials (3 values)
2. `make sync-env` calls `scripts/infisical_export.py` to pull secrets matching the requested tags
3. Secrets are written to `.env` which is gitignored
4. All Make targets and `src/common/config.py` read from `.env`
5. If Infisical returns 0 secrets, `dev.env` is used as a fallback

### Environment Separation in Infisical

Each environment (dev, staging, prod) has its own set of secrets in Infisical. The `tenant=` parameter maps directly to the Infisical environment slug. Secrets like database credentials, API keys, and Centrifugo keys differ per environment, providing full isolation.

## Environment File Structure

```
panbot/
├── infisical.env              # Infisical credentials (gitignored)
├── .env                       # Active secrets from sync-env (gitignored)
├── dev.env                    # Fallback dev config
├── docker-compose.yml         # Local infrastructure
└── apps/desktop/
    ├── .env                   # Frontend config (gitignored)
    └── env.example            # Template
```
