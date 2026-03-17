# PanBot Documentation Site

Internal documentation site for PanBot, built with [Astro](https://astro.build) + [Starlight](https://starlight.astro.build).

Hosted at **https://docs.panbot.ai** (password-protected).

## Project Structure

```
.
├── src/
│   ├── assets/
│   └── content/
│       └── docs/           # Markdown documentation files
│           ├── architecture/
│           ├── guides/
│           └── reference/
├── astro.config.mjs        # Astro + Starlight config
├── Dockerfile              # Astro dev server (local Docker Compose)
├── Dockerfile.azure        # Production build for Azure Container Apps
├── Dockerfile.auth         # Cookie session auth service
├── Dockerfile.proxy        # nginx reverse proxy (local Docker Compose)
├── docker-compose.yml      # Local dev setup
├── nginx.conf              # nginx config (local, uses auth_request)
├── nginx.azure.conf        # nginx config (Azure, serves static files)
├── auth_service.py         # Python cookie auth service
├── supervisord.conf        # Process manager for Azure container
└── .env                    # Credentials (not committed)
```

## Local Development

```bash
npm install
npm run dev             # Dev server at localhost:4321
npm run build           # Production build to ./dist/
npm run preview         # Preview production build
```

## Production Deployment (Azure Container Apps)

The docs site runs on **Azure Container Apps** as a single serverless container.
It scales to 0 replicas when idle (no traffic = no cost).

### Architecture

```
Browser → Cloudflare (HTTPS, proxied) → Azure Container Apps
            └── panbot-docs container
                  ├── nginx (port 80) — serves static files + auth_request
                  └── auth_service.py (port 4322) — cookie session auth
```

- **Cloudflare** handles DNS and HTTPS proxying (`CNAME docs → ACA FQDN`)
- **Azure Container Apps** provides managed TLS, auto-scaling (min 0, max 2)
- **nginx** validates session cookies via `auth_request`, serves static Astro build
- **auth_service.py** issues 7-day session cookies on correct password

### Azure Resources

| Resource | Value |
|----------|-------|
| Container App | `panbot-docs` |
| Resource Group | `novaserve-ai` |
| Environment | `panbot-prod-envvars` (Central US) |
| Image | `ghcr.io/enkira-ai/panbot-docs:prod` |
| Default URL | `panbot-docs.purplebush-3b410248.centralus.azurecontainerapps.io` |
| Custom Domain | `docs.panbot.ai` |
| SSL | Azure Managed Certificate (auto-renew) |

### DNS (Cloudflare)

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| `CNAME` | `docs` | `panbot-docs.purplebush-3b410248.centralus.azurecontainerapps.io` | Proxied ✅ |
| `TXT` | `asuid.docs` | Azure domain verification token | DNS only |

### Deploying / Updating

```bash
# 1. Build and push new image
cd docs/
docker build -f Dockerfile.azure \
  --build-arg SITE_URL=https://docs.panbot.ai \
  -t ghcr.io/enkira-ai/panbot-docs:prod .
docker push ghcr.io/enkira-ai/panbot-docs:prod

# 2. Update the Container App
source ../.env   # load AZURE_* vars
az login --service-principal \
  -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
az containerapp update \
  --name panbot-docs \
  --resource-group novaserve-ai \
  --image ghcr.io/enkira-ai/panbot-docs:prod
```

### Managing the Service

```bash
# View logs
az containerapp logs show --name panbot-docs --resource-group novaserve-ai --tail 50

# Check status
az containerapp show --name panbot-docs --resource-group novaserve-ai \
  --query "{status:properties.provisioningState,url:properties.configuration.ingress.fqdn}" -o table

# Scale to 0 (stop, no charges)
az containerapp update --name panbot-docs --resource-group novaserve-ai \
  --min-replicas 0 --max-replicas 0

# Restore
az containerapp update --name panbot-docs --resource-group novaserve-ai \
  --min-replicas 0 --max-replicas 2
```

### Changing the Password

The password is stored as env var `DOCS_PASSWORD` in the Container App.
Get/set it via Infisical (add to prod environment) then update the app:

```bash
az containerapp update \
  --name panbot-docs \
  --resource-group novaserve-ai \
  --set-env-vars "DOCS_PASSWORD=<new-password>"
```

---

## Legacy: EC2 Setup (decommissioned 2026-03-16)

Previously hosted on AWS EC2 (`aegis`, `ec2-13-58-176-229.us-east-2.compute.amazonaws.com`)
via Docker Compose with nginx basic auth. Migrated to Azure Container Apps for cost savings
(EC2 always-on vs ACA scale-to-zero).

The old EC2 Docker containers (`docs-docs-1`, `docs-auth-1`, `docs-proxy-1`) can be stopped:
```bash
ssh aegis "cd /home/ubuntu/projects/panbot/docs && docker compose down"
```
