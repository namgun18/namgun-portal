# Phase 2: iRedMail → Stalwart Mail Server Migration

## Summary

| Item | Details |
|------|---------|
| Date | 2026-02-18 |
| Author | Kiwan Nam |
| Target Server | 192.168.0.250 (Hyper-V VM, Rocky Linux 9.7) |
| Public IP | 211.244.144.69 (MX record) |
| Domain | namgun.or.kr |

---

## 1. Migration Overview

### 1.1 Before

| Component | Details |
|-----------|---------|
| MTA | Postfix 3.5.25 |
| MDA | Dovecot 2.3.16 |
| Spam Filter | Amavis + SpamAssassin + ClamAV |
| Webmail | Roundcube |
| Auth | PostgreSQL (iRedMail built-in) |
| Accounts | 9 |
| Mail Size | 66MB (Maildir) |

### 1.2 After

| Component | Details |
|-----------|---------|
| Mail Server | Stalwart Mail Server (latest, Podman) |
| Storage | RocksDB (built-in) |
| Auth | Authentik LDAP Outpost (sidecar) |
| Web UI | Stalwart built-in Web Admin / JMAP |
| Protocols | SMTP(25), SMTPS(465), Submission(587), IMAPS(993), ManageSieve(4190) |
| Container Runtime | Podman (rootless, network_mode: host) |

---

## 2. Architecture

### 2.1 Container Layout

```
192.168.0.250 (Mail Server VM)
├── stalwart (Podman, network_mode: host)
│   ├── SMTP :25, :465, :587
│   ├── IMAP :993
│   ├── Web Admin :8080 (→ Nginx proxy)
│   ├── HTTPS :443 (internal API)
│   └── ManageSieve :4190
│
└── stalwart-ldap (Podman, network_mode: host)
    ├── LDAP :3389
    └── LDAPS :6636
    └── → Authentik (auth.namgun.or.kr) WebSocket
```

### 2.2 Authentication Flow

```
[Mail Client] → IMAP/SMTP auth
    → [Stalwart] → LDAP lookup (127.0.0.1:3389)
        → [LDAP Outpost sidecar] → Authentik API
            → auth result

[Browser] → https://mail.namgun.or.kr
    → [Nginx 192.168.0.150] → Stalwart :8080
```

---

## 3. Key Configuration

### 3.1 LDAP Directory

```toml
directory.ldap.type = "ldap"
directory.ldap.url = "ldap://127.0.0.1:3389"
directory.ldap.base-dn = "ou=users,dc=ldap,dc=goauthentik,dc=io"
directory.ldap.bind.dn = "cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io"
directory.ldap.bind.auth.method = "lookup"
directory.ldap.filter.name = "(&(objectClass=user)(|(uid=?)(cn=?)(mail=?)))"
storage.directory = "ldap"
```

### 3.2 DKIM Signing (config.toml)

```toml
[signature."rsa-namgun.or.kr"]
algorithm = "rsa-sha256"
domain = "namgun.or.kr"
selector = "default"
canonicalization = "relaxed/relaxed"
headers = ["From", "To", "Date", "Subject", "Message-ID"]
```

### 3.3 Podman Compose

```yaml
services:
  stalwart:
    image: docker.io/stalwartlabs/stalwart:latest
    container_name: stalwart
    network_mode: host
    volumes:
      - stalwart-data:/opt/stalwart
      - /etc/letsencrypt:/etc/letsencrypt:ro

  ldap-outpost:
    image: ghcr.io/goauthentik/ldap:2025.10
    container_name: stalwart-ldap
    network_mode: host
    environment:
      AUTHENTIK_HOST: https://auth.namgun.or.kr
      AUTHENTIK_TOKEN: <outpost-token>
    extra_hosts:
      - "auth.namgun.or.kr:192.168.0.150"
```

---

## 4. DNS Records

| Record | Type | Value |
|--------|------|-------|
| namgun.or.kr | MX | mail.namgun.or.kr (priority 10) |
| mail.namgun.or.kr | A | 211.244.144.69 |
| namgun.or.kr | TXT (SPF) | `v=spf1 ip4:211.244.144.69 mx ~all` |
| _dmarc.namgun.or.kr | TXT | `v=DMARC1; p=quarantine; rua=mailto:postmaster@namgun.or.kr` |
| default._domainkey.namgun.or.kr | TXT | `v=DKIM1; k=rsa; p=<pubkey>` (split at 255 chars for Windows DNS) |

---

## 5. Troubleshooting Notes

### 5.1 LDAP Auth — bind.auth.method

Stalwart v0.15 requires `bind.auth.method = "lookup"` for search-then-bind authentication. The old `bind.auth.enable = true` syntax defaults to local password hash comparison, which fails with Authentik (no userPassword attribute exposed).

### 5.2 DKIM Signer Naming Convention

Stalwart uses `{algorithm}-{domain}` naming for DKIM signers (e.g., `rsa-namgun.or.kr`). Custom names like `dkim-namgun` will not match the default expression and will be ignored.

### 5.3 Rootless Podman Networking

Rootless Podman with slirp4netns cannot reliably reach host LAN IPs. Solution: deploy LDAP Outpost as a sidecar on the same host with `network_mode: host` for localhost communication.

### 5.4 Windows DNS TXT 255-char Limit

2048-bit RSA DKIM public keys (410 chars) must be split into two TXT strings (255 + 155 chars) on Windows Server DNS.

---

## 6. Account Mapping

| iRedMail Account | Authentik User | Type |
|------------------|---------------|------|
| namgun18@namgun.or.kr | namgun18 (LDAP) | Personal |
| tsha@namgun.or.kr | tsha (LDAP) | Personal |
| nahee14@namgun.or.kr | nahee14 (LDAP) | Personal |
| kkb@namgun.or.kr | kkb (LDAP) | Personal |
| administrator@namgun.or.kr | administrator (LDAP) | Personal |
| system@namgun.or.kr | — | Stalwart internal |
| postmaster@namgun.or.kr | — | Stalwart internal |
| git@namgun.or.kr | — | Stalwart internal |
| noreply@namgun.or.kr | — | Stalwart internal |

---

## 7. Removed Packages

```
postfix, dovecot, amavis, clamav, spamassassin, php-fpm
nginx (disabled)
```

Legacy mail data at `/var/vmail/` (72MB) preserved for backup.

---

## 8. Remaining Tasks

- [ ] Verify `dkim=pass` after DNS cache expiry
- [ ] Register PTR record (ISP: SK Broadband, 211.244.144.69 → mail.namgun.or.kr)
- [ ] Add SPF TXT record for mail.namgun.or.kr (resolve SPF_HELO_NONE)
- [ ] Set passwords for remaining accounts (tsha, nahee14, kkb) in Authentik
- [ ] Optional: Add ed25519 DKIM signature
