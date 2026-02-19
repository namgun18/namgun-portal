# Phase 5-6: 서비스 개선, 메일/회의 통합 및 네이티브 로그인/SSO

## 작업 요약

| 항목 | 내용 |
|------|------|
| 작업일 | 2026-02-18 ~ 2026-02-19 |
| 작성자 | 남기완 |
| 대상 시스템 | namgun.or.kr 포털 (WSL2 Docker, 192.168.0.50) |
| Nginx VM | 192.168.0.150 (Rocky Linux 10, Hyper-V) |
| BBB 서버 | 192.168.0.249 (meet.namgun.or.kr) |
| 인증 서버 | auth.namgun.or.kr (Authentik 2025.10.4) |
| 프로젝트 경로 | `/mnt/d/Docker/namgun-portal` |

---

## Phase 5: 서비스 개선 및 메일/회의 통합

---

## 1. 파일브라우저 성능 개선

### 1.1 인메모리 TTL 캐시

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

### 1.2 캐시 무효화

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

### 1.3 비동기 래핑

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

### 1.4 NFS 환경 최적화 효과

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| 디렉토리 리스팅 응답 | 200~500ms (NFS I/O) | <5ms (캐시 히트) |
| 이벤트 루프 차단 | 발생 | 없음 (`to_thread`) |
| 동시 요청 처리 | I/O 대기 중 차단 | 논블로킹 병렬 처리 |
| 캐시 일관성 | N/A | 쓰기 시 즉시 무효화 |

---

## 2. 대시보드 서비스 카드 변경

### 2.1 SERVICE_DEFS 변경사항

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

### 2.2 변경 상세

| 서비스 | 변경 전 | 변경 후 | 사유 |
|--------|---------|---------|------|
| Stalwart Mail | `internal_only: False` | `internal_only: True` | 포털 내 iframe 통합 (`/mail` 페이지) |
| Pi-Hole | SERVICE_DEFS에 존재 | **제거** | 내부 DNS 서버, 대시보드 노출 불필요 |
| RustDesk | `health_url` (HTTP) | `health_tcp: "192.168.0.50:21114"` | RustDesk API 서버가 HTTP 헬스 엔드포인트를 제공하지 않음 |
| 화상회의 (BBB) | 없음 | **추가** | BigBlueButton 3.0 통합 |
| Gitea | `external_url` 일반 URL | OAuth 직접 트리거 URL | SSO 통합 (Phase 6) |

### 2.3 TCP 헬스체크 구현

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

### 2.4 ServiceStatus 스키마

```python
class ServiceStatus(BaseModel):
    name: str
    url: str | None       # external URL (None for internal_only display)
    status: str           # "ok" | "down" | "checking"
    response_ms: int | None
    internal_only: bool
```

`internal_only: True`인 서비스는 대시보드에서 외부 링크 대신 포털 내부 페이지로 연결된다.

---

## 3. BigBlueButton 화상회의 통합

### 3.1 아키텍처

```
[포털 프론트엔드] → /api/meetings/*
    → [FastAPI Backend] → BBB API (SHA256 checksum)
        → [BBB 3.0 서버] 192.168.0.249 (meet.namgun.or.kr)
```

### 3.2 BBB API 클라이언트

**구현 위치**: `backend/app/meetings/bbb.py`

#### 3.2.1 SHA256 체크섬 생성

BBB API는 모든 요청에 `checksum` 파라미터를 요구한다. 체크섬은 `SHA256(method + queryString + sharedSecret)` 방식으로 생성된다.

```python
def _checksum(method: str, query_string: str) -> str:
    raw = f"{method}{query_string}{settings.bbb_secret}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

#### 3.2.2 URL 빌드

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

#### 3.2.3 XML 파싱

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

#### 3.2.4 API 메서드

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

### 3.3 API 엔드포인트

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

### 3.4 Pydantic 스키마

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

### 3.5 프론트엔드 컴포넌트

#### 3.5.1 Composable: `useMeetings.ts`

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

#### 3.5.2 페이지: `meetings.vue`

**위치**: `frontend/pages/meetings.vue`

2개의 탭(회의/녹화)으로 구성되며, 회의 탭에서는 그리드 뷰와 상세 패널을 동시에 표시한다.

#### 3.5.3 컴포넌트 목록

| 컴포넌트 | 위치 | 설명 |
|----------|------|------|
| `MeetingCard.vue` | `frontend/components/meetings/` | 회의 카드 (이름, 상태, 참가자 수, 참가/종료 버튼) |
| `MeetingDetail.vue` | `frontend/components/meetings/` | 회의 상세 패널 (참가자 목록, 음성/비디오 상태) |
| `CreateMeetingModal.vue` | `frontend/components/meetings/` | 회의 생성 모달 (이름, 녹화, 시간 제한 등) |
| `RecordingList.vue` | `frontend/components/meetings/` | 녹화 목록 (재생, 삭제) |

### 3.6 BBB 서버 설정

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

---

## 4. Stalwart Mail 포털 내 통합

### 4.1 `/mail` 페이지

**위치**: `frontend/pages/mail.vue`

Stalwart Mail의 웹 UI를 포털 내 네이티브 메일 클라이언트로 통합하였다. 3단 레이아웃(사이드바, 메일 리스트, 메일 뷰)으로 구성된다.

```
[MailSidebar] | [MailList] | [MailView]
              |            |
              | [MailCompose 모달]
```

### 4.2 Nginx CSP 설정

Stalwart Mail 웹 UI를 포털 iframe에서 로드할 수 있도록 Nginx에 Content-Security-Policy 헤더를 설정하였다.

**설정 위치**: `mail.namgun.or.kr.conf` (192.168.0.150)

```nginx
# X-Frame-Options → CSP로 대체
add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
```

> **참고**: `X-Frame-Options: DENY`가 기존에 설정되어 있으면 CSP `frame-ancestors`와 충돌하므로 `X-Frame-Options` 헤더를 제거해야 한다.

### 4.3 JMAP API 클라이언트

**구현 위치**: `backend/app/mail/jmap.py`

향후 네이티브 메일 클라이언트(iframe이 아닌 완전한 자체 UI) 전환을 대비하여 JMAP 클라이언트를 구현하였다.

#### 4.3.1 JMAP Account ID 해석

Stalwart의 Admin API principal ID와 JMAP account ID가 다르다. JMAP accountId는 `hex(principal_id + offset)` 형식이며, offset은 설치별로 다르다.

```python
async def _discover_jmap_offset(client) -> int:
    """Discover the offset between admin API principal IDs and JMAP account IDs."""
    # offset 0~29 범위를 스캔하여 실제 데이터가 있는 계정 발견
    ...
```

#### 4.3.2 제공 API

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

#### 4.3.3 Mail API 엔드포인트

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

### 4.4 메일/회의 네비게이션 링크

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

---

## Phase 6: 네이티브 로그인 및 SSO 통합

---

## 5. 네이티브 로그인 아키텍처

### 5.1 개요

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

### 5.2 왜 팝업 브릿지 패턴인가

#### iframe의 한계

모던 브라우저(Chrome 120+, Firefox 118+, Safari 17+)는 **third-party cookie partitioning**을 적용한다. iframe 내의 `auth.namgun.or.kr`에서 설정된 쿠키는 top-level context(`namgun.or.kr`)와 파티셔닝되어 별도의 쿠키 저장소를 사용한다. 이로 인해:

1. iframe 내에서 Authentik에 로그인하더라도 SSO 세션 쿠키(`authentik_session`)가 다른 서비스(Gitea 등)의 OAuth 리다이렉트에서 인식되지 않는다.
2. Authentik의 CSRF 보호가 쿠키 불일치로 실패할 수 있다.

#### 팝업의 장점

팝업은 **top-level browsing context**로 취급된다. 따라서:

1. `auth.namgun.or.kr`에서 설정하는 쿠키가 **first-party cookie**로 저장된다.
2. Authentik의 `authentik_session` 쿠키가 정상적으로 설정되어 SSO가 작동한다.
3. `window.opener.postMessage()`를 통해 포털과 안전하게 통신할 수 있다.

### 5.3 브릿지 페이지 구성

브릿지 페이지는 Nginx VM(192.168.0.150)의 `auth.namgun.or.kr` 도메인에 배치된다. Authentik과 same-origin이므로 CORS 문제 없이 API를 호출할 수 있다.

#### 5.3.1 브릿지 메인 페이지

**위치**: `/var/www/portal-bridge/index.html` (192.168.0.150)

역할:
1. 포털로부터 `portal-login` 메시지 수신
2. Authentik Flow Executor API를 통한 인증 단계 수행
3. 인증 완료 후 OAuth authorize를 **페이지 네비게이션으로** 호출하여 SSO 쿠키를 확실히 설정
4. callback 페이지로 리다이렉트

#### 5.3.2 콜백 페이지

**위치**: `/var/www/portal-bridge/callback` (확장자 없음, 192.168.0.150)

역할:
1. URL에서 `code`와 `state` 파라미터 추출
2. `window.opener.postMessage()`로 포털에 코드 전달

> **주의**: 파일에 확장자가 없으므로 Nginx에서 `default_type text/html;`을 설정해야 한다.

#### 5.3.3 Nginx 설정

```nginx
# auth.namgun.or.kr.conf (192.168.0.150)
location /portal-bridge/ {
    alias /var/www/portal-bridge/;
    default_type text/html;
    add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
    add_header Cache-Control "no-store";
}
```

#### 5.3.4 SELinux

Rocky Linux 10에서 Nginx가 파일에 접근하려면 SELinux 컨텍스트가 올바르게 설정되어야 한다.

```bash
semanage fcontext -a -t httpd_sys_content_t "/var/www/portal-bridge(/.*)?"
restorecon -Rv /var/www/portal-bridge/
```

### 5.4 Authentik Flow Executor API 상세

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

### 5.5 PKCE (S256) 구현

#### 5.5.1 클라이언트 사이드 (Web Crypto API)

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

#### 5.5.2 서버 사이드 (기존 redirect 방식 유지)

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

### 5.6 Backend 변경사항

#### 5.6.1 `POST /api/auth/native-callback`

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

#### 5.6.2 `GET /api/auth/oidc-config`

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

#### 5.6.3 `POST /api/auth/logout`

Authentik end-session 호출을 제거하고, 포털 세션 쿠키만 클리어한다.

```python
@router.post("/logout")
async def logout():
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
```

> **사유**: 네이티브 로그인 방식에서는 Authentik 세션 쿠키의 유지가 SSO에 필수적이므로, 포털 로그아웃 시 Authentik 세션을 종료하지 않는다. Authentik 세션은 자연 만료되거나, 사용자가 Authentik 관리 UI에서 직접 종료할 수 있다.

#### 5.6.4 `exchange_code()` 변경

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

#### 5.6.5 `NativeCallbackRequest` 스키마

**구현 위치**: `backend/app/auth/schemas.py`

```python
class NativeCallbackRequest(BaseModel):
    code: str
    code_verifier: str
```

#### 5.6.6 `config.py` 설정 추가

```python
# Authentik Native Login
authentik_flow_slug: str = "default-authentication-flow"
bridge_redirect_uri: str = "https://auth.namgun.or.kr/portal-bridge/callback"
```

### 5.7 Frontend 변경사항

#### 5.7.1 `useAuth.ts` — `nativeLogin()` 함수

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

#### 5.7.2 `login.vue` — 네이티브 로그인 폼

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

---

## 6. SSO 통합

### 6.1 SSO 쿠키 메커니즘

#### 6.1.1 `authentik_session` 쿠키 특성

| 속성 | 값 | 설명 |
|------|-----|------|
| Domain | `auth.namgun.or.kr` | Authentik 도메인 |
| SameSite | `None` | cross-origin 요청에서도 전송 |
| Secure | `true` | HTTPS만 |
| HttpOnly | `true` | JavaScript 접근 불가 |
| Path | `/` | 전체 경로 |

#### 6.1.2 팝업에서의 SSO 쿠키 설정

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

#### 6.1.3 fetch() vs 페이지 네비게이션

| 방식 | 쿠키 설정 | SSO 지원 |
|------|-----------|----------|
| `fetch()` (JSON API) | credentials 설정에 따라 다름, 불확실 | 불안정 |
| 페이지 네비게이션 (`window.location`) | 브라우저 기본 동작으로 확실하게 설정 | 안정적 |

따라서 브릿지의 마지막 authorize 호출은 반드시 **페이지 네비게이션**으로 실행한다.

### 6.2 Gitea SSO

#### 6.2.1 Nginx 리다이렉트 설정

**설정 위치**: `git.namgun.or.kr.conf` (192.168.0.150)

```nginx
location = /user/login {
    return 302 https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik;
}
```

- 사용자가 `git.namgun.or.kr/user/login`에 접근하면 포털 로그인 페이지로 리다이렉트
- 로그인 완료 후 Gitea의 OAuth2 엔드포인트로 리다이렉트
- Authentik 세션 쿠키가 이미 설정되어 있으므로 자동 인증

#### 6.2.2 Gitea app.ini 설정

```ini
[service]
ENABLE_BASIC_AUTHENTICATION = true  ; git push 인증용
ENABLE_OPENID_SIGNIN = false        ; OpenID 로그인 비활성화
```

> **주의**: `ENABLE_BASIC_AUTHENTICATION = false`로 설정하면 git push 시 HTTPS 인증이 실패한다. Nginx가 웹 로그인은 이미 포털로 redirect하므로, 기본 인증은 활성화 상태로 유지해야 한다.

#### 6.2.3 대시보드 external_url

```python
# SERVICE_DEFS에서 Gitea의 external_url
"external_url": "https://git.namgun.or.kr/user/oauth2/authentik",
```

대시보드 서비스 카드에서 Gitea 클릭 시 OAuth2 엔드포인트를 직접 트리거하여, Authentik 세션이 있으면 자동으로 Gitea에 로그인된다.

### 6.3 Authentik 설정

#### 6.3.1 OAuth2 Provider redirect_uris

브릿지 콜백 URL을 redirect_uris에 추가:

```
https://auth.namgun.or.kr/portal-bridge/callback
```

기존 redirect_uri도 유지 (redirect 방식 로그인 fallback):

```
https://namgun.or.kr/api/auth/callback
```

#### 6.3.2 Authorization Flow

```
default-provider-authorization-implicit-consent
```

동의 화면 없이 즉시 인가 코드를 발급한다. 내부 포털이므로 매번 동의를 요구할 필요가 없다.

#### 6.3.3 Authentication Flow

```
default-authentication-flow
```

Authentik 기본 인증 플로우를 사용한다. 이 플로우의 slug가 `config.py`의 `authentik_flow_slug` 설정과 일치해야 한다.

---

## 7. 핵심 트러블슈팅

### 7.1 fetch()의 cross-origin redirect hang

**증상**: 포털에서 `fetch("https://auth.namgun.or.kr/application/o/authorize/?...")`를 호출하면 응답이 돌아오지 않고 hang 상태에 빠짐.

**원인**: `fetch()`가 cross-origin redirect를 따라가면서, Authentik이 로그인 페이지로 302 redirect를 반환하고, 이 리다이렉트 대상이 다시 redirect를 발생시키는 등 opaque redirect 체인이 형성되어 브라우저가 요청을 블록하였다.

**해결**: `redirect_uri`를 `auth.namgun.or.kr/portal-bridge/callback` (same-origin)으로 변경하여, Authentik API 호출이 same-origin에서 수행되도록 브릿지 아키텍처를 도입하였다.

### 7.2 opaque redirect loop — status=0

**증상**: `fetch(authorizeUrl, { redirect: "manual" })`로 호출하면 `response.status === 0`이 되어 Location 헤더에서 code를 추출할 수 없음.

**원인**: `redirect: "manual"` 옵션은 cross-origin redirect에서 opaque redirect response를 반환한다. 이 응답에서는 status, headers 등 모든 정보가 숨겨진다.

**해결**: same-origin redirect_uri를 사용하고, authorize를 fetch가 아닌 **페이지 네비게이션**(`window.location`)으로 호출하여 브라우저가 자연스럽게 redirect를 따라가도록 하였다. code는 callback 페이지에서 `URLSearchParams`로 추출한다.

### 7.3 query 파라미터 미인코딩

**증상**: Flow Executor API 호출 시 `query=response_type=code&client_id=...`에서 `client_id` 이후 파라미터가 누락됨.

**원인**: OAuth 파라미터 문자열의 `&`가 Flow Executor URL의 쿼리 파라미터 분리자로 해석되어, `query` 파라미터의 값이 첫 번째 `&` 이전까지만 전달되었다.

**해결**: `encodeURIComponent(oauthParams)`를 적용하여 `&`, `=` 등이 URL 인코딩되도록 하였다.

```javascript
const flowUrl = `/api/v3/flows/executor/${flowSlug}/?query=${encodeURIComponent(oauthParams)}`;
```

### 7.4 플로우 완료 후 `to: "/"`

**증상**: 비밀번호 인증 성공 후 Authentik이 `component: "xak-flow-redirect"`, `to: "/"` 응답을 반환. OAuth code가 발급되지 않음.

**원인**: Flow Executor를 JSON API로 호출하면, 플로우 완료 시 Authentik이 OAuth pending authorization context를 찾지 못한다. 이는 JSON API 세션과 OAuth authorize 세션이 분리되어 있기 때문이다.

**해결**: 플로우 완료(`to: "/"`) 확인 후, OAuth authorize를 **직접 재호출**한다. 이때 Authentik은 이미 인증된 세션을 인식하고, 동의 화면 없이(implicit consent) 즉시 code를 발급하여 redirect_uri로 리다이렉트한다.

### 7.5 iframe third-party cookie 문제

**증상**: iframe 내에서 Authentik 인증 후 설정된 `authentik_session` 쿠키가 Gitea 등 다른 서비스의 OAuth redirect에서 인식되지 않음.

**원인**: Chrome 120+, Firefox 118+, Safari 17+ 등 모던 브라우저의 **cookie partitioning** (CHIPS, Storage Partitioning) 정책. iframe 내의 third-party 쿠키는 (top-level-origin, embedded-origin) 쌍으로 파티셔닝되어, top-level context에서 직접 접근한 경우의 쿠키와 별도로 저장된다.

**해결**: iframe 대신 **popup** 방식으로 전환. 팝업은 top-level browsing context이므로 쿠키가 정상적으로 first-party로 설정된다.

### 7.6 popup-portal race condition

**증상**: 간헐적으로 `Bridge load timeout` 에러 발생. 팝업이 빠르게 로드되어 `portal-bridge-ready` 메시지를 보내는데, 포털의 메시지 리스너가 아직 설정되지 않은 상태.

**원인**: 팝업을 열고 `await`하는 사이에 팝업이 이미 로드 완료되어 `postMessage()`를 전송. 포털에서는 이후에 `addEventListener('message', ...)`를 호출하여 메시지를 놓침.

**해결**: **메시지 리스너를 팝업 열기 전에 설정**하여, 팝업의 ready 메시지를 반드시 수신할 수 있도록 하였다.

```typescript
// 1. 리스너 먼저 설정
const bridgeReady = new Promise<void>((resolve, reject) => {
    window.addEventListener('message', onReady)
})

// 2. 그 다음 팝업 열기
const popup = window.open(BRIDGE_URL, ...)
```

### 7.7 callback 파일 content-type

**증상**: `/portal-bridge/callback` 접근 시 브라우저가 파일 다운로드를 시도함.

**원인**: `callback` 파일에 `.html` 확장자가 없어 Nginx가 `application/octet-stream`으로 MIME 타입을 설정.

**해결**: Nginx location 블록에 `default_type text/html;`을 추가하여 확장자 없는 파일도 HTML로 서빙되도록 하였다.

```nginx
location /portal-bridge/ {
    alias /var/www/portal-bridge/;
    default_type text/html;
}
```

### 7.8 SSO 쿠키 미설정

**증상**: 네이티브 로그인 후 Gitea에 접근하면 다시 로그인을 요구함. `authentik_session` 쿠키가 없음.

**원인**: 전체 인증 흐름을 `fetch()` JSON API로만 수행하면, 브라우저가 `Set-Cookie` 헤더를 처리하지만 `SameSite=None` + `Secure` 조합에서 `credentials: 'include'` 설정 누락이나 preflight 문제로 쿠키가 불확실하게 설정됨.

**해결**: 브릿지의 마지막 authorize 호출을 `fetch()`가 아닌 **페이지 네비게이션**(`window.location.href = authorizeUrl`)으로 실행하여, 브라우저가 일반 페이지 요청으로 처리하고 쿠키를 확실하게 설정하도록 하였다.

### 7.9 Gitea 자동 로그인 안 됨

**증상**: 포털에서 로그인 후 Gitea 대시보드 링크를 클릭하면 Gitea 자체 로그인 페이지가 표시됨. OAuth auto-redirect가 동작하지 않음.

**원인**: Gitea는 기본적으로 자체 로그인 페이지(`/user/login`)를 표시하며, OAuth 자동 리다이렉트 기능이 내장되어 있지 않다.

**해결**: Nginx에서 Gitea의 `/user/login` 경로를 포털 로그인 페이지로 redirect하도록 설정. 포털에서 로그인하면 `redirect` 파라미터에 지정된 Gitea OAuth 엔드포인트로 이동하여, Authentik 세션을 이용한 자동 인증이 수행된다.

```nginx
location = /user/login {
    return 302 https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik;
}
```

### 7.10 git push 인증 실패

**증상**: `git push` 시 `403 Forbidden` 또는 인증 실패.

**원인**: `ENABLE_BASIC_AUTHENTICATION = false` 설정으로 인해 git CLI의 HTTP Basic 인증이 비활성화됨.

**해결**: `ENABLE_BASIC_AUTHENTICATION = true`로 다시 설정. Nginx에서 웹 브라우저의 `/user/login` 접근은 이미 포털로 redirect하므로, 기본 인증을 활성화해도 웹 로그인은 포털을 경유한다. git CLI는 Basic Auth로 직접 인증한다.

---

## 8. 수정 파일 목록

### 8.1 Backend

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

### 8.2 Frontend

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

### 8.3 Nginx (192.168.0.150)

| 파일 경로 | 설명 |
|-----------|------|
| `/etc/nginx/conf.d/auth.namgun.or.kr.conf` | `/portal-bridge/` location 추가, `default_type text/html` |
| `/etc/nginx/conf.d/git.namgun.or.kr.conf` | `/user/login` → 포털 redirect |
| `/etc/nginx/conf.d/mail.namgun.or.kr.conf` | CSP `frame-ancestors` 설정 |

### 8.4 브릿지 파일 (192.168.0.150)

| 파일 경로 | 설명 |
|-----------|------|
| `/var/www/portal-bridge/index.html` | 브릿지 메인 (Flow Executor 인증) |
| `/var/www/portal-bridge/callback` | 콜백 (code 추출 → postMessage) |

---

## 9. Nginx 설정 변경 상세

### 9.1 auth.namgun.or.kr.conf

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

### 9.2 git.namgun.or.kr.conf

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

### 9.3 mail.namgun.or.kr.conf

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

---

## 10. 검증 결과

### 10.1 Phase 5 검증

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

### 10.2 Phase 6 검증

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

---

## 11. 잔여 작업

- [ ] Authentik 세션 만료 시 포털 자동 재인증 UX 개선
- [ ] BBB 녹화 자동 정리 정책 설정
- [ ] JMAP 기반 네이티브 메일 UI 완성 (현재 iframe 방식에서 전환)
- [ ] 메일 첨부파일 업로드 (JMAP Blob upload)
- [ ] 다중 브라우저 SSO 테스트 (Safari, Firefox strict mode)
- [ ] 모바일 브라우저 팝업 호환성 검증 (iOS Safari, Android Chrome)
