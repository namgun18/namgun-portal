# namgun.or.kr Unified Portal SSO Integration Platform

## Project Design Document (PDD) v1.0

| Item | Detail |
|------|--------|
| Document Version | v1.0 |
| Date | 2026-02-18 |
| Author | Kiwan Nam |
| Classification | Internal / Confidential |
| Target Domain | namgun.or.kr (*.namgun.or.kr) |

---

## 1. Project Overview

### 1.1 Background & Objectives

Six independent services (Gitea, Game Panel, RustDesk, FileBrowser, BigBlueButton, Mail Server) are currently operated under the namgun.or.kr domain, each with its own authentication system. This results in credential sprawl and inconsistent security posture. This project aims to build a unified SSO portal that consolidates all services under a single credential source.

### 1.2 Scope

- Deploy SSO IdP (Authentik) with OIDC/LDAP integration across all services
- Migrate mail server from iRedMail to Stalwart Mail Server
- Restructure file server (OMV FileBrowser → WebDAV + Portal file tab)
- Develop unified portal (mail, files, calendar, contacts, blog, notifications)
- Consolidate Nginx reverse proxy (TLS termination, single entry point)
- Separate test/production environments via Docker Compose Profiles

---

## 2. Current Infrastructure

### 2.1 Hardware Environment

| Component | Specifications | Purpose |
|-----------|---------------|---------|
| Homelab Server | Dual Intel Xeon Gold 6138 / 128GB RAM | Docker Host, Hyper-V Host |
| NAS Storage | 4TB HDD (Hyper-V passthrough) | OMV VM → File server |
| Mail Server | Dedicated host 211.244.144.69 | iRedMail (SMTP/IMAP) |

### 2.2 Service Inventory & SSO Feasibility

| Service | Subdomain | SSO Method | Portal Integration | Priority |
|---------|-----------|-----------|-------------------|----------|
| Gitea | git.namgun.or.kr | OIDC native | External link | P1 |
| RustDesk | remote.namgun.or.kr | OIDC (Pro) | External link | P1 |
| BBB | meet.namgun.or.kr | OIDC (Greenlight 3.x) | External link | P2 |
| Stalwart Mail | mail.namgun.or.kr | OIDC + LDAP | Native (JMAP: mail/calendar/contacts) | P2 |
| OMV/FileServer | file.namgun.or.kr | Proxy Auth | Native (WebDAV) | P2 |
| Game Panel | game.namgun.or.kr | N/A (Discord OAuth2) | External link | - |

---

## 3. Architecture Design

### 3.1 Credential Source Topology

Authentik serves as the Single Source of Truth for credentials, providing appropriate authentication protocols per service characteristics.

```
[Authentik (Single Credential Source)]
  ├── OIDC → Gitea, RustDesk, BBB, Stalwart (web), Portal
  ├── LDAP Outpost → Stalwart (IMAP/SMTP, for mail clients)
  ├── Proxy Auth → OMV WebDAV
  └── X Game Panel (independent, Discord OAuth2)
```

### 3.2 Network Architecture

All external traffic enters through the Nginx reverse proxy as a single entry point. Internal service endpoints are never exposed externally.

```
[Internet]
    │
    ▼
[Nginx Reverse Proxy] (:443 TLS termination, single entry point)
    │
    ├── namgun.or.kr
    │     ├── /          → Nuxt 3 Frontend (internal)
    │     └── /api/*     → FastAPI Gateway (internal)
    │           ├── /api/mail/*     → Stalwart JMAP
    │           ├── /api/files/*    → OMV WebDAV
    │           ├── /api/calendar/* → Stalwart JMAP (CalDAV)
    │           ├── /api/contacts/* → Stalwart CardDAV
    │           ├── /api/blog/*     → PostgreSQL
    │           └── /api/notify/*   → Unified notifications
    │
    ├── auth.namgun.or.kr   → Authentik (IdP)
    ├── git.namgun.or.kr    → Gitea
    ├── remote.namgun.or.kr → RustDesk Pro
    ├── meet.namgun.or.kr   → BBB (Greenlight)
    ├── game.namgun.or.kr   → Game Panel
    ├── demo.namgun.or.kr   → Demo (mock, frontend only)
    ├── dev.namgun.or.kr    → Test environment
    │
    └── mail.namgun.or.kr (:25/465/587/993)
          → Stalwart (211.244.144.69)
          ※ SMTP/IMAP direct, web UI via reverse proxy only
```

### 3.3 Backend Proxy Pattern (Endpoint Concealment)

The FastAPI backend acts as a reverse proxy so that actual service endpoints are never exposed to the browser. This is a non-negotiable security design principle.

| API Path | Internal Target | Auth |
|----------|----------------|------|
| /api/mail/* | Stalwart JMAP (192.168.x.x) | SSO token |
| /api/files/* | OMV WebDAV (192.168.x.x) | SSO token |
| /api/calendar/* | Stalwart CalDAV (internal) | SSO token |
| /api/contacts/* | Stalwart CardDAV (internal) | SSO token |
| /api/blog/* | PostgreSQL (internal) | SSO token |
| /api/notify/* | Unified notifications (internal) | SSO token |

---

## 4. Technology Stack

### 4.1 Frontend: Nuxt 3 (Vue.js)

**Selection Rationale:**

- **React Server Components (RSC) vulnerability avoidance**: CVE-2025-55182 (React2Shell, CVSS 10.0) — a pre-authentication RCE vulnerability disclosed in December 2025, enabling arbitrary code execution via a single HTTP request. China state-nexus threat groups began exploiting it within hours. Vue.js/Nuxt lacks the RSC architecture, making it structurally immune to this class of vulnerability.
- **Maintainability for non-developers**: Vue template syntax is nearly identical to HTML, allowing infrastructure engineers to intuitively understand the code.
- **SSR/SSG support**: Blog SSG and dashboard SSR can coexist.
- **Korean enterprise standard**: Vue.js is adopted as the GS-certified standard in Korean large enterprise SI market.

### 4.2 Backend: FastAPI (Python)

**Selection Rationale:**

- Python-based, synergizing with existing automation tool development experience
- Swagger UI auto-generation minimizes API documentation overhead
- Async-native for concurrent external service API calls
- Easy JMAP, WebDAV, CalDAV, CardDAV protocol client implementation

### 4.3 IdP: Authentik

**Selection Rationale:**

- OIDC Provider + LDAP Outpost in a single deployment
- Docker-native (PostgreSQL + Redis)
- Native Forward Auth/Proxy Auth support
- Resource footprint: ~2-3GB RAM (ample headroom in current environment)
- Rejected alternatives: Keycloak (Java, 3-4GB+, excessive for homelab), Authelia (immature OIDC Provider)

### 4.4 Mail Server: Stalwart Mail Server

Replacing iRedMail Community with Stalwart Mail Server (AGPL-3.0).

- OIDC client feature open-sourced since v0.11.5 (Enterprise tier not required)
- Native LDAP backend support (Authentik LDAP Outpost integration)
- All-in-one Rust binary: SMTP, IMAP, POP3, JMAP, CalDAV, CardDAV, WebDAV, Sieve
- Built-in web UI + JMAP API (enables portal mail tab, Roundcube unnecessary)
- Official Docker image: `stalwartlabs/stalwart:latest`

### 4.5 Technology Stack Summary

| Layer | Technology | License |
|-------|-----------|---------|
| Frontend | Nuxt 3 + Vue 3 + TailwindCSS | MIT |
| Backend | FastAPI + Python 3.12+ | MIT |
| IdP | Authentik | MIT |
| Mail Server | Stalwart Mail Server | AGPL-3.0 |
| Database | PostgreSQL | PostgreSQL License |
| Blog Rendering | @nuxt/content (MDX) | MIT |
| Reverse Proxy | Nginx | BSD-2-Clause |
| Container | Docker + Docker Compose | Apache-2.0 |
| File Server | OpenMediaVault + WebDAV | GPL-3.0 |
| Remote Desktop | RustDesk Pro | Custom (Pro) |
| Git Server | Gitea | MIT |
| Video Conferencing | BigBlueButton + Greenlight 3.x | LGPL-3.0 |

---

## 5. Security Design

### 5.1 React Exclusion Rationale

CVE-2025-55182 (React2Shell) is a CVSS 10.0 pre-authentication RCE vulnerability that allows arbitrary code execution on the server via a single HTTP request. Within hours of disclosure in December 2025, China state-nexus threat groups began active exploitation. Three additional CVEs followed (CVE-2025-55183, CVE-2025-55184, CVE-2025-67779).

In a self-hosted environment without enterprise-grade protections (WAF, dedicated security team), structurally eliminating the attack surface is the best defense. Vue.js/Nuxt lacks the RSC architecture, making the same class of vulnerability structurally impossible.

### 5.2 Authentication & Authorization

- Authentik OIDC: Authorization Code Flow with PKCE
- Authentik LDAP Outpost: Password auth for mail clients (OAUTHBEARER unsupported client fallback)
- Nginx Forward Auth: Authentik auth delegation for OMV WebDAV access
- SSO token-based API auth: Authentication middleware on all /api/* requests

### 5.3 Network Security

- TLS termination: Single TLS termination at Nginx; internal traffic is plaintext (Docker network)
- Endpoint concealment: All internal service IPs/ports never exposed externally
- OMV firewall: Allow only FastAPI backend IP (defense in depth)
- Nginx configuration rules: Deprecated directives forbidden (`ssl on`, `listen ssl http2` → `listen 443 ssl;` + `http2 on;`)

### 5.4 Data Security

- Authentik DB regular backups (SPOF mitigation)
- Local admin account fallback (emergency access during auth server outage)
- Stalwart migration: imapsync dry-run with integrity verification
- DNS SPF/DKIM/DMARC reconfiguration: Stalwart DKIM key regeneration

---

## 6. Portal Feature Specifications

### 6.1 Dashboard (Home)

- Service status cards (Health Check API-based)
- Notification feed (mail receipt, service alerts unified)
- External service shortcuts (automatic SSO redirect)

### 6.2 Mail Tab

- Browser email client based on Stalwart JMAP API
- Inbox, compose, reply, attachments, folder management
- Portal SSO token passed to JMAP endpoint

### 6.3 Files Tab

- Browser file manager based on OMV WebDAV
- Browse, upload, download, rename, delete, create folders
- OMV address fully concealed via FastAPI backend proxy

### 6.4 Calendar Tab

- Based on Stalwart CalDAV API
- View, create, edit, delete events

### 6.5 Contacts Tab

- Based on Stalwart CardDAV API
- View, create, edit, delete contacts

### 6.6 Blog Tab

- Markdown storage and rendering in portal DB (PostgreSQL)
- Public/private toggle, tags, code highlighting
- SEO optimization via @nuxt/content SSG

### 6.7 Notification Center

- Unified mail receipt + service alert notifications
- Real-time monitoring via Health Check poller

---

## 7. Test/Production Environment Separation

Docker Compose Profiles are used to separate port/network on the same host. No additional VM is required.

| Item | Production | Test |
|------|-----------|------|
| Domain | namgun.or.kr | dev.namgun.or.kr |
| Frontend Port | :443 | :8443 |
| Backend Port | :8000 (internal) | :8001 (internal) |
| DB | PostgreSQL (prod schema) | PostgreSQL (dev schema) |
| Deploy Command | `docker compose --profile prod up -d` | `docker compose --profile dev up -d` |
| Additional Resources | N/A | ~500MB RAM |

Operational flow: Code change → test on dev.namgun.or.kr → verify → build/deploy prod. CI/CD automation via Gitea Actions planned after GitOps training begins.

---

## 8. Development Roadmap

### Phase 0: Infrastructure Preparation

1. Deploy Authentik Docker Compose (server, worker, PostgreSQL, Redis)
2. DNS configuration: *.namgun.or.kr wildcard or individual A records
3. TLS certificates: Let's Encrypt (ACME DNS-01 challenge)
4. Nginx reverse proxy: auth.namgun.or.kr → Authentik
5. Initial admin account creation, branding configuration

### Phase 1: SSO PoC

1. Create OIDC application for Gitea in Authentik
2. Configure Gitea OAuth2 authentication source and verify SSO flow
3. Configure RustDesk Pro OIDC and verify flow

### Phase 2: Mail Server Migration

1. Deploy Stalwart Docker and configure Authentik LDAP Outpost integration
2. Create Authentik OIDC application (for Stalwart web UI)
3. imapsync dry-run and execute actual migration
4. DNS update: regenerate DKIM keys, update SPF/DKIM/DMARC records
5. 2-week parallel operation, then decommission iRedMail

### Phase 3: Portal Core Development

1. Initialize Nuxt 3 project + FastAPI backend scaffolding
2. Authentik OIDC login (Authorization Code Flow with PKCE)
3. Dashboard: service status cards + external service links
4. Docker Compose Profile-based dev/prod separation

### Phase 4: Native Integrations

1. Mail tab (JMAP client)
2. Files tab (WebDAV client)
3. Calendar tab (CalDAV client)
4. Contacts tab (CardDAV client)
5. Blog tab (markdown-based)
6. Notification center (unified notifications)

### Phase 5: Remaining SSO Integrations

1. BBB Greenlight 3.x OIDC configuration
2. OMV Proxy Auth finalization

---

## 9. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| iRedMail migration data loss | High | Low | imapsync dry-run, Maildir backup |
| Stalwart OIDC-only mail bounce | High | Med | Use Authentik LDAP as primary backend |
| Mail client OAUTHBEARER unsupported | Med | High | LDAP Outpost password auth fallback |
| Authentik SPOF | High | Low | Local admin fallback, regular DB backup |
| DNS/TLS propagation delay | Med | Low | Pre-set low TTL, dig verification before cutover |
| Frontend framework vulnerability | Critical | N/A | React/RSC excluded; Vue.js/Nuxt adopted for structural elimination |

---

## 10. References

- Authentik: https://goauthentik.io/docs/
- Stalwart Mail Server: https://stalw.art/docs/
- Stalwart OIDC Open-Source Announcement: https://stalw.art/blog/oidc-open-source/
- RustDesk OIDC: https://rustdesk.com/docs/en/self-host/rustdesk-server-pro/oidc/
- Gitea Authentication: https://docs.gitea.com/usage/authentication
- Nuxt 3: https://nuxt.com/docs
- FastAPI: https://fastapi.tiangolo.com/
- CVE-2025-55182 (React2Shell): https://react.dev/blog/2025/12/03/critical-security-vulnerability-in-react-server-components
- OpenMediaVault: https://www.openmediavault.org/

---

*End of Document*
