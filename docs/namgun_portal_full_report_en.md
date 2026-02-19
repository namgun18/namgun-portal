# namgun.or.kr Integrated Portal SSO Platform — Comprehensive Technical Document

| Field | Detail |
|-------|--------|
| Project | namgun.or.kr Integrated Portal SSO Platform |
| Author | Kiwan Nam |
| Document Version | v1.0 |
| Date | 2026-02-19 |
| Classification | Internal / Confidential |
| Target Domain | namgun.or.kr (*.namgun.or.kr) |

## Document History

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| v1.0 | 2026-02-19 | Kiwan Nam | Comprehensive technical document integrating PDD, progress reports, Phase 2 details, and Phase 5-6 details |

---

## 1. Project Overview

### 1.1 Background and Purpose

Six independent services (Gitea, Game Panel, RustDesk, FileBrowser, BigBlueButton, Mail Server) operating under the namgun.or.kr domain each use separate authentication systems, resulting in credential fragmentation. This project aims to build an SSO (Single Sign-On) integrated portal that consolidates all services under a single credential source.

The namgun.or.kr integrated portal is a self-hosted, unified platform designed for household and small-organization use. It places Authentik as the central Identity Provider (IdP) and aims to consolidate diverse services — Git hosting, remote desktop, mail, video conferencing, file management, and game servers — under a single SSO (Single Sign-On) umbrella.

### 1.2 Core Objectives

- Unified SSO authentication across all services (OIDC / LDAP)
- Infrastructure aligned with ISMS-P security standards
- Data sovereignty through self-hosting
- Phased service rollout (Phase 0 through Phase 6)

### 1.3 Project Scope

- SSO IdP (Authentik) deployment and OIDC/LDAP integration across all services
- Mail server migration (iRedMail to Stalwart Mail Server)
- File server restructuring (OMV FileBrowser to WebDAV + portal file tab)
- Integrated portal development (mail, files, calendar, contacts, blog, notifications)
- Nginx reverse proxy consolidation (TLS termination, single entry point)
- Test/production environment separation (Docker Compose Profile)

### 1.4 Hardware Environment

| Component | Specifications | Purpose |
|-----------|---------------|---------|
| Homelab Server | Dual Intel Xeon Gold 6138 / 128GB RAM | Docker Host, Hyper-V Host |
| NAS Storage | 4TB HDD (Hyper-V passthrough) | OMV VM — File Server |
| Mail Server | Dedicated host 211.244.144.69 | Stalwart Mail Server (SMTP/IMAP) |

### 1.5 Service Status and SSO Integration Analysis

| Service | Subdomain | SSO Method | Portal Integration | Priority |
|---------|-----------|------------|-------------------|----------|
| Gitea | git.namgun.or.kr | Native OIDC | External link | P1 |
| RustDesk | remote.namgun.or.kr | OIDC (Pro) | External link | P1 |
| BBB | meet.namgun.or.kr | OIDC (Greenlight 3.x) | External link | P2 |
| Stalwart Mail | mail.namgun.or.kr | OIDC + LDAP | Native (JMAP) | P2 |
| OMV/FileServer | file.namgun.or.kr | Proxy Auth | Native (WebDAV) | P2 |
| Game Panel | game.namgun.or.kr | N/A (Discord OAuth2) | External link | - |

### 1.6 Phase Progress Summary

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| Phase 0 | Infrastructure Preparation | **Complete** | Authentik, DNS, Nginx, TLS |
| Phase 1 | SSO PoC | **Complete** | Gitea OIDC, RustDesk OIDC |
| Phase 2 | Mail Server Migration | **Complete** | Stalwart + LDAP + OIDC |
| Phase 3 | Portal Core Development | **Complete** | Nuxt 3 + FastAPI + PostgreSQL |
| Phase 4 | File Browser | **Complete** | NFS mount + in-portal file management UI |
| Phase 5 | Service Enhancements & Mail/Conferencing Integration | **Complete** | BBB, mail iframe, caching, navigation |
| Phase 6 | Native Login & SSO Integration | **Complete** | Native login form, Popup Bridge, Gitea SSO |

---

## 2. Infrastructure Topology

### 2.1 Physical / Logical Layout

```
Internet
  |
  +- 211.244.144.47 (Public IP, main services)
  |    +-- Port forwarding -> 192.168.0.150 (Nginx Reverse Proxy)
  |
  +- 211.244.144.69 (Public IP, MX record)
  |    +-- Direct connection -> 192.168.0.250 (Stalwart Mail)
  |
  +-------------------- LAN 192.168.0.0/24 --------------------+
  |                                                              |
  |  [192.168.0.50] Windows Host (Dual Xeon Gold 6138, 128GB)   |
  |    +-- WSL2 / Docker                                         |
  |       +-- Authentik (server + worker + PostgreSQL 16)        |
  |       +-- Portal Stack                                       |
  |       |    +-- portal-frontend (Nuxt 3 SSR, :3000)          |
  |       |    +-- portal-backend (FastAPI, :8000)               |
  |       |    +-- portal-db (PostgreSQL 16, named volume)       |
  |       |    +-- portal-nginx (internal reverse proxy, :8080)  |
  |       +-- Gitea 1.25.4                                       |
  |       +-- RustDesk Pro (hbbs + hbbr)                         |
  |       +-- Game Panel (backend + nginx + palworld)            |
  |                                                              |
  |  [192.168.0.100] OMV (OpenMediaVault) -- NAS                 |
  |    +-- NFSv4 server (/export/root, fsid=0)                   |
  |       +-- /portal -> Docker NFS volume (/storage)            |
  |                                                              |
  |  [192.168.0.150] Hyper-V VM -- Nginx (Rocky Linux 10)        |
  |    +-- Central reverse proxy, TLS Termination                |
  |                                                              |
  |  [192.168.0.249] BigBlueButton 3.0 (Video Conferencing)      |
  |    +-- BBB API (SHA256 checksum authentication)              |
  |                                                              |
  |  [192.168.0.250] Hyper-V VM -- Mail (Rocky Linux 9.7)        |
  |    +-- Podman (rootless)                                     |
  |       +-- Stalwart Mail Server (network_mode: host)          |
  |       +-- Authentik LDAP Outpost (sidecar)                   |
  |                                                              |
  |  [192.168.0.251] Pi-Hole DNS (Internal primary DNS)          |
  |                                                              |
  +--------------------------------------------------------------+
```

### 2.2 Service Status Summary (As of Phase 6 Completion)

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

### 2.3 Credential Source Topology

Authentik serves as the Single Source of Truth for credentials, providing authentication protocols tailored to each service's characteristics.

```
[Authentik (Single Credential Source)]
  +-- OIDC -> Gitea, RustDesk, BBB, Stalwart (web), Portal
  +-- LDAP Outpost -> Stalwart (IMAP/SMTP, for mail clients)
  +-- Proxy Auth -> OMV WebDAV
  +-- X Game Panel (independent, Discord OAuth2)
```

### 2.4 Network Architecture

All external traffic enters through the Nginx reverse proxy as a single entry point. Internal service endpoints are never exposed externally.

```
[Internet]
    |
    v
[Nginx Reverse Proxy] (:443 TLS termination, single entry point)
    |
    +-- namgun.or.kr
    |     +-- /          -> Nuxt 3 Frontend (internal)
    |     +-- /api/*     -> FastAPI Gateway (internal)
    |           +-- /api/mail/*     -> Stalwart JMAP
    |           +-- /api/files/*    -> OMV WebDAV
    |           +-- /api/calendar/* -> Stalwart CalDAV
    |           +-- /api/contacts/* -> Stalwart CardDAV
    |           +-- /api/blog/*     -> PostgreSQL
    |           +-- /api/notify/*   -> Unified notifications
    |
    +-- auth.namgun.or.kr   -> Authentik (IdP)
    +-- git.namgun.or.kr    -> Gitea
    +-- remote.namgun.or.kr -> RustDesk Pro
    +-- meet.namgun.or.kr   -> BBB (Greenlight)
    +-- game.namgun.or.kr   -> Game Panel
    +-- dev.namgun.or.kr    -> Test environment
    |
    +-- mail.namgun.or.kr (:25/465/587/993)
          -> Stalwart (211.244.144.69)
          * SMTP/IMAP direct, only web UI via reverse proxy
```

### 2.5 Backend Proxy Pattern (Endpoint Concealment)

The FastAPI backend acts as a reverse proxy, ensuring that actual service endpoints are never exposed to the browser. This is an unacceptable design principle to compromise on from a security engineering perspective.

| API Path | Internal Target | Authentication |
|----------|----------------|----------------|
| /api/mail/* | Stalwart JMAP (192.168.x.x) | SSO token |
| /api/files/* | OMV WebDAV (192.168.x.x) | SSO token |
| /api/calendar/* | Stalwart CalDAV (internal) | SSO token |
| /api/contacts/* | Stalwart CardDAV (internal) | SSO token |
| /api/blog/* | PostgreSQL (internal) | SSO token |
| /api/notify/* | Unified notifications (internal) | SSO token |

---

## 3. Technology Stack

### 3.1 Frontend: Nuxt 3 (Vue.js)

**Selection rationale:**

- **React Server Components (RSC) vulnerability avoidance**: CVE-2025-55182 (React2Shell, CVSS 10.0) — a pre-authentication RCE vulnerability disclosed in December 2025 that led to large-scale real-world attacks. Vue.js/Nuxt lacks the RSC architecture and is structurally immune to this class of vulnerability
- **Maintainability for non-developers**: Vue template syntax is nearly identical to HTML, making it intuitively understandable for infrastructure engineers
- **SSR/SSG support**: Enables mixed blog SSG and dashboard SSR usage
- **Public/enterprise SI standard**: Vue.js is adopted as the GS certification standard in the domestic Korean enterprise SI market

### 3.2 Backend: FastAPI (Python)

**Selection rationale:**

- Python-based, leveraging synergy with existing automation tool development experience
- Automatic Swagger UI generation minimizes API documentation burden
- Native async support, suitable for concurrent external service API calls
- Straightforward implementation of JMAP, WebDAV, CalDAV, and CardDAV protocol clients

### 3.3 IdP: Authentik

**Selection rationale:**

- Provides both OIDC Provider and LDAP Outpost simultaneously (single deployment)
- Docker-native (PostgreSQL + Redis)
- Native Forward Auth / Proxy Auth support
- Resource usage: ~2-3GB RAM (adequate for the current environment)
- Rejected alternatives: Keycloak (Java, 3-4GB+ RAM, excessive for homelab), Authelia (OIDC Provider immature)

### 3.4 Mail Server: Stalwart Mail Server

Replacing the iRedMail community edition with Stalwart Mail Server (AGPL-3.0).

- OIDC client functionality open-sourced since v0.11.5 (Enterprise edition not required)
- Native LDAP backend support (Authentik LDAP Outpost integration)
- All-in-one Rust binary: SMTP, IMAP, POP3, JMAP, CalDAV, CardDAV, WebDAV, Sieve
- Built-in web UI + JMAP API (enables portal mail tab implementation, Roundcube not required)
- Official Docker image: `stalwartlabs/stalwart:latest`

### 3.5 Technology Stack Summary

| Category | Technology | License |
|----------|------------|---------|
| Identity Provider | Authentik 2025.10.4 | MIT |
| Authentication protocols | OIDC, LDAP, OAuth2 | — |
| Frontend | Nuxt 3 + Vue 3 + TailwindCSS + shadcn-vue | MIT |
| Backend | FastAPI + Python 3.12+ + SQLAlchemy 2.0 (async) + asyncpg | MIT |
| Mail server | Stalwart Mail Server (RocksDB) | AGPL-3.0 |
| Database | PostgreSQL 16 | PostgreSQL License |
| Blog rendering | @nuxt/content (MDX) | MIT |
| Reverse proxy | Nginx (Rocky Linux 10) | BSD-2-Clause |
| Containers (Docker) | Authentik, Portal (frontend + backend + nginx + PostgreSQL), Gitea, RustDesk Pro, Game Panel | Apache-2.0 |
| Containers (Podman) | Stalwart Mail, LDAP Outpost | — |
| File server | OpenMediaVault + WebDAV, NFS v4.1 | GPL-3.0 |
| Remote desktop | RustDesk Pro | Custom (Pro) |
| Git server | Gitea 1.25.4 | MIT |
| Video conferencing | BigBlueButton 3.0 + Greenlight 3.x | LGPL-3.0 |
| TLS certificates | Let's Encrypt (certbot + ACME) | — |
| DNS | Windows Server DNS, Pi-Hole | — |
| Host OS | Windows (WSL2), Rocky Linux 10, Rocky Linux 9.7 | — |
| Virtualization | Hyper-V | — |

---

## 4. Security Design

### 4.1 Rationale for Excluding React

CVE-2025-55182 (React2Shell) is a pre-authentication RCE vulnerability with a CVSS score of 10.0, enabling arbitrary code execution on the server via a single HTTP request. Within hours of its public disclosure in December 2025, Chinese state-sponsored hacking groups began exploiting it. Subsequently, three additional CVEs were discovered (CVE-2025-55183, CVE-2025-55184, CVE-2025-67779).

In a personal hosting environment without enterprise-grade protections such as a WAF or dedicated security teams, the best defense is to structurally eliminate the attack surface. Vue.js/Nuxt lacks the RSC architecture, making identical vulnerability types structurally impossible.

### 4.2 Authentication / Authorization Security

- Authentik OIDC: Authorization Code Flow with PKCE
- Authentik LDAP Outpost: Password authentication for mail clients (for clients that do not support OAUTHBEARER)
- Nginx Forward Auth: Delegates OMV WebDAV access authentication to Authentik
- SSO token-based API authentication: Authentication middleware applied to all /api/* requests
- PKCE S256 authorization code protection (replay attack prevention)
- Signed session cookies (itsdangerous, httponly, secure, samesite=lax)
- Redirect URL domain whitelist (`*.namgun.or.kr`)

### 4.3 Network Security

- TLS termination: Single TLS termination at Nginx; internal communication in plaintext (Docker network)
- Endpoint concealment: All internal service IPs/ports never exposed externally
- OMV firewall: Only FastAPI backend IP allowed (defense in depth)
- Nginx configuration rules: Deprecated directives not used (`ssl on`, `listen ssl http2` replaced with `listen 443 ssl;` + `http2 on;`)

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

### 4.4 Data Security

- Authentik DB regular backup (SPOF mitigation)
- Local admin account fallback (emergency access in case of authentication server failure)
- Stalwart migration: Integrity verification after imapsync dry-run
- DNS SPF/DKIM/DMARC reconfiguration: Stalwart DKIM key regeneration
- Filesystem path traversal prevention (resolve + prefix verification)
- DKIM + SPF + DMARC email authentication framework

### 4.5 Applied Security Policies Summary

- ISMS-P compliant security headers applied across all sites
- TLS 1.2+ enforced (HSTS preload)
- Server information disclosure suppressed (`server_tokens off`, `X-Powered-By` / `Server` headers removed)
- Scanner/bot blocking rules
- DKIM + SPF + DMARC email authentication framework
- PKCE S256 authorization code protection (replay attack prevention)
- Signed session cookies (itsdangerous, httponly, secure, samesite=lax)
- Filesystem path traversal prevention (resolve + prefix verification)
- Redirect URL domain whitelist (`*.namgun.or.kr`)

---

## 5. Phase 0: Infrastructure Preparation (Complete)

### 5.1 Authentik SSO (Identity Provider)

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

### 5.2 DNS Configuration

- **Management tool**: Windows Server DNS
- **Internal DNS**: Pi-Hole (192.168.0.251)
- **Registered records**:
  - A records: All subdomains (auth, git, game, mail, meet, remote, namgun.or.kr)
  - MX record: mail.namgun.or.kr
  - TXT records: SPF, DKIM, DMARC

#### Windows Server DNS Limitation

> When a TXT record exceeds 255 characters, it must be split into multiple strings within a single record. The DKIM public key (RSA-2048) is a representative example.

### 5.3 Nginx Reverse Proxy (192.168.0.150)

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

### 5.4 TLS Certificates

| Target | Issuance Method | Renewal Method |
|--------|----------------|----------------|
| Nginx sites (*.namgun.or.kr) | Let's Encrypt certbot | webroot (/var/www/certbot), automatic renewal |
| Stalwart Mail Server | Let's Encrypt ACME | Stalwart built-in ACME automatic renewal (separate from Nginx) |

---

## 6. Phase 1: SSO PoC (Complete)

### 6.1 Gitea SSO Integration

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

### 6.2 RustDesk Pro SSO Integration

- **Access URL**: https://remote.namgun.or.kr
- **Components**: hbbs (signaling server) + hbbr (relay server)
- **Authentication method**: OIDC via Authentik

---

## 7. Phase 2: Mail Server Migration (Complete)

The legacy mail server based on iRedMail (Postfix + Dovecot) was migrated to Stalwart Mail Server, and authentication integration via Authentik LDAP was completed.

### 7.1 Migration Overview

#### Before

| Item | Details |
|------|---------|
| MTA | Postfix 3.5.25 |
| MDA | Dovecot 2.3.16 |
| Spam filter | Amavis + SpamAssassin + ClamAV |
| Webmail | Roundcube |
| Authentication | PostgreSQL (iRedMail native) |
| Account count | 9 |
| Mail storage | 66MB (Maildir) |

#### After

| Item | Details |
|------|---------|
| Mail server | Stalwart Mail Server (latest, Podman) |
| Storage | RocksDB (built-in) |
| Authentication | Authentik LDAP Outpost (sidecar) |
| Web UI | Stalwart built-in Web Admin / JMAP |
| Protocols | SMTP(25), SMTPS(465), Submission(587), IMAPS(993), ManageSieve(4190) |
| Container runtime | Podman (rootless, network_mode: host) |

### 7.2 Architecture

#### 7.2.1 Container Layout

```
192.168.0.250 (Mail Server VM)
+-- stalwart (Podman, network_mode: host)
|   +-- SMTP :25, :465, :587
|   +-- IMAP :993
|   +-- Web Admin :8080 (-> Nginx proxy)
|   +-- HTTPS :443 (internal API)
|   +-- ManageSieve :4190
|
+-- stalwart-ldap (Podman, network_mode: host)
    +-- LDAP :3389
    +-- LDAPS :6636
    +-- -> Authentik (auth.namgun.or.kr) WebSocket connection
```

#### 7.2.2 Authentication Flow

```
[Mail Client] -> IMAP/SMTP authentication
    -> [Stalwart] -> LDAP lookup (127.0.0.1:3389)
        -> [LDAP Outpost sidecar] -> Authentik API
            -> Authentication result returned

[Web Browser] -> https://mail.namgun.or.kr
    -> [Nginx 192.168.0.150] -> Stalwart :8080
```

#### 7.2.3 DKIM Signing Flow

```
[Authenticated User] -> SMTP Submission (:465/:587)
    -> [Stalwart] -> DKIM signing (rsa-sha256, selector=default)
        -> Outbound delivery to external MTA
```

### 7.3 Step-by-Step Progress

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

#### Step 4: Nginx Reverse Proxy Configuration

- Configuration file: `mail.namgun.or.kr.conf` (192.168.0.150)
- HTTPS 443 -> Stalwart 8080 (Web Admin / JMAP)
- SMTP (25, 465, 587) / IMAP (993) are not proxied (direct connection)
- ISMS-P security headers applied

### 7.4 Key Configuration

#### 7.4.1 Stalwart LDAP Directory

```toml
directory.ldap.type = "ldap"
directory.ldap.url = "ldap://127.0.0.1:3389"
directory.ldap.base-dn = "ou=users,dc=ldap,dc=goauthentik,dc=io"
directory.ldap.bind.dn = "cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io"
directory.ldap.bind.auth.method = "lookup"
directory.ldap.filter.name = "(&(objectClass=user)(|(uid=?)(cn=?)(mail=?)))"
directory.ldap.filter.email = "(&(objectClass=user)(mail=?))"
storage.directory = "ldap"
```

#### 7.4.2 DKIM Signing (config.toml)

```toml
[signature."rsa-namgun.or.kr"]
algorithm = "rsa-sha256"
domain = "namgun.or.kr"
selector = "default"
canonicalization = "relaxed/relaxed"
headers = ["From", "To", "Date", "Subject", "Message-ID"]
report = false
private-key = """
-----BEGIN RSA PRIVATE KEY-----
(2048-bit RSA, DNS TXT: default._domainkey.namgun.or.kr)
-----END RSA PRIVATE KEY-----
"""
```

#### 7.4.3 Podman Compose (192.168.0.250)

```yaml
services:
  stalwart:
    image: docker.io/stalwartlabs/stalwart:latest
    container_name: stalwart
    restart: unless-stopped
    network_mode: host
    volumes:
      - stalwart-data:/opt/stalwart
      - /etc/letsencrypt:/etc/letsencrypt:ro
    extra_hosts:
      - "auth.namgun.or.kr:192.168.0.150"

  ldap-outpost:
    image: ghcr.io/goauthentik/ldap:2025.10
    container_name: stalwart-ldap
    restart: unless-stopped
    network_mode: host
    environment:
      AUTHENTIK_HOST: https://auth.namgun.or.kr
      AUTHENTIK_INSECURE: "false"
      AUTHENTIK_TOKEN: <outpost-token>
    extra_hosts:
      - "auth.namgun.or.kr:192.168.0.150"

volumes:
  stalwart-data:
    name: stalwart-data
```

### 7.5 DNS Records

| Record | Type | Value |
|--------|------|-------|
| namgun.or.kr | MX | mail.namgun.or.kr (priority 10) |
| mail.namgun.or.kr | A | 211.244.144.69 |
| namgun.or.kr | TXT (SPF) | `v=spf1 ip4:211.244.144.69 mx ~all` |
| _dmarc.namgun.or.kr | TXT | `v=DMARC1; p=quarantine; rua=mailto:postmaster@namgun.or.kr` |
| default._domainkey.namgun.or.kr | TXT | `v=DKIM1; k=rsa; p=<public-key>` (must be split into 2 strings at 255 chars) |

> **Windows Server DNS note**: TXT records exceeding 255 characters must be split into two strings for registration.

### 7.6 Account Mapping

A total of 9 accounts were migrated.

**Personal Accounts (5) — LDAP via Authentik**

| iRedMail Account | Authentik User | Type | Notes |
|------------------|---------------|------|-------|
| namgun18@namgun.or.kr | namgun18 (LDAP) | Personal | Authentik username changed from `namgun` to `namgun18` (LDAP cn matching) |
| tsha@namgun.or.kr | tsha (LDAP) | Personal | Password setup pending |
| nahee14@namgun.or.kr | nahee14 (LDAP) | Personal | Password setup pending |
| kkb@namgun.or.kr | kkb (LDAP) | Personal | Password setup pending |
| administrator@namgun.or.kr | administrator (LDAP) | Personal | — |

**Service Accounts (4) — Stalwart Internal Authentication**

| Account | Email | Purpose |
|---------|-------|---------|
| system | system@namgun.or.kr | System mail |
| postmaster | postmaster@namgun.or.kr | Postmaster |
| git | git@namgun.or.kr | Gitea notification mail |
| noreply | noreply@namgun.or.kr | Automated outbound only |

**Mail data migration**: Transferred from Dovecot to Stalwart using imapsync

### 7.7 Security Configuration (ISMS-P)

| Item | Configuration |
|------|--------------|
| TLS minimum version | 1.2 |
| IMAP | Implicit TLS only (:993), plaintext 143 recommended disabled |
| SMTP | STARTTLS (:587), Implicit TLS (:465) |
| POP3 | Recommended disabled |
| DKIM | rsa-sha256, 2048-bit |
| SPF | `v=spf1 ip4:211.244.144.69 mx ~all` |
| DMARC | `p=quarantine` |
| Nginx security headers | HSTS, X-Frame-Options, X-Content-Type-Options, etc. |
| Web Admin access | Via Nginx proxy, internal IP restriction recommended |

### 7.8 Verification Results

| Test Item | Result | Notes |
|-----------|--------|-------|
| SMTP authentication | **Passed** | namgun18@namgun.or.kr via LDAP |
| IMAP authentication | **Passed** | — |
| Outbound delivery | **Passed** | Confirmed receipt at Gmail, amitl.co.kr |
| Inbound delivery | **Passed** | — |
| Samsung Email app | **Passed** | IMAP 993 SSL, SMTP 465 SSL |
| DKIM signing | **Operational** | Message size increase from 1292 to 4313 bytes confirmed |
| DKIM DNS verification | **Pending confirmation** | Public key update complete; need to confirm dkim=pass after DNS cache expiry |
| SPF | **Passed** | — |
| DMARC | **Passed** | Based on SPF alignment |

### 7.9 Removed Packages

```
postfix, postfix-pcre, postfix-pgsql
dovecot, dovecot-pgsql, dovecot-pigeonhole
amavis, perl-Amavis
clamav-filesystem
spamassassin
php-fpm
nginx (disabled)
```

Legacy mail data at `/var/vmail/` (72MB) preserved.

---

## 8. Phase 3: Portal Core Development (Complete)

The portal web application core was developed using Nuxt 3 + FastAPI + PostgreSQL and deployed to production in a Docker Compose environment.

### 8.1 Technology Stack and Architecture

| Category | Technology |
|----------|------------|
| Frontend | Nuxt 3 (Vue 3, SSR), shadcn-vue (UI components) |
| Backend | FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| Database | PostgreSQL 16 (Alpine) |
| Authentication | OIDC via Authentik (PKCE S256) |
| Session management | itsdangerous (URLSafeTimedSerializer), signed cookies |
| Containers | Docker Compose, `--profile prod` deployment |

### 8.2 Docker Compose Configuration

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

### 8.3 Test / Production Environment Separation

Docker Compose Profiles are used to separate environments by port/network on the same host. No separate VM is required.

| Item | Production | Test |
|------|-----------|------|
| Domain | namgun.or.kr | dev.namgun.or.kr |
| Frontend port | :443 | :8443 |
| Backend port | :8000 (internal) | :8001 (internal) |
| Database | PostgreSQL (prod schema) | PostgreSQL (dev schema) |
| Deploy command | `docker compose --profile prod up -d` | `docker compose --profile dev up -d` |
| Additional resources | N/A | ~500MB RAM |

Operational flow: Code change -> Test on dev.namgun.or.kr -> Verify -> Prod build/deploy. Automation via Gitea Actions CI/CD pipeline is planned after GitOps training begins.

### 8.4 OIDC Authentication (Authentik)

- **Authentication flow**: Authorization Code + PKCE (S256)
- **Endpoints**:
  - Authorization: `https://auth.namgun.or.kr/application/o/authorize/`
  - Token: `https://auth.namgun.or.kr/application/o/token/`
  - Userinfo: `https://auth.namgun.or.kr/application/o/userinfo/`
  - End Session: `https://auth.namgun.or.kr/application/o/portal/end-session/`
- **Redirect URI**: `https://namgun.or.kr/api/auth/callback`
- **PKCE storage**: `portal_pkce` cookie (httponly, secure, samesite=lax, max_age=600)
- **Session cookie**: `portal_session` (httponly, secure, samesite=lax, 7-day validity)

### 8.5 User Model (User)

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

### 8.6 Dashboard Service Monitoring

- **Number of services**: 6 (Authentik, Gitea, RustDesk, Game Panel, Stalwart Mail, BBB)
- **Health check interval**: 60 seconds (background task)
- **Check method**: HTTP GET (status code < 400 -> ok) or TCP port check (RustDesk)
- **In-memory cache**: `_cache` list, queried by frontend at `/api/services/`
- **ServiceCard**: Service name, status badge (ok/down/checking), response time (ms), external URL link

### 8.7 NFS Mount (File Storage)

- **NFS server**: OMV (192.168.0.100), `/export/root` (fsid=0)
- **Docker NFS volume**: `portal-storage` -> `/storage` inside containers
- **Mount options**: `addr=192.168.0.100,nfsvers=4,rw,hard,noatime,nolock`
- **Client device**: `:/portal` (because fsid=0 is bound to `/export/root`)

---

## 9. Phase 4: File Browser (Complete)

A file browser was developed that enables web-based management of NFS-mounted storage from within the portal.

### 9.1 NFS Integration Details

| Item | Details |
|------|---------|
| NFS server | OMV (192.168.0.100) |
| Export path | `/export/root` (fsid=0) |
| Docker volume device | `:/portal` |
| NFS version | v4.1 (WSL2 kernel does not support v4.2; v4.1 is used instead) |
| Mount options | `nfsvers=4,rw,hard,noatime,nolock` |
| WSL2 package requirement | `nfs-common` must be installed |

### 9.2 Filesystem Structure

```
/storage/
├── shared/          <- Shared folder (all users can read; only admins can write)
└── users/
    └── {user_id}/   <- Personal folder (isolated per user)
```

- **Virtual path scheme**: `my/...` -> `/storage/users/{user_id}/...`, `shared/...` -> `/storage/shared/...`
- **Admin path**: `users/...` -> `/storage/users/...` (browse all user directories)
- **Path security**: Path traversal prevention via `resolve()` followed by base path prefix verification

### 9.3 File Operations (API)

| Operation | Endpoint | Notes |
|-----------|----------|-------|
| Directory listing | GET `/api/files/list` | Virtual-path based |
| File upload | POST `/api/files/upload` | multipart/form-data, max 1024MB |
| File download | GET `/api/files/download` | StreamingResponse |
| File/folder deletion | DELETE `/api/files/delete` | Admin-only for shared; unrestricted in own folder |
| Rename | POST `/api/files/rename` | — |
| Move/copy | POST `/api/files/move` | Copy supported via `copy` parameter |
| Create folder | POST `/api/files/mkdir` | — |

### 9.4 Frontend UI

- **Breadcrumb navigation**: Displays the current path hierarchically; click to navigate
- **File grid/list view**: Filename, size, modification date, MIME type
- **Sidebar**: Root navigation for my / shared / users (admin)
- **Command bar**: Toolbar for upload, new folder, delete, rename, etc.
- **Context menu**: Right-click menu (download, rename, move, delete)
- **Upload modal**: Drag-and-drop or file selection
- **Preview modal**: Image/text file preview
- **Share link modal**: External share link generation (ShareLink model, expiration/download limits)

---

## 10. Phase 5: Service Enhancements & Mail/Conferencing Integration (Complete)

File listing cache, BBB video conferencing integration, Stalwart Mail iframe integration, service card improvements, and navigation additions were completed.

### 10.1 File Browser Performance Improvements

#### 10.1.1 In-Memory TTL Cache

In the NFS v4.1 environment, each directory listing request triggered `iterdir()` + `stat()` system calls, resulting in observed latencies of several hundred milliseconds. An in-memory TTL cache was introduced to address this.

**Implementation location**: `backend/app/files/service.py`

```python
# TTL cache: {real_path_str: (timestamp, [FileItem, ...])}
_dir_cache: dict[str, tuple[float, list[FileItem]]] = {}
_CACHE_TTL = 30  # seconds

# TTL cache for directory sizes: {path_str: (timestamp, size_bytes)}
_size_cache: dict[str, tuple[float, int]] = {}
_SIZE_CACHE_TTL = 60  # seconds
```

| Item | Value | Description |
|------|-------|-------------|
| `_dir_cache` | TTL 30s | Directory file listing cache |
| `_size_cache` | TTL 60s | Directory size calculation cache |
| Cache key | `str(real_path.resolve())` | Absolute path string |
| Time source | `time.monotonic()` | Unaffected by system clock changes |

**Cache lookup logic** (`list_directory()`):

```python
def list_directory(real_path: Path, virtual_prefix: str) -> list[FileItem]:
    if not real_path.is_dir():
        return []

    cache_key = str(real_path.resolve())
    now = time.monotonic()

    cached = _dir_cache.get(cache_key)
    if cached is not None:
        ts, items = cached
        if now - ts < _CACHE_TTL:
            return items

    items = _scan_directory(real_path, virtual_prefix)
    _dir_cache[cache_key] = (now, items)
    return items
```

#### 10.1.2 Cache Invalidation

After every write operation (upload, delete, rename, move, mkdir), `invalidate_cache()` must be called to immediately remove the cache entry for the affected directory.

```python
def invalidate_cache(real_path: Path) -> None:
    key = str(real_path.resolve())
    _dir_cache.pop(key, None)
    _size_cache.clear()
```

**Call sites** (`backend/app/files/router.py`):

| Operation | Invalidation Target |
|-----------|---------------------|
| `upload_file()` | `fs.invalidate_cache(real_dir)` |
| `delete_file()` | `fs.invalidate_cache(real.parent)` |
| `rename_file()` | `fs.invalidate_cache(real.parent)` |
| `move_file()` | `fs.invalidate_cache(src_real.parent)` + `fs.invalidate_cache(dst_real)` |
| `mkdir()` | `fs.invalidate_cache(parent_real)` |

> **Note**: `_size_cache` is cleared entirely on write operations (`_size_cache.clear()`) because parent directories may be affected.

#### 10.1.3 Async Wrapping

Since NFS I/O is a blocking call, it was wrapped with `asyncio.to_thread()` to avoid blocking FastAPI's async event loop.

```python
# backend/app/files/router.py
items = await asyncio.to_thread(fs.list_directory, real, vp)
```

The same wrapping is applied to storage information queries:

```python
personal, shared = await asyncio.gather(
    asyncio.to_thread(fs.get_dir_size, personal_path),
    asyncio.to_thread(fs.get_dir_size, shared_path),
)
```

#### 10.1.4 NFS Environment Optimization Results

| Item | Before | After |
|------|--------|-------|
| Directory listing response | 200~500ms (NFS I/O) | <5ms (cache hit) |
| Event loop blocking | Occurred | None (`to_thread`) |
| Concurrent request handling | Blocked during I/O wait | Non-blocking parallel processing |
| Cache consistency | N/A | Immediate invalidation on write |

### 10.2 Dashboard Service Card Changes

#### 10.2.1 SERVICE_DEFS Changes

**Implementation location**: `backend/app/services/health.py`

```python
SERVICE_DEFS = [
    {
        "name": "Authentik",
        "health_url": "http://192.168.0.50:9000/-/health/ready/",
        "external_url": "https://auth.namgun.or.kr",
        "internal_only": False,
    },
    {
        "name": "Gitea",
        "health_url": "http://192.168.0.50:3000/api/v1/version",
        "external_url": "https://git.namgun.or.kr/user/oauth2/authentik",
        "internal_only": False,
    },
    {
        "name": "RustDesk",
        "health_tcp": "192.168.0.50:21114",
        "external_url": "https://remote.namgun.or.kr",
        "internal_only": False,
    },
    {
        "name": "Game Panel",
        "health_url": "http://192.168.0.50:8090/api/health",
        "external_url": "https://game.namgun.or.kr",
        "internal_only": False,
    },
    {
        "name": "Stalwart Mail",
        "health_url": "http://192.168.0.250:8080/healthz",
        "external_url": "https://mail.namgun.or.kr",
        "internal_only": True,
    },
    {
        "name": "Video Conference (BBB)",
        "health_url": "https://meet.namgun.or.kr/bigbluebutton/api",
        "external_url": None,
        "internal_only": True,
    },
]
```

#### 10.2.2 Change Details

| Service | Before | After | Reason |
|---------|--------|-------|--------|
| Stalwart Mail | `internal_only: False` | `internal_only: True` | Integrated within portal via iframe (`/mail` page) |
| Pi-Hole | Present in SERVICE_DEFS | **Removed** | Internal DNS server; dashboard exposure unnecessary |
| RustDesk | `health_url` (HTTP) | `health_tcp: "192.168.0.50:21114"` | RustDesk API server does not provide an HTTP health endpoint |
| Video Conference (BBB) | Not present | **Added** | BigBlueButton 3.0 integration |
| Gitea | `external_url` generic URL | OAuth direct trigger URL | SSO integration (Phase 6) |

#### 10.2.3 TCP Health Check Implementation

For RustDesk, the health check is performed by attempting a TCP port connection instead of an HTTP endpoint.

```python
async def check_service(svc: dict) -> ServiceStatus:
    try:
        start = time.monotonic()
        if "health_tcp" in svc:
            host, port = svc["health_tcp"].rsplit(":", 1)
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, int(port)), timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            elapsed_ms = int((time.monotonic() - start) * 1000)
            status = "ok"
        else:
            # HTTP check ...
```

#### 10.2.4 ServiceStatus Schema

```python
class ServiceStatus(BaseModel):
    name: str
    url: str | None       # external URL (None for internal_only display)
    status: str           # "ok" | "down" | "checking"
    response_ms: int | None
    internal_only: bool
```

Services with `internal_only: True` are linked to internal portal pages on the dashboard instead of external URLs.

### 10.3 BigBlueButton Video Conference Integration

#### 10.3.1 Architecture

```
[Portal Frontend] -> /api/meetings/*
    -> [FastAPI Backend] -> BBB API (SHA256 checksum)
        -> [BBB 3.0 Server] 192.168.0.249 (meet.namgun.or.kr)
```

#### 10.3.2 BBB API Client

**Implementation location**: `backend/app/meetings/bbb.py`

**SHA256 Checksum Generation:**

The BBB API requires a `checksum` parameter on every request. The checksum is generated using the formula `SHA256(method + queryString + sharedSecret)`.

```python
def _checksum(method: str, query_string: str) -> str:
    raw = f"{method}{query_string}{settings.bbb_secret}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

**URL Construction:**

```python
def _build_url(method: str, params: dict | None = None) -> str:
    params = params or {}
    params = {k: v for k, v in params.items() if v is not None}
    query_string = urlencode(params)
    checksum = _checksum(method, query_string)
    if query_string:
        query_string += f"&checksum={checksum}"
    else:
        query_string = f"checksum={checksum}"
    return f"{settings.bbb_url}/{method}?{query_string}"
```

**XML Parsing:**

The BBB API returns XML responses, which are recursively converted to dictionaries. When the same tag appears multiple times (e.g., multiple `<attendee>` elements), it is automatically converted to a list.

```python
def _xml_to_dict(element: ET.Element) -> dict | str:
    result = {}
    for child in element:
        tag = child.tag
        if len(child) > 0:
            value = _xml_to_dict(child)
        else:
            value = child.text or ""
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(value)
        else:
            result[tag] = value
    return result if result else (element.text or "")
```

**API Methods:**

| Function | BBB API | Description |
|----------|---------|-------------|
| `get_meetings()` | `getMeetings` | List active meetings |
| `get_meeting_info(meeting_id)` | `getMeetingInfo` | Meeting details |
| `create_meeting(name, ...)` | `create` | Create a meeting |
| `get_join_url(meeting_id, full_name, ...)` | `join` | Generate join URL |
| `end_meeting(meeting_id)` | `end` | End a meeting |
| `get_recordings(meeting_id?)` | `getRecordings` | List recordings |
| `delete_recording(record_id)` | `deleteRecordings` | Delete a recording |

`create_meeting()` parameters:

```python
async def create_meeting(
    name: str,
    meeting_id: str | None = None,
    *,
    record: bool = False,
    duration: int = 0,
    welcome: str | None = None,
    mute_on_start: bool = False,
    max_participants: int = 0,
    moderator_pw: str | None = None,
    attendee_pw: str | None = None,
) -> dict:
```

- If `meeting_id` is None, it is auto-generated using `uuid.uuid4()`
- If `moderator_pw`/`attendee_pw` are None, they are auto-generated in the format `mod-<hex8>`/`att-<hex8>`

#### 10.3.3 API Endpoints

**Implementation location**: `backend/app/meetings/router.py`

| Method | Path | Description | Auth | Permission |
|--------|------|-------------|------|------------|
| GET | `/api/meetings/` | List active meetings | Required | All |
| GET | `/api/meetings/{meeting_id}` | Meeting details | Required | All |
| POST | `/api/meetings/` | Create a meeting | Required | All |
| POST | `/api/meetings/{meeting_id}/join` | Generate join URL | Required | All |
| POST | `/api/meetings/{meeting_id}/end` | End a meeting | Required | **admin** |
| GET | `/api/meetings/recordings` | List recordings | Required | All |
| DELETE | `/api/meetings/recordings/{record_id}` | Delete a recording | Required | **admin** |

> **Note**: In the `join` endpoint, if `user.is_admin` is true, the user joins with the `MODERATOR` role; otherwise, they join with the `VIEWER` role.

#### Router Registration

```python
# backend/app/main.py
from app.meetings.router import router as meetings_router
app.include_router(meetings_router)
```

#### 10.3.4 Pydantic Schemas

**Implementation location**: `backend/app/meetings/schemas.py`

```python
class Attendee(BaseModel):
    fullName: str
    role: str
    hasJoinedVoice: bool = False
    hasVideo: bool = False

class Meeting(BaseModel):
    meetingID: str
    meetingName: str
    running: bool = False
    participantCount: int = 0
    moderatorCount: int = 0
    createTime: str = ""
    hasBeenForciblyEnded: bool = False

class MeetingDetail(Meeting):
    attendees: list[Attendee] = []
    startTime: str = ""
    moderatorPW: str = ""
    attendeePW: str = ""

class CreateMeetingRequest(BaseModel):
    name: str
    meetingID: str | None = None
    record: bool = False
    duration: int = 0
    welcome: str | None = None
    muteOnStart: bool = False
    maxParticipants: int = 0

class JoinMeetingResponse(BaseModel):
    joinUrl: str

class Recording(BaseModel):
    recordID: str
    meetingID: str
    name: str = ""
    state: str = ""
    startTime: str = ""
    endTime: str = ""
    playbackUrl: str = ""
    size: int = 0
```

#### 10.3.5 Frontend Components

**Composable: `useMeetings.ts`**

**Location**: `frontend/composables/useMeetings.ts`

Module-level singleton state is used to share meeting state across the entire application.

```typescript
const meetings = ref<Meeting[]>([])
const selectedMeeting = ref<MeetingDetail | null>(null)
const recordings = ref<Recording[]>([])
const loadingMeetings = ref(false)
const loadingDetail = ref(false)
const loadingRecordings = ref(false)
const showCreateModal = ref(false)
```

Provided functions:

| Function | Description |
|----------|-------------|
| `fetchMeetings()` | Calls `GET /api/meetings/` |
| `fetchMeetingDetail(id)` | Calls `GET /api/meetings/{id}` |
| `createMeeting(data)` | Calls `POST /api/meetings/` then refreshes the list |
| `joinMeeting(id)` | Calls `POST /api/meetings/{id}/join` and opens the join URL in a new tab |
| `endMeeting(id)` | Calls `POST /api/meetings/{id}/end` then refreshes the list |
| `fetchRecordings(meetingId?)` | Calls `GET /api/meetings/recordings` |
| `deleteRecording(id)` | Calls `DELETE /api/meetings/recordings/{id}` then refreshes the list |
| `clearSelectedMeeting()` | Clears the selected meeting |

**Page: `meetings.vue`**

**Location**: `frontend/pages/meetings.vue`

The page consists of two tabs (Meetings / Recordings). The Meetings tab displays a grid view and a detail panel side by side.

**Component List:**

| Component | Location | Description |
|-----------|----------|-------------|
| `MeetingCard.vue` | `frontend/components/meetings/` | Meeting card (name, status, participant count, join/end buttons) |
| `MeetingDetail.vue` | `frontend/components/meetings/` | Meeting detail panel (attendee list, voice/video status) |
| `CreateMeetingModal.vue` | `frontend/components/meetings/` | Meeting creation modal (name, recording, time limit, etc.) |
| `RecordingList.vue` | `frontend/components/meetings/` | Recording list (playback, delete) |

#### 10.3.6 BBB Server Configuration

| Item | Value |
|------|-------|
| Server IP | 192.168.0.249 |
| Domain | meet.namgun.or.kr |
| API Endpoint | `https://meet.namgun.or.kr/bigbluebutton/api` |
| Version | BigBlueButton 3.0 |

Backend configuration (`backend/app/config.py`):

```python
bbb_url: str = "https://meet.namgun.or.kr/bigbluebutton/api"
bbb_secret: str = ""
```

### 10.4 Stalwart Mail Portal Integration

#### 10.4.1 `/mail` Page

**Location**: `frontend/pages/mail.vue`

The Stalwart Mail web UI was integrated into the portal as a native mail client. The layout consists of three panels (sidebar, mail list, mail view).

```
[MailSidebar] | [MailList] | [MailView]
              |            |
              | [MailCompose modal]
```

#### 10.4.2 Nginx CSP Configuration

A Content-Security-Policy header was configured in Nginx to allow loading the Stalwart Mail web UI within a portal iframe.

**Configuration location**: `mail.namgun.or.kr.conf` (192.168.0.150)

```nginx
# X-Frame-Options -> replaced with CSP
add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
```

> **Note**: If `X-Frame-Options: DENY` was previously set, it conflicts with CSP `frame-ancestors`, so the `X-Frame-Options` header must be removed.

#### 10.4.3 JMAP API Client

**Implementation location**: `backend/app/mail/jmap.py`

A JMAP client was implemented in preparation for a future transition to a fully native mail client (replacing the current iframe approach with a self-contained UI).

**JMAP Account ID Resolution:**

The Stalwart Admin API principal ID and the JMAP account ID differ. The JMAP accountId follows the format `hex(principal_id + offset)`, where the offset varies per installation.

```python
async def _discover_jmap_offset(client) -> int:
    """Discover the offset between admin API principal IDs and JMAP account IDs."""
    # Scans offset range 0~29 to find an account with actual data
    ...
```

**Provided API:**

| Function | JMAP Method | Description |
|----------|-------------|-------------|
| `get_session()` | `/.well-known/jmap` | Session information |
| `resolve_account_id(email)` | Admin API + JMAP | Email to JMAP account ID conversion |
| `get_mailboxes(account_id)` | `Mailbox/get` | Mailbox list |
| `get_messages(account_id, mailbox_id, ...)` | `Email/query` + `Email/get` | Message list |
| `get_message(account_id, message_id)` | `Email/get` (full) | Message details |
| `update_message(account_id, message_id, ...)` | `Email/set` (update) | Read/star/move |
| `destroy_message(account_id, message_id)` | `Email/set` (destroy) | Delete message |
| `send_message(account_id, ...)` | `Email/set` + `EmailSubmission/set` | Send message |
| `download_blob(account_id, blob_id)` | `/jmap/download/...` | Download attachment |

**Mail API Endpoints:**

**Implementation location**: `backend/app/mail/router.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/mail/mailboxes` | Mailbox list (sorted by role) |
| GET | `/api/mail/messages` | Message list (paginated) |
| GET | `/api/mail/messages/{id}` | Message details (automatically marks as read) |
| PATCH | `/api/mail/messages/{id}` | Read/star/move |
| DELETE | `/api/mail/messages/{id}` | Delete (trash then permanent delete) |
| POST | `/api/mail/send` | Send message |
| GET | `/api/mail/blob/{blob_id}` | Attachment download proxy |

### 10.5 Navigation Additions

**Implementation location**: `frontend/components/layout/AppHeader.vue`

Mail and meeting links were added to the desktop/mobile navigation.

```html
<!-- Desktop nav -->
<nav v-if="user" class="hidden sm:flex items-center gap-1">
  <NuxtLink to="/">Dashboard</NuxtLink>
  <NuxtLink to="/files">Files</NuxtLink>
  <NuxtLink to="/mail">Mail</NuxtLink>
  <NuxtLink to="/meetings">Meetings</NuxtLink>
</nav>
```

AppHeader navigation menu:

| Menu | Path | Description |
|------|------|-------------|
| Dashboard | `/` | Service status dashboard |
| Files | `/files` | File browser |
| Mail | `/mail` | Stalwart Mail iframe |
| Meetings | `/meetings` | BBB meeting management |

Mobile-responsive navigation (hamburger menu) included.

---

## 11. Phase 6: Native Login & SSO Integration (Complete)

The Authentik redirect-based login was replaced with a native login form, SSO cookies are established through the Popup Bridge pattern, and Gitea SSO integration was implemented.

### 11.1 Native Login Architecture

#### 11.1.1 Overview

Previously, users were redirected to the Authentik UI during login and used Authentik's own login form. In Phase 6, the Authentik UI was fully replaced with a "native login" approach: users enter their username and password on the portal's own login form (`/login`), and authentication is performed in the background via the Authentik Flow Executor API.

```
[User] -> Portal /login page (native login form)
    -> [Popup] auth.namgun.or.kr/portal-bridge/ (bridge page)
        -> Authentik Flow Executor API (same-origin)
        -> OAuth authorize -> callback -> extract code
    -> [postMessage] deliver code to portal
    -> [Portal Backend] POST /api/auth/native-callback
        -> Authentik Token exchange -> issue session cookie
```

#### 11.1.2 Native Login Form

- **Page**: `/login` (auth layout)
- **Input fields**: Username/email, password
- **Redirect parameter**: `?redirect=<URL>` query parameter support (for external service SSO)
- **Security**: Redirects are restricted to the `namgun.or.kr` domain or relative paths only

### 11.2 Popup Bridge Pattern

The previous Authentik full-page redirect approach provided a poor UX, and the iframe approach failed to set SSO cookies due to third-party cookie partitioning (browser security policy). The Popup Bridge pattern was adopted to solve these issues.

#### 11.2.1 Why the Popup Bridge Pattern

**Limitations of iframes:**

Modern browsers (Chrome 120+, Firefox 118+, Safari 17+) enforce **third-party cookie partitioning**. Cookies set by `auth.namgun.or.kr` within an iframe are partitioned from the top-level context (`namgun.or.kr`) and stored in a separate cookie jar. This causes:

1. Even if the user logs in to Authentik within an iframe, the SSO session cookie (`authentik_session`) is not recognized during OAuth redirects for other services (e.g., Gitea).
2. Authentik's CSRF protection may fail due to cookie mismatch.

**Advantages of popups:**

A popup is treated as a **top-level browsing context**. Therefore:

1. Cookies set by `auth.namgun.or.kr` are stored as **first-party cookies**.
2. The `authentik_session` cookie from Authentik is set correctly, enabling SSO to work.
3. Secure communication with the portal is possible via `window.opener.postMessage()`.

#### 11.2.2 Flow

1. User enters username/password on the `/login` page and submits
2. The browser synchronously opens a `https://auth.namgun.or.kr/portal-bridge/` popup (bypassing popup blockers)
3. The Bridge page sends a `portal-bridge-ready` postMessage
4. The portal retrieves the OIDC config + generates PKCE, then sends a `portal-login` message to the popup
5. The Bridge calls the Authentik Flow Executor API to authenticate (processing each stage sequentially)
6. After authentication completes, the `authorize` endpoint is called -> `code` is obtained
7. The Bridge delivers the code to the portal via a `portal-login-result` message
8. The portal backend exchanges the code for a token at `/api/auth/native-callback` and issues a session cookie

### 11.3 Bridge Page Structure

The bridge page is deployed on the Nginx VM (192.168.0.150) under the `auth.namgun.or.kr` domain. Being same-origin with Authentik, it can call the API without CORS issues.

#### 11.3.1 Bridge Main Page

**Location**: `/var/www/portal-bridge/index.html` (192.168.0.150)

Responsibilities:
1. Receive `portal-login` message from the portal
2. Perform authentication steps via the Authentik Flow Executor API
3. After authentication completes, call OAuth authorize via **page navigation** to reliably set SSO cookies
4. Redirect to the callback page

#### 11.3.2 Callback Page

**Location**: `/var/www/portal-bridge/callback` (no extension, 192.168.0.150)

Responsibilities:
1. Extract `code` and `state` parameters from the URL
2. Deliver the code to the portal via `window.opener.postMessage()`

> **Note**: Since the file has no extension, `default_type text/html;` must be set in Nginx.

#### 11.3.3 Nginx Configuration

```nginx
# auth.namgun.or.kr.conf (192.168.0.150)
location /portal-bridge/ {
    alias /var/www/portal-bridge/;
    default_type text/html;
    add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
    add_header Cache-Control "no-store";
}
```

#### 11.3.4 SELinux

On Rocky Linux 10, Nginx requires the correct SELinux context to access files.

```bash
semanage fcontext -a -t httpd_sys_content_t "/var/www/portal-bridge(/.*)?"
restorecon -Rv /var/www/portal-bridge/
```

### 11.4 Authentik Flow Executor API Details

The complete authentication flow performed by the bridge page proceeds through the following steps.

#### Step 1: Register OAuth Pending Authorization

```javascript
await fetch("/application/o/authorize/?" + oauthParams, {
    redirect: "manual"
});
```

By calling with `redirect: "manual"`, the actual redirect is not followed; instead, a pending authorization is registered within Authentik. At this point, the status is 0 (opaque redirect).

#### Step 2: Start Flow Executor

```javascript
const flowUrl = `/api/v3/flows/executor/${flowSlug}/?query=${encodeURIComponent(oauthParams)}`;
const resp = await fetch(flowUrl, {
    headers: { "Accept": "application/json" }
});
const challenge = await resp.json();
```

> **Key point**: When passing OAuth parameters in the `query` parameter, `encodeURIComponent()` must be applied. Otherwise, `&` characters are interpreted as URL separators and parameters are lost.

#### Step 3: ak-stage-identification (User Identification)

```javascript
// challenge.component === "ak-stage-identification"
const resp = await fetch(flowUrl, {
    method: "POST",
    headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
    },
    body: JSON.stringify({ uid_field: username })
});
```

#### Step 4: xak-flow-redirect (Mid-flow Redirect)

If Authentik sends a mid-flow redirect, the specified URL is followed.

```javascript
// challenge.component === "xak-flow-redirect"
// If challenge.to is a relative path, make a GET request to that path
```

#### Step 5: ak-stage-password (Password Submission)

```javascript
// challenge.component === "ak-stage-password"
const resp = await fetch(flowUrl, {
    method: "POST",
    headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
    },
    body: JSON.stringify({ password: password })
});
```

#### Step 6: Flow Completion — `xak-flow-redirect to="/"`

Upon successful password authentication, Authentik returns a response with `component: "xak-flow-redirect"` and `to: "/"`. This indicates that the flow has completed, but Authentik cannot find the OAuth context and is attempting to redirect to the home page.

> **Key issue**: Because the Flow Executor was called via the JSON API, Authentik cannot automatically process the OAuth pending authorization at the point of flow completion.

#### Step 7: Re-invoke Authorize (Page Navigation)

```javascript
// After flow completion, call OAuth authorize via page navigation
// Execute via window.location change, not fetch()
window.location.href = "/application/o/authorize/?" + oauthParams;
```

This ensures:
1. The SSO session cookie (`authentik_session`) is **reliably** set (since it is a top-level navigation).
2. Authentik recognizes the already-authenticated session and issues an OAuth code.
3. The browser redirects to `redirect_uri` (`/portal-bridge/callback`).

#### Step 8: Extract Code from Callback

```javascript
// /portal-bridge/callback page
const params = new URLSearchParams(window.location.search);
const code = params.get("code");
window.opener.postMessage({
    type: "portal-login-result",
    success: true,
    code: code
}, "https://namgun.or.kr");
```

### 11.5 PKCE (S256) Implementation

#### 11.5.1 Client Side (Web Crypto API)

**Implementation location**: `frontend/composables/useAuth.ts`

```typescript
function generateCodeVerifier(): string {
    const array = new Uint8Array(64)
    crypto.getRandomValues(array)
    return btoa(String.fromCharCode(...array))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/g, '')
}

async function generateCodeChallenge(verifier: string): Promise<string> {
    const data = new TextEncoder().encode(verifier)
    const digest = await crypto.subtle.digest('SHA-256', data)
    return btoa(String.fromCharCode(...new Uint8Array(digest)))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/g, '')
}

function generateState(): string {
    const array = new Uint8Array(32)
    crypto.getRandomValues(array)
    return btoa(String.fromCharCode(...array))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/g, '')
}
```

- `code_verifier`: 64 random bytes -> base64url
- `code_challenge`: SHA-256(code_verifier) -> base64url
- Uses `crypto.getRandomValues()` + `crypto.subtle.digest('SHA-256', ...)`
- The PKCE pair is generated on the browser side; `code_verifier` is retained by the portal and not transmitted to the popup

#### 11.5.2 Server Side (Existing Redirect Flow Retained)

**Implementation location**: `backend/app/auth/oidc.py`

```python
def generate_pkce() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge
```

PKCE method:
- `code_challenge_method`: `S256`
- `code_verifier`: Generated on the client, sent during token exchange
- `code_challenge`: `BASE64URL(SHA256(code_verifier))`

### 11.6 Backend Changes

#### 11.6.1 `POST /api/auth/native-callback`

**Implementation location**: `backend/app/auth/router.py`

Exchanges the authorization code received from the bridge callback for a token with Authentik, retrieves user information, and issues a session cookie.

```python
@router.post("/native-callback")
async def native_callback(
    body: NativeCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        tokens = await exchange_code(
            body.code, body.code_verifier, settings.bridge_redirect_uri
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authorization code")

    access_token = tokens["access_token"]
    userinfo = await get_userinfo(access_token)
    sub = userinfo["sub"]
    groups = userinfo.get("groups", [])

    # Upsert user (same logic as callback)
    # ...

    session_data = sign_value({"user_id": user.id})
    response = JSONResponse(content={"status": "ok"})
    response.set_cookie(
        SESSION_COOKIE,
        session_data,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        path="/",
    )
    return response
```

Key differences:
- `redirect_uri` is set to `settings.bridge_redirect_uri` (bridge callback URL instead of the original callback URL)
- The response is a `JSONResponse`, not a redirect

#### 11.6.2 `GET /api/auth/oidc-config`

Returns public configuration needed by the browser to generate PKCE parameters.

```python
@router.get("/oidc-config")
async def oidc_config():
    return {
        "client_id": settings.oidc_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
        "scope": "openid profile email",
        "flow_slug": settings.authentik_flow_slug,
    }
```

#### 11.6.3 `POST /api/auth/logout`

Removed the Authentik end-session call and only clears the portal session cookie.

```python
@router.post("/logout")
async def logout():
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
```

> **Rationale**: In the native login approach, maintaining the Authentik session cookie is essential for SSO. Therefore, the portal logout does not terminate the Authentik session. The Authentik session expires naturally or can be manually terminated by the user via the Authentik admin UI.

#### 11.6.4 `exchange_code()` Changes

An optional `redirect_uri` parameter was added so the function can be used by both the native callback and the existing callback.

```python
async def exchange_code(
    code: str, code_verifier: str, redirect_uri: str | None = None
) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri or settings.oidc_redirect_uri,
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
                "code_verifier": code_verifier,
            },
        )
        resp.raise_for_status()
        return resp.json()
```

#### 11.6.5 `NativeCallbackRequest` Schema

**Implementation location**: `backend/app/auth/schemas.py`

```python
class NativeCallbackRequest(BaseModel):
    code: str
    code_verifier: str
```

#### 11.6.6 `config.py` Configuration Additions

```python
# Authentik Native Login
authentik_flow_slug: str = "default-authentication-flow"
bridge_redirect_uri: str = "https://auth.namgun.or.kr/portal-bridge/callback"
```

#### 11.6.7 Backend Endpoint Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | GET | OIDC redirect (legacy, sets PKCE cookie) |
| `/api/auth/callback` | GET | OIDC callback (legacy, code exchange + session setup) |
| `/api/auth/oidc-config` | GET | Returns public OIDC configuration (client_id, redirect_uri, scope, flow_slug) |
| `/api/auth/native-callback` | POST | Native login code exchange (code + code_verifier -> session cookie) |
| `/api/auth/me` | GET | Current authenticated user information |
| `/api/auth/logout` | POST | Session cookie deletion |

### 11.7 Frontend Changes

#### 11.7.1 `useAuth.ts` — `nativeLogin()` Function

**Implementation location**: `frontend/composables/useAuth.ts`

The existing `login()` function (redirect to Authentik UI) was replaced with the `nativeLogin()` function (popup bridge approach).

```typescript
const BRIDGE_URL = 'https://auth.namgun.or.kr/portal-bridge/'
const BRIDGE_ORIGIN = 'https://auth.namgun.or.kr'
const BRIDGE_CALLBACK = 'https://auth.namgun.or.kr/portal-bridge/callback'
```

`nativeLogin()` function flow:

1. **Register bridge-ready listener** (before opening the popup)
2. **Open popup synchronously** (`window.open()` -- executed before any await to avoid popup blockers)
3. **Wait for bridge-ready + fetch OIDC config** (Promise.all in parallel)
4. **Generate PKCE** (code_verifier, code_challenge, state)
5. **Send credentials to popup** (`popup.postMessage()`)
6. **Wait for result** (portal-login-result message)
7. **Exchange code** (`POST /api/auth/native-callback`)
8. **Fetch user info** (`GET /api/auth/me`)

```typescript
const nativeLogin = async (username: string, password: string): Promise<void> => {
    // 1. Set up listener (before opening popup -- prevents race condition)
    const bridgeReady = new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Bridge load timeout')), 15000)
        function onReady(event: MessageEvent) {
            if (event.origin !== BRIDGE_ORIGIN) return
            if (event.data?.type !== 'portal-bridge-ready') return
            clearTimeout(timeout)
            window.removeEventListener('message', onReady)
            resolve()
        }
        window.addEventListener('message', onReady)
    })

    // 2. Open popup synchronously (before await)
    const popup = window.open(BRIDGE_URL, '_portal_auth', 'width=1,height=1,left=-100,top=-100')
    if (!popup) throw new Error('Popup was blocked.')

    try {
        // 3~8. Authentication flow...
    } finally {
        popup.close()
    }
}
```

> **Note**: The popup size is set to 1x1 and positioned off-screen so it is invisible to the user.

#### 11.7.2 `login.vue` — Native Login Form

**Implementation location**: `frontend/pages/login.vue`

- `layout: 'auth'` (full-screen centered layout)
- Username/email + password input form
- Supports `redirect` query parameter (navigates to the original page after login)
- Error messages displayed (authentication failure, timeout, etc.)

```typescript
const redirectTo = computed(() => {
    const r = route.query.redirect as string | undefined
    // Domain validation: only allow https URLs under the namgun.or.kr domain
    if (r && (r.startsWith('https://') && r.includes('.namgun.or.kr'))) return r
    return '/'
})
```

### 11.8 SSO Cookie Mechanism

#### 11.8.1 `authentik_session` Cookie Properties

| Attribute | Value | Description |
|-----------|-------|-------------|
| Domain | `auth.namgun.or.kr` | Authentik domain |
| SameSite | `None` | Sent on cross-origin requests |
| Secure | `true` | HTTPS only |
| HttpOnly | `true` | Inaccessible to JavaScript |
| Path | `/` | Entire path |

#### 11.8.2 SSO Cookie Setting via Popup

```
[Popup] = top-level browsing context
    |
[auth.namgun.or.kr] = first-party
    |
authentik_session cookie = stored as first-party cookie
    |
[Gitea OAuth redirect] -> auth.namgun.or.kr
    |
authentik_session cookie = sent automatically -> automatic authentication
```

#### 11.8.3 fetch() vs Page Navigation

| Approach | Cookie Setting | SSO Support |
|----------|---------------|-------------|
| `fetch()` (JSON API) | Depends on credentials configuration; unreliable | Unstable |
| Page navigation (`window.location`) | Reliably set by default browser behavior | Stable |

Therefore, the final authorize call from the bridge must be executed as a **page navigation**.

### 11.9 Gitea SSO Integration

#### 11.9.1 Nginx Redirect Configuration

**Configuration location**: `git.namgun.or.kr.conf` (192.168.0.150)

```nginx
location = /user/login {
    return 302 https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik;
}
```

- When a user accesses `git.namgun.or.kr/user/login`, they are redirected to the portal login page
- After login, the user is redirected to Gitea's OAuth2 endpoint
- Since the Authentik session cookie is already set, authentication occurs automatically

#### 11.9.2 Gitea app.ini Configuration

```ini
[service]
ENABLE_BASIC_AUTHENTICATION = true  ; required for git push authentication
ENABLE_OPENID_SIGNIN = false        ; disable OpenID login
```

> **Warning**: Setting `ENABLE_BASIC_AUTHENTICATION = false` causes HTTPS authentication to fail during git push. Since Nginx already redirects web login to the portal, basic authentication must remain enabled.

#### 11.9.3 Dashboard external_url

```python
# Gitea external_url in SERVICE_DEFS
"external_url": "https://git.namgun.or.kr/user/oauth2/authentik",
```

When clicking Gitea on the dashboard service card, the OAuth2 endpoint is triggered directly. If an Authentik session exists, the user is automatically logged in to Gitea.

#### 11.9.4 Login Redirect Parameter

```
https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik
```

- The `redirect` query parameter is used when sending users from external services to the portal login page
- After login completes, the user is automatically redirected to the specified URL
- Security: Only `https://` + `.namgun.or.kr` domains or `/` relative paths are permitted

### 11.10 Authentik Configuration

#### 11.10.1 OAuth2 Provider redirect_uris

Add the bridge callback URL to redirect_uris:

```
https://auth.namgun.or.kr/portal-bridge/callback
```

The existing redirect_uri is also retained (fallback for redirect-based login):

```
https://namgun.or.kr/api/auth/callback
```

#### 11.10.2 Authorization Flow

```
default-provider-authorization-implicit-consent
```

Issues the authorization code immediately without a consent screen. Since this is an internal portal, requiring consent on every login is unnecessary.

#### 11.10.3 Authentication Flow

```
default-authentication-flow
```

Uses the default Authentik authentication flow. The slug of this flow must match the `authentik_flow_slug` setting in `config.py`.

---

## 12. Comprehensive Troubleshooting

All troubleshooting items encountered across all phases are consolidated below. Duplicate items retain the most detailed version.

### Phase 0: Infrastructure

| # | Problem | Cause | Resolution |
|---|---------|-------|------------|
| 1 | Authentik initial login failure | BOOTSTRAP_PASSWORD contained special characters such as `==` | Use simple alphanumeric password |
| 2 | Authentik repeated login blocked | Accumulated reputation score | Clear the `Reputation` table |
| 3 | Windows Server DNS TXT record save failure | 255-character TXT record limit | Split a single record into multiple strings |

### Phase 1: SSO PoC

| # | Problem | Cause | Resolution |
|---|---------|-------|------------|
| 4 | Permission error when running Gitea CLI | Executed as root user | Specify git user with `--user git` option |

### Phase 2: Mail Migration

| # | Problem | Cause | Resolution |
|---|---------|-------|------------|
| 5 | LDAP authentication failure in Stalwart v0.15 — Password verification failed | `bind.auth.enable = true` is legacy syntax (v0.13). The default operates in password hash comparison mode, and Authentik does not expose userPassword hashes | Set `directory.ldap.bind.auth.method = "lookup"`. This uses search-then-bind, delegating bind authentication directly to the LDAP server |
| 6 | session.auth.directory expression override failure — After storing the string `'ldap'` in `session.auth.directory`, the evaluated value remains `"*"` (default directory) | Expression field priority issue. DB settings fail to override built-in defaults | Changed to `storage.directory = "ldap"` to set the global directory to LDAP. Internal accounts are maintained separately in the internal directory |
| 7 | Stalwart DKIM signing key not recognized — `dkim.signer-not-found: rsa-namgun.or.kr` warning | Stalwart's default DKIM configuration uses `{algorithm}-{domain}` naming convention. The manually created name `dkim-namgun` did not match | Defined the signature in config.toml as `[signature."rsa-namgun.or.kr"]`. The `ed25519-namgun.or.kr` unused warning can be safely ignored |
| 8 | Unreliable host LAN IP access from rootless Podman — Stalwart container cannot access LAN IP (192.168.0.50) LDAP Outpost | Rootless Podman slirp4netns networking has unstable host LAN access | Deployed LDAP Outpost as sidecar on the mail server VM. Uses `network_mode: host` for localhost communication. Removed LDAP Outpost from WSL2 |
| 9 | DNS DKIM public key truncated — Gmail returns `dkim=neutral (invalid public key)` | Windows Server DNS TXT record 255-character limit truncates the 2048-bit RSA public key (410 chars) | Split TXT record into two strings (first 255 chars + remaining 155 chars) |

### Phase 3: Portal Core

| # | Problem | Cause | Resolution |
|---|---------|-------|------------|
| 10 | PostgreSQL bind mount failure | NTFS (/mnt/d/) filesystem permission issue in WSL2 | Use Docker named volume (`portal-db-data`) |
| 11 | NFS v4.2 mount failure | WSL2 kernel (5.15.x) does not support NFS v4.2 | Use `nfsvers=4` (v4.1) |

### Phase 6: Native Login & SSO

| # | Problem | Cause | Resolution |
|---|---------|-------|------------|
| 12 | fetch() cross-origin redirect hang — Calling Authentik authorize from the portal yields no response and hangs | When `fetch()` follows a cross-origin redirect, Authentik returns a 302 redirect to the login page, which triggers additional redirects forming an opaque redirect chain that causes the browser to block the request | Changed `redirect_uri` to `auth.namgun.or.kr/portal-bridge/callback` (same-origin) and introduced the bridge architecture so that Authentik API calls are performed from same-origin |
| 13 | Opaque redirect loop — fetch authorize call results in `response.status === 0`, making it impossible to extract the code from the Location header | The `redirect: "manual"` option returns an opaque redirect response for cross-origin redirects. All information including status and headers is hidden in this response | Used a same-origin redirect_uri and executed the authorize call via **page navigation** (`window.location`) instead of fetch. The code is extracted from the callback page using `URLSearchParams` |
| 14 | OAuth parameter encoding omission — Flow Executor API call loses parameters after `client_id` | The `&` characters in the OAuth parameter string were interpreted as query parameter separators in the Flow Executor URL, causing the `query` parameter value to be truncated at the first `&` | Applied `encodeURIComponent(oauthParams)` |
| 15 | Authentik flow completion returns `to: "/"` — No OAuth code issued after successful password authentication | When the Flow Executor is called via the JSON API, Authentik cannot locate the OAuth pending authorization context at flow completion. The JSON API session and the OAuth authorize session are separate | After confirming flow completion (`to: "/"`), **re-invoke OAuth authorize directly**. Authentik recognizes the already-authenticated session and immediately issues a code with implicit consent |
| 16 | Authentik cookies not set in iframe — `authentik_session` cookie is not recognized during OAuth redirects for other services | **Cookie partitioning** (CHIPS, Storage Partitioning) policy in modern browsers including Chrome 120+, Firefox 118+, and Safari 17+. Third-party cookies within an iframe are partitioned by the (top-level-origin, embedded-origin) pair | Switched from iframe to **popup** approach. Since a popup is a top-level browsing context, cookies are correctly set as first-party |
| 17 | Popup-portal race condition — Intermittent `Bridge load timeout` errors | The popup finishes loading and calls `postMessage()` during the interval between opening the popup and the next `await`. The portal then calls `addEventListener` afterward, missing the message | **Set up the message listener before opening the popup** to ensure the bridge's ready message is always received |
| 18 | Callback file Content-Type — Accessing `/portal-bridge/callback` causes the browser to attempt a file download | The `callback` file has no `.html` extension, so Nginx sets the MIME type to `application/octet-stream` | Added `default_type text/html;` to the Nginx location block |
| 19 | SSO cookies not set — After native login, accessing Gitea requires logging in again | When the entire authentication flow is performed solely via `fetch()` JSON API, cookies may be unreliably set due to the `SameSite=None` + `Secure` combination | Changed the bridge's final authorize call to **page navigation** (`window.location.href`) so the browser reliably sets the cookie |
| 20 | Gitea auto-login failure — After logging in to the portal, accessing Gitea displays its own login page | Gitea displays its own login page (`/user/login`) by default and does not have a built-in OAuth auto-redirect feature | Configured Nginx to redirect Gitea's `/user/login` path to the portal login page. The `redirect` parameter specifies the Gitea OAuth endpoint |
| 21 | git push HTTP authentication failure — `git push` results in `403 Forbidden` | `ENABLE_BASIC_AUTHENTICATION = false` disabled HTTP Basic authentication for the git CLI | Changed back to `ENABLE_BASIC_AUTHENTICATION = true`. Since Nginx already redirects browser access to `/user/login` to the portal, enabling basic authentication does not affect web login |

---

## 13. Modified File List

### 13.1 Backend

| File Path | Description |
|-----------|-------------|
| `backend/app/config.py` | Added `bbb_url`, `bbb_secret`, `authentik_flow_slug`, `bridge_redirect_uri` settings |
| `backend/app/main.py` | Registered `meetings_router`, `mail_router` |
| `backend/app/auth/router.py` | Added `native-callback`, `oidc-config` endpoints; modified `logout` |
| `backend/app/auth/oidc.py` | Added optional `redirect_uri` parameter to `exchange_code()` |
| `backend/app/auth/schemas.py` | Added `NativeCallbackRequest` schema |
| `backend/app/auth/deps.py` | Session authentication logic (unchanged, for reference) |
| `backend/app/services/health.py` | Modified `SERVICE_DEFS`: Stalwart `internal_only`, removed Pi-Hole, RustDesk TCP, added BBB |
| `backend/app/services/schemas.py` | `internal_only` field on `ServiceStatus` (added in Phase 4) |
| `backend/app/files/service.py` | Added `_dir_cache`, `_size_cache` TTL caches and `invalidate_cache()` |
| `backend/app/files/router.py` | Added `asyncio.to_thread()` wrapping; `invalidate_cache()` calls after write operations |
| `backend/app/mail/__init__.py` | Mail module initialization |
| `backend/app/mail/jmap.py` | JMAP client (session, mailbox, message CRUD, send, attachments) |
| `backend/app/mail/schemas.py` | Mail API Pydantic schemas |
| `backend/app/mail/router.py` | Mail API endpoints (mailboxes, messages, send, attachment proxy) |
| `backend/app/meetings/__init__.py` | Meetings module initialization |
| `backend/app/meetings/bbb.py` | BBB API client (SHA256 checksum, XML parsing) |
| `backend/app/meetings/schemas.py` | Meetings API Pydantic schemas |
| `backend/app/meetings/router.py` | Meetings API endpoints (CRUD, join, recordings) |

### 13.2 Frontend

| File Path | Description |
|-----------|-------------|
| `frontend/composables/useAuth.ts` | Added `nativeLogin()` function, PKCE/bridge constants; removed `login()` |
| `frontend/composables/useMail.ts` | Mail state management composable (mailboxes, messages, send, attachments) |
| `frontend/composables/useMeetings.ts` | Meetings state management composable (list, detail, create, join, recordings) |
| `frontend/pages/login.vue` | Native login form (supports redirect query parameter) |
| `frontend/pages/mail.vue` | Mail page (three-panel layout) |
| `frontend/pages/meetings.vue` | Meetings page (meetings/recordings tabs) |
| `frontend/pages/callback.vue` | OAuth callback page (existing, retained) |
| `frontend/components/layout/AppHeader.vue` | Added mail/meetings links to navigation |
| `frontend/components/mail/MailSidebar.vue` | Mail sidebar (mailbox list) |
| `frontend/components/mail/MailList.vue` | Mail list |
| `frontend/components/mail/MailView.vue` | Mail detail view |
| `frontend/components/mail/MailCompose.vue` | Mail compose modal |
| `frontend/components/meetings/MeetingCard.vue` | Meeting card component |
| `frontend/components/meetings/MeetingDetail.vue` | Meeting detail panel |
| `frontend/components/meetings/CreateMeetingModal.vue` | Meeting creation modal |
| `frontend/components/meetings/RecordingList.vue` | Recording list component |
| `frontend/middleware/auth.global.ts` | Auth middleware (`/login` included in publicPages) |

### 13.3 Nginx (192.168.0.150)

| File Path | Description |
|-----------|-------------|
| `/etc/nginx/conf.d/auth.namgun.or.kr.conf` | Added `/portal-bridge/` location with `default_type text/html` |
| `/etc/nginx/conf.d/git.namgun.or.kr.conf` | `/user/login` redirect to portal |
| `/etc/nginx/conf.d/mail.namgun.or.kr.conf` | CSP `frame-ancestors` configuration |

### 13.4 Nginx Configuration Change Details

#### 13.4.1 auth.namgun.or.kr.conf

```nginx
server {
    listen 443 ssl http2;
    server_name auth.namgun.or.kr;

    # ... SSL, existing Authentik proxy settings ...

    # Portal bridge pages
    location /portal-bridge/ {
        alias /var/www/portal-bridge/;
        default_type text/html;
        add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
        add_header Cache-Control "no-store";
    }

    # Existing Authentik proxy
    location / {
        proxy_pass http://192.168.0.50:9000;
        # ...
    }
}
```

#### 13.4.2 git.namgun.or.kr.conf

```nginx
server {
    listen 443 ssl http2;
    server_name git.namgun.or.kr;

    # ... SSL settings ...

    # SSO: redirect web login to portal
    location = /user/login {
        return 302 https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik;
    }

    # Existing Gitea proxy
    location / {
        proxy_pass http://192.168.0.50:3000;
        # ...
    }
}
```

#### 13.4.3 mail.namgun.or.kr.conf

```nginx
server {
    listen 443 ssl http2;
    server_name mail.namgun.or.kr;

    # ... SSL settings ...

    location / {
        proxy_pass http://192.168.0.250:8080;
        # ...

        # Allow iframe embedding (used by portal)
        add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
        # X-Frame-Options removed (replaced by CSP frame-ancestors)
    }
}
```

### 13.5 Bridge Files (192.168.0.150)

| File Path | Description |
|-----------|-------------|
| `/var/www/portal-bridge/index.html` | Bridge main page (Flow Executor authentication) |
| `/var/www/portal-bridge/callback` | Callback (code extraction via postMessage) |

---

## 14. Verification Results

### 14.1 Phase 5 Verification

| Test Item | Result |
|-----------|--------|
| File list cache hit (re-request within 30 seconds) | PASS |
| Cache invalidation after file upload (immediate reflection) | PASS |
| Cache invalidation after file deletion | PASS |
| Cache invalidation after file rename | PASS |
| Cache invalidation of source/target directories after file move | PASS |
| Cache invalidation after folder creation | PASS |
| asyncio.to_thread async wrapping operation | PASS |
| Dashboard service card: Stalwart internal_only display | PASS |
| Dashboard service card: Pi-Hole removal confirmed | PASS |
| RustDesk TCP health check (port 21114) | PASS |
| BBB service card display | PASS |
| BBB meeting list query | PASS |
| BBB meeting creation | PASS |
| BBB meeting join (MODERATOR/VIEWER) | PASS |
| BBB meeting end (admin only) | PASS |
| BBB recording list query | PASS |
| BBB recording deletion (admin only) | PASS |
| Mail page (/mail) access | PASS |
| Mailbox list query | PASS |
| Message list query (pagination) | PASS |
| Message detail view (automatic mark as read) | PASS |
| Send message | PASS |
| Attachment download | PASS |
| AppHeader mail/meetings navigation links | PASS |

### 14.2 Phase 6 Verification

| Test Item | Result |
|-----------|--------|
| Native login form display | PASS |
| Login with valid credentials | PASS |
| Error message for invalid credentials | PASS |
| PKCE S256 verification (Authentik token exchange) | PASS |
| Error message when popup is blocked | PASS |
| Login timeout handling | PASS |
| Session cookie issuance (portal_session) | PASS |
| Logout (session cookie deletion) | PASS |
| authentik_session SSO cookie setting confirmed | PASS |
| Automatic Gitea login after portal login (SSO) | PASS |
| Gitea /user/login redirect to portal | PASS |
| git push HTTPS authentication (Basic Auth) | PASS |
| redirect query parameter (navigate to original page after login) | PASS |
| Bridge page Content-Type (text/html) | PASS |
| Bridge page SELinux context | PASS |
| /api/auth/oidc-config endpoint | PASS |
| /api/auth/native-callback endpoint | PASS |
| No bridge-ready message race condition | PASS |
| Popup auto-close (after login completion/failure) | PASS |

### 14.3 Phase 2 Verification

| Test Item | Result | Notes |
|-----------|--------|-------|
| SMTP authentication | **Passed** | namgun18@namgun.or.kr via LDAP |
| IMAP authentication | **Passed** | — |
| Outbound delivery | **Passed** | Confirmed receipt at Gmail, amitl.co.kr |
| Inbound delivery | **Passed** | — |
| Samsung Email app | **Passed** | IMAP 993 SSL, SMTP 465 SSL |
| DKIM signing | **Operational** | Message size increase from 1292 to 4313 bytes confirmed |
| SPF | **Passed** | — |
| DMARC | **Passed** | Based on SPF alignment |

---

## 15. Remaining Tasks and Future Plans

### 15.1 Immediate Action Required

- [x] Confirm DKIM `dkim=pass` (after DNS cache expiry)
- [ ] Register PTR record (SK Broadband, `211.244.144.69 -> mail.namgun.or.kr`)
- [ ] Add SPF TXT record for `mail.namgun.or.kr` (resolve SPF_HELO_NONE)
- [ ] Set Authentik account passwords: tsha, nahee14, kkb
- [ ] Add ed25519 DKIM signature (optional)
- [ ] Clean up /var/vmail/ backup data (after confirming migration completion)

### 15.2 Phase 5-6 Remaining Tasks

- [ ] Improve UX for automatic re-authentication when Authentik session expires
- [ ] Configure automatic cleanup policy for BBB recordings
- [ ] Complete JMAP-based native mail UI (transition from current iframe approach)
- [ ] Mail attachment upload (JMAP Blob upload)
- [ ] Multi-browser SSO testing (Safari, Firefox strict mode)
- [ ] Mobile browser popup compatibility verification (iOS Safari, Android Chrome)

### 15.3 Completed Items

| Item | Completed Phase |
|------|----------------|
| Portal core development (Nuxt 3 + FastAPI) | Phase 3 |
| File browser (NFS integration) | Phase 4 |
| BBB video conferencing integration | Phase 5 |
| Stalwart Mail iframe integration | Phase 5 |
| Native login form | Phase 6 |
| Popup Bridge SSO | Phase 6 |
| Gitea SSO integration | Phase 6 |

### 15.4 Future Plans

| Item | Description | Expected Technology Stack |
|------|-------------|--------------------------|
| Demo site | Build public demo environment at demo.namgun.or.kr | Nuxt 3 + FastAPI (read-only mode) |
| Game Panel portal integration | Manage game servers directly within the portal | Portal API + Game Panel API integration |
| CalDAV / CardDAV | Calendar/contacts synchronization | Stalwart built-in or separate server |
| Naver Works-grade ERP | Groupware features such as organization management, approvals, and messaging | Long-term objective |

### 15.5 Planned Security Enhancements

- Complete reverse DNS verification through PTR record registration
- Review and addition of CSP (Content-Security-Policy) headers
- Strengthen Authentik MFA (multi-factor authentication) policies

---

## 16. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| iRedMail migration data loss | High | Low | imapsync dry-run, Maildir backup |
| Stalwart OIDC-only mail bounce | High | Med | Use Authentik LDAP as primary backend |
| Mail client OAUTHBEARER not supported | Med | High | Provide parallel password authentication via LDAP Outpost |
| Authentik SPOF | High | Low | Local admin fallback, regular DB backup |
| DNS/TLS propagation delay | Med | Low | Pre-set low TTL, verify with dig before cutover |
| Frontend framework vulnerability | Critical | N/A | Structurally eliminated by excluding React/RSC and adopting Vue.js/Nuxt |

---

## 17. References

- Authentik: https://goauthentik.io/docs/
- Stalwart Mail Server: https://stalw.art/docs/
- Stalwart OIDC open-source announcement: https://stalw.art/blog/oidc-open-source/
- RustDesk OIDC: https://rustdesk.com/docs/en/self-host/rustdesk-server-pro/oidc/
- Gitea authentication: https://docs.gitea.com/usage/authentication
- Nuxt 3: https://nuxt.com/docs
- FastAPI: https://fastapi.tiangolo.com/
- CVE-2025-55182 (React2Shell): https://react.dev/blog/2025/12/03/critical-security-vulnerability-in-react-server-components
- OpenMediaVault: https://www.openmediavault.org/

---

*End of document. Last updated: 2026-02-19*
