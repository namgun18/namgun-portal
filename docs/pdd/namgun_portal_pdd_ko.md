# namgun.or.kr 종합 포털 SSO 통합 플랫폼

## 프로젝트 설계 문서 (PDD) v1.0

| 항목 | 내용 |
|------|------|
| 문서 버전 | v1.0 |
| 작성일 | 2026-02-18 |
| 작성자 | 남기완 |
| 분류 | Internal / Confidential |
| 대상 도메인 | namgun.or.kr (*.namgun.or.kr) |

---

## 1. 프로젝트 개요

### 1.1 배경 및 목적

namgun.or.kr 도메인에서 운영 중인 6개 독립 서비스(Gitea, Game Panel, RustDesk, FileBrowser, BigBlueButton, 메일서버)가 각각 별도 인증 체계를 사용하여 크레덴셜 분산 문제가 발생하고 있다. 본 프로젝트는 SSO(Single Sign-On) 통합 포털을 구축하여 단일 크레덴셜 소스로 모든 서비스를 통합 관리하는 것을 목표로 한다.

### 1.2 프로젝트 범위

- SSO IdP(Authentik) 배포 및 전 서비스 OIDC/LDAP 연동
- 메일서버 마이그레이션 (iRedMail → Stalwart Mail Server)
- 파일서버 재구성 (OMV FileBrowser → WebDAV + 포털 파일 탭)
- 통합 포털 개발 (메일, 파일, 캘린더, 연락처, 블로그, 알림)
- Nginx 리버스 프록시 통합 (TLS 종단, 단일 진입점)
- 테스트/프로덕션 환경 분리 (Docker Compose Profile)

---

## 2. 현재 인프라 현황

### 2.1 하드웨어 환경

| 컴포넌트 | 사양 | 용도 |
|---------|------|------|
| 홈랩 서버 | Dual Intel Xeon Gold 6138 / 128GB RAM | Docker Host, Hyper-V Host |
| NAS 스토리지 | 4TB HDD (Hyper-V 패스스루) | OMV VM → 파일서버 |
| 메일서버 | 전용 호스트 211.244.144.69 | iRedMail (SMTP/IMAP) |

### 2.2 서비스 현황 및 SSO 연동 분석

| 서비스 | 서브도메인 | SSO 방식 | 포털 통합 | 우선순위 |
|--------|-----------|---------|----------|---------|
| Gitea | git.namgun.or.kr | OIDC 네이티브 | 외부 링크 | P1 |
| RustDesk | remote.namgun.or.kr | OIDC (Pro) | 외부 링크 | P1 |
| BBB | meet.namgun.or.kr | OIDC (Greenlight 3.x) | 외부 링크 | P2 |
| Stalwart Mail | mail.namgun.or.kr | OIDC + LDAP | 네이티브 (JMAP: 메일/캘린더/연락처) | P2 |
| OMV/FileServer | file.namgun.or.kr | Proxy Auth | 네이티브 (WebDAV) | P2 |
| Game Panel | game.namgun.or.kr | N/A (Discord OAuth2) | 외부 링크 | - |

---

## 3. 아키텍처 설계

### 3.1 크레덴셜 소스 토폴로지

Authentik을 단일 크레덴셜 소스(Single Source of Truth)로 사용하며, 서비스별 특성에 맞는 인증 프로토콜을 제공한다.

```
[Authentik (단일 크레덴셜 소스)]
  ├── OIDC → Gitea, RustDesk, BBB, Stalwart(웹), Portal
  ├── LDAP Outpost → Stalwart(IMAP/SMTP, 메일 클라이언트용)
  ├── Proxy Auth → OMV WebDAV
  └── X Game Panel (독립, Discord OAuth2)
```

### 3.2 네트워크 아키텍처

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
    │           ├── /api/calendar/* → Stalwart JMAP (CalDAV)
    │           ├── /api/contacts/* → Stalwart CardDAV
    │           ├── /api/blog/*     → PostgreSQL
    │           └── /api/notify/*   → 통합 알림
    │
    ├── auth.namgun.or.kr   → Authentik (IdP)
    ├── git.namgun.or.kr    → Gitea
    ├── remote.namgun.or.kr → RustDesk Pro
    ├── meet.namgun.or.kr   → BBB (Greenlight)
    ├── game.namgun.or.kr   → Game Panel
    ├── demo.namgun.or.kr   → 데모 (mock, 프론트엔드만)
    ├── dev.namgun.or.kr    → 테스트 환경
    │
    └── mail.namgun.or.kr (:25/465/587/993)
          → Stalwart (211.244.144.69)
          ※ SMTP/IMAP 직접, 웹 UI만 리버스 프록시
```

### 3.3 백엔드 프록시 패턴 (엔드포인트 은닉)

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

## 4. 기술 스택

### 4.1 프론트엔드: Nuxt 3 (Vue.js)

**선정 근거:**

- **React Server Components(RSC) 취약점 회피**: CVE-2025-55182 (React2Shell, CVSS 10.0) — 사전인증 RCE 취약점이 2025년 12월 공개되어 대규모 실제 공격이 발생. Vue.js/Nuxt는 RSC 구조가 없어 해당 취약점 유형에 구조적으로 면역
- **비개발자 유지보수 용이성**: Vue 템플릿 문법이 HTML과 거의 동일하여 인프라 엔지니어가 직관적으로 이해 가능
- **SSR/SSG 지원**: 블로그 SSG, 대시보드 SSR 혼용 가능
- **공공/대기업 SI 표준**: 국내 대기업 SI 시장에서 Vue.js가 GS인증 표준으로 채택

### 4.2 백엔드: FastAPI (Python)

**선정 근거:**

- Python 기반으로 기존 자동화 도구 개발 경험과 시너지
- Swagger UI 자동 생성으로 API 문서화 부담 최소화
- 비동기(async) 네이티브로 다수 외부 서비스 API 동시 호출에 적합
- JMAP, WebDAV, CalDAV, CardDAV 프로토콜 클라이언트 구현이 용이

### 4.3 IdP: Authentik

**선정 근거:**

- OIDC Provider + LDAP Outpost 동시 제공 (단일 배포)
- Docker 네이티브 (PostgreSQL + Redis)
- Forward Auth/Proxy Auth 네이티브 지원
- 리소스: ~2-3GB RAM (현재 환경에서 여유)
- 기각된 대안: Keycloak (Java, 3-4GB+ RAM, 홈랩 과도), Authelia (OIDC Provider 미성숙)

### 4.4 메일서버: Stalwart Mail Server

iRedMail 커뮤니티에서 Stalwart Mail Server(AGPL-3.0)로 교체한다.

- v0.11.5부터 OIDC client 기능 오픈소스화 (Enterprise 불필요)
- LDAP 백엔드 네이티브 지원 (Authentik LDAP Outpost 연동)
- All-in-one Rust 바이너리: SMTP, IMAP, POP3, JMAP, CalDAV, CardDAV, WebDAV, Sieve
- 빌트인 웹 UI + JMAP API (포털 메일 탭 구현 가능, Roundcube 불필요)
- 공식 Docker 이미지: `stalwartlabs/stalwart:latest`

### 4.5 기술 스택 요약

| 계층 | 기술 | 라이선스 |
|------|------|---------|
| 프론트엔드 | Nuxt 3 + Vue 3 + TailwindCSS | MIT |
| 백엔드 | FastAPI + Python 3.12+ | MIT |
| IdP | Authentik | MIT |
| 메일서버 | Stalwart Mail Server | AGPL-3.0 |
| DB | PostgreSQL | PostgreSQL License |
| 블로그 렌더링 | @nuxt/content (MDX) | MIT |
| 리버스 프록시 | Nginx | BSD-2-Clause |
| 컨테이너 | Docker + Docker Compose | Apache-2.0 |
| 파일서버 | OpenMediaVault + WebDAV | GPL-3.0 |
| 원격 데스크톱 | RustDesk Pro | Custom (Pro) |
| Git 서버 | Gitea | MIT |
| 화상회의 | BigBlueButton + Greenlight 3.x | LGPL-3.0 |

---

## 5. 보안 설계

### 5.1 React 배제 근거

CVE-2025-55182 (React2Shell)는 CVSS 10.0 만점의 사전인증 RCE 취약점으로, 단일 HTTP 요청으로 서버에서 임의 코드 실행이 가능하다. 2025년 12월 공개 직후 중국 국가지원 해킹 그룹이 수시간 내에 익스플로잇을 시작했으며, 이후 추가 CVE 3건(CVE-2025-55183, CVE-2025-55184, CVE-2025-67779)이 발견되었다.

개인 호스팅 환경에서는 WAF, 전담 보안팀 등 기업급 보호 장치가 없으므로, 취약점 표면을 구조적으로 제거하는 것이 최선의 방어이다. Vue.js/Nuxt는 RSC 아키텍처가 없어 동일 유형의 취약점이 구조적으로 불가능하다.

### 5.2 인증/인가 보안

- Authentik OIDC: Authorization Code Flow with PKCE
- Authentik LDAP Outpost: 메일 클라이언트용 비밀번호 인증 (OAUTHBEARER 미지원 클라이언트 대응)
- Nginx Forward Auth: OMV WebDAV 접근 시 Authentik 인증 위임
- SSO 토큰 기반 API 인증: 모든 /api/* 요청에 인증 미들웨어 적용

### 5.3 네트워크 보안

- TLS 종단: Nginx에서 단일 TLS 종단, 내부 통신은 평문 (Docker 네트워크)
- 엔드포인트 은닉: 모든 내부 서비스 IP/포트 외부 미노출
- OMV 방화벽: FastAPI 백엔드 IP만 허용 (이중 방어)
- Nginx 설정 규칙: deprecated 지시어 사용 금지 (`ssl on`, `listen ssl http2` → `listen 443 ssl;` + `http2 on;`)

### 5.4 데이터 보안

- Authentik DB 정기 백업 (SPOF 대응)
- 로컬 admin 계정 fallback (인증 서버 장애 시 비상 접근)
- Stalwart 마이그레이션: imapsync dry-run 후 무결성 검증
- DNS SPF/DKIM/DMARC 재설정: Stalwart DKIM 키 재생성

---

## 6. 포털 기능 명세

### 6.1 대시보드 (홈)

- 서비스 상태 카드 (Health Check API 기반)
- 알림 피드 (메일 수신, 서비스 장애 통합)
- 외부 서비스 바로가기 (자동 SSO 리디렉션)

### 6.2 메일 탭

- Stalwart JMAP API 기반 브라우저 이메일 클라이언트
- 받은편지함, 작성, 답장, 첨부파일, 폴더 관리
- 포털 SSO 토큰을 JMAP 엔드포인트로 전달

### 6.3 파일 탭

- OMV WebDAV 기반 브라우저 파일 관리자
- 탐색, 업로드, 다운로드, 이름변경, 삭제, 폴더 생성
- FastAPI 백엔드 프록시를 통해 OMV 주소 완전 은닉

### 6.4 캘린더 탭

- Stalwart CalDAV API 기반
- 일정 조회, 생성, 수정, 삭제

### 6.5 연락처 탭

- Stalwart CardDAV API 기반
- 연락처 조회, 생성, 수정, 삭제

### 6.6 블로그 탭

- 포털 자체 DB(PostgreSQL)에 마크다운 저장 및 렌더링
- 공개/비공개 설정, 태그, 코드 하이라이팅
- @nuxt/content 기반 SSG로 SEO 최적화

### 6.7 알림 센터

- 메일 수신 알림 + 서비스 장애 알림 통합
- Health Check 폴러 기반 실시간 모니터링

---

## 7. 테스트/프로덕션 환경 분리

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

---

## 8. 개발 로드맵

### Phase 0: 인프라 준비

1. Authentik Docker Compose 배포 (server, worker, PostgreSQL, Redis)
2. DNS 설정: *.namgun.or.kr 와일드카드 또는 개별 A 레코드
3. TLS 인증서: Let's Encrypt (ACME DNS-01 challenge)
4. Nginx 리버스 프록시: auth.namgun.or.kr → Authentik
5. 초기 admin 계정 생성, 브랜딩 설정

### Phase 1: SSO PoC

1. Authentik에서 Gitea용 OIDC 애플리케이션 생성
2. Gitea OAuth2 인증 소스 설정 및 SSO 플로우 검증
3. RustDesk Pro OIDC 설정 및 플로우 검증

### Phase 2: 메일서버 마이그레이션

1. Stalwart Docker 배포 및 Authentik LDAP Outpost 연동
2. Authentik OIDC 애플리케이션 생성 (Stalwart 웹 UI용)
3. imapsync dry-run 및 실제 마이그레이션 실행
4. DNS 업데이트: DKIM 키 재생성, SPF/DKIM/DMARC 갱신
5. 2주 병렬 운영 후 iRedMail 폐기

### Phase 3: 포털 코어 개발

1. Nuxt 3 프로젝트 초기화 + FastAPI 백엔드 스캐폴딩
2. Authentik OIDC 로그인 (Authorization Code Flow with PKCE)
3. 대시보드: 서비스 상태 카드 + 외부 서비스 링크
4. Docker Compose Profile 기반 dev/prod 분리

### Phase 4: 네이티브 통합

1. 메일 탭 (JMAP 클라이언트)
2. 파일 탭 (WebDAV 클라이언트)
3. 캘린더 탭 (CalDAV 클라이언트)
4. 연락처 탭 (CardDAV 클라이언트)
5. 블로그 탭 (마크다운 기반)
6. 알림 센터 (통합 알림)

### Phase 5: 나머지 SSO 통합

1. BBB Greenlight 3.x OIDC 설정
2. OMV Proxy Auth 최종 확정

---

## 9. 리스크 평가

| 리스크 | 영향 | 확률 | 완화 방안 |
|--------|------|------|----------|
| iRedMail 마이그레이션 데이터 손실 | High | Low | imapsync dry-run, Maildir 백업 |
| Stalwart OIDC-only 메일 바운스 | High | Med | Authentik LDAP를 primary 백엔드로 사용 |
| 메일 클라이언트 OAUTHBEARER 미지원 | Med | High | LDAP Outpost로 비밀번호 인증 병행 |
| Authentik SPOF | High | Low | 로컬 admin fallback, 정기 DB 백업 |
| DNS/TLS 전파 지연 | Med | Low | 낮은 TTL 사전 설정, dig 검증 후 전환 |
| 프론트엔드 프레임워크 취약점 | Critical | N/A | React/RSC 배제, Vue.js/Nuxt 채택으로 구조적 제거 |

---

## 10. 참고 문헌

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

*End of Document*
