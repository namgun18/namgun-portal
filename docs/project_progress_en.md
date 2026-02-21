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
| v1.3 | 2026-02-21 | 남기완 | Added Phase 8 (BBB New Tab Meetings), Phase 9 (Gitea Portal Integration), Phase 10 (Dashboard Renewal) |
| v1.4 | 2026-02-22 | 남기완 | Added Phase 11 (Visual Refresh), Phase 12 (Infrastructure Security Hardening) |
| v1.5 | 2026-02-22 | 남기완 | Added Phase 13 (LocalStack Lab — AWS IaC Learning Environment) |

---

## 1. Project Overview

The namgun.or.kr Integrated Portal is a self-hosted, unified platform designed for household and small-organization use. It places Authentik as the central Identity Provider (IdP) and aims to consolidate diverse services — Git hosting, remote desktop, mail, video conferencing, file management, and game servers — under a single SSO (Single Sign-On) umbrella.

### 1.1 Core Objectives

- Unified SSO authentication across all services (OIDC / LDAP)
- Infrastructure aligned with ISMS-P security standards
- Data sovereignty through self-hosting
- Phased service rollout (Phase 0 through Phase 13)

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
| Phase 8 | BBB New Tab Meetings | **Complete** | — | New tab meeting join, auto-close, Greenlight blocking, Learning Analytics |
| Phase 9 | Gitea Portal Integration | **Complete** | — | Repo browsing, code viewer (syntax highlighting), issues/PR management (v0.5.0) |
| Phase 10 | Dashboard Home Renewal | **Complete** | — | 8 widgets, game server status, storage gauge, Git cache (v0.5.1) |
| Phase 11 | Visual Refresh | **Complete** | — | Color palette separation, card/button interactions, gradient hero/header, widget color icons (v0.5.2) |
| Phase 12 | Infrastructure Security Hardening | **Complete** | — | Full-server vulnerability scan, CSP headers, firewalld activation, OS security patches, test page cleanup |
| Phase 13 | LocalStack Lab — AWS IaC Learning Environment | **Complete** | — | Terraform IaC, per-user LocalStack containers, topology visualization, templates, CI/CD |

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
  │       ├─ Game Panel (backend + nginx + palworld)             │
│       └─ LocalStack Lab (per-user dynamic containers, lab-net)│
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

## 13. Phase 8: BBB New Tab Meetings (Complete)

Transitioned the BBB video conferencing integration (Phase 5) from iframe-based to new tab (popup) approach, and added Learning Analytics dashboard.

### 13.1 New Tab Meeting Join

| Item | Detail |
|------|--------|
| Method | `window.open(joinURL, '_blank')` — join meeting in a separate tab |
| logoutURL | Auto-close page (`/bbb-close`) — tab closes automatically when meeting ends |
| Greenlight blocking | Nginx blocks direct access to BBB's default web client (Greenlight) |

### 13.2 Learning Analytics

- Integrated BBB 3.0 built-in Learning Analytics Dashboard via iframe within the portal
- Displays participant statistics, speaking time, activity metrics during meetings
- Admin/host only access

### 13.3 Frontend Changes

| File | Change |
|------|--------|
| `pages/meetings.vue` | iframe → new tab meeting join + Learning Analytics iframe added |
| `pages/bbb-close.vue` | Auto-close page for meeting end (new) |

---

## 14. Phase 9: Gitea Portal Integration (Complete, v0.5.0)

Wrapped the Gitea API through the portal backend, enabling users to browse Git repositories, view source code, and manage issues/PRs directly within the portal.

### 14.1 Backend Architecture

**Module**: `backend/app/git/`

| File | Role |
|------|------|
| `gitea.py` | httpx-based async Gitea API client |
| `router.py` | FastAPI router — 13 endpoints |
| `schemas.py` | Pydantic response models |

### 14.2 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/git/repos` | Search repositories (pagination, sorting) |
| `GET /api/git/repos/{owner}/{repo}` | Repository detail (includes README) |
| `GET /api/git/repos/{owner}/{repo}/contents` | Directory listing |
| `GET /api/git/repos/{owner}/{repo}/file` | File content (Base64 decoded) |
| `GET /api/git/repos/{owner}/{repo}/branches` | Branch listing |
| `GET /api/git/repos/{owner}/{repo}/commits` | Commit history |
| `GET /api/git/repos/{owner}/{repo}/issues` | Issue listing |
| `POST /api/git/repos/{owner}/{repo}/issues` | Create issue |
| `GET /api/git/repos/{owner}/{repo}/issues/{index}` | Issue detail |
| `GET /api/git/repos/{owner}/{repo}/issues/{index}/comments` | Issue comments |
| `POST /api/git/repos/{owner}/{repo}/issues/{index}/comments` | Add comment |
| `GET /api/git/repos/{owner}/{repo}/pulls` | Pull request listing |
| `GET /api/git/repos/{owner}/{repo}/pulls/{index}` | Pull request detail |

### 14.3 Frontend Pages

| Path | Description |
|------|-------------|
| `/git` | Repository list (search, sort, language filter) |
| `/git/:owner/:repo` | Repository detail — file tree, README rendering, branches/commits/issues/PR tabs |
| `/git/:owner/:repo/blob/:path` | Code viewer — Shiki syntax highlighting, line numbers, file size display |

### 14.4 Key Technical Details

- **Shiki syntax highlighting**: Server-side rendering supporting 100+ languages
- **Markdown rendering**: `markdown-it` + code block syntax highlighting
- **Large file handling**: Files exceeding 1MB flagged as `too_large` with preview blocked
- **Base64 decoding**: Gitea API Base64-encoded file content decoded in backend

---

## 15. Phase 10: Dashboard Home Renewal (Complete, v0.5.1)

Renewed the dashboard from a basic ServiceGrid (6 service cards) to a comprehensive home screen with 8 widgets.

### 15.1 Dashboard Layout

```
┌──────────────────────────────────────────────────┐
│  Greeting (time-of-day) + Date/Time               │
├──────────────────────────────────────────────────┤
│ ● Service status bar (6 service health checks)    │
├────────────────────────┬─────────────────────────┤
│ Recent mail (2 cols)   │ Quick shortcuts (1 col)  │
│                        ├─────────────────────────┤
│                        │ Storage usage            │
├────────────────────────┼─────────────────────────┤
│ Recent Git activity    │ Active meetings          │
│ (2 cols)               ├─────────────────────────┤
│                        │ Game server status        │
└────────────────────────┴─────────────────────────┘
```

- Desktop: 3-column grid, Mobile: single-column stack
- Each widget has independent loading skeleton

### 15.2 Widget Composition

| Widget | Component | Data Source |
|--------|-----------|-------------|
| Greeting | `DashboardGreeting.vue` | useAuth (user) |
| Service Status | `DashboardServiceStatus.vue` | `/api/services/status` |
| Recent Mail | `DashboardRecentMail.vue` | `/api/mail/mailboxes` → `/api/mail/messages` |
| Recent Git Activity | `DashboardRecentGit.vue` | `/api/git/recent-commits` (new) |
| Active Meetings | `DashboardMeetings.vue` | `/api/meetings/` |
| Game Server Status | `DashboardGameServers.vue` | `/api/dashboard/game-servers` (new) |
| Storage | `DashboardStorage.vue` | `/api/files/info` |
| Quick Shortcuts | `DashboardShortcuts.vue` | Routing only |

### 15.3 New Backend APIs

#### `GET /api/git/recent-commits?limit=5`

- Fetches 3 commits each from the 5 most recently updated repos in **parallel** (`asyncio.gather`)
- Sorted by time, caches up to 20 commits
- **In-memory TTL cache**: 120 seconds — only first request hits Gitea API, subsequent calls return cache

#### `GET /api/dashboard/game-servers`

- Queries containers with `game-panel.managed=true` label via Docker socket (`/var/run/docker.sock:ro`)
- **Read-only**: cannot control containers, status query only
- Returns empty array on failure (graceful fallback)

### 15.4 Storage Capacity Display Improvements

- `shutil.disk_usage()` for instant NFS volume total/used capacity (replaced `rglob("*")` tree walk)
- Dashboard: percentage gauge bar + total capacity display
- File browser sidebar: same percentage gauge bar added
- Color coded: green below 70%, yellow 70–90%, red above 90%

### 15.5 Stalwart Health Check Fix

- Confirmed Stalwart v0.15 returns 404 for `/healthz`
- Changed to `/health/liveness` which returns 200
- Modified `backend/app/services/health.py`

### 15.6 Shared Utilities

**File**: `frontend/lib/date.ts`

| Function | Description |
|----------|-------------|
| `timeAgo(dateStr)` | Relative time display (just now, N minutes ago, N hours ago, N days ago) |
| `formatSize(bytes)` | Bytes → human-readable size (B, KB, MB, GB, TB) |

---

## 16. Phase 11: Visual Refresh (Complete, v0.5.2)

Improved the monotonous visual elements of the existing portal UI by separating the color palette, adding card/button interactions, gradient hero cards, and per-widget colored icons.

### 16.1 Color Palette Renewal

Previously, `primary`, `accent`, `secondary`, and `muted` all shared the same gray value (HSL `210 40% 96.1%`), making visual distinction impossible. This was resolved by assigning distinct values.

**Light Mode Key Changes** (`frontend/assets/css/main.css`):

| Variable | Before | After | Description |
|----------|--------|-------|-------------|
| `--primary` | `222.2 47.4% 11.2%` (near-black) | `221 83% 53%` (#3B82F6) | Vivid blue |
| `--accent` | `210 40% 96.1%` (same as primary) | `214 95% 93%` (#DBEAFE) | Light blue |
| `--ring` | `222.2 84% 4.9%` | `221 83% 53%` | Matched to primary |

**Dark Mode Key Changes**:

| Variable | Before | After |
|----------|--------|-------|
| `--primary` | `210 40% 98%` | `217 91% 60%` (#60A5FA) |
| `--accent` | `217.2 32.6% 17.5%` | `217 50% 20%` |
| `--ring` | `212.7 26.8% 83.9%` | `217 91% 60%` |

`secondary` and `muted` were kept unchanged to maintain their neutral gray role.

### 16.2 Card/Button Interactions

| Component | Changes |
|-----------|---------|
| `Card.vue` | Added `hover:shadow-md transition-shadow duration-200` — shadow transition on hover |
| `Button.vue` | `active:scale-[0.98]` press feedback, `transition-all`, default variant gets `shadow-sm hover:shadow-md` |

### 16.3 Gradient Hero Card

Converted the dashboard greeting from plain text to a gradient background card.

- **Light mode**: `bg-gradient-to-r from-blue-600 to-indigo-600` blue-to-indigo gradient with white text
- **Dark mode**: `from-blue-500/20 to-indigo-500/20` translucent gradient + `border-blue-500/30` border

### 16.4 Header Gradient Line

Added a 2px gradient line at the bottom of AppHeader:

```html
<div class="h-0.5 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-80" />
```

### 16.5 Shortcut Icon Color Backgrounds

Applied unique colored circular backgrounds to each shortcut icon.

| Shortcut | Color | Class |
|----------|-------|-------|
| Compose Mail | Blue | `bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400` |
| Start Meeting | Green | `bg-green-100 text-green-600 dark:bg-green-500/20 dark:text-green-400` |
| Upload File | Amber | `bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400` |
| Git Repos | Purple | `bg-purple-100 text-purple-600 dark:bg-purple-500/20 dark:text-purple-400` |

### 16.6 Widget Card Header Color Icons

Added colored SVG icons next to each dashboard widget card title to visually distinguish services.

| Widget | Icon | Color |
|--------|------|-------|
| Recent Mail | mail (envelope) | `text-blue-500` |
| Recent Git | git-branch | `text-purple-500` |
| Active Meetings | video | `text-green-500` |
| Game Servers | gamepad-2 | `text-orange-500` |
| Storage | hard-drive | `text-teal-500` |

### 16.7 Modified Files (14 total)

| # | File | Change |
|---|------|--------|
| 1 | `frontend/assets/css/main.css` | Color palette renewal |
| 2 | `frontend/components/ui/Card.vue` | Hover shadow transition |
| 3 | `frontend/components/ui/Button.vue` | Click feedback, shadow |
| 4 | `frontend/components/layout/AppHeader.vue` | Gradient line |
| 5 | `frontend/pages/index.vue` | Widget gap widened (gap-4 → gap-5) |
| 6 | `frontend/components/dashboard/DashboardGreeting.vue` | Gradient hero card |
| 7 | `frontend/components/dashboard/DashboardServiceStatus.vue` | Checking state pulse animation |
| 8 | `frontend/components/dashboard/DashboardShortcuts.vue` | Icon colored circular backgrounds |
| 9–13 | `Dashboard{RecentMail,RecentGit,Meetings,GameServers,Storage}.vue` | Header color icons |
| 14 | `frontend/tailwind.config.ts` | Keyframes extension (if needed) |

---

## 17. Phase 12: Infrastructure Security Hardening (Complete)

Conducted a full-server vulnerability scan and remediated all findings with zero service downtime.

### 17.1 Scan Targets

| Server | Host | Scan Items |
|--------|------|------------|
| Nginx Reverse Proxy | 192.168.0.150 | SSL/TLS, security headers, firewall, OS patches |
| Mail Server | 192.168.0.250 | SSL/TLS, SELinux, firewall, OS patches |
| Docker Host (WSL2) | 192.168.0.50 | Docker images, unused resources |
| Public Domains (6) | namgun/meet/file/game/mail/git | SSL certificates, TLS versions, security headers |

### 17.2 CSP (Content-Security-Policy) Headers Added

All sites were missing CSP headers. Site-specific policies were applied.

| Site | Key CSP Policy |
|------|---------------|
| namgun.or.kr | `frame-src https://meet.namgun.or.kr https://mail.namgun.or.kr` (allow meeting/mail iframes) |
| file.namgun.or.kr | `img-src 'self' data: blob:` (allow file preview blobs) |
| game.namgun.or.kr | Default `default-src 'self'` |
| git.namgun.or.kr | `img-src 'self' data: https:; font-src 'self' data:` (allow external images/fonts) |
| auth.namgun.or.kr | Default `default-src 'self'` |

### 17.3 Missing Security Headers Remediated

| Site | Headers Added |
|------|--------------|
| file.namgun.or.kr | `X-XSS-Protection`, `Permissions-Policy` |
| game.namgun.or.kr | `X-XSS-Protection`, `Permissions-Policy`, `server_tokens off`, `proxy_hide_header Server` |
| meet.namgun.or.kr | `Permissions-Policy` (`camera=(self), microphone=(self)` — for BBB mic/camera) |

### 17.4 Firewall (firewalld) Activation

| Server | Previous State | Action | Allowed Ports |
|--------|---------------|--------|---------------|
| Nginx (192.168.0.150) | masked (inactive) | `systemctl unmask && enable --now` | http, https, ssh, 9090 (cockpit) |
| Mail (192.168.0.250) | not loaded | `dnf install && enable --now` | ssh, smtp(25), smtps(465), submission(587), imaps(993), https(443), 8080 |

### 17.5 SELinux Status Improvement

| Server | Before | Action | Notes |
|--------|--------|--------|-------|
| Nginx (192.168.0.150) | Enforcing | Maintained | Normal |
| Mail (192.168.0.250) | Disabled | → Permissive (config changed, effective after reboot) | `/etc/selinux/config` modified |

### 17.6 OS Security Patches Applied

| Server | Patch Details |
|--------|--------------|
| Nginx (192.168.0.150) | openssl, python3-urllib3, kernel, and 90+ packages security updates |
| Mail (192.168.0.250) | kernel, python3-urllib3, and other security updates |

> **Note**: Kernel updates applied. New kernel will load upon reboot (services running without interruption).

### 17.7 Temporary Test Page Cleanup

Cleaned up all resources related to `test.namgun.or.kr:47264` that were created for firewall testing during Phase 0.

| Item | Action |
|------|--------|
| Nginx config | Deleted `test.namgun.or.kr.conf`, `test-acme.conf` |
| TLS certificate | `certbot delete --cert-name test.namgun.or.kr` |
| SELinux port | `semanage port -d -t http_port_t -p tcp 47264` |
| Web directory | Deleted `/var/www/test-page` |

### 17.8 Docker Cleanup

| Item | Action |
|------|--------|
| Unused images | `docker image prune -a` (~2GB reclaimed) |
| Build cache | `docker builder prune -a` |

---

## 18. Phase 13: LocalStack Lab — AWS IaC Learning Environment (Complete)

Integrated a LocalStack-based AWS learning environment with Terraform IaC into the portal. Each user gets an isolated LocalStack Docker container, manages AWS resources declaratively through Terraform, and visualizes the resource topology.

### 18.1 Core Design Principles

| Principle | Description |
|-----------|-------------|
| IaC First | Terraform HCL code is the primary resource management method; click-based UI is supplementary |
| User Isolation | Dedicated LocalStack Docker container per user (2GB RAM, 2 CPU limit) |
| Tenant Sharing | Environments can be shared with other users via member invitations |
| Backend Relay | All AWS/Terraform commands route through the backend; no direct frontend access |

### 18.2 Supported AWS Services (6 Beginner-Friendly)

| Service | Purpose | Key Features |
|---------|---------|--------------|
| S3 | Object Storage | Bucket CRUD, file upload/delete |
| SQS | Message Queue | Queue CRUD, send/receive messages |
| Lambda | Serverless Functions | Python function creation/invocation |
| DynamoDB | NoSQL DB | Table CRUD, item scan |
| SNS | Notifications | Topic creation, SQS subscription, message publishing |
| IAM | Access Management | User/role/policy listing (read-only) |

### 18.3 Terraform IaC Integration

| Item | Detail |
|------|--------|
| Terraform version | 1.9.8 (bundled in backend Docker image) |
| Workflow | Init → Plan → Apply → Destroy |
| provider.tf | Auto-generated per environment (LocalStack endpoint injection, read-only) |
| User files | `main.tf` provided by default, additional `.tf` files freely created/deleted |
| Plugin cache | Shared `TF_PLUGIN_CACHE_DIR=/tmp/tf-plugin-cache` |
| Execution limits | 180s timeout, `-no-color`, `TF_IN_AUTOMATION=1` |

### 18.4 Pre-defined Templates (5)

| Template | Content |
|----------|---------|
| S3 Static Website | S3 bucket + website hosting config + index.html upload |
| Lambda Function | Python Lambda function + IAM role + CloudWatch log group |
| SQS + SNS | SNS topic + SQS queue + subscription linkage |
| DynamoDB Table | DynamoDB table + GSI (Global Secondary Index) |
| Full Stack (S3 + Lambda + DynamoDB) | S3 + Lambda + DynamoDB + IAM role serverless pattern |

### 18.5 Topology Visualization

Uses cytoscape.js with dagre layout to render AWS resource relationships as a graph.

| Item | Detail |
|------|--------|
| Libraries | cytoscape 3.30, cytoscape-dagre 2.5, dagre 0.8 |
| Node colors | S3=green, Lambda=orange, SQS=purple, DynamoDB=blue, SNS=red, IAM=gray |
| Edge discovery | Lambda event source mappings, SNS subscriptions |
| Auto-refresh | 10-second polling interval (toggleable) |
| Layout | dagre hierarchical (default) |

### 18.6 CI/CD Deploy Endpoint

Provides a deploy API for Git-based CI/CD automation.

```
POST /api/lab/environments/{id}/terraform/deploy
Body: { "files": { "main.tf": "...", "network.tf": "..." } }
→ Runs init → plan → apply automatically
```

### 18.7 DB Models

| Model | Fields | Purpose |
|-------|--------|---------|
| `LabEnvironment` | id, owner_id, name, container_name, container_id, status, created_at | Environment metadata |
| `LabMember` | id, environment_id, user_id, role, invited_at | Member management (owner/member) |

### 18.8 API Endpoints (26)

| Category | Endpoint | Description |
|----------|----------|-------------|
| Environment | `GET/POST /api/lab/environments` | List / Create |
| | `GET/DELETE /api/lab/environments/{id}` | Detail / Delete |
| | `POST .../start`, `POST .../stop` | Start / Stop |
| Members | `POST/DELETE .../members` | Invite / Remove |
| Terraform | `GET/PUT .../terraform/files` | File get / save |
| | `POST .../terraform/{init,plan,apply,destroy}` | Run commands |
| | `GET .../terraform/templates` | Template list |
| | `POST .../terraform/deploy` | CI/CD deploy |
| Topology | `GET .../topology` | Resource graph |
| Resources | `GET/POST/DELETE .../resources/{service}` | CRUD |
| S3/SQS/Lambda/DynamoDB/SNS | Service-specific endpoints | Detailed operations |

### 18.9 Frontend Components

| Component | Role |
|-----------|------|
| `pages/lab.vue` | Main page (sidebar + Terraform/Resources tabs) |
| `composables/useLab.ts` | State management (environments, Terraform, topology) |
| `components/lab/LabSidebar.vue` | Environment list, create, start/stop/delete |
| `components/lab/LabTerraform.vue` | HCL code editor, file tabs, run buttons, output terminal |
| `components/lab/LabTopology.vue` | cytoscape.js topology graph |
| `components/lab/LabResourcePanel.vue` | Per-service resource CRUD (S3/SQS/Lambda/DynamoDB/SNS) |
| `components/lab/LabMemberDialog.vue` | Member invite/management dialog |

### 18.10 Docker Infrastructure Changes

| Item | Change |
|------|--------|
| Docker socket | `:ro` → `:rw` (container creation/management required) |
| Network | Added `lab-net` (LocalStack + backend communication) |
| Backend image | Added Terraform 1.9.8 + Git installation |
| Container limits | Max 5 environments per user, each 2GB RAM / 2 CPU |

### 18.11 Modified/Created Files (17)

| # | File | Type |
|---|------|------|
| 1 | `backend/Dockerfile` | Modified (Terraform + Git install) |
| 2 | `backend/app/db/models.py` | Modified (LabEnvironment + LabMember) |
| 3 | `backend/app/main.py` | Modified (lab_router registration) |
| 4 | `backend/requirements.txt` | Modified (boto3 added) |
| 5 | `docker-compose.yml` | Modified (socket rw + lab-net) |
| 6 | `frontend/package.json` | Modified (cytoscape added) |
| 7 | `frontend/components/layout/AppHeader.vue` | Modified (Lab navigation) |
| 8 | `backend/app/lab/__init__.py` | New |
| 9 | `backend/app/lab/docker_manager.py` | New (Docker lifecycle) |
| 10 | `backend/app/lab/aws_client.py` | New (boto3 wrapper) |
| 11 | `backend/app/lab/router.py` | New (API router) |
| 12 | `backend/app/lab/schemas.py` | New (Pydantic schemas) |
| 13 | `backend/app/lab/terraform_manager.py` | New (Terraform workspace) |
| 14 | `frontend/pages/lab.vue` | New (main page) |
| 15 | `frontend/composables/useLab.ts` | New (state management) |
| 16 | `frontend/components/lab/*.vue` (4) | New (UI components) |

---

## 19. Key Troubleshooting Summary

| # | Problem | Cause | Resolution |
| 23 | Git recent-commits response delay | Sequential fetching from 50 repos | Reduced to 5 repos + asyncio.gather parallel + 120s in-memory TTL cache |
| 24 | Storage capacity query delay | `rglob("*")` NFS tree walk | Switched to instant `shutil.disk_usage()` |
| 25 | Stalwart health check always failing | v0.15 returns 404 for `/healthz` | Changed URL to `/health/liveness` (returns 200) |
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

## 20. Remaining Tasks

### 20.1 Immediate Action Required

- [x] Confirm DKIM `dkim=pass` (after DNS cache expiry)
- [ ] Register PTR record (SK Broadband, `211.244.144.69 → mail.namgun.or.kr`)
- [ ] Add SPF TXT record for `mail.namgun.or.kr` (resolve SPF_HELO_NONE)
- [ ] Set Authentik account passwords: tsha, nahee14, kkb
- [ ] Reboot Nginx/Mail servers for kernel update (security patches applied, new kernel pending load)
- [ ] Transition mail server SELinux to Enforcing (verify services after reboot)

### 20.2 Completed Items

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
| BBB new tab meeting join + auto-close | Phase 8 |
| Greenlight direct access blocking | Phase 8 |
| Learning Analytics dashboard (iframe) | Phase 8 |
| Gitea API wrapping (13 endpoints) | Phase 9 |
| Repo browsing + code viewer (Shiki syntax highlighting) | Phase 9 |
| Issue/PR management | Phase 9 |
| Dashboard 8-widget renewal | Phase 10 |
| Game server status query (Docker socket) | Phase 10 |
| Storage capacity percentage gauge | Phase 10 |
| Git recent-commits in-memory cache | Phase 10 |
| Stalwart health check URL fix | Phase 10 |
| Color palette separation (primary/accent/ring) | Phase 11 |
| Card/button hover and click interactions | Phase 11 |
| Gradient hero card + header line | Phase 11 |
| Dashboard widget color icons | Phase 11 |
| CSP headers applied across all sites | Phase 12 |
| firewalld firewall activation (Nginx + Mail) | Phase 12 |
| OS security patches applied (Nginx + Mail) | Phase 12 |
| Temporary test page cleanup (test.namgun.or.kr) | Phase 12 |
| Docker unused image/cache cleanup | Phase 12 |
| LocalStack Lab AWS learning environment | Phase 13 |
| Terraform IaC integration (Init/Plan/Apply/Destroy) | Phase 13 |
| Per-user isolated LocalStack containers | Phase 13 |
| cytoscape.js topology visualization | Phase 13 |
| Pre-defined Terraform templates (5) | Phase 13 |
| CI/CD deploy endpoint | Phase 13 |
| Member invite/management (multi-tenant) | Phase 13 |

### 20.3 Future Plans

| Item | Description | Expected Technology Stack |
|------|-------------|--------------------------|
| MFA Integration | Authentik MFA flow + portal UI challenge handling | Authentik Flow Executor + TOTP/WebAuthn |
| Game Panel portal integration | Manage game servers directly within the portal (status query completed) | Portal API + Game Panel API integration |
| CalDAV / CardDAV | Calendar/contacts synchronization | Stalwart built-in or separate server |
| Demo site | Build public demo environment at demo.namgun.or.kr | Nuxt 3 + FastAPI (read-only mode) |
| Naver Works-grade ERP | Groupware features such as organization management, approvals, and messaging | Long-term objective |

---

## 21. Technology Stack Summary

| Category | Technology |
|----------|------------|
| Identity Provider | Authentik 2025.10.4 |
| Authentication protocols | OIDC, LDAP, OAuth2 |
| Portal frontend | Nuxt 3, Vue 3, shadcn-vue |
| Portal backend | FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| Reverse proxy | Nginx (Rocky Linux 10) |
| TLS certificates | Let's Encrypt (certbot + ACME) |
| IaC / Learning | Terraform 1.9.8, LocalStack 3.8, boto3, cytoscape.js |
| Containers (Docker) | Authentik, Portal (frontend + backend + nginx + PostgreSQL), Gitea, RustDesk Pro, Game Panel, LocalStack Lab |
| Containers (Podman) | Stalwart Mail, LDAP Outpost |
| Mail server | Stalwart Mail Server (RocksDB) |
| Video conferencing | BigBlueButton 3.0 |
| File storage | NFS v4.1 (OMV, 192.168.0.100) |
| Git hosting | Gitea 1.25.4 |
| DNS | Windows Server DNS, Pi-Hole |
| Host OS | Windows (WSL2), Rocky Linux 10, Rocky Linux 9.7 |
| Virtualization | Hyper-V |

---

## 22. Security Considerations

### 22.1 Applied Security Policies

- ISMS-P compliant security headers applied across all sites
- TLS 1.2+ enforced (HSTS preload)
- Server information disclosure suppressed (`server_tokens off`, `X-Powered-By` / `Server` headers removed)
- Scanner/bot blocking rules
- DKIM + SPF + DMARC email authentication framework
- PKCE S256 authorization code protection (replay attack prevention)
- Signed session cookies (itsdangerous, httponly, secure, samesite=lax)
- Filesystem path traversal prevention (resolve + prefix verification)
- Redirect URL domain whitelist (`*.namgun.or.kr`)
- CSP (Content-Security-Policy) applied across all sites (Phase 12)
- firewalld firewall activated on all servers (Phase 12)
- Regular OS security patch application (Phase 12)

### 22.2 Planned Security Enhancements

- Complete reverse DNS verification through PTR record registration
- Strengthen Authentik MFA (multi-factor authentication) policies
- Mail server SELinux Permissive → Enforcing transition (requires reboot verification)

---

*End of document. Last updated: 2026-02-22 (v1.5)*
