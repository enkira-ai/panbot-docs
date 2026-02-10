---
title: Authentication with Logto
description: How to set up Logto Cloud as PanBot's identity provider with social login (Google, Facebook, Microsoft, Apple).
---

:::caution[🚧 Planned / Target State]
Logto integration is **planned** (see Issue #30) and not fully implemented in the codebase yet. Use this guide as a target-state reference.
Current production auth uses **fastapi-users JWT**.
:::

PanBot uses [Logto](https://logto.io) as its OIDC identity provider. This guide covers setting up Logto Cloud, configuring social login connectors, and connecting everything to the PanBot backend and web dashboard.

## Prerequisites

- A Logto Cloud account ([sign up free](https://cloud.logto.io))
- Access to the PanBot backend (`src/`) and web dashboard (`apps/web/`)
- Developer accounts for each social provider you want to enable

## Logto Cloud Setup

:::tip[Automated Setup Available]
We provide a Python script that automates most of the Logto configuration via the Management API. See [Automated Setup with Script](#automated-setup-with-script) below for the faster path.
:::

### Manual Setup

#### Create Your Tenant

1. Sign in to [Logto Cloud](https://cloud.logto.io)
2. Create a tenant if you don't have one
3. Note your **Logto endpoint** — it looks like `https://<tenant-id>.logto.app`

#### Create the Web Dashboard Application

1. Go to **Applications** → **Create application**
2. Choose **Traditional Web** as the type
3. Name it `PanBot Dashboard`
4. After creation, copy these values (you'll need them for environment variables):

| Value | Where to find it |
|-------|-----------------|
| **App ID** | Application details page |
| **App Secret** | Click "Show" on application details page |
| **Endpoint** | Your tenant URL, e.g. `https://abc123.logto.app` |

5. Add **Redirect URIs**:
   - Development: `http://localhost:3000/callback`
   - Production: `https://your-dashboard-domain.com/callback`
6. Add **Post sign-out redirect URIs**:
   - Development: `http://localhost:3000`
   - Production: `https://your-dashboard-domain.com`
7. Click **Save changes**

### Create the API Resource

This tells Logto about PanBot's backend API so it can issue access tokens for it.

1. Go to **API Resources** → **Create API resource**
2. **Name**: `PanBot Backend API`
3. **API Identifier**: `https://api.novaserve.ai` (use your actual API domain — this is a logical identifier, not a URL that Logto calls)
4. Add permissions in the **Permissions** tab:

| Permission | Description |
|-----------|-------------|
| `read:businesses` | View business information |
| `write:businesses` | Modify businesses |
| `read:orders` | View orders |
| `write:orders` | Modify orders |
| `read:calls` | View call records |
| `read:menus` | View menus |
| `write:menus` | Edit menus |
| `manage:staff` | Manage staff accounts |

### Create Roles

Go to **Authorization** → **Roles** and create:

| Role | Permissions |
|------|-------------|
| `staff` | `read:businesses`, `read:orders`, `read:calls`, `read:menus` |
| `owner` | All read + all write + `manage:staff` |
| `admin` | All permissions |

---

## Automated Setup with Script

For faster setup, use the provided automation script that configures everything via Logto Management API.

### Prerequisites

1. **Install dependencies**:
   ```bash
   pip install requests pyyaml
   ```

2. **Create an M2M app in Logto Console** (one-time manual step):
   - Go to **Applications** → **Create** → **Machine-to-machine**
   - Name: `Setup Automation`
   - Go to **Authorization** → **Roles** → Assign **"Logto Management API access"** role
   - Copy the **App ID** and **App Secret**

3. **Get OAuth credentials** from each social provider you want to enable. See the [OAuth Credentials Guide](https://github.com/StellarChiron/panbot/blob/main/dev_docs/oauth_credentials_guide.md) for detailed steps:
   - Google → Client ID + Client Secret
   - Facebook → App ID + App Secret
   - Microsoft → Client ID + Client Secret + Tenant ID
   - Apple → Service ID + Team ID + Key ID + Private Key (.p8 file)
   - LinkedIn → Client ID + Client Secret
   - WeChat → App ID + App Secret

### Run the Setup Script

1. **Create configuration file**:
   ```bash
   cp scripts/logto_config.example.yaml scripts/logto_config.yaml
   ```

2. **Edit `scripts/logto_config.yaml`** and fill in:
   - Your Logto endpoint and M2M credentials
   - OAuth credentials from each provider
   - Production redirect URIs

3. **Run the script**:
   ```bash
   python scripts/setup_logto.py --config scripts/logto_config.yaml
   ```

   Or use interactive mode:
   ```bash
   python scripts/setup_logto.py --interactive
   ```

4. **Copy the generated credentials** to your environment files as shown in the script output.

The script creates:
- Web dashboard application with configured redirect URIs
- API resource (`https://api.novaserve.ai`) with permissions
- RBAC roles (staff, owner, admin)
- Social connectors (Google, Facebook, Microsoft, Apple, LinkedIn, WeChat)

---

## Manual Social Login Setup

If you prefer to configure social connectors manually through the Logto Console UI:

### Google

#### 1. Google Cloud Console

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. **Create Credentials** → **OAuth client ID** → Type: **Web application**
3. Add **Authorized redirect URI**: copy the exact URI shown in Logto's Google connector setup page
   - Format: `https://<your-tenant>.logto.app/callback/<connector-id>`
4. Copy the **Client ID** and **Client Secret**

#### 2. Logto Console

1. **Connectors** → **Social connectors** → **Add** → **Google**
2. Paste **Client ID** and **Client Secret**
3. Default scopes (`openid profile email`) are sufficient
4. Save

:::note
Google requires HTTPS for all redirect URIs. Changes to redirect URIs can take up to 5 minutes to propagate.
:::

### Facebook

#### 1. Meta Developer Portal

1. Go to [Meta for Developers](https://developers.facebook.com/apps) → **Create App**
2. Select **Authentication and account creation**
3. In the app, add the **Facebook Login** product
4. Go to **Facebook Login** → **Settings**
5. Add **Valid OAuth Redirect URI** from Logto's Facebook connector page
6. Enable **Client OAuth Login** and **Web OAuth Login**
7. Copy **App ID** and **App Secret** from **Settings** → **Basic**

#### 2. Logto Console

1. **Connectors** → **Social connectors** → **Add** → **Facebook**
2. Paste **Client ID** (App ID) and **Client Secret** (App Secret)
3. Save

#### 3. Go Live

Facebook apps start in Development mode (only developers/testers can log in). For production:

1. Fill in **Privacy Policy URL** and **Data Deletion** URL in **Settings** → **Basic**
2. Click the **Live** switch in the app's top bar

### Microsoft (Entra ID)

#### 1. Entra Admin Center

1. Go to [Microsoft Entra admin center](https://entra.microsoft.com/) → **Identity** → **Applications** → **App registrations**
2. **New registration**:
   - Name: `Logto SSO Integration`
   - Supported account types: **Multitenant + personal accounts** (for broadest access)
   - Redirect URI: Platform = **Web**, URI from Logto's Microsoft connector page
3. Copy **Application (client) ID** from the Overview page
4. Go to **Certificates & secrets** → **New client secret** → Copy the **Value** immediately (it won't be shown again)
5. Go to **Overview** → **Endpoints** → Copy **OpenID Connect metadata document** URL, then remove the `/.well-known/openid-configuration` suffix to get the Issuer URL

#### 2. Logto Console

1. **Connectors** → **SSO connectors** → **Add** → **Microsoft Entra ID (OIDC)**
2. Enter **Client ID**, **Client Secret**, and **Issuer URL**
3. Save

:::caution
Don't include `/.well-known/openid-configuration` in the Issuer URL — Logto appends it automatically. Client secrets expire — set a reminder to rotate before expiry.
:::

### Apple Sign-In

Apple Sign-In requires an Apple Developer Program membership ($99/year) and has stricter requirements than other providers.

#### 1. Apple Developer Portal

**Create a Service ID** (for web login):

1. Go to [Identifiers](https://developer.apple.com/account/resources/identifiers/) → **+** → **Services IDs**
2. Identifier: `com.yourcompany.panbot.web`
3. Enable **Sign in with Apple** → **Configure**
4. **Domains**: Enter your Logto tenant domain without protocol (e.g., `abc123.logto.app`)
5. **Return URLs**: Copy from Logto's Apple connector page
6. Save

**Create a Signing Key**:

1. Go to **Keys** → **+** → Enable **Sign in with Apple** → Configure → Select your App ID → Save
2. **Register** and **Download** the `.p8` key file
3. Note the **Key ID** (10-character string)

:::danger
The `.p8` key file can only be downloaded once. Store it securely in your team's secrets manager.
:::

4. Find your **Team ID** in the top-right corner of the Apple Developer portal

#### 2. Logto Console

1. **Connectors** → **Social connectors** → **Add** → **Apple**
2. Enter:
   - **Client ID**: Your Service ID identifier (`com.yourcompany.panbot.web`)
   - **Team ID**: 10-character alphanumeric string
   - **Key ID**: From the signing key
   - **Private Key**: Full contents of the `.p8` file
3. Save

:::note
Apple does not support HTTP or localhost. For local development, add `127.0.0.1 dev.panbot.local` to `/etc/hosts` and use [mkcert](https://github.com/FiloSottile/mkcert) for a local HTTPS certificate.
:::

---

## Environment Configuration

### Backend (`dev.env` / `prod.env`)

```bash
LOGTO_ENDPOINT=https://<your-tenant>.logto.app
LOGTO_APP_ID=<your-app-id>
LOGTO_APP_SECRET=<your-app-secret>
```

### Web Dashboard (`apps/web/.env.local`)

```bash
LOGTO_ENDPOINT=https://<your-tenant>.logto.app
LOGTO_APP_ID=<your-app-id>
LOGTO_APP_SECRET=<your-app-secret>
LOGTO_COOKIE_SECRET=<random-string-min-32-chars>
LOGTO_BASE_URL=http://localhost:3000
LOGTO_API_RESOURCE=https://api.novaserve.ai
```

Generate the cookie secret:

```bash
openssl rand -base64 32
```

---

## How It Works

### Authentication Flow

```
Browser → Logto sign-in page → Social provider (Google/FB/MS/Apple)
  ↓
Logto validates identity, issues authorization code
  ↓
Browser redirects to /callback with auth code
  ↓
Next.js exchanges code with Logto for tokens (server-side)
  ↓
Next.js calls POST /api/v1/auth/oidc/callback on PanBot backend
  ↓
Backend validates tokens, syncs user to UserDB + UserBusinessDB
  ↓
Backend returns PanBot JWT (access + refresh tokens)
  ↓
Dashboard uses PanBot JWT for all subsequent API calls
```

### Key Files

| File | Purpose |
|------|---------|
| `apps/web/lib/logto.ts` | Logto SDK configuration |
| `apps/web/app/api/logto/` | Sign-in, sign-out, callback, access-token routes |
| `apps/web/lib/auth.ts` | `useAuth()` hook for client components |
| `apps/web/middleware.ts` | Route protection (checks `logto-session` cookie) |
| `src/auth/oidc.py` | Backend OIDC token validation (JWKS-based) |
| `src/api/v1/auth_fastapi_users.py` | `/auth/oidc/callback` and `/auth/oidc/webhook` endpoints |

---

## Machine-to-Machine (M2M)

For backend services (scrapers, workers, scheduled jobs) that call PanBot APIs without a user:

1. Create an **M2M application** in Logto Console
2. Assign a role with the required API permissions
3. Use the **client credentials** grant to get an access token:

```bash
curl -X POST https://<tenant>.logto.app/oidc/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic $(echo -n 'APP_ID:APP_SECRET' | base64)" \
  -d "grant_type=client_credentials&resource=https://api.novaserve.ai&scope=read:orders write:orders"
```

Cache the returned token (valid for ~1 hour) and refresh before expiry.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Redirect URI mismatch" | URI must match exactly in both Logto and the provider — check protocol, trailing slash, port |
| "Invalid client_id" | Verify App ID in env vars matches Logto Console |
| Apple login fails locally | Apple requires HTTPS + real domain — use mkcert with a hosts file entry |
| Facebook "only admins can use this app" | Switch app to Live mode in Meta developer portal |
| Microsoft "needs admin approval" | Ask tenant admin to grant consent, or use multitenant + personal account type |
| 401 from backend API | Access token may be expired — frontend refreshes automatically via `/api/logto/access-token` |
| "Cookie too large" error | Reduce requested scopes or check for oversized session data |

---

## References

- [Logto Docs: Next.js App Router Quick Start](https://docs.logto.io/quick-starts/next-app-router)
- [Logto Docs: Protect API Resources](https://docs.logto.io/authorization/global-api-resources)
- [Logto Docs: Machine-to-Machine](https://docs.logto.io/quick-starts/m2m)
- [Google OAuth 2.0 for Web](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Facebook Login for Web](https://developers.facebook.com/docs/facebook-login/web)
- [Microsoft Entra ID OIDC](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc)
- [Apple Sign-In for Web](https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_js)
