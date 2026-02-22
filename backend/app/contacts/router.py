"""Contacts API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.deps import get_current_user
from app.db.models import User
from app.mail.jmap import resolve_account_id
from app.contacts import jmap_contacts
from app.contacts.schemas import (
    AddressBook,
    AddressBookCreate,
    AddressBookListResponse,
    Contact,
    ContactCreate,
    ContactUpdate,
    ContactListResponse,
    SyncInfo,
)

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


async def _get_account_id(user: User) -> str:
    if not user.email:
        raise HTTPException(status_code=400, detail="User has no email address")
    account_id = await resolve_account_id(user.email)
    if not account_id:
        raise HTTPException(status_code=404, detail="Mail account not found")
    return account_id


# ─── Address Books ───


@router.get("/address-books", response_model=AddressBookListResponse)
async def list_address_books(user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    books = await jmap_contacts.get_address_books(account_id)
    return {"address_books": [AddressBook(**b) for b in books]}


@router.post("/address-books", response_model=AddressBook)
async def create_address_book(body: AddressBookCreate, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    result = await jmap_contacts.create_address_book(account_id, body.name)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create address book")
    return AddressBook(**result)


@router.delete("/address-books/{book_id}", response_model=dict)
async def delete_address_book(book_id: str, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    ok = await jmap_contacts.delete_address_book(account_id, book_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to delete address book")
    return {"ok": True}


# ─── Contacts ───


@router.get("/", response_model=ContactListResponse)
async def list_contacts(
    q: str | None = Query(None),
    book_id: str | None = Query(None),
    page: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    contacts, total = await jmap_contacts.get_contacts(account_id, q, book_id, page, limit)
    return {"contacts": [Contact(**c) for c in contacts], "total": total}


@router.get("/sync-info", response_model=SyncInfo)
async def sync_info(user: User = Depends(get_current_user)):
    return SyncInfo(
        carddav_url=f"https://mail.namgun.or.kr/dav/addressbooks/{user.email}/",
        description="Thunderbird, iOS, Android 등에서 CardDAV로 동기화할 수 있습니다.",
    )


@router.get("/{contact_id}", response_model=Contact)
async def get_contact(contact_id: str, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    contact = await jmap_contacts.get_contact(account_id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return Contact(**contact)


@router.post("/", response_model=Contact)
async def create_contact(body: ContactCreate, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    data = body.model_dump()
    # Convert TypedValue objects to dicts
    for field in ["emails", "phones", "addresses"]:
        if data.get(field):
            data[field] = [{"type": v["type"], "value": v["value"]} for v in data[field]]
    result = await jmap_contacts.create_contact(account_id, data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create contact")
    return Contact(**result)


@router.patch("/{contact_id}", response_model=dict)
async def update_contact(
    contact_id: str,
    body: ContactUpdate,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    data = body.model_dump(exclude_none=True)
    # Convert TypedValue objects to dicts
    for field in ["emails", "phones", "addresses"]:
        if data.get(field):
            data[field] = [{"type": v["type"], "value": v["value"]} for v in data[field]]
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    ok = await jmap_contacts.update_contact(account_id, contact_id, data)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update contact")
    return {"ok": True}


@router.delete("/{contact_id}", response_model=dict)
async def delete_contact(contact_id: str, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    ok = await jmap_contacts.delete_contact(account_id, contact_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to delete contact")
    return {"ok": True}
