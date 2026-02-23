"""Mail API endpoints."""

from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.models import MailSignature, User
from app.db.session import get_db
from app.mail import jmap
from app.mail.schemas import (
    Mailbox,
    MailboxListResponse,
    MessageDetail,
    MessageListResponse,
    MessageSummary,
    MessageUpdateRequest,
    SendMessageRequest,
    BulkActionRequest,
    SignatureCreate,
    SignatureUpdate,
    SignatureResponse,
    EmailAddress,
    Attachment,
)

router = APIRouter(prefix="/api/mail", tags=["mail"])

# Mailbox role sort priority
ROLE_ORDER = {
    "inbox": 0,
    "drafts": 1,
    "sent": 2,
    "junk": 3,
    "trash": 4,
    "archive": 5,
}


# ─── Helpers ───


def _parse_addr(raw: dict | None) -> EmailAddress:
    if not raw:
        return EmailAddress(email="")
    return EmailAddress(name=raw.get("name"), email=raw.get("email", ""))


def _parse_addrs(raw: list | None) -> list[EmailAddress]:
    if not raw:
        return []
    return [_parse_addr(a) for a in raw]


def _parse_keywords(keywords: dict | None) -> tuple[bool, bool]:
    """Returns (is_unread, is_flagged)."""
    if not keywords:
        return True, False
    is_unread = "$seen" not in keywords
    is_flagged = "$flagged" in keywords
    return is_unread, is_flagged


async def _get_account_id(user: User) -> str:
    """Resolve user email to JMAP account ID."""
    if not user.email:
        raise HTTPException(status_code=400, detail="User has no email address")
    account_id = await jmap.resolve_account_id(user.email)
    if not account_id:
        raise HTTPException(status_code=404, detail="Mail account not found")
    return account_id


# ─── Mailboxes ───


@router.get("/mailboxes", response_model=MailboxListResponse)
async def list_mailboxes(user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    raw_mailboxes = await jmap.get_mailboxes(account_id)

    mailboxes = []
    for mb in raw_mailboxes:
        role = mb.get("role")
        sort_order = ROLE_ORDER.get(role, 99) if role else 99
        mailboxes.append(Mailbox(
            id=mb["id"],
            name=mb.get("name", ""),
            role=role,
            unread_count=mb.get("unreadEmails", 0),
            total_count=mb.get("totalEmails", 0),
            sort_order=sort_order,
        ))

    mailboxes.sort(key=lambda m: (m.sort_order, m.name))
    return MailboxListResponse(mailboxes=mailboxes)


# ─── Messages list ───


@router.get("/messages", response_model=MessageListResponse)
async def list_messages(
    mailbox_id: str = Query(...),
    page: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    q: str | None = Query(None),
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    raw_messages, total = await jmap.get_messages(account_id, mailbox_id, page, limit, query=q)

    messages = []
    for msg in raw_messages:
        is_unread, is_flagged = _parse_keywords(msg.get("keywords"))
        messages.append(MessageSummary(
            id=msg["id"],
            thread_id=msg.get("threadId"),
            mailbox_ids=list(msg.get("mailboxIds", {}).keys()),
            from_=_parse_addrs(msg.get("from")),
            to=_parse_addrs(msg.get("to")),
            subject=msg.get("subject"),
            preview=msg.get("preview"),
            received_at=msg.get("receivedAt"),
            is_unread=is_unread,
            is_flagged=is_flagged,
            has_attachment=msg.get("hasAttachment", False),
        ))

    return MessageListResponse(messages=messages, total=total, page=page, limit=limit)


# ─── Message detail ───


@router.get("/messages/{message_id}", response_model=MessageDetail)
async def get_message(
    message_id: str,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    msg = await jmap.get_message(account_id, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Auto mark as read
    keywords = msg.get("keywords", {})
    if "$seen" not in keywords:
        keywords["$seen"] = True
        await jmap.update_message(account_id, message_id, {"keywords": keywords})

    is_unread, is_flagged = _parse_keywords(msg.get("keywords"))

    # Extract body text
    body_values = msg.get("bodyValues", {})
    text_body = None
    html_body = None

    for part in msg.get("textBody", []):
        part_id = part.get("partId")
        if part_id and part_id in body_values:
            text_body = body_values[part_id].get("value", "")
            break

    for part in msg.get("htmlBody", []):
        part_id = part.get("partId")
        if part_id and part_id in body_values:
            html_body = body_values[part_id].get("value", "")
            break

    # Parse attachments
    attachments = []
    for att in msg.get("attachments", []):
        attachments.append(Attachment(
            blob_id=att.get("blobId", ""),
            name=att.get("name"),
            type=att.get("type"),
            size=att.get("size", 0),
        ))

    return MessageDetail(
        id=msg["id"],
        thread_id=msg.get("threadId"),
        mailbox_ids=list(msg.get("mailboxIds", {}).keys()),
        from_=_parse_addrs(msg.get("from")),
        to=_parse_addrs(msg.get("to")),
        cc=_parse_addrs(msg.get("cc")),
        bcc=_parse_addrs(msg.get("bcc")),
        reply_to=_parse_addrs(msg.get("replyTo")),
        subject=msg.get("subject"),
        text_body=text_body,
        html_body=html_body,
        preview=msg.get("preview"),
        received_at=msg.get("receivedAt"),
        is_unread=is_unread,
        is_flagged=is_flagged,
        attachments=attachments,
    )


# ─── Update message (read/star/move) ───


@router.patch("/messages/{message_id}")
async def update_message(
    message_id: str,
    body: MessageUpdateRequest,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)

    # Fetch current message to get keywords
    msg = await jmap.get_message(account_id, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    updates: dict = {}
    keywords = dict(msg.get("keywords", {}))

    if body.is_unread is not None:
        if body.is_unread:
            keywords.pop("$seen", None)
        else:
            keywords["$seen"] = True
        updates["keywords"] = keywords

    if body.is_flagged is not None:
        if body.is_flagged:
            keywords["$flagged"] = True
        else:
            keywords.pop("$flagged", None)
        updates["keywords"] = keywords

    if body.mailbox_ids is not None:
        updates["mailboxIds"] = {mid: True for mid in body.mailbox_ids}

    if not updates:
        return {"ok": True}

    ok = await jmap.update_message(account_id, message_id, updates)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update message")
    return {"ok": True}


# ─── Delete message ───


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)

    # Check if already in trash → permanent delete
    msg = await jmap.get_message(account_id, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    mailbox_ids = list(msg.get("mailboxIds", {}).keys())

    # Find trash mailbox
    mailboxes = await jmap.get_mailboxes(account_id)
    trash_id = None
    for mb in mailboxes:
        if mb.get("role") == "trash":
            trash_id = mb["id"]
            break

    is_in_trash = trash_id and trash_id in mailbox_ids

    if is_in_trash:
        # Permanent delete
        ok = await jmap.destroy_message(account_id, message_id)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to delete message")
        return {"ok": True, "permanent": True}
    elif trash_id:
        # Move to trash
        ok = await jmap.update_message(
            account_id, message_id,
            {"mailboxIds": {trash_id: True}},
        )
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to move to trash")
        return {"ok": True, "permanent": False}
    else:
        # No trash folder, permanent delete
        ok = await jmap.destroy_message(account_id, message_id)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to delete message")
        return {"ok": True, "permanent": True}


# ─── Send message ───


@router.post("/send")
async def send_message(
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)

    # Find sent mailbox
    mailboxes = await jmap.get_mailboxes(account_id)
    sent_id = None
    for mb in mailboxes:
        if mb.get("role") == "sent":
            sent_id = mb["id"]
            break

    mailbox_ids = {}
    if sent_id:
        mailbox_ids[sent_id] = True

    from_addr = {"name": user.display_name or user.username, "email": user.email}

    # Convert attachments if provided
    att_list = None
    if body.attachments:
        att_list = [a.model_dump() for a in body.attachments]

    result = await jmap.send_message(
        account_id=account_id,
        from_addr=from_addr,
        to=[a.model_dump() for a in body.to],
        cc=[a.model_dump() for a in body.cc],
        bcc=[a.model_dump() for a in body.bcc],
        subject=body.subject,
        text_body=body.text_body,
        html_body=body.html_body,
        in_reply_to=body.in_reply_to,
        references=body.references or None,
        mailbox_ids=mailbox_ids or None,
        attachments=att_list,
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to send message")

    return {"ok": True, "id": result.get("id")}


# ─── Bulk operations ───


@router.post("/bulk")
async def bulk_action(
    body: BulkActionRequest,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)

    if not body.message_ids:
        raise HTTPException(status_code=400, detail="메시지를 선택해주세요")

    if body.action == "read":
        ok = await jmap.bulk_update_messages(
            account_id, body.message_ids, {"keywords/$seen": True}
        )
    elif body.action == "unread":
        ok = await jmap.bulk_update_messages(
            account_id, body.message_ids, {"keywords/$seen": None}
        )
    elif body.action == "star":
        ok = await jmap.bulk_update_messages(
            account_id, body.message_ids, {"keywords/$flagged": True}
        )
    elif body.action == "unstar":
        ok = await jmap.bulk_update_messages(
            account_id, body.message_ids, {"keywords/$flagged": None}
        )
    elif body.action == "delete":
        # Move to trash (or permanent delete if already in trash)
        mailboxes = await jmap.get_mailboxes(account_id)
        trash_id = None
        for mb in mailboxes:
            if mb.get("role") == "trash":
                trash_id = mb["id"]
                break
        if trash_id:
            ok = await jmap.bulk_update_messages(
                account_id, body.message_ids, {"mailboxIds": {trash_id: True}}
            )
        else:
            ok = await jmap.bulk_destroy_messages(account_id, body.message_ids)
    elif body.action == "move":
        if not body.mailbox_id:
            raise HTTPException(status_code=400, detail="이동할 메일함을 지정해주세요")
        ok = await jmap.bulk_update_messages(
            account_id, body.message_ids, {"mailboxIds": {body.mailbox_id: True}}
        )
    else:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 작업: {body.action}")

    if not ok:
        raise HTTPException(status_code=500, detail="일괄 작업 처리에 실패했습니다")

    return {"ok": True, "count": len(body.message_ids)}


# ─── Upload attachment blob ───


@router.post("/upload")
async def upload_attachment(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    content = await file.read()

    # 25MB limit
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="파일 크기는 25MB를 초과할 수 없습니다")

    content_type = file.content_type or "application/octet-stream"
    blob_id = await jmap.upload_blob(account_id, content, content_type)

    return {
        "blobId": blob_id,
        "type": content_type,
        "name": file.filename or "attachment",
        "size": len(content),
    }


# ─── Blob download (attachment proxy) ───


@router.get("/blob/{blob_id}")
async def download_blob(
    blob_id: str,
    name: str = Query("attachment"),
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    try:
        resp = await jmap.download_blob(account_id, blob_id)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Mail server timeout")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Blob not found")
        raise HTTPException(status_code=502, detail="Mail server error")
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to download blob")

    content_type = resp.headers.get("content-type", "application/octet-stream")
    # RFC 5987 encoded filename to prevent header injection
    safe_name = name.replace('"', '').replace('\n', '').replace('\r', '')
    encoded_name = quote(safe_name, safe='')
    return Response(
        content=resp.content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{encoded_name}",
        },
    )


# ─── Signatures CRUD ───


@router.get("/signatures", response_model=list[SignatureResponse])
async def list_signatures(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MailSignature)
        .where(MailSignature.user_id == user.id)
        .order_by(MailSignature.created_at)
    )
    sigs = result.scalars().all()
    return [
        SignatureResponse(
            id=s.id,
            name=s.name,
            html_content=s.html_content,
            is_default=s.is_default,
            created_at=s.created_at.isoformat(),
        )
        for s in sigs
    ]


@router.get("/signatures/default", response_model=SignatureResponse | None)
async def get_default_signature(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MailSignature).where(
            MailSignature.user_id == user.id, MailSignature.is_default == True
        )
    )
    sig = result.scalar_one_or_none()
    if not sig:
        return None
    return SignatureResponse(
        id=sig.id,
        name=sig.name,
        html_content=sig.html_content,
        is_default=sig.is_default,
        created_at=sig.created_at.isoformat(),
    )


@router.post("/signatures", response_model=SignatureResponse, status_code=201)
async def create_signature(
    body: SignatureCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # If setting as default, unset other defaults
    if body.is_default:
        result = await db.execute(
            select(MailSignature).where(
                MailSignature.user_id == user.id, MailSignature.is_default == True
            )
        )
        for s in result.scalars():
            s.is_default = False

    sig = MailSignature(
        user_id=user.id,
        name=body.name,
        html_content=body.html_content,
        is_default=body.is_default,
    )
    db.add(sig)
    await db.commit()
    await db.refresh(sig)
    return SignatureResponse(
        id=sig.id,
        name=sig.name,
        html_content=sig.html_content,
        is_default=sig.is_default,
        created_at=sig.created_at.isoformat(),
    )


@router.patch("/signatures/{sig_id}", response_model=SignatureResponse)
async def update_signature(
    sig_id: str,
    body: SignatureUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sig = await db.get(MailSignature, sig_id)
    if not sig or sig.user_id != user.id:
        raise HTTPException(status_code=404, detail="서명을 찾을 수 없습니다")

    if body.name is not None:
        sig.name = body.name
    if body.html_content is not None:
        sig.html_content = body.html_content
    if body.is_default is not None:
        if body.is_default:
            # Unset other defaults
            result = await db.execute(
                select(MailSignature).where(
                    MailSignature.user_id == user.id,
                    MailSignature.is_default == True,
                    MailSignature.id != sig_id,
                )
            )
            for s in result.scalars():
                s.is_default = False
        sig.is_default = body.is_default

    await db.commit()
    await db.refresh(sig)
    return SignatureResponse(
        id=sig.id,
        name=sig.name,
        html_content=sig.html_content,
        is_default=sig.is_default,
        created_at=sig.created_at.isoformat(),
    )


@router.delete("/signatures/{sig_id}")
async def delete_signature(
    sig_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sig = await db.get(MailSignature, sig_id)
    if not sig or sig.user_id != user.id:
        raise HTTPException(status_code=404, detail="서명을 찾을 수 없습니다")
    await db.delete(sig)
    await db.commit()
    return {"ok": True}
