# namgun.or.kr 종합 포털

셀프 호스팅 통합 플랫폼. Authentik SSO를 중심으로 Git, 메일, 화상회의, 파일 관리, 게임 서버 등 독립 서비스를 하나의 포털 UI로 통합한다.

## 아키텍처

```
[사용자 브라우저]
       │
       ▼
┌──────────────────────────────────────┐
│  namgun.or.kr (통합 포털)             │
│  Frontend: Nuxt 3 (Vue 3, SSR)      │
│  Backend:  FastAPI (API Gateway)     │
│  DB:       PostgreSQL 16             │
└──────────┬───────────────────────────┘
           │ Nginx Reverse Proxy (192.168.0.150)
           │
   ┌───────┼─────────┬──────────────┬──────────────┬──────────────┐
   ▼       ▼         ▼              ▼              ▼              ▼
Authentik  Gitea    Stalwart     BigBlueButton  OMV(NFS)     Game Panel
 (SSO)    (Git)    (Mail/LDAP)   (화상회의)     (파일)        (게임서버)
```

## 기술 스택

| 분류 | 기술 |
|------|------|
| 프론트엔드 | Nuxt 3, Vue 3, TailwindCSS, shadcn-vue |
| 백엔드 | FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| 인증 | Authentik 2025.10.4 (OIDC, LDAP, Flow Executor API) |
| 데이터베이스 | PostgreSQL 16 |
| 메일 | Stalwart Mail Server v0.15 (JMAP, LDAP) |
| 화상회의 | BigBlueButton 3.0 |
| 파일 스토리지 | NFS v4.1 (OpenMediaVault) |
| Git | Gitea 1.25.4 |
| 컨테이너 | Docker Compose |
| 리버스 프록시 | Nginx (Rocky Linux 10) |
| TLS | Let's Encrypt (certbot + ACME) |

## 주요 기능

### 통합 인증
- 포털 자체 로그인 폼 (Authentik 미노출)
- 서버사이드 Flow Executor API 인증
- 포털 OIDC 제공자 (Gitea 등 외부 서비스 SSO)
- 승인제 회원가입 (`username@namgun.or.kr` 자동 이메일)
- 비밀번호 변경/찾기 (Stalwart SMTP로 복구 링크 발송)

### 서비스 통합
- **파일 관리**: NFS 기반 웹 파일 브라우저 (업로드/다운로드/공유링크)
- **메일**: Stalwart JMAP 기반 웹메일 클라이언트
- **화상회의**: BBB API 기반 회의 생성/참가/녹화 관리
- **Git**: Gitea API 기반 저장소 브라우징, 코드 뷰어 (구문 강조), 이슈/PR 관리
- **대시보드**: 종합 홈화면 (서비스 상태, 최근 메일/Git 활동, 회의, 게임서버, 스토리지, 바로가기)

### 관리자 패널
- 사용자 승인/거절/비활성화
- 관리자 권한 부여/해제 (Authentik 그룹 동기화)
- 전체 사용자 목록 관리

## 배포

```bash
# 프로덕션 배포
docker compose --profile prod up -d --build

# 개발 환경
docker compose --profile dev up -d --build
```

### 환경 변수

`.env.example`을 `.env`로 복사한 뒤 설정:

```bash
cp .env.example .env
```

주요 설정:
- `SECRET_KEY` — 세션 서명 키 (64자 랜덤 문자열)
- `DATABASE_URL` — PostgreSQL 연결 URL
- `OIDC_*` — Authentik OIDC 설정
- `AUTHENTIK_API_TOKEN` — Authentik Admin API 토큰
- `AUTHENTIK_*_GROUP_PK` — Authentik 그룹 UUID
- `BBB_URL`, `BBB_SECRET` — BigBlueButton API
- `STALWART_URL` — Stalwart Mail JMAP 엔드포인트
- `GITEA_URL`, `GITEA_TOKEN` — Gitea API URL 및 관리자 토큰

## 프로젝트 구조

```
namgun-portal/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI 앱 초기화
│       ├── config.py            # 환경 설정
│       ├── auth/                # 인증 (로그인, 회원가입, OIDC, OAuth 제공자)
│       ├── admin/               # 관리자 API (사용자 관리, 권한)
│       ├── files/               # 파일 브라우저 (NFS)
│       ├── mail/                # 메일 (JMAP 클라이언트)
│       ├── meetings/            # 화상회의 (BBB API)
│       ├── git/                 # Git (Gitea API 클라이언트)
│       ├── dashboard/            # 대시보드 (게임서버 상태 등)
│       ├── services/            # 서비스 헬스체크
│       └── db/                  # DB 모델, 세션
├── frontend/
│   ├── pages/                   # Nuxt 페이지 (9개)
│   ├── components/              # Vue 컴포넌트 (31개)
│   ├── composables/             # 상태 관리 (5개)
│   ├── layouts/                 # 레이아웃 (default, auth)
│   └── middleware/              # 인증 미들웨어
├── nginx/                       # 내부 리버스 프록시 설정
├── docs/                        # 프로젝트 문서
├── docker-compose.yml
├── .env.example
└── README.md
```

## API 엔드포인트

| 모듈 | 경로 | 주요 기능 |
|------|------|-----------|
| 인증 | `/api/auth/*` | 로그인, 회원가입, 프로필, 비밀번호 변경/찾기 |
| OAuth | `/oauth/*` | OIDC Discovery, authorize, token, userinfo |
| 관리자 | `/api/admin/*` | 사용자 목록, 승인/거절, 권한 관리 |
| 파일 | `/api/files/*` | 파일 목록/업로드/다운로드/이동/삭제/공유 |
| 메일 | `/api/mail/*` | 메일박스, 메시지 CRUD, 전송, 첨부파일 |
| 회의 | `/api/meetings/*` | 회의 생성/참가/종료, 녹화 관리 |
| Git | `/api/git/*` | 저장소 검색, 코드 브라우징, 이슈/PR |
| 대시보드 | `/api/dashboard/*` | 게임서버 상태 조회 |
| 서비스 | `/api/services/*` | 서비스 상태 조회 |

## 문서

- [프로젝트 진행 보고서 (한국어)](docs/project_progress_ko.md)
- [Project Progress Report (English)](docs/project_progress_en.md)
- [PDD (한국어)](docs/pdd/namgun_portal_pdd_ko.md)
- [PDD (English)](docs/pdd/namgun_portal_pdd_en.md)

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v0.1.0 | 2026-02-18 | 포털 코어 + 파일 브라우저 + 메일/회의 통합 + 네이티브 로그인 |
| v0.2.0 | 2026-02-20 | 서버사이드 인증 전환, 포털 OIDC 제공자, Gitea SSO |
| v0.3.0 | 2026-02-21 | 승인제 회원가입, 관리자 패널, 권한 관리, 프로필/비밀번호 관리 |
| v0.4.0 | 2026-02-21 | BBB 새 탭 회의 참가 + 세션 종료 시 자동 탭 닫힘, Greenlight 로그인/등록 차단 |
| v0.5.0 | 2026-02-21 | Gitea 포털 내재화 — 저장소 브라우징, 코드 뷰어 (구문 강조), 이슈/PR 관리 |
| v0.5.1 | 2026-02-21 | 대시보드 홈화면 리뉴얼 — 인사말, 서비스 상태 바, 최근 메일/Git, 회의, 게임서버, 스토리지, 바로가기 |
| v0.5.2 | 2026-02-21 | 비주얼 리프레시 — 색상 팔레트 분리, 카드/버튼 인터랙션, 그라디언트 히어로·헤더, 위젯 색상 아이콘 |

## 라이선스

Private — Internal use only.
