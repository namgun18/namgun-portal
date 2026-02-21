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
| v1.2 | 2026-02-21 | 남기완 | Phase 6.5(인증 게이트웨이 전환), Phase 7(회원가입·관리자 패널) 추가 |
| v1.3 | 2026-02-21 | 남기완 | Phase 8(BBB 새 탭 회의), Phase 9(Gitea 포털 내재화), Phase 10(대시보드 리뉴얼) 추가 |
| v1.4 | 2026-02-22 | 남기완 | Phase 11(비주얼 리프레시), Phase 12(인프라 보안 강화) 추가 |

---

## 1. 프로젝트 개요

namgun.or.kr 종합 포털은 가정 및 소규모 조직을 위한 셀프 호스팅 통합 플랫폼이다. Authentik을 중앙 Identity Provider(IdP)로 두고, Git 저장소, 원격 데스크톱, 메일, 화상회의, 파일 관리, 게임 서버 등 다양한 서비스를 SSO(Single Sign-On)로 통합하는 것을 목표로 한다.

### 1.1 핵심 목표

- 모든 서비스에 대한 SSO 인증 통합 (OIDC / LDAP)
- ISMS-P 보안 기준에 준하는 인프라 구성
- 셀프 호스팅 기반의 데이터 주권 확보
- 단계적 서비스 확장 (Phase 0 ~ Phase 12)

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
| Phase 6.5 | 중앙 인증 게이트웨이 전환 | **완료** | — | 서버사이드 로그인, 포털 OIDC 제공자, Popup Bridge 제거 |
| Phase 7 | 회원가입 및 관리자 패널 | **완료** | — | 승인제 회원가입, 프로필·비밀번호 관리, 관리자 패널, 권한 관리 |
| Phase 8 | BBB 새 탭 회의 참여 | **완료** | — | 새 탭 회의 참여, 자동 닫힘, Greenlight 차단, 학습분석 |
| Phase 9 | Gitea 포털 내재화 | **완료** | — | 저장소 탐색, 코드 뷰어(구문 강조), 이슈/PR 관리 (v0.5.0) |
| Phase 10 | 대시보드 홈화면 리뉴얼 | **완료** | — | 8개 위젯, 게임서버 상태, 스토리지 게이지, Git 캐시 (v0.5.1) |
| Phase 11 | 비주얼 리프레시 | **완료** | — | 색상 팔레트 분리, 카드/버튼 인터랙션, 그라디언트 히어로·헤더, 위젯 색상 아이콘 (v0.5.2) |
| Phase 12 | 인프라 보안 강화 | **완료** | — | 전서버 취약점 스캔, CSP 헤더, firewalld 활성화, OS 보안 패치, test 페이지 정리 |

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

## 11. Phase 6.5: 중앙 인증 게이트웨이 전환 (완료)

Popup Bridge 기반의 인증 방식을 제거하고, 포털 백엔드가 Authentik Flow Executor API를 직접 호출하는 서버사이드 인증으로 전환하였다. 또한 포털이 OIDC 제공자(Provider) 역할을 하여 Gitea 등 외부 서비스에 SSO를 제공하는 구조로 변경하였다.

### 11.1 서버사이드 네이티브 로그인

- **이전 방식**: 프론트엔드에서 Popup Bridge를 통해 Authentik Flow Executor 호출 → 복잡한 팝업 간 메시지 교환
- **변경 방식**: 프론트엔드 → `POST /api/auth/login` → 백엔드가 Authentik Flow Executor API 직접 호출 → 세션 쿠키 발급
- **장점**: 팝업 차단기 문제 제거, SSO 쿠키 불필요, 코드 복잡도 대폭 감소

#### 인증 플로우

```
1. 사용자 → 포털 로그인 폼에 ID/PW 입력
2. POST /api/auth/login → 백엔드
3. 백엔드 → Authentik Flow Executor API 호출 (identification → password stage)
4. Authentik → 플로우 완료 → 백엔드가 OIDC authorize 호출 → 토큰 교환 → userinfo
5. 백엔드 → 세션 쿠키 발급 → 프론트엔드 로그인 완료
```

### 11.2 포털 OIDC 제공자 (OAuth2 Provider)

포털이 직접 OIDC 제공자 역할을 하여 Gitea 등 외부 서비스에 SSO를 제공한다.

#### 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /oauth/.well-known/openid-configuration` | OIDC Discovery |
| `GET /oauth/authorize` | Authorization endpoint (code 발급) |
| `POST /oauth/token` | Token endpoint (access_token + id_token 발급) |
| `GET /oauth/userinfo` | Userinfo endpoint |

#### 클라이언트 관리

- `.env`의 `OAUTH_CLIENTS_JSON`에 JSON 형태로 정의
- 현재 등록 클라이언트: `portal-gitea` (Gitea SSO용)
- `redirect_uris` 화이트리스트 검증
- PKCE (S256) 지원

#### id_token (JWT)

토큰 응답에 OpenID Connect 표준 `id_token`을 포함한다:

```json
{
  "iss": "https://namgun.or.kr",
  "sub": "<user_id>",
  "aud": "<client_id>",
  "preferred_username": "namgun18",
  "name": "Kiwan Nam",
  "email": "namgun18@namgun.or.kr",
  "groups": ["admin"],
  "nonce": "...",
  "iat": ...,
  "exp": ...
}
```

### 11.3 Gitea SSO 전환

- **이전**: Gitea → Authentik OIDC (직접 연동)
- **변경**: Gitea → 포털 OIDC 제공자 (포털 세션 기반 SSO)
- **OAuth 소스 변경**: `gitea admin auth add-oauth --name portal --provider openidConnect --auto-discover-url https://namgun.or.kr/oauth/.well-known/openid-configuration`
- **Gitea 대시보드 링크**: `/user/oauth2/portal` (기존 `/user/oauth2/authentik`에서 변경)

### 11.4 제거된 코드

- Popup Bridge 프론트엔드 (`bridge-login.ts`)
- Authentik Bridge 페이지 (`/portal-bridge/`)
- `POST /api/auth/native-callback` (Popup 전용 콜백)
- `GET /api/auth/oidc-config` (Popup 전용 설정)

---

## 12. Phase 7: 회원가입 및 관리자 패널 (완료)

승인제 회원가입, 프로필 관리, 비밀번호 변경/찾기, 관리자 사용자 관리 및 권한 할당 기능을 구현하였다.

### 12.1 Authentik Admin API 클라이언트

Authentik Admin API를 래핑하는 httpx 기반 비동기 클라이언트를 개발하였다.

**파일**: `backend/app/auth/authentik_admin.py`

| 함수 | Authentik API | 설명 |
|------|--------------|------|
| `create_user()` | `POST /api/v3/core/users/` + `set_password` + `add_user` | 비활성 사용자 생성 + 비밀번호 설정 + Users 그룹 추가 |
| `activate_user(pk)` | `PATCH /api/v3/core/users/{pk}/` | 사용자 활성화 (관리자 승인) |
| `deactivate_user(pk)` | `PATCH /api/v3/core/users/{pk}/` | 사용자 비활성화 |
| `update_user(pk, **fields)` | `PATCH /api/v3/core/users/{pk}/` | 사용자 정보 수정 |
| `set_password(pk, password)` | `POST /api/v3/core/users/{pk}/set_password/` | 비밀번호 변경 |
| `delete_user(pk)` | `DELETE /api/v3/core/users/{pk}/` | 사용자 삭제 |
| `get_recovery_link(pk)` | `POST /api/v3/core/users/{pk}/recovery/` | 비밀번호 복구 링크 생성 |
| `lookup_pk_by_username()` | `GET /api/v3/core/users/?username=` | PK 조회 |
| `add_user_to_group()` | `POST /api/v3/core/groups/{pk}/add_user/` | 그룹 추가 |
| `remove_user_from_group()` | `POST /api/v3/core/groups/{pk}/remove_user/` | 그룹 제거 |

#### 환경 변수

| 변수 | 용도 |
|------|------|
| `AUTHENTIK_API_TOKEN` | Admin API Bearer 토큰 (namgun18 소유) |
| `AUTHENTIK_USERS_GROUP_PK` | "Users" 그룹 UUID |
| `AUTHENTIK_ADMINS_GROUP_PK` | "authentik Admins" 그룹 UUID |

### 12.2 승인제 회원가입

#### 회원가입 플로우

```
1. 사용자 → /register 페이지에서 정보 입력
   (사용자명, 비밀번호, 표시 이름, 복구 이메일)
2. 이메일 자동 생성: {username}@namgun.or.kr
3. Authentik API → 사용자 생성 (is_active=False)
4. 포털 DB → User 레코드 생성 (is_active=False)
5. "가입 신청 완료, 관리자 승인 후 이용 가능" 안내
6. 관리자가 /admin/users 페이지에서 승인
7. Authentik → is_active=True, 포털 DB → is_active=True
8. → LDAP Outpost 자동 동기화 → Stalwart 메일 사용 가능
```

#### 검증 규칙

| 필드 | 규칙 |
|------|------|
| 사용자명 | 영문소문자+숫자+점/하이픈, 3~30자 |
| 비밀번호 | 최소 8자 |
| 복구 이메일 | `@namgun.or.kr` 차단 (외부 이메일만 허용) |

#### Authentik UID vs PK 문제

- OIDC `sub` = Authentik `uid` (SHA256 해시 문자열)
- Admin API = 숫자 `pk`
- 포털 DB에 `authentik_sub` (uid)와 `authentik_pk` (숫자) 두 필드를 별도 저장
- 회원가입 시 두 값을 모두 저장하여 이후 Admin API 호출과 OIDC 로그인이 동일 레코드를 참조

### 12.3 프로필 관리

| 엔드포인트 | 설명 |
|-----------|------|
| `PATCH /api/auth/profile` | 표시 이름, 복구 이메일 변경 (Authentik + 포털 DB 동기화) |
| `POST /api/auth/change-password` | 비밀번호 변경 (현재 비밀번호 검증 → Authentik set_password) |
| `POST /api/auth/forgot-password` | 비밀번호 찾기 (Authentik recovery 링크 생성 → 복구 이메일로 전송) |

- 비밀번호 변경: 현재 비밀번호를 `server_side_authenticate()`로 검증한 후 Authentik API로 변경
- 비밀번호 찾기: 사용자명 열거 방지를 위해 항상 동일한 성공 메시지 반환
- 복구 이메일 전송: Stalwart SMTP (port 25) 사용

### 12.4 관리자 사용자 관리

**파일**: `backend/app/admin/router.py`

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/admin/users` | 전체 사용자 목록 |
| `GET /api/admin/users/pending` | 승인 대기 목록 |
| `POST /api/admin/users/{id}/approve` | 가입 승인 (Authentik 활성화 + DB 활성화) |
| `POST /api/admin/users/{id}/reject` | 가입 거절 (Authentik + DB 삭제) |
| `POST /api/admin/users/{id}/deactivate` | 사용자 비활성화 |
| `POST /api/admin/users/{id}/set-role` | 관리자 권한 부여/해제 |

- 모든 엔드포인트는 `require_admin` 의존성으로 `is_admin` 검증
- `set-role`: Authentik "authentik Admins" 그룹에 add/remove + 포털 DB `is_admin` 동기화
- 자기보호: 자신의 권한 변경, 자기 비활성화 차단

### 12.5 관리자 권한 관리

- **관리자 그룹**: Authentik "authentik Admins" (`AUTHENTIK_ADMINS_GROUP_PK`)
- **권한 부여**: `add_user_to_group(user_pk, admins_group_pk)` → 포털 DB `is_admin=True`
- **권한 해제**: `remove_user_from_group(user_pk, admins_group_pk)` → 포털 DB `is_admin=False`
- **로그인 시 동기화**: OIDC userinfo의 `groups`에 `authentik Admins` 포함 여부로 `is_admin` 갱신

### 12.6 프론트엔드 페이지

| 페이지 | 경로 | 설명 |
|--------|------|------|
| 회원가입 | `/register` | 사용자명(+`@namgun.or.kr` 미리보기), 비밀번호, 표시 이름, 복구 이메일 |
| 비밀번호 찾기 | `/forgot-password` | 사용자명 입력 → 복구 이메일로 링크 전송 |
| 프로필 | `/profile` | 사용자 정보(읽기전용) + 표시 이름/복구 이메일 수정 + 비밀번호 변경 |
| 관리자 패널 | `/admin/users` | 승인 대기 탭 + 전체 사용자 탭 (승인/거절/비활성화/권한 토글) |

### 12.7 DB 모델 변경

User 모델에 다음 필드 추가:

| 필드 | 타입 | 설명 |
|------|------|------|
| `authentik_pk` | Integer (nullable) | Authentik Admin API 숫자 PK |
| `recovery_email` | String 255 (nullable) | 외부 복구 이메일 (비밀번호 찾기용) |

### 12.8 ISMS-P 보안 조치

- **akadmin 기본 계정 비활성화**: Authentik 기본 관리자 계정(akadmin)을 비활성화하고, `namgun18` 계정으로 Admin API 토큰을 재발급
- **API 토큰 소유자 변경**: akadmin → namgun18 (pk=5)

---

## 13. Phase 8: BBB 새 탭 회의 참여 (완료)

기존 BBB 화상회의 통합(Phase 5)에서 iframe 기반이었던 회의 참여를 새 탭(팝업) 방식으로 전환하고, 학습분석 대시보드를 추가했다.

### 13.1 새 탭 회의 참여

| 항목 | 내용 |
|------|------|
| 방식 | `window.open(joinURL, '_blank')` — 별도 탭에서 회의 참여 |
| logoutURL | 자동 닫힘 페이지 (`/bbb-close`) → 회의 종료 시 탭 자동 닫힘 |
| Greenlight 차단 | Nginx에서 BBB의 기본 웹 클라이언트(Greenlight) 직접 접속 차단 |

### 13.2 학습분석 (Learning Analytics)

- BBB 3.0 내장 Learning Analytics Dashboard를 포털 내 iframe으로 통합
- 회의 중 참여자 통계, 발화 시간, 활동 지표 등 표시
- 관리자/호스트 전용 접근

### 13.3 프론트엔드 변경

| 파일 | 변경 |
|------|------|
| `pages/meetings.vue` | iframe → 새 탭 회의 참여 + 학습분석 iframe 추가 |
| `pages/bbb-close.vue` | 회의 종료 시 자동 닫힘 페이지 (신규) |

---

## 14. Phase 9: Gitea 포털 내재화 (완료, v0.5.0)

Gitea API를 포털 백엔드에서 래핑하여, 사용자가 포털 내에서 Git 저장소를 탐색하고 코드를 열람하며 이슈/PR을 관리할 수 있도록 구현했다.

### 14.1 백엔드 아키텍처

**파일**: `backend/app/git/` 모듈

| 파일 | 역할 |
|------|------|
| `gitea.py` | httpx 기반 Gitea API 클라이언트 (비동기) |
| `router.py` | FastAPI 라우터 — 13개 엔드포인트 |
| `schemas.py` | Pydantic 응답 모델 |

### 14.2 API 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/git/repos` | 저장소 검색 (페이지네이션, 정렬) |
| `GET /api/git/repos/{owner}/{repo}` | 저장소 상세 (README 포함) |
| `GET /api/git/repos/{owner}/{repo}/contents` | 디렉토리 목록 |
| `GET /api/git/repos/{owner}/{repo}/file` | 파일 내용 (Base64 디코딩) |
| `GET /api/git/repos/{owner}/{repo}/branches` | 브랜치 목록 |
| `GET /api/git/repos/{owner}/{repo}/commits` | 커밋 이력 |
| `GET /api/git/repos/{owner}/{repo}/issues` | 이슈 목록 |
| `POST /api/git/repos/{owner}/{repo}/issues` | 이슈 생성 |
| `GET /api/git/repos/{owner}/{repo}/issues/{index}` | 이슈 상세 |
| `GET /api/git/repos/{owner}/{repo}/issues/{index}/comments` | 이슈 댓글 |
| `POST /api/git/repos/{owner}/{repo}/issues/{index}/comments` | 댓글 작성 |
| `GET /api/git/repos/{owner}/{repo}/pulls` | PR 목록 |
| `GET /api/git/repos/{owner}/{repo}/pulls/{index}` | PR 상세 |

### 14.3 프론트엔드 페이지

| 경로 | 설명 |
|------|------|
| `/git` | 저장소 목록 (검색, 정렬, 언어 필터) |
| `/git/:owner/:repo` | 저장소 상세 — 파일 트리, README 렌더링, 브랜치/커밋/이슈/PR 탭 |
| `/git/:owner/:repo/blob/:path` | 코드 뷰어 — Shiki 구문 강조, 줄번호, 파일 크기 표시 |

### 14.4 주요 기술 사항

- **Shiki 구문 강조**: 서버사이드 렌더링으로 100+ 언어 지원
- **Markdown 렌더링**: `markdown-it` + 코드 블록 구문 강조
- **대용량 파일 처리**: 1MB 초과 파일은 `too_large` 플래그로 미리보기 차단
- **Base64 디코딩**: Gitea API의 Base64 인코딩 파일 내용을 백엔드에서 디코딩

---

## 15. Phase 10: 대시보드 홈화면 리뉴얼 (완료, v0.5.1)

기존 ServiceGrid(서비스 카드 6장)만 있던 대시보드를 8개 위젯으로 구성된 종합 홈화면으로 리뉴얼했다.

### 15.1 대시보드 레이아웃

```
┌──────────────────────────────────────────────────┐
│  인사말 (시간대별) + 날짜/시간                       │
├──────────────────────────────────────────────────┤
│ ● 서비스 상태 표시줄 (6개 서비스 헬스체크)            │
├────────────────────────┬─────────────────────────┤
│ 최근 메일 (2열)        │ 빠른 바로가기 (1열)      │
│                        ├─────────────────────────┤
│                        │ 스토리지 사용량           │
├────────────────────────┼─────────────────────────┤
│ 최근 Git 활동 (2열)    │ 진행 중인 회의            │
│                        ├─────────────────────────┤
│                        │ 게임서버 상태             │
└────────────────────────┴─────────────────────────┘
```

- 데스크톱: 3열 그리드, 모바일: 1열 스택
- 각 위젯 독립 로딩 스켈레톤

### 15.2 위젯 구성

| 위젯 | 컴포넌트 | 데이터 소스 |
|------|---------|-----------|
| 인사말 | `DashboardGreeting.vue` | useAuth (user) |
| 서비스 상태 | `DashboardServiceStatus.vue` | `/api/services/status` |
| 최근 메일 | `DashboardRecentMail.vue` | `/api/mail/mailboxes` → `/api/mail/messages` |
| 최근 Git 활동 | `DashboardRecentGit.vue` | `/api/git/recent-commits` (신규) |
| 진행 중인 회의 | `DashboardMeetings.vue` | `/api/meetings/` |
| 게임서버 상태 | `DashboardGameServers.vue` | `/api/dashboard/game-servers` (신규) |
| 스토리지 | `DashboardStorage.vue` | `/api/files/info` |
| 빠른 바로가기 | `DashboardShortcuts.vue` | 라우팅만 |

### 15.3 신규 백엔드 API

#### `GET /api/git/recent-commits?limit=5`

- 최근 업데이트된 5개 저장소에서 각 3개 커밋을 **병렬**(`asyncio.gather`)로 가져옴
- 시간순 정렬 후 최대 20개 캐싱
- **인메모리 TTL 캐시**: 120초 — 첫 요청만 Gitea API 호출, 이후 캐시 반환

#### `GET /api/dashboard/game-servers`

- Docker 소켓(`/var/run/docker.sock:ro`)으로 `game-panel.managed=true` 라벨 컨테이너 조회
- **읽기 전용**: 컨테이너 제어 불가, 상태 조회만 수행
- 실패 시 빈 배열 반환 (graceful fallback)

### 15.4 스토리지 용량 표시 개선

- `shutil.disk_usage()`로 NFS 볼륨 전체 용량/사용량 즉시 조회 (기존 `rglob("*")` 트리 워크 제거)
- 대시보드: 퍼센트 게이지 바 + 전체 용량 표시
- 파일 브라우저 사이드바: 동일한 퍼센트 게이지 바 추가
- 색상 코드: 70% 이하 초록, 70~90% 노랑, 90% 이상 빨강

### 15.5 Stalwart 헬스체크 수정

- Stalwart v0.15에서 `/healthz` → 404 반환 확인
- `/health/liveness` → 200 반환으로 URL 변경
- `backend/app/services/health.py` 수정

### 15.6 공통 유틸리티

**파일**: `frontend/lib/date.ts`

| 함수 | 설명 |
|------|------|
| `timeAgo(dateStr)` | 상대 시간 표시 (방금 전, N분 전, N시간 전, N일 전) |
| `formatSize(bytes)` | 바이트 → 사람이 읽을 수 있는 크기 (B, KB, MB, GB, TB) |

---

## 16. Phase 11: 비주얼 리프레시 (완료, v0.5.2)

기존 포털 UI의 단조로운 시각 요소를 개선하여, 색상 팔레트 분리, 카드/버튼 인터랙션, 그라디언트 히어로 카드, 위젯별 색상 아이콘을 적용하였다.

### 16.1 색상 팔레트 리뉴얼

기존에 `primary`, `accent`, `secondary`, `muted`가 모두 동일한 회색 계열(HSL `210 40% 96.1%`)이어서 시각적 구분이 불가능했던 문제를 해결하였다.

**Light 모드 핵심 변경** (`frontend/assets/css/main.css`):

| 변수 | 이전 | 이후 | 설명 |
|------|------|------|------|
| `--primary` | `222.2 47.4% 11.2%` (거의 검정) | `221 83% 53%` (#3B82F6) | 선명한 블루 |
| `--accent` | `210 40% 96.1%` (primary와 동일) | `214 95% 93%` (#DBEAFE) | 연한 블루 |
| `--ring` | `222.2 84% 4.9%` | `221 83% 53%` | primary 맞춤 |

**Dark 모드 핵심 변경**:

| 변수 | 이전 | 이후 |
|------|------|------|
| `--primary` | `210 40% 98%` | `217 91% 60%` (#60A5FA) |
| `--accent` | `217.2 32.6% 17.5%` | `217 50% 20%` |
| `--ring` | `212.7 26.8% 83.9%` | `217 91% 60%` |

`secondary`, `muted`는 중립 회색 역할을 유지하기 위해 변경하지 않았다.

### 16.2 카드/버튼 인터랙션

| 컴포넌트 | 변경 내용 |
|---------|----------|
| `Card.vue` | `hover:shadow-md transition-shadow duration-200` 추가 — 마우스 오버 시 그림자 전환 |
| `Button.vue` | `active:scale-[0.98]` 클릭 축소 피드백, `transition-all`, default variant에 `shadow-sm hover:shadow-md` |

### 16.3 그라디언트 히어로 카드

대시보드 인사말을 플레인 텍스트에서 그라디언트 배경 카드로 전환하였다.

- **Light 모드**: `bg-gradient-to-r from-blue-600 to-indigo-600` 블루→인디고 그라디언트, 흰 텍스트
- **Dark 모드**: `from-blue-500/20 to-indigo-500/20` 반투명 그라디언트 + `border-blue-500/30` 보더

### 16.4 헤더 그라디언트 라인

AppHeader 하단에 2px 그라디언트 라인 추가:

```html
<div class="h-0.5 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-80" />
```

### 16.5 바로가기 아이콘 색상 배경

각 바로가기 아이콘에 고유한 색상의 원형 배경을 적용하였다.

| 바로가기 | 색상 | 클래스 |
|---------|------|--------|
| 메일 쓰기 | 블루 | `bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400` |
| 회의 시작 | 그린 | `bg-green-100 text-green-600 dark:bg-green-500/20 dark:text-green-400` |
| 파일 업로드 | 앰버 | `bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400` |
| Git 저장소 | 퍼플 | `bg-purple-100 text-purple-600 dark:bg-purple-500/20 dark:text-purple-400` |

### 16.6 위젯 카드 헤더 색상 아이콘

대시보드 위젯 카드의 제목 옆에 각 서비스를 상징하는 색상 SVG 아이콘을 추가하였다.

| 위젯 | 아이콘 | 색상 |
|------|--------|------|
| 최근 메일 | mail (봉투) | `text-blue-500` |
| 최근 Git | git-branch | `text-purple-500` |
| 진행 중인 회의 | video | `text-green-500` |
| 게임서버 | gamepad-2 | `text-orange-500` |
| 스토리지 | hard-drive | `text-teal-500` |

### 16.7 수정 파일 목록 (14개)

| # | 파일 | 변경 |
|---|------|------|
| 1 | `frontend/assets/css/main.css` | 색상 팔레트 리뉴얼 |
| 2 | `frontend/components/ui/Card.vue` | 호버 그림자 전환 |
| 3 | `frontend/components/ui/Button.vue` | 클릭 피드백, 그림자 |
| 4 | `frontend/components/layout/AppHeader.vue` | 그라디언트 라인 |
| 5 | `frontend/pages/index.vue` | 위젯 간격 확대 (gap-4 → gap-5) |
| 6 | `frontend/components/dashboard/DashboardGreeting.vue` | 그라디언트 히어로 카드 |
| 7 | `frontend/components/dashboard/DashboardServiceStatus.vue` | checking 상태 pulse 애니메이션 |
| 8 | `frontend/components/dashboard/DashboardShortcuts.vue` | 아이콘 색상 원형 배경 |
| 9–13 | `Dashboard{RecentMail,RecentGit,Meetings,GameServers,Storage}.vue` | 헤더 색상 아이콘 |
| 14 | `frontend/tailwind.config.ts` | keyframes 확장 (필요 시) |

---

## 17. Phase 12: 인프라 보안 강화 (완료)

전 서버 취약점 스캔을 실시하고, 발견된 문제점을 서비스 무중단으로 즉시 조치하였다.

### 17.1 취약점 스캔 대상

| 서버 | 호스트 | 스캔 항목 |
|------|--------|----------|
| Nginx 리버스 프록시 | 192.168.0.150 | SSL/TLS, 보안 헤더, 방화벽, OS 패치 |
| 메일서버 | 192.168.0.250 | SSL/TLS, SELinux, 방화벽, OS 패치 |
| Docker 호스트 (WSL2) | 192.168.0.50 | Docker 이미지, 미사용 리소스 |
| 공개 도메인 (6개) | namgun/meet/file/game/mail/git | SSL 인증서, TLS 버전, 보안 헤더 |

### 17.2 CSP(Content-Security-Policy) 헤더 추가

전 사이트에 CSP 헤더가 누락되어 있었으며, 각 사이트 특성에 맞는 정책을 적용하였다.

| 사이트 | CSP 주요 정책 |
|--------|-------------|
| namgun.or.kr | `frame-src https://meet.namgun.or.kr https://mail.namgun.or.kr` (회의/메일 iframe 허용) |
| file.namgun.or.kr | `img-src 'self' data: blob:` (파일 미리보기 blob 허용) |
| game.namgun.or.kr | 기본 `default-src 'self'` |
| git.namgun.or.kr | `img-src 'self' data: https:; font-src 'self' data:` (외부 이미지/폰트 허용) |
| auth.namgun.or.kr | 기본 `default-src 'self'` |

### 17.3 누락된 보안 헤더 보완

| 사이트 | 추가된 헤더 |
|--------|-----------|
| file.namgun.or.kr | `X-XSS-Protection`, `Permissions-Policy` |
| game.namgun.or.kr | `X-XSS-Protection`, `Permissions-Policy`, `server_tokens off`, `proxy_hide_header Server` |
| meet.namgun.or.kr | `Permissions-Policy` (`camera=(self), microphone=(self)` — BBB 마이크/카메라 허용) |

### 17.4 방화벽 (firewalld) 활성화

| 서버 | 이전 상태 | 조치 | 허용 포트 |
|------|----------|------|----------|
| Nginx (192.168.0.150) | masked (비활성) | `systemctl unmask && enable --now` | http, https, ssh, 9090(cockpit) |
| Mail (192.168.0.250) | not loaded | `dnf install && enable --now` | ssh, smtp(25), smtps(465), submission(587), imaps(993), https(443), 8080 |

### 17.5 SELinux 상태 개선

| 서버 | 이전 | 조치 | 비고 |
|------|------|------|------|
| Nginx (192.168.0.150) | Enforcing | 유지 | 정상 |
| Mail (192.168.0.250) | Disabled | → Permissive (설정 변경, 재부팅 시 적용) | `/etc/selinux/config` 수정 |

### 17.6 OS 보안 패치 적용

| 서버 | 패치 내용 |
|------|----------|
| Nginx (192.168.0.150) | openssl, python3-urllib3, kernel 등 90+ 패키지 보안 업데이트 |
| Mail (192.168.0.250) | kernel, python3-urllib3 등 보안 업데이트 |

> **참고**: 커널 업데이트 적용 완료. 재부팅 시 신규 커널 로드 예정 (서비스 무중단 운영 중).

### 17.7 임시 테스트 페이지 정리

Phase 0에서 방화벽 테스트용으로 생성했던 `test.namgun.or.kr:47264` 관련 자원을 모두 정리하였다.

| 항목 | 조치 |
|------|------|
| Nginx 설정 | `test.namgun.or.kr.conf`, `test-acme.conf` 삭제 |
| TLS 인증서 | `certbot delete --cert-name test.namgun.or.kr` |
| SELinux 포트 | `semanage port -d -t http_port_t -p tcp 47264` |
| 웹 디렉토리 | `/var/www/test-page` 삭제 |

### 17.8 Docker 정리

| 항목 | 조치 |
|------|------|
| 미사용 이미지 | `docker image prune -a` (약 2GB 회수) |
| 빌드 캐시 | `docker builder prune -a` |

---

## 18. 핵심 트러블슈팅 정리

| # | 문제 | 원인 | 해결 방법 |
| 23 | Git recent-commits 응답 지연 | 50개 저장소를 순차 조회 | 5개로 축소 + asyncio.gather 병렬 + 120초 인메모리 TTL 캐시 |
| 24 | 스토리지 용량 조회 지연 | `rglob("*")` NFS 트리 워크 | `shutil.disk_usage()` 즉시 조회로 변경 |
| 25 | Stalwart 헬스체크 항상 실패 | v0.15에서 `/healthz` → 404 | `/health/liveness` (200)로 URL 변경 |
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
| 19 | `recovery_email` 컬럼 누락 (500 오류) | `create_all()`은 기존 테이블에 컬럼 추가 불가 | `ALTER TABLE users ADD COLUMN` 수동 실행 |
| 20 | `authentik_sub` 불일치 (중복 레코드) | 회원가입 시 Authentik PK(정수)를 `authentik_sub`에 저장, OIDC 로그인은 uid(해시) 저장 | `authentik_pk` 별도 컬럼 추가, `authentik_sub`에는 uid만 저장 |
| 21 | Gitea OAuth `id_token` 누락 | 포털 OIDC 토큰 응답에 `id_token`이 없음 | 토큰 엔드포인트에 JWT `id_token` 추가 |
| 22 | Gitea OAuth `redirect_uri` 불일치 | `.env`에 `/callback` 누락 | `redirect_uris`에 `/user/oauth2/portal/callback` 전체 경로 등록 |

---

## 19. 잔여 작업 항목

### 19.1 즉시 조치 필요

- [x] DKIM `dkim=pass` 확인 (DNS 캐시 만료 후)
- [ ] PTR 레코드 등록 (SK 브로드밴드, `211.244.144.69 → mail.namgun.or.kr`)
- [ ] `mail.namgun.or.kr`에 대한 SPF TXT 레코드 추가 (SPF_HELO_NONE 해결)
- [ ] Authentik 계정 비밀번호 설정: tsha, nahee14, kkb
- [ ] Nginx/Mail 서버 커널 재부팅 (보안 패치 적용 완료, 신규 커널 로드 필요)
- [ ] 메일서버 SELinux Enforcing 전환 (재부팅 후 서비스 정상 확인 필요)

### 19.2 완료된 항목

| 항목 | 완료 단계 |
|------|----------|
| 포털 코어 개발 (Nuxt 3 + FastAPI) | Phase 3 |
| 파일 브라우저 (NFS 연동) | Phase 4 |
| BBB 화상회의 통합 | Phase 5 |
| Stalwart Mail iframe 통합 | Phase 5 |
| 네이티브 로그인 폼 | Phase 6 |
| Popup Bridge SSO | Phase 6 |
| Gitea SSO 연동 | Phase 6 |
| 서버사이드 네이티브 로그인 전환 | Phase 6.5 |
| 포털 OIDC 제공자 (Gitea SSO) | Phase 6.5 |
| 승인제 회원가입 | Phase 7 |
| 프로필/비밀번호 관리 | Phase 7 |
| 관리자 사용자 관리 패널 | Phase 7 |
| 관리자 권한 할당 (RBAC) | Phase 7 |
| akadmin 기본 계정 비활성화 (ISMS-P) | Phase 7 |
| BBB 새 탭 회의 참여 + 자동 닫힘 | Phase 8 |
| Greenlight 직접 접속 차단 | Phase 8 |
| 학습분석 대시보드 (iframe) | Phase 8 |
| Gitea API 래핑 (13개 엔드포인트) | Phase 9 |
| 저장소 탐색 + 코드 뷰어 (Shiki 구문 강조) | Phase 9 |
| 이슈/PR 관리 | Phase 9 |
| 대시보드 8개 위젯 리뉴얼 | Phase 10 |
| 게임서버 상태 조회 (Docker 소켓) | Phase 10 |
| 스토리지 용량 퍼센트 게이지 | Phase 10 |
| Git recent-commits 인메모리 캐시 | Phase 10 |
| Stalwart 헬스체크 URL 수정 | Phase 10 |
| 색상 팔레트 분리 (primary/accent/ring) | Phase 11 |
| 카드/버튼 호버·클릭 인터랙션 | Phase 11 |
| 그라디언트 히어로 카드 + 헤더 라인 | Phase 11 |
| 대시보드 위젯 색상 아이콘 | Phase 11 |
| CSP 헤더 전 사이트 적용 | Phase 12 |
| firewalld 방화벽 활성화 (Nginx + Mail) | Phase 12 |
| OS 보안 패치 적용 (Nginx + Mail) | Phase 12 |
| 임시 테스트 페이지 정리 (test.namgun.or.kr) | Phase 12 |
| Docker 미사용 이미지/캐시 정리 | Phase 12 |

### 19.3 향후 계획

| 항목 | 내용 | 예상 기술 스택 |
|------|------|---------------|
| MFA 추가 | Authentik MFA 플로우 연동 + 포털 UI에서 challenge 처리 | Authentik Flow Executor + TOTP/WebAuthn |
| Game Panel 포털 통합 | 게임 서버 관리를 포털 내에서 직접 수행 (현재 상태 조회만 완료) | 포털 API + Game Panel API 연동 |
| CalDAV / CardDAV | 캘린더/연락처 동기화 | Stalwart 내장 또는 별도 서버 |
| 데모 사이트 | demo.namgun.or.kr 공개 데모 환경 구축 | Nuxt 3 + FastAPI (읽기 전용 모드) |
| Naver Works급 ERP | 조직 관리, 결재, 메신저 등 그룹웨어 기능 | 장기 목표 |

---

## 20. 기술 스택 요약

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

## 21. 보안 고려사항

### 21.1 적용된 보안 정책

- ISMS-P 기준 보안 헤더 전 사이트 적용
- TLS 1.2+ 강제 (HSTS preload)
- 서버 정보 노출 차단 (`server_tokens off`, `X-Powered-By` / `Server` 헤더 제거)
- 스캐너/봇 차단 규칙
- DKIM + SPF + DMARC 이메일 인증 체계
- PKCE S256 인증 코드 보호 (replay 공격 방지)
- 서명된 세션 쿠키 (itsdangerous, httponly, secure, samesite=lax)
- 파일 시스템 path traversal 방지 (resolve + prefix 검증)
- 리다이렉트 URL 도메인 화이트리스트 (`*.namgun.or.kr`)
- CSP(Content-Security-Policy) 전 사이트 적용 (Phase 12)
- firewalld 방화벽 전 서버 활성화 (Phase 12)
- 정기 OS 보안 패치 적용 (Phase 12)

### 21.2 계획된 보안 강화

- PTR 레코드 등록으로 역방향 DNS 검증 완성
- Authentik MFA(다중 인증) 정책 강화
- 메일서버 SELinux Permissive → Enforcing 전환 (재부팅 후 검증 필요)

---

*문서 끝. 최종 갱신: 2026-02-22*
