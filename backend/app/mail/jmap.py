"""JMAP client for Stalwart Mail Server."""

import httpx

from app.config import get_settings

settings = get_settings()

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.stalwart_url,
            auth=(settings.stalwart_admin_user, settings.stalwart_admin_password),
            timeout=30.0,
            follow_redirects=True,
        )
    return _client


# ─── Account ID cache (email → JMAP account ID) ───

_account_cache: dict[str, str] = {}
_jmap_offset: int | None = None  # principal_id + offset = JMAP document ID


async def get_session() -> dict:
    """GET /.well-known/jmap → session object with accounts."""
    client = _get_client()
    resp = await client.get("/.well-known/jmap")
    resp.raise_for_status()
    return resp.json()


async def _discover_jmap_offset(client) -> int:
    """Discover the offset between admin API principal IDs and JMAP account IDs.

    Stalwart stores JMAP accounts as RocksDB documents with sequential IDs.
    The offset = (JMAP document ID) - (principal ID) is fixed per installation.
    We discover it by scanning a range of JMAP accountIds to find one with data.
    """
    global _jmap_offset
    if _jmap_offset is not None:
        return _jmap_offset

    # Get principals with known data (non-zero quota)
    resp = await client.get("/api/principal", params={"types": "individual", "limit": 100})
    resp.raise_for_status()
    principals = resp.json().get("data", {}).get("items", [])

    # Find a principal with usedQuota > 0 to use as reference
    ref = None
    for p in principals:
        if p.get("usedQuota", 0) > 0:
            ref = p
            break

    if not ref:
        # No principal with data — use default offset of 10
        _jmap_offset = 10
        return _jmap_offset

    ref_pid = ref["id"]

    # Scan offsets 0-20 to find the one that yields emails
    for offset in range(0, 30):
        jmap_id = format(ref_pid + offset, "x")
        try:
            body = {
                "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
                "methodCalls": [
                    ["Email/query", {"accountId": jmap_id, "calculateTotal": True, "limit": 0}, "q0"],
                ],
            }
            r = await client.post("/jmap", json=body)
            if r.status_code != 200:
                continue
            result = r.json()
            for mr in result.get("methodResponses", []):
                if mr[0] == "Email/query" and mr[1].get("total", 0) > 0:
                    _jmap_offset = offset
                    return _jmap_offset
        except Exception:
            continue

    # Fallback
    _jmap_offset = 10
    return _jmap_offset


async def resolve_account_id(email: str) -> str | None:
    """Resolve email to Stalwart JMAP account ID.

    Admin API principal IDs differ from JMAP account IDs.
    JMAP accountId = hex(principal_id + offset) where offset is installation-specific.
    """
    if email in _account_cache:
        return _account_cache[email]

    client = _get_client()

    # Discover offset if not yet known
    offset = await _discover_jmap_offset(client)

    # Get all principals and build cache
    resp = await client.get("/api/principal", params={"types": "individual", "limit": 100})
    resp.raise_for_status()
    data = resp.json()

    for item in data.get("data", {}).get("items", []):
        emails = item.get("emails", [])
        name = item.get("name", "")
        principal_id = item.get("id", 0)
        jmap_id = format(principal_id + offset, "x")
        for e in emails:
            _account_cache[e] = jmap_id
        _account_cache[name] = jmap_id

    # Try email match
    if email in _account_cache:
        return _account_cache[email]

    # Try username part (before @)
    username = email.split("@")[0]
    if username in _account_cache:
        _account_cache[email] = _account_cache[username]
        return _account_cache[email]

    return None


# ─── Generic JMAP call ───


async def jmap_call(method_calls: list, account_id: str | None = None) -> dict:
    """POST /jmap with JMAP method calls."""
    client = _get_client()
    body = {
        "using": [
            "urn:ietf:params:jmap:core",
            "urn:ietf:params:jmap:mail",
            "urn:ietf:params:jmap:submission",
        ],
        "methodCalls": method_calls,
    }
    resp = await client.post("/jmap", json=body)
    resp.raise_for_status()
    return resp.json()


# ─── Mailboxes ───


async def get_mailboxes(account_id: str) -> list[dict]:
    """Get all mailboxes for an account."""
    result = await jmap_call([
        ["Mailbox/get", {"accountId": account_id}, "m0"],
    ])
    for resp in result.get("methodResponses", []):
        if resp[0] == "Mailbox/get":
            return resp[1].get("list", [])
    return []


# ─── Messages ───


async def get_messages(
    account_id: str,
    mailbox_id: str,
    page: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    """Query + fetch messages for a mailbox. Returns (messages, total)."""
    position = page * limit
    result = await jmap_call([
        [
            "Email/query",
            {
                "accountId": account_id,
                "filter": {"inMailbox": mailbox_id},
                "sort": [{"property": "receivedAt", "isAscending": False}],
                "position": position,
                "limit": limit,
                "calculateTotal": True,
            },
            "q0",
        ],
        [
            "Email/get",
            {
                "accountId": account_id,
                "#ids": {
                    "resultOf": "q0",
                    "name": "Email/query",
                    "path": "/ids",
                },
                "properties": [
                    "id", "threadId", "mailboxIds", "from", "to",
                    "subject", "preview", "receivedAt",
                    "keywords", "hasAttachment",
                ],
            },
            "g0",
        ],
    ])

    total = 0
    messages = []
    for resp in result.get("methodResponses", []):
        if resp[0] == "Email/query":
            total = resp[1].get("total", 0)
        elif resp[0] == "Email/get":
            messages = resp[1].get("list", [])

    return messages, total


async def get_message(account_id: str, message_id: str) -> dict | None:
    """Get full message detail including body and attachments."""
    result = await jmap_call([
        [
            "Email/get",
            {
                "accountId": account_id,
                "ids": [message_id],
                "properties": [
                    "id", "threadId", "mailboxIds", "from", "to", "cc", "bcc",
                    "replyTo", "subject", "preview", "receivedAt",
                    "keywords", "hasAttachment",
                    "textBody", "htmlBody", "attachments", "bodyValues",
                ],
                "fetchTextBodyValues": True,
                "fetchHTMLBodyValues": True,
                "fetchAllBodyValues": True,
            },
            "g0",
        ],
    ])

    for resp in result.get("methodResponses", []):
        if resp[0] == "Email/get":
            msgs = resp[1].get("list", [])
            return msgs[0] if msgs else None
    return None


# ─── Update message (read/star/move) ───


async def update_message(account_id: str, message_id: str, updates: dict) -> bool:
    """Update message keywords or mailboxIds."""
    result = await jmap_call([
        [
            "Email/set",
            {
                "accountId": account_id,
                "update": {message_id: updates},
            },
            "u0",
        ],
    ])
    for resp in result.get("methodResponses", []):
        if resp[0] == "Email/set":
            updated = resp[1].get("updated")
            return updated is not None and message_id in updated
    return False


# ─── Destroy message ───


async def destroy_message(account_id: str, message_id: str) -> bool:
    """Permanently delete a message."""
    result = await jmap_call([
        [
            "Email/set",
            {
                "accountId": account_id,
                "destroy": [message_id],
            },
            "d0",
        ],
    ])
    for resp in result.get("methodResponses", []):
        if resp[0] == "Email/set":
            destroyed = resp[1].get("destroyed", [])
            return message_id in destroyed
    return False


# ─── Send message ───


async def send_message(
    account_id: str,
    from_addr: dict,
    to: list[dict],
    cc: list[dict],
    bcc: list[dict],
    subject: str,
    text_body: str,
    html_body: str | None = None,
    in_reply_to: str | None = None,
    references: list[str] | None = None,
    mailbox_ids: dict | None = None,
) -> dict | None:
    """Create and send an email in one JMAP call."""
    email_body = [{"partId": "text", "type": "text/plain"}]
    body_values = {"text": {"value": text_body}}

    if html_body:
        email_body = [
            {"partId": "text", "type": "text/plain"},
            {"partId": "html", "type": "text/html"},
        ]
        body_values["html"] = {"value": html_body}

    email_create = {
        "from": [from_addr],
        "to": to,
        "subject": subject,
        "bodyValues": body_values,
        "textBody": [{"partId": "text", "type": "text/plain"}],
        "keywords": {"$seen": True},
    }

    if html_body:
        email_create["htmlBody"] = [{"partId": "html", "type": "text/html"}]

    if cc:
        email_create["cc"] = cc
    if bcc:
        email_create["bcc"] = bcc
    if in_reply_to:
        email_create["inReplyTo"] = [in_reply_to]
    if references:
        email_create["references"] = references
    if mailbox_ids:
        email_create["mailboxIds"] = mailbox_ids

    result = await jmap_call([
        [
            "Email/set",
            {
                "accountId": account_id,
                "create": {"draft": email_create},
            },
            "c0",
        ],
        [
            "EmailSubmission/set",
            {
                "accountId": account_id,
                "onSuccessUpdateEmail": {
                    "#sendIt": {
                        "keywords/$draft": None,
                    },
                },
                "create": {
                    "sendIt": {
                        "emailId": "#draft",
                        "envelope": None,
                    },
                },
            },
            "s0",
        ],
    ])

    for resp in result.get("methodResponses", []):
        if resp[0] == "Email/set":
            created = resp[1].get("created", {})
            if "draft" in created:
                return created["draft"]
    return None


# ─── Blob download ───


async def download_blob(account_id: str, blob_id: str) -> httpx.Response:
    """Download a blob (attachment) from Stalwart."""
    client = _get_client()
    # Use fixed URL path instead of session downloadUrl (which may use public hostname)
    url = f"/jmap/download/{account_id}/{blob_id}/attachment"
    resp = await client.get(url)
    resp.raise_for_status()
    return resp
