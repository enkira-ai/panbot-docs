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
├── docker-compose.yml      # Self-hosted setup (nginx + Astro dev)
├── Dockerfile              # Astro dev server container
├── Dockerfile.proxy        # nginx auth proxy container
├── nginx.conf              # Reverse proxy + basic auth config
├── proxy-entrypoint.sh     # Generates htpasswd from env vars
└── .env                    # Credentials (not committed)
```

## Local Development

```bash
npm install
npm run dev             # Dev server at localhost:4321
npm run build           # Production build to ./dist/
npm run preview         # Preview production build
```

## Self-Hosted Setup (docs.panbot.ai)

The docs site runs on an EC2 instance via Docker Compose with two containers:

| Container | Role | Port |
|-----------|------|------|
| `docs` | Astro dev server with hot reload | 4321 (internal) |
| `proxy` | nginx reverse proxy with basic auth | 80 + 3001 (exposed) |

### Architecture

```
Browser → Cloudflare (HTTPS) → EC2:80 → nginx (basic auth) → Astro dev :4321
```

- **Cloudflare** handles DNS and HTTPS termination (A record, proxied)
- **nginx** enforces basic auth and proxies to the Astro dev server
- **Astro** runs in dev mode with volume-mounted source for hot reload
- **Docker** `restart: unless-stopped` ensures persistence across VM reboots

### DNS (Cloudflare)

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `docs` | EC2 public IP | Proxied (orange cloud) |

### EC2 Security Group

Inbound rule required on the instance security group:

| Type | Port | Source |
|------|------|--------|
| HTTP | 80 | `0.0.0.0/0` |

### Managing the Service

```bash
cd /home/ubuntu/projects/panbot/docs

# Start / rebuild
docker compose up -d --build

# Stop
docker compose down

# View logs
docker compose logs -f
docker compose logs proxy --tail=50

# Restart after config change
docker compose restart docs
```

### Changing the Password

Edit `.env`:

```
DOCS_USER=panbot
DOCS_PASSWORD=your-password
```

Then restart the proxy:

```bash
docker compose up -d --build proxy
```

### Configuration

The `astro.config.mjs` reads env vars for deployment flexibility:

| Env Var | Docker value | Default (GitHub Pages) |
|---------|-------------|----------------------|
| `SITE_URL` | `https://docs.panbot.ai` | `https://stellarchiron.github.io` |
| `BASE_PATH` | `/` | `/panbot-docs/` |

The `vite.server.allowedHosts` setting includes `docs.panbot.ai` to allow proxied requests.

### Files Not Committed

- `.env` — contains `DOCS_USER` and `DOCS_PASSWORD`
