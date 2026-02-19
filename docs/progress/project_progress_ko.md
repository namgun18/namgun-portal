# namgun.or.kr 종합 포털 SSO 통합 플랫폼 — 프로젝트 진행 보고서

| 항목 | 내용 |
|------|------|
| 프로젝트명 | namgun.or.kr 종합 포털 SSO 통합 플랫폼 |
| 작성자 | 남기완 (Kiwan Nam) |
| 분류 | 내부 / 대외비 |

## 문서 이력

| 버전 | 날짜 | 작성자 | 비고 |
|------|------|--------|------|
| v1.0 | 2026-02-18 | 남기완 | 최초 작성 (Phase 0 ~ Phase 2 완료 기준) |
| v1.1 | 2026-02-19 | 남기완 | Phase 3 ~ Phase 6 완료 기준 갱신 |

---

## 1. 프로젝트 개요

namgun.or.kr 종합 포털은 가정 및 소규모 조직을 위한 셀프 호스팅 통합 플랫폼이다. Authentik을 중앙 Identity Provider(IdP)로 두고, Git 저장소, 원격 데스크톱, 메일, 화상회의, 파일 관리, 게임 서버 등 다양한 서비스를 SSO(Single Sign-On)로 통합하는 것을 목표로 한다.

### 1.1 핵심 목표

- 모든 서비스에 대한 SSO 인증 통합 (OIDC / LDAP)
- ISMS-P 보안 기준에 준하는 인프라 구성
- 셀프 호스팅 기반의 데이터 주권 확보
- 단계적 서비스 확장 (Phase 0 ~ Phase 6)

---

## 2. 단계별 진행 현황 요약

| 단계 | 명칭 | 상태 | 기간 | 비고 |
|------|------|------|------|------|
| Phase 0 | 인프라 준비 | **완료** | — | Authentik, DNS, Nginx, TLS |
| Phase 1 | SSO PoC | **완료** | — | Gitea OIDC, RustDesk OIDC |
| Phase 2 | 메일 서버 마이그레이션 | **완료** | — | Stalwart + LDAP + OIDC |
| Phase 3 | 포털 코어 개발 | **완료** | — | Nuxt 3 + FastAPI + PostgreSQL |
| Phase 4 | 파일 브라우저 | **완료** | — | NFS 마운트 + 포털 내 파일 관리 UI |
| Phase 5 | 서비스 개선 및 메일/회의 통합 | **완료** | — | BBB, 메일 iframe, 캐시, 네비게이션 |
| Phase 6 | 네이티브 로그인 및 SSO 통합 | **완료** | — | 네이티브 로그인 폼, Popup Bridge, Gitea SSO |

---

## 3. 인프라 토폴로지

### 3.1 물리/논리 구성도

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

### 3.2 서비스 현황 종합

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

---

## 4. Phase 0: 인프라 준비 (완료)

### 4.1 Authentik SSO (Identity Provider)

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

### 4.2 DNS 구성

- **관리 도구**: Windows Server DNS
- **내부 DNS**: Pi-Hole (192.168.0.251)
- **등록된 레코드**:
  - A 레코드: 모든 서브도메인 (auth, git, game, mail, meet, remote, namgun.or.kr)
  - MX 레코드: mail.namgun.or.kr
  - TXT 레코드: SPF, DKIM, DMARC

#### Windows Server DNS 제약사항

> TXT 레코드가 255자를 초과할 경우, 하나의 레코드 안에서 여러 문자열로 분할하여 입력해야 한다. DKIM 공개키(RSA-2048)가 대표적인 예시이다.

### 4.3 Nginx 리버스 프록시 (192.168.0.150)

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

### 4.4 TLS 인증서

| 대상 | 발급 방식 | 갱신 방식 |
|------|----------|----------|
| Nginx 사이트 (*.namgun.or.kr) | Let's Encrypt certbot | webroot (/var/www/certbot), 자동 갱신 |
| Stalwart Mail Server | Let's Encrypt ACME | Stalwart 내장 ACME 자동 갱신 (Nginx와 별도) |

---

## 5. Phase 1: SSO PoC (완료)

### 5.1 Gitea SSO 통합

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

### 5.2 RustDesk Pro SSO 통합

- **접속 URL**: https://remote.namgun.or.kr
- **구성**: hbbs (시그널링 서버) + hbbr (릴레이 서버)
- **인증 방식**: OIDC via Authentik

---

## 6. Phase 2: 메일 서버 마이그레이션 (완료)

iRedMail(Postfix + Dovecot) 기반의 레거시 메일 서버를 Stalwart Mail Server로 마이그레이션하고, Authentik LDAP를 통한 인증 통합을 완료하였다.

### 6.1 단계별 진행 내역

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

#### Step 4: 계정 마이그레이션

총 9개 계정을 마이그레이션하였다.

**개인 계정 (5개) — LDAP via Authentik**

| 계정명 | 이메일 | 비고 |
|--------|--------|------|
| namgun18 | namgun18@namgun.or.kr | Authentik username `namgun` → `namgun18`로 변경 (LDAP cn 매칭) |
| tsha | tsha@namgun.or.kr | 비밀번호 설정 대기 |
| nahee14 | nahee14@namgun.or.kr | 비밀번호 설정 대기 |
| kkb | kkb@namgun.or.kr | 비밀번호 설정 대기 |
| administrator | administrator@namgun.or.kr | — |

**서비스 계정 (4개) — Stalwart 내부 인증**

| 계정명 | 용도 |
|--------|------|
| system | 시스템 메일 |
| postmaster | 포스트마스터 |
| git | Gitea 알림 메일 |
| noreply | 자동 발신 전용 |

**메일 데이터 마이그레이션**: imapsync를 사용하여 Dovecot → Stalwart로 이전

#### Step 5: DNS 업데이트

| 레코드 | 내용 | 비고 |
|--------|------|------|
| DKIM | RSA-2048 신규 키 생성, DNS TXT 레코드 갱신 | Windows DNS에서 2개 문자열로 분할 입력 |
| SPF | `v=spf1 ip4:211.244.144.69 mx ~all` | 변경 없음 |
| DMARC | `v=DMARC1; p=quarantine` | 변경 없음 |
| Selector | `default` | — |

#### Step 6: Nginx 리버스 프록시 설정

- 설정 파일: `mail.namgun.or.kr.conf` (192.168.0.150)
- HTTPS 443 → Stalwart 8080 (Web Admin / JMAP)
- SMTP (25, 465, 587) / IMAP (993)은 프록시하지 않음 (직접 연결)
- ISMS-P 보안 헤더 적용

#### Step 7: 검증 결과

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

#### Step 8: iRedMail 제거

제거된 패키지:

```
postfix, dovecot, amavis, clamav, spamassassin, php-fpm
```

- 메일 서버 VM의 nginx 비활성화
- 레거시 메일 데이터 `/var/vmail/` (72MB) 보존

#### Step 9: 문서화

- `phase2_mail_migration_ko.md` / `_en.md` 작성 후 Gitea에 푸시 완료

---

## 7. Phase 3: 포털 코어 개발 (완료)

Nuxt 3 + FastAPI + PostgreSQL 기반의 포털 웹 애플리케이션 코어를 개발하고, Docker Compose 환경에서 프로덕션 배포를 완료하였다.

### 7.1 기술 스택 및 아키텍처

| 분류 | 기술 |
|------|------|
| 프론트엔드 | Nuxt 3 (Vue 3, SSR), shadcn-vue (UI 컴포넌트) |
| 백엔드 | FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| 데이터베이스 | PostgreSQL 16 (Alpine) |
| 인증 | OIDC via Authentik (PKCE S256) |
| 세션 관리 | itsdangerous (URLSafeTimedSerializer), 서명된 쿠키 |
| 컨테이너 | Docker Compose, `--profile prod` 배포 |

### 7.2 Docker Compose 구성

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

### 7.3 OIDC 인증 (Authentik)

- **인증 플로우**: Authorization Code + PKCE (S256)
- **엔드포인트**:
  - Authorization: `https://auth.namgun.or.kr/application/o/authorize/`
  - Token: `https://auth.namgun.or.kr/application/o/token/`
  - Userinfo: `https://auth.namgun.or.kr/application/o/userinfo/`
  - End Session: `https://auth.namgun.or.kr/application/o/portal/end-session/`
- **Redirect URI**: `https://namgun.or.kr/api/auth/callback`
- **PKCE 저장**: `portal_pkce` 쿠키 (httponly, secure, samesite=lax, max_age=600)
- **세션 쿠키**: `portal_session` (httponly, secure, samesite=lax, 7일 유효)

### 7.4 사용자 모델 (User)

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

### 7.5 대시보드 서비스 모니터링

- **서비스 수**: 6개 (Authentik, Gitea, RustDesk, Game Panel, Stalwart Mail, BBB)
- **헬스체크 주기**: 60초 (백그라운드 태스크)
- **체크 방식**: HTTP GET (상태코드 < 400 → ok) 또는 TCP 포트 체크 (RustDesk)
- **인메모리 캐시**: `_cache` 리스트, 프론트엔드에서 `/api/services/` 로 조회
- **ServiceCard**: 서비스명, 상태 뱃지 (ok/down/checking), 응답 시간(ms), 외부 URL 링크

### 7.6 NFS 마운트 (파일 스토리지)

- **NFS 서버**: OMV (192.168.0.100), `/export/root` (fsid=0)
- **Docker NFS 볼륨**: `portal-storage` → 컨테이너 내 `/storage`
- **마운트 옵션**: `addr=192.168.0.100,nfsvers=4,rw,hard,noatime,nolock`
- **클라이언트 디바이스**: `:/portal` (fsid=0이 `/export/root`에 걸리므로)

---

## 8. Phase 4: 파일 브라우저 (완료)

NFS 마운트된 스토리지를 포털 내에서 웹 브라우저로 관리할 수 있는 파일 브라우저를 개발하였다.

### 8.1 NFS 연동 상세

| 항목 | 내용 |
|------|------|
| NFS 서버 | OMV (192.168.0.100) |
| Export 경로 | `/export/root` (fsid=0) |
| Docker 볼륨 디바이스 | `:/portal` |
| NFS 버전 | v4.1 (WSL2 커널이 v4.2를 지원하지 않아 v4.1 사용) |
| 마운트 옵션 | `nfsvers=4,rw,hard,noatime,nolock` |
| WSL2 패키지 요구사항 | `nfs-common` 설치 필요 |

### 8.2 파일 시스템 구조

```
/storage/
├── shared/          ← 공유 폴더 (전체 사용자 읽기, 관리자만 쓰기)
└── users/
    └── {user_id}/   ← 개인 폴더 (사용자별 격리)
```

- **가상 경로 체계**: `my/...` → `/storage/users/{user_id}/...`, `shared/...` → `/storage/shared/...`
- **관리자 경로**: `users/...` → `/storage/users/...` (전체 사용자 디렉토리 탐색)
- **경로 보안**: `resolve()` 후 base 경로 접두어 검증으로 path traversal 방지

### 8.3 파일 작업 (API)

| 작업 | 엔드포인트 | 비고 |
|------|-----------|------|
| 디렉토리 목록 | GET `/api/files/list` | 가상 경로 기반 |
| 파일 업로드 | POST `/api/files/upload` | multipart/form-data, 최대 1024MB |
| 파일 다운로드 | GET `/api/files/download` | StreamingResponse |
| 파일/폴더 삭제 | DELETE `/api/files/delete` | 관리자 전용 (shared), 본인 폴더는 자유 |
| 이름 변경 | POST `/api/files/rename` | — |
| 이동/복사 | POST `/api/files/move` | `copy` 파라미터로 복사 지원 |
| 폴더 생성 | POST `/api/files/mkdir` | — |

### 8.4 프론트엔드 UI

- **Breadcrumb 네비게이션**: 현재 경로를 계층별로 표시, 클릭으로 이동
- **파일 그리드/리스트 뷰**: 파일명, 크기, 수정일, MIME 타입 표시
- **사이드바**: my / shared / users(관리자) 루트 탐색
- **커맨드 바**: 업로드, 새 폴더, 삭제, 이름 변경 등 도구 모음
- **컨텍스트 메뉴**: 우클릭 메뉴 (다운로드, 이름 변경, 이동, 삭제)
- **업로드 모달**: 드래그 앤 드롭 또는 파일 선택
- **프리뷰 모달**: 이미지/텍스트 파일 미리보기
- **공유 링크 모달**: 외부 공유 링크 생성 (ShareLink 모델, 만료/다운로드 제한)

---

## 9. Phase 5: 서비스 개선 및 메일/회의 통합 (완료)

파일 리스트 캐시, BBB 화상회의 통합, Stalwart Mail iframe 통합, 서비스 카드 개선 및 네비게이션 추가를 완료하였다.

### 9.1 파일 리스트 캐시

- **인메모리 TTL 캐시**: `_dir_cache` (30초 TTL), `_size_cache` (60초 TTL)
- **캐시 무효화**: 쓰기 작업(upload, delete, rename, move, mkdir) 완료 후 `invalidate_cache()` 호출
- **asyncio 래핑**: `list_directory()` → `asyncio.to_thread()` 래핑으로 NFS I/O 블로킹 방지

### 9.2 BBB 화상회의 통합

- **서버**: BigBlueButton 3.0 (192.168.0.249)
- **접속 URL**: https://meet.namgun.or.kr
- **API 클라이언트**: SHA256 checksum 인증 방식의 BBB API 클라이언트 (`meetings/bbb.py`)
- **기능**: 회의 생성(create), 목록 조회(getMeetings), 상세 조회(getMeetingInfo), 참여 URL 생성(join), 종료(end), 녹화 조회/삭제(getRecordings/deleteRecordings)
- **프론트엔드**: MeetingCard, MeetingDetail, CreateMeetingModal, RecordingList 컴포넌트
- **라우터**: `/api/meetings/` (list, create, join, end, recordings)

### 9.3 Stalwart Mail iframe 통합

- **포털 내 접근**: `/mail` 페이지에서 Stalwart 웹 UI를 iframe으로 임베드
- **Nginx 설정**: `mail.namgun.or.kr.conf`에서 `X-Frame-Options` 대신 `Content-Security-Policy: frame-ancestors 'self' https://namgun.or.kr` 사용
- **서비스 카드**: `internal_only: True` 설정으로 대시보드에서 외부 링크 비노출

### 9.4 서비스 카드 변경사항

| 서비스 | 변경 사항 |
|--------|----------|
| RustDesk | HTTP 헬스체크 → TCP 포트 체크 (`192.168.0.50:21114`) |
| Pi-Hole | SERVICE_DEFS에서 제거 (포털 대시보드 미노출) |
| BBB (화상회의) | 신규 추가 (`health_url: https://meet.namgun.or.kr/bigbluebutton/api`, `internal_only: True`) |
| Stalwart Mail | `internal_only: True` 설정 (iframe 통합으로 외부 링크 불필요) |

### 9.5 네비게이션 추가

AppHeader에 네비게이션 메뉴 추가:

| 메뉴 | 경로 | 설명 |
|------|------|------|
| 대시보드 | `/` | 서비스 상태 대시보드 |
| 파일 | `/files` | 파일 브라우저 |
| 메일 | `/mail` | Stalwart Mail iframe |
| 회의 | `/meetings` | BBB 회의 관리 |

모바일 반응형 네비게이션 (햄버거 메뉴) 포함.

---

## 10. Phase 6: 네이티브 로그인 및 SSO 통합 (완료)

Authentik 리다이렉트 방식의 로그인을 네이티브 로그인 폼으로 대체하고, Popup Bridge 패턴을 통해 SSO 쿠키를 설정하며, Gitea 연동 SSO를 구현하였다.

### 10.1 네이티브 로그인 폼

- **페이지**: `/login` (auth 레이아웃)
- **입력 필드**: 사용자명/이메일, 비밀번호
- **리다이렉트 파라미터**: `?redirect=<URL>` 쿼리 파라미터 지원 (외부 서비스 SSO용)
- **보안**: `namgun.or.kr` 도메인 또는 상대 경로만 리다이렉트 허용

### 10.2 Popup Bridge 패턴

기존 Authentik 전체 화면 리다이렉트 방식은 UX가 좋지 않고, iframe 방식은 third-party cookie partitioning(브라우저 보안 정책)으로 인해 SSO 쿠키가 설정되지 않는 문제가 있었다. 이를 해결하기 위해 Popup Bridge 패턴을 도입하였다.

#### 플로우

1. 사용자가 `/login` 페이지에서 사용자명/비밀번호 입력 후 제출
2. 브라우저가 `https://auth.namgun.or.kr/portal-bridge/` 팝업을 동기적으로 열림 (팝업 차단기 회피)
3. Bridge 페이지가 `portal-bridge-ready` postMessage 전송
4. 포털이 OIDC config 조회 + PKCE 생성 후 `portal-login` 메시지를 팝업에 전송
5. Bridge가 Authentik Flow Executor API를 호출하여 인증 (단계별 stage 처리)
6. 인증 완료 후 `authorize` 엔드포인트 호출 → `code` 획득
7. Bridge가 `portal-login-result` 메시지로 코드를 포털에 전달
8. 포털 백엔드가 `/api/auth/native-callback`에서 코드를 토큰으로 교환, 세션 쿠키 발급

#### PKCE S256 클라이언트 사이드 생성

```typescript
// code_verifier: 64바이트 랜덤 → base64url
// code_challenge: SHA-256(code_verifier) → base64url
```

- `crypto.getRandomValues()` + `crypto.subtle.digest('SHA-256', ...)` 사용
- 브라우저 측에서 PKCE 쌍 생성 후 `code_verifier`를 팝업에 전달하지 않고 포털에서 보관

#### Bridge 페이지 네비게이션 (SSO 쿠키 설정)

- Popup은 `https://auth.namgun.or.kr` origin에서 실행되므로 Authentik 쿠키가 first-party로 설정됨
- Flow Executor API 호출 시 Authentik 세션 쿠키가 정상적으로 저장됨
- Bridge callback 페이지(`/portal-bridge/callback`)에서 `code` 파라미터를 추출하여 opener에 postMessage

### 10.3 백엔드 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/auth/login` | GET | OIDC 리다이렉트 (레거시, PKCE 쿠키 설정) |
| `/api/auth/callback` | GET | OIDC 콜백 (레거시, 코드 교환 + 세션 설정) |
| `/api/auth/oidc-config` | GET | 공개 OIDC 설정 반환 (client_id, redirect_uri, scope, flow_slug) |
| `/api/auth/native-callback` | POST | 네이티브 로그인 코드 교환 (code + code_verifier → 세션 쿠키) |
| `/api/auth/me` | GET | 현재 인증 사용자 정보 |
| `/api/auth/logout` | POST | 세션 쿠키 삭제 |

### 10.4 Authentik Flow Executor API 단계

네이티브 로그인에서 Bridge가 호출하는 Authentik API 흐름:

1. `GET /api/v3/flows/executor/{flow_slug}/` → 첫 번째 stage 정보
2. `POST /api/v3/flows/executor/{flow_slug}/` (uid_field: username) → identification stage 제출
3. `POST /api/v3/flows/executor/{flow_slug}/` (password: password) → password stage 제출
4. 플로우 완료 시 `redirect_to` URL이 반환됨
5. Bridge가 `redirect_to` 내의 authorize URL을 페이지 네비게이션으로 호출 → SSO 쿠키 설정 + code 발급
6. Callback 페이지에서 URL의 `code` 파라미터 추출

> **주의**: 플로우 완료 후 `to: "/"` 응답이 오는 경우, authorize 엔드포인트를 수동으로 재호출해야 한다.

### 10.5 Gitea SSO 연동

- **방식**: OAuth2 전용 로그인 (자체 로그인 폼 미노출)
- **미인증 접근 처리**: Nginx `namgun.or.kr.conf` 또는 `git.namgun.or.kr.conf`에서 미인증 사용자를 포털 로그인 페이지로 리다이렉트 (`?redirect=https://git.namgun.or.kr/user/oauth2/authentik`)
- **인증 후**: 포털 로그인 완료 → Authentik SSO 쿠키 설정됨 → Gitea OAuth2 버튼 클릭 시 자동 인증 통과
- **git push HTTP 인증**: BASIC_AUTH가 비활성화되면 git push 인증이 실패하므로, HTTP git 작업을 위해 BASIC_AUTH를 재활성화

### 10.6 로그인 리다이렉트 파라미터

```
https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik
```

- 외부 서비스에서 포털 로그인 페이지로 보낼 때 `redirect` 쿼리 파라미터 사용
- 로그인 완료 후 해당 URL로 자동 이동
- 보안: `https://` + `.namgun.or.kr` 도메인 또는 `/` 상대 경로만 허용

---

## 11. 핵심 트러블슈팅 정리

| # | 문제 | 원인 | 해결 방법 |
|---|------|------|----------|
| 1 | Stalwart v0.15에서 LDAP 인증 실패 | `bind.auth.enable`이 기본적으로 hash 비교 모드 | `bind.auth.method = "lookup"` 설정 |
| 2 | Stalwart DKIM 서명 키 인식 실패 | 키 네이밍 컨벤션 불일치 | `{algorithm}-{domain}` 형식 사용 (예: `rsa-namgun.or.kr`) |
| 3 | Stalwart expression 필드 DB override 불가 | 일부 built-in 기본값은 DB override 미지원 | 설정 파일에서 직접 수정 |
| 4 | rootless Podman에서 호스트 LAN IP 접근 불안정 | Podman rootless 네트워크 제약 | sidecar + `network_mode: host` 사용 |
| 5 | Windows Server DNS TXT 레코드 저장 실패 | 255자 초과 TXT 레코드 제한 | 하나의 레코드를 여러 문자열로 분할 |
| 6 | Authentik 최초 로그인 실패 | BOOTSTRAP_PASSWORD에 `==` 등 특수문자 포함 | 단순 영숫자 비밀번호 사용 |
| 7 | Authentik 반복 로그인 차단 | reputation score 누적 | `Reputation` 테이블 초기화 |
| 8 | Gitea CLI 실행 시 권한 오류 | root 사용자로 실행 | `--user git` 옵션으로 git 사용자 지정 |
| 9 | PostgreSQL bind mount 실패 | WSL2 환경에서 NTFS(/mnt/d/) 파일시스템 권한 문제 | Docker named volume (`portal-db-data`) 사용 |
| 10 | NFS v4.2 마운트 실패 | WSL2 커널(5.15.x)이 NFS v4.2를 지원하지 않음 | `nfsvers=4` (v4.1) 사용 |
| 11 | fetch() cross-origin redirect 시 브라우저 hang | OIDC redirect_uri가 다른 origin인 경우 fetch가 무한 대기 | same-origin redirect_uri 사용 (`namgun.or.kr/api/auth/callback`) |
| 12 | OAuth 파라미터 인코딩 누락 | `encodeURIComponent` 미적용으로 query 파라미터가 깨짐 | `URLSearchParams`를 사용하여 자동 인코딩 |
| 13 | Authentik 플로우 완료 후 `to: "/"` 응답 | Flow Executor가 authorize가 아닌 기본 경로로 리다이렉트 반환 | authorize 엔드포인트를 수동으로 재호출 |
| 14 | iframe에서 Authentik 쿠키 미설정 | 브라우저의 third-party cookie partitioning 정책 | iframe 대신 popup 방식으로 전환 (first-party context) |
| 15 | Bridge-Portal 간 race condition | 팝업이 로드되기 전에 postMessage 전송 | `portal-bridge-ready` 메시지 수신 후 login 메시지 전송 (listener 선설정) |
| 16 | SSO 쿠키 미설정 (fetch 기반) | fetch/XHR로 authorize를 호출하면 브라우저 쿠키 저장이 안 됨 | 페이지 네비게이션(`window.location.href`) 방식으로 변경 |
| 17 | Gitea 자동 로그인 안 됨 | 미인증 사용자가 Gitea에 직접 접근 시 포털 세션 없음 | Nginx에서 포털 로그인 페이지로 redirect 룰 추가 (`?redirect=...`) |
| 18 | git push HTTP 인증 실패 | BASIC_AUTH가 비활성화된 상태 | git HTTP 작업을 위해 BASIC_AUTH 재활성화 |

---

## 12. 잔여 작업 항목

### 12.1 즉시 조치 필요

- [x] DKIM `dkim=pass` 확인 (DNS 캐시 만료 후)
- [ ] PTR 레코드 등록 (SK 브로드밴드, `211.244.144.69 → mail.namgun.or.kr`)
- [ ] `mail.namgun.or.kr`에 대한 SPF TXT 레코드 추가 (SPF_HELO_NONE 해결)
- [ ] Authentik 계정 비밀번호 설정: tsha, nahee14, kkb

### 12.2 완료된 항목

| 항목 | 완료 단계 |
|------|----------|
| 포털 코어 개발 (Nuxt 3 + FastAPI) | Phase 3 |
| 파일 브라우저 (NFS 연동) | Phase 4 |
| BBB 화상회의 통합 | Phase 5 |
| Stalwart Mail iframe 통합 | Phase 5 |
| 네이티브 로그인 폼 | Phase 6 |
| Popup Bridge SSO | Phase 6 |
| Gitea SSO 연동 | Phase 6 |

### 12.3 향후 계획

| 항목 | 내용 | 예상 기술 스택 |
|------|------|---------------|
| 데모 사이트 | demo.namgun.or.kr 공개 데모 환경 구축 | Nuxt 3 + FastAPI (읽기 전용 모드) |
| Game Panel 포털 통합 | 게임 서버 관리를 포털 내에서 직접 수행 | 포털 API + Game Panel API 연동 |
| CalDAV / CardDAV | 캘린더/연락처 동기화 | Stalwart 내장 또는 별도 서버 |
| Naver Works급 ERP | 조직 관리, 결재, 메신저 등 그룹웨어 기능 | 장기 목표 |

---

## 13. 기술 스택 요약

| 분류 | 기술 |
|------|------|
| Identity Provider | Authentik 2025.10.4 |
| 인증 프로토콜 | OIDC, LDAP, OAuth2 |
| 포털 프론트엔드 | Nuxt 3, Vue 3, shadcn-vue |
| 포털 백엔드 | FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| 리버스 프록시 | Nginx (Rocky Linux 10) |
| TLS 인증서 | Let's Encrypt (certbot + ACME) |
| 컨테이너 (Docker) | Authentik, Portal (frontend + backend + nginx + PostgreSQL), Gitea, RustDesk Pro, Game Panel |
| 컨테이너 (Podman) | Stalwart Mail, LDAP Outpost |
| 메일 서버 | Stalwart Mail Server (RocksDB) |
| 화상회의 | BigBlueButton 3.0 |
| 파일 스토리지 | NFS v4.1 (OMV, 192.168.0.100) |
| Git 호스팅 | Gitea 1.25.4 |
| DNS | Windows Server DNS, Pi-Hole |
| 호스트 OS | Windows (WSL2), Rocky Linux 10, Rocky Linux 9.7 |
| 가상화 | Hyper-V |

---

## 14. 보안 고려사항

### 14.1 적용된 보안 정책

- ISMS-P 기준 보안 헤더 전 사이트 적용
- TLS 1.2+ 강제 (HSTS preload)
- 서버 정보 노출 차단 (`server_tokens off`, `X-Powered-By` / `Server` 헤더 제거)
- 스캐너/봇 차단 규칙
- DKIM + SPF + DMARC 이메일 인증 체계
- PKCE S256 인증 코드 보호 (replay 공격 방지)
- 서명된 세션 쿠키 (itsdangerous, httponly, secure, samesite=lax)
- 파일 시스템 path traversal 방지 (resolve + prefix 검증)
- 리다이렉트 URL 도메인 화이트리스트 (`*.namgun.or.kr`)

### 14.2 계획된 보안 강화

- PTR 레코드 등록으로 역방향 DNS 검증 완성
- CSP(Content-Security-Policy) 헤더 추가 검토
- Authentik MFA(다중 인증) 정책 강화

---

*문서 끝. 최종 갱신: 2026-02-19*
