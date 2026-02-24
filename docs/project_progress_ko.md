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
| v1.5 | 2026-02-22 | 남기완 | Phase 13(LocalStack Lab — AWS IaC 학습 환경) 추가 |
| v1.6 | 2026-02-22 | 남기완 | Phase 14(UI 개선 및 SSR 인증 수정) 추가 |
| v1.7 | 2026-02-22 | 남기완 | Phase 15 (캘린더/연락처 + 데모 사이트) 추가 |
| v1.8 | 2026-02-22 | 남기완 | v0.7.1 데모 사이트 버그 수정 + Nginx 캐시 헤더 강화 추가 |
| v1.9 | 2026-02-22 | 남기완 | Stalwart + LDAP Outpost 네이티브 마이그레이션 (Podman → systemd) |
| v2.0 | 2026-02-22 | 남기완 | **v1.0.0 정식 릴리즈** — SELinux Enforcing, 잔여 작업 정리, WSL Docker 포트 자동복구 |
| v2.1 | 2026-02-23 | 남기완 | Phase 16: 보안 취약점 감사 및 수정 (Critical 4건 + High 4건 + Medium 9건) |
| v2.2 | 2026-02-23 | 남기완 | Phase 17: JMAP 계정 매핑 버그 수정, 관리자 가입 알림, Lab UI 수정, SMTP 대안 조사 |
| v2.3 | 2026-02-23 | 남기완 | Phase 17 확장: 메일 전수 감사, JMAP EmailSubmission identityId 수정, 워치독 연쇄 재시작 해결 |
| v2.4 | 2026-02-24 | 남기완 | Phase 18: 관리 대시보드 — 방문자 분석 + 서비스 현황 모니터링 (v1.1.0) |

---

## 1. 프로젝트 개요

namgun.or.kr 종합 포털은 가정 및 소규모 조직을 위한 셀프 호스팅 통합 플랫폼이다. Authentik을 중앙 Identity Provider(IdP)로 두고, Git 저장소, 원격 데스크톱, 메일, 화상회의, 파일 관리, 게임 서버 등 다양한 서비스를 SSO(Single Sign-On)로 통합하는 것을 목표로 한다.

### 1.1 핵심 목표

- 모든 서비스에 대한 SSO 인증 통합 (OIDC / LDAP)
- ISMS-P 보안 기준에 준하는 인프라 구성
- 셀프 호스팅 기반의 데이터 주권 확보
- 단계적 서비스 확장 (Phase 0 ~ Phase 15)

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
| Phase 13 | LocalStack Lab — AWS IaC 학습 환경 | **완료** | — | Terraform IaC, 사용자별 LocalStack 컨테이너, 토폴로지 시각화, 템플릿, CI/CD |
| Phase 14 | UI 개선 및 SSR 인증 수정 | **완료** | — | Lab 좌우 분할·리사이즈, 메일 팝업 작성·서명 선택, SSR 쿠키 전달, Nginx 캐시 제어 (v0.6.1) |
| Phase 15 | 캘린더/연락처 + 데모 사이트 | **완료** | — | JMAP 캘린더/연락처, 캘린더 공유, CalDAV/CardDAV, demo.namgun.or.kr (v0.7.0 → v0.7.1) |
| Phase 16 | 보안 취약점 감사 및 수정 | **완료** | — | 전체 코드 보안 감사, Critical 4건 + High 4건 + Medium 9건 수정, Rate Limiting 도입 |
| Phase 17 | 메일 시스템 버그 수정 및 안정화 | **완료** | — | JMAP base-26 버그, 관리자 알림, EmailSubmission identityId, 전수 감사(C4+H5), 워치독 연쇄 재시작 해결 |
| Phase 18 | 관리 대시보드 — 방문자 분석 + 서비스 모니터링 | **완료** | — | AccessLog 미들웨어, GeoIP, Chart.js, 10개 분석 엔드포인트, 데모 mock (v1.1.0) |

---

## 3. 인프라 토폴로지

### 3.1 물리/논리 구성도

```
인터넷 (SK브로드밴드, AS17613)
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  Check Point Quantum Security Gateway 3100                      │
│  (IPS / Anti-Bot / SandBlast Threat Prevention / URL Filtering) │
│  평가판 라이센스 (파트너사 무제한 갱신)                             │
└──────────────────────┬──────────────────────────────────────────┘
  │                    │
  ├─ 211.244.144.47 (공인 IP, 메인 서비스)
  │    └─ 포트포워딩 → 192.168.0.150 (Nginx Reverse Proxy)
  │
  ├─ 211.244.144.69 (공인 IP, MX 레코드)
  │    └─ 직접 연결 → 192.168.0.250 (Stalwart Mail)
  │
  ┌──── MikroTik CRS317-1G-16S+ (10G SFP+ x16 스위치) ──────────┐
  │          내부망 192.168.0.0/24 — 10Gbps SFP+ 백본              │
  │                                                                │
  │  [192.168.0.50] Windows Host — 메인 서버                       │
  │    HW: Dual Xeon Gold 6138 (40C/80T), 128GB DDR4 ECC          │
  │        ASUS 서드파티 서버보드, 4U 산업용 케이스                   │
  │        Intel X520-DA2 10G SFP+ NIC                             │
  │        전체 팬 Noctua 교체 (정숙 운영)                           │
  │    SW: Windows Server / Hyper-V                                │
  │    └─ WSL2 (192.168.0.150) / Docker                            │
  │       ├─ Authentik (server + worker + PostgreSQL 16)           │
  │       ├─ Portal Stack                                          │
  │       │    ├─ portal-frontend (Nuxt 3 SSR, :3000)             │
  │       │    ├─ portal-backend (FastAPI, :8000)                  │
  │       │    ├─ portal-db (PostgreSQL 16, named volume)          │
  │       │    └─ portal-nginx (내부 리버스 프록시, :8080)           │
  │       ├─ Gitea 1.25.4                                          │
  │       ├─ RustDesk Pro (hbbs + hbbr)                            │
  │       ├─ Game Panel (backend + nginx + palworld)               │
  │       ├─ LocalStack Lab (사용자별 동적 컨테이너, lab-net)       │
  │       └─ Demo Frontend (Nuxt 3 SSR, :3001, demo mode)         │
  │                                                                │
  │  [192.168.0.50] Hyper-V VM — Nginx (Rocky Linux 10)           │
  │    └─ 중앙 리버스 프록시, TLS Termination (192.168.0.150)       │
  │                                                                │
  │  [192.168.0.50] Hyper-V VM — Mail (Rocky Linux 9.7)           │
  │    IP: 192.168.0.250 / SELinux Enforcing                       │
  │    └─ 네이티브 systemd 서비스                                    │
  │       ├─ stalwart-mail.service (v0.15.5)                       │
  │       └─ authentik-ldap-outpost.service (2025.10.4)            │
  │                                                                │
  │  [192.168.0.249] Hyper-V VM — BigBlueButton 3.0 (화상회의)     │
  │    └─ BBB API (SHA256 checksum 인증)                            │
  │                                                                │
  │  [192.168.0.100] OMV (OpenMediaVault) — NAS                   │
  │    └─ NFSv4 서버 (/export/root, fsid=0)                        │
  │       └─ /portal → Docker NFS volume (/storage)                │
  │                                                                │
  │  [192.168.0.251] Pi-Hole DNS (내부 1차 DNS)                    │
  │                                                                │
  │  [게임용 PC] ── Intel X520-DA2 10G SFP+ ── 서버 직결            │
  │                                                                │
  └────────────────────────────────────────────────────────────────┘

네트워크 사양:
  - WAN: SK브로드밴드 고정 공인IP x2 (211.244.144.47, .69)
  - LAN: 10Gbps SFP+ (서버↔PC↔NAS), DAC/광모듈 직결
  - 보안: Check Point IPS + Threat Prevention → firewalld → SELinux (다층 방어)
  - DNS: Pi-Hole (내부) + Windows Server DNS (AD) + 공인 DNS (namgun.or.kr)
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
| Stalwart Mail | mail.namgun.or.kr | 192.168.0.250 (네이티브 systemd) | LDAP + OIDC, 포털 내 iframe 통합 | 운영 중 |
| LDAP Outpost | — | 192.168.0.250 (네이티브 systemd) | Authentik → Stalwart LDAP 인증 | 운영 중 |
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

## 18. Phase 13: LocalStack Lab — AWS IaC 학습 환경 (완료)

AWS 서비스를 로컬에서 에뮬레이션하는 LocalStack과 Terraform IaC를 결합한 학습 환경을 포털에 통합하였다. 사용자별 격리된 LocalStack 컨테이너를 제공하며, Terraform을 통해 AWS 리소스를 선언적으로 관리하고 토폴로지를 시각화한다.

### 18.1 핵심 설계 원칙

| 원칙 | 설명 |
|------|------|
| IaC First | Terraform HCL 코드를 통한 리소스 관리가 핵심. 클릭 기반 UI는 보조 |
| 사용자 격리 | 사용자별 전용 LocalStack Docker 컨테이너 (2GB RAM, 2 CPU 제한) |
| 테넌트 공유 | 환경을 다른 사용자에게 초대 가능 (멤버 관리) |
| 백엔드 중계 | 모든 AWS/Terraform 명령은 백엔드를 경유, 프론트엔드 직접 접근 불가 |

### 18.2 지원 AWS 서비스 (초보 친화 6종)

| 서비스 | 용도 | 주요 기능 |
|--------|------|-----------|
| S3 | 오브젝트 스토리지 | 버킷 CRUD, 파일 업로드/삭제 |
| SQS | 메시지 큐 | 큐 CRUD, 메시지 발송/수신 |
| Lambda | 서버리스 함수 | Python 함수 생성/실행 |
| DynamoDB | NoSQL DB | 테이블 CRUD, 아이템 스캔 |
| SNS | 알림 | 토픽 생성, SQS 구독, 메시지 발행 |
| IAM | 권한 관리 | 유저/역할/정책 조회 (읽기 전용) |

### 18.3 Terraform IaC 통합

| 항목 | 내용 |
|------|------|
| Terraform 버전 | 1.9.8 (백엔드 Docker 이미지에 포함) |
| 워크플로 | Init → Plan → Apply → Destroy |
| provider.tf | 환경별 자동 생성 (LocalStack 엔드포인트 주입, 읽기 전용) |
| 사용자 파일 | `main.tf` 기본 제공, 추가 `.tf` 파일 자유 생성/삭제 |
| 플러그인 캐시 | `TF_PLUGIN_CACHE_DIR=/tmp/tf-plugin-cache` 공유 |
| 실행 제한 | 180초 타임아웃, `-no-color`, `TF_IN_AUTOMATION=1` |

### 18.4 사전 정의 템플릿 (5종)

| 템플릿 | 내용 |
|--------|------|
| S3 정적 웹사이트 | S3 버킷 + 웹사이트 호스팅 설정 + index.html 업로드 |
| Lambda 함수 | Python Lambda 함수 + IAM 역할 + CloudWatch 로그 그룹 |
| SQS + SNS | SNS 토픽 + SQS 큐 + 구독 연결 |
| DynamoDB 테이블 | DynamoDB 테이블 + GSI (Global Secondary Index) |
| 풀스택 (S3 + Lambda + DynamoDB) | S3 + Lambda + DynamoDB + IAM 역할을 결합한 서버리스 패턴 |

### 18.5 토폴로지 시각화

cytoscape.js + dagre 레이아웃을 사용하여 AWS 리소스 관계를 그래프로 표시한다.

| 항목 | 내용 |
|------|------|
| 라이브러리 | cytoscape 3.30, cytoscape-dagre 2.5, dagre 0.8 |
| 노드 색상 | S3=초록, Lambda=주황, SQS=보라, DynamoDB=파랑, SNS=빨강, IAM=회색 |
| 엣지 발견 | Lambda event source mappings, SNS subscriptions |
| 자동 새로고침 | 10초 간격 폴링 (토글 가능) |
| 레이아웃 | dagre 계층형 (기본) |

### 18.6 CI/CD 배포 엔드포인트

Git 기반 CI/CD를 위한 배포 API를 제공한다.

```
POST /api/lab/environments/{id}/terraform/deploy
Body: { "files": { "main.tf": "...", "network.tf": "..." } }
→ init → plan → apply 자동 실행
```

### 18.7 DB 모델

| 모델 | 필드 | 역할 |
|------|------|------|
| `LabEnvironment` | id, owner_id, name, container_name, container_id, status, created_at | 환경 메타데이터 |
| `LabMember` | id, environment_id, user_id, role, invited_at | 멤버 관리 (owner/member) |

### 18.8 API 엔드포인트 (26개)

| 분류 | 엔드포인트 | 설명 |
|------|-----------|------|
| 환경 관리 | `GET/POST /api/lab/environments` | 목록 조회 / 생성 |
| | `GET/DELETE /api/lab/environments/{id}` | 상세 / 삭제 |
| | `POST .../start`, `POST .../stop` | 시작 / 중지 |
| 멤버 | `POST/DELETE .../members` | 초대 / 제거 |
| Terraform | `GET/PUT .../terraform/files` | 파일 조회 / 저장 |
| | `POST .../terraform/{init,plan,apply,destroy}` | 명령 실행 |
| | `GET .../terraform/templates` | 템플릿 목록 |
| | `POST .../terraform/deploy` | CI/CD 배포 |
| 토폴로지 | `GET .../topology` | 리소스 그래프 |
| 리소스 | `GET/POST/DELETE .../resources/{service}` | CRUD |
| S3/SQS/Lambda/DynamoDB/SNS | 서비스별 전용 엔드포인트 | 상세 작업 |

### 18.9 프론트엔드 구성

| 컴포넌트 | 역할 |
|---------|------|
| `pages/lab.vue` | 메인 페이지 (사이드바 + Terraform/리소스 탭) |
| `composables/useLab.ts` | 상태 관리 (환경, Terraform, 토폴로지) |
| `components/lab/LabSidebar.vue` | 환경 목록, 생성, 시작/중지/삭제 |
| `components/lab/LabTerraform.vue` | HCL 코드 에디터, 파일 탭, 실행 버튼, 출력 터미널 |
| `components/lab/LabTopology.vue` | cytoscape.js 토폴로지 그래프 |
| `components/lab/LabResourcePanel.vue` | 서비스별 리소스 CRUD (S3/SQS/Lambda/DynamoDB/SNS) |
| `components/lab/LabMemberDialog.vue` | 멤버 초대/관리 다이얼로그 |

### 18.10 Docker 인프라 변경

| 항목 | 변경 |
|------|------|
| Docker socket | `:ro` → `:rw` (컨테이너 생성/관리 필요) |
| 네트워크 | `lab-net` 추가 (LocalStack + backend 통신용) |
| backend 이미지 | Terraform 1.9.8 + Git 설치 추가 |
| 컨테이너 제한 | 사용자당 최대 5개 환경, 각 2GB RAM / 2 CPU |

### 18.11 수정/생성 파일 (17개)

| # | 파일 | 구분 |
|---|------|------|
| 1 | `backend/Dockerfile` | 수정 (Terraform + Git 설치) |
| 2 | `backend/app/db/models.py` | 수정 (LabEnvironment + LabMember) |
| 3 | `backend/app/main.py` | 수정 (lab_router 등록) |
| 4 | `backend/requirements.txt` | 수정 (boto3 추가) |
| 5 | `docker-compose.yml` | 수정 (socket rw + lab-net) |
| 6 | `frontend/package.json` | 수정 (cytoscape 추가) |
| 7 | `frontend/components/layout/AppHeader.vue` | 수정 (Lab 네비게이션) |
| 8 | `backend/app/lab/__init__.py` | 신규 |
| 9 | `backend/app/lab/docker_manager.py` | 신규 (Docker 라이프사이클) |
| 10 | `backend/app/lab/aws_client.py` | 신규 (boto3 래퍼) |
| 11 | `backend/app/lab/router.py` | 신규 (API 라우터) |
| 12 | `backend/app/lab/schemas.py` | 신규 (Pydantic 스키마) |
| 13 | `backend/app/lab/terraform_manager.py` | 신규 (Terraform 워크스페이스) |
| 14 | `frontend/pages/lab.vue` | 신규 (메인 페이지) |
| 15 | `frontend/composables/useLab.ts` | 신규 (상태 관리) |
| 16 | `frontend/components/lab/*.vue` (4개) | 신규 (UI 컴포넌트) |

---

## 19. Phase 14: UI 개선 및 SSR 인증 수정 (완료, v0.6.1)

포털 UI의 사용성을 전면 개선하고, SSR 환경에서 인증 쿠키가 전달되지 않던 근본적 문제를 해결하였다.

### 19.1 Lab 페이지 좌우 분할 레이아웃

기존 상하 배치(에디터 위 / 토폴로지 아래)에서 **데스크톱(lg+) 좌우 분할**로 변경하여 코드와 토폴로지를 동시에 확인 가능하게 개선하였다.

```
데스크톱 (lg+):
┌─────────┬──────────────────┬──────────────────┐
│         │ Terraform        │ Topology         │
│ Sidebar │ (에디터 + 출력)   │ (그래프)          │
│         │                  ├──────────────────┤
│         │                  │ Resources (접기)  │
└─────────┴──────────────────┴──────────────────┘

모바일 (<lg): 기존 상하 스택 + 탭 전환 유지
```

- **드래그 리사이즈**: 토폴로지와 리소스 패널 사이를 마우스 드래그로 분할 비율 조정 가능
- **리소스 패널 접기**: 버튼 클릭으로 리소스 패널을 완전히 접어 토폴로지 전체 표시

### 19.2 메일 작성 팝업 창

기존 Teleport 모달(같은 페이지 오버레이)에서 **`window.open()` 별도 팝업 창**으로 변경하여, 메일 목록을 확인하면서 작성할 수 있도록 개선하였다.

| 항목 | 내용 |
|------|------|
| 새 파일 | `frontend/pages/mail/compose.vue` (독립 페이지, layout 없음) |
| 팝업 크기 | 700×600px |
| 전달 방식 | 쿼리 파라미터: `?mode=new\|reply\|replyAll\|forward&msgId=...` |
| 전송 완료 | `window.close()` + 부모 창에 `postMessage`로 목록 새로고침 신호 |

#### 서명 선택 기능

- 본문 에디터 하단에 서명 드롭다운 추가
- 기존 `useMailSignature()` 컴포저블과 연동
- 기본 서명 자동 삽입, 서명 변경 시 본문 하단 교체
- "서명 없음" 옵션 포함

### 19.3 메일 리스트 번호 컬럼

메일 목록에 **순번 컬럼**을 추가하여 페이지네이션 시에도 전체 목록 기준 일관된 번호를 표시한다.
- 번호 산출: `(currentPage - 1) * limit + index + 1`
- 모바일(sm 이하)에서는 자동 숨김

### 19.4 전체 뷰포트 레이아웃 조정

| 변경 사항 | 설명 |
|-----------|------|
| 컨테이너 제약 제거 | `max-w-7xl` 컨테이너 → 전체 너비 사용 |
| 푸터 제거 | `AppFooter.vue` 비활성화, 페이지 영역 극대화 |
| 프로필 2열 그리드 | lg 이상에서 프로필 카드를 2열 `grid-cols-2`로 배치 |
| flex overflow 수정 | 중첩 flex 컨테이너에 `min-h-0` 추가하여 스크롤 체인 정상 작동 |

### 19.5 SSR 쿠키 전달 수정

| 항목 | 내용 |
|------|------|
| 문제 | Nuxt 3 SSR에서 `$fetch('/api/auth/me')` 호출 시 브라우저 쿠키 미포함 → 서버에서 미인증 판정 → 새로고침 시 홈으로 리다이렉트 |
| 원인 | SSR 단계에서 `$fetch`는 서버-to-서버 호출이므로 브라우저의 `Set-Cookie`가 자동 전달되지 않음 |
| 해결 | `useRequestHeaders(['cookie'])`로 요청 헤더를 캡처, `$fetch` 옵션에 `headers: { cookie }` 전달 |
| 수정 파일 | `frontend/composables/useAuth.ts` |

### 19.6 Nginx 캐시 제어

| 위치 | Cache-Control 헤더 |
|------|-------------------|
| `/_nuxt/` (정적 에셋) | `public, max-age=31536000, immutable` (content-hash 파일명으로 무효화 보장) |
| `/` (HTML/SSR) | `no-cache, no-store, must-revalidate` (항상 최신 HTML 응답) |

### 19.7 기타 수정

- **대시보드 메일 바로가기**: `navigateTo('/mail')` 제거 (팝업 전환으로 불필요)
- **DB 초기화 재시도**: PostgreSQL 연결 실패 시 5회 재시도 로직 추가

### 19.8 수정 파일 목록

| # | 파일 | 구분 |
|---|------|------|
| 1 | `frontend/pages/lab.vue` | 수정 (좌우 분할 + 드래그 리사이즈) |
| 2 | `frontend/pages/mail/compose.vue` | **신규** (팝업 메일 작성 + 서명 선택) |
| 3 | `frontend/components/mail/MailList.vue` | 수정 (번호 컬럼) |
| 4 | `frontend/components/mail/MailCompose.vue` | 수정 (모달 비활성화) |
| 5 | `frontend/composables/useMail.ts` | 수정 (window.open + postMessage) |
| 6 | `frontend/composables/useAuth.ts` | 수정 (SSR 쿠키 전달) |
| 7 | `frontend/layouts/default.vue` | 수정 (전체 뷰포트 레이아웃) |
| 8 | `frontend/pages/profile.vue` | 수정 (2열 그리드) |
| 9 | `frontend/pages/files.vue` | 수정 (레이아웃 조정) |
| 10 | `frontend/pages/mail/index.vue` | 수정 (레이아웃 조정) |
| 11 | `frontend/pages/meetings.vue` | 수정 (레이아웃 조정) |
| 12 | `frontend/pages/git/index.vue` | 수정 (레이아웃 조정) |
| 13 | `frontend/pages/admin.vue` | 수정 (레이아웃 조정) |
| 14 | `frontend/components/dashboard/DashboardShortcuts.vue` | 수정 (navigateTo 제거) |
| 15 | `frontend/components/AppFooter.vue` | 수정 (비활성화) |
| 16 | `nginx/nginx.conf` | 수정 (캐시 제어 헤더) |
| 17 | `backend/app/db/session.py` | 수정 (DB 재시도 로직) |

---

## 20. Phase 15: 캘린더/연락처 + 데모 사이트 (완료, v0.7.0 → v0.7.1)

Stalwart v0.15의 JMAP for Calendars(RFC 8984) + Contacts(RFC 9553) 지원을 활용하여 포털 내 캘린더 및 연락처 기능을 구현하고, demo.namgun.or.kr에 형상 데모 사이트를 배포하였다.

### 20.1 캘린더 (JMAP for Calendars)

Stalwart JMAP API를 통해 캘린더 및 일정 CRUD를 구현하였다. JSCalendar(RFC 8984)의 `start` + `duration` 형식을 프론트엔드 친화적인 `start`/`end` 형식으로 양방향 변환한다.

| 기능 | 설명 |
|------|------|
| 캘린더 CRUD | 생성/수정/삭제, 색상 지정, 가시성 토글 |
| 일정 CRUD | 생성/수정/삭제, 종일 이벤트 지원 |
| 뷰 모드 | 월간 그리드 / 주간 시간표 / 일간 시간표 전환 |
| 캘린더 공유 | JMAP `shareWith` 속성 활용, 사용자별 읽기/쓰기 권한 제어 |
| CalDAV 동기화 | 외부 클라이언트(Thunderbird, iOS, Android)용 CalDAV URL 안내 |

**API 엔드포인트 (13개):**
```
GET/POST           /api/calendar/calendars
PATCH/DELETE        /api/calendar/calendars/{id}
GET/POST/DELETE     /api/calendar/calendars/{id}/shares
GET                 /api/calendar/events?start=&end=
GET/POST            /api/calendar/events[/{id}]
PATCH/DELETE        /api/calendar/events/{id}
GET                 /api/calendar/sync-info
```

### 20.2 연락처 (JMAP for Contacts)

JSContact(RFC 9553) 형식의 연락처 데이터를 프론트엔드 친화적인 플랫 구조로 변환하여 제공한다.

| 기능 | 설명 |
|------|------|
| 주소록 CRUD | 생성/삭제, 주소록별 필터링 |
| 연락처 CRUD | 생성/수정/삭제, 검색, 페이지네이션 |
| 다중 필드 | 이메일/전화/주소 복수 입력 (타입별 분류) |
| CardDAV 동기화 | 외부 클라이언트용 CardDAV URL 안내 |

**API 엔드포인트 (10개):**
```
GET/POST/DELETE     /api/contacts/address-books[/{id}]
GET/POST            /api/contacts/[{id}]
PATCH/DELETE        /api/contacts/{id}
GET                 /api/contacts/sync-info
```

### 20.3 CalDAV/CardDAV 리버스 프록시

외부 Nginx(192.168.0.150)에서 `mail.namgun.or.kr`의 well-known URL을 Stalwart로 리다이렉트하여, Thunderbird 등 데스크톱 클라이언트에서 자동 검색이 가능하도록 구성하였다.

```nginx
location = /.well-known/caldav  { return 301 /dav/; }
location = /.well-known/carddav { return 301 /dav/; }
```

### 20.4 데모 사이트 (demo.namgun.or.kr)

같은 Nuxt 3 프론트엔드에 `NUXT_PUBLIC_DEMO_MODE=true` 환경변수를 적용하여, 백엔드 없이 mock 데이터로 UI를 체험할 수 있는 데모 사이트를 구성하였다.

| 항목 | 설명 |
|------|------|
| 아키텍처 | Nitro 서버 미들웨어에서 `/api/*` 인터셉트 → mock 데이터 반환 |
| GET 요청 | 사전 정의된 mock 데이터 반환 (메일, 캘린더, 연락처, 파일, 회의 등) |
| 쓰기 요청 | 403 + "데모 모드에서는 변경할 수 없습니다" 토스트 표시 |
| 인증 | 자동 로그인 (인증 미들웨어 바이패스) |
| 배포 | `docker-compose.demo.yml` (프론트엔드만, 포트 3001) |
| TLS | Let's Encrypt 정식 인증서 (certbot webroot) |
| DNS | Pi-Hole 내부 DNS + 공인 DNS 등록 |
| 크롤링 | `robots.txt Allow: /` (AI 크롤링 허용) |

### 20.5 프론트엔드 변경

| 항목 | 설명 |
|------|------|
| 로그인 페이지 | "데모 체험하기" 버튼 추가 (demo.namgun.or.kr 링크) |
| 네비게이션 | 헤더에 캘린더/연락처 메뉴 링크 추가 |
| 대시보드 | 바로가기 위젯에 캘린더/연락처 추가 |
| 프로필 | CalDAV/CardDAV 동기화 URL 표시 + 복사 버튼 |

### 20.6 수정 파일 목록

| # | 파일 | 구분 |
|---|------|------|
| 1 | `backend/app/mail/jmap.py` | 수정 (USING_CALENDAR/CONTACTS 상수, using 파라미터) |
| 2 | `backend/app/main.py` | 수정 (calendar/contacts 라우터 등록, v0.7.0) |
| 3 | `backend/app/calendar/__init__.py` | **신규** |
| 4 | `backend/app/calendar/schemas.py` | **신규** (캘린더/일정/공유 스키마) |
| 5 | `backend/app/calendar/jmap_calendar.py` | **신규** (JMAP 캘린더 API 래핑, 공유 포함) |
| 6 | `backend/app/calendar/router.py` | **신규** (13개 엔드포인트) |
| 7 | `backend/app/contacts/__init__.py` | **신규** |
| 8 | `backend/app/contacts/schemas.py` | **신규** (주소록/연락처 스키마) |
| 9 | `backend/app/contacts/jmap_contacts.py` | **신규** (JMAP 연락처 API 래핑) |
| 10 | `backend/app/contacts/router.py` | **신규** (10개 엔드포인트) |
| 11 | `frontend/composables/useCalendar.ts` | **신규** (캘린더 상태 관리 + 공유) |
| 12 | `frontend/pages/calendar.vue` | **신규** (캘린더 메인 페이지) |
| 13 | `frontend/components/calendar/CalendarMiniMonth.vue` | **신규** |
| 14 | `frontend/components/calendar/CalendarSidebar.vue` | **신규** |
| 15 | `frontend/components/calendar/CalendarMonthView.vue` | **신규** |
| 16 | `frontend/components/calendar/CalendarWeekView.vue` | **신규** |
| 17 | `frontend/components/calendar/CalendarDayView.vue` | **신규** |
| 18 | `frontend/components/calendar/CalendarEventChip.vue` | **신규** |
| 19 | `frontend/components/calendar/CalendarEventModal.vue` | **신규** |
| 20 | `frontend/components/calendar/CalendarShareModal.vue` | **신규** (캘린더 공유 모달) |
| 21 | `frontend/composables/useContacts.ts` | **신규** (연락처 상태 관리) |
| 22 | `frontend/pages/contacts.vue` | **신규** (연락처 메인 페이지) |
| 23 | `frontend/components/contacts/ContactsSidebar.vue` | **신규** |
| 24 | `frontend/components/contacts/ContactsList.vue` | **신규** |
| 25 | `frontend/components/contacts/ContactsDetail.vue` | **신규** |
| 26 | `frontend/components/contacts/ContactsEditModal.vue` | **신규** |
| 27 | `frontend/demo/mockData.ts` | **신규** (전체 mock 데이터) |
| 28 | `frontend/server/middleware/demo.ts` | **신규** (Nitro API 인터셉트) |
| 29 | `frontend/plugins/demo-toast.client.ts` | **신규** (데모 403 토스트) |
| 30 | `docker-compose.demo.yml` | **신규** (데모 전용 Compose) |
| 31 | `frontend/nuxt.config.ts` | 수정 (demoMode 설정) |
| 32 | `frontend/middleware/auth.global.ts` | 수정 (데모 바이패스) |
| 33 | `frontend/components/layout/AppHeader.vue` | 수정 (네비 링크 추가) |
| 34 | `frontend/components/dashboard/DashboardShortcuts.vue` | 수정 (바로가기 추가) |
| 35 | `frontend/pages/profile.vue` | 수정 (동기화 설정 섹션) |
| 36 | `frontend/pages/login.vue` | 수정 (데모 버튼) |

### 20.7 v0.7.1 버그 수정 및 안정화

데모 사이트 품질 이슈, SSR 하이드레이션 오류, JMAP 호환성 문제를 수정하였다.

**데모 사이트 버그 수정:**

| # | 문제 | 수정 내용 |
|---|------|----------|
| 1 | 메일 상세 보기에서 모든 메시지가 동일한 본문 반환 | `getMessageDetail(id)` 함수로 메시지별 고유 HTML 본문 생성 |
| 2 | 메일함 필터링 미동작 (받은편지함/보낸편지함/임시보관/휴지통 구분 없음) | `mailbox_id` 쿼리 파라미터로 메시지 필터링, 보낸 메일 3건 + 임시보관 1건 + 휴지통 2건 추가 |
| 3 | 파일 mock 데이터가 `FileItem` 인터페이스와 불일치 | `file()`/`dir()` 헬퍼 함수로 전면 재작성, 인터페이스 완전 일치 |
| 4 | 파일 탭 구분 미동작 (내 파일/공유 파일/전체 사용자) | `my`, `shared`, `users` 루트 경로별 하위 디렉토리 mock 데이터 추가 |
| 5 | 파일 다운로드 시 `undefined` 페이지 열림 | 클라이언트: 데모 모드 체크 후 `alert()`, 서버: `__DEMO_BLOCK__` → 403 |
| 6 | 캘린더 이름 클릭 시 단독 필터 기능 없음 | `soloCalendar(id)` 함수 추가 — 클릭 시 해당 캘린더만 표시 |

**SSR 하이드레이션 오류 근본 해결:**

| # | 문제 | 원인 | 수정 내용 |
|---|------|------|----------|
| 7 | 다크 모드 토글 SVG 아이콘 불일치 | SSR은 `colorMode` light 폴백, 클라이언트는 OS 설정 감지 | `<ClientOnly>` 래퍼 + fallback placeholder |
| 8 | 대시보드 인사말 시간대 불일치 | Docker(UTC) vs 브라우저(KST)의 `new Date()` 차이 | `onMounted`에서 초기화, SSR은 "안녕하세요" 렌더링 |
| 9 | 캘린더 전체 날짜 불일치 | 모듈 레벨 `new Date()`가 서버/클라이언트 시간대 차이 | 캘린더 페이지 전체를 `<ClientOnly>` 래퍼 |

**JMAP 호환성 수정:**

| # | 문제 | 원인 | 수정 내용 |
|---|------|------|----------|
| 10 | 연락처 목록 500 에러 | Stalwart가 `name/full` 정렬 미지원 (`unsupportedSort`) | `sort` 파라미터 제거 |
| 11 | 연락처/캘린더 필터 없을 때 400 에러 | Stalwart가 `"filter": null` JSON 파싱 거부 | 빈 필터 시 `filter` 키 자체 생략 |

**Nginx 캐시 헤더 강화:**

| # | 변경 | 설명 |
|---|------|------|
| 12 | 내부 Nginx `add_header ... always` | 모든 응답 코드에 캐시 헤더 적용 + `Pragma` 추가 |
| 13 | 외부 Nginx `map $uri` 기반 캐시 제어 | `/_nuxt/` → immutable, 나머지 → no-cache, `proxy_hide_header`로 업스트림 헤더 통합 관리 |

**수정 파일:**

| # | 파일 | 변경 |
|---|------|------|
| 1 | `frontend/demo/mockData.ts` | 메시지별 HTML, 메일함 필터, 파일 인터페이스 재작성, 다운로드 차단 |
| 2 | `frontend/server/middleware/demo.ts` | 쿼리 파라미터 전달, `__DEMO_BLOCK__` 처리 |
| 3 | `frontend/composables/useCalendar.ts` | `soloCalendar()` 함수 추가 |
| 4 | `frontend/components/calendar/CalendarSidebar.vue` | 캘린더 이름 클릭 핸들러 추가 |
| 5 | `frontend/composables/useFiles.ts` | 데모 모드 다운로드 차단 |
| 6 | `frontend/components/layout/AppHeader.vue` | colorMode `v-if` → `<ClientOnly>` 래퍼 |
| 7 | `frontend/components/dashboard/DashboardGreeting.vue` | `new Date()` → `onMounted` 초기화 |
| 8 | `frontend/pages/calendar.vue` | 뷰 영역 + 사이드바 `<ClientOnly>` 래퍼 |
| 9 | `backend/app/contacts/jmap_contacts.py` | `sort` 제거, `filter: null` → 키 생략 |
| 10 | `backend/app/calendar/jmap_calendar.py` | `filter: null` → 키 생략 |
| 11 | `nginx/nginx.conf` | `add_header ... always` + `Pragma` |
| 12 | `192.168.0.150:namgun.or.kr.conf` | `map $uri` 캐시 제어 + `proxy_hide_header` |
| 13 | `backend/app/main.py` | 버전 v0.7.0 → v0.7.1 |

---

## 20.5. Phase 16: 보안 취약점 감사 및 수정 (완료, 2026-02-23)

전체 포털 코드에 대한 보안 감사를 실시하고, 발견된 취약점을 수정하였다. 메일 모듈(JMAP 클라이언트, 메일 라우터, 메일 뷰어, 메일 작성)과 전체 백엔드/프론트엔드 코드를 대상으로 하였다.

### 20.5.1 메일 모듈 보안 수정 (Critical 4건 + Medium 6건)

| 심각도 | 취약점 | 수정 내용 | 수정 파일 |
|--------|--------|----------|----------|
| **CRITICAL** | HTTP Header Injection (Content-Disposition) | RFC 5987 인코딩 적용, 따옴표/개행 제거 | `backend/app/mail/router.py` |
| **CRITICAL** | postMessage origin 미검증 (MailView iframe) | `e.origin` 검증 추가 (`'null'` 또는 자체 origin만 허용) | `frontend/components/mail/MailView.vue` |
| **CRITICAL** | postMessage origin 미검증 (Compose 팝업) | `window.location.origin` 지정, 수신 측 origin 검증 | `frontend/pages/mail/compose.vue`, `frontend/composables/useMail.ts` |
| **CRITICAL** | 이메일 주소 파싱 부실 (regex 탈출) | `<>` 파싱 개선 + 이메일 형식 정규식 검증 | `frontend/pages/mail/compose.vue` |
| MEDIUM | DOMPurify 로딩 전 미정제 HTML 노출 | 로딩 전 빈 문자열 반환 (`purifyReady` ref) | `frontend/components/mail/MailView.vue` |
| MEDIUM | DOMPurify 과다 허용 태그 | `style/meta/head/link/object/embed/form` FORBID 처리 | `frontend/components/mail/MailView.vue` |
| MEDIUM | 서명 HTML XSS | DOMPurify sanitize 적용 후 삽입 | `frontend/pages/mail/compose.vue` |
| MEDIUM | Blob 다운로드 에러 뭉개기 | 에러 유형별 분류 (Timeout→504, 404→404, 기타→502) | `backend/app/mail/router.py` |
| MEDIUM | JMAP 계정 해석 fallback 검증 부족 | `@` 포맷 체크 후 username fallback | `backend/app/mail/jmap.py` |
| LOW | 서명 HTML 길이 무제한 | `max_length=50000` 제한 | `backend/app/mail/schemas.py` |
| LOW | 첨부 용량 누적 버그 | `let totalSize` + 루프 내 누적 처리 | `frontend/pages/mail/compose.vue` |

### 20.5.2 전체 포털 보안 수정 (Critical 3건 + High 5건)

| 심각도 | 취약점 | 수정 내용 | 수정 파일 |
|--------|--------|----------|----------|
| **CRITICAL** | SVG 파일 XSS (JavaScript 삽입 가능) | SVG 응답에 CSP `default-src 'none'` 헤더 추가 | `backend/app/files/router.py` |
| **CRITICAL** | Terraform 사용자 코드 실행 (provisioner/local-exec) | `_BLOCKED_PATTERNS` 정규식으로 위험 구문 차단 + env_id UUID 검증 | `backend/app/lab/terraform_manager.py` |
| **CRITICAL** | .env 시크릿 평문 노출 | `.gitignore`에 이미 포함, git 추적 안 됨 확인 | `.gitignore` |
| **HIGH** | Docker 소켓 임의 컨테이너 접근 | 컨테이너 이름 패턴 검증 (`lab-[a-f0-9]{8}`만 허용) | `backend/app/lab/docker_manager.py` |
| **HIGH** | 파일 업로드 파일명 검증 미흡 | `os.path.basename` + `.`시작/`..`/널바이트/255자 초과 차단 | `backend/app/files/router.py` |
| **HIGH** | 공유 링크 경로 탈출 (Path Traversal) | `storage_root` 범위 밖 파일 접근 차단 (resolve + prefix 검증) | `backend/app/files/router.py` |
| **HIGH** | Rate Limiting 미적용 | slowapi 도입, 로그인 10/min, 회원가입 5/min, 비밀번호찾기 3/min, 전체 60/min | `backend/app/rate_limit.py`, `backend/app/main.py`, `backend/app/auth/router.py` |
| **HIGH** | Shiki v-html XSS | DOMPurify sanitize 추가 | `frontend/components/git/GitFileViewer.vue` |

### 20.5.3 추가된 의존성

| 패키지 | 용도 |
|--------|------|
| `slowapi==0.1.9` | IP 기반 API Rate Limiting |

### 20.5.4 수정 파일 목록 (15개)

| # | 파일 | 작업 |
|---|------|------|
| 1 | `backend/app/mail/router.py` | Header Injection 수정 + Blob 에러 분류 |
| 2 | `backend/app/mail/jmap.py` | 계정 해석 fallback 검증 |
| 3 | `backend/app/mail/schemas.py` | 서명 길이 제한 |
| 4 | `backend/app/files/router.py` | SVG CSP + 파일명 검증 + 공유 링크 경로 검증 |
| 5 | `backend/app/lab/terraform_manager.py` | Terraform 보안 검증 + 경로 탈출 방지 |
| 6 | `backend/app/lab/docker_manager.py` | 컨테이너 이름 검증 |
| 7 | `backend/app/lab/router.py` | TerraformSecurityError 핸들링 |
| 8 | `backend/app/main.py` | Rate Limiting 미들웨어 등록 |
| 9 | `backend/app/auth/router.py` | 로그인/회원가입/비밀번호찾기 Rate Limit |
| 10 | `backend/app/rate_limit.py` | **신규** — slowapi Limiter 인스턴스 |
| 11 | `backend/requirements.txt` | slowapi 추가 |
| 12 | `frontend/components/mail/MailView.vue` | DOMPurify 레이스 컨디션 + 태그 제한 + postMessage origin 검증 |
| 13 | `frontend/pages/mail/compose.vue` | 이메일 파싱 + 서명 XSS + postMessage origin + 첨부 용량 |
| 14 | `frontend/composables/useMail.ts` | postMessage origin 검증 |
| 15 | `frontend/components/git/GitFileViewer.vue` | Shiki 출력 DOMPurify sanitize |

---

## 20.7. Phase 17: 메일 시스템 버그 수정 및 안정화 (완료, 2026-02-23)

### 20.7.1 JMAP 계정 ID 매핑 버그 수정 (Critical)

Stalwart Mail Server의 JMAP accountId 인코딩 방식을 잘못 구현하여, **일부 사용자의 메일 기능이 완전히 불능**이었던 버그를 수정하였다.

**원인 분석:**

Stalwart는 JMAP accountId로 **bijective base-26 인코딩**(`a=0, b=1, ..., z=25, aa=26, ...`)을 사용한다. 기존 코드는 `hex(principal_id + offset)` 방식으로 계산하고 있었다.

| 사용자 | PID | 기존 코드 `hex(pid+10)` | 실제 (base-26) | 일치? |
|--------|-----|----------------------|---------------|-------|
| namgun18 | 2 | `c` | `c` | O (우연) |
| tsha | 3 | `d` | `d` | O (우연) |
| nahee14 | 5 | `f` | `f` | O (우연) |
| **kkb** | **6** | **`10`** | **`g`** | **X** |
| **noreply** | **9** | **`13`** | **`j`** | **X** |
| **ysj7705** | **14** | **`18`** | **`o`** | **X** |

PID 2~5에서만 우연히 일치한 이유: hex 숫자 `a-f`와 base-26 문자 `a-f`가 동일하고, offset 10을 더하면 PID 2→hex(12)=`c`, PID 5→hex(15)=`f`로 같은 문자가 출력됨. PID 6부터는 hex(16)=`10`(두 글자)이 되어 완전히 어긋남.

**수정 내용:**

| 항목 | 이전 | 이후 |
|------|------|------|
| 인코딩 | `format(principal_id + offset, "x")` (hex) | `_encode_account_id()` (bijective base-26) |
| offset 탐색 | `_discover_jmap_offset()` 함수 (스캔 방식) | **삭제** (불필요) |
| 캐시 | `_jmap_offset` 전역 변수 | **삭제** |

**수정 파일:** `backend/app/mail/jmap.py`

### 20.7.2 관리자 가입 알림 메일 추가

새 사용자가 회원가입 신청 시, 관리자 이메일(namgun18@namgun.or.kr)로 알림 메일이 발송되도록 구현하였다.

| 항목 | 내용 |
|------|------|
| 트리거 | `POST /api/auth/register` 성공 시 |
| 수신자 | `ADMIN_EMAILS` 환경변수 (쉼표 구분, 복수 가능) |
| 내용 | 사용자명, 표시이름, 포털 메일, 복구 이메일, 관리 페이지 링크 |
| 실패 처리 | 알림 실패해도 회원가입 자체는 정상 진행 |

**수정 파일:**
- `backend/app/config.py` — `admin_emails` 설정 추가
- `backend/app/auth/router.py` — `_send_admin_registration_notify()` 함수 추가
- `.env` — `ADMIN_EMAILS=namgun18@namgun.or.kr` 추가

### 20.7.3 Lab UI 수정 (2건)

| 문제 | 원인 | 수정 |
|------|------|------|
| 템플릿 드롭다운 안 보임 | 카드 컨테이너의 `overflow-hidden`이 absolute 드롭다운을 클리핑 | 카드에서 `overflow-hidden` 제거, editor+output 영역에만 적용 |
| 토폴로지 노드 이름 짤림/겹침 | `text-wrap: 'ellipsis'`, `text-max-width: 80`, `nodeSep: 60` 부족 | `text-wrap: 'wrap'`, `text-max-width: 140`, `nodeSep: 100`, `rankSep: 100` |

**수정 파일:**
- `frontend/components/lab/LabTerraform.vue`
- `frontend/components/lab/LabTopology.vue`

### 20.7.4 메일 오류 처리 개선

| 항목 | 수정 내용 |
|------|----------|
| JMAP 연결 재시도 | `jmap_call()`에 ConnectError/ReadError/WriteError 시 1회 재시도 + 자동 재연결 |
| 계정 해석 재시도 | `resolve_account_id()`에 HTTP 오류 시 1회 재시도 |
| 오류 메시지 개선 | 502: "메일 서버에 연결할 수 없습니다", 404: "메일 계정을 찾을 수 없습니다 ({email})" |

**수정 파일:** `backend/app/mail/jmap.py`, `backend/app/mail/router.py`

### 20.7.5 사용자 승인 시 메일함 자동 생성

Stalwart LDAP 디렉토리는 읽기 전용이어서 Admin API로 principal을 생성할 수 없다. 관리자가 사용자를 승인하면 Welcome 메일을 발송하여 Stalwart가 메일함을 자동 생성하도록 하였다.

**플로우:**
1. 관리자가 `/api/admin/users/{id}/approve` 호출
2. Authentik에서 사용자 활성화
3. Welcome 메일 발송 (SMTP) → Stalwart가 수신 시 principal 자동 생성
4. JMAP 계정 생성 대기 (최대 5회, 2초 간격)
5. 메일함 준비 완료 메시지 반환

**수정 파일:** `backend/app/admin/router.py`

### 20.7.6 SMTP 대안 조사 (참고)

Stalwart 안정성 우려로 대안 메일 서버를 조사하였다.

| 순위 | 옵션 | LDAP | JMAP | 안정성 | 판정 |
|------|------|------|------|--------|------|
| 1 | **Stalwart 유지 (인프라 안정화)** | O | O | 중 | **현재 선택** — 불안정 원인은 LDAP outpost/컨테이너 런타임이지 Stalwart 자체 아님 |
| 2 | docker-mailserver (Postfix+Dovecot) | O | X | 상 | 최선의 대안 — JMAP 없어 포털 IMAP 전환 필요 |
| 3 | Apache James | O | O | 중 | JVM 기반, 커뮤니티 작음 |
| — | mailcow | △ (nightly) | X | 상 | LDAP 미안정, 리소스 과다 (6-8GB) |
| — | Mailu | X | X | 중 | LDAP 미지원 (탈락) |
| — | iRedMail | △ (자체 LDAP) | X | 상 | Authentik 연동 어려움 |
| — | Maddy | O | X | 중 | API 전무, 포털 연동 난이도 높음 |
| — | Exchange Server | O (AD 필수) | X | 상 | 별도 라이선스 필요 (~$1,900), AD 인프라 필요, 10명 규모 과잉 |

**결론:** 네이티브 전환 완료 + base-26 버그 수정으로 핵심 문제 해결. 당분간 Stalwart 유지하며 안정성 모니터링.

### 20.7.7 메일 코드 전수 감사 및 수정

메일 관련 전체 코드를 1줄 단위로 감사하여 Critical 4건, High 5건, Medium 13건의 이슈를 발견·수정하였다.

**Critical (즉시 수정 — 서비스 장애 유발):**

| # | 파일 | 문제 | 수정 |
|---|------|------|------|
| 1 | `auth/router.py` `_send_verify_email()` | `smtplib.SMTP`(블로킹 I/O)를 `async def`에서 직접 호출 → FastAPI 이벤트 루프 전체 차단 | `asyncio.to_thread(_smtp_send, msg)` 래핑 |
| 2 | `auth/router.py` `_send_recovery_email()` | 동일 — 블로킹 SMTP | `asyncio.to_thread()` 래핑 |
| 3 | `auth/router.py` `_send_admin_registration_notify()` | 동일 — 블로킹 SMTP | `asyncio.to_thread()` 래핑 |
| 4 | `admin/router.py` `_send_welcome_email()` | 동일 — 블로킹 SMTP | `asyncio.to_thread()` 래핑 |

**High (운영 영향):**

| # | 파일 | 문제 | 수정 |
|---|------|------|------|
| 5 | `mail/jmap.py` `resolve_account_id()` | `data` 변수 미초기화 시 `UnboundLocalError` | `data = {}` 초기화 |
| 6 | `mail/jmap.py` `resolve_account_id()` | principal 조회 `limit: 100` → 100명 초과 시 누락 | `limit: 0` (무제한) |
| 7 | `mail/router.py` `upload_attachment()` | `file.read()` 무제한 → 메모리 고갈 DoS | `file.read(max_size + 1)` + 크기 검증 |
| 8 | `mail/jmap.py` `send_message()` | `mailboxIds` 미지정 시 Stalwart 거부 ("at least one mailbox") | Sent → Drafts → 첫 메일함 순 폴백 |
| 9 | `composables/useMail.ts` | `window.addEventListener('message')` 중복 등록 (컴포저블 재호출마다) | 모듈 레벨 `_listenerRegistered` 플래그 |

**수정 파일:**
- `backend/app/auth/router.py` — `_smtp_send()` 공통 헬퍼 추출 + `asyncio.to_thread()` 래핑
- `backend/app/admin/router.py` — `_send_welcome_email()` 동일 래핑
- `backend/app/mail/jmap.py` — `data` 초기화, `limit: 0`, `mailboxIds` 폴백
- `backend/app/mail/router.py` — 업로드 크기 제한
- `frontend/composables/useMail.ts` — 리스너 중복 등록 방지

### 20.7.8 JMAP EmailSubmission identityId 누락 수정 (Critical — 발송 불능 근본 원인)

포털에서 메일 발송 시 JMAP `EmailSubmission/set` 호출에 **`identityId` 필드가 누락**되어, Stalwart가 `"emailId and identityId properties are required."` 에러를 반환하고 있었다. 그러나 기존 코드는 `Email/set` (초안 생성) 성공만 확인하고 `EmailSubmission/set` 응답을 전혀 체크하지 않아 **200 OK를 반환하면서 실제로는 한 통도 발송되지 않는** 상태였다.

**원인 분석:**

```
JMAP 호출 구조:
  1) Email/set → 이메일 초안 생성 → ✅ 성공 (Sent 폴더에 저장)
  2) EmailSubmission/set → 실제 발송 → ❌ 실패 (identityId 누락)
     → notCreated: {"sendIt": {"type": "invalidProperties", ...}}

코드 결과 확인:
  for resp in result["methodResponses"]:
      if resp[0] == "Email/set":     ← Email/set만 체크
          return resp[1]["created"]   ← 200 OK 반환 (실제 미발송)
  # EmailSubmission/set 응답은 완전히 무시됨
```

**수정 내용:**

| 항목 | 이전 | 이후 |
|------|------|------|
| Identity 조회 | 없음 | `get_identity_id()` 함수 추가 (`Identity/get` JMAP 호출) |
| EmailSubmission | `identityId` 없음 | `identityId: identity_id` 포함 |
| 에러 체크 | `Email/set` created만 확인 | `EmailSubmission/set` created/notCreated 모두 확인 |
| 로깅 | 없음 | `Email/set`, `EmailSubmission/set` 실패 시 에러 로그 |

**수정 파일:** `backend/app/mail/jmap.py`

### 20.7.9 워치독 연쇄 재시작 문제 해결 (Stalwart 안정성)

Stalwart가 5분(워치독 v2 적용 전 2분)마다 반복적으로 재시작되어 메일 수발신이 불가능했던 문제를 해결하였다.

**원인 분석 (2중 문제):**

1. **워치독 false-positive**: LDAP outpost가 정상 작동 중이었으나 워치독의 포트 체크 타이밍 문제로 매번 "down"으로 판정하여 재시작 트리거
2. **systemd 의존성 연쇄**: `stalwart-mail.service`에 `Requires=authentik-ldap-outpost.service` 설정이 있어, 워치독이 LDAP outpost만 재시작해도 systemd가 **Stalwart까지 연쇄 재시작**

```
워치독 실행 → LDAP "down" 판정 → systemctl restart authentik-ldap-outpost
                                      ↓ (Requires= 의존성)
                              systemd가 stalwart-mail도 자동 재시작
                                      ↓
                              메일 서비스 중단 (수발신 불가)
```

하루 550회 이상 재시작이 발생하여 사실상 메일 서비스가 정상 운영된 적이 없었다.

**수정 내용:**

| 항목 | 이전 | 이후 |
|------|------|------|
| systemd 의존성 | `Requires=authentik-ldap-outpost.service` | `Wants=authentik-ldap-outpost.service` (연쇄 재시작 방지) |
| 워치독 Stalwart 재시작 | 매번 LDAP + Stalwart 동시 재시작 | LDAP outpost만 재시작 (Stalwart 미접촉) |
| 워치독 실행 간격 | `*/2` (2분) | `*/5` (5분) |
| 동시 실행 방지 | 없음 | lockfile (`/tmp/ldap-watchdog.lock`) |
| 재시작 쿨다운 | 없음 | 3분 이내 재시작 스킵 (`ActiveEnterTimestamp` 확인) |
| 재시작 후 검증 | 30초 (6×5s) | 60초 (12×5s) |

**수정 파일:**
- `/etc/systemd/system/stalwart-mail.service` (192.168.0.250) — `Requires` → `Wants`
- `/home/namgun/stalwart/ldap-watchdog.sh` (192.168.0.250) — 워치독 v2

---

## 21. 핵심 트러블슈팅 정리

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
| 26 | SSR에서 페이지 새로고침 시 홈으로 리다이렉트 | Nuxt 3 SSR `$fetch`가 브라우저 쿠키를 자동 전달하지 않음 → 서버에서 미인증 판정 | `useRequestHeaders(['cookie'])`로 쿠키 캡처 후 `$fetch` 헤더에 전달 |
| 27 | 배포 후 SPA 네비게이션 완전 불능 | 브라우저가 이전 빌드의 JS 청크를 캐시 → 하이드레이션 실패 → NuxtLink가 `<a>` 태그로 퇴화 | Nginx `Cache-Control: no-cache` (HTML) + `immutable` (에셋 content-hash) 적용 + 브라우저 캐시 전체 삭제 |
| 28 | 데모 사이트 메일 상세가 모든 메시지에 동일 본문 반환 | `getMockResponse()`가 경로의 메시지 ID를 무시하고 정적 `demoMessageDetail` 반환 | `getMessageDetail(id)` 함수로 메시지별 고유 HTML 본문 동적 생성 |
| 29 | 데모 사이트 파일 다운로드 시 `undefined` 페이지 열림 | `window.open(url)`이 데모 미들웨어의 mock JSON을 표시 | 클라이언트에서 데모 모드 감지 후 `alert()` 차단 + 서버에서 `__DEMO_BLOCK__` → 403 반환 |
| 30 | 본서버 SSR 하이드레이션 오류 (`nextSibling is null`) | `useColorMode()` `v-if`가 SSR(light 폴백)/클라이언트(OS 감지) 간 SVG 아이콘 불일치; `new Date()`가 Docker(UTC)/브라우저(KST) 시간대 차이로 DOM 불일치 | colorMode → `<ClientOnly>`, DashboardGreeting → `onMounted` 초기화, 캘린더 → `<ClientOnly>` 래퍼 |
| 31 | 연락처 목록 500 에러 | Stalwart가 `ContactCard/query`의 `name/full` 정렬 미지원 + `"filter": null` JSON 파싱 거부 | `sort` 제거, 빈 필터 시 `filter` 키 생략 |
| 32 | PID 6+ 사용자 메일 기능 불능 (ysj7705, kkb, noreply 등) | JMAP accountId를 `hex(pid+offset)`으로 계산했으나, Stalwart는 bijective base-26 인코딩 사용. PID 2~5만 우연히 일치 | `_encode_account_id()` base-26 인코딩 함수 구현, offset 탐색 로직 전체 제거 |
| 33 | 신규 사용자 승인 후 메일함 없음 | Stalwart LDAP 디렉토리는 읽기 전용, Admin API로 principal 생성 불가 | 승인 시 Welcome 메일 발송하여 Stalwart가 수신 시 자동 principal 생성 유도 |
| 34 | Lab 템플릿 드롭다운 안 보임 | 부모 카드의 `overflow-hidden`이 absolute 위치 드롭다운 클리핑 | 카드에서 `overflow-hidden` 제거, editor+output 영역에만 적용 |
| 35 | 포털 메일 발송 200 OK이나 실제 미발송 | JMAP `EmailSubmission/set`에 `identityId` 필드 누락 → Stalwart `notCreated` 반환하나 코드가 `Email/set` 성공만 확인 | `get_identity_id()` 함수 추가, `identityId` 포함, `EmailSubmission/set` 응답 에러 체크 |
| 36 | Stalwart 2~5분마다 반복 재시작 (하루 550회+) | `stalwart-mail.service`의 `Requires=authentik-ldap-outpost.service` 의존성 + 워치독 LDAP 재시작 → systemd 연쇄 재시작 | `Requires=` → `Wants=` 변경, 워치독 v2 (lockfile, cooldown, Stalwart 미접촉) |
| 37 | `smtplib.SMTP`가 FastAPI 이벤트 루프 차단 | 블로킹 SMTP 호출을 `async def`에서 직접 실행 → 전체 서버 응답 지연 | `asyncio.to_thread()` 래핑으로 별도 스레드 실행 |

---

## 22. 잔여 작업 항목

### 22.1 즉시 조치 필요

- [x] DKIM `dkim=pass` 확인 (DNS 캐시 만료 후)
- [ ] PTR 레코드 등록 (SK 브로드밴드, `211.244.144.69 → mail.namgun.or.kr`) — 담주 요청 예정
- [ ] `mail.namgun.or.kr`에 대한 SPF TXT 레코드 추가 (SPF_HELO_NONE 해결)
- [ ] Authentik 계정 비밀번호 설정: tsha, nahee14, kkb
- [x] Nginx/Mail 서버 커널 재부팅 (5.14.0-611.30.1.el9_7, 2026-02-22 적용 완료)
- [x] 메일서버 SELinux Enforcing 전환 (2026-02-22 적용, AVC 거부 0건 확인 후 전환)
- [x] Stalwart + LDAP Outpost 네이티브 마이그레이션 (Podman → systemd, 2026-02-22)
- [x] WSL Docker 포트 바인딩 자동 복구 서비스 (docker-fix-ports.service, 2026-02-22)

### 22.2 완료된 항목

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
| LocalStack Lab AWS 학습 환경 | Phase 13 |
| Terraform IaC 통합 (Init/Plan/Apply/Destroy) | Phase 13 |
| 사용자별 격리 LocalStack 컨테이너 | Phase 13 |
| cytoscape.js 토폴로지 시각화 | Phase 13 |
| 사전 정의 Terraform 템플릿 5종 | Phase 13 |
| CI/CD 배포 엔드포인트 | Phase 13 |
| 멤버 초대/관리 (멀티테넌트) | Phase 13 |
| Lab 좌우 분할 레이아웃 + 드래그 리사이즈 | Phase 14 |
| 메일 작성 팝업 창 (window.open) | Phase 14 |
| 메일 작성 시 서명 선택 기능 | Phase 14 |
| 메일 리스트 번호 컬럼 | Phase 14 |
| 전체 뷰포트 레이아웃 (컨테이너 제약 제거) | Phase 14 |
| SSR 쿠키 전달 수정 (useRequestHeaders) | Phase 14 |
| Nginx 캐시 제어 헤더 | Phase 14 |
| JMAP 캘린더 (월/주/일 뷰, 일정 CRUD) | Phase 15 |
| JMAP 연락처 (주소록, 검색, CRUD) | Phase 15 |
| 캘린더 공유 (shareWith 권한 제어) | Phase 15 |
| CalDAV/CardDAV Nginx 프록시 + well-known | Phase 15 |
| 데모 사이트 (demo.namgun.or.kr) | Phase 15 |
| 데모 mock 데이터 (Nitro 미들웨어) | Phase 15 |
| 로그인 페이지 데모 버튼 | Phase 15 |
| 데모 메일 메시지별 상세 + 메일함 필터링 | Phase 15 (v0.7.1) |
| 데모 파일 탭 구분 (내 파일/공유/전체 사용자) + 다운로드 차단 | Phase 15 (v0.7.1) |
| 캘린더 이름 클릭 단독 필터 | Phase 15 (v0.7.1) |
| Nginx 캐시 헤더 `always` 강화 + 외부 `map $uri` 캐시 제어 | Phase 15 (v0.7.1) |
| SSR 하이드레이션 오류 근본 해결 (colorMode, Date 시간대) | Phase 15 (v0.7.1) |
| JMAP 연락처 `unsupportedSort` + `filter: null` 수정 | Phase 15 (v0.7.1) |
| 전체 코드 보안 감사 (Critical 4 + High 4 + Medium 9) | Phase 16 |
| JMAP 계정 ID 매핑 버그 수정 (base-26 인코딩) | Phase 17 |
| 관리자 가입 알림 메일 기능 | Phase 17 |
| Lab 템플릿 드롭다운 overflow 수정 | Phase 17 |
| Lab 토폴로지 노드 라벨 짤림/겹침 수정 | Phase 17 |
| 메일 오류 처리 개선 (재시도, 재연결, 오류 메시지) | Phase 17 |
| 사용자 승인 시 Welcome 메일 자동 발송 (메일함 생성) | Phase 17 |
| SMTP 대안 조사 (docker-mailserver, Apache James 등 7종 비교) | Phase 17 |
| 메일 코드 전수 감사 (Critical 4 + High 5 + Medium 13) | Phase 17 |
| JMAP EmailSubmission identityId 수정 (발송 불능 근본 원인) | Phase 17 |
| EmailSubmission 응답 에러 체크 + 로깅 추가 | Phase 17 |
| 블로킹 SMTP → asyncio.to_thread() 래핑 (4곳) | Phase 17 |
| 워치독 연쇄 재시작 수정 (Requires → Wants + 워치독 v2) | Phase 17 |
| Content-Disposition Header Injection 수정 | Phase 16 |
| postMessage origin 검증 (MailView, Compose, useMail) | Phase 16 |
| 이메일 주소 파싱 정규식 검증 강화 | Phase 16 |
| DOMPurify 레이스 컨디션 + 과다 허용 태그 수정 | Phase 16 |
| SVG 파일 서빙 CSP 헤더 추가 | Phase 16 |
| Terraform 코드 보안 검증 (provisioner 차단) | Phase 16 |
| Docker 컨테이너 이름 패턴 검증 | Phase 16 |
| 파일 업로드 파일명 검증 강화 | Phase 16 |
| 공유 링크 경로 탈출 방지 | Phase 16 |
| API Rate Limiting (slowapi) 도입 | Phase 16 |
| Shiki v-html DOMPurify sanitize 추가 | Phase 16 |
| 관리 대시보드 신규 (방문자 분석 + 서비스 모니터링) | Phase 18 |
| AccessLog 미들웨어 (비동기 배치 삽입) | Phase 18 |
| GeoIP 국가 조회 (MaxMind GeoLite2, LRU 캐시) | Phase 18 |
| User-Agent 파싱 (규칙 기반, LRU 캐시) | Phase 18 |
| Chart.js 차트 (Line/Bar/Doughnut, vue-chartjs) | Phase 18 |
| 분석 API 10개 (overview, daily, countries, service, active, logins, logs, git) | Phase 18 |
| 국기 이모지 (ISO → Unicode Regional Indicator) | Phase 18 |
| 접속 로그 자동 정리 (90일, 일일 백그라운드 태스크) | Phase 18 |
| 데모 사이트 분석 mock 데이터 | Phase 18 |
| 관리 페이지 서브 탭 네비게이션 (대시보드/사용자) | Phase 18 |

### 22.3 Phase 18: 관리 대시보드 — 방문자 분석 + 서비스 현황 모니터링 (완료, 2026-02-24)

관리자 전용 대시보드를 신규 구현하였다. 모든 API 요청을 자동 캡처하여 방문자 통계, 서비스 사용량, 국가별 분포, 실시간 활성 사용자 등을 시각화한다.

#### 22.3.1 백엔드 — AccessLog 미들웨어

| 구성 요소 | 내용 |
|-----------|------|
| `AccessLog` 모델 | UUID PK, IP(IPv6 대응), method, path, status_code, response_time_ms, UA 파싱 결과, GeoIP 국가, user_id(FK), service 분류 |
| 인덱스 | `created_at`, `user_id`, 복합(`created_at, service`), 복합(`created_at, country_code`) |
| `AccessLogMiddleware` | 모든 `/api/` 요청 캡처 (health/docs 제외), `X-Real-IP` 헤더에서 실제 IP 추출 |
| 비동기 배치 삽입 | `deque` 버퍼 → 5초마다 or 50건마다 일괄 INSERT (응답 지연 0) |
| GeoIP | `geoip2` + MaxMind GeoLite2-Country DB (~6MB), `@lru_cache(maxsize=4096)`, 사설 IP 무시 |
| UA 파서 | 외부 라이브러리 없이 규칙 기반 (Chrome/Firefox/Safari/Edge + OS + Device), `@lru_cache(maxsize=1024)` |
| 로그 정리 | 매일 03:00 KST 백그라운드 태스크, 90일 이상 로그 자동 삭제 |

**신규 파일:**
- `backend/app/middleware/__init__.py`
- `backend/app/middleware/access_log.py` — 미들웨어 + 배치 삽입 + 정리 태스크
- `backend/app/middleware/geoip.py` — GeoIP 조회
- `backend/app/middleware/ua_parser.py` — User-Agent 파싱

#### 22.3.2 백엔드 — Analytics API (10개 엔드포인트)

모든 엔드포인트는 `Depends(require_admin)` 보호.

| 엔드포인트 | 파라미터 | 반환 |
|-----------|---------|------|
| `GET /api/admin/analytics/overview` | `period=today\|7d\|30d` | 총 방문, 유니크 IP, 인증/비인증, 평균 응답시간 |
| `GET /api/admin/analytics/daily-visits` | `days=30` | 일별 방문 추이 (날짜, 전체, 인증, 비인증) |
| `GET /api/admin/analytics/top-pages` | `period`, `limit=10` | 상위 페이지 (경로, 건수) |
| `GET /api/admin/analytics/countries` | `period`, `limit=15` | 국가별 분포 (코드, 한국어 국가명, 건수) |
| `GET /api/admin/analytics/service-usage` | `period` | 서비스별 사용량 (mail, calendar, files 등) |
| `GET /api/admin/analytics/active-users` | — | 5분 내 활성 사용자 (이름, 경로, IP, 국가) |
| `GET /api/admin/analytics/recent-logins` | `limit=20` | 최근 로그인 (사용자, IP, 국가, 시간) |
| `GET /api/admin/analytics/access-logs` | `page`, `limit`, `service`, `user_id` | 페이지네이션 원시 로그 |
| `GET /api/admin/analytics/git-activity` | — | Gitea Push/Issue/PR 이벤트 (전 저장소) |
| `GET /api/admin/analytics/git-stats` | — | 총 저장소, 사용자, 이슈, PR 현황 |

**신규 파일:** `backend/app/admin/schemas.py`

#### 22.3.3 프론트엔드 — Chart.js 대시보드

패키지 추가: `chart.js`, `vue-chartjs`

| 컴포넌트 | 내용 |
|----------|------|
| `AdminAnalyticsOverview.vue` | 4개 stat 카드 (총 방문, 유니크, 인증, 응답시간) |
| `AdminAnalyticsDailyChart.vue` | Line chart — 일별 방문 추이 (전체/인증/비인증) |
| `AdminAnalyticsCountries.vue` | 수평 Bar chart — 국가별 분포 + 국기 이모지 |
| `AdminAnalyticsTopPages.vue` | 수평 Bar chart — 인기 페이지 |
| `AdminAnalyticsServiceUsage.vue` | Doughnut chart — 서비스별 사용량 (한국어 레이블) |
| `AdminAnalyticsActiveUsers.vue` | 실시간 테이블 — 5분 내 활성 사용자 |
| `AdminAnalyticsRecentLogins.vue` | 테이블 — 최근 로그인 (IP 마스킹) |
| `AdminAnalyticsAccessLogs.vue` | 페이지네이션 테이블 — 원시 로그 (서비스 필터) |
| `AdminAnalyticsGitActivity.vue` | Git 활동 타임라인 (push/issue/PR 이벤트) |

**국기 이모지:** ISO 코드 → Unicode Regional Indicator 변환 (`KR` → 🇰🇷)

#### 22.3.4 네비게이션 변경

- AppHeader 관리 링크: `/admin/users` → `/admin/dashboard`
- 관리 페이지 서브 탭: `[대시보드] [사용자 관리]` (양쪽 페이지에 동일하게 표시)
- 사용자 드롭다운: "사용자 관리" → "관리 대시보드"

#### 22.3.5 데모 사이트 동일 지원

`frontend/demo/mockData.ts`에 10개 분석 API에 대한 mock 데이터 추가:
- 30일치 랜덤 방문 데이터 (100~300/일)
- 6개 국가 분포 (KR 85%, US 5%, JP 3%, 기타)
- 8개 서비스 사용량
- 활성 사용자 3명, 최근 로그인 5건
- 접속 로그 50건 (랜덤 생성)
- Git 활동 6건, Git 통계

#### 22.3.6 수정 파일 요약

| 작업 | 파일 | 내용 |
|------|------|------|
| 신규 | `backend/app/middleware/__init__.py` | 패키지 |
| 신규 | `backend/app/middleware/access_log.py` | 요청 로깅 미들웨어 + 배치 삽입 |
| 신규 | `backend/app/middleware/geoip.py` | GeoIP 조회 (geoip2 + LRU 캐시) |
| 신규 | `backend/app/middleware/ua_parser.py` | UA 파싱 (규칙 기반 + LRU 캐시) |
| 신규 | `backend/app/admin/schemas.py` | Analytics 응답 스키마 (12개) |
| 신규 | `frontend/pages/admin/dashboard.vue` | 관리 대시보드 페이지 |
| 신규 | `frontend/composables/useAdminAnalytics.ts` | Analytics composable |
| 신규 | `frontend/components/admin/Admin*.vue` | 차트/테이블 컴포넌트 9개 |
| 수정 | `backend/app/db/models.py` | AccessLog 모델 + 4개 인덱스 |
| 수정 | `backend/app/main.py` | 미들웨어 등록 + 백그라운드 태스크 3개 |
| 수정 | `backend/app/config.py` | geoip_db_path 설정 |
| 수정 | `backend/app/admin/router.py` | 분석 엔드포인트 10개 추가 |
| 수정 | `backend/requirements.txt` | geoip2 추가 |
| 수정 | `backend/Dockerfile` | GeoIP DB 다운로드 |
| 수정 | `frontend/package.json` | chart.js, vue-chartjs 추가 |
| 수정 | `frontend/components/layout/AppHeader.vue` | 관리 네비게이션 변경 |
| 수정 | `frontend/pages/admin/users.vue` | 서브 탭 추가 |
| 수정 | `frontend/demo/mockData.ts` | 분석 mock 데이터 10개 |

### 22.5 인프라 변경: Stalwart + LDAP Outpost 네이티브 마이그레이션 (2026-02-22)

192.168.0.250 (Rocky Linux 9.7) 에서 운영 중이던 Stalwart Mail + Authentik LDAP Outpost를 Podman rootless 컨테이너에서 네이티브 systemd 서비스로 전환하였다.

**전환 사유**: `conmon` 프로세스 사망으로 인한 반복적 장애 (WSL 재시작마다 비정상 종료 + 포트 바인딩 실패)

| 구성 요소 | 이전 (Podman) | 이후 (네이티브) |
|-----------|---------------|----------------|
| Stalwart Mail v0.15.5 | Podman rootless 컨테이너 | `/usr/local/bin/stalwart-mail` + `stalwart-mail.service` |
| Authentik LDAP Outpost | Podman rootless 컨테이너 (2025.10) | `/usr/local/bin/authentik-ldap-outpost` (2025.10.4) + `authentik-ldap-outpost.service` |
| 데이터 경로 | `~/.local/share/containers/storage/volumes/stalwart-data/` | `/opt/stalwart-mail/` |
| 자동 시작 | Podman 의존 (불안정) | systemd enable (안정) |
| Watchdog | `podman restart` | `sudo systemctl restart` |

### 22.6 향후 계획

| 항목 | 내용 | 예상 기술 스택 |
|------|------|---------------|
| MFA 추가 | Authentik MFA 플로우 연동 + 포털 UI에서 challenge 처리 | Authentik Flow Executor + TOTP/WebAuthn |
| Game Panel 포털 통합 | 게임 서버 관리를 포털 내에서 직접 수행 (현재 상태 조회만 완료) | 포털 API + Game Panel API 연동 |
| Naver Works급 ERP | 조직 관리, 결재, 메신저 등 그룹웨어 기능 | 장기 목표 |

---

## 23. 기술 스택 요약

| 분류 | 기술 |
|------|------|
| **하드웨어** | |
| 메인 서버 | Dual Intel Xeon Gold 6138 (40C/80T), 128GB DDR4 ECC, ASUS 서버보드, 4U 산업용 케이스, Noctua 팬 전교체 |
| 네트워크 (NIC) | Intel X520-DA2 10G SFP+ (서버, 게임PC) |
| 네트워크 (스위치) | MikroTik CRS317-1G-16S+ (10G SFP+ x16 포트) |
| 방화벽 (어플라이언스) | Check Point Quantum Security Gateway 3100 |
| **네트워크/보안** | |
| WAN | SK브로드밴드 고정 공인IP x2, AS17613 |
| LAN | 10Gbps SFP+ 백본 (DAC/광모듈) |
| 경계 보안 | Check Point IPS, Anti-Bot, SandBlast Threat Prevention, URL Filtering |
| 호스트 보안 | SELinux Enforcing, firewalld, ISMS-P 보안 헤더 |
| TLS 인증서 | Let's Encrypt (certbot + Stalwart 내장 ACME) |
| DNS | Windows Server DNS, Pi-Hole (내부), 공인 DNS (namgun.or.kr) |
| **소프트웨어** | |
| Identity Provider | Authentik 2025.10.4 |
| 인증 프로토콜 | OIDC, LDAP, OAuth2 |
| 포털 프론트엔드 | Nuxt 3, Vue 3, shadcn-vue, Chart.js (vue-chartjs) |
| 포털 백엔드 | FastAPI, SQLAlchemy 2.0 (async), asyncpg, geoip2 |
| 리버스 프록시 | Nginx (Rocky Linux 10) |
| IaC / 학습 | Terraform 1.9.8, LocalStack 3.8, boto3, cytoscape.js |
| 컨테이너 (Docker) | Authentik, Portal (frontend + backend + nginx + PostgreSQL), Gitea, RustDesk Pro, Game Panel, LocalStack Lab |
| 네이티브 서비스 (systemd) | Stalwart Mail v0.15.5, Authentik LDAP Outpost 2025.10.4 (192.168.0.250) |
| 메일 서버 | Stalwart Mail Server (RocksDB, JMAP, CalDAV/CardDAV) |
| 화상회의 | BigBlueButton 3.0 |
| 파일 스토리지 | NFS v4.1 (OMV, 192.168.0.100) |
| Git 호스팅 | Gitea 1.25.4 |
| 호스트 OS | Windows Server (WSL2/Hyper-V), Rocky Linux 10, Rocky Linux 9.7 |
| 가상화 | Hyper-V (BBB, Nginx, Mail 서버) |

---

## 24. 보안 고려사항

### 24.1 적용된 보안 정책

**경계 보안 (Perimeter):**
- Check Point Quantum 3100 Security Gateway
  - IPS (침입 방지 시스템)
  - Anti-Bot (봇넷 C&C 탐지/차단)
  - SandBlast Threat Prevention (제로데이 위협 샌드박싱)
  - URL Filtering (악성 URL 차단)

**호스트 보안:**
- SELinux Enforcing (메일서버, 2026-02-22 적용)
- firewalld 방화벽 전 서버 활성화 (Phase 12)
- 정기 OS 보안 패치 적용 (커널 5.14.0-611.30.1.el9_7)

**애플리케이션 보안:**
- ISMS-P 기준 보안 헤더 전 사이트 적용
- TLS 1.2+ 강제 (HSTS preload)
- 서버 정보 노출 차단 (`server_tokens off`, `X-Powered-By` / `Server` 헤더 제거)
- 스캐너/봇 차단 규칙
- CSP(Content-Security-Policy) 전 사이트 적용 (Phase 12)
- API Rate Limiting — slowapi 기반 IP별 요청 제한 (Phase 16)
- SVG 파일 서빙 시 CSP `default-src 'none'` 적용 (Phase 16)
- Terraform 사용자 코드 보안 검증 (provisioner/local-exec 차단, Phase 16)
- Docker 컨테이너 이름 패턴 검증 (lab-prefix 강제, Phase 16)

**인증/암호화:**
- DKIM + SPF + DMARC 이메일 인증 체계
- PKCE S256 인증 코드 보호 (replay 공격 방지)
- 서명된 세션 쿠키 (itsdangerous, httponly, secure, samesite=lax)
- 파일 시스템 path traversal 방지 (resolve + prefix 검증)
- 리다이렉트 URL 도메인 화이트리스트 (`*.namgun.or.kr`)
- postMessage origin 검증 (iframe/popup 간 통신, Phase 16)
- DOMPurify HTML 정제 (메일 본문, 서명, 코드 하이라이팅, Phase 16)
- Content-Disposition RFC 5987 인코딩 (헤더 인젝션 방지, Phase 16)

**보안 아키텍처 (다층 방어):**
```
인터넷 → Check Point (IPS/Anti-Bot/SandBlast) → firewalld → SELinux → 앱 보안 헤더
```

### 24.2 계획된 보안 강화

- PTR 레코드 등록으로 역방향 DNS 검증 완성 (담주 SK 요청 예정)
- Authentik MFA(다중 인증) 정책 강화 (v1.1 예정)
- ~~메일서버 SELinux Enforcing 전환~~ → **완료** (2026-02-22, AVC 0건 확인 후 적용)

---

*문서 끝. 최종 갱신: 2026-02-24 (v2.4 — Phase 18: 관리 대시보드 — 방문자 분석 + 서비스 현황 모니터링)*
