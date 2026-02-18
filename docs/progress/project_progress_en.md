# namgun.or.kr Integrated Portal SSO Platform — Project Progress Report

| Field | Detail |
|-------|--------|
| Project | namgun.or.kr Integrated Portal SSO Platform |
| Author | Kiwan Nam |
| Classification | Internal / Confidential |

## Document History

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| v1.0 | 2026-02-18 | Kiwan Nam | Initial release (Phase 0 through Phase 2 complete) |

---

## 1. Project Overview

The namgun.or.kr Integrated Portal is a self-hosted, unified platform designed for household and small-organization use. It places Authentik as the central Identity Provider (IdP) and aims to consolidate diverse services — Git hosting, remote desktop, mail, video conferencing, file management, and game servers — under a single SSO (Single Sign-On) umbrella.

### 1.1 Core Objectives

- Unified SSO authentication across all services (OIDC / LDAP)
- Infrastructure aligned with ISMS-P security standards
- Data sovereignty through self-hosting
- Phased service rollout (Phase 0 through Phase 5)

---

## 2. Phase Progress Overview

| Phase | Name | Status | Period | Notes |
|-------|------|--------|--------|-------|
| Phase 0 | Infrastructure Preparation | **Complete** | — | Authentik, DNS, Nginx, TLS |
| Phase 1 | SSO PoC | **Complete** | — | Gitea OIDC, RustDesk OIDC |
| Phase 2 | Mail Server Migration | **Complete** | — | Stalwart + LDAP + OIDC |
| Phase 3 | Portal Core Development | Planned | — | Nuxt 3 + FastAPI |
| Phase 4 | Native Integrations | Planned | — | JMAP, WebDAV, CalDAV, CardDAV |
| Phase 5 | Additional Service Integration | Planned | — | BBB Greenlight OIDC, OMV Proxy Auth |

---

## 3. Infrastructure Topology

### 3.1 Physical / Logical Layout

```
Internet
  |
  +-- 211.244.144.47 (Public IP, main services)
  |     └── Port forwarding → 192.168.0.150 (Nginx Reverse Proxy)
  |
  +-- 211.244.144.69 (Public IP, MX record)
  |     └── Direct connection → 192.168.0.250 (Stalwart Mail)
  |
  ┌──────────────── Internal LAN 192.168.0.0/24 ─────────────────┐
  |                                                                |
  |  [192.168.0.50] Windows Host (Dual Xeon Gold 6138, 128GB)     |
  |    └── WSL2 / Docker                                           |
  |       ├── Authentik (server + worker + PostgreSQL 16)          |
  |       ├── Gitea 1.25.4                                         |
  |       ├── RustDesk Pro (hbbs + hbbr)                           |
  |       └── Game Panel (backend + nginx + palworld)              |
  |                                                                |
  |  [192.168.0.150] Hyper-V VM — Nginx (Rocky Linux 10)          |
  |    └── Central reverse proxy, TLS termination                  |
  |                                                                |
  |  [192.168.0.250] Hyper-V VM — Mail (Rocky Linux 9.7)          |
  |    └── Podman (rootless)                                       |
  |       ├── Stalwart Mail Server (network_mode: host)            |
  |       └── Authentik LDAP Outpost (sidecar)                     |
  |                                                                |
  |  [192.168.0.251] Pi-Hole DNS (internal primary DNS)            |
  |                                                                |
  └────────────────────────────────────────────────────────────────┘
```

### 3.2 Services Summary

| Service | Subdomain | Host | SSO Method | Status |
|---------|-----------|------|------------|--------|
| Authentik | auth.namgun.or.kr | 192.168.0.50 (Docker) | — (IdP) | Running |
| Gitea | git.namgun.or.kr | 192.168.0.50 (Docker) | OIDC | Running |
| RustDesk Pro | remote.namgun.or.kr | 192.168.0.50 (Docker) | OIDC | Running |
| Game Panel | game.namgun.or.kr | 192.168.0.50 (Docker) | Discord OAuth2 | Running |
| Stalwart Mail | mail.namgun.or.kr | 192.168.0.250 (Podman) | LDAP + OIDC | Running |
| LDAP Outpost | — | 192.168.0.250 (Podman sidecar) | — | Running |
| Nginx Proxy | *.namgun.or.kr | 192.168.0.150 (VM) | — | Running |
| Pi-Hole | — | 192.168.0.251 | — | Running |
| BBB | meet.namgun.or.kr | TBD | OIDC (planned) | Planned |
| OMV/Files | file.namgun.or.kr | TBD | Proxy Auth (planned) | Planned |
| Portal | namgun.or.kr | TBD | OIDC (planned) | Planned |

---

## 4. Phase 0: Infrastructure Preparation (Complete)

### 4.1 Authentik SSO (Identity Provider)

- **Version**: 2025.10.4
- **Deployment**: Docker Compose on 192.168.0.50
- **Components**: Authentik Server (:9000/:9443), Worker, PostgreSQL 16
- **URL**: https://auth.namgun.or.kr
- **Bootstrap**: Admin account created

#### Caveats and Troubleshooting

| Issue | Detail |
|-------|--------|
| BOOTSTRAP_PASSWORD | Special characters (e.g., `==`) cause authentication failure. Use simple alphanumeric strings. |
| Reputation system | Accumulated reputation scores can block logins. Reset the `Reputation` table to resolve. |
| redirect_uris format | Version 2025.10 requires `RedirectURI` dataclass list format. Creation via REST API is recommended. |
| OAuth2Provider required fields | `authorization_flow` and `invalidation_flow` are mandatory. REST API preferred over CLI shell. |

### 4.2 DNS Configuration

- **Management tool**: Windows Server DNS
- **Internal DNS**: Pi-Hole (192.168.0.251)
- **Records**:
  - A records: All subdomains (auth, git, game, mail, meet, remote, namgun.or.kr)
  - MX record: mail.namgun.or.kr
  - TXT records: SPF, DKIM, DMARC

#### Windows Server DNS Limitation

> TXT records exceeding 255 characters must be split into multiple strings within a single record. The DKIM public key (RSA-2048) is a typical case requiring this treatment.

### 4.3 Nginx Reverse Proxy (192.168.0.150)

- **OS**: Rocky Linux 10 (Hyper-V VM)
- **Site configurations**: 7

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
- **HTTP/2**: Uses `http2 on` directive (not the deprecated `listen ... ssl http2` syntax)

#### ISMS-P Security Headers (applied to all sites)

```nginx
# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# Server information disclosure prevention
server_tokens off;
proxy_hide_header X-Powered-By;
proxy_hide_header Server;

# Scanner/bot blocking rules applied
```

### 4.4 TLS Certificates

| Target | Issuance | Renewal |
|--------|----------|---------|
| Nginx sites (*.namgun.or.kr) | Let's Encrypt certbot | Webroot (/var/www/certbot), automatic renewal |
| Stalwart Mail Server | Let's Encrypt ACME | Stalwart built-in ACME auto-renewal (independent of Nginx) |

---

## 5. Phase 1: SSO PoC (Complete)

### 5.1 Gitea SSO Integration

- **Version**: 1.25.4
- **URL**: https://git.namgun.or.kr
- **Authentication**: OAuth2 via Authentik OIDC

#### Configuration Method

Gitea does not expose an API endpoint for authentication sources, so the OAuth2 source was added via CLI.

```bash
docker exec --user git gitea gitea admin auth add-oauth \
  --name "Authentik" \
  --provider openidConnect \
  --key "<client-id>" \
  --secret "<client-secret>" \
  --auto-discover-url "https://auth.namgun.or.kr/application/o/<slug>/.well-known/openid-configuration"
```

> **Important**: The command must be run as the `git` user (`--user git`). Running as root causes permission errors.

#### SSO Flow Verification

1. User navigates to Gitea login page
2. Clicks "Sign in with Authentik" button
3. Redirected to Authentik authentication screen
4. After successful authentication, redirected back to Gitea
5. Gitea dashboard access confirmed

### 5.2 RustDesk Pro SSO Integration

- **URL**: https://remote.namgun.or.kr
- **Components**: hbbs (signaling server) + hbbr (relay server)
- **Authentication**: OIDC via Authentik

---

## 6. Phase 2: Mail Server Migration (Complete)

The legacy mail server based on iRedMail (Postfix + Dovecot) was migrated to Stalwart Mail Server with authentication integrated through Authentik LDAP.

### 6.1 Step-by-Step Progress

#### Step 1: Authentik LDAP Outpost Setup

| Item | Detail |
|------|--------|
| Base DN | `dc=ldap,dc=goauthentik,dc=io` |
| LDAP Application | LDAP Provider + Application + Outpost created in Authentik |
| Service account | `ldapservice` user created with "Search full LDAP directory" permission |
| Deployment location | Sidecar on the mail server VM (192.168.0.250) |

> **Rationale for outpost placement**: Rootless Podman cannot reliably reach host LAN IPs. Therefore, the LDAP Outpost was deployed as a sidecar on the same VM as the mail server.

#### Step 2: Stalwart Mail Server Deployment

- **Deployment**: Podman (rootless), `network_mode: host`
- **Storage**: RocksDB
- **Configuration management**: Configuration is stored in RocksDB after first boot; managed via CLI/API thereafter
- **TLS**: Let's Encrypt ACME auto-renewal
- **stalwart-cli path**: Located within the Podman overlay filesystem

#### Step 3: Authentik OIDC Application (Stalwart Web UI)

- OAuth2Provider created via Authentik REST API
- Application slug: `stalwart`
- Redirect URI: `https://mail.namgun.or.kr/login/callback`

#### Step 4: Account Migration

A total of 9 accounts were migrated.

**Personal accounts (5) — LDAP via Authentik**

| Account | Email | Notes |
|---------|-------|-------|
| namgun18 | namgun18@namgun.or.kr | Authentik username changed from `namgun` to `namgun18` for LDAP cn matching |
| tsha | tsha@namgun.or.kr | Password setup pending |
| nahee14 | nahee14@namgun.or.kr | Password setup pending |
| kkb | kkb@namgun.or.kr | Password setup pending |
| administrator | administrator@namgun.or.kr | — |

**Service accounts (4) — Stalwart internal authentication**

| Account | Purpose |
|---------|---------|
| system | System mail |
| postmaster | Postmaster |
| git | Gitea notification mail |
| noreply | Automated outbound only |

**Mail data migration**: imapsync from Dovecot to Stalwart

#### Step 5: DNS Update

| Record | Content | Notes |
|--------|---------|-------|
| DKIM | New RSA-2048 key generated, DNS TXT record updated | Split into 2 strings for Windows DNS |
| SPF | `v=spf1 ip4:211.244.144.69 mx ~all` | Unchanged |
| DMARC | `v=DMARC1; p=quarantine` | Unchanged |
| Selector | `default` | — |

#### Step 6: Nginx Reverse Proxy Configuration

- Configuration file: `mail.namgun.or.kr.conf` on 192.168.0.150
- HTTPS 443 → Stalwart 8080 (Web Admin / JMAP)
- SMTP (25, 465, 587) / IMAP (993) are not proxied (direct connection)
- ISMS-P security headers applied

#### Step 7: Verification Results

| Test | Result | Notes |
|------|--------|-------|
| SMTP authentication | **Pass** | namgun18@namgun.or.kr via LDAP |
| IMAP authentication | **Pass** | — |
| External send | **Pass** | Received by Gmail and amitl.co.kr |
| External receive | **Pass** | — |
| Samsung Email app | **Pass** | IMAP 993 SSL, SMTP 465 SSL |
| DKIM signing | **Working** | Message size increased from 1292 to 4313 bytes |
| DKIM DNS verification | **Pending** | Public key corrected; awaiting DNS cache expiry for dkim=pass |
| SPF | **Pass** | — |
| DMARC | **Pass** | Via SPF alignment |

#### Step 8: iRedMail Removal

Removed packages:

```
postfix, dovecot, amavis, clamav, spamassassin, php-fpm
```

- nginx disabled on the mail server VM
- Legacy mail data at `/var/vmail/` (72MB) preserved

#### Step 9: Documentation

- `phase2_mail_migration_ko.md` / `_en.md` written and pushed to Gitea

---

## 7. Key Troubleshooting Lessons

| # | Problem | Root Cause | Resolution |
|---|---------|------------|------------|
| 1 | Stalwart v0.15 LDAP authentication failure | `bind.auth.enable` defaults to hash comparison mode | Set `bind.auth.method = "lookup"` |
| 2 | Stalwart DKIM signing key not recognized | Naming convention mismatch | Use `{algorithm}-{domain}` format (e.g., `rsa-namgun.or.kr`) |
| 3 | Stalwart expression fields not overridable via DB | Some built-in defaults do not support DB overrides | Modify directly in configuration file |
| 4 | Rootless Podman cannot reach host LAN IP reliably | Podman rootless networking limitation | Deploy as sidecar with `network_mode: host` |
| 5 | Windows Server DNS fails to save TXT record | 255-character limit per TXT string | Split single record into multiple strings |
| 6 | Authentik initial login failure | BOOTSTRAP_PASSWORD contained `==` special characters | Use simple alphanumeric password |
| 7 | Authentik blocks repeated login attempts | Accumulated reputation score | Reset the `Reputation` table |
| 8 | Gitea CLI execution permission error | Running as root user | Specify `--user git` option |

---

## 8. Remaining Work Items

### 8.1 Immediate Action Required

- [ ] Confirm DKIM `dkim=pass` after DNS cache expiry (~1 hour)
- [ ] Register PTR record (SK Broadband, `211.244.144.69 → mail.namgun.or.kr`)
- [ ] Add SPF TXT record for `mail.namgun.or.kr` (resolve SPF_HELO_NONE)
- [ ] Set Authentik account passwords: tsha, nahee14, kkb

### 8.2 Future Phases

| Phase | Scope | Expected Technology Stack |
|-------|-------|--------------------------|
| Phase 3 | Portal core development | Nuxt 3 (frontend) + FastAPI (backend) |
| Phase 4 | Native integrations | JMAP (mail), WebDAV (files), CalDAV (calendar), CardDAV (contacts) |
| Phase 5 | Additional service integration | BBB Greenlight OIDC, OMV Proxy Auth |

---

## 9. Technology Stack Summary

| Category | Technology |
|----------|-----------|
| Identity Provider | Authentik 2025.10.4 |
| Authentication Protocols | OIDC, LDAP, OAuth2 |
| Reverse Proxy | Nginx (Rocky Linux 10) |
| TLS Certificates | Let's Encrypt (certbot + ACME) |
| Containers (Docker) | Authentik, Gitea, RustDesk Pro, Game Panel |
| Containers (Podman) | Stalwart Mail, LDAP Outpost |
| Mail Server | Stalwart Mail Server (RocksDB) |
| Git Hosting | Gitea 1.25.4 |
| DNS | Windows Server DNS, Pi-Hole |
| Host OS | Windows (WSL2), Rocky Linux 10, Rocky Linux 9.7 |
| Virtualization | Hyper-V |

---

## 10. Security Considerations

### 10.1 Implemented Security Policies

- ISMS-P compliant security headers applied to all sites
- TLS 1.2+ enforced (HSTS preload)
- Server information disclosure prevention (`server_tokens off`, `X-Powered-By` / `Server` headers removed)
- Scanner/bot blocking rules
- DKIM + SPF + DMARC email authentication framework

### 10.2 Planned Security Enhancements

- PTR record registration to complete reverse DNS verification
- CSP (Content-Security-Policy) header review
- Authentik MFA (multi-factor authentication) policy strengthening

---

*End of document. Last updated: 2026-02-18*
