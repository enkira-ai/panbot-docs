<div align="center">
  <img src="panbot.jpg" alt="PanBot Logo" width="200"/>
  
  # PanBot

  A production-ready restaurant phone assistant built with [LiveKit Agents](https://docs.livekit.io/agents/) and optimized for real-world deployment. This multi-tenant system handles restaurant phone calls for taking orders, making reservations, and providing customer service via traditional phone systems using Telnyx as the SIP provider.
</div>

This system now features:
- **Database-driven multi-tenant support** - Handle multiple restaurants from one deployment
- **Optimized RAG performance** - Pre-built, cached indices for 95% faster response times
- **Redis caching** - Restaurant data cached for lightning-fast lookups
- **Automatic restaurant detection** - Routes calls based on phone number
- **Production deployment ready** - PostgreSQL + Redis + K8S support

## Prerequisites

### Required
- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL 15+ (for restaurant data)
- Redis 7+ (for caching)
- [LiveKit CLI](https://docs.livekit.io/home/client-sdks/cli.md) (`brew install livekit` on macOS)
- OpenAI API key (get one at [OpenAI Platform](https://platform.openai.com/api-keys))
- LiveKit project (free account at [LiveKit Cloud](https://cloud.livekit.io))
- Telnyx account for telephony (sign up at [Telnyx](https://telnyx.com))
- Phone number purchased through Telnyx
- Telnyx API v2 key (create at [Telnyx Portal](https://portal.telnyx.com/#/app/api-keys))
- Groq API key (for LLM)
- DeepGram API key (for STT)
- Cartesia API key (for TTS)

Run:
```bash
# Setup local .venv with uv:
uv sync --extra scraper
# Download turn-detection model for livekit:
uv run python scripts/download_models.py download-files
# Download playwright chromium browser for scraper (only needed if running scraper directly):
uv run python -m playwright install --with-deps chromium
```

**Note:** If you use `make run-scraper-script` (Docker-based), Playwright is pre-installed in the container and you don't need to install it locally.

### For Desktop App Development
- Node.js 22+ LTS and npm (see [official installation guide](https://nodejs.org/en/download/))
- Rust (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- System dependencies: `sudo apt-get install -y libwebkit2gtk-4.0-dev libwebkit2gtk-4.1-dev libsoup-3.0-dev libjavascriptcoregtk-4.1-dev build-essential curl wget file libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev`

### Optional (for enhanced performance)
- LlamaIndex (for vector search - auto-installs if available)

## Quick Setup

### 1. **Environment Setup**
```bash
cd panbot
uv sync

# Backend environment (for development)
cp env.example dev.env

# Desktop app environment (for frontend)
cd apps/desktop
cp env.example dev.env
cd ../..
```

Edit `dev.env` and `apps/desktop/dev.env` with your credentials

### 2. **Database Setup**
```bash
# Start PostgreSQL and Redis (we currently use Upstash)

# Run database migrations
./migrate upgrade head
```

### 3. **Restaurant Onboarding**
```bash
  # Scrape and onboard your target restaurant
  uv run python src/scripts/scrape_and_onboard.py -q "your restaurant"
```

### 4. **Local Development**
```bash
# Start all services locally (API, Agent, Scraper, Centrifugo) with auto-reload
make dev

# This automatically:
# - Uses dev.env for backend configuration
# - Generates Centrifugo namespace constants from config.json
# - Creates .env symlink for Docker Compose compatibility
# - Starts local infrastructure (Centrifugo via Docker)
# - Starts API with hot reload on :8000
# - Starts Telephony Agent in console mode
# - Starts Scraper worker for background jobs
# - Follows colored logs from all services
```

The `make dev` command includes automatic generation of type-safe Centrifugo namespace constants to prevent "unknown channel" errors.
The `make dev` command includes automatic generation of type-safe Centrifugo namespace constants to prevent "unknown channel" errors.

### 5. **Desktop App Development** 
```bash
# Start desktop app in development mode
make desktop-dev

# This automatically:
# - Uses apps/desktop/dev.env for frontend configuration
# - Syncs TypeScript API client from backend
# - Starts Vite dev server on localhost:1420
# - Opens Tauri desktop window with hot reload
```

### 6. **Additional Development Commands**
```bash
# Stop all local services
make stop-dev

# Clean development artifacts and orphaned processes  
make clean-dev

# Show status of all local services
make dev-status

# Run scraper script in Docker (with Playwright pre-installed)
make run-scraper-script query="Restaurant Name" tenant=dev

# Build desktop app for production
make desktop-build              # Uses apps/desktop/prod.env

# Build desktop app for development testing
make desktop-build-dev          # Uses apps/desktop/dev.env
```

### 7. **Pre-build RAG Indices (deprecated for the time being, we will revisit RAG in later development stage)**
```bash
# Build indices for all restaurants (improves call setup speed by 95%)
# uv run python scripts/prebuild_rag_indices.py --all
```

## Environment File Structure

```
panbot/
├── dev.env                    # Backend development (localhost services)
├── prod.env                   # Backend production (EXTERNAL_DOMAIN=api.novaserve.ai)
├── staging.env                # Backend staging (optional)
└── apps/desktop/
    ├── .env                  # Frontend config (VITE_BACKEND_API_URL)
    └── env.example           # Template
```

**Backend Environment Files**: 
- Database, Redis, API keys, and domain configuration
- `EXTERNAL_DOMAIN` - API domain (e.g., `api.novaserve.ai`)
- `CENTRIFUGO_EXTERNAL_DOMAIN` - Realtime WebSocket domain (e.g., `realtime.novaserve.ai`)
- For Kubernetes with path-based routing, only `EXTERNAL_DOMAIN` is needed
- For Azure Container Apps (per-service URLs), both domains are required

**Frontend Environment Files**: 
- Only needs `VITE_BACKEND_API_URL` (Centrifugo URL returned by backend during login)

## Setup Telephony Integration

### Dashboard Setup (Recommended)

Manual configuration via the Telnyx and LiveKit dashboards is easier than debugging CLI issues, especially when managing multiple phone numbers with different configurations.

#### Step 1: Configure Environment Variables

In your `prod.env` (or `dev.env`), ensure these LiveKit credentials match your LiveKit project:

```bash
# Must match the LiveKit project you're configuring
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

#### Step 2: Configure Telnyx

Follow [LiveKit SIP Setup](https://docs.livekit.io/telephony/start/sip-trunk-setup/#livekit-setup)

**Critical:** The agent name in your dispatch rule must exactly match the agent name in the code:

```python
# src/agents/telephony/entrypoint.py
agent_name="restaurant-telephony-agent"
```

This is currently hardcoded. In the future we can make it into an env var.

#### Environment Separation (Current Setup)

We currently separate production and development using:
- **Different Telnyx accounts** with different phone numbers
- **Different LiveKit projects** with separate credentials

This provides complete isolation between environments.

#### Future: Multi-Agent Routing

When serving different industries with different agents, you can:
1. Use a single Telnyx account with multiple gateway numbers
2. Configure dispatch rules in LiveKit to route based on the dialed number
3. Our internal agent router can further route based on the forwarding caller ID

This allows consolidating into one account while using dispatch rules to route calls to different agent workers.

### SIP Headers

See [inbound trunk headers](./telnyx-config/inbound-trunk-with-headers.json) for additional headers you can add to your Livekit inbound trunk config. This helps our [SIP parsing](./src/agents/telephony/base.py).


### 📞 **How Call Routing Works**

The system uses SIP headers to detect which restaurant to serve:

```
Development Call:
Customer dials: +1-555-DEV-NUM (your Telnyx number)
├── SIP header: sip.h.to = "+1-555-DEV-NUM"
├── Database lookup: businesses.phone_number OR business_phone_numbers.phone_e164 = "+1-555-DEV-NUM"  
└── Loads: "Test Restaurant Dev" data

Production Call (Forwarding):
Customer dials: +1-800-RESTAURANT (restaurant's real number)
├── Call forwards to: +1-555-DEV-NUM (your Telnyx number)
├── SIP header: sip.h.diversion = "+1-800-RESTAURANT"
├── Database lookup: businesses.phone_number OR business_phone_numbers.phone_e164 = "+1-800-RESTAURANT"
└── Loads: "Real Restaurant" data

Multi-Line Restaurant:
Customer dials: +1-800-TAKEOUT (restaurant's takeout line)
├── Call forwards to: +1-555-DEV-NUM (your Telnyx number)
├── SIP header: sip.h.diversion = "+1-800-TAKEOUT"
├── Database lookup: business_phone_numbers.phone_e164 = "+1-800-TAKEOUT" (label: "Takeout")
└── Loads: Same restaurant data with context about takeout line
```

#### Example Multi-Restaurant Flow

**Customer calls restaurant A**: `+1-123-456-7890`
- System loads restaurant A's menu and info
- **Agent**: "Hello, thank you for calling restaurant A! How can I help you today?"
- **Customer**: "What spicy dishes do you have?"
- **Agent**: "We have several spicy options! Our General Tso's Chicken has a spice level of 3 out of 5..."

**Different customer calls another restaurant**: `+1-555-123-4567`
- System automatically loads different restaurant's data
- Completely different menu and restaurant context
- No interference between calls

### 🏢 **Multi-Restaurant Testing**

We need multiple Telnyx number to test multiple restaurants in parallel. Or assign the number to one restaurant at a time to test them in series.

### Test Outbound Calls

```bash
# Replace +1234567890 with the target phone number
lk dispatch create \
  --new-room \
  --agent-name restaurant-telephony-agent \
  --metadata '{"phone_number": "+1234567890"}'
```

### Console Mode (Voice Testing)

For testing the agent without telephony:

```bash
# First, set the default restaurant for console testing
echo "DEFAULT_TELNYX_PHONE=+1234567890" >> dev.env

# Then run console mode
uv run python -m src.agents.telephony.entrypoint console
```

## Adding New Restaurants

### Method 1: Using Onboarding Script (Recommended)

**Using Docker (includes Playwright):**
```bash
make run-scraper-script query="Your Restaurant Name NYC" tenant=dev

# Basic usage with a single query
make run-scraper-script query="Your Restaurant Name NYC" tenant=dev

# With JSON output for debugging
make run-scraper-script query="Your Restaurant Name NYC" json_output=debug.json tenant=dev

# With image downloading enabled
make run-scraper-script query="Your Restaurant Name NYC" download_images=true tenant=dev

# Using an input file with multiple queries
make run-scraper-script input=queries.txt tenant=dev

# All options together
make run-scraper-script query="Restaurant Name" json_output=output.json download_images=true tenant=dev
```

**Direct Python execution:**
```bash
uv run python src/scripts/scrape_and_onboard.py -q "Your Restaurant Name NYC"
```

The script will:
- Scrape Google Maps data for the restaurant
- Generate STT optimization keywords (LLM-enhanced if available)
- Onboard the restaurant directly to your database
- Save debug JSON output if requested

### Method 2: Direct Database Insert

```python
from src.models import BusinessDB
# Create restaurant and menu items programmatically
```

### Method 3: Admin API (Future)
```bash
# Coming in Sprint 3
curl -X POST /api/v1/restaurants -d @restaurant.json
```

### Method 4: Desktop/Web UI (React + Tauri)

Coming in Sprint 5

## Production Deployment

### Custom Domain Setup (Recommended)

Using your own domains means you configure once and never change environment variables when switching cloud providers. Just update DNS CNAMEs.

#### Domain Architecture

| Domain | Purpose | Cloud Routing |
|--------|---------|---------------|
| `api.novaserve.ai` | REST API | Points to API container |
| `realtime.novaserve.ai` | WebSocket (Centrifugo) | Points to Centrifugo container |

**Why two domains?** Azure Container Apps gives each service a separate URL. Kubernetes can use path-based routing with one domain, but using two domains works everywhere and simplifies migration.

#### 1. Configure DNS (One-Time)

At your domain registrar (e.g., Namecheap), add:

| Type | Host | Value |
|------|------|-------|
| CNAME | `api` | Your API endpoint (e.g., `panbot-api.eastus.azurecontainerapps.io`) |
| TXT | `asuid.api` | Verification ID from Azure (for managed SSL certs) |
| CNAME | `realtime` | Your Centrifugo endpoint (e.g., `panbot-centrifugo.eastus.azurecontainerapps.io`) |
| TXT | `asuid.realtime` | Verification ID from Azure (for managed SSL certs) |

#### 2. Set Environment Variables (One-Time)

```bash
# Backend (prod.env) - set once, never change
EXTERNAL_DOMAIN=api.novaserve.ai
CENTRIFUGO_EXTERNAL_DOMAIN=realtime.novaserve.ai

# Desktop app (apps/desktop/.env) - set once, never change
VITE_BACKEND_API_URL=https://api.novaserve.ai
```

#### 3. Switching Cloud Providers

With custom domains, migration is simple:
1. Deploy to new cloud provider
2. Update DNS CNAMEs to point to new endpoints
3. Wait 5-15 min for DNS propagation
4. Done! No code or config changes needed

See [Kubernetes Deployment Guide](infrastructure/k8s/DEPLOYMENT_GUIDE.md) for detailed setup.

### Desktop/Web App Configuration

The React + Tauri app uses Vite environment variables:

```bash
cd apps/desktop
cp env.example .env
# Edit .env with your production URL (https://api.novaserve.ai)
```

**Build for Deployment**:
```bash
# From project root:
make desktop-build          # Production build
make desktop-build-dev      # Development build

# Or manually:
cd apps/desktop
npm run tauri build  # Desktop app
npm run build        # Web static files
```

### Important Notes

- **Single Frontend**: The React + Tauri app serves both desktop and web use cases
- **Build Time vs Runtime**: Frontend URLs are embedded at build time, not runtime
- **Centrifugo WebSocket**: URL is auto-constructed from `CENTRIFUGO_EXTERNAL_DOMAIN` (or `EXTERNAL_DOMAIN` for path-based routing) and returned during login
- **Two Domains for Azure**: Azure Container Apps needs separate domains (`api.*` and `realtime.*`) since it doesn't support path-based routing between apps
- **Desktop App CORS**: Desktop apps bypass CORS automatically - see `docs/CENTRIFUGO_CORS_AND_DESKTOP_APPS.md`

## Using LiveKit Cloud

Deploy directly to LiveKit Cloud for managed hosting. See the [deployment guide](https://docs.livekit.io/agents/deployment/) for details.

## Database Migrations

```bash
# Apply all pending migrations (uses dev.env by default)
./migrate upgrade head

# Check current migration status
./migrate current

# View migration history
./migrate history

# Create new migration (after model changes)
./migrate revision --autogenerate -m "description"

# For other environments, temporarily copy the env file:
# cp prod.env dev.env && ./migrate upgrade head
```

### Legacy Issues

1. **"Failed to load model files"**
   - Run: `uv run python scripts/download_models.py download-files`

2. **"Authentication failed"**
   - Verify your API key and LiveKit credentials in `dev.env`

3. **"Telnyx setup failed"**
   - Ensure your Telnyx API key is valid and has proper permissions
   - Verify your phone number is purchased and active in Telnyx
   - Check that all required environment variables are set in `dev.env`

4. **"LiveKit CLI not found"**
   - Install LiveKit CLI: `brew install livekit` (macOS) or follow [installation guide](https://docs.livekit.io/home/client-sdks/cli.md)

5. **"SIP trunk creation failed"**
   - Ensure LiveKit CLI is authenticated: `lk auth`
   - Verify the generated JSON configuration files in `telnyx-config/`
   - Check the setup report in `reports/` for detailed error information

### Deploy to Kubernetes
```bash
# Deploy API (includes scraper for onboarding)
kubectl apply -f infrastructure/k8s/api.yaml

cd infrastructure/k8s

# Local development (ARM64)
make build && make deploy

# Production deployment (requires ARM64 nodes)
make deploy tenant=prod
```

### Cloud Deployment Options

The system is **cloud-agnostic** - use `EXTERNAL_DOMAIN` with your custom domain and switch providers by updating DNS only.

#### Unified Deployment Workflow

All platforms follow the **same 3-step workflow**:

```bash
# Step 1: Build and push images to GHCR
make push tenant=prod

# Step 2: Sync environment to cloud secret store
make [platform]-sync-env tenant=prod

# Step 3: Deploy
make [platform]-deploy tenant=prod
```

Where `[platform]` is one of: `azure`, `gcp`, or `aws`.

#### Platform Comparison

| Platform | Secret Store | Sync Command | Deploy Command |
|----------|--------------|--------------|----------------|
| Azure Container Apps | Key Vault | `make azure-sync-env tenant=prod` | `make azure-deploy tenant=prod` |
| GCP Cloud Run | Secret Manager | `make gcp-sync-env tenant=prod` | `make gcp-deploy tenant=prod` |
| AWS Fargate | Secrets Manager | `make aws-sync-env tenant=prod` | `make aws-deploy tenant=prod` |

#### How Environment Sync Works

1. Edit `prod.env` as usual (database credentials, API keys, etc.)
2. Run the sync command - it automatically detects sensitive values and pushes them to the cloud secret store
3. Deploy containers - they reference secrets from the store, not hardcoded values

**Auto-detected sensitive patterns:** `PASSWORD`, `SECRET`, `KEY`, `TOKEN`, `API_KEY`, `CREDENTIAL`

```bash
# Preview what will be synced (dry run - no changes made)
make azure-sync-env-dry-run tenant=prod
make gcp-sync-env-dry-run tenant=prod
make aws-sync-env-dry-run tenant=prod
```

Generated files are stored in `infrastructure/{azure,gcp,aws}/` for reference.

#### Azure Container Apps

##### First-Time Azure Setup (One-Time)

Before your first deployment, complete these one-time setup steps:

```bash
# 1. Login to Azure
az login --use-device-code

# 2. Set your subscription
az account set --subscription <AZURE_SUBSCRIPTION_ID>

# 3. Create resource group (if it doesn't exist)
az group create --name <AZURE_RESOURCE_GROUP> --location eastus

# 4. Register required resource providers (can take 1-2 minutes each)
az provider register -n Microsoft.App --wait
az provider register -n Microsoft.OperationalInsights --wait
az provider register -n Microsoft.KeyVault --wait
az provider register -n Microsoft.ContainerRegistry --wait
az provider register -n Microsoft.ManagedIdentity --wait

# 5. (Optional) Create service principal for automated login
az ad sp create-for-rbac --name "panbot-deploy" --role Contributor \
  --scopes /subscriptions/<AZURE_SUBSCRIPTION_ID>
# Add output to prod.env: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
```

You can verify provider registration status:
```bash
az provider show -n Microsoft.App --query "registrationState" -o tsv
```

##### Deployment Workflow

```bash
# First-time deployment (builds, pushes, creates apps, syncs env)
make azure-deploy tenant=prod

# Day-to-day updates (builds, pushes, updates apps, syncs env)
make azure-update tenant=prod

# Sync env vars only (no rebuild - fast updating apps with new env)
make azure-sync-env tenant=prod

# Monitoring
make azure-status tenant=prod            # Service status
make azure-logs-api tenant=prod          # View logs
make azure-test-api tenant=prod          # Health check

# Cost management
make azure-stop-all tenant=prod          # Scale to 0 (no charges)
make azure-start-all tenant=prod         # Restore replicas
```

All commands use `prod.env` as single source of truth. See `azure.makefile` for more commands.

##### Custom Domain & SSL Setup (One-Time, After First Deploy)

After your first deployment, set up custom domains with managed SSL for both the API and Centrifugo (realtime WebSocket).

**1. Get the verification ID and container FQDNs:**
```bash
# Get verification ID (same for all apps in the environment)
az containerapp env show \
  --name panbot-prod-envvars \
  --resource-group novaserve-ai \
  --query "properties.customDomainConfiguration.customDomainVerificationId" \
  -o tsv

# Get API container FQDN
az containerapp show --name panbot-api --resource-group novaserve-ai \
  --query "properties.configuration.ingress.fqdn" -o tsv

# Get Centrifugo container FQDN  
az containerapp show --name panbot-centrifugo --resource-group novaserve-ai \
  --query "properties.configuration.ingress.fqdn" -o tsv
```

**2. Add DNS records at your registrar (e.g., Namecheap):**

| Type | Host | Value |
|------|------|-------|
| TXT | `asuid.api` | `<verification-id>` |
| CNAME | `api` | `<panbot-api-fqdn>` |
| TXT | `asuid.realtime` | `<verification-id>` |
| CNAME | `realtime` | `<panbot-centrifugo-fqdn>` |

**3. Wait for DNS propagation (~5-15 minutes), then add custom domains:**

```bash
# === API Domain (api.novaserve.ai) ===
az containerapp hostname add \
  --name panbot-api \
  --resource-group novaserve-ai \
  --hostname api.novaserve.ai

az containerapp hostname bind \
  --name panbot-api \
  --resource-group novaserve-ai \
  --hostname api.novaserve.ai \
  --environment panbot-prod-envvars \
  --validation-method CNAME

# === Realtime Domain (realtime.novaserve.ai) ===
az containerapp hostname add \
  --name panbot-centrifugo \
  --resource-group novaserve-ai \
  --hostname realtime.novaserve.ai

az containerapp hostname bind \
  --name panbot-centrifugo \
  --resource-group novaserve-ai \
  --hostname realtime.novaserve.ai \
  --environment panbot-prod-envvars \
  --validation-method CNAME
```

**4. Verify both domains are working:**
```bash
# Test API
curl https://api.novaserve.ai/api/v1/health/

# Test Centrifugo (should return JSON error - that's expected without auth)
curl https://realtime.novaserve.ai/connection/websocket
```

##### Renewing Expired Service Principal Secrets

Service principal secrets expire after 1 year by default. If Azure login fails with `AADSTS7000215` or "invalid client secret":

```bash
# 1. Login interactively first
az login --use-device-code

# 2. Regenerate the secret (extends for 1 year)
az ad sp credential reset --id <AZURE_CLIENT_ID> --years 1

# 3. Update AZURE_CLIENT_SECRET in prod.env with the new password from output
```

To check when your current secret expires:
```bash
az ad app credential list --id <AZURE_CLIENT_ID> --query "[].endDateTime" -o tsv
```

#### Google Cloud Platform (Cloud Run)
```bash
# Full deployment workflow
make push tenant=prod                    # Build & push images
make gcp-sync-env tenant=prod            # Sync secrets to Secret Manager
make gcp-setup-infrastructure tenant=prod # Create Cloud SQL, Redis, etc.
make gcp-deploy tenant=prod              # Deploy all services

# Day-to-day updates
make push tenant=prod && make gcp-update tenant=prod

# Monitoring
make gcp-status tenant=prod              # Service status
make gcp-logs-api tenant=prod            # View logs
make gcp-test-api tenant=prod            # Health check
```

See `googlecloud.makefile` for all GCP commands.

#### AWS Fargate (ECS)
```bash
# Full deployment workflow
make push tenant=prod                    # Build & push images
make aws-sync-env tenant=prod            # Sync secrets to Secrets Manager
make aws-deploy tenant=prod              # Deploy all services

# Day-to-day updates
make push tenant=prod && make aws-update tenant=prod

# Monitoring
make aws-status tenant=prod              # Service status
make aws-logs-api tenant=prod            # View logs
make aws-test-api tenant=prod            # Health check
```

See `aws.makefile` for all AWS commands.

#### Kubernetes (Any Provider)
```bash
cd infrastructure/k8s

# Build and deploy
make build && make deploy tenant=prod
```

Works on: **Azure AKS**, **AWS EKS**, **Google GKE**, **Rancher Desktop**, etc.

#### Supported Platforms

| Platform | Compute | Makefile | Notes |
|----------|---------|----------|-------|
| Azure Container Apps | Serverless | `azure.makefile` | Current production |
| AWS Fargate | Serverless | `aws.makefile` | ECS-based containers |
| GCP Cloud Run | Serverless | `googlecloud.makefile` | Easy scaling |
| Azure AKS | Kubernetes | `infrastructure/k8s/` | ARM64 node pools |
| AWS EKS | Kubernetes | `infrastructure/k8s/` | Graviton ARM64 instances |
| GCP GKE | Kubernetes | `infrastructure/k8s/` | Tau T2A ARM64 instances |

#### Environment Configuration
- `dev.env` - Development (localhost services)
- `prod.env` - Production (with `EXTERNAL_DOMAIN=api.novaserve.ai`)
- `staging.env` - Staging (optional)

#### Quick Reference: All Platform Commands

| Action | Azure | GCP | AWS |
|--------|-------|-----|-----|
| Sync env | `azure-sync-env` | `gcp-sync-env` | `aws-sync-env` |
| Deploy all | `azure-deploy` | `gcp-deploy` | `aws-deploy` |
| Update all | `azure-update` | `gcp-update` | `aws-update` |
| Status | `azure-status` | `gcp-status` | `aws-status` |
| API logs | `azure-logs-api` | `gcp-logs-api` | `aws-logs-api` |
| Test API | `azure-test-api` | `gcp-test-api` | `aws-test-api` |
| Delete all | `azure-delete-all` | `gcp-teardown` | `aws-delete-all` |
| Help | `azure-help` | - | `aws-help` |

## Documentation

### Current Planning & Architecture
- **`sprints/`** - Active sprint planning and execution logs
- **`architecture_design_doc.md`** - System architecture and design decisions  
- **`frontend_implementation_plan.md`** - React + Tauri frontend planning
- **`feature-wishlist.md`** - Customer feedback and feature requests
- **`FUTURE_BACKLOG.md`** - Future work items and enhancements

### Development
- **`.cursor/rules/dev-guide.mdc`** - Essential development patterns for AI agents
- **`docs/`** - Technical documentation and guides

## License

This project is licensed under the MIT License. See the original LiveKit Agents framework license for framework-specific terms.