# namgun.or.kr Integrated Portal SSO Platform — Project Progress Report

| Field | Detail |
|-------|--------|
| Project | namgun.or.kr Integrated Portal SSO Platform |
| Author | 남기완 (Kiwan Nam) |
| Classification | Internal / Confidential |

## Document History

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| v1.0 | 2026-02-18 | 남기완 | Initial release (Phase 0 through Phase 2 complete) |
| v1.1 | 2026-02-19 | 남기완 | Updated through Phase 3 – Phase 6 completion |
| v1.2 | 2026-02-21 | 남기완 | Added Phase 6.5 (Auth Gateway) and Phase 7 (Registration & Admin Panel) |

---

## 1. Project Overview

The namgun.or.kr Integrated Portal is a self-hosted, unified platform designed for household and small-organization use. It places Authentik as the central Identity Provider (IdP) and aims to consolidate diverse services — Git hosting, remote desktop, mail, video conferencing, file management, and game servers — under a single SSO (Single Sign-On) umbrella.

### 1.1 Core Objectives

- Unified SSO authentication across all services (OIDC / LDAP)
- Infrastructure aligned with ISMS-P security standards
- Data sovereignty through self-hosting
- Phased service rollout (Phase 0 through Phase 6)

---

## 2. Phase Progress Overview

| Phase | Name | Status | Period | Notes |
|-------|------|--------|--------|-------|
| Phase 0 | Infrastructure Preparation | **Complete** | — | Authentik, DNS, Nginx, TLS |
| Phase 1 | SSO PoC | **Complete** | — | Gitea OIDC, RustDesk OIDC |
| Phase 2 | Mail Server Migration | **Complete** | — | Stalwart + LDAP + OIDC |
| Phase 3 | Portal Core Development | **Complete** | — | Nuxt 3 + FastAPI + PostgreSQL |
| Phase 4 | File Browser | **Complete** | — | NFS mount + in-portal file management UI |
| Phase 5 | Service Enhancements & Mail/Conferencing Integration | **Complete** | — | BBB, mail iframe, caching, navigation |
| Phase 6 | Native Login & SSO Integration | **Complete** | — | Native login form, Popup Bridge, Gitea SSO |
| Phase 6.5 | Central Auth Gateway Transition | **Complete** | — | Server-side login, Portal OIDC Provider, Popup Bridge removal |
| Phase 7 | Registration & Admin Panel | **Complete** | — | Approval-based registration, profile/password management, admin panel, RBAC |

---

## 3. Infrastructure Topology

### 3.1 Physical / Logical Layout

```
Internet
  │
  ├─ 211.244.144.47 (Public IP, main services)
  │    └─ Port forwarding → 192.168.0.150 (Nginx Reverse Proxy)
  │
  ├─ 211.244.144.69 (Public IP, MX record)
  │    └─ Direct connection → 192.168.0.250 (Stalwart Mail)
  │
  ┌──────────────────── LAN 192.168.0.0/24 ────────────────────┐
  │                                                              │
  │  [192.168.0.50] Windows Host (Dual Xeon Gold 6138, 128GB)   │
  │    └─ WSL2 / Docker                                          │
  │       ├─ Authentik (server + worker + PostgreSQL 16)         │
  │       ├─ Portal Stack                                        │
  │       │    ├─ portal-frontend (Nuxt 3 SSR, :3000)           │
  │       │    ├─ portal-backend (FastAPI, :8000)                │
  │       │    ├─ portal-db (PostgreSQL 16, named volume)        │
  │       │    └─ portal-nginx (internal reverse proxy, :8080)   │
  │       ├─ Gitea 1.25.4                                        │
  │       ├─ RustDesk Pro (hbbs + hbbr)                          │
  │       └─ Game Panel (backend + nginx + palworld)             │
  │                                                              │
  │  [192.168.0.100] OMV (OpenMediaVault) — NAS                 │
  │    └─ NFSv4 server (/export/root, fsid=0)                   │
  │       └─ /portal → Docker NFS volume (/storage)             │
  │                                                              │
  │  [192.168.0.150] Hyper-V VM — Nginx (Rocky Linux 10)        │
  │    └─ Central reverse proxy, TLS Termination                 │
  │                                                              │
  │  [192.168.0.249] BigBlueButton 3.0 (Video Conferencing)     │
  │    └─ BBB API (SHA256 checksum authentication)               │
  │                                                              │
  │  [192.168.0.250] Hyper-V VM — Mail (Rocky Linux 9.7)        │
  │    └─ Podman (rootless)                                      │
  │       ├─ Stalwart Mail Server (network_mode: host)           │
  │       └─ Authentik LDAP Outpost (sidecar)                    │
  │                                                              │
  │  [192.168.0.251] Pi-Hole DNS (Internal primary DNS)          │
  │                                                              │
  └──────────────────────────────────────────────────────────────┘
```

### 3.2 Service Status Summary

| Service | Subdomain | Host | SSO Method | Status |
|---------|-----------|------|------------|--------|
| Portal | namgun.or.kr | 192.168.0.50 (Docker) | OIDC (native) | Operational |
| Authentik | auth.namgun.or.kr | 192.168.0.50 (Docker) | — (IdP) | Operational |
| Gitea | git.namgun.or.kr | 192.168.0.50 (Docker) | OIDC + Portal SSO | Operational |
| RustDesk Pro | remote.namgun.or.kr | 192.168.0.50 (Docker) | OIDC | Operational |
| Game Panel | game.namgun.or.kr | 192.168.0.50 (Docker) | Discord OAuth2 | Operational |
| BBB (Video Conferencing) | meet.namgun.or.kr | 192.168.0.249 | OIDC (integrated within portal) | Operational |
| OMV/Files | — | 192.168.0.100 (NFS) | In-portal file browser | Operational |
| Stalwart Mail | mail.namgun.or.kr | 192.168.0.250 (Podman) | LDAP + OIDC, in-portal iframe integration | Operational |
| LDAP Outpost | — | 192.168.0.250 (Podman sidecar) | — | Operational |
| Nginx Proxy | *.namgun.or.kr | 192.168.0.150 (VM) | — | Operational |
| Pi-Hole | — | 192.168.0.251 | — | Operational |

> **Gitea note**: The Gitea login page has its built-in login form disabled, exposing only the OAuth2 (Authentik) button. Unauthenticated users accessing Gitea are redirected to the portal login page via the Nginx `portal_redirect` rule.

---

## 4. Phase 0: Infrastructure Preparation (Complete)

### 4.1 Authentik SSO (Identity Provider)

- **Version**: 2025.10.4
- **Deployment**: Docker Compose (192.168.0.50)
- **Components**: Authentik Server (:9000/:9443), Worker, PostgreSQL 16
- **Access URL**: https://auth.namgun.or.kr
- **Bootstrap**: Admin account creation complete

#### Caveats and Troubleshooting

| Item | Details |
|------|---------|
| BOOTSTRAP_PASSWORD | Special characters (e.g., `==`) cause authentication failure. Use simple alphanumeric strings only. |
| Reputation system | Login is blocked once the reputation score accumulates. Resolve by clearing the `Reputation` table. |
| redirect_uris format | Version 2025.10 requires `RedirectURI` dataclass list format. Creating via REST API is recommended. |
| OAuth2Provider required fields | `authorization_flow` and `invalidation_flow` are mandatory. REST API usage is recommended over the CLI shell. |

### 4.2 DNS Configuration

- **Management tool**: Windows Server DNS
- **Internal DNS**: Pi-Hole (192.168.0.251)
- **Registered records**:
  - A records: All subdomains (auth, git, game, mail, meet, remote, namgun.or.kr)
  - MX record: mail.namgun.or.kr
  - TXT records: SPF, DKIM, DMARC

#### Windows Server DNS Limitation

> When a TXT record exceeds 255 characters, it must be split into multiple strings within a single record. The DKIM public key (RSA-2048) is a representative example.

### 4.3 Nginx Reverse Proxy (192.168.0.150)

- **OS**: Rocky Linux 10 (Hyper-V VM)
- **Number of site configuration files**: 7

```
/etc/nginx/conf.d/
├── auth.namgun.or.kr.conf
├── git.namgun.or.kr.conf
├── game.namgun.or.kr.conf
├── mail.namgun.or.kr.conf
├── meet.namgun.or.kr.conf
├── remote.namgun.or.kr.conf
└── namgun.or.kr.conf
```

- **TLS Termination**: Let's Encrypt (certbot webroot)
- **HTTP/2**: Uses the `http2 on` directive (not the deprecated `listen ... ssl http2` syntax)

#### ISMS-P Security Headers (Applied to All Sites)

```nginx
# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# Suppress server information disclosure
server_tokens off;
proxy_hide_header X-Powered-By;
proxy_hide_header Server;

# Scanner/bot blocking rules applied
```

### 4.4 TLS Certificates

| Target | Issuance Method | Renewal Method |
|--------|----------------|----------------|
| Nginx sites (*.namgun.or.kr) | Let's Encrypt certbot | webroot (/var/www/certbot), automatic renewal |
| Stalwart Mail Server | Let's Encrypt ACME | Stalwart built-in ACME automatic renewal (separate from Nginx) |

---

## 5. Phase 1: SSO PoC (Complete)

### 5.1 Gitea SSO Integration

- **Version**: 1.25.4
- **Access URL**: https://git.namgun.or.kr
- **Authentication method**: OAuth2 via Authentik OIDC

#### Configuration Method

The OAuth2 authentication source is not supported by the Gitea API, so it was added via the CLI.

```bash
docker exec --user git gitea gitea admin auth add-oauth \
  --name "Authentik" \
  --provider openidConnect \
  --key "<client-id>" \
  --secret "<client-secret>" \
  --auto-discover-url "https://auth.namgun.or.kr/application/o/<slug>/.well-known/openid-configuration"
```

> **Note**: The command must be executed with `--user git`. Running as root will produce a permission error.

#### SSO Flow Verification

1. User navigates to the Gitea login page
2. Clicks "Sign in with Authentik" button
3. Redirected to the Authentik authentication screen
4. After successful authentication, callback to Gitea
5. Gitea dashboard access confirmed

### 5.2 RustDesk Pro SSO Integration

- **Access URL**: https://remote.namgun.or.kr
- **Components**: hbbs (signaling server) + hbbr (relay server)
- **Authentication method**: OIDC via Authentik

---

## 6. Phase 2: Mail Server Migration (Complete)

The legacy mail server based on iRedMail (Postfix + Dovecot) was migrated to Stalwart Mail Server, and authentication integration via Authentik LDAP was completed.

### 6.1 Step-by-Step Progress

#### Step 1: Authentik LDAP Outpost Configuration

| Item | Details |
|------|---------|
| Base DN | `dc=ldap,dc=goauthentik,dc=io` |
| LDAP Application | Created LDAP Provider + Application + Outpost in Authentik |
| Service account | Created `ldapservice` user, granted "Search full LDAP directory" permission |
| Deployment location | Deployed as a sidecar on the mail server VM (192.168.0.250) |

> **Rationale for outpost deployment location**: In a rootless Podman environment, access to the host LAN IP is unreliable, so the LDAP Outpost was placed as a sidecar on the same VM as the mail server.

#### Step 2: Stalwart Mail Server Deployment

- **Deployment**: Podman (rootless), `network_mode: host`
- **Storage**: RocksDB
- **Configuration management**: After initial boot, settings are persisted in RocksDB and managed via CLI/API
- **TLS**: Let's Encrypt ACME automatic renewal
- **stalwart-cli path**: Inside the Podman overlay filesystem

#### Step 3: Authentik OIDC Application (Stalwart Web UI)

- OAuth2Provider created via Authentik REST API
- Application slug: `stalwart`
- Redirect URI: `https://mail.namgun.or.kr/login/callback`

#### Step 4: Account Migration

A total of 9 accounts were migrated.

**Personal Accounts (5) — LDAP via Authentik**

| Account | Email | Notes |
|---------|-------|-------|
| namgun18 | namgun18@namgun.or.kr | Authentik username changed from `namgun` to `namgun18` (LDAP cn matching) |
| tsha | tsha@namgun.or.kr | Password setup pending |
| nahee14 | nahee14@namgun.or.kr | Password setup pending |
| kkb | kkb@namgun.or.kr | Password setup pending |
| administrator | administrator@namgun.or.kr | — |

**Service Accounts (4) — Stalwart Internal Authentication**

| Account | Purpose |
|---------|---------|
| system | System mail |
| postmaster | Postmaster |
| git | Gitea notification mail |
| noreply | Automated outbound only |

**Mail data migration**: Transferred from Dovecot to Stalwart using imapsync

#### Step 5: DNS Update

| Record | Details | Notes |
|--------|---------|-------|
| DKIM | New RSA-2048 key generated, DNS TXT record updated | Split into 2 strings in Windows DNS |
| SPF | `v=spf1 ip4:211.244.144.69 mx ~all` | No change |
| DMARC | `v=DMARC1; p=quarantine` | No change |
| Selector | `default` | — |

#### Step 6: Nginx Reverse Proxy Configuration

- Configuration file: `mail.namgun.or.kr.conf` (192.168.0.150)
- HTTPS 443 → Stalwart 8080 (Web Admin / JMAP)
- SMTP (25, 465, 587) / IMAP (993) are not proxied (direct connection)
- ISMS-P security headers applied

#### Step 7: Verification Results

| Test Item | Result | Notes |
|-----------|--------|-------|
| SMTP authentication | **Passed** | namgun18@namgun.or.kr via LDAP |
| IMAP authentication | **Passed** | — |
| Outbound delivery | **Passed** | Confirmed receipt at Gmail, amitl.co.kr |
| Inbound delivery | **Passed** | — |
| Samsung Email app | **Passed** | IMAP 993 SSL, SMTP 465 SSL |
| DKIM signing | **Operational** | Message size increase from 1292 → 4313 bytes confirmed |
| DKIM DNS verification | **Pending confirmation** | Public key update complete; need to confirm dkim=pass after DNS cache expiry |
| SPF | **Passed** | — |
| DMARC | **Passed** | Based on SPF alignment |

#### Step 8: iRedMail Removal

Removed packages:

```
postfix, dovecot, amavis, clamav, spamassassin, php-fpm
```

- Disabled nginx on the mail server VM
- Legacy mail data at `/var/vmail/` (72MB) preserved

#### Step 9: Documentation

- `phase2_mail_migration_ko.md` / `_en.md` authored and pushed to Gitea

---

## 7. Phase 3: Portal Core Development (Complete)

The portal web application core was developed using Nuxt 3 + FastAPI + PostgreSQL and deployed to production in a Docker Compose environment.

### 7.1 Technology Stack and Architecture

| Category | Technology |
|----------|------------|
| Frontend | Nuxt 3 (Vue 3, SSR), shadcn-vue (UI components) |
| Backend | FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| Database | PostgreSQL 16 (Alpine) |
| Authentication | OIDC via Authentik (PKCE S256) |
| Session management | itsdangerous (URLSafeTimedSerializer), signed cookies |
| Containers | Docker Compose, `--profile prod` deployment |

### 7.2 Docker Compose Configuration

```
docker compose --profile prod up -d --build
```

| Service | Container Name | Port | Notes |
|---------|---------------|------|-------|
| portal-db | portal-db | — (internal) | PostgreSQL 16-alpine, named volume (`portal-db-data`) |
| backend | portal-backend | 8000 (internal) | FastAPI, healthcheck `/api/health` |
| frontend | portal-frontend | 3000 (internal) | Nuxt 3 SSR |
| nginx | portal-nginx | 8080 (external) | Internal reverse proxy, prod profile only |

> **WSL2 note**: PostgreSQL cannot use NTFS bind mounts, so a Docker named volume (`portal-db-data`) is used instead.

### 7.3 OIDC Authentication (Authentik)

- **Authentication flow**: Authorization Code + PKCE (S256)
- **Endpoints**:
  - Authorization: `https://auth.namgun.or.kr/application/o/authorize/`
  - Token: `https://auth.namgun.or.kr/application/o/token/`
  - Userinfo: `https://auth.namgun.or.kr/application/o/userinfo/`
  - End Session: `https://auth.namgun.or.kr/application/o/portal/end-session/`
- **Redirect URI**: `https://namgun.or.kr/api/auth/callback`
- **PKCE storage**: `portal_pkce` cookie (httponly, secure, samesite=lax, max_age=600)
- **Session cookie**: `portal_session` (httponly, secure, samesite=lax, 7-day validity)

### 7.4 User Model (User)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID (String 36) | PK |
| authentik_sub | String 255 | Authentik subject, unique index |
| username | String 150 | preferred_username |
| display_name | String 255 | Display name (nullable) |
| email | String 255 | Email address (nullable) |
| avatar_url | String 500 | Avatar URL (nullable) |
| is_admin | Boolean | Membership in the Authentik `authentik Admins` group |
| is_active | Boolean | Active status (default: True) |
| last_login_at | DateTime (tz) | Last login timestamp |
| created_at | DateTime (tz) | Creation timestamp |
| updated_at | DateTime (tz) | Last update timestamp |

### 7.5 Dashboard Service Monitoring

- **Number of services**: 6 (Authentik, Gitea, RustDesk, Game Panel, Stalwart Mail, BBB)
- **Health check interval**: 60 seconds (background task)
- **Check method**: HTTP GET (status code < 400 → ok) or TCP port check (RustDesk)
- **In-memory cache**: `_cache` list, queried by frontend at `/api/services/`
- **ServiceCard**: Service name, status badge (ok/down/checking), response time (ms), external URL link

### 7.6 NFS Mount (File Storage)

- **NFS server**: OMV (192.168.0.100), `/export/root` (fsid=0)
- **Docker NFS volume**: `portal-storage` → `/storage` inside containers
- **Mount options**: `addr=192.168.0.100,nfsvers=4,rw,hard,noatime,nolock`
- **Client device**: `:/portal` (because fsid=0 is bound to `/export/root`)

---

## 8. Phase 4: File Browser (Complete)

A file browser was developed that enables web-based management of NFS-mounted storage from within the portal.

### 8.1 NFS Integration Details

| Item | Details |
|------|---------|
| NFS server | OMV (192.168.0.100) |
| Export path | `/export/root` (fsid=0) |
| Docker volume device | `:/portal` |
| NFS version | v4.1 (WSL2 kernel does not support v4.2; v4.1 is used instead) |
| Mount options | `nfsvers=4,rw,hard,noatime,nolock` |
| WSL2 package requirement | `nfs-common` must be installed |

### 8.2 Filesystem Structure

```
/storage/
├── shared/          ← Shared folder (all users can read; only admins can write)
└── users/
    └── {user_id}/   ← Personal folder (isolated per user)
```

- **Virtual path scheme**: `my/...` → `/storage/users/{user_id}/...`, `shared/...` → `/storage/shared/...`
- **Admin path**: `users/...` → `/storage/users/...` (browse all user directories)
- **Path security**: Path traversal prevention via `resolve()` followed by base path prefix verification

### 8.3 File Operations (API)

| Operation | Endpoint | Notes |
|-----------|----------|-------|
| Directory listing | GET `/api/files/list` | Virtual-path based |
| File upload | POST `/api/files/upload` | multipart/form-data, max 1024MB |
| File download | GET `/api/files/download` | StreamingResponse |
| File/folder deletion | DELETE `/api/files/delete` | Admin-only for shared; unrestricted in own folder |
| Rename | POST `/api/files/rename` | — |
| Move/copy | POST `/api/files/move` | Copy supported via `copy` parameter |
| Create folder | POST `/api/files/mkdir` | — |

### 8.4 Frontend UI

- **Breadcrumb navigation**: Displays the current path hierarchically; click to navigate
- **File grid/list view**: Filename, size, modification date, MIME type
- **Sidebar**: Root navigation for my / shared / users (admin)
- **Command bar**: Toolbar for upload, new folder, delete, rename, etc.
- **Context menu**: Right-click menu (download, rename, move, delete)
- **Upload modal**: Drag-and-drop or file selection
- **Preview modal**: Image/text file preview
- **Share link modal**: External share link generation (ShareLink model, expiration/download limits)

---

## 9. Phase 5: Service Enhancements & Mail/Conferencing Integration (Complete)

File listing cache, BBB video conferencing integration, Stalwart Mail iframe integration, service card improvements, and navigation additions were completed.

### 9.1 File Listing Cache

- **In-memory TTL cache**: `_dir_cache` (30-second TTL), `_size_cache` (60-second TTL)
- **Cache invalidation**: `invalidate_cache()` is called after write operations (upload, delete, rename, move, mkdir)
- **asyncio wrapping**: `list_directory()` wrapped with `asyncio.to_thread()` to prevent NFS I/O blocking

### 9.2 BBB Video Conferencing Integration

- **Server**: BigBlueButton 3.0 (192.168.0.249)
- **Access URL**: https://meet.namgun.or.kr
- **API client**: BBB API client with SHA256 checksum authentication (`meetings/bbb.py`)
- **Features**: Create meeting (create), list meetings (getMeetings), meeting details (getMeetingInfo), generate join URL (join), end meeting (end), list/delete recordings (getRecordings/deleteRecordings)
- **Frontend**: MeetingCard, MeetingDetail, CreateMeetingModal, RecordingList components
- **Router**: `/api/meetings/` (list, create, join, end, recordings)

### 9.3 Stalwart Mail iframe Integration

- **Portal access**: The Stalwart web UI is embedded as an iframe on the `/mail` page
- **Nginx configuration**: `mail.namgun.or.kr.conf` uses `Content-Security-Policy: frame-ancestors 'self' https://namgun.or.kr` instead of `X-Frame-Options`
- **Service card**: `internal_only: True` setting hides the external link on the dashboard

### 9.4 Service Card Changes

| Service | Change |
|---------|--------|
| RustDesk | HTTP health check → TCP port check (`192.168.0.50:21114`) |
| Pi-Hole | Removed from SERVICE_DEFS (no longer shown on the portal dashboard) |
| BBB (Video Conferencing) | Newly added (`health_url: https://meet.namgun.or.kr/bigbluebutton/api`, `internal_only: True`) |
| Stalwart Mail | `internal_only: True` setting (external link unnecessary due to iframe integration) |

### 9.5 Navigation Additions

Navigation menu added to AppHeader:

| Menu | Path | Description |
|------|------|-------------|
| Dashboard | `/` | Service status dashboard |
| Files | `/files` | File browser |
| Mail | `/mail` | Stalwart Mail iframe |
| Meetings | `/meetings` | BBB meeting management |

Mobile-responsive navigation (hamburger menu) included.

---

## 10. Phase 6: Native Login & SSO Integration (Complete)

The Authentik redirect-based login was replaced with a native login form, SSO cookies are established through the Popup Bridge pattern, and Gitea SSO integration was implemented.

### 10.1 Native Login Form

- **Page**: `/login` (auth layout)
- **Input fields**: Username/email, password
- **Redirect parameter**: `?redirect=<URL>` query parameter support (for external service SSO)
- **Security**: Redirects are restricted to the `namgun.or.kr` domain or relative paths only

### 10.2 Popup Bridge Pattern

The previous Authentik full-page redirect approach provided a poor UX, and the iframe approach failed to set SSO cookies due to third-party cookie partitioning (browser security policy). The Popup Bridge pattern was adopted to solve these issues.

#### Flow

1. User enters username/password on the `/login` page and submits
2. The browser synchronously opens a `https://auth.namgun.or.kr/portal-bridge/` popup (bypassing popup blockers)
3. The Bridge page sends a `portal-bridge-ready` postMessage
4. The portal retrieves the OIDC config + generates PKCE, then sends a `portal-login` message to the popup
5. The Bridge calls the Authentik Flow Executor API to authenticate (processing each stage sequentially)
6. After authentication completes, the `authorize` endpoint is called → `code` is obtained
7. The Bridge delivers the code to the portal via a `portal-login-result` message
8. The portal backend exchanges the code for a token at `/api/auth/native-callback` and issues a session cookie

#### PKCE S256 Client-Side Generation

```typescript
// code_verifier: 64 random bytes → base64url
// code_challenge: SHA-256(code_verifier) → base64url
```

- Uses `crypto.getRandomValues()` + `crypto.subtle.digest('SHA-256', ...)`
- The PKCE pair is generated on the browser side; `code_verifier` is retained by the portal and not transmitted to the popup

#### Bridge Page Navigation (SSO Cookie Establishment)

- The popup executes in the `https://auth.namgun.or.kr` origin, so Authentik cookies are set as first-party
- Authentik session cookies are stored correctly when the Flow Executor API is invoked
- The Bridge callback page (`/portal-bridge/callback`) extracts the `code` parameter and sends it to the opener via postMessage

### 10.3 Backend Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | GET | OIDC redirect (legacy, sets PKCE cookie) |
| `/api/auth/callback` | GET | OIDC callback (legacy, code exchange + session setup) |
| `/api/auth/oidc-config` | GET | Returns public OIDC configuration (client_id, redirect_uri, scope, flow_slug) |
| `/api/auth/native-callback` | POST | Native login code exchange (code + code_verifier → session cookie) |
| `/api/auth/me` | GET | Current authenticated user information |
| `/api/auth/logout` | POST | Session cookie deletion |

### 10.4 Authentik Flow Executor API Stages

The Authentik API flow invoked by the Bridge during native login:

1. `GET /api/v3/flows/executor/{flow_slug}/` → First stage information
2. `POST /api/v3/flows/executor/{flow_slug}/` (uid_field: username) → Identification stage submission
3. `POST /api/v3/flows/executor/{flow_slug}/` (password: password) → Password stage submission
4. Upon flow completion, a `redirect_to` URL is returned
5. The Bridge invokes the `redirect_to` authorize URL via page navigation → SSO cookie is set + code is issued
6. The callback page extracts the `code` parameter from the URL

> **Note**: When the flow completion returns `to: "/"`, the authorize endpoint must be manually re-invoked.

### 10.5 Gitea SSO Integration

- **Method**: OAuth2-only login (built-in login form not displayed)
- **Unauthenticated access handling**: An Nginx rule in `namgun.or.kr.conf` or `git.namgun.or.kr.conf` redirects unauthenticated users to the portal login page (`?redirect=https://git.namgun.or.kr/user/oauth2/authentik`)
- **Post-authentication**: Portal login completes → Authentik SSO cookie is set → Clicking the Gitea OAuth2 button passes authentication automatically
- **git push HTTP authentication**: Since disabling BASIC_AUTH breaks git push authentication, BASIC_AUTH was re-enabled for HTTP git operations

### 10.6 Login Redirect Parameter

```
https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik
```

- The `redirect` query parameter is used when sending users from external services to the portal login page
- After login completes, the user is automatically redirected to the specified URL
- Security: Only `https://` + `.namgun.or.kr` domains or `/` relative paths are permitted

---

## 11. Phase 6.5: Central Auth Gateway Transition (Complete)

The Popup Bridge authentication mechanism was removed and replaced with server-side authentication where the portal backend directly calls the Authentik Flow Executor API. Additionally, the portal now acts as an OIDC Provider to deliver SSO to external services such as Gitea.

### 11.1 Server-Side Native Login

- **Previous**: Frontend Popup Bridge → Authentik Flow Executor → complex inter-window messaging
- **Current**: Frontend → `POST /api/auth/login` → Backend calls Authentik Flow Executor API directly → session cookie issued
- **Benefits**: No popup blocker issues, no SSO cookies needed, significantly reduced code complexity

#### Authentication Flow

```
1. User enters ID/PW on portal login form
2. POST /api/auth/login → backend
3. Backend → Authentik Flow Executor API (identification → password stage)
4. Authentik → flow complete → backend calls OIDC authorize → token exchange → userinfo
5. Backend → session cookie issued → frontend login complete
```

### 11.2 Portal OIDC Provider (OAuth2 Provider)

The portal acts as an OIDC Provider to deliver SSO to external services like Gitea.

#### Endpoints

| Path | Description |
|------|-------------|
| `GET /oauth/.well-known/openid-configuration` | OIDC Discovery |
| `GET /oauth/authorize` | Authorization endpoint (code issuance) |
| `POST /oauth/token` | Token endpoint (access_token + id_token) |
| `GET /oauth/userinfo` | Userinfo endpoint |

#### Client Management

- Defined as JSON in `.env` `OAUTH_CLIENTS_JSON`
- Current registered client: `portal-gitea` (for Gitea SSO)
- `redirect_uris` whitelist validation
- PKCE (S256) support

### 11.3 Gitea SSO Transition

- **Previous**: Gitea → Authentik OIDC (direct)
- **Current**: Gitea → Portal OIDC Provider (portal session-based SSO)
- **OAuth source changed**: `gitea admin auth add-oauth --name portal --provider openidConnect --auto-discover-url https://namgun.or.kr/oauth/.well-known/openid-configuration`
- **Dashboard link**: `/user/oauth2/portal` (changed from `/user/oauth2/authentik`)

### 11.4 Removed Code

- Popup Bridge frontend (`bridge-login.ts`)
- Authentik Bridge page (`/portal-bridge/`)
- `POST /api/auth/native-callback` (popup-only callback)
- `GET /api/auth/oidc-config` (popup-only config)

---

## 12. Phase 7: Registration & Admin Panel (Complete)

Implemented approval-based registration, profile management, password change/recovery, admin user management, and role assignment features.

### 12.1 Authentik Admin API Client

Developed an httpx-based async client wrapping the Authentik Admin API.

**File**: `backend/app/auth/authentik_admin.py`

| Function | Authentik API | Description |
|----------|--------------|-------------|
| `create_user()` | `POST /api/v3/core/users/` + `set_password` + `add_user` | Create inactive user + set password + add to Users group |
| `activate_user(pk)` | `PATCH /api/v3/core/users/{pk}/` | Activate user (admin approval) |
| `deactivate_user(pk)` | `PATCH /api/v3/core/users/{pk}/` | Deactivate user |
| `set_password(pk, password)` | `POST /api/v3/core/users/{pk}/set_password/` | Change password |
| `delete_user(pk)` | `DELETE /api/v3/core/users/{pk}/` | Delete user |
| `get_recovery_link(pk)` | `POST /api/v3/core/users/{pk}/recovery/` | Generate password recovery link |
| `add_user_to_group()` | `POST /api/v3/core/groups/{pk}/add_user/` | Add to group |
| `remove_user_from_group()` | `POST /api/v3/core/groups/{pk}/remove_user/` | Remove from group |

### 12.2 Approval-Based Registration

#### Registration Flow

```
1. User enters info on /register page
   (username, password, display name, recovery email)
2. Email auto-generated: {username}@namgun.or.kr
3. Authentik API → create user (is_active=False)
4. Portal DB → create User record (is_active=False)
5. "Registration complete, available after admin approval" notice
6. Admin approves on /admin/users page
7. Authentik → is_active=True, Portal DB → is_active=True
8. → LDAP Outpost auto-sync → Stalwart mail becomes available
```

### 12.3 Profile Management

| Endpoint | Description |
|----------|-------------|
| `PATCH /api/auth/profile` | Update display name and recovery email (synced to Authentik + portal DB) |
| `POST /api/auth/change-password` | Change password (verify current password → Authentik set_password) |
| `POST /api/auth/forgot-password` | Password recovery (Authentik recovery link → sent to recovery email) |

### 12.4 Admin User Management

| Endpoint | Description |
|----------|-------------|
| `GET /api/admin/users` | List all users |
| `GET /api/admin/users/pending` | List pending approvals |
| `POST /api/admin/users/{id}/approve` | Approve registration |
| `POST /api/admin/users/{id}/reject` | Reject registration (delete from Authentik + DB) |
| `POST /api/admin/users/{id}/deactivate` | Deactivate user |
| `POST /api/admin/users/{id}/set-role` | Grant/revoke admin role |

- All endpoints require `is_admin` via `require_admin` dependency
- `set-role`: Authentik "authentik Admins" group add/remove + portal DB `is_admin` sync
- Self-protection: cannot change own role or deactivate self

### 12.5 Frontend Pages

| Page | Path | Description |
|------|------|-------------|
| Registration | `/register` | Username (+`@namgun.or.kr` preview), password, display name, recovery email |
| Forgot Password | `/forgot-password` | Username input → recovery link sent to recovery email |
| Profile | `/profile` | User info (readonly) + display name/recovery email edit + password change |
| Admin Panel | `/admin/users` | Pending tab + all users tab (approve/reject/deactivate/role toggle) |

### 12.6 ISMS-P Security Measures

- **akadmin default account deactivated**: Authentik default admin account (akadmin) deactivated, Admin API token reissued under `namgun18` account
- **API token ownership change**: akadmin → namgun18

---

## 13. Key Troubleshooting Summary

| # | Problem | Cause | Resolution |
|---|---------|-------|------------|
| 1 | LDAP authentication failure in Stalwart v0.15 | `bind.auth.enable` defaults to hash comparison mode | Set `bind.auth.method = "lookup"` |
| 2 | Stalwart DKIM signing key not recognized | Key naming convention mismatch | Use `{algorithm}-{domain}` format (e.g., `rsa-namgun.or.kr`) |
| 3 | Stalwart expression field cannot be overridden via DB | Some built-in defaults do not support DB override | Modify directly in the configuration file |
| 4 | Unreliable host LAN IP access from rootless Podman | Podman rootless networking limitations | Use sidecar + `network_mode: host` |
| 5 | Windows Server DNS TXT record save failure | 255-character TXT record limit | Split a single record into multiple strings |
| 6 | Authentik initial login failure | BOOTSTRAP_PASSWORD contained special characters such as `==` | Use simple alphanumeric password |
| 7 | Authentik repeated login blocked | Accumulated reputation score | Clear the `Reputation` table |
| 8 | Permission error when running Gitea CLI | Executed as root user | Specify git user with `--user git` option |
| 9 | PostgreSQL bind mount failure | NTFS (/mnt/d/) filesystem permission issue in WSL2 | Use Docker named volume (`portal-db-data`) |
| 10 | NFS v4.2 mount failure | WSL2 kernel (5.15.x) does not support NFS v4.2 | Use `nfsvers=4` (v4.1) |
| 11 | Browser hang on fetch() cross-origin redirect | fetch enters infinite wait when OIDC redirect_uri is on a different origin | Use same-origin redirect_uri (`namgun.or.kr/api/auth/callback`) |
| 12 | OAuth parameter encoding omission | Missing `encodeURIComponent` caused query parameter corruption | Use `URLSearchParams` for automatic encoding |
| 13 | Authentik flow completion returns `to: "/"` | Flow Executor returns default path redirect instead of authorize | Manually re-invoke the authorize endpoint |
| 14 | Authentik cookies not set in iframe | Browser third-party cookie partitioning policy | Switch from iframe to popup approach (first-party context) |
| 15 | Race condition between Bridge and Portal | postMessage sent before popup finished loading | Send login message only after receiving `portal-bridge-ready` message (listener pre-registration) |
| 16 | SSO cookies not set (fetch-based) | Calling authorize via fetch/XHR does not store browser cookies | Switch to page navigation (`window.location.href`) approach |
| 17 | Gitea automatic login not working | Unauthenticated user accessing Gitea directly has no portal session | Add Nginx redirect rule to portal login page (`?redirect=...`) |
| 18 | git push HTTP authentication failure | BASIC_AUTH was disabled | Re-enable BASIC_AUTH for HTTP git operations |
| 19 | `recovery_email` column missing (500 error) | `create_all()` cannot add columns to existing tables | Manual `ALTER TABLE users ADD COLUMN` |
| 20 | `authentik_sub` mismatch (duplicate records) | Registration stored Authentik PK (integer) as `authentik_sub`, OIDC login stored uid (hash) | Added separate `authentik_pk` column, `authentik_sub` stores uid only |
| 21 | Gitea OAuth `id_token` missing | Portal OIDC token response lacked `id_token` | Added JWT `id_token` to token endpoint |
| 22 | Gitea OAuth `redirect_uri` mismatch | `.env` missing `/callback` suffix | Registered full path `/user/oauth2/portal/callback` in `redirect_uris` |

---

## 14. Remaining Tasks

### 14.1 Immediate Action Required

- [x] Confirm DKIM `dkim=pass` (after DNS cache expiry)
- [ ] Register PTR record (SK Broadband, `211.244.144.69 → mail.namgun.or.kr`)
- [ ] Add SPF TXT record for `mail.namgun.or.kr` (resolve SPF_HELO_NONE)
- [ ] Set Authentik account passwords: tsha, nahee14, kkb

### 14.2 Completed Items

| Item | Completed Phase |
|------|----------------|
| Portal core development (Nuxt 3 + FastAPI) | Phase 3 |
| File browser (NFS integration) | Phase 4 |
| BBB video conferencing integration | Phase 5 |
| Stalwart Mail iframe integration | Phase 5 |
| Native login form | Phase 6 |
| Popup Bridge SSO | Phase 6 |
| Gitea SSO integration | Phase 6 |
| Server-side native login transition | Phase 6.5 |
| Portal OIDC Provider (Gitea SSO) | Phase 6.5 |
| Approval-based registration | Phase 7 |
| Profile/password management | Phase 7 |
| Admin user management panel | Phase 7 |
| Admin role assignment (RBAC) | Phase 7 |
| akadmin default account deactivation (ISMS-P) | Phase 7 |

### 14.3 Future Plans

| Item | Description | Expected Technology Stack |
|------|-------------|--------------------------|
| MFA Integration | Authentik MFA flow + portal UI challenge handling | Authentik Flow Executor + TOTP/WebAuthn |
| Game Panel portal integration | Manage game servers directly within the portal | Portal API + Game Panel API integration |
| CalDAV / CardDAV | Calendar/contacts synchronization | Stalwart built-in or separate server |
| Demo site | Build public demo environment at demo.namgun.or.kr | Nuxt 3 + FastAPI (read-only mode) |
| Naver Works-grade ERP | Groupware features such as organization management, approvals, and messaging | Long-term objective |

---

## 15. Technology Stack Summary

| Category | Technology |
|----------|------------|
| Identity Provider | Authentik 2025.10.4 |
| Authentication protocols | OIDC, LDAP, OAuth2 |
| Portal frontend | Nuxt 3, Vue 3, shadcn-vue |
| Portal backend | FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| Reverse proxy | Nginx (Rocky Linux 10) |
| TLS certificates | Let's Encrypt (certbot + ACME) |
| Containers (Docker) | Authentik, Portal (frontend + backend + nginx + PostgreSQL), Gitea, RustDesk Pro, Game Panel |
| Containers (Podman) | Stalwart Mail, LDAP Outpost |
| Mail server | Stalwart Mail Server (RocksDB) |
| Video conferencing | BigBlueButton 3.0 |
| File storage | NFS v4.1 (OMV, 192.168.0.100) |
| Git hosting | Gitea 1.25.4 |
| DNS | Windows Server DNS, Pi-Hole |
| Host OS | Windows (WSL2), Rocky Linux 10, Rocky Linux 9.7 |
| Virtualization | Hyper-V |

---

## 16. Security Considerations

### 16.1 Applied Security Policies

- ISMS-P compliant security headers applied across all sites
- TLS 1.2+ enforced (HSTS preload)
- Server information disclosure suppressed (`server_tokens off`, `X-Powered-By` / `Server` headers removed)
- Scanner/bot blocking rules
- DKIM + SPF + DMARC email authentication framework
- PKCE S256 authorization code protection (replay attack prevention)
- Signed session cookies (itsdangerous, httponly, secure, samesite=lax)
- Filesystem path traversal prevention (resolve + prefix verification)
- Redirect URL domain whitelist (`*.namgun.or.kr`)

### 16.2 Planned Security Enhancements

- Complete reverse DNS verification through PTR record registration
- Review and addition of CSP (Content-Security-Policy) headers
- Strengthen Authentik MFA (multi-factor authentication) policies

---

*End of document. Last updated: 2026-02-21*
