"""Contacts API schemas."""

from pydantic import BaseModel


class TypedValue(BaseModel):
    type: str  # home, work, other
    value: str


class AddressBook(BaseModel):
    id: str
    name: str


class Contact(BaseModel):
    id: str
    address_book_id: str
    name: str
    first_name: str | None = None
    last_name: str | None = None
    organization: str | None = None
    emails: list[TypedValue] = []
    phones: list[TypedValue] = []
    addresses: list[TypedValue] = []
    notes: str | None = None
    created: str | None = None
    updated: str | None = None


class ContactCreate(BaseModel):
    address_book_id: str
    name: str
    first_name: str | None = None
    last_name: str | None = None
    organization: str | None = None
    emails: list[TypedValue] = []
    phones: list[TypedValue] = []
    addresses: list[TypedValue] = []
    notes: str | None = None


class ContactUpdate(BaseModel):
    address_book_id: str | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    organization: str | None = None
    emails: list[TypedValue] | None = None
    phones: list[TypedValue] | None = None
    addresses: list[TypedValue] | None = None
    notes: str | None = None


class AddressBookCreate(BaseModel):
    name: str


class AddressBookListResponse(BaseModel):
    address_books: list[AddressBook]


class ContactListResponse(BaseModel):
    contacts: list[Contact]
    total: int = 0


class SyncInfo(BaseModel):
    carddav_url: str
    description: str
