"""JMAP client for Stalwart Mail Server."""

import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
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


async def get_session() -> dict:
    """GET /.well-known/jmap → session object with accounts."""
    client = _get_client()
    resp = await client.get("/.well-known/jmap")
    resp.raise_for_status()
    return resp.json()


def _encode_account_id(principal_id: int) -> str:
    """Encode principal_id to Stalwart JMAP accountId (bijective base-26).

    Stalwart uses: a=0, b=1, ..., z=25, aa=26, ab=27, ...
    """
    if principal_id < 26:
        return chr(ord("a") + principal_id)
    result = ""
    n = principal_id
    while n >= 0:
        result = chr(ord("a") + (n % 26)) + result
        n = n // 26 - 1
        if n < 0:
            break
    return result


async def resolve_account_id(email: str) -> str | None:
    """Resolve email to Stalwart JMAP account ID.

    Uses Admin API to get principal_id, then encodes with bijective base-26.
    """
    if email in _account_cache:
        return _account_cache[email]

    client = _get_client()

    # Get all principals and build cache (retry once on failure)
    data = {}
    for attempt in range(2):
        try:
            resp = await client.get("/api/principal", params={"types": "individual", "limit": 0})
            resp.raise_for_status()
            data = resp.json()
            break
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning("Stalwart principal API failed (attempt %d): %s", attempt + 1, e)
            if attempt == 1:
                raise
            _reconnect()
            client = _get_client()

    for item in data.get("data", {}).get("items", []):
        emails = item.get("emails", [])
        name = item.get("name", "")
        principal_id = item.get("id", 0)
        jmap_id = _encode_account_id(principal_id)
        for e in emails:
            _account_cache[e] = jmap_id
        _account_cache[name] = jmap_id

    # Try email match
    if email in _account_cache:
        return _account_cache[email]

    # Try username part (before @)
    if "@" in email:
        username = email.split("@")[0]
        if username and username in _account_cache:
            _account_cache[email] = _account_cache[username]
            return _account_cache[email]

    logger.warning("Mail account not found for: %s", email)
    return None


def _reconnect():
    """Force reconnect on next call."""
    global _client
    if _client and not _client.is_closed:
        try:
            import asyncio
            asyncio.get_event_loop().create_task(_client.aclose())
        except Exception:
            pass
    _client = None


def clear_cache():
    """Clear account cache (useful after Stalwart restart)."""
    _account_cache.clear()


# ─── Generic JMAP call ───


USING_MAIL = [
    "urn:ietf:params:jmap:core",
    "urn:ietf:params:jmap:mail",
    "urn:ietf:params:jmap:submission",
]

USING_CALENDAR = [
    "urn:ietf:params:jmap:core",
    "urn:ietf:params:jmap:calendars",
]

USING_CONTACTS = [
    "urn:ietf:params:jmap:core",
    "urn:ietf:params:jmap:contacts",
]


async def jmap_call(
    method_calls: list,
    account_id: str | None = None,
    using: list[str] | None = None,
) -> dict:
    """POST /jmap with JMAP method calls (retry once on connection error)."""
    body = {
        "using": using or USING_MAIL,
        "methodCalls": method_calls,
    }
    for attempt in range(2):
        try:
            client = _get_client()
            resp = await client.post("/jmap", json=body)
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
            logger.warning("JMAP call failed (attempt %d): %s", attempt + 1, e)
            if attempt == 1:
                raise
            _reconnect()
    raise httpx.ConnectError("JMAP call failed after retries")


# ─── Identities ───


async def get_identity_id(account_id: str) -> str | None:
    """Get the first (primary) identity ID for an account."""
    result = await jmap_call([
        ["Identity/get", {"accountId": account_id}, "i0"],
    ])
    for resp in result.get("methodResponses", []):
        if resp[0] == "Identity/get":
            ids = resp[1].get("list", [])
            if ids:
                return ids[0]["id"]
    return None


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
    query: str | None = None,
) -> tuple[list[dict], int]:
    """Query + fetch messages for a mailbox. Returns (messages, total)."""
    position = page * limit

    if query:
        jmap_filter = {
            "operator": "AND",
            "conditions": [
                {"inMailbox": mailbox_id},
                {"text": query},
            ],
        }
    else:
        jmap_filter = {"inMailbox": mailbox_id}

    result = await jmap_call([
        [
            "Email/query",
            {
                "accountId": account_id,
                "filter": jmap_filter,
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
    attachments: list[dict] | None = None,
) -> dict | None:
    """Create and send an email in one JMAP call."""
    # Resolve identity (required by Stalwart for EmailSubmission)
    identity_id = await get_identity_id(account_id)
    if not identity_id:
        logger.error("No identity found for account %s", account_id)
        return None

    body_values = {"text": {"value": text_body}}
    if html_body:
        body_values["html"] = {"value": html_body}

    # Build body structure
    if attachments:
        # multipart/mixed with body + attachments
        body_parts: list[dict] = []
        if html_body:
            body_parts.append({
                "type": "multipart/alternative",
                "subParts": [
                    {"partId": "text", "type": "text/plain"},
                    {"partId": "html", "type": "text/html"},
                ],
            })
        else:
            body_parts.append({"partId": "text", "type": "text/plain"})

        for att in attachments:
            body_parts.append({
                "blobId": att["blobId"],
                "type": att.get("type", "application/octet-stream"),
                "name": att.get("name"),
                "disposition": "attachment",
                "size": att.get("size", 0),
            })

        email_create = {
            "from": [from_addr],
            "to": to,
            "subject": subject,
            "bodyValues": body_values,
            "bodyStructure": {
                "type": "multipart/mixed",
                "subParts": body_parts,
            },
            "keywords": {"$seen": True},
        }
    else:
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
                        "identityId": identity_id,
                        "envelope": None,
                    },
                },
            },
            "s0",
        ],
    ])

    email_created = None
    submission_ok = False

    for resp in result.get("methodResponses", []):
        if resp[0] == "Email/set":
            created = resp[1].get("created", {})
            not_created = resp[1].get("notCreated", {})
            if "draft" in created:
                email_created = created["draft"]
            if not_created:
                logger.error("Email/set notCreated: %s", not_created)
                return None
        elif resp[0] == "EmailSubmission/set":
            created = resp[1].get("created", {})
            not_created = resp[1].get("notCreated", {})
            if "sendIt" in created:
                submission_ok = True
            if not_created:
                logger.error("EmailSubmission/set notCreated: %s", not_created)
        elif resp[0] == "error":
            logger.error("JMAP error in send_message: %s", resp[1])
            return None

    if not email_created:
        logger.error("Email/set did not create draft. Full response: %s", result)
        return None

    if not submission_ok:
        logger.error(
            "EmailSubmission/set failed. Email created but not submitted. "
            "Full response: %s", result
        )

    return email_created


# ─── Bulk operations ───


async def bulk_update_messages(
    account_id: str, message_ids: list[str], updates: dict
) -> bool:
    """Update multiple messages in one JMAP call."""
    update_map = {mid: updates for mid in message_ids}
    result = await jmap_call([
        [
            "Email/set",
            {"accountId": account_id, "update": update_map},
            "b0",
        ],
    ])
    for resp in result.get("methodResponses", []):
        if resp[0] == "Email/set":
            return resp[1].get("updated") is not None
    return False


async def bulk_destroy_messages(account_id: str, message_ids: list[str]) -> bool:
    """Delete multiple messages in one JMAP call."""
    result = await jmap_call([
        [
            "Email/set",
            {"accountId": account_id, "destroy": message_ids},
            "d0",
        ],
    ])
    for resp in result.get("methodResponses", []):
        if resp[0] == "Email/set":
            return len(resp[1].get("destroyed", [])) > 0
    return False


# ─── Blob upload ───


async def upload_blob(account_id: str, content: bytes, content_type: str) -> str:
    """Upload a blob (attachment) to Stalwart. Returns blobId."""
    client = _get_client()
    resp = await client.post(
        f"/jmap/upload/{account_id}/",
        content=content,
        headers={"Content-Type": content_type},
    )
    resp.raise_for_status()
    return resp.json()["blobId"]


# ─── Blob download ───


async def download_blob(account_id: str, blob_id: str) -> httpx.Response:
    """Download a blob (attachment) from Stalwart."""
    client = _get_client()
    # Use fixed URL path instead of session downloadUrl (which may use public hostname)
    url = f"/jmap/download/{account_id}/{blob_id}/attachment"
    resp = await client.get(url)
    resp.raise_for_status()
    return resp
