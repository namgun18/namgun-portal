# Phase 5-6: Service Improvements, Mail/Meeting Integration, and Native Login/SSO

## Summary

| Item | Details |
|------|---------|
| Date | 2026-02-18 ~ 2026-02-19 |
| Author | 남기완 (Kiwan Nam) |
| Classification | Internal / Confidential |
| Target System | namgun.or.kr portal (WSL2 Docker, 192.168.0.50) |
| Nginx VM | 192.168.0.150 (Rocky Linux 10, Hyper-V) |
| BBB Server | 192.168.0.249 (meet.namgun.or.kr) |
| Auth Server | auth.namgun.or.kr (Authentik 2025.10.4) |
| Project Path | `/mnt/d/Docker/namgun-portal` |

---

## Phase 5: Service Improvements and Mail/Meeting Integration

---

## 1. File Browser Performance Improvements

### 1.1 In-Memory TTL Cache

In the NFS v4.1 environment, each directory listing request triggered `iterdir()` + `stat()` system calls, resulting in observed latencies of several hundred milliseconds. An in-memory TTL cache was introduced to address this.

**Implementation location**: `backend/app/files/service.py`

```python
# TTL cache: {real_path_str: (timestamp, [FileItem, ...])}
_dir_cache: dict[str, tuple[float, list[FileItem]]] = {}
_CACHE_TTL = 30  # seconds

# TTL cache for directory sizes: {path_str: (timestamp, size_bytes)}
_size_cache: dict[str, tuple[float, int]] = {}
_SIZE_CACHE_TTL = 60  # seconds
```

| Item | Value | Description |
|------|-------|-------------|
| `_dir_cache` | TTL 30s | Directory file listing cache |
| `_size_cache` | TTL 60s | Directory size calculation cache |
| Cache key | `str(real_path.resolve())` | Absolute path string |
| Time source | `time.monotonic()` | Unaffected by system clock changes |

**Cache lookup logic** (`list_directory()`):

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

### 1.2 Cache Invalidation

After every write operation (upload, delete, rename, move, mkdir), `invalidate_cache()` must be called to immediately remove the cache entry for the affected directory.

```python
def invalidate_cache(real_path: Path) -> None:
    key = str(real_path.resolve())
    _dir_cache.pop(key, None)
    _size_cache.clear()
```

**Call sites** (`backend/app/files/router.py`):

| Operation | Invalidation Target |
|-----------|---------------------|
| `upload_file()` | `fs.invalidate_cache(real_dir)` |
| `delete_file()` | `fs.invalidate_cache(real.parent)` |
| `rename_file()` | `fs.invalidate_cache(real.parent)` |
| `move_file()` | `fs.invalidate_cache(src_real.parent)` + `fs.invalidate_cache(dst_real)` |
| `mkdir()` | `fs.invalidate_cache(parent_real)` |

> **Note**: `_size_cache` is cleared entirely on write operations (`_size_cache.clear()`) because parent directories may be affected.

### 1.3 Async Wrapping

Since NFS I/O is a blocking call, it was wrapped with `asyncio.to_thread()` to avoid blocking FastAPI's async event loop.

```python
# backend/app/files/router.py
items = await asyncio.to_thread(fs.list_directory, real, vp)
```

The same wrapping is applied to storage information queries:

```python
personal, shared = await asyncio.gather(
    asyncio.to_thread(fs.get_dir_size, personal_path),
    asyncio.to_thread(fs.get_dir_size, shared_path),
)
```

### 1.4 NFS Environment Optimization Results

| Item | Before | After |
|------|--------|-------|
| Directory listing response | 200~500ms (NFS I/O) | <5ms (cache hit) |
| Event loop blocking | Occurred | None (`to_thread`) |
| Concurrent request handling | Blocked during I/O wait | Non-blocking parallel processing |
| Cache consistency | N/A | Immediate invalidation on write |

---

## 2. Dashboard Service Card Changes

### 2.1 SERVICE_DEFS Changes

**Implementation location**: `backend/app/services/health.py`

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
        "name": "Video Conference (BBB)",
        "health_url": "https://meet.namgun.or.kr/bigbluebutton/api",
        "external_url": None,
        "internal_only": True,
    },
]
```

### 2.2 Change Details

| Service | Before | After | Reason |
|---------|--------|-------|--------|
| Stalwart Mail | `internal_only: False` | `internal_only: True` | Integrated within portal via iframe (`/mail` page) |
| Pi-Hole | Present in SERVICE_DEFS | **Removed** | Internal DNS server; dashboard exposure unnecessary |
| RustDesk | `health_url` (HTTP) | `health_tcp: "192.168.0.50:21114"` | RustDesk API server does not provide an HTTP health endpoint |
| Video Conference (BBB) | Not present | **Added** | BigBlueButton 3.0 integration |
| Gitea | `external_url` generic URL | OAuth direct trigger URL | SSO integration (Phase 6) |

### 2.3 TCP Health Check Implementation

For RustDesk, the health check is performed by attempting a TCP port connection instead of an HTTP endpoint.

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

### 2.4 ServiceStatus Schema

```python
class ServiceStatus(BaseModel):
    name: str
    url: str | None       # external URL (None for internal_only display)
    status: str           # "ok" | "down" | "checking"
    response_ms: int | None
    internal_only: bool
```

Services with `internal_only: True` are linked to internal portal pages on the dashboard instead of external URLs.

---

## 3. BigBlueButton Video Conference Integration

### 3.1 Architecture

```
[Portal Frontend] → /api/meetings/*
    → [FastAPI Backend] → BBB API (SHA256 checksum)
        → [BBB 3.0 Server] 192.168.0.249 (meet.namgun.or.kr)
```

### 3.2 BBB API Client

**Implementation location**: `backend/app/meetings/bbb.py`

#### 3.2.1 SHA256 Checksum Generation

The BBB API requires a `checksum` parameter on every request. The checksum is generated using the formula `SHA256(method + queryString + sharedSecret)`.

```python
def _checksum(method: str, query_string: str) -> str:
    raw = f"{method}{query_string}{settings.bbb_secret}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

#### 3.2.2 URL Construction

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

#### 3.2.3 XML Parsing

The BBB API returns XML responses, which are recursively converted to dictionaries. When the same tag appears multiple times (e.g., multiple `<attendee>` elements), it is automatically converted to a list.

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

#### 3.2.4 API Methods

| Function | BBB API | Description |
|----------|---------|-------------|
| `get_meetings()` | `getMeetings` | List active meetings |
| `get_meeting_info(meeting_id)` | `getMeetingInfo` | Meeting details |
| `create_meeting(name, ...)` | `create` | Create a meeting |
| `get_join_url(meeting_id, full_name, ...)` | `join` | Generate join URL |
| `end_meeting(meeting_id)` | `end` | End a meeting |
| `get_recordings(meeting_id?)` | `getRecordings` | List recordings |
| `delete_recording(record_id)` | `deleteRecordings` | Delete a recording |

`create_meeting()` parameters:

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

- If `meeting_id` is None, it is auto-generated using `uuid.uuid4()`
- If `moderator_pw`/`attendee_pw` are None, they are auto-generated in the format `mod-<hex8>`/`att-<hex8>`

### 3.3 API Endpoints

**Implementation location**: `backend/app/meetings/router.py`

| Method | Path | Description | Auth | Permission |
|--------|------|-------------|------|------------|
| GET | `/api/meetings/` | List active meetings | Required | All |
| GET | `/api/meetings/{meeting_id}` | Meeting details | Required | All |
| POST | `/api/meetings/` | Create a meeting | Required | All |
| POST | `/api/meetings/{meeting_id}/join` | Generate join URL | Required | All |
| POST | `/api/meetings/{meeting_id}/end` | End a meeting | Required | **admin** |
| GET | `/api/meetings/recordings` | List recordings | Required | All |
| DELETE | `/api/meetings/recordings/{record_id}` | Delete a recording | Required | **admin** |

> **Note**: In the `join` endpoint, if `user.is_admin` is true, the user joins with the `MODERATOR` role; otherwise, they join with the `VIEWER` role.

#### Router Registration

```python
# backend/app/main.py
from app.meetings.router import router as meetings_router
app.include_router(meetings_router)
```

### 3.4 Pydantic Schemas

**Implementation location**: `backend/app/meetings/schemas.py`

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

### 3.5 Frontend Components

#### 3.5.1 Composable: `useMeetings.ts`

**Location**: `frontend/composables/useMeetings.ts`

Module-level singleton state is used to share meeting state across the entire application.

```typescript
const meetings = ref<Meeting[]>([])
const selectedMeeting = ref<MeetingDetail | null>(null)
const recordings = ref<Recording[]>([])
const loadingMeetings = ref(false)
const loadingDetail = ref(false)
const loadingRecordings = ref(false)
const showCreateModal = ref(false)
```

Provided functions:

| Function | Description |
|----------|-------------|
| `fetchMeetings()` | Calls `GET /api/meetings/` |
| `fetchMeetingDetail(id)` | Calls `GET /api/meetings/{id}` |
| `createMeeting(data)` | Calls `POST /api/meetings/` then refreshes the list |
| `joinMeeting(id)` | Calls `POST /api/meetings/{id}/join` and opens the join URL in a new tab |
| `endMeeting(id)` | Calls `POST /api/meetings/{id}/end` then refreshes the list |
| `fetchRecordings(meetingId?)` | Calls `GET /api/meetings/recordings` |
| `deleteRecording(id)` | Calls `DELETE /api/meetings/recordings/{id}` then refreshes the list |
| `clearSelectedMeeting()` | Clears the selected meeting |

#### 3.5.2 Page: `meetings.vue`

**Location**: `frontend/pages/meetings.vue`

The page consists of two tabs (Meetings / Recordings). The Meetings tab displays a grid view and a detail panel side by side.

#### 3.5.3 Component List

| Component | Location | Description |
|-----------|----------|-------------|
| `MeetingCard.vue` | `frontend/components/meetings/` | Meeting card (name, status, participant count, join/end buttons) |
| `MeetingDetail.vue` | `frontend/components/meetings/` | Meeting detail panel (attendee list, voice/video status) |
| `CreateMeetingModal.vue` | `frontend/components/meetings/` | Meeting creation modal (name, recording, time limit, etc.) |
| `RecordingList.vue` | `frontend/components/meetings/` | Recording list (playback, delete) |

### 3.6 BBB Server Configuration

| Item | Value |
|------|-------|
| Server IP | 192.168.0.249 |
| Domain | meet.namgun.or.kr |
| API Endpoint | `https://meet.namgun.or.kr/bigbluebutton/api` |
| Version | BigBlueButton 3.0 |

Backend configuration (`backend/app/config.py`):

```python
bbb_url: str = "https://meet.namgun.or.kr/bigbluebutton/api"
bbb_secret: str = ""
```

---

## 4. Stalwart Mail Portal Integration

### 4.1 `/mail` Page

**Location**: `frontend/pages/mail.vue`

The Stalwart Mail web UI was integrated into the portal as a native mail client. The layout consists of three panels (sidebar, mail list, mail view).

```
[MailSidebar] | [MailList] | [MailView]
              |            |
              | [MailCompose modal]
```

### 4.2 Nginx CSP Configuration

A Content-Security-Policy header was configured in Nginx to allow loading the Stalwart Mail web UI within a portal iframe.

**Configuration location**: `mail.namgun.or.kr.conf` (192.168.0.150)

```nginx
# X-Frame-Options → replaced with CSP
add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
```

> **Note**: If `X-Frame-Options: DENY` was previously set, it conflicts with CSP `frame-ancestors`, so the `X-Frame-Options` header must be removed.

### 4.3 JMAP API Client

**Implementation location**: `backend/app/mail/jmap.py`

A JMAP client was implemented in preparation for a future transition to a fully native mail client (replacing the current iframe approach with a self-contained UI).

#### 4.3.1 JMAP Account ID Resolution

The Stalwart Admin API principal ID and the JMAP account ID differ. The JMAP accountId follows the format `hex(principal_id + offset)`, where the offset varies per installation.

```python
async def _discover_jmap_offset(client) -> int:
    """Discover the offset between admin API principal IDs and JMAP account IDs."""
    # Scans offset range 0~29 to find an account with actual data
    ...
```

#### 4.3.2 Provided API

| Function | JMAP Method | Description |
|----------|-------------|-------------|
| `get_session()` | `/.well-known/jmap` | Session information |
| `resolve_account_id(email)` | Admin API + JMAP | Email to JMAP account ID conversion |
| `get_mailboxes(account_id)` | `Mailbox/get` | Mailbox list |
| `get_messages(account_id, mailbox_id, ...)` | `Email/query` + `Email/get` | Message list |
| `get_message(account_id, message_id)` | `Email/get` (full) | Message details |
| `update_message(account_id, message_id, ...)` | `Email/set` (update) | Read/star/move |
| `destroy_message(account_id, message_id)` | `Email/set` (destroy) | Delete message |
| `send_message(account_id, ...)` | `Email/set` + `EmailSubmission/set` | Send message |
| `download_blob(account_id, blob_id)` | `/jmap/download/...` | Download attachment |

#### 4.3.3 Mail API Endpoints

**Implementation location**: `backend/app/mail/router.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/mail/mailboxes` | Mailbox list (sorted by role) |
| GET | `/api/mail/messages` | Message list (paginated) |
| GET | `/api/mail/messages/{id}` | Message details (automatically marks as read) |
| PATCH | `/api/mail/messages/{id}` | Read/star/move |
| DELETE | `/api/mail/messages/{id}` | Delete (trash then permanent delete) |
| POST | `/api/mail/send` | Send message |
| GET | `/api/mail/blob/{blob_id}` | Attachment download proxy |

### 4.4 Mail/Meeting Navigation Links

**Implementation location**: `frontend/components/layout/AppHeader.vue`

Mail and meeting links were added to the desktop/mobile navigation.

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

## Phase 6: Native Login and SSO Integration

---

## 5. Native Login Architecture

### 5.1 Overview

Previously, users were redirected to the Authentik UI during login and used Authentik's own login form. In Phase 6, the Authentik UI was fully replaced with a "native login" approach: users enter their username and password on the portal's own login form (`/login`), and authentication is performed in the background via the Authentik Flow Executor API.

```
[User] → Portal /login page (native login form)
    → [Popup] auth.namgun.or.kr/portal-bridge/ (bridge page)
        → Authentik Flow Executor API (same-origin)
        → OAuth authorize → callback → extract code
    → [postMessage] deliver code to portal
    → [Portal Backend] POST /api/auth/native-callback
        → Authentik Token exchange → issue session cookie
```

### 5.2 Why the Popup Bridge Pattern

#### Limitations of iframes

Modern browsers (Chrome 120+, Firefox 118+, Safari 17+) enforce **third-party cookie partitioning**. Cookies set by `auth.namgun.or.kr` within an iframe are partitioned from the top-level context (`namgun.or.kr`) and stored in a separate cookie jar. This causes:

1. Even if the user logs in to Authentik within an iframe, the SSO session cookie (`authentik_session`) is not recognized during OAuth redirects for other services (e.g., Gitea).
2. Authentik's CSRF protection may fail due to cookie mismatch.

#### Advantages of Popups

A popup is treated as a **top-level browsing context**. Therefore:

1. Cookies set by `auth.namgun.or.kr` are stored as **first-party cookies**.
2. The `authentik_session` cookie from Authentik is set correctly, enabling SSO to work.
3. Secure communication with the portal is possible via `window.opener.postMessage()`.

### 5.3 Bridge Page Structure

The bridge page is deployed on the Nginx VM (192.168.0.150) under the `auth.namgun.or.kr` domain. Being same-origin with Authentik, it can call the API without CORS issues.

#### 5.3.1 Bridge Main Page

**Location**: `/var/www/portal-bridge/index.html` (192.168.0.150)

Responsibilities:
1. Receive `portal-login` message from the portal
2. Perform authentication steps via the Authentik Flow Executor API
3. After authentication completes, call OAuth authorize via **page navigation** to reliably set SSO cookies
4. Redirect to the callback page

#### 5.3.2 Callback Page

**Location**: `/var/www/portal-bridge/callback` (no extension, 192.168.0.150)

Responsibilities:
1. Extract `code` and `state` parameters from the URL
2. Deliver the code to the portal via `window.opener.postMessage()`

> **Note**: Since the file has no extension, `default_type text/html;` must be set in Nginx.

#### 5.3.3 Nginx Configuration

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

On Rocky Linux 10, Nginx requires the correct SELinux context to access files.

```bash
semanage fcontext -a -t httpd_sys_content_t "/var/www/portal-bridge(/.*)?"
restorecon -Rv /var/www/portal-bridge/
```

### 5.4 Authentik Flow Executor API Details

The complete authentication flow performed by the bridge page proceeds through the following steps.

#### Step 1: Register OAuth Pending Authorization

```javascript
await fetch("/application/o/authorize/?" + oauthParams, {
    redirect: "manual"
});
```

By calling with `redirect: "manual"`, the actual redirect is not followed; instead, a pending authorization is registered within Authentik. At this point, the status is 0 (opaque redirect).

#### Step 2: Start Flow Executor

```javascript
const flowUrl = `/api/v3/flows/executor/${flowSlug}/?query=${encodeURIComponent(oauthParams)}`;
const resp = await fetch(flowUrl, {
    headers: { "Accept": "application/json" }
});
const challenge = await resp.json();
```

> **Key point**: When passing OAuth parameters in the `query` parameter, `encodeURIComponent()` must be applied. Otherwise, `&` characters are interpreted as URL separators and parameters are lost.

#### Step 3: ak-stage-identification (User Identification)

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

#### Step 4: xak-flow-redirect (Mid-flow Redirect)

If Authentik sends a mid-flow redirect, the specified URL is followed.

```javascript
// challenge.component === "xak-flow-redirect"
// If challenge.to is a relative path, make a GET request to that path
```

#### Step 5: ak-stage-password (Password Submission)

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

#### Step 6: Flow Completion — `xak-flow-redirect to="/"`

Upon successful password authentication, Authentik returns a response with `component: "xak-flow-redirect"` and `to: "/"`. This indicates that the flow has completed, but Authentik cannot find the OAuth context and is attempting to redirect to the home page.

> **Key issue**: Because the Flow Executor was called via the JSON API, Authentik cannot automatically process the OAuth pending authorization at the point of flow completion.

#### Step 7: Re-invoke Authorize (Page Navigation)

```javascript
// After flow completion, call OAuth authorize via page navigation
// Execute via window.location change, not fetch()
window.location.href = "/application/o/authorize/?" + oauthParams;
```

This ensures:
1. The SSO session cookie (`authentik_session`) is **reliably** set (since it is a top-level navigation).
2. Authentik recognizes the already-authenticated session and issues an OAuth code.
3. The browser redirects to `redirect_uri` (`/portal-bridge/callback`).

#### Step 8: Extract Code from Callback

```javascript
// /portal-bridge/callback page
const params = new URLSearchParams(window.location.search);
const code = params.get("code");
window.opener.postMessage({
    type: "portal-login-result",
    success: true,
    code: code
}, "https://namgun.or.kr");
```

### 5.5 PKCE (S256) Implementation

#### 5.5.1 Client Side (Web Crypto API)

**Implementation location**: `frontend/composables/useAuth.ts`

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

#### 5.5.2 Server Side (Existing Redirect Flow Retained)

**Implementation location**: `backend/app/auth/oidc.py`

```python
def generate_pkce() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge
```

PKCE method:
- `code_challenge_method`: `S256`
- `code_verifier`: Generated on the client, sent during token exchange
- `code_challenge`: `BASE64URL(SHA256(code_verifier))`

### 5.6 Backend Changes

#### 5.6.1 `POST /api/auth/native-callback`

**Implementation location**: `backend/app/auth/router.py`

Exchanges the authorization code received from the bridge callback for a token with Authentik, retrieves user information, and issues a session cookie.

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

    # Upsert user (same logic as callback)
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

Key differences:
- `redirect_uri` is set to `settings.bridge_redirect_uri` (bridge callback URL instead of the original callback URL)
- The response is a `JSONResponse`, not a redirect

#### 5.6.2 `GET /api/auth/oidc-config`

Returns public configuration needed by the browser to generate PKCE parameters.

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

Removed the Authentik end-session call and only clears the portal session cookie.

```python
@router.post("/logout")
async def logout():
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
```

> **Rationale**: In the native login approach, maintaining the Authentik session cookie is essential for SSO. Therefore, the portal logout does not terminate the Authentik session. The Authentik session expires naturally or can be manually terminated by the user via the Authentik admin UI.

#### 5.6.4 `exchange_code()` Changes

An optional `redirect_uri` parameter was added so the function can be used by both the native callback and the existing callback.

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

#### 5.6.5 `NativeCallbackRequest` Schema

**Implementation location**: `backend/app/auth/schemas.py`

```python
class NativeCallbackRequest(BaseModel):
    code: str
    code_verifier: str
```

#### 5.6.6 `config.py` Configuration Additions

```python
# Authentik Native Login
authentik_flow_slug: str = "default-authentication-flow"
bridge_redirect_uri: str = "https://auth.namgun.or.kr/portal-bridge/callback"
```

### 5.7 Frontend Changes

#### 5.7.1 `useAuth.ts` — `nativeLogin()` Function

**Implementation location**: `frontend/composables/useAuth.ts`

The existing `login()` function (redirect to Authentik UI) was replaced with the `nativeLogin()` function (popup bridge approach).

```typescript
const BRIDGE_URL = 'https://auth.namgun.or.kr/portal-bridge/'
const BRIDGE_ORIGIN = 'https://auth.namgun.or.kr'
const BRIDGE_CALLBACK = 'https://auth.namgun.or.kr/portal-bridge/callback'
```

`nativeLogin()` function flow:

1. **Register bridge-ready listener** (before opening the popup)
2. **Open popup synchronously** (`window.open()` — executed before any await to avoid popup blockers)
3. **Wait for bridge-ready + fetch OIDC config** (Promise.all in parallel)
4. **Generate PKCE** (code_verifier, code_challenge, state)
5. **Send credentials to popup** (`popup.postMessage()`)
6. **Wait for result** (portal-login-result message)
7. **Exchange code** (`POST /api/auth/native-callback`)
8. **Fetch user info** (`GET /api/auth/me`)

```typescript
const nativeLogin = async (username: string, password: string): Promise<void> => {
    // 1. Set up listener (before opening popup — prevents race condition)
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

    // 2. Open popup synchronously (before await)
    const popup = window.open(BRIDGE_URL, '_portal_auth', 'width=1,height=1,left=-100,top=-100')
    if (!popup) throw new Error('Popup was blocked.')

    try {
        // 3~8. Authentication flow...
    } finally {
        popup.close()
    }
}
```

> **Note**: The popup size is set to 1x1 and positioned off-screen so it is invisible to the user.

#### 5.7.2 `login.vue` — Native Login Form

**Implementation location**: `frontend/pages/login.vue`

- `layout: 'auth'` (full-screen centered layout)
- Username/email + password input form
- Supports `redirect` query parameter (navigates to the original page after login)
- Error messages displayed in Korean (authentication failure, timeout, etc.)

```typescript
const redirectTo = computed(() => {
    const r = route.query.redirect as string | undefined
    // Domain validation: only allow https URLs under the namgun.or.kr domain
    if (r && (r.startsWith('https://') && r.includes('.namgun.or.kr'))) return r
    return '/'
})
```

---

## 6. SSO Integration

### 6.1 SSO Cookie Mechanism

#### 6.1.1 `authentik_session` Cookie Properties

| Attribute | Value | Description |
|-----------|-------|-------------|
| Domain | `auth.namgun.or.kr` | Authentik domain |
| SameSite | `None` | Sent on cross-origin requests |
| Secure | `true` | HTTPS only |
| HttpOnly | `true` | Inaccessible to JavaScript |
| Path | `/` | Entire path |

#### 6.1.2 SSO Cookie Setting via Popup

```
[Popup] = top-level browsing context
    ↓
[auth.namgun.or.kr] = first-party
    ↓
authentik_session cookie = stored as first-party cookie
    ↓
[Gitea OAuth redirect] → auth.namgun.or.kr
    ↓
authentik_session cookie = sent automatically → automatic authentication
```

#### 6.1.3 fetch() vs Page Navigation

| Approach | Cookie Setting | SSO Support |
|----------|---------------|-------------|
| `fetch()` (JSON API) | Depends on credentials configuration; unreliable | Unstable |
| Page navigation (`window.location`) | Reliably set by default browser behavior | Stable |

Therefore, the final authorize call from the bridge must be executed as a **page navigation**.

### 6.2 Gitea SSO

#### 6.2.1 Nginx Redirect Configuration

**Configuration location**: `git.namgun.or.kr.conf` (192.168.0.150)

```nginx
location = /user/login {
    return 302 https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik;
}
```

- When a user accesses `git.namgun.or.kr/user/login`, they are redirected to the portal login page
- After login, the user is redirected to Gitea's OAuth2 endpoint
- Since the Authentik session cookie is already set, authentication occurs automatically

#### 6.2.2 Gitea app.ini Configuration

```ini
[service]
ENABLE_BASIC_AUTHENTICATION = true  ; required for git push authentication
ENABLE_OPENID_SIGNIN = false        ; disable OpenID login
```

> **Warning**: Setting `ENABLE_BASIC_AUTHENTICATION = false` causes HTTPS authentication to fail during git push. Since Nginx already redirects web login to the portal, basic authentication must remain enabled.

#### 6.2.3 Dashboard external_url

```python
# Gitea external_url in SERVICE_DEFS
"external_url": "https://git.namgun.or.kr/user/oauth2/authentik",
```

When clicking Gitea on the dashboard service card, the OAuth2 endpoint is triggered directly. If an Authentik session exists, the user is automatically logged in to Gitea.

### 6.3 Authentik Configuration

#### 6.3.1 OAuth2 Provider redirect_uris

Add the bridge callback URL to redirect_uris:

```
https://auth.namgun.or.kr/portal-bridge/callback
```

The existing redirect_uri is also retained (fallback for redirect-based login):

```
https://namgun.or.kr/api/auth/callback
```

#### 6.3.2 Authorization Flow

```
default-provider-authorization-implicit-consent
```

Issues the authorization code immediately without a consent screen. Since this is an internal portal, requiring consent on every login is unnecessary.

#### 6.3.3 Authentication Flow

```
default-authentication-flow
```

Uses the default Authentik authentication flow. The slug of this flow must match the `authentik_flow_slug` setting in `config.py`.

---

## 7. Key Troubleshooting

### 7.1 fetch() Cross-Origin Redirect Hang

**Symptom**: Calling `fetch("https://auth.namgun.or.kr/application/o/authorize/?...")` from the portal results in no response and a hang state.

**Cause**: When `fetch()` follows a cross-origin redirect, Authentik returns a 302 redirect to the login page, which in turn triggers additional redirects, forming an opaque redirect chain that causes the browser to block the request.

**Resolution**: Changed `redirect_uri` to `auth.namgun.or.kr/portal-bridge/callback` (same-origin), and introduced the bridge architecture so that Authentik API calls are performed from same-origin.

### 7.2 Opaque Redirect Loop — status=0

**Symptom**: Calling `fetch(authorizeUrl, { redirect: "manual" })` results in `response.status === 0`, making it impossible to extract the code from the Location header.

**Cause**: The `redirect: "manual"` option returns an opaque redirect response for cross-origin redirects. All information including status and headers is hidden in this response.

**Resolution**: Used a same-origin redirect_uri and executed the authorize call via **page navigation** (`window.location`) instead of fetch, allowing the browser to naturally follow the redirect. The code is extracted from the callback page using `URLSearchParams`.

### 7.3 Unencoded Query Parameters

**Symptom**: When calling the Flow Executor API with `query=response_type=code&client_id=...`, parameters after `client_id` are lost.

**Cause**: The `&` characters in the OAuth parameter string were interpreted as query parameter separators in the Flow Executor URL, causing the `query` parameter value to be truncated at the first `&`.

**Resolution**: Applied `encodeURIComponent(oauthParams)` so that `&`, `=`, and other characters are URL-encoded.

```javascript
const flowUrl = `/api/v3/flows/executor/${flowSlug}/?query=${encodeURIComponent(oauthParams)}`;
```

### 7.4 `to: "/"` After Flow Completion

**Symptom**: After successful password authentication, Authentik returns `component: "xak-flow-redirect"` with `to: "/"`. No OAuth code is issued.

**Cause**: When the Flow Executor is called via the JSON API, Authentik cannot locate the OAuth pending authorization context at flow completion. This is because the JSON API session and the OAuth authorize session are separate.

**Resolution**: After confirming flow completion (`to: "/"`), **re-invoke OAuth authorize directly**. At this point, Authentik recognizes the already-authenticated session and immediately issues a code with implicit consent, redirecting to the redirect_uri.

### 7.5 iframe Third-Party Cookie Issue

**Symptom**: The `authentik_session` cookie set after authenticating within an iframe is not recognized during OAuth redirects for other services such as Gitea.

**Cause**: **Cookie partitioning** (CHIPS, Storage Partitioning) policy in modern browsers including Chrome 120+, Firefox 118+, and Safari 17+. Third-party cookies within an iframe are partitioned by the (top-level-origin, embedded-origin) pair, stored separately from cookies set when accessing the same origin directly as a top-level context.

**Resolution**: Switched from iframe to **popup** approach. Since a popup is a top-level browsing context, cookies are correctly set as first-party.

### 7.6 Popup-Portal Race Condition

**Symptom**: Intermittent `Bridge load timeout` errors. The popup loads quickly and sends the `portal-bridge-ready` message while the portal's message listener has not yet been set up.

**Cause**: The popup finishes loading and calls `postMessage()` during the interval between opening the popup and the next `await`. The portal then calls `addEventListener('message', ...)` afterward, missing the message.

**Resolution**: **Set up the message listener before opening the popup** to ensure the bridge's ready message is always received.

```typescript
// 1. Set up listener first
const bridgeReady = new Promise<void>((resolve, reject) => {
    window.addEventListener('message', onReady)
})

// 2. Then open the popup
const popup = window.open(BRIDGE_URL, ...)
```

### 7.7 Callback File Content-Type

**Symptom**: Accessing `/portal-bridge/callback` causes the browser to attempt a file download.

**Cause**: The `callback` file has no `.html` extension, so Nginx sets the MIME type to `application/octet-stream`.

**Resolution**: Added `default_type text/html;` to the Nginx location block so that files without an extension are served as HTML.

```nginx
location /portal-bridge/ {
    alias /var/www/portal-bridge/;
    default_type text/html;
}
```

### 7.8 SSO Cookie Not Set

**Symptom**: After native login, accessing Gitea requires logging in again. The `authentik_session` cookie is missing.

**Cause**: When the entire authentication flow is performed solely via `fetch()` JSON API, the browser processes the `Set-Cookie` header but the cookie may be unreliably set due to missing `credentials: 'include'` configuration or preflight issues with the `SameSite=None` + `Secure` combination.

**Resolution**: Changed the bridge's final authorize call from `fetch()` to **page navigation** (`window.location.href = authorizeUrl`), so the browser processes it as a standard page request and reliably sets the cookie.

### 7.9 Gitea Auto-Login Failure

**Symptom**: After logging in to the portal, clicking the Gitea dashboard link displays Gitea's own login page. OAuth auto-redirect does not work.

**Cause**: Gitea displays its own login page (`/user/login`) by default and does not have a built-in OAuth auto-redirect feature.

**Resolution**: Configured Nginx to redirect Gitea's `/user/login` path to the portal login page. After logging in to the portal, the user is directed to the Gitea OAuth endpoint specified in the `redirect` parameter, where automatic authentication is performed using the Authentik session.

```nginx
location = /user/login {
    return 302 https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik;
}
```

### 7.10 git push Authentication Failure

**Symptom**: `git push` results in `403 Forbidden` or authentication failure.

**Cause**: The `ENABLE_BASIC_AUTHENTICATION = false` setting disabled HTTP Basic authentication for the git CLI.

**Resolution**: Changed the setting back to `ENABLE_BASIC_AUTHENTICATION = true`. Since Nginx already redirects browser access to `/user/login` to the portal, enabling basic authentication does not affect web login, which still goes through the portal. The git CLI authenticates directly via Basic Auth.

---

## 8. Modified File List

### 8.1 Backend

| File Path | Description |
|-----------|-------------|
| `backend/app/config.py` | Added `bbb_url`, `bbb_secret`, `authentik_flow_slug`, `bridge_redirect_uri` settings |
| `backend/app/main.py` | Registered `meetings_router`, `mail_router` |
| `backend/app/auth/router.py` | Added `native-callback`, `oidc-config` endpoints; modified `logout` |
| `backend/app/auth/oidc.py` | Added optional `redirect_uri` parameter to `exchange_code()` |
| `backend/app/auth/schemas.py` | Added `NativeCallbackRequest` schema |
| `backend/app/auth/deps.py` | Session authentication logic (unchanged, for reference) |
| `backend/app/services/health.py` | Modified `SERVICE_DEFS`: Stalwart `internal_only`, removed Pi-Hole, RustDesk TCP, added BBB |
| `backend/app/services/schemas.py` | `internal_only` field on `ServiceStatus` (added in Phase 4) |
| `backend/app/files/service.py` | Added `_dir_cache`, `_size_cache` TTL caches and `invalidate_cache()` |
| `backend/app/files/router.py` | Added `asyncio.to_thread()` wrapping; `invalidate_cache()` calls after write operations |
| `backend/app/mail/__init__.py` | Mail module initialization |
| `backend/app/mail/jmap.py` | JMAP client (session, mailbox, message CRUD, send, attachments) |
| `backend/app/mail/schemas.py` | Mail API Pydantic schemas |
| `backend/app/mail/router.py` | Mail API endpoints (mailboxes, messages, send, attachment proxy) |
| `backend/app/meetings/__init__.py` | Meetings module initialization |
| `backend/app/meetings/bbb.py` | BBB API client (SHA256 checksum, XML parsing) |
| `backend/app/meetings/schemas.py` | Meetings API Pydantic schemas |
| `backend/app/meetings/router.py` | Meetings API endpoints (CRUD, join, recordings) |

### 8.2 Frontend

| File Path | Description |
|-----------|-------------|
| `frontend/composables/useAuth.ts` | Added `nativeLogin()` function, PKCE/bridge constants; removed `login()` |
| `frontend/composables/useMail.ts` | Mail state management composable (mailboxes, messages, send, attachments) |
| `frontend/composables/useMeetings.ts` | Meetings state management composable (list, detail, create, join, recordings) |
| `frontend/pages/login.vue` | Native login form (supports redirect query parameter) |
| `frontend/pages/mail.vue` | Mail page (three-panel layout) |
| `frontend/pages/meetings.vue` | Meetings page (meetings/recordings tabs) |
| `frontend/pages/callback.vue` | OAuth callback page (existing, retained) |
| `frontend/components/layout/AppHeader.vue` | Added mail/meetings links to navigation |
| `frontend/components/mail/MailSidebar.vue` | Mail sidebar (mailbox list) |
| `frontend/components/mail/MailList.vue` | Mail list |
| `frontend/components/mail/MailView.vue` | Mail detail view |
| `frontend/components/mail/MailCompose.vue` | Mail compose modal |
| `frontend/components/meetings/MeetingCard.vue` | Meeting card component |
| `frontend/components/meetings/MeetingDetail.vue` | Meeting detail panel |
| `frontend/components/meetings/CreateMeetingModal.vue` | Meeting creation modal |
| `frontend/components/meetings/RecordingList.vue` | Recording list component |
| `frontend/middleware/auth.global.ts` | Auth middleware (`/login` included in publicPages) |

### 8.3 Nginx (192.168.0.150)

| File Path | Description |
|-----------|-------------|
| `/etc/nginx/conf.d/auth.namgun.or.kr.conf` | Added `/portal-bridge/` location with `default_type text/html` |
| `/etc/nginx/conf.d/git.namgun.or.kr.conf` | `/user/login` redirect to portal |
| `/etc/nginx/conf.d/mail.namgun.or.kr.conf` | CSP `frame-ancestors` configuration |

### 8.4 Bridge Files (192.168.0.150)

| File Path | Description |
|-----------|-------------|
| `/var/www/portal-bridge/index.html` | Bridge main page (Flow Executor authentication) |
| `/var/www/portal-bridge/callback` | Callback (code extraction via postMessage) |

---

## 9. Nginx Configuration Change Details

### 9.1 auth.namgun.or.kr.conf

```nginx
server {
    listen 443 ssl http2;
    server_name auth.namgun.or.kr;

    # ... SSL, existing Authentik proxy settings ...

    # Portal bridge pages
    location /portal-bridge/ {
        alias /var/www/portal-bridge/;
        default_type text/html;
        add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
        add_header Cache-Control "no-store";
    }

    # Existing Authentik proxy
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

    # ... SSL settings ...

    # SSO: redirect web login to portal
    location = /user/login {
        return 302 https://namgun.or.kr/login?redirect=https://git.namgun.or.kr/user/oauth2/authentik;
    }

    # Existing Gitea proxy
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

    # ... SSL settings ...

    location / {
        proxy_pass http://192.168.0.250:8080;
        # ...

        # Allow iframe embedding (used by portal)
        add_header Content-Security-Policy "frame-ancestors 'self' https://namgun.or.kr";
        # X-Frame-Options removed (replaced by CSP frame-ancestors)
    }
}
```

---

## 10. Verification Results

### 10.1 Phase 5 Verification

| Test Item | Result |
|-----------|--------|
| File list cache hit (re-request within 30 seconds) | PASS |
| Cache invalidation after file upload (immediate reflection) | PASS |
| Cache invalidation after file deletion | PASS |
| Cache invalidation after file rename | PASS |
| Cache invalidation of source/target directories after file move | PASS |
| Cache invalidation after folder creation | PASS |
| asyncio.to_thread async wrapping operation | PASS |
| Dashboard service card: Stalwart internal_only display | PASS |
| Dashboard service card: Pi-Hole removal confirmed | PASS |
| RustDesk TCP health check (port 21114) | PASS |
| BBB service card display | PASS |
| BBB meeting list query | PASS |
| BBB meeting creation | PASS |
| BBB meeting join (MODERATOR/VIEWER) | PASS |
| BBB meeting end (admin only) | PASS |
| BBB recording list query | PASS |
| BBB recording deletion (admin only) | PASS |
| Mail page (/mail) access | PASS |
| Mailbox list query | PASS |
| Message list query (pagination) | PASS |
| Message detail view (automatic mark as read) | PASS |
| Send message | PASS |
| Attachment download | PASS |
| AppHeader mail/meetings navigation links | PASS |

### 10.2 Phase 6 Verification

| Test Item | Result |
|-----------|--------|
| Native login form display | PASS |
| Login with valid credentials | PASS |
| Error message for invalid credentials | PASS |
| PKCE S256 verification (Authentik token exchange) | PASS |
| Error message when popup is blocked | PASS |
| Login timeout handling | PASS |
| Session cookie issuance (portal_session) | PASS |
| Logout (session cookie deletion) | PASS |
| authentik_session SSO cookie setting confirmed | PASS |
| Automatic Gitea login after portal login (SSO) | PASS |
| Gitea /user/login redirect to portal | PASS |
| git push HTTPS authentication (Basic Auth) | PASS |
| redirect query parameter (navigate to original page after login) | PASS |
| Bridge page Content-Type (text/html) | PASS |
| Bridge page SELinux context | PASS |
| /api/auth/oidc-config endpoint | PASS |
| /api/auth/native-callback endpoint | PASS |
| No bridge-ready message race condition | PASS |
| Popup auto-close (after login completion/failure) | PASS |

---

## 11. Remaining Work

- [ ] Improve UX for automatic re-authentication when Authentik session expires
- [ ] Configure automatic cleanup policy for BBB recordings
- [ ] Complete JMAP-based native mail UI (transition from current iframe approach)
- [ ] Mail attachment upload (JMAP Blob upload)
- [ ] Multi-browser SSO testing (Safari, Firefox strict mode)
- [ ] Mobile browser popup compatibility verification (iOS Safari, Android Chrome)
