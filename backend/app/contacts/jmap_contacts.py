"""JMAP Contacts operations for Stalwart Mail Server.

Stalwart v0.15 supports JMAP for Contacts (RFC 9553).
JSContact format is converted to a simplified structure for the frontend.
"""

from app.mail.jmap import jmap_call, resolve_account_id, USING_CONTACTS


def _jscontact_to_contact(item: dict) -> dict:
    """Convert a JSContact card to our Contact format."""
    # Address book ID from addressBookIds
    ab_ids = item.get("addressBookIds") or {}
    address_book_id = next(iter(ab_ids), "")

    # Name
    name_obj = item.get("name") or {}
    full_name = name_obj.get("full", "")
    given = ""
    surname = ""
    components = name_obj.get("components") or []
    for comp in components:
        kind = comp.get("kind", "")
        val = comp.get("value", "")
        if kind == "given":
            given = val
        elif kind == "surname":
            surname = val
    if not full_name and (given or surname):
        full_name = f"{surname}{given}".strip() or f"{given} {surname}".strip()

    # Organization
    org = ""
    orgs = item.get("organizations") or {}
    if orgs:
        first_org = next(iter(orgs.values()), {})
        org = first_org.get("name", "")

    # Emails
    emails = []
    raw_emails = item.get("emails") or {}
    for key, val in raw_emails.items():
        emails.append({
            "type": val.get("contexts", {}).get("work", False) and "work" or
                   val.get("contexts", {}).get("private", False) and "home" or "other",
            "value": val.get("address", ""),
        })

    # Phones
    phones = []
    raw_phones = item.get("phones") or {}
    for key, val in raw_phones.items():
        phones.append({
            "type": val.get("contexts", {}).get("work", False) and "work" or
                   val.get("contexts", {}).get("private", False) and "home" or "other",
            "value": val.get("number", ""),
        })

    # Addresses
    addresses = []
    raw_addrs = item.get("addresses") or {}
    for key, val in raw_addrs.items():
        full_addr = val.get("full", "")
        if not full_addr:
            parts = []
            for comp in val.get("components") or []:
                parts.append(comp.get("value", ""))
            full_addr = " ".join(parts)
        ctx = val.get("contexts") or {}
        addr_type = "work" if ctx.get("work") else "home" if ctx.get("private") else "other"
        addresses.append({"type": addr_type, "value": full_addr})

    # Notes
    notes = ""
    raw_notes = item.get("notes") or {}
    if raw_notes:
        first_note = next(iter(raw_notes.values()), {})
        notes = first_note.get("note", "")

    return {
        "id": item.get("id", ""),
        "address_book_id": address_book_id,
        "name": full_name,
        "first_name": given,
        "last_name": surname,
        "organization": org,
        "emails": emails,
        "phones": phones,
        "addresses": addresses,
        "notes": notes,
        "created": item.get("created"),
        "updated": item.get("updated"),
    }


def _contact_to_jscontact(data: dict) -> dict:
    """Convert our Contact format to JSContact for JMAP set."""
    jsc: dict = {}

    # Name
    name_parts: dict = {}
    components = []
    if data.get("last_name"):
        components.append({"kind": "surname", "value": data["last_name"]})
    if data.get("first_name"):
        components.append({"kind": "given", "value": data["first_name"]})
    if components:
        name_parts["components"] = components
    if data.get("name"):
        name_parts["full"] = data["name"]
    if name_parts:
        jsc["name"] = name_parts

    # Address book
    if data.get("address_book_id"):
        jsc["addressBookIds"] = {data["address_book_id"]: True}

    # Organization
    if data.get("organization"):
        jsc["organizations"] = {"org1": {"name": data["organization"]}}

    # Emails
    if "emails" in data and data["emails"] is not None:
        emails_map = {}
        for i, e in enumerate(data["emails"]):
            ctx = {}
            if e.get("type") == "work":
                ctx["work"] = True
            elif e.get("type") == "home":
                ctx["private"] = True
            emails_map[f"e{i}"] = {"address": e["value"], "contexts": ctx}
        jsc["emails"] = emails_map

    # Phones
    if "phones" in data and data["phones"] is not None:
        phones_map = {}
        for i, p in enumerate(data["phones"]):
            ctx = {}
            if p.get("type") == "work":
                ctx["work"] = True
            elif p.get("type") == "home":
                ctx["private"] = True
            phones_map[f"p{i}"] = {"number": p["value"], "contexts": ctx}
        jsc["phones"] = phones_map

    # Addresses
    if "addresses" in data and data["addresses"] is not None:
        addrs_map = {}
        for i, a in enumerate(data["addresses"]):
            ctx = {}
            if a.get("type") == "work":
                ctx["work"] = True
            elif a.get("type") == "home":
                ctx["private"] = True
            addrs_map[f"a{i}"] = {"full": a["value"], "contexts": ctx}
        jsc["addresses"] = addrs_map

    # Notes
    if data.get("notes"):
        jsc["notes"] = {"n1": {"note": data["notes"]}}

    return jsc


# ─── Address Book CRUD ───


async def get_address_books(account_id: str) -> list[dict]:
    """Get all address books."""
    result = await jmap_call(
        [["AddressBook/get", {"accountId": account_id}, "a0"]],
        using=USING_CONTACTS,
    )
    books = []
    for resp in result.get("methodResponses", []):
        if resp[0] == "AddressBook/get":
            for ab in resp[1].get("list", []):
                books.append({
                    "id": ab.get("id", ""),
                    "name": ab.get("name", ""),
                })
    return books


async def create_address_book(account_id: str, name: str) -> dict | None:
    """Create a new address book."""
    result = await jmap_call(
        [["AddressBook/set", {
            "accountId": account_id,
            "create": {"new": {"name": name}},
        }, "a0"]],
        using=USING_CONTACTS,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "AddressBook/set":
            created = resp[1].get("created", {})
            if "new" in created:
                return {"id": created["new"]["id"], "name": name}
    return None


async def delete_address_book(account_id: str, book_id: str) -> bool:
    """Delete an address book."""
    result = await jmap_call(
        [["AddressBook/set", {
            "accountId": account_id,
            "destroy": [book_id],
        }, "a0"]],
        using=USING_CONTACTS,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "AddressBook/set":
            return book_id in resp[1].get("destroyed", [])
    return False


# ─── Contact CRUD ───


async def get_contacts(
    account_id: str,
    q: str | None = None,
    book_id: str | None = None,
    page: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    """Query contacts with optional search/filter. Returns (contacts, total)."""
    position = page * limit

    jmap_filter: dict = {}
    if q:
        jmap_filter["text"] = q
    if book_id:
        jmap_filter["inAddressBooks"] = [book_id]

    query_params: dict = {
        "accountId": account_id,
        "position": position,
        "limit": limit,
        "calculateTotal": True,
    }
    if jmap_filter:
        query_params["filter"] = jmap_filter

    method_calls = [
        ["ContactCard/query", query_params, "q0"],
        ["ContactCard/get", {
            "accountId": account_id,
            "#ids": {
                "resultOf": "q0",
                "name": "ContactCard/query",
                "path": "/ids",
            },
            "properties": [
                "id", "addressBookIds", "name", "organizations",
                "emails", "phones", "addresses", "notes",
                "created", "updated",
            ],
        }, "g0"],
    ]

    result = await jmap_call(method_calls, using=USING_CONTACTS)

    total = 0
    contacts = []
    for resp in result.get("methodResponses", []):
        if resp[0] == "ContactCard/query":
            total = resp[1].get("total", 0)
        elif resp[0] == "ContactCard/get":
            for item in resp[1].get("list", []):
                contacts.append(_jscontact_to_contact(item))

    return contacts, total


async def get_contact(account_id: str, contact_id: str) -> dict | None:
    """Get a single contact."""
    result = await jmap_call(
        [["ContactCard/get", {
            "accountId": account_id,
            "ids": [contact_id],
            "properties": [
                "id", "addressBookIds", "name", "organizations",
                "emails", "phones", "addresses", "notes",
                "created", "updated",
            ],
        }, "g0"]],
        using=USING_CONTACTS,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "ContactCard/get":
            items = resp[1].get("list", [])
            if items:
                return _jscontact_to_contact(items[0])
    return None


async def create_contact(account_id: str, data: dict) -> dict | None:
    """Create a contact."""
    jsc = _contact_to_jscontact(data)
    result = await jmap_call(
        [["ContactCard/set", {
            "accountId": account_id,
            "create": {"new": jsc},
        }, "c0"]],
        using=USING_CONTACTS,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "ContactCard/set":
            created = resp[1].get("created", {})
            if "new" in created:
                return {"id": created["new"]["id"], **data}
    return None


async def update_contact(account_id: str, contact_id: str, data: dict) -> bool:
    """Update a contact."""
    jsc = _contact_to_jscontact(data)
    if not jsc:
        return False

    result = await jmap_call(
        [["ContactCard/set", {
            "accountId": account_id,
            "update": {contact_id: jsc},
        }, "u0"]],
        using=USING_CONTACTS,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "ContactCard/set":
            return resp[1].get("updated") is not None
    return False


async def delete_contact(account_id: str, contact_id: str) -> bool:
    """Delete a contact."""
    result = await jmap_call(
        [["ContactCard/set", {
            "accountId": account_id,
            "destroy": [contact_id],
        }, "d0"]],
        using=USING_CONTACTS,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "ContactCard/set":
            return contact_id in resp[1].get("destroyed", [])
    return False
