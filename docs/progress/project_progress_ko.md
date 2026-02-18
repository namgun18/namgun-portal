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

---

## 1. 프로젝트 개요

namgun.or.kr 종합 포털은 가정 및 소규모 조직을 위한 셀프 호스팅 통합 플랫폼이다. Authentik을 중앙 Identity Provider(IdP)로 두고, Git 저장소, 원격 데스크톱, 메일, 화상회의, 파일 관리, 게임 서버 등 다양한 서비스를 SSO(Single Sign-On)로 통합하는 것을 목표로 한다.

### 1.1 핵심 목표

- 모든 서비스에 대한 SSO 인증 통합 (OIDC / LDAP)
- ISMS-P 보안 기준에 준하는 인프라 구성
- 셀프 호스팅 기반의 데이터 주권 확보
- 단계적 서비스 확장 (Phase 0 ~ Phase 5)

---

## 2. 단계별 진행 현황 요약

| 단계 | 명칭 | 상태 | 기간 | 비고 |
|------|------|------|------|------|
| Phase 0 | 인프라 준비 | **완료** | — | Authentik, DNS, Nginx, TLS |
| Phase 1 | SSO PoC | **완료** | — | Gitea OIDC, RustDesk OIDC |
| Phase 2 | 메일 서버 마이그레이션 | **완료** | — | Stalwart + LDAP + OIDC |
| Phase 3 | 포털 코어 개발 | 예정 | — | Nuxt 3 + FastAPI |
| Phase 4 | 네이티브 통합 | 예정 | — | JMAP, WebDAV, CalDAV, CardDAV |
| Phase 5 | 추가 서비스 통합 | 예정 | — | BBB Greenlight OIDC, OMV Proxy Auth |

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
  │       ├─ Gitea 1.25.4                                          │
  │       ├─ RustDesk Pro (hbbs + hbbr)                            │
  │       └─ Game Panel (backend + nginx + palworld)               │
  │                                                                │
  │  [192.168.0.150] Hyper-V VM — Nginx (Rocky Linux 10)          │
  │    └─ 중앙 리버스 프록시, TLS Termination                       │
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
| Authentik | auth.namgun.or.kr | 192.168.0.50 (Docker) | — (IdP) | 운영 중 |
| Gitea | git.namgun.or.kr | 192.168.0.50 (Docker) | OIDC | 운영 중 |
| RustDesk Pro | remote.namgun.or.kr | 192.168.0.50 (Docker) | OIDC | 운영 중 |
| Game Panel | game.namgun.or.kr | 192.168.0.50 (Docker) | Discord OAuth2 | 운영 중 |
| Stalwart Mail | mail.namgun.or.kr | 192.168.0.250 (Podman) | LDAP + OIDC | 운영 중 |
| LDAP Outpost | — | 192.168.0.250 (Podman sidecar) | — | 운영 중 |
| Nginx Proxy | *.namgun.or.kr | 192.168.0.150 (VM) | — | 운영 중 |
| Pi-Hole | — | 192.168.0.251 | — | 운영 중 |
| BBB | meet.namgun.or.kr | TBD | OIDC (계획) | 계획 |
| OMV/Files | file.namgun.or.kr | TBD | Proxy Auth (계획) | 계획 |
| Portal | namgun.or.kr | TBD | OIDC (계획) | 계획 |

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

## 7. 핵심 트러블슈팅 정리

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

---

## 8. 잔여 작업 항목

### 8.1 즉시 조치 필요

- [ ] DKIM `dkim=pass` 확인 (DNS 캐시 만료 후, ~1시간)
- [ ] PTR 레코드 등록 (SK 브로드밴드, `211.244.144.69 → mail.namgun.or.kr`)
- [ ] `mail.namgun.or.kr`에 대한 SPF TXT 레코드 추가 (SPF_HELO_NONE 해결)
- [ ] Authentik 계정 비밀번호 설정: tsha, nahee14, kkb

### 8.2 향후 단계

| 단계 | 내용 | 예상 기술 스택 |
|------|------|---------------|
| Phase 3 | 포털 코어 개발 | Nuxt 3 (프론트엔드) + FastAPI (백엔드) |
| Phase 4 | 네이티브 통합 | JMAP (메일), WebDAV (파일), CalDAV (캘린더), CardDAV (연락처) |
| Phase 5 | 추가 서비스 통합 | BBB Greenlight OIDC, OMV Proxy Auth |

---

## 9. 기술 스택 요약

| 분류 | 기술 |
|------|------|
| Identity Provider | Authentik 2025.10.4 |
| 인증 프로토콜 | OIDC, LDAP, OAuth2 |
| 리버스 프록시 | Nginx (Rocky Linux 10) |
| TLS 인증서 | Let's Encrypt (certbot + ACME) |
| 컨테이너 (Docker) | Authentik, Gitea, RustDesk Pro, Game Panel |
| 컨테이너 (Podman) | Stalwart Mail, LDAP Outpost |
| 메일 서버 | Stalwart Mail Server (RocksDB) |
| Git 호스팅 | Gitea 1.25.4 |
| DNS | Windows Server DNS, Pi-Hole |
| 호스트 OS | Windows (WSL2), Rocky Linux 10, Rocky Linux 9.7 |
| 가상화 | Hyper-V |

---

## 10. 보안 고려사항

### 10.1 적용된 보안 정책

- ISMS-P 기준 보안 헤더 전 사이트 적용
- TLS 1.2+ 강제 (HSTS preload)
- 서버 정보 노출 차단 (`server_tokens off`, `X-Powered-By` / `Server` 헤더 제거)
- 스캐너/봇 차단 규칙
- DKIM + SPF + DMARC 이메일 인증 체계

### 10.2 계획된 보안 강화

- PTR 레코드 등록으로 역방향 DNS 검증 완성
- CSP(Content-Security-Policy) 헤더 추가 검토
- Authentik MFA(다중 인증) 정책 강화

---

*문서 끝. 최종 갱신: 2026-02-18*
