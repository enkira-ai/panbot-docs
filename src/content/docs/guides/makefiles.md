---
title: Makefile Reference
---
# 🎯 Makefile Usage Guide - Serverless Container Engines

Perfect! Your Makefile is ready to streamline your development and deployment workflow with multi-tenant support. Here's how to use it:

## 🌟 **Multi-Tenant Environment System**

The Makefile uses a clean tenant-based environment system with `[tenant].env` files:

```bash
# Default development environment (uses dev.env)
make dev
make deploy

# Production environment (uses prod.env)  
make deploy tenant=prod

# Staging environment (uses staging.env)
make deploy tenant=staging

# Custom environment (uses custom.env)
make deploy tenant=custom
```

## 📁 **Environment File Structure**

```
panbot/
├── dev.env                    # Backend development (localhost services)
├── prod.env                   # Backend production (cloud services)
├── staging.env                # Backend staging (optional)
└── apps/desktop/
    ├── dev.env               # Frontend development (localhost URLs)
    └── prod.env              # Frontend production (deployed URLs)
```

## 🚀 Quick Start

### 1. **Set up your backend environment files:**
```bash
# Copy the example for each environment
cp env.example dev.env       # Development (default)
cp env.example prod.env      # Production  
cp env.example staging.env   # Staging (optional)

# Edit each file with environment-specific credentials:
# - APP_NAME (base name for applications, e.g., "myapp" creates "myapp-api", "myapp-agent", "myapp-secrets")
# - Database and service credentials
```

### 2. **Set up your frontend environment files:**
```bash
cd apps/desktop

# Copy the examples
cp env.example dev.env       # Development (localhost URLs)
cp env.example prod.env      # Production (deployed URLs)

# Edit with your specific URLs:
# dev.env:  VITE_BACKEND_API_URL=http://localhost:8000
# prod.env: VITE_BACKEND_API_URL=https://your-api.domain.com
```

### 3. **Run database migrations locally**:
```bash
# Uses dev.env by default
./migrate

# For other environments, temporarily copy: cp prod.env dev.env
```

### 4. **Local Development**:
```bash
# Start all backend services (uses dev.env automatically)
make dev

# This automatically:
# - Uses dev.env for backend configuration
# - Creates .env symlink for Docker Compose
# - Starts API, Agent, Scraper + follows colored logs
```

### 5. **Desktop/Frontend Development**:
```bash
# Start desktop app in development mode (uses apps/desktop/dev.env)
make desktop-dev

# Build desktop app for production (uses apps/desktop/prod.env)
make desktop-build

# Build desktop app for development testing (uses apps/desktop/dev.env)
make desktop-build-dev
```

### 6. **Deploy to cloud environments**:
```bash
# Deploy to production
make deploy tenant=prod

# Deploy to staging  
make deploy tenant=staging

# Deploy to default/development
make deploy
```

That's it! This will automatically:
- ✅ Login to Cloud and select your project
- ✅ Build Docker images for API and Telephony Agent
- ✅ Push images to Github Container Registry  
- ✅ Create secrets from your environment file
- ✅ Deploy API application with auto-scaling (0.5 CPU, 1G memory)
- ✅ Deploy Telephony Agent application (2.0 CPU, 4G memory)
- ✅ Configure proper resource allocations and scaling

## 🛠️ Daily Development Commands

### **Local Development**
```bash
# Start local development (backend)
make dev                            # Uses dev.env automatically
make stop-dev                       # Stop all local services
make clean-dev                      # Clean logs and orphaned processes

# Desktop/Frontend development
make desktop-dev                    # Start desktop app (uses apps/desktop/dev.env)
make desktop-build                  # Build for production (uses apps/desktop/prod.env)
make desktop-build-dev              # Build for dev testing (uses apps/desktop/dev.env)
make desktop-clean                  # Clean build artifacts

# Development status and logs
make dev-status                     # Show status of all local services
make dev-logs-infra                 # Follow Centrifugo logs only
```

### **Cloud Development Cycle**
```bash
# Development cycle (with tenant support)
make build tenant=prod              # Build Docker images for production
make push tenant=staging            # Build and push to registry for staging
make update tenant=dev              # Update both applications in dev

# Update individual applications
make update-api tenant=prod         # Update API only in production
make update-agent tenant=staging    # Update Telephony Agent in staging

# Monitor your applications  
make logs-api tenant=prod           # Show recent API logs from production
make logs-agent tenant=staging      # Show recent Agent logs from staging
make logs-api-follow tenant=prod    # Follow API logs in real-time
make logs-agent-follow tenant=dev   # Follow Agent logs in real-time

# Test your applications
make test-api tenant=prod           # Run API health check

# Application management
make restart-api tenant=staging     # Restart API in staging
make restart-agent tenant=prod      # Restart Agent in production

# Local database migrations
./migrate                           # Run migrations locally (uses dev.env)
```

## 🗣️ Chat Client Testing

For local development and testing of the telephony agent without real phone calls:

```bash
# Quick start - automated testing setup
make chat-test                      # Start server + open chat client (uses default phone)
make chat-test phone=+1555123456    # Start server + open chat client (specific phone)
make chat-stop                      # Stop the background server when done

# Manual testing (for more control)
make chat-server                    # Start LiveKit agent server in text-only mode
make chat-client                    # Start chat client in current terminal (default phone)
make chat-client phone=+1555123456  # Start chat client with specific business phone

# Multi-business testing workflow
make chat-test phone=+1555123456    # Test Restaurant A
# ... interact with Restaurant A agent ...
# Type 'quit' to exit chat client

make chat-test phone=+1555789012    # Test Restaurant B (same server)
# ... interact with Restaurant B agent ...
# Type 'quit' to exit

make chat-stop                      # Clean shutdown when done
```

**What `chat-test` does:**
- ✅ Starts LiveKit agent server in text-only mode (background)
- ✅ Waits 3 seconds for server initialization  
- ✅ Opens new terminal window with chat client
- ✅ Loads restaurant context based on phone number
- ✅ Cross-platform terminal support (macOS Terminal, Linux gnome-terminal, xterm)

**Business Context Loading:**
- Each chat session can test different restaurants by specifying `phone=+1234567890`
- Agent loads menu, hours, and configuration for that specific business
- Defaults to `DEFAULT_TELNYX_PHONE` from `.env` if no phone specified
- One server can handle multiple business contexts without restart

## 🔧 Configuration Management

### When you update environment files:
```bash
# Update applications after changing .envprod
make update tenant=prod

# Update only secrets after changing .envstaging  
make update-secret tenant=staging

# Update default environment
make update
```

## 🎯 Application Architecture

### 📱 **API Application (`{APP_NAME}-api`)**
- **Purpose**: RESTful API for restaurant management, orders, customer profiles
- **Resources**: 0.5 CPU, 1G memory, 2G storage, auto-scales 1-10 instances  
- **Port**: 8000
- **Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 2`

### 📞 **Telephony Agent Application (`{APP_NAME}-agent`)**
- **Purpose**: AI voice agent for handling restaurant phone calls
- **Resources**: 2.0 CPU, 4G memory, 4G storage, auto-scales 1-5 instances
- **Port**: 8080  
- **Command**: `python -m src.agents.telephony.entrypoint`

### 🔐 **Secrets (`{APP_NAME}-secrets`)**
- **Purpose**: Stores environment variables and credentials
- **Source**: Created from your environment files (`.env`, `.envprod`, etc.)
- **Usage**: Automatically injected into both applications

## 🔄 Development Workflows

### **First Time Setup**
```bash
# 1. Backend environment setup
cp env.example dev.env       # Development (default)
cp env.example prod.env      # Production
cp env.example staging.env   # Staging (optional)
# Edit each file with environment-specific credentials

# 2. Frontend environment setup
cd apps/desktop
cp env.example dev.env       # Development URLs
cp env.example prod.env      # Production URLs
cd ../..

# 3. Run database migrations locally
./migrate

# 4. Start local development
make dev                     # Test backend locally

# 5. Deploy to staging first
make deploy tenant=staging

# 6. Deploy to production
make deploy tenant=prod

# 7. Verify deployments
make test-api tenant=staging
make test-api tenant=prod
```

### **Development Cycle**
```bash
# Make code changes...

# Test locally first
make dev                            # Start local development
# ... test your changes ...
make stop-dev                       # Stop when done

# Test in staging
make update tenant=staging
make logs-api-follow tenant=staging

# Deploy to production when ready
make update tenant=prod
make logs-api-follow tenant=prod
```

### **Multi-Environment Management**
```bash
# Different regions/projects per environment
make deploy tenant=dev      # Uses dev.env (us-east region)
make deploy tenant=staging  # Uses staging.env (us-south region)  
make deploy tenant=prod     # Uses prod.env (eu-gb region)

# Monitor different environments
make logs-api tenant=dev &
make logs-agent tenant=staging &
make test-api tenant=prod
```

## 🔐 Cloud Environment Sync

All cloud platforms require environment variables to be synced to their respective secret stores. The `prod.env` file is the **single source of truth** - sync scripts automatically detect sensitive values and push them to the cloud.

### **Unified Workflow (All Platforms)**

All platforms follow the same 3-step workflow:

```bash
# Step 1: Build and push images to GHCR
make push tenant=prod

# Step 2: Sync environment to cloud secret store
make [platform]-sync-env tenant=prod

# Step 3: Deploy
make [platform]-deploy tenant=prod
```

### **Environment Sync Commands**

| Platform | Secret Store | Sync Command | Deploy Command |
|----------|--------------|--------------|----------------|
| Azure Container Apps | Key Vault | `make azure-sync-env tenant=prod` | `make azure-deploy tenant=prod` |
| GCP Cloud Run | Secret Manager | `make gcp-sync-env tenant=prod` | `make gcp-deploy tenant=prod` |
| AWS Fargate | Secrets Manager | `make aws-sync-env tenant=prod` | `make aws-deploy tenant=prod` |

### **Azure Workflow**
```bash
# Preview what will be synced (dry run)
make azure-sync-env-dry-run tenant=prod

# Sync prod.env → Azure Key Vault
make azure-sync-env tenant=prod

# Deploy containers
make azure-deploy tenant=prod

# Grant containers access to Key Vault secrets
make azure-setup-identity tenant=prod

# Day-to-day updates
make push tenant=prod && make azure-update tenant=prod
```

### **GCP Workflow**
```bash
# Preview what will be synced (dry run)
make gcp-sync-env-dry-run tenant=prod

# Sync prod.env → Google Secret Manager
make gcp-sync-env tenant=prod

# Deploy containers
make gcp-deploy tenant=prod

# Day-to-day updates
make push tenant=prod && make gcp-update tenant=prod
```

### **AWS Workflow**
```bash
# Preview what will be synced (dry run)
make aws-sync-env-dry-run tenant=prod

# Sync prod.env → AWS Secrets Manager
make aws-sync-env tenant=prod

# Deploy containers
make aws-deploy tenant=prod

# Day-to-day updates
make push tenant=prod && make aws-update tenant=prod
```

### **How It Works**
1. Edit `prod.env` as usual (database credentials, API keys, etc.)
2. Run the sync command - it automatically detects sensitive values
3. Sensitive vars (`PASSWORD`, `SECRET`, `KEY`, `TOKEN`, `API_KEY`) → Secret Store
4. Non-sensitive vars → Plain environment variables
5. Deploy containers - they reference secrets from the store

### **Quick Reference: All Platform Commands**

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

**Generated files** are stored in `infrastructure/{azure,gcp,aws}/` for reference.

## 🚀 Advanced Operations

### **Monitoring & Debugging**
```bash
# Real-time monitoring per environment
make logs-api-follow tenant=prod        # Follow production API logs
make logs-agent-follow tenant=staging   # Follow staging Agent logs
```

### **Application Management**
```bash
# Restart applications per environment
make restart-api tenant=prod
make restart-agent tenant=staging

# Delete applications (be careful!)
make delete-api tenant=staging
make delete-agent tenant=dev

# Update secrets after changing environment files
make update-secret tenant=prod
```

### **Tenant Management Best Practices**
```bash
# Example environment-specific APP_NAME values:
# dev.env:     APP_NAME=myapp-dev      → myapp-dev-api, myapp-dev-agent
# staging.env: APP_NAME=myapp-staging  → myapp-staging-api, myapp-staging-agent  
# prod.env:    APP_NAME=myapp          → myapp-api, myapp-agent

# This prevents accidental cross-environment deployments
```

## 🎯 **Environment Variables Summary**

### **Backend Files** (Root Directory)
- **`dev.env`**: Local development, localhost services
- **`prod.env`**: Production deployment, cloud services  
- **`staging.env`**: Staging deployment (optional)

### **Frontend Files** (`apps/desktop/`)
- **`dev.env`**: Development URLs (localhost:8000)
- **`prod.env`**: Production URLs (deployed endpoints)

### **Auto-Generated Files**
- **`.env`**: Symlink created automatically during `make dev` (points to `dev.env`)
- **`apps/desktop/.env`**: Created during build from respective environment file