# Phase 2: iRedMail → Stalwart Mail Server 마이그레이션

## 작업 요약

| 항목 | 내용 |
|------|------|
| 작업일 | 2026-02-18 |
| 작성자 | 남기완 |
| 대상 서버 | 192.168.0.250 (Hyper-V VM, Rocky Linux 9.7) |
| 공인 IP | 211.244.144.69 (MX 레코드) |
| 도메인 | namgun.or.kr |

---

## 1. 마이그레이션 개요

### 1.1 변경 전

| 항목 | 내용 |
|------|------|
| MTA | Postfix 3.5.25 |
| MDA | Dovecot 2.3.16 |
| 스팸 필터 | Amavis + SpamAssassin + ClamAV |
| 웹메일 | Roundcube |
| 인증 | PostgreSQL (iRedMail 자체) |
| 계정 수 | 9개 |
| 메일 용량 | 66MB (Maildir) |

### 1.2 변경 후

| 항목 | 내용 |
|------|------|
| 메일 서버 | Stalwart Mail Server (latest, Podman) |
| 스토리지 | RocksDB (내장) |
| 인증 | Authentik LDAP Outpost (사이드카) |
| 웹 UI | Stalwart 내장 Web Admin / JMAP |
| 프로토콜 | SMTP(25), SMTPS(465), Submission(587), IMAPS(993), ManageSieve(4190) |
| 컨테이너 런타임 | Podman (rootless, network_mode: host) |

---

## 2. 아키텍처

### 2.1 컨테이너 구성

```
192.168.0.250 (메일서버 VM)
├── stalwart (Podman, network_mode: host)
│   ├── SMTP :25, :465, :587
│   ├── IMAP :993
│   ├── Web Admin :8080 (→ Nginx 프록시)
│   ├── HTTPS :443 (내부 API)
│   └── ManageSieve :4190
│
└── stalwart-ldap (Podman, network_mode: host)
    ├── LDAP :3389
    └── LDAPS :6636
    └── → Authentik (auth.namgun.or.kr) WebSocket 연결
```

### 2.2 인증 흐름

```
[메일 클라이언트] → IMAP/SMTP 인증
    → [Stalwart] → LDAP 조회 (127.0.0.1:3389)
        → [LDAP Outpost 사이드카] → Authentik API
            → 인증 결과 반환

[웹 브라우저] → https://mail.namgun.or.kr
    → [Nginx 192.168.0.150] → Stalwart :8080
```

### 2.3 DKIM 서명 흐름

```
[인증된 사용자] → SMTP Submission (:465/:587)
    → [Stalwart] → DKIM 서명 (rsa-sha256, selector=default)
        → 외부 MTA 발송
```

---

## 3. 주요 설정

### 3.1 Stalwart LDAP 디렉토리

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

### 3.2 DKIM 서명 (config.toml)

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

### 3.3 Podman Compose (192.168.0.250)

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

---

## 4. DNS 레코드

| 레코드 | 타입 | 값 |
|--------|------|-----|
| namgun.or.kr | MX | mail.namgun.or.kr (우선순위 10) |
| mail.namgun.or.kr | A | 211.244.144.69 |
| namgun.or.kr | TXT (SPF) | `v=spf1 ip4:211.244.144.69 mx ~all` |
| _dmarc.namgun.or.kr | TXT | `v=DMARC1; p=quarantine; rua=mailto:postmaster@namgun.or.kr` |
| default._domainkey.namgun.or.kr | TXT | `v=DKIM1; k=rsa; p=<공개키>` (255자 분할 필요) |

> **Windows Server DNS 주의**: TXT 레코드가 255자를 초과하면 두 개의 문자열로 분할 등록해야 함.

---

## 5. 트러블슈팅 기록

### 5.1 LDAP 인증 실패 — bind.auth.method

**증상**: LDAP 사용자 검색은 성공하나 "Password verification failed"

**원인**: Stalwart v0.15에서 `bind.auth.enable = true`는 구 문법(v0.13). 기본값이 password hash 비교 모드로 동작하며, Authentik은 userPassword 해시를 노출하지 않음.

**해결**: `directory.ldap.bind.auth.method = "lookup"` 설정. search-then-bind 방식으로 LDAP 서버에 직접 bind 인증 위임.

### 5.2 session.auth.directory expression 설정 불가

**증상**: `session.auth.directory`에 문자열 `'ldap'` 저장 후에도 평가값이 `"*"` (기본 디렉토리)

**원인**: Expression 필드의 우선순위 문제. DB 설정이 내장 기본값을 오버라이드하지 못함.

**해결**: `storage.directory = "ldap"`로 전역 디렉토리를 LDAP으로 변경. 내부 계정은 internal 디렉토리에 별도 유지.

### 5.3 DKIM signer not found

**증상**: `dkim.signer-not-found: rsa-namgun.or.kr` 경고

**원인**: Stalwart 기본 DKIM 설정이 `{algorithm}-{domain}` 네이밍 규칙 사용. 수동 생성한 `dkim-namgun` 이름과 불일치.

**해결**: config.toml에 `[signature."rsa-namgun.or.kr"]` 섹션으로 서명 정의. `ed25519-namgun.or.kr`은 미사용 경고(무시 가능).

### 5.4 Rootless Podman LAN 접근 불가

**증상**: Stalwart 컨테이너에서 LAN IP(192.168.0.50)의 LDAP Outpost 접근 불가

**원인**: Rootless Podman의 slirp4netns 네트워크에서 호스트 LAN 접근이 불안정

**해결**: LDAP Outpost를 메일서버 VM에 사이드카로 배포. `network_mode: host`로 localhost 통신. WSL2의 LDAP Outpost 제거.

### 5.5 DNS DKIM 공개키 잘림

**증상**: Gmail에서 `dkim=neutral (invalid public key)`

**원인**: Windows Server DNS의 TXT 레코드 255자 제한으로 2048-bit RSA 공개키(410자) 잘림

**해결**: TXT 레코드를 두 개 문자열로 분할 등록 (첫 255자 + 나머지 155자)

---

## 6. 계정 매핑

| iRedMail 계정 | Authentik 사용자 | 유형 |
|---------------|-----------------|------|
| namgun18@namgun.or.kr | namgun18 (LDAP) | 개인 |
| tsha@namgun.or.kr | tsha (LDAP) | 개인 |
| nahee14@namgun.or.kr | nahee14 (LDAP) | 개인 |
| kkb@namgun.or.kr | kkb (LDAP) | 개인 |
| administrator@namgun.or.kr | administrator (LDAP) | 개인 |
| system@namgun.or.kr | — | Stalwart 내부 계정 |
| postmaster@namgun.or.kr | — | Stalwart 내부 계정 |
| git@namgun.or.kr | — | Stalwart 내부 계정 |
| noreply@namgun.or.kr | — | Stalwart 내부 계정 |

---

## 7. 보안 설정 (ISMS-P)

| 항목 | 설정 |
|------|------|
| TLS 최소 버전 | 1.2 |
| IMAP | Implicit TLS only (:993), 평문 143 비활성화 권장 |
| SMTP | STARTTLS (:587), Implicit TLS (:465) |
| POP3 | 비활성화 권장 |
| DKIM | rsa-sha256, 2048-bit |
| SPF | `v=spf1 ip4:211.244.144.69 mx ~all` |
| DMARC | `p=quarantine` |
| Nginx 보안 헤더 | HSTS, X-Frame-Options, X-Content-Type-Options 등 |
| Web Admin 접근 | Nginx 프록시 경유, 내부 IP 제한 권장 |

---

## 8. 제거된 패키지

```
postfix, postfix-pcre, postfix-pgsql
dovecot, dovecot-pgsql, dovecot-pigeonhole
amavis, perl-Amavis
clamav-filesystem
spamassassin
php-fpm
nginx (비활성화)
```

기존 메일 데이터 `/var/vmail/` (72MB)은 보존.

---

## 9. 잔여 작업

- [ ] DKIM DNS 캐시 만료 후 `dkim=pass` 최종 확인
- [ ] PTR 레코드 등록 (SK브로드밴드, 211.244.144.69 → mail.namgun.or.kr)
- [ ] mail.namgun.or.kr SPF TXT 레코드 추가 (SPF_HELO_NONE 해소)
- [ ] 나머지 개인 계정(tsha, nahee14, kkb) Authentik 비밀번호 설정 및 로그인 테스트
- [ ] ed25519 DKIM 서명 추가 (선택)
- [ ] /var/vmail/ 백업 데이터 정리 (마이그레이션 완료 확인 후)
