"""Mail API schemas."""

from pydantic import BaseModel


class EmailAddress(BaseModel):
    name: str | None = None
    email: str


class Mailbox(BaseModel):
    id: str
    name: str
    role: str | None = None  # inbox, sent, drafts, trash, junk, archive
    unread_count: int = 0
    total_count: int = 0
    sort_order: int = 0


class MailboxListResponse(BaseModel):
    mailboxes: list[Mailbox]


class Attachment(BaseModel):
    blob_id: str
    name: str | None = None
    type: str | None = None
    size: int = 0


class MessageSummary(BaseModel):
    id: str
    thread_id: str | None = None
    mailbox_ids: list[str] = []
    from_: list[EmailAddress] = []
    to: list[EmailAddress] = []
    subject: str | None = None
    preview: str | None = None
    received_at: str | None = None
    is_unread: bool = False
    is_flagged: bool = False
    has_attachment: bool = False

    model_config = {"populate_by_name": True}


class MessageListResponse(BaseModel):
    messages: list[MessageSummary]
    total: int = 0
    page: int = 0
    limit: int = 50


class MessageDetail(BaseModel):
    id: str
    thread_id: str | None = None
    mailbox_ids: list[str] = []
    from_: list[EmailAddress] = []
    to: list[EmailAddress] = []
    cc: list[EmailAddress] = []
    bcc: list[EmailAddress] = []
    reply_to: list[EmailAddress] = []
    subject: str | None = None
    text_body: str | None = None
    html_body: str | None = None
    preview: str | None = None
    received_at: str | None = None
    is_unread: bool = False
    is_flagged: bool = False
    attachments: list[Attachment] = []

    model_config = {"populate_by_name": True}


class MessageUpdateRequest(BaseModel):
    is_unread: bool | None = None
    is_flagged: bool | None = None
    mailbox_ids: list[str] | None = None  # move to mailbox


class SendMessageRequest(BaseModel):
    to: list[EmailAddress]
    cc: list[EmailAddress] = []
    bcc: list[EmailAddress] = []
    subject: str = ""
    text_body: str = ""
    html_body: str | None = None
    in_reply_to: str | None = None  # message id for threading
    references: list[str] = []
