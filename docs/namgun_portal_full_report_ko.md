# namgun.or.kr 종합 포털 SSO 통합 플랫폼 — 프로젝트 종합 기술문서

| 항목 | 내용 |
|------|------|
| 프로젝트명 | namgun.or.kr 종합 포털 SSO 통합 플랫폼 |
| 작성자 | 남기완 (Kiwan Nam) |
| 문서 버전 | v1.0 |
| 작성일 | 2026-02-19 |
| 분류 | 내부 / 대외비 |
| 대상 도메인 | namgun.or.kr (*.namgun.or.kr) |

## 문서 이력

| 버전 | 날짜 | 작성자 | 비고 |
|------|------|--------|------|
| v1.0 | 2026-02-19 | 남기완 | PDD, 진행 보고서, Phase 2 상세, Phase 5-6 상세 통합 종합 기술문서 작성 |

---

## 1. 프로젝트 개요

### 1.1 배경 및 목적

namgun.or.kr 도메인에서 운영 중인 6개 독립 서비스(Gitea, Game Panel, RustDesk, FileBrowser, BigBlueButton, 메일서버)가 각각 별도 인증 체계를 사용하여 크레덴셜 분산 문제가 발생하고 있다. 본 프로젝트는 SSO(Single Sign-On) 통합 포털을 구축하여 단일 크레덴셜 소스로 모든 서비스를 통합 관리하는 것을 목표로 한다.

namgun.or.kr 종합 포털은 가정 및 소규모 조직을 위한 셀프 호스팅 통합 플랫폼이다. Authentik을 중앙 Identity Provider(IdP)로 두고, Git 저장소, 원격 데스크톱, 메일, 화상회의, 파일 관리, 게임 서버 등 다양한 서비스를 SSO(Single Sign-On)로 통합하는 것을 목표로 한다.

### 1.2 핵심 목표

- 모든 서비스에 대한 SSO 인증 통합 (OIDC / LDAP)
- ISMS-P 보안 기준에 준하는 인프라 구성
- 셀프 호스팅 기반의 데이터 주권 확보
- 단계적 서비스 확장 (Phase 0 ~ Phase 6)

### 1.3 프로젝트 범위

- SSO IdP(Authentik) 배포 및 전 서비스 OIDC/LDAP 연동
- 메일서버 마이그레이션 (iRedMail → Stalwart Mail Server)
- 파일서버 재구성 (OMV FileBrowser → WebDAV + 포털 파일 탭)
- 통합 포털 개발 (메일, 파일, 캘린더, 연락처, 블로그, 알림)
- Nginx 리버스 프록시 통합 (TLS 종단, 단일 진입점)
- 테스트/프로덕션 환경 분리 (Docker Compose Profile)

### 1.4 하드웨어 환경

| 컴포넌트 | 사양 | 용도 |
|---------|------|------|
| 홈랩 서버 | Dual Intel Xeon Gold 6138 / 128GB RAM | Docker Host, Hyper-V Host |
| NAS 스토리지 | 4TB HDD (Hyper-V 패스스루) | OMV VM → 파일서버 |
| 메일서버 | 전용 호스트 211.244.144.69 | Stalwart Mail Server (SMTP/IMAP) |

### 1.5 서비스 현황 및 SSO 연동 분석

| 서비스 | 서브도메인 | SSO 방식 | 포털 통합 | 우선순위 |
|--------|-----------|---------|----------|---------|
| Gitea | git.namgun.or.kr | OIDC 네이티브 | 외부 링크 | P1 |
| RustDesk | remote.namgun.or.kr | OIDC (Pro) | 외부 링크 | P1 |
| BBB | meet.namgun.or.kr | OIDC (Greenlight 3.x) | 외부 링크 | P2 |
| Stalwart Mail | mail.namgun.or.kr | OIDC + LDAP | 네이티브 (JMAP) | P2 |
| OMV/FileServer | file.namgun.or.kr | Proxy Auth | 네이티브 (WebDAV) | P2 |
| Game Panel | game.namgun.or.kr | N/A (Discord OAuth2) | 외부 링크 | - |

### 1.6 단계별 진행 현황 요약

| 단계 | 명칭 | 상태 | 비고 |
|------|------|------|------|
| Phase 0 | 인프라 준비 | **완료** | Authentik, DNS, Nginx, TLS |
| Phase 1 | SSO PoC | **완료** | Gitea OIDC, RustDesk OIDC |
| Phase 2 | 메일 서버 마이그레이션 | **완료** | Stalwart + LDAP + OIDC |
| Phase 3 | 포털 코어 개발 | **완료** | Nuxt 3 + FastAPI + PostgreSQL |
| Phase 4 | 파일 브라우저 | **완료** | NFS 마운트 + 포털 내 파일 관리 UI |
| Phase 5 | 서비스 개선 및 메일/회의 통합 | **완료** | BBB, 메일 iframe, 캐시, 네비게이션 |
| Phase 6 | 네이티브 로그인 및 SSO 통합 | **완료** | 네이티브 로그인 폼, Popup Bridge, Gitea SSO |

---

## 2. 인프라 토폴로지

### 2.1 물리/논리 구성도

```
인터넷
  │
  ├─ 211.244.144.47 (공인 IP, 메인 서비스)
  │    └─ 포트포워딩 → 192.168.0.150 (Nginx Reverse Proxy)
  │
  ├─ 211.244.144.69 (공인 IP, MX 레코드)
  │    └─ 직접 연결 → 192.168.0.250 (Stalwart Mail)
  │
  ┌──────────────────── 내부망 192.168.0.0/24 ────────────────────┐
  │                                                                │
  │  [192.168.0.50] Windows Host (Dual Xeon Gold 6138, 128GB)     │
  │    └─ WSL2 / Docker                                            │
  │       ├─ Authentik (server + worker + PostgreSQL 16)           │
  │       ├─ Portal Stack                                          │
  │       │    ├─ portal-frontend (Nuxt 3 SSR, :3000)             │
  │       │    ├─ portal-backend (FastAPI, :8000)                  │
  │       │    ├─ portal-db (PostgreSQL 16, named volume)          │
  │       │    └─ portal-nginx (내부 리버스 프록시, :8080)           │
  │       ├─ Gitea 1.25.4                                          │
  │       ├─ RustDesk Pro (hbbs + hbbr)                            │
  │       └─ Game Panel (backend + nginx + palworld)               │
  │                                                                │
  │  [192.168.0.100] OMV (OpenMediaVault) — NAS                   │
  │    └─ NFSv4 서버 (/export/root, fsid=0)                        │
  │       └─ /portal → Docker NFS volume (/storage)                │
  │                                                                │
  │  [192.168.0.150] Hyper-V VM — Nginx (Rocky Linux 10)          │
  │    └─ 중앙 리버스 프록시, TLS Termination                       │
  │                                                                │
  │  [192.168.0.249] BigBlueButton 3.0 (화상회의)                   │
  │    └─ BBB API (SHA256 checksum 인증)                            │
  │                                                                │
  │  [192.168.0.250] Hyper-V VM — Mail (Rocky Linux 9.7)          │
  │    └─ Podman (rootless)                                        │
  │       ├─ Stalwart Mail Server (network_mode: host)             │
  │       └─ Authentik LDAP Outpost (sidecar)                      │
  │                                                                │
  │  [192.168.0.251] Pi-Hole DNS (내부 1차 DNS)                    │
  │                                                                │
  └────────────────────────────────────────────────────────────────┘
```

### 2.2 서비스 현황 종합 (Phase 6 완료 기준)

| 서비스 | 서브도메인 | 호스트 | SSO 방식 | 상태 |
|--------|-----------|--------|----------|------|
| Portal | namgun.or.kr | 192.168.0.50 (Docker) | OIDC (네이티브) | 운영 중 |
| Authentik | auth.namgun.or.kr | 192.168.0.50 (Docker) | — (IdP) | 운영 중 |
| Gitea | git.namgun.or.kr | 192.168.0.50 (Docker) | OIDC + 포털 SSO | 운영 중 |
| RustDesk Pro | remote.namgun.or.kr | 192.168.0.50 (Docker) | OIDC | 운영 중 |
| Game Panel | game.namgun.or.kr | 192.168.0.50 (Docker) | Discord OAuth2 | 운영 중 |
| BBB (화상회의) | meet.namgun.or.kr | 192.168.0.249 | OIDC (포털 내 통합) | 운영 중 |
| OMV/Files | — | 192.168.0.100 (NFS) | 포털 내 파일브라우저 | 운영 중 |
| Stalwart Mail | mail.namgun.or.kr | 192.168.0.250 (Podman) | LDAP + OIDC, 포털 내 iframe 통합 | 운영 중 |
| LDAP Outpost | — | 192.168.0.250 (Podman sidecar) | — | 운영 중 |
| Nginx Proxy | *.namgun.or.kr | 192.168.0.150 (VM) | — | 운영 중 |
| Pi-Hole | — | 192.168.0.251 | — | 운영 중 |

> **Gitea 참고**: Gitea 로그인 페이지에서 자체 로그인 폼을 비활성화하고, OAuth2(Authentik) 버튼만 노출한다. 미인증 사용자가 Gitea에 접근하면 포털 로그인 페이지로 리다이렉트된다 (Nginx `portal_redirect` 룰).

### 2.3 크레덴셜 소스 토폴로지

Authentik을 단일 크레덴셜 소스(Single Source of Truth)로 사용하며, 서비스별 특성에 맞는 인증 프로토콜을 제공한다.

```
[Authentik (단일 크레덴셜 소스)]
  ├── OIDC → Gitea, RustDesk, BBB, Stalwart(웹), Portal
  ├── LDAP Outpost → Stalwart(IMAP/SMTP, 메일 클라이언트용)
  ├── Proxy Auth → OMV WebDAV
  └── X Game Panel (독립, Discord OAuth2)
```

### 2.4 네트워크 아키텍처

모든 외부 트래픽은 Nginx 리버스 프록시를 통해 단일 진입점으로 진입하며, 내부 서비스 엔드포인트는 외부에 절대 노출되지 않는다.

```
[Internet]
    │
    ▼
[Nginx Reverse Proxy] (:443 TLS 종단, 단일 진입점)
    │
    ├── namgun.or.kr
    │     ├── /          → Nuxt 3 Frontend (내부)
    │     └── /api/*     → FastAPI Gateway (내부)
    │           ├── /api/mail/*     → Stalwart JMAP
    │           ├── /api/files/*    → OMV WebDAV
    │           ├── /api/calendar/* → Stalwart CalDAV
    │           ├── /api/contacts/* → Stalwart CardDAV
    │           ├── /api/blog/*     → PostgreSQL
    │           └── /api/notify/*   → 통합 알림
    │
    ├── auth.namgun.or.kr   → Authentik (IdP)
    ├── git.namgun.or.kr    → Gitea
    ├── remote.namgun.or.kr → RustDesk Pro
    ├── meet.namgun.or.kr   → BBB (Greenlight)
    ├── game.namgun.or.kr   → Game Panel
    ├── dev.namgun.or.kr    → 테스트 환경
    │
    └── mail.namgun.or.kr (:25/465/587/993)
          → Stalwart (211.244.144.69)
          ※ SMTP/IMAP 직접, 웹 UI만 리버스 프록시
```

### 2.5 백엔드 프록시 패턴 (엔드포인트 은닉)

FastAPI 백엔드가 리버스 프록시 역할을 하여 브라우저에는 실제 서비스 엔드포인트가 절대 노출되지 않는다. 이는 보안 엔지니어로서 용납할 수 없는 설계 원칙이다.

| API 경로 | 내부 대상 | 인증 |
|---------|---------|------|
| /api/mail/* | Stalwart JMAP (192.168.x.x) | SSO 토큰 |
| /api/files/* | OMV WebDAV (192.168.x.x) | SSO 토큰 |
| /api/calendar/* | Stalwart CalDAV (내부) | SSO 토큰 |
| /api/contacts/* | Stalwart CardDAV (내부) | SSO 토큰 |
| /api/blog/* | PostgreSQL (내부) | SSO 토큰 |
| /api/notify/* | 통합 알림 (내부) | SSO 토큰 |

---

## 3. 기술 스택

### 3.1 프론트엔드: Nuxt 3 (Vue.js)

**선정 근거:**

- **React Server Components(RSC) 취약점 회피**: CVE-2025-55182 (React2Shell, CVSS 10.0) — 사전인증 RCE 취약점이 2025년 12월 공개되어 대규모 실제 공격이 발생. Vue.js/Nuxt는 RSC 구조가 없어 해당 취약점 유형에 구조적으로 면역
- **비개발자 유지보수 용이성**: Vue 템플릿 문법이 HTML과 거의 동일하여 인프라 엔지니어가 직관적으로 이해 가능
- **SSR/SSG 지원**: 블로그 SSG, 대시보드 SSR 혼용 가능
- **공공/대기업 SI 표준**: 국내 대기업 SI 시장에서 Vue.js가 GS인증 표준으로 채택

### 3.2 백엔드: FastAPI (Python)

**선정 근거:**

- Python 기반으로 기존 자동화 도구 개발 경험과 시너지
- Swagger UI 자동 생성으로 API 문서화 부담 최소화
- 비동기(async) 네이티브로 다수 외부 서비스 API 동시 호출에 적합
- JMAP, WebDAV, CalDAV, CardDAV 프로토콜 클라이언트 구현이 용이

### 3.3 IdP: Authentik

**선정 근거:**

- OIDC Provider + LDAP Outpost 동시 제공 (단일 배포)
- Docker 네이티브 (PostgreSQL + Redis)
- Forward Auth/Proxy Auth 네이티브 지원
- 리소스: ~2-3GB RAM (현재 환경에서 여유)
- 기각된 대안: Keycloak (Java, 3-4GB+ RAM, 홈랩 과도), Authelia (OIDC Provider 미성숙)

### 3.4 메일서버: Stalwart Mail Server

iRedMail 커뮤니티에서 Stalwart Mail Server(AGPL-3.0)로 교체한다.

- v0.11.5부터 OIDC client 기능 오픈소스화 (Enterprise 불필요)
- LDAP 백엔드 네이티브 지원 (Authentik LDAP Outpost 연동)
- All-in-one Rust 바이너리: SMTP, IMAP, POP3, JMAP, CalDAV, CardDAV, WebDAV, Sieve
- 빌트인 웹 UI + JMAP API (포털 메일 탭 구현 가능, Roundcube 불필요)
- 공식 Docker 이미지: `stalwartlabs/stalwart:latest`

### 3.5 기술 스택 종합 요약

| 분류 | 기술 | 라이선스 |
|------|------|---------|
| Identity Provider | Authentik 2025.10.4 | MIT |
| 인증 프로토콜 | OIDC, LDAP, OAuth2 | — |
| 프론트엔드 | Nuxt 3 + Vue 3 + TailwindCSS + shadcn-vue | MIT |
| 백엔드 | FastAPI + Python 3.12+ + SQLAlchemy 2.0 (async) + asyncpg | MIT |
| 메일서버 | Stalwart Mail Server (RocksDB) | AGPL-3.0 |
| DB | PostgreSQL 16 | PostgreSQL License |
| 블로그 렌더링 | @nuxt/content (MDX) | MIT |
| 리버스 프록시 | Nginx (Rocky Linux 10) | BSD-2-Clause |
| 컨테이너 (Docker) | Authentik, Portal (frontend + backend + nginx + PostgreSQL), Gitea, RustDesk Pro, Game Panel | Apache-2.0 |
| 컨테이너 (Podman) | Stalwart Mail, LDAP Outpost | — |
| 파일서버 | OpenMediaVault + WebDAV, NFS v4.1 | GPL-3.0 |
| 원격 데스크톱 | RustDesk Pro | Custom (Pro) |
| Git 서버 | Gitea 1.25.4 | MIT |
| 화상회의 | BigBlueButton 3.0 + Greenlight 3.x | LGPL-3.0 |
| TLS 인증서 | Let's Encrypt (certbot + ACME) | — |
| DNS | Windows Server DNS, Pi-Hole | — |
| 호스트 OS | Windows (WSL2), Rocky Linux 10, Rocky Linux 9.7 | — |
| 가상화 | Hyper-V | — |

---

## 4. 보안 설계

### 4.1 React 배제 근거

CVE-2025-55182 (React2Shell)는 CVSS 10.0 만점의 사전인증 RCE 취약점으로, 단일 HTTP 요청으로 서버에서 임의 코드 실행이 가능하다. 2025년 12월 공개 직후 중국 국가지원 해킹 그룹이 수시간 내에 익스플로잇을 시작했으며, 이후 추가 CVE 3건(CVE-2025-55183, CVE-2025-55184, CVE-2025-67779)이 발견되었다.

개인 호스팅 환경에서는 WAF, 전담 보안팀 등 기업급 보호 장치가 없으므로, 취약점 표면을 구조적으로 제거하는 것이 최선의 방어이다. Vue.js/Nuxt는 RSC 아키텍처가 없어 동일 유형의 취약점이 구조적으로 불가능하다.

### 4.2 인증/인가 보안

- Authentik OIDC: Authorization Code Flow with PKCE
- Authentik LDAP Outpost: 메일 클라이언트용 비밀번호 인증 (OAUTHBEARER 미지원 클라이언트 대응)
- Nginx Forward Auth: OMV WebDAV 접근 시 Authentik 인증 위임
- SSO 토큰 기반 API 인증: 모든 /api/* 요청에 인증 미들웨어 적용
- PKCE S256 인증 코드 보호 (replay 공격 방지)
- 서명된 세션 쿠키 (itsdangerous, httponly, secure, samesite=lax)
- 리다이렉트 URL 도메인 화이트리스트 (`*.namgun.or.kr`)

### 4.3 네트워크 보안

- TLS 종단: Nginx에서 단일 TLS 종단, 내부 통신은 평문 (Docker 네트워크)
- 엔드포인트 은닉: 모든 내부 서비스 IP/포트 외부 미노출
- OMV 방화벽: FastAPI 백엔드 IP만 허용 (이중 방어)
- Nginx 설정 규칙: deprecated 지시어 사용 금지 (`ssl on`, `listen ssl http2` → `listen 443 ssl;` + `http2 on;`)

#### ISMS-P 보안 헤더 (전 사이트 공통)

```nginx
# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# 보안 헤더
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# 서버 정보 노출 차단
server_tokens off;
proxy_hide_header X-Powered-By;
proxy_hide_header Server;

# 스캐너/봇 차단 규칙 적용
```

### 4.4 데이터 보안

- Authentik DB 정기 백업 (SPOF 대응)
- 로컬 admin 계정 fallback (인증 서버 장애 시 비상 접근)
- Stalwart 마이그레이션: imapsync dry-run 후 무결성 검증
- DNS SPF/DKIM/DMARC 재설정: Stalwart DKIM 키 재생성
- 파일 시스템 path traversal 방지 (resolve + prefix 검증)
- DKIM + SPF + DMARC 이메일 인증 체계

### 4.5 적용된 보안 정책 종합

- ISMS-P 기준 보안 헤더 전 사이트 적용
- TLS 1.2+ 강제 (HSTS preload)
- 서버 정보 노출 차단 (`server_tokens off`, `X-Powered-By` / `Server` 헤더 제거)
- 스캐너/봇 차단 규칙
- DKIM + SPF + DMARC 이메일 인증 체계
- PKCE S256 인증 코드 보호 (replay 공격 방지)
- 서명된 세션 쿠키 (itsdangerous, httponly, secure, samesite=lax)
- 파일 시스템 path traversal 방지 (resolve + prefix 검증)
- 리다이렉트 URL 도메인 화이트리스트 (`*.namgun.or.kr`)

---

## 5. Phase 0: 인프라 준비 (완료)

### 5.1 Authentik SSO (Identity Provider)

- **버전**: 2025.10.4
- **배포 방식**: Docker Compose (192.168.0.50)
- **구성 요소**: Authentik Server (:9000/:9443), Worker, PostgreSQL 16
- **접속 URL**: https://auth.namgun.or.kr
- **부트스트랩**: admin 계정 생성 완료

#### 주의사항 및 트러블슈팅

| 항목 | 내용 |
|------|------|
| BOOTSTRAP_PASSWORD | 특수문자(`==` 등) 사용 시 인증 실패 발생. 단순 영숫자 문자열 사용 필요 |
| Reputation 시스템 | reputation score가 누적되면 로그인 차단됨. `Reputation` 테이블 초기화로 해결 |
| redirect_uris 형식 | 2025.10 버전에서 `RedirectURI` dataclass 리스트 형식. REST API로 생성 권장 |
| OAuth2Provider 필수 필드 | `authorization_flow`, `invalidation_flow` 필수. CLI shell보다 REST API 사용 권장 |

### 5.2 DNS 구성

- **관리 도구**: Windows Server DNS
- **내부 DNS**: Pi-Hole (192.168.0.251)
- **등록된 레코드**:
  - A 레코드: 모든 서브도메인 (auth, git, game, mail, meet, remote, namgun.or.kr)
  - MX 레코드: mail.namgun.or.kr
  - TXT 레코드: SPF, DKIM, DMARC

#### Windows Server DNS 제약사항

> TXT 레코드가 255자를 초과할 경우, 하나의 레코드 안에서 여러 문자열로 분할하여 입력해야 한다. DKIM 공개키(RSA-2048)가 대표적인 예시이다.

### 5.3 Nginx 리버스 프록시 (192.168.0.150)

- **OS**: Rocky Linux 10 (Hyper-V VM)
- **사이트 설정 파일 수**: 7개

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
- **HTTP/2**: `http2 on` 디렉티브 사용 (deprecated `listen ... ssl http2` 방식 미사용)

### 5.4 TLS 인증서

| 대상 | 발급 방식 | 갱신 방식 |
|------|----------|----------|
| Nginx 사이트 (*.namgun.or.kr) | Let's Encrypt certbot | webroot (/var/www/certbot), 자동 갱신 |
| Stalwart Mail Server | Let's Encrypt ACME | Stalwart 내장 ACME 자동 갱신 (Nginx와 별도) |

---

## 6. Phase 1: SSO PoC (완료)

### 6.1 Gitea SSO 통합

- **버전**: 1.25.4
- **접속 URL**: https://git.namgun.or.kr
- **인증 방식**: OAuth2 via Authentik OIDC

#### 설정 방법

OAuth2 인증 소스는 Gitea API에서 지원하지 않으므로, CLI를 통해 추가하였다.

```bash
docker exec --user git gitea gitea admin auth add-oauth \
  --name "Authentik" \
  --provider openidConnect \
  --key "<client-id>" \
  --secret "<client-secret>" \
  --auto-discover-url "https://auth.namgun.or.kr/application/o/<slug>/.well-known/openid-configuration"
```

> **주의**: 반드시 `--user git`으로 실행해야 한다. root로 실행하면 권한 오류가 발생한다.

#### SSO 플로우 확인

1. 사용자가 Gitea 로그인 페이지 접속
2. "Authentik으로 로그인" 버튼 클릭
3. Authentik 인증 화면으로 리다이렉트
4. 인증 완료 후 Gitea로 콜백
5. Gitea 대시보드 접속 확인

### 6.2 RustDesk Pro SSO 통합

- **접속 URL**: https://remote.namgun.or.kr
- **구성**: hbbs (시그널링 서버) + hbbr (릴레이 서버)
- **인증 방식**: OIDC via Authentik

---

## 7. Phase 2: 메일 서버 마이그레이션 (완료)

iRedMail(Postfix + Dovecot) 기반의 레거시 메일 서버를 Stalwart Mail Server로 마이그레이션하고, Authentik LDAP를 통한 인증 통합을 완료하였다.

### 7.1 마이그레이션 개요

#### 변경 전

| 항목 | 내용 |
|------|------|
| MTA | Postfix 3.5.25 |
| MDA | Dovecot 2.3.16 |
| 스팸 필터 | Amavis + SpamAssassin + ClamAV |
| 웹메일 | Roundcube |
| 인증 | PostgreSQL (iRedMail 자체) |
| 계정 수 | 9개 |
| 메일 용량 | 66MB (Maildir) |

#### 변경 후

| 항목 | 내용 |
|------|------|
| 메일 서버 | Stalwart Mail Server (latest, Podman) |
| 스토리지 | RocksDB (내장) |
| 인증 | Authentik LDAP Outpost (사이드카) |
| 웹 UI | Stalwart 내장 Web Admin / JMAP |
| 프로토콜 | SMTP(25), SMTPS(465), Submission(587), IMAPS(993), ManageSieve(4190) |
| 컨테이너 런타임 | Podman (rootless, network_mode: host) |

### 7.2 아키텍처

#### 7.2.1 컨테이너 구성

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

#### 7.2.2 인증 흐름

```
[메일 클라이언트] → IMAP/SMTP 인증
    → [Stalwart] → LDAP 조회 (127.0.0.1:3389)
        → [LDAP Outpost 사이드카] → Authentik API
            → 인증 결과 반환

[웹 브라우저] → https://mail.namgun.or.kr
    → [Nginx 192.168.0.150] → Stalwart :8080
```

#### 7.2.3 DKIM 서명 흐름

```
[인증된 사용자] → SMTP Submission (:465/:587)
    → [Stalwart] → DKIM 서명 (rsa-sha256, selector=default)
        → 외부 MTA 발송
```

### 7.3 단계별 진행 내역

#### Step 1: Authentik LDAP Outpost 구성

| 항목 | 내용 |
|------|------|
| Base DN | `dc=ldap,dc=goauthentik,dc=io` |
| LDAP Application | Authentik에서 LDAP Provider + Application + Outpost 생성 |
| 서비스 계정 | `ldapservice` 사용자 생성, "Search full LDAP directory" 권한 부여 |
| 배포 위치 | 메일 서버 VM (192.168.0.250)에 sidecar로 배포 |

> **Outpost 배포 위치 결정 근거**: rootless Podman 환경에서는 호스트 LAN IP로의 접근이 불안정하므로, LDAP Outpost를 메일 서버와 동일한 VM에 sidecar로 배치하였다.

#### Step 2: Stalwart Mail Server 배포

- **배포 방식**: Podman (rootless), `network_mode: host`
- **스토리지**: RocksDB
- **설정 관리**: 최초 부팅 후 설정이 RocksDB에 저장되며, 이후 CLI/API를 통해 관리
- **TLS**: Let's Encrypt ACME 자동 갱신
- **stalwart-cli 경로**: Podman overlay 파일시스템 내부

#### Step 3: Authentik OIDC Application (Stalwart Web UI)

- OAuth2Provider를 Authentik REST API를 통해 생성
- Application slug: `stalwart`
- Redirect URI: `https://mail.namgun.or.kr/login/callback`

#### Step 4: Nginx 리버스 프록시 설정

- 설정 파일: `mail.namgun.or.kr.conf` (192.168.0.150)
- HTTPS 443 → Stalwart 8080 (Web Admin / JMAP)
- SMTP (25, 465, 587) / IMAP (993)은 프록시하지 않음 (직접 연결)
- ISMS-P 보안 헤더 적용

### 7.4 주요 설정

#### 7.4.1 Stalwart LDAP 디렉토리

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

#### 7.4.2 DKIM 서명 (config.toml)

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

### 7.5 DNS 레코드

| 레코드 | 타입 | 값 |
|--------|------|-----|
| namgun.or.kr | MX | mail.namgun.or.kr (우선순위 10) |
| mail.namgun.or.kr | A | 211.244.144.69 |
| namgun.or.kr | TXT (SPF) | `v=spf1 ip4:211.244.144.69 mx ~all` |
| _dmarc.namgun.or.kr | TXT | `v=DMARC1; p=quarantine; rua=mailto:postmaster@namgun.or.kr` |
| default._domainkey.namgun.or.kr | TXT | `v=DKIM1; k=rsa; p=<공개키>` (255자 분할 필요) |

> **Windows Server DNS 주의**: TXT 레코드가 255자를 초과하면 두 개의 문자열로 분할 등록해야 함.

### 7.6 계정 매핑

총 9개 계정을 마이그레이션하였다.

**개인 계정 (5개) — LDAP via Authentik**

| iRedMail 계정 | Authentik 사용자 | 유형 | 비고 |
|---------------|-----------------|------|------|
| namgun18@namgun.or.kr | namgun18 (LDAP) | 개인 | Authentik username `namgun` → `namgun18`로 변경 (LDAP cn 매칭) |
| tsha@namgun.or.kr | tsha (LDAP) | 개인 | 비밀번호 설정 대기 |
| nahee14@namgun.or.kr | nahee14 (LDAP) | 개인 | 비밀번호 설정 대기 |
| kkb@namgun.or.kr | kkb (LDAP) | 개인 | 비밀번호 설정 대기 |
| administrator@namgun.or.kr | administrator (LDAP) | 개인 | — |

**서비스 계정 (4개) — Stalwart 내부 인증**

| 계정명 | 이메일 | 용도 |
|--------|--------|------|
| system | system@namgun.or.kr | 시스템 메일 |
| postmaster | postmaster@namgun.or.kr | 포스트마스터 |
| git | git@namgun.or.kr | Gitea 알림 메일 |
| noreply | noreply@namgun.or.kr | 자동 발신 전용 |

**메일 데이터 마이그레이션**: imapsync를 사용하여 Dovecot → Stalwart로 이전

### 7.7 보안 설정 (ISMS-P)

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

### 7.8 검증 결과

| 테스트 항목 | 결과 | 비고 |
|------------|------|------|
| SMTP 인증 | **통과** | namgun18@namgun.or.kr via LDAP |
| IMAP 인증 | **통과** | — |
| 외부 발신 | **통과** | Gmail, amitl.co.kr 수신 확인 |
| 외부 수신 | **통과** | — |
| Samsung Email 앱 | **통과** | IMAP 993 SSL, SMTP 465 SSL |
| DKIM 서명 | **동작** | 메시지 크기 1292 → 4313 bytes 증가 확인 |
| DKIM DNS 검증 | **확인 대기** | 공개키 수정 완료, DNS 캐시 만료 후 dkim=pass 확인 필요 |
| SPF | **통과** | — |
| DMARC | **통과** | SPF alignment 기반 |

### 7.9 제거된 패키지

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

## 8. Phase 3: 포털 코어 개발 (완료)

Nuxt 3 + FastAPI + PostgreSQL 기반의 포털 웹 애플리케이션 코어를 개발하고, Docker Compose 환경에서 프로덕션 배포를 완료하였다.

### 8.1 기술 스택 및 아키텍처

| 분류 | 기술 |
|------|------|
| 프론트엔드 | Nuxt 3 (Vue 3, SSR), shadcn-vue (UI 컴포넌트) |
| 백엔드 | FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| 데이터베이스 | PostgreSQL 16 (Alpine) |
| 인증 | OIDC via Authentik (PKCE S256) |
| 세션 관리 | itsdangerous (URLSafeTimedSerializer), 서명된 쿠키 |
| 컨테이너 | Docker Compose, `--profile prod` 배포 |

### 8.2 Docker Compose 구성

```
docker compose --profile prod up -d --build
```

| 서비스 | 컨테이너명 | 포트 | 비고 |
|--------|-----------|------|------|
| portal-db | portal-db | — (내부) | PostgreSQL 16-alpine, named volume (`portal-db-data`) |
| backend | portal-backend | 8000 (내부) | FastAPI, healthcheck `/api/health` |
| frontend | portal-frontend | 3000 (내부) | Nuxt 3 SSR |
| nginx | portal-nginx | 8080 (외부) | 내부 리버스 프록시, prod 프로필 전용 |

> **WSL2 주의**: PostgreSQL은 NTFS bind mount가 불가하므로 Docker named volume (`portal-db-data`)을 사용한다.

### 8.3 테스트/프로덕션 환경 분리

Docker Compose Profile을 활용하여 동일 호스트에서 포트/네트워크만 분리한다. 별도 VM 확보는 불필요하다.

| 항목 | 프로덕션 | 테스트 |
|------|---------|--------|
| 도메인 | namgun.or.kr | dev.namgun.or.kr |
| 프론트 포트 | :443 | :8443 |
| 백엔드 포트 | :8000 (내부) | :8001 (내부) |
| DB | PostgreSQL (prod 스키마) | PostgreSQL (dev 스키마) |
| 배포 명령 | `docker compose --profile prod up -d` | `docker compose --profile dev up -d` |
| 추가 리소스 | N/A | ~500MB RAM |

운영 플로우: 코드 수정 → dev.namgun.or.kr 테스트 → 확인 → prod 빌드/배포. GitOps 교육 시작 후 Gitea Actions CI/CD 파이프라인으로 자동화 예정.

### 8.4 OIDC 인증 (Authentik)

- **인증 플로우**: Authorization Code + PKCE (S256)
- **엔드포인트**:
  - Authorization: `https://auth.namgun.or.kr/application/o/authorize/`
  - Token: `https://auth.namgun.or.kr/application/o/token/`
  - Userinfo: `https://auth.namgun.or.kr/application/o/userinfo/`
  - End Session: `https://auth.namgun.or.kr/application/o/portal/end-session/`
- **Redirect URI**: `https://namgun.or.kr/api/auth/callback`
- **PKCE 저장**: `portal_pkce` 쿠키 (httponly, secure, samesite=lax, max_age=600)
- **세션 쿠키**: `portal_session` (httponly, secure, samesite=lax, 7일 유효)

### 8.5 사용자 모델 (User)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID (String 36) | PK |
| authentik_sub | String 255 | Authentik subject, unique index |
| username | String 150 | preferred_username |
| display_name | String 255 | 표시 이름 (nullable) |
| email | String 255 | 이메일 (nullable) |
| avatar_url | String 500 | 아바타 URL (nullable) |
| is_admin | Boolean | Authentik `authentik Admins` 그룹 소속 여부 |
| is_active | Boolean | 활성 여부 (기본값: True) |
| last_login_at | DateTime (tz) | 마지막 로그인 시각 |
| created_at | DateTime (tz) | 생성 시각 |
| updated_at | DateTime (tz) | 수정 시각 |

### 8.6 대시보드 서비스 모니터링

- **서비스 수**: 6개 (Authentik, Gitea, RustDesk, Game Panel, Stalwart Mail, BBB)
- **헬스체크 주기**: 60초 (백그라운드 태스크)
- **체크 방식**: HTTP GET (상태코드 < 400 → ok) 또는 TCP 포트 체크 (RustDesk)
- **인메모리 캐시**: `_cache` 리스트, 프론트엔드에서 `/api/services/` 로 조회
- **ServiceCard**: 서비스명, 상태 뱃지 (ok/down/checking), 응답 시간(ms), 외부 URL 링크

### 8.7 NFS 마운트 (파일 스토리지)

- **NFS 서버**: OMV (192.168.0.100), `/export/root` (fsid=0)
- **Docker NFS 볼륨**: `portal-storage` → 컨테이너 내 `/storage`
- **마운트 옵션**: `addr=192.168.0.100,nfsvers=4,rw,hard,noatime,nolock`
- **클라이언트 디바이스**: `:/portal` (fsid=0이 `/export/root`에 걸리므로)

---

## 9. Phase 4: 파일 브라우저 (완료)

NFS 마운트된 스토리지를 포털 내에서 웹 브라우저로 관리할 수 있는 파일 브라우저를 개발하였다.

### 9.1 NFS 연동 상세

| 항목 | 내용 |
|------|------|
| NFS 서버 | OMV (192.168.0.100) |
| Export 경로 | `/export/root` (fsid=0) |
| Docker 볼륨 디바이스 | `:/portal` |
| NFS 버전 | v4.1 (WSL2 커널이 v4.2를 지원하지 않아 v4.1 사용) |
| 마운트 옵션 | `nfsvers=4,rw,hard,noatime,nolock` |
| WSL2 패키지 요구사항 | `nfs-common` 설치 필요 |

### 9.2 파일 시스템 구조

```
/storage/
├── shared/          ← 공유 폴더 (전체 사용자 읽기, 관리자만 쓰기)
└── users/
    └── {user_id}/   ← 개인 폴더 (사용자별 격리)
```

- **가상 경로 체계**: `my/...` → `/storage/users/{user_id}/...`, `shared/...` → `/storage/shared/...`
- **관리자 경로**: `users/...` → `/storage/users/...` (전체 사용자 디렉토리 탐색)
- **경로 보안**: `resolve()` 후 base 경로 접두어 검증으로 path traversal 방지

### 9.3 파일 작업 (API)

| 작업 | 엔드포인트 | 비고 |
|------|-----------|------|
| 디렉토리 목록 | GET `/api/files/list` | 가상 경로 기반 |
| 파일 업로드 | POST `/api/files/upload` | multipart/form-data, 최대 1024MB |
| 파일 다운로드 | GET `/api/files/download` | StreamingResponse |
| 파일/폴더 삭제 | DELETE `/api/files/delete` | 관리자 전용 (shared), 본인 폴더는 자유 |
| 이름 변경 | POST `/api/files/rename` | — |
| 이동/복사 | POST `/api/files/move` | `copy` 파라미터로 복사 지원 |
| 폴더 생성 | POST `/api/files/mkdir` | — |

### 9.4 프론트엔드 UI

- **Breadcrumb 네비게이션**: 현재 경로를 계층별로 표시, 클릭으로 이동
- **파일 그리드/리스트 뷰**: 파일명, 크기, 수정일, MIME 타입 표시
- **사이드바**: my / shared / users(관리자) 루트 탐색
- **커맨드 바**: 업로드, 새 폴더, 삭제, 이름 변경 등 도구 모음
- **컨텍스트 메뉴**: 우클릭 메뉴 (다운로드, 이름 변경, 이동, 삭제)
- **업로드 모달**: 드래그 앤 드롭 또는 파일 선택
- **프리뷰 모달**: 이미지/텍스트 파일 미리보기
- **공유 링크 모달**: 외부 공유 링크 생성 (ShareLink 모델, 만료/다운로드 제한)

---

## 10. Phase 5: 서비스 개선 및 메일/회의 통합 (완료)

파일 리스트 캐시, BBB 화상회의 통합, Stalwart Mail iframe 통합, 서비스 카드 개선 및 네비게이션 추가를 완료하였다.

### 10.1 파일브라우저 성능 개선

#### 10.1.1 인메모리 TTL 캐시

NFS v4.1 환경에서 디렉토리 리스팅 시 매 요청마다 `iterdir()` + `stat()` 시스템 콜이 발생하여 수백 밀리초의 지연이 관측되었다. 이를 해결하기 위해 인메모리 TTL 캐시를 도입하였다.

**구현 위치**: `backend/app/files/service.py`

```python
# TTL cache: {real_path_str: (timestamp, [FileItem, ...])}
_dir_cache: dict[str, tuple[float, list[FileItem]]] = {}
_CACHE_TTL = 30  # seconds

# TTL cache for directory sizes: {path_str: (timestamp, size_bytes)}
_size_cache: dict[str, tuple[float, int]] = {}
_SIZE_CACHE_TTL = 60  # seconds
```

| 항목 | 설정값 | 설명 |
|------|--------|------|
| `_dir_cache` | TTL 30초 | 디렉토리 파일 목록 캐시 |
| `_size_cache` | TTL 60초 | 디렉토리 크기 계산 캐시 |
| 캐시 키 | `str(real_path.resolve())` | 절대 경로 문자열 |
| 시간 기준 | `time.monotonic()` | 시스템 시계 변경에 영향받지 않음 |

**캐시 조회 로직** (`list_directory()`):

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

#### 10.1.2 캐시 무효화

쓰기 작업(upload, delete, rename, move, mkdir) 수행 후 반드시 `invalidate_cache()`를 호출하여 해당 디렉토리의 캐시를 즉시 제거한다.

```python
def invalidate_cache(real_path: Path) -> None:
    key = str(real_path.resolve())
    _dir_cache.pop(key, None)
    _size_cache.clear()
```

**호출 위치** (`backend/app/files/router.py`):

| 작업 | 무효화 대상 |
|------|-------------|
| `upload_file()` | `fs.invalidate_cache(real_dir)` |
| `delete_file()` | `fs.invalidate_cache(real.parent)` |
| `rename_file()` | `fs.invalidate_cache(real.parent)` |
| `move_file()` | `fs.invalidate_cache(src_real.parent)` + `fs.invalidate_cache(dst_real)` |
| `mkdir()` | `fs.invalidate_cache(parent_real)` |

> **참고**: `_size_cache`는 부모 디렉토리가 영향을 받을 수 있으므로 쓰기 작업 시 전체를 클리어한다 (`_size_cache.clear()`).

#### 10.1.3 비동기 래핑

NFS I/O가 블로킹 호출이므로 FastAPI의 async 이벤트 루프를 차단하지 않도록 `asyncio.to_thread()`로 래핑하였다.

```python
# backend/app/files/router.py
items = await asyncio.to_thread(fs.list_directory, real, vp)
```

스토리지 정보 조회에도 동일하게 적용:

```python
personal, shared = await asyncio.gather(
    asyncio.to_thread(fs.get_dir_size, personal_path),
    asyncio.to_thread(fs.get_dir_size, shared_path),
)
```

#### 10.1.4 NFS 환경 최적화 효과

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| 디렉토리 리스팅 응답 | 200~500ms (NFS I/O) | <5ms (캐시 히트) |
| 이벤트 루프 차단 | 발생 | 없음 (`to_thread`) |
| 동시 요청 처리 | I/O 대기 중 차단 | 논블로킹 병렬 처리 |
| 캐시 일관성 | N/A | 쓰기 시 즉시 무효화 |

### 10.2 대시보드 서비스 카드 변경

#### 10.2.1 SERVICE_DEFS 변경사항

**구현 위치**: `backend/app/services/health.py`

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
        "name": "화상회의 (BBB)",
        "health_url": "https://meet.namgun.or.kr/bigbluebutton/api",
        "external_url": None,
        "internal_only": True,
    },
]
```

#### 10.2.2 변경 상세

| 서비스 | 변경 전 | 변경 후 | 사유 |
|--------|---------|---------|------|
| Stalwart Mail | `internal_only: False` | `internal_only: True` | 포털 내 iframe 통합 (`/mail` 페이지) |
| Pi-Hole | SERVICE_DEFS에 존재 | **제거** | 내부 DNS 서버, 대시보드 노출 불필요 |
| RustDesk | `health_url` (HTTP) | `health_tcp: "192.168.0.50:21114"` | RustDesk API 서버가 HTTP 헬스 엔드포인트를 제공하지 않음 |
| 화상회의 (BBB) | 없음 | **추가** | BigBlueButton 3.0 통합 |
| Gitea | `external_url` 일반 URL | OAuth 직접 트리거 URL | SSO 통합 (Phase 6) |

#### 10.2.3 TCP 헬스체크 구현

RustDesk의 경우 HTTP 엔드포인트 대신 TCP 포트 연결을 시도하는 방식으로 헬스체크를 수행한다.

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

#### 10.2.4 ServiceStatus 스키마

```python
class ServiceStatus(BaseModel):
    name: str
    url: str | None       # external URL (None for internal_only display)
    status: str           # "ok" | "down" | "checking"
    response_ms: int | None
    internal_only: bool
```

`internal_only: True`인 서비스는 대시보드에서 외부 링크 대신 포털 내부 페이지로 연결된다.

### 10.3 BigBlueButton 화상회의 통합

#### 10.3.1 아키텍처

```
[포털 프론트엔드] → /api/meetings/*
    → [FastAPI Backend] → BBB API (SHA256 checksum)
        → [BBB 3.0 서버] 192.168.0.249 (meet.namgun.or.kr)
```

#### 10.3.2 BBB API 클라이언트

**구현 위치**: `backend/app/meetings/bbb.py`

**SHA256 체크섬 생성:**

BBB API는 모든 요청에 `checksum` 파라미터를 요구한다. 체크섬은 `SHA256(method + queryString + sharedSecret)` 방식으로 생성된다.

```python
def _checksum(method: str, query_string: str) -> str:
    raw = f"{method}{query_string}{settings.bbb_secret}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

**URL 빌드:**

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

**XML 파싱:**

BBB API는 XML 응답을 반환하므로 재귀적으로 dict로 변환한다. 동일 태그가 반복되는 경우(예: 여러 `<attendee>`) 자동으로 리스트로 변환된다.

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

**API 메서드:**

| 함수 | BBB API | 설명 |
|------|---------|------|
| `get_meetings()` | `getMeetings` | 활성 회의 목록 |
| `get_meeting_info(meeting_id)` | `getMeetingInfo` | 회의 상세 정보 |
| `create_meeting(name, ...)` | `create` | 회의 생성 |
| `get_join_url(meeting_id, full_name, ...)` | `join` | 참가 URL 생성 |
| `end_meeting(meeting_id)` | `end` | 회의 종료 |
| `get_recordings(meeting_id?)` | `getRecordings` | 녹화 목록 |
| `delete_recording(record_id)` | `deleteRecordings` | 녹화 삭제 |

`create_meeting()` 파라미터:

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

- `meeting_id`가 None이면 `uuid.uuid4()`로 자동 생성
- `moderator_pw`/`attendee_pw`가 None이면 `mod-<hex8>`/`att-<hex8>` 형식으로 자동 생성

#### 10.3.3 API 엔드포인트

**구현 위치**: `backend/app/meetings/router.py`

| 메서드 | 경로 | 설명 | 인증 | 권한 |
|--------|------|------|------|------|
| GET | `/api/meetings/` | 활성 회의 목록 | 필수 | 전체 |
| GET | `/api/meetings/{meeting_id}` | 회의 상세 정보 | 필수 | 전체 |
| POST | `/api/meetings/` | 회의 생성 | 필수 | 전체 |
| POST | `/api/meetings/{meeting_id}/join` | 참가 URL 생성 | 필수 | 전체 |
| POST | `/api/meetings/{meeting_id}/end` | 회의 종료 | 필수 | **admin** |
| GET | `/api/meetings/recordings` | 녹화 목록 | 필수 | 전체 |
| DELETE | `/api/meetings/recordings/{record_id}` | 녹화 삭제 | 필수 | **admin** |

> **참고**: `join` 엔드포인트에서 `user.is_admin`이면 `MODERATOR` 역할, 아니면 `VIEWER` 역할로 참가한다.

#### 라우터 등록

```python
# backend/app/main.py
from app.meetings.router import router as meetings_router
app.include_router(meetings_router)
```

#### 10.3.4 Pydantic 스키마

**구현 위치**: `backend/app/meetings/schemas.py`

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

#### 10.3.5 프론트엔드 컴포넌트

**Composable: `useMeetings.ts`**

**위치**: `frontend/composables/useMeetings.ts`

모듈 레벨 싱글톤 상태를 사용하여 전체 앱에서 회의 상태를 공유한다.

```typescript
const meetings = ref<Meeting[]>([])
const selectedMeeting = ref<MeetingDetail | null>(null)
const recordings = ref<Recording[]>([])
const loadingMeetings = ref(false)
const loadingDetail = ref(false)
const loadingRecordings = ref(false)
const showCreateModal = ref(false)
```

제공 함수:

| 함수 | 설명 |
|------|------|
| `fetchMeetings()` | `GET /api/meetings/` 호출 |
| `fetchMeetingDetail(id)` | `GET /api/meetings/{id}` 호출 |
| `createMeeting(data)` | `POST /api/meetings/` 호출 후 목록 새로고침 |
| `joinMeeting(id)` | `POST /api/meetings/{id}/join` → 새 탭에서 참가 URL 열기 |
| `endMeeting(id)` | `POST /api/meetings/{id}/end` 호출 후 목록 새로고침 |
| `fetchRecordings(meetingId?)` | `GET /api/meetings/recordings` 호출 |
| `deleteRecording(id)` | `DELETE /api/meetings/recordings/{id}` 호출 후 목록 새로고침 |
| `clearSelectedMeeting()` | 선택된 회의 초기화 |

**페이지: `meetings.vue`**

**위치**: `frontend/pages/meetings.vue`

2개의 탭(회의/녹화)으로 구성되며, 회의 탭에서는 그리드 뷰와 상세 패널을 동시에 표시한다.

**컴포넌트 목록:**

| 컴포넌트 | 위치 | 설명 |
|----------|------|------|
| `MeetingCard.vue` | `frontend/components/meetings/` | 회의 카드 (이름, 상태, 참가자 수, 참가/종료 버튼) |
| `MeetingDetail.vue` | `frontend/components/meetings/` | 회의 상세 패널 (참가자 목록, 음성/비디오 상태) |
| `CreateMeetingModal.vue` | `frontend/components/meetings/` | 회의 생성 모달 (이름, 녹화, 시간 제한 등) |
| `RecordingList.vue` | `frontend/components/meetings/` | 녹화 목록 (재생, 삭제) |

#### 10.3.6 BBB 서버 설정

| 항목 | 값 |
|------|-----|
| 서버 IP | 192.168.0.249 |
| 도메인 | meet.namgun.or.kr |
| API 엔드포인트 | `https://meet.namgun.or.kr/bigbluebutton/api` |
| 버전 | BigBlueButton 3.0 |

백엔드 설정 (`backend/app/config.py`):

```python
bbb_url: str = "https://meet.namgun.or.kr/bigbluebutton/api"
bbb_secret: str = ""
```

### 10.4 Stalwart Mail 포털 내 통합

#### 10.4.1 `/mail` 페이지

**위치**: `frontend/pages/mail.vue`

Stalwart Mail의 웹 UI를 포털 내 네이티브 메일 클라이언트로 통합하였다. 3단 레이아웃(사이드바, 메일 리스트, 메일 뷰)으로 구성된다.

```
[MailSidebar] | [MailList] | [MailView]
              |            |
              | [MailCompose 모달]
```

#### 10.4.2 Nginx CSP 설정

Stalwart Mail 웹 UI를 포털 iframe에서 로드할 수 있도록 Nginx에 Content-Security-Policy 헤더를 설정하였다.

**설정 위치**: `mail.namgun.or.kr.conf` (192.168.0.150)

```nginx
# X-Frame-Options → CSP로 대체
add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
```

> **참고**: `X-Frame-Options: DENY`가 기존에 설정되어 있으면 CSP `frame-ancestors`와 충돌하므로 `X-Frame-Options` 헤더를 제거해야 한다.

#### 10.4.3 JMAP API 클라이언트

**구현 위치**: `backend/app/mail/jmap.py`

향후 네이티브 메일 클라이언트(iframe이 아닌 완전한 자체 UI) 전환을 대비하여 JMAP 클라이언트를 구현하였다.

**JMAP Account ID 해석:**

Stalwart의 Admin API principal ID와 JMAP account ID가 다르다. JMAP accountId는 `hex(principal_id + offset)` 형식이며, offset은 설치별로 다르다.

```python
async def _discover_jmap_offset(client) -> int:
    """Discover the offset between admin API principal IDs and JMAP account IDs."""
    # offset 0~29 범위를 스캔하여 실제 데이터가 있는 계정 발견
    ...
```

**제공 API:**

| 함수 | JMAP 메서드 | 설명 |
|------|-------------|------|
| `get_session()` | `/.well-known/jmap` | 세션 정보 |
| `resolve_account_id(email)` | Admin API + JMAP | 이메일 → JMAP account ID 변환 |
| `get_mailboxes(account_id)` | `Mailbox/get` | 메일박스 목록 |
| `get_messages(account_id, mailbox_id, ...)` | `Email/query` + `Email/get` | 메일 목록 |
| `get_message(account_id, message_id)` | `Email/get` (full) | 메일 상세 |
| `update_message(account_id, message_id, ...)` | `Email/set` (update) | 읽음/별표/이동 |
| `destroy_message(account_id, message_id)` | `Email/set` (destroy) | 메일 삭제 |
| `send_message(account_id, ...)` | `Email/set` + `EmailSubmission/set` | 메일 발송 |
| `download_blob(account_id, blob_id)` | `/jmap/download/...` | 첨부파일 다운로드 |

**Mail API 엔드포인트:**

**구현 위치**: `backend/app/mail/router.py`

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/mail/mailboxes` | 메일박스 목록 (역할별 정렬) |
| GET | `/api/mail/messages` | 메일 목록 (페이지네이션) |
| GET | `/api/mail/messages/{id}` | 메일 상세 (자동 읽음 처리) |
| PATCH | `/api/mail/messages/{id}` | 읽음/별표/이동 |
| DELETE | `/api/mail/messages/{id}` | 삭제 (휴지통 → 영구 삭제) |
| POST | `/api/mail/send` | 메일 발송 |
| GET | `/api/mail/blob/{blob_id}` | 첨부파일 다운로드 프록시 |

### 10.5 네비게이션 추가

**구현 위치**: `frontend/components/layout/AppHeader.vue`

데스크톱/모바일 네비게이션에 메일과 회의 링크를 추가하였다.

```html
<!-- Desktop nav -->
<nav v-if="user" class="hidden sm:flex items-center gap-1">
  <NuxtLink to="/">대시보드</NuxtLink>
  <NuxtLink to="/files">파일</NuxtLink>
  <NuxtLink to="/mail">메일</NuxtLink>
  <NuxtLink to="/meetings">회의</NuxtLink>
</nav>
```

AppHeader 네비게이션 메뉴:

| 메뉴 | 경로 | 설명 |
|------|------|------|
| 대시보드 | `/` | 서비스 상태 대시보드 |
| 파일 | `/files` | 파일 브라우저 |
| 메일 | `/mail` | Stalwart Mail iframe |
| 회의 | `/meetings` | BBB 회의 관리 |

모바일 반응형 네비게이션 (햄버거 메뉴) 포함.

---

## 11. Phase 6: 네이티브 로그인 및 SSO 통합 (완료)

Authentik 리다이렉트 방식의 로그인을 네이티브 로그인 폼으로 대체하고, Popup Bridge 패턴을 통해 SSO 쿠키를 설정하며, Gitea 연동 SSO를 구현하였다.

### 11.1 네이티브 로그인 아키텍처

#### 11.1.1 개요

기존에는 사용자가 로그인 시 Authentik UI로 리다이렉트되어 Authentik 자체의 로그인 폼을 사용하였다. Phase 6에서는 Authentik UI를 완전히 대체하여 포털 자체의 로그인 폼(`/login`)에서 사용자명과 비밀번호를 입력하고, 백그라운드에서 Authentik Flow Executor API를 통해 인증을 수행하는 "네이티브 로그인" 방식을 구현하였다.

```
[사용자] → 포털 /login 페이지 (네이티브 로그인 폼)
    → [팝업] auth.namgun.or.kr/portal-bridge/ (브릿지 페이지)
        → Authentik Flow Executor API (same-origin)
        → OAuth authorize → callback → code 추출
    → [postMessage] code를 포털에 전달
    → [포털 Backend] POST /api/auth/native-callback
        → Authentik Token 교환 → 세션 쿠키 발급
```

#### 11.1.2 네이티브 로그인 폼

- **페이지**: `/login` (auth 레이아웃)
- **입력 필드**: 사용자명/이메일, 비밀번호
- **리다이렉트 파라미터**: `?redirect=<URL>` 쿼리 파라미터 지원 (외부 서비스 SSO용)
- **보안**: `namgun.or.kr` 도메인 또는 상대 경로만 리다이렉트 허용

### 11.2 Popup Bridge 패턴

기존 Authentik 전체 화면 리다이렉트 방식은 UX가 좋지 않고, iframe 방식은 third-party cookie partitioning(브라우저 보안 정책)으로 인해 SSO 쿠키가 설정되지 않는 문제가 있었다. 이를 해결하기 위해 Popup Bridge 패턴을 도입하였다.

#### 11.2.1 왜 팝업 브릿지 패턴인가

**iframe의 한계:**

모던 브라우저(Chrome 120+, Firefox 118+, Safari 17+)는 **third-party cookie partitioning**을 적용한다. iframe 내의 `auth.namgun.or.kr`에서 설정된 쿠키는 top-level context(`namgun.or.kr`)와 파티셔닝되어 별도의 쿠키 저장소를 사용한다. 이로 인해:

1. iframe 내에서 Authentik에 로그인하더라도 SSO 세션 쿠키(`authentik_session`)가 다른 서비스(Gitea 등)의 OAuth 리다이렉트에서 인식되지 않는다.
2. Authentik의 CSRF 보호가 쿠키 불일치로 실패할 수 있다.

**팝업의 장점:**

팝업은 **top-level browsing context**로 취급된다. 따라서:

1. `auth.namgun.or.kr`에서 설정하는 쿠키가 **first-party cookie**로 저장된다.
2. Authentik의 `authentik_session` 쿠키가 정상적으로 설정되어 SSO가 작동한다.
3. `window.opener.postMessage()`를 통해 포털과 안전하게 통신할 수 있다.

#### 11.2.2 플로우

1. 사용자가 `/login` 페이지에서 사용자명/비밀번호 입력 후 제출
2. 브라우저가 `https://auth.namgun.or.kr/portal-bridge/` 팝업을 동기적으로 열림 (팝업 차단기 회피)
3. Bridge 페이지가 `portal-bridge-ready` postMessage 전송
4. 포털이 OIDC config 조회 + PKCE 생성 후 `portal-login` 메시지를 팝업에 전송
5. Bridge가 Authentik Flow Executor API를 호출하여 인증 (단계별 stage 처리)
6. 인증 완료 후 `authorize` 엔드포인트 호출 → `code` 획득
7. Bridge가 `portal-login-result` 메시지로 코드를 포털에 전달
8. 포털 백엔드가 `/api/auth/native-callback`에서 코드를 토큰으로 교환, 세션 쿠키 발급

### 11.3 브릿지 페이지 구성

브릿지 페이지는 Nginx VM(192.168.0.150)의 `auth.namgun.or.kr` 도메인에 배치된다. Authentik과 same-origin이므로 CORS 문제 없이 API를 호출할 수 있다.

#### 11.3.1 브릿지 메인 페이지

**위치**: `/var/www/portal-bridge/index.html` (192.168.0.150)

역할:
1. 포털로부터 `portal-login` 메시지 수신
2. Authentik Flow Executor API를 통한 인증 단계 수행
3. 인증 완료 후 OAuth authorize를 **페이지 네비게이션으로** 호출하여 SSO 쿠키를 확실히 설정
4. callback 페이지로 리다이렉트

#### 11.3.2 콜백 페이지

**위치**: `/var/www/portal-bridge/callback` (확장자 없음, 192.168.0.150)

역할:
1. URL에서 `code`와 `state` 파라미터 추출
2. `window.opener.postMessage()`로 포털에 코드 전달

> **주의**: 파일에 확장자가 없으므로 Nginx에서 `default_type text/html;`을 설정해야 한다.

#### 11.3.3 Nginx 설정

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

Rocky Linux 10에서 Nginx가 파일에 접근하려면 SELinux 컨텍스트가 올바르게 설정되어야 한다.

```bash
semanage fcontext -a -t httpd_sys_content_t "/var/www/portal-bridge(/.*)?"
restorecon -Rv /var/www/portal-bridge/
```

### 11.4 Authentik Flow Executor API 상세

브릿지 페이지에서 수행하는 인증 흐름의 전체 단계는 다음과 같다.

#### 단계 1: OAuth pending authorization 등록

```javascript
await fetch("/application/o/authorize/?" + oauthParams, {
    redirect: "manual"
});
```

`redirect: "manual"`로 호출하여 실제 리다이렉트를 따라가지 않고, Authentik 내부에 pending authorization을 등록만 한다. 이 시점에서 status는 0(opaque redirect)이 된다.

#### 단계 2: Flow Executor 시작

```javascript
const flowUrl = `/api/v3/flows/executor/${flowSlug}/?query=${encodeURIComponent(oauthParams)}`;
const resp = await fetch(flowUrl, {
    headers: { "Accept": "application/json" }
});
const challenge = await resp.json();
```

> **핵심**: `query` 파라미터에 OAuth 파라미터를 전달할 때 반드시 `encodeURIComponent()`를 적용해야 한다. 그렇지 않으면 `&`가 URL 분리자로 해석되어 파라미터가 누락된다.

#### 단계 3: ak-stage-identification (사용자 식별)

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

#### 단계 4: xak-flow-redirect (중간 리다이렉트)

Authentik이 mid-flow redirect를 보내는 경우 해당 URL을 따라간다.

```javascript
// challenge.component === "xak-flow-redirect"
// challenge.to가 상대 경로인 경우 해당 경로로 GET 요청
```

#### 단계 5: ak-stage-password (비밀번호 전송)

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

#### 단계 6: 플로우 완료 — `xak-flow-redirect to="/"`

비밀번호 인증이 성공하면 Authentik은 `component: "xak-flow-redirect"`, `to: "/"` 응답을 반환한다. 이는 플로우가 완료되었음을 의미하지만, Authentik이 OAuth context를 찾지 못하여 홈으로 리다이렉트하려는 것이다.

> **핵심 문제**: Flow Executor가 JSON API로 호출되었기 때문에, 플로우 완료 시점에서 Authentik은 OAuth pending authorization을 자동으로 처리하지 못한다.

#### 단계 7: authorize 재호출 (페이지 네비게이션)

```javascript
// 플로우 완료 후, OAuth authorize를 페이지 네비게이션으로 호출
// fetch()가 아닌 window.location 변경으로 실행
window.location.href = "/application/o/authorize/?" + oauthParams;
```

이렇게 하면:
1. SSO 세션 쿠키(`authentik_session`)가 **확실하게** 설정된다 (top-level navigation이므로).
2. Authentik이 이미 인증된 세션을 인식하고 OAuth code를 발급한다.
3. `redirect_uri`(`/portal-bridge/callback`)로 리다이렉트된다.

#### 단계 8: callback에서 code 추출

```javascript
// /portal-bridge/callback 페이지
const params = new URLSearchParams(window.location.search);
const code = params.get("code");
window.opener.postMessage({
    type: "portal-login-result",
    success: true,
    code: code
}, "https://namgun.or.kr");
```

### 11.5 PKCE (S256) 구현

#### 11.5.1 클라이언트 사이드 (Web Crypto API)

**구현 위치**: `frontend/composables/useAuth.ts`

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

- `code_verifier`: 64바이트 랜덤 → base64url
- `code_challenge`: SHA-256(code_verifier) → base64url
- `crypto.getRandomValues()` + `crypto.subtle.digest('SHA-256', ...)` 사용
- 브라우저 측에서 PKCE 쌍 생성 후 `code_verifier`를 팝업에 전달하지 않고 포털에서 보관

#### 11.5.2 서버 사이드 (기존 redirect 방식 유지)

**구현 위치**: `backend/app/auth/oidc.py`

```python
def generate_pkce() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge
```

PKCE 방식:
- `code_challenge_method`: `S256`
- `code_verifier`: 클라이언트에서 생성, 토큰 교환 시 전송
- `code_challenge`: `BASE64URL(SHA256(code_verifier))`

### 11.6 Backend 변경사항

#### 11.6.1 `POST /api/auth/native-callback`

**구현 위치**: `backend/app/auth/router.py`

브릿지 콜백에서 전달된 authorization code를 Authentik에서 토큰으로 교환하고, 사용자 정보를 조회하여 세션 쿠키를 발급한다.

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

    # Upsert user (callback과 동일 로직)
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

핵심 차이점:
- `redirect_uri`에 `settings.bridge_redirect_uri`를 전달 (기존 callback URL이 아닌 bridge callback URL)
- 응답이 `JSONResponse`이며, 리다이렉트가 아님

#### 11.6.2 `GET /api/auth/oidc-config`

브라우저에서 PKCE 파라미터 생성에 필요한 공개 설정을 반환한다.

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

Authentik end-session 호출을 제거하고, 포털 세션 쿠키만 클리어한다.

```python
@router.post("/logout")
async def logout():
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
```

> **사유**: 네이티브 로그인 방식에서는 Authentik 세션 쿠키의 유지가 SSO에 필수적이므로, 포털 로그아웃 시 Authentik 세션을 종료하지 않는다. Authentik 세션은 자연 만료되거나, 사용자가 Authentik 관리 UI에서 직접 종료할 수 있다.

#### 11.6.4 `exchange_code()` 변경

선택적 `redirect_uri` 파라미터를 추가하여 네이티브 콜백과 기존 콜백에서 모두 사용할 수 있도록 하였다.

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

#### 11.6.5 `NativeCallbackRequest` 스키마

**구현 위치**: `backend/app/auth/schemas.py`

```python
class NativeCallbackRequest(BaseModel):
    code: str
    code_verifier: str
```

#### 11.6.6 `config.py` 설정 추가

```python
# Authentik Native Login
authentik_flow_slug: str = "default-authentication-flow"
bridge_redirect_uri: str = "https://auth.namgun.or.kr/portal-bridge/callback"
```

#### 11.6.7 백엔드 엔드포인트 종합

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/auth/login` | GET | OIDC 리다이렉트 (레거시, PKCE 쿠키 설정) |
| `/api/auth/callback` | GET | OIDC 콜백 (레거시, 코드 교환 + 세션 설정) |
| `/api/auth/oidc-config` | GET | 공개 OIDC 설정 반환 (client_id, redirect_uri, scope, flow_slug) |
| `/api/auth/native-callback` | POST | 네이티브 로그인 코드 교환 (code + code_verifier → 세션 쿠키) |
| `/api/auth/me` | GET | 현재 인증 사용자 정보 |
| `/api/auth/logout` | POST | 세션 쿠키 삭제 |

### 11.7 Frontend 변경사항

#### 11.7.1 `useAuth.ts` — `nativeLogin()` 함수

**구현 위치**: `frontend/composables/useAuth.ts`

기존 `login()` 함수(Authentik UI로 리다이렉트)를 `nativeLogin()` 함수(팝업 브릿지 방식)로 대체하였다.

```typescript
const BRIDGE_URL = 'https://auth.namgun.or.kr/portal-bridge/'
const BRIDGE_ORIGIN = 'https://auth.namgun.or.kr'
const BRIDGE_CALLBACK = 'https://auth.namgun.or.kr/portal-bridge/callback'
```

`nativeLogin()` 함수 흐름:

1. **bridge-ready 리스너 등록** (팝업 열기 전)
2. **팝업 동기적 열기** (`window.open()` — await 이전에 실행하여 팝업 차단 회피)
3. **bridge-ready 대기 + OIDC 설정 fetch** (Promise.all 병렬)
4. **PKCE 생성** (code_verifier, code_challenge, state)
5. **팝업에 credentials 전송** (`popup.postMessage()`)
6. **결과 대기** (portal-login-result 메시지)
7. **code 교환** (`POST /api/auth/native-callback`)
8. **사용자 정보 fetch** (`GET /api/auth/me`)

```typescript
const nativeLogin = async (username: string, password: string): Promise<void> => {
    // 1. 리스너 설정 (팝업 열기 전 — race condition 방지)
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

    // 2. 팝업 동기적 열기 (await 전)
    const popup = window.open(BRIDGE_URL, '_portal_auth', 'width=1,height=1,left=-100,top=-100')
    if (!popup) throw new Error('팝업이 차단되었습니다.')

    try {
        // 3~8. 인증 흐름...
    } finally {
        popup.close()
    }
}
```

> **참고**: 팝업 크기를 1x1로 설정하고 화면 밖에 배치하여 사용자에게 보이지 않도록 한다.

#### 11.7.2 `login.vue` — 네이티브 로그인 폼

**구현 위치**: `frontend/pages/login.vue`

- `layout: 'auth'` (전체 화면 중앙 정렬)
- 사용자명/이메일 + 비밀번호 입력 폼
- `redirect` 쿼리 파라미터 지원 (로그인 후 원래 페이지로 이동)
- 에러 메시지 한국어 표시 (인증 실패, 타임아웃 등)

```typescript
const redirectTo = computed(() => {
    const r = route.query.redirect as string | undefined
    // 도메인 검증: namgun.or.kr 도메인의 https URL만 허용
    if (r && (r.startsWith('https://') && r.includes('.namgun.or.kr'))) return r
    return '/'
})
```

### 11.8 SSO 쿠키 메커니즘

#### 11.8.1 `authentik_session` 쿠키 특성

| 속성 | 값 | 설명 |
|------|-----|------|
| Domain | `auth.namgun.or.kr` | Authentik 도메인 |
| SameSite | `None` | cross-origin 요청에서도 전송 |
| Secure | `true` | HTTPS만 |
| HttpOnly | `true` | JavaScript 접근 불가 |
| Path | `/` | 전체 경로 |

#### 11.8.2 팝업에서의 SSO 쿠키 설정

```
[팝업] = top-level browsing context
    ↓
[auth.namgun.or.kr] = first-party
    ↓
authentik_session 쿠키 = first-party cookie로 저장
    ↓
[Gitea OAuth redirect] → auth.namgun.or.kr
    ↓
authentik_session 쿠키 = 자동 전송 → 자동 인증
```

#### 11.8.3 fetch() vs 페이지 네비게이션

| 방식 | 쿠키 설정 | SSO 지원 |
|------|-----------|----------|
| `fetch()` (JSON API) | credentials 설정에 따라 다름, 불확실 | 불안정 |
| 페이지 네비게이션 (`window.location`) | 브라우저 기본 동작으로 확실하게 설정 | 안정적 |

따라서 브릿지의 마지막 authorize 호출은 반드시 **페이지 네비게이션**으로 실행한다.

### 11.9 Gitea SSO 연동

#### 11.9.1 Nginx 리다이렉트 설정

**설정 위치**: `git.namgun.or.kr.conf` (192.168.0.150)

```nginx
location = /user/login {
    return 302 https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik;
}
```

- 사용자가 `git.namgun.or.kr/user/login`에 접근하면 포털 로그인 페이지로 리다이렉트
- 로그인 완료 후 Gitea의 OAuth2 엔드포인트로 리다이렉트
- Authentik 세션 쿠키가 이미 설정되어 있으므로 자동 인증

#### 11.9.2 Gitea app.ini 설정

```ini
[service]
ENABLE_BASIC_AUTHENTICATION = true  ; git push 인증용
ENABLE_OPENID_SIGNIN = false        ; OpenID 로그인 비활성화
```

> **주의**: `ENABLE_BASIC_AUTHENTICATION = false`로 설정하면 git push 시 HTTPS 인증이 실패한다. Nginx가 웹 로그인은 이미 포털로 redirect하므로, 기본 인증은 활성화 상태로 유지해야 한다.

#### 11.9.3 대시보드 external_url

```python
# SERVICE_DEFS에서 Gitea의 external_url
"external_url": "https://git.namgun.or.kr/user/oauth2/authentik",
```

대시보드 서비스 카드에서 Gitea 클릭 시 OAuth2 엔드포인트를 직접 트리거하여, Authentik 세션이 있으면 자동으로 Gitea에 로그인된다.

#### 11.9.4 로그인 리다이렉트 파라미터

```
https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik
```

- 외부 서비스에서 포털 로그인 페이지로 보낼 때 `redirect` 쿼리 파라미터 사용
- 로그인 완료 후 해당 URL로 자동 이동
- 보안: `https://` + `.namgun.or.kr` 도메인 또는 `/` 상대 경로만 허용

### 11.10 Authentik 설정

#### 11.10.1 OAuth2 Provider redirect_uris

브릿지 콜백 URL을 redirect_uris에 추가:

```
https://auth.namgun.or.kr/portal-bridge/callback
```

기존 redirect_uri도 유지 (redirect 방식 로그인 fallback):

```
https://namgun.or.kr/api/auth/callback
```

#### 11.10.2 Authorization Flow

```
default-provider-authorization-implicit-consent
```

동의 화면 없이 즉시 인가 코드를 발급한다. 내부 포털이므로 매번 동의를 요구할 필요가 없다.

#### 11.10.3 Authentication Flow

```
default-authentication-flow
```

Authentik 기본 인증 플로우를 사용한다. 이 플로우의 slug가 `config.py`의 `authentik_flow_slug` 설정과 일치해야 한다.

---

## 12. 트러블슈팅 종합

전 Phase에 걸쳐 발생한 모든 트러블슈팅 항목을 통합하여 정리한다. 중복 항목은 가장 상세한 버전을 유지하였다.

### Phase 0: 인프라

| # | 문제 | 원인 | 해결 방법 |
|---|------|------|----------|
| 1 | Authentik 최초 로그인 실패 | BOOTSTRAP_PASSWORD에 `==` 등 특수문자 포함 | 단순 영숫자 비밀번호 사용 |
| 2 | Authentik 반복 로그인 차단 | reputation score 누적 | `Reputation` 테이블 초기화 |
| 3 | Windows Server DNS TXT 레코드 저장 실패 | 255자 초과 TXT 레코드 제한 | 하나의 레코드를 여러 문자열로 분할 |

### Phase 1: SSO PoC

| # | 문제 | 원인 | 해결 방법 |
|---|------|------|----------|
| 4 | Gitea CLI 실행 시 권한 오류 | root 사용자로 실행 | `--user git` 옵션으로 git 사용자 지정 |

### Phase 2: 메일 마이그레이션

| # | 문제 | 원인 | 해결 방법 |
|---|------|------|----------|
| 5 | Stalwart v0.15에서 LDAP 인증 실패 — Password verification failed | `bind.auth.enable = true`는 구 문법(v0.13). 기본값이 password hash 비교 모드로 동작하며, Authentik은 userPassword 해시를 노출하지 않음 | `directory.ldap.bind.auth.method = "lookup"` 설정. search-then-bind 방식으로 LDAP 서버에 직접 bind 인증 위임 |
| 6 | session.auth.directory expression 설정 불가 — `session.auth.directory`에 문자열 `'ldap'` 저장 후에도 평가값이 `"*"` (기본 디렉토리) | Expression 필드의 우선순위 문제. DB 설정이 내장 기본값을 오버라이드하지 못함 | `storage.directory = "ldap"`로 전역 디렉토리를 LDAP으로 변경. 내부 계정은 internal 디렉토리에 별도 유지 |
| 7 | Stalwart DKIM 서명 키 인식 실패 — `dkim.signer-not-found: rsa-namgun.or.kr` 경고 | Stalwart 기본 DKIM 설정이 `{algorithm}-{domain}` 네이밍 규칙 사용. 수동 생성한 `dkim-namgun` 이름과 불일치 | config.toml에 `[signature."rsa-namgun.or.kr"]` 섹션으로 서명 정의. `ed25519-namgun.or.kr`은 미사용 경고(무시 가능) |
| 8 | rootless Podman에서 호스트 LAN IP 접근 불안정 — Stalwart 컨테이너에서 LAN IP(192.168.0.50)의 LDAP Outpost 접근 불가 | Rootless Podman의 slirp4netns 네트워크에서 호스트 LAN 접근이 불안정 | LDAP Outpost를 메일서버 VM에 사이드카로 배포. `network_mode: host`로 localhost 통신. WSL2의 LDAP Outpost 제거 |
| 9 | DNS DKIM 공개키 잘림 — Gmail에서 `dkim=neutral (invalid public key)` | Windows Server DNS의 TXT 레코드 255자 제한으로 2048-bit RSA 공개키(410자) 잘림 | TXT 레코드를 두 개 문자열로 분할 등록 (첫 255자 + 나머지 155자) |

### Phase 3: 포털 코어

| # | 문제 | 원인 | 해결 방법 |
|---|------|------|----------|
| 10 | PostgreSQL bind mount 실패 | WSL2 환경에서 NTFS(/mnt/d/) 파일시스템 권한 문제 | Docker named volume (`portal-db-data`) 사용 |
| 11 | NFS v4.2 마운트 실패 | WSL2 커널(5.15.x)이 NFS v4.2를 지원하지 않음 | `nfsvers=4` (v4.1) 사용 |

### Phase 6: 네이티브 로그인 및 SSO

| # | 문제 | 원인 | 해결 방법 |
|---|------|------|----------|
| 12 | fetch()의 cross-origin redirect hang — 포털에서 Authentik authorize 호출 시 응답이 돌아오지 않고 hang | `fetch()`가 cross-origin redirect를 따라가면서, Authentik이 로그인 페이지로 302 redirect를 반환하고, opaque redirect 체인이 형성되어 브라우저가 요청을 블록 | `redirect_uri`를 `auth.namgun.or.kr/portal-bridge/callback` (same-origin)으로 변경하여, Authentik API 호출이 same-origin에서 수행되도록 브릿지 아키텍처 도입 |
| 13 | opaque redirect loop — fetch authorize 호출 시 `response.status === 0`이 되어 Location 헤더에서 code 추출 불가 | `redirect: "manual"` 옵션은 cross-origin redirect에서 opaque redirect response를 반환. 이 응답에서는 status, headers 등 모든 정보가 숨겨짐 | same-origin redirect_uri 사용 + authorize를 fetch가 아닌 **페이지 네비게이션**(`window.location`)으로 호출. code는 callback 페이지에서 `URLSearchParams`로 추출 |
| 14 | OAuth 파라미터 인코딩 누락 — Flow Executor API 호출 시 `client_id` 이후 파라미터 누락 | OAuth 파라미터 문자열의 `&`가 Flow Executor URL의 쿼리 파라미터 분리자로 해석되어, `query` 파라미터의 값이 첫 번째 `&` 이전까지만 전달됨 | `encodeURIComponent(oauthParams)` 적용 |
| 15 | Authentik 플로우 완료 후 `to: "/"` 응답 — 비밀번호 인증 성공 후 OAuth code가 발급되지 않음 | Flow Executor를 JSON API로 호출하면, 플로우 완료 시 Authentik이 OAuth pending authorization context를 찾지 못함. JSON API 세션과 OAuth authorize 세션이 분리 | 플로우 완료(`to: "/"`) 확인 후, OAuth authorize를 **직접 재호출**. Authentik은 이미 인증된 세션을 인식하고, implicit consent로 즉시 code 발급 |
| 16 | iframe에서 Authentik 쿠키 미설정 — `authentik_session` 쿠키가 다른 서비스의 OAuth redirect에서 인식되지 않음 | Chrome 120+, Firefox 118+, Safari 17+의 **cookie partitioning** (CHIPS, Storage Partitioning) 정책. iframe 내의 third-party 쿠키는 (top-level-origin, embedded-origin) 쌍으로 파티셔닝 | iframe 대신 **popup** 방식으로 전환. 팝업은 top-level browsing context이므로 쿠키가 first-party로 설정 |
| 17 | popup-portal race condition — 간헐적으로 Bridge load timeout 에러 | 팝업을 열고 `await`하는 사이에 팝업이 이미 로드 완료되어 `postMessage()` 전송. 포털에서는 이후에 `addEventListener` 호출하여 메시지를 놓침 | **메시지 리스너를 팝업 열기 전에 설정**하여, 팝업의 ready 메시지를 반드시 수신 |
| 18 | callback 파일 content-type — `/portal-bridge/callback` 접근 시 브라우저가 파일 다운로드 시도 | `callback` 파일에 `.html` 확장자가 없어 Nginx가 `application/octet-stream`으로 MIME 타입 설정 | Nginx location 블록에 `default_type text/html;` 추가 |
| 19 | SSO 쿠키 미설정 — 네이티브 로그인 후 Gitea 접근 시 다시 로그인 요구 | 전체 인증 흐름을 `fetch()` JSON API로만 수행하면, `SameSite=None` + `Secure` 조합에서 쿠키가 불확실하게 설정됨 | 브릿지의 마지막 authorize 호출을 **페이지 네비게이션**(`window.location.href`)으로 실행하여 브라우저가 쿠키를 확실하게 설정 |
| 20 | Gitea 자동 로그인 안 됨 — 포털 로그인 후 Gitea 접근 시 자체 로그인 페이지 표시 | Gitea는 기본적으로 자체 로그인 페이지를 표시하며, OAuth 자동 리다이렉트 기능이 내장되어 있지 않음 | Nginx에서 Gitea `/user/login` 경로를 포털 로그인 페이지로 redirect. `redirect` 파라미터에 Gitea OAuth 엔드포인트 지정 |
| 21 | git push HTTP 인증 실패 — `git push` 시 `403 Forbidden` | `ENABLE_BASIC_AUTHENTICATION = false` 설정으로 인해 git CLI의 HTTP Basic 인증이 비활성화됨 | `ENABLE_BASIC_AUTHENTICATION = true`로 설정. Nginx가 웹 브라우저의 `/user/login`은 이미 포털로 redirect하므로, 기본 인증을 활성화해도 웹 로그인은 포털 경유 |

---

## 13. 수정 파일 목록

### 13.1 Backend

| 파일 경로 | 설명 |
|-----------|------|
| `backend/app/config.py` | `bbb_url`, `bbb_secret`, `authentik_flow_slug`, `bridge_redirect_uri` 설정 추가 |
| `backend/app/main.py` | `meetings_router`, `mail_router` 등록 |
| `backend/app/auth/router.py` | `native-callback`, `oidc-config` 엔드포인트 추가, `logout` 변경 |
| `backend/app/auth/oidc.py` | `exchange_code()` 선택적 `redirect_uri` 파라미터 추가 |
| `backend/app/auth/schemas.py` | `NativeCallbackRequest` 스키마 추가 |
| `backend/app/auth/deps.py` | 세션 인증 로직 (변경 없음, 참조용) |
| `backend/app/services/health.py` | `SERVICE_DEFS` 변경: Stalwart `internal_only`, Pi-Hole 제거, RustDesk TCP, BBB 추가 |
| `backend/app/services/schemas.py` | `ServiceStatus`에 `internal_only` 필드 (Phase 4에서 추가) |
| `backend/app/files/service.py` | `_dir_cache`, `_size_cache` TTL 캐시 추가, `invalidate_cache()` |
| `backend/app/files/router.py` | `asyncio.to_thread()` 래핑, 쓰기 작업 후 `invalidate_cache()` 호출 |
| `backend/app/mail/__init__.py` | 메일 모듈 초기화 |
| `backend/app/mail/jmap.py` | JMAP 클라이언트 (세션, 메일박스, 메시지 CRUD, 발송, 첨부파일) |
| `backend/app/mail/schemas.py` | 메일 API Pydantic 스키마 |
| `backend/app/mail/router.py` | 메일 API 엔드포인트 (메일박스, 메시지, 발송, 첨부파일 프록시) |
| `backend/app/meetings/__init__.py` | 회의 모듈 초기화 |
| `backend/app/meetings/bbb.py` | BBB API 클라이언트 (SHA256 checksum, XML 파싱) |
| `backend/app/meetings/schemas.py` | 회의 API Pydantic 스키마 |
| `backend/app/meetings/router.py` | 회의 API 엔드포인트 (CRUD, 참가, 녹화) |

### 13.2 Frontend

| 파일 경로 | 설명 |
|-----------|------|
| `frontend/composables/useAuth.ts` | `nativeLogin()` 함수, PKCE/bridge 상수 추가, `login()` 제거 |
| `frontend/composables/useMail.ts` | 메일 상태 관리 composable (메일박스, 메시지, 발송, 첨부파일) |
| `frontend/composables/useMeetings.ts` | 회의 상태 관리 composable (목록, 상세, 생성, 참가, 녹화) |
| `frontend/pages/login.vue` | 네이티브 로그인 폼 (redirect 쿼리 파라미터 지원) |
| `frontend/pages/mail.vue` | 메일 페이지 (3단 레이아웃) |
| `frontend/pages/meetings.vue` | 회의 페이지 (회의/녹화 탭) |
| `frontend/pages/callback.vue` | OAuth callback 페이지 (기존, 유지) |
| `frontend/components/layout/AppHeader.vue` | 네비게이션에 메일/회의 링크 추가 |
| `frontend/components/mail/MailSidebar.vue` | 메일 사이드바 (메일박스 목록) |
| `frontend/components/mail/MailList.vue` | 메일 목록 |
| `frontend/components/mail/MailView.vue` | 메일 상세 보기 |
| `frontend/components/mail/MailCompose.vue` | 메일 작성 모달 |
| `frontend/components/meetings/MeetingCard.vue` | 회의 카드 컴포넌트 |
| `frontend/components/meetings/MeetingDetail.vue` | 회의 상세 패널 |
| `frontend/components/meetings/CreateMeetingModal.vue` | 회의 생성 모달 |
| `frontend/components/meetings/RecordingList.vue` | 녹화 목록 컴포넌트 |
| `frontend/middleware/auth.global.ts` | 인증 미들웨어 (publicPages에 `/login` 포함) |

### 13.3 Nginx (192.168.0.150)

| 파일 경로 | 설명 |
|-----------|------|
| `/etc/nginx/conf.d/auth.namgun.or.kr.conf` | `/portal-bridge/` location 추가, `default_type text/html` |
| `/etc/nginx/conf.d/git.namgun.or.kr.conf` | `/user/login` → 포털 redirect |
| `/etc/nginx/conf.d/mail.namgun.or.kr.conf` | CSP `frame-ancestors` 설정 |

### 13.4 Nginx 설정 변경 상세

#### 13.4.1 auth.namgun.or.kr.conf

```nginx
server {
    listen 443 ssl http2;
    server_name auth.namgun.or.kr;

    # ... SSL, 기존 Authentik 프록시 설정 ...

    # Portal bridge pages
    location /portal-bridge/ {
        alias /var/www/portal-bridge/;
        default_type text/html;
        add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
        add_header Cache-Control "no-store";
    }

    # 기존 Authentik 프록시
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

    # ... SSL 설정 ...

    # SSO: 웹 로그인을 포털로 redirect
    location = /user/login {
        return 302 https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik;
    }

    # 기존 Gitea 프록시
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

    # ... SSL 설정 ...

    location / {
        proxy_pass http://192.168.0.250:8080;
        # ...

        # iframe 내장 허용 (포털에서 사용)
        add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
        # X-Frame-Options는 제거 (CSP frame-ancestors로 대체)
    }
}
```

### 13.5 브릿지 파일 (192.168.0.150)

| 파일 경로 | 설명 |
|-----------|------|
| `/var/www/portal-bridge/index.html` | 브릿지 메인 (Flow Executor 인증) |
| `/var/www/portal-bridge/callback` | 콜백 (code 추출 → postMessage) |

---

## 14. 검증 결과

### 14.1 Phase 5 검증

| 테스트 항목 | 결과 |
|-------------|------|
| 파일 리스트 캐시 히트 (30초 이내 재요청) | PASS |
| 파일 업로드 후 캐시 무효화 (즉시 반영) | PASS |
| 파일 삭제 후 캐시 무효화 | PASS |
| 파일 이름 변경 후 캐시 무효화 | PASS |
| 파일 이동 후 소스/대상 디렉토리 캐시 무효화 | PASS |
| 폴더 생성 후 캐시 무효화 | PASS |
| asyncio.to_thread 비동기 래핑 동작 | PASS |
| 대시보드 서비스 카드: Stalwart internal_only 표시 | PASS |
| 대시보드 서비스 카드: Pi-Hole 제거 확인 | PASS |
| RustDesk TCP 헬스체크 (21114 포트) | PASS |
| BBB 서비스 카드 표시 | PASS |
| BBB 회의 목록 조회 | PASS |
| BBB 회의 생성 | PASS |
| BBB 회의 참가 (MODERATOR/VIEWER) | PASS |
| BBB 회의 종료 (admin only) | PASS |
| BBB 녹화 목록 조회 | PASS |
| BBB 녹화 삭제 (admin only) | PASS |
| 메일 페이지 (/mail) 접근 | PASS |
| 메일박스 목록 조회 | PASS |
| 메일 목록 조회 (페이지네이션) | PASS |
| 메일 상세 보기 (자동 읽음 처리) | PASS |
| 메일 발송 | PASS |
| 첨부파일 다운로드 | PASS |
| AppHeader 메일/회의 네비게이션 링크 | PASS |

### 14.2 Phase 6 검증

| 테스트 항목 | 결과 |
|-------------|------|
| 네이티브 로그인 폼 표시 | PASS |
| 올바른 자격 증명으로 로그인 | PASS |
| 잘못된 자격 증명 에러 메시지 | PASS |
| PKCE S256 검증 (Authentik 토큰 교환) | PASS |
| 팝업 차단 시 에러 메시지 | PASS |
| 로그인 타임아웃 처리 | PASS |
| 세션 쿠키 발급 (portal_session) | PASS |
| 로그아웃 (세션 쿠키 삭제) | PASS |
| authentik_session SSO 쿠키 설정 확인 | PASS |
| 포털 로그인 후 Gitea 자동 로그인 (SSO) | PASS |
| Gitea /user/login → 포털 redirect | PASS |
| git push HTTPS 인증 (Basic Auth) | PASS |
| redirect 쿼리 파라미터 (로그인 후 원래 페이지 이동) | PASS |
| 브릿지 페이지 Content-Type (text/html) | PASS |
| 브릿지 페이지 SELinux 컨텍스트 | PASS |
| /api/auth/oidc-config 엔드포인트 | PASS |
| /api/auth/native-callback 엔드포인트 | PASS |
| bridge-ready 메시지 race condition 없음 | PASS |
| 팝업 자동 닫힘 (로그인 완료/실패 후) | PASS |

### 14.3 Phase 2 검증

| 테스트 항목 | 결과 | 비고 |
|------------|------|------|
| SMTP 인증 | **통과** | namgun18@namgun.or.kr via LDAP |
| IMAP 인증 | **통과** | — |
| 외부 발신 | **통과** | Gmail, amitl.co.kr 수신 확인 |
| 외부 수신 | **통과** | — |
| Samsung Email 앱 | **통과** | IMAP 993 SSL, SMTP 465 SSL |
| DKIM 서명 | **동작** | 메시지 크기 1292 → 4313 bytes 증가 확인 |
| SPF | **통과** | — |
| DMARC | **통과** | SPF alignment 기반 |

---

## 15. 잔여 작업 및 향후 계획

### 15.1 즉시 조치 필요

- [x] DKIM `dkim=pass` 확인 (DNS 캐시 만료 후)
- [ ] PTR 레코드 등록 (SK 브로드밴드, `211.244.144.69 → mail.namgun.or.kr`)
- [ ] `mail.namgun.or.kr`에 대한 SPF TXT 레코드 추가 (SPF_HELO_NONE 해결)
- [ ] Authentik 계정 비밀번호 설정: tsha, nahee14, kkb
- [ ] ed25519 DKIM 서명 추가 (선택)
- [ ] /var/vmail/ 백업 데이터 정리 (마이그레이션 완료 확인 후)

### 15.2 Phase 5-6 잔여 작업

- [ ] Authentik 세션 만료 시 포털 자동 재인증 UX 개선
- [ ] BBB 녹화 자동 정리 정책 설정
- [ ] JMAP 기반 네이티브 메일 UI 완성 (현재 iframe 방식에서 전환)
- [ ] 메일 첨부파일 업로드 (JMAP Blob upload)
- [ ] 다중 브라우저 SSO 테스트 (Safari, Firefox strict mode)
- [ ] 모바일 브라우저 팝업 호환성 검증 (iOS Safari, Android Chrome)

### 15.3 완료된 항목

| 항목 | 완료 단계 |
|------|----------|
| 포털 코어 개발 (Nuxt 3 + FastAPI) | Phase 3 |
| 파일 브라우저 (NFS 연동) | Phase 4 |
| BBB 화상회의 통합 | Phase 5 |
| Stalwart Mail iframe 통합 | Phase 5 |
| 네이티브 로그인 폼 | Phase 6 |
| Popup Bridge SSO | Phase 6 |
| Gitea SSO 연동 | Phase 6 |

### 15.4 향후 계획

| 항목 | 내용 | 예상 기술 스택 |
|------|------|---------------|
| 데모 사이트 | demo.namgun.or.kr 공개 데모 환경 구축 | Nuxt 3 + FastAPI (읽기 전용 모드) |
| Game Panel 포털 통합 | 게임 서버 관리를 포털 내에서 직접 수행 | 포털 API + Game Panel API 연동 |
| CalDAV / CardDAV | 캘린더/연락처 동기화 | Stalwart 내장 또는 별도 서버 |
| Naver Works급 ERP | 조직 관리, 결재, 메신저 등 그룹웨어 기능 | 장기 목표 |

### 15.5 계획된 보안 강화

- PTR 레코드 등록으로 역방향 DNS 검증 완성
- CSP(Content-Security-Policy) 헤더 추가 검토
- Authentik MFA(다중 인증) 정책 강화

---

## 16. 리스크 평가

| 리스크 | 영향 | 확률 | 완화 방안 |
|--------|------|------|----------|
| iRedMail 마이그레이션 데이터 손실 | High | Low | imapsync dry-run, Maildir 백업 |
| Stalwart OIDC-only 메일 바운스 | High | Med | Authentik LDAP를 primary 백엔드로 사용 |
| 메일 클라이언트 OAUTHBEARER 미지원 | Med | High | LDAP Outpost로 비밀번호 인증 병행 |
| Authentik SPOF | High | Low | 로컬 admin fallback, 정기 DB 백업 |
| DNS/TLS 전파 지연 | Med | Low | 낮은 TTL 사전 설정, dig 검증 후 전환 |
| 프론트엔드 프레임워크 취약점 | Critical | N/A | React/RSC 배제, Vue.js/Nuxt 채택으로 구조적 제거 |

---

## 17. 참고 문헌

- Authentik: https://goauthentik.io/docs/
- Stalwart Mail Server: https://stalw.art/docs/
- Stalwart OIDC 오픈소스 발표: https://stalw.art/blog/oidc-open-source/
- RustDesk OIDC: https://rustdesk.com/docs/en/self-host/rustdesk-server-pro/oidc/
- Gitea 인증: https://docs.gitea.com/usage/authentication
- Nuxt 3: https://nuxt.com/docs
- FastAPI: https://fastapi.tiangolo.com/
- CVE-2025-55182 (React2Shell): https://react.dev/blog/2025/12/03/critical-security-vulnerability-in-react-server-components
- OpenMediaVault: https://www.openmediavault.org/

---

*문서 끝. 최종 갱신: 2026-02-19*
