---
title: Deployment Guide
description: How to deploy PanBot to cloud platforms.
---

## Cloud-Agnostic Design

PanBot uses custom domains (`EXTERNAL_DOMAIN`) so you can switch cloud providers by updating DNS only.

| Domain | Purpose |
|--------|---------|
| `api.novaserve.ai` | REST API |
| `realtime.novaserve.ai` | Centrifugo WebSocket |

## Supported Platforms

| Platform | Type | Makefile | Status |
|----------|------|----------|--------|
| Azure Container Apps | Serverless | `azure.makefile` | Current production |
| GCP Cloud Run | Serverless | `googlecloud.makefile` | Available |
| AWS Fargate | Serverless | `aws.makefile` | Available |
| Kubernetes (any) | Container orchestration | `infrastructure/k8s/` | Available |

## Unified Workflow

All platforms follow the same 3-step workflow:

```bash
# 1. Build and push images to GHCR
make push tenant=prod

# 2. Sync environment to cloud secret store
make [platform]-sync-env tenant=prod

# 3. Deploy
make [platform]-deploy tenant=prod
```

## Platform Commands

| Action | Azure | GCP | AWS |
|--------|-------|-----|-----|
| Deploy all | `azure-deploy` | `gcp-deploy` | `aws-deploy` |
| Update all | `azure-update` | `gcp-update` | `aws-update` |
| Sync env | `azure-sync-env` | `gcp-sync-env` | `aws-sync-env` |
| Status | `azure-status` | `gcp-status` | `aws-status` |
| API logs | `azure-logs-api` | `gcp-logs-api` | `aws-logs-api` |
| Stop (save cost) | `azure-stop-all` | — | — |

All commands accept `tenant=prod|staging|dev`.

## Environment Files

```
panbot/
├── dev.env          # Backend development
├── prod.env         # Backend production
├── staging.env      # Backend staging (optional)
└── apps/desktop/
    ├── dev.env      # Frontend development
    └── prod.env     # Frontend production
```

**Auto-detected secrets**: Values matching `PASSWORD`, `SECRET`, `KEY`, `TOKEN`, `API_KEY`, `CREDENTIAL` are automatically pushed to cloud secret stores.

## Desktop App Build

```bash
make desktop-build          # Production build (uses apps/desktop/prod.env)
make desktop-build-dev      # Development build (uses apps/desktop/dev.env)
```

Frontend URLs are embedded at build time, not runtime.

## Detailed Setup

See `docs/src/content/docs/index.md` (README) for:
- First-time Azure setup
- Custom domain and SSL configuration
- Service principal management
- Telephony integration (Telnyx + LiveKit)
