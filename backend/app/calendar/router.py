"""Calendar API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.deps import get_current_user
from app.db.models import User
from app.mail.jmap import resolve_account_id
from app.calendar import jmap_calendar
from app.calendar.schemas import (
    CalendarInfo,
    CalendarCreate,
    CalendarUpdate,
    CalendarEvent,
    EventCreate,
    EventUpdate,
    CalendarListResponse,
    EventListResponse,
    CalendarShareRequest,
    CalendarShareInfo,
    SyncInfo,
)

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


async def _get_account_id(user: User) -> str:
    if not user.email:
        raise HTTPException(status_code=400, detail="User has no email address")
    account_id = await resolve_account_id(user.email)
    if not account_id:
        raise HTTPException(status_code=404, detail="Mail account not found")
    return account_id


# ─── Calendars ───


@router.get("/calendars", response_model=CalendarListResponse)
async def list_calendars(user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    calendars = await jmap_calendar.get_calendars(account_id)
    return {"calendars": [CalendarInfo(**c) for c in calendars]}


@router.post("/calendars", response_model=CalendarInfo)
async def create_calendar(body: CalendarCreate, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    result = await jmap_calendar.create_calendar(account_id, body.name, body.color)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create calendar")
    return CalendarInfo(
        id=result["id"],
        name=result["name"],
        color=result.get("color"),
    )


@router.patch("/calendars/{calendar_id}", response_model=dict)
async def update_calendar(
    calendar_id: str,
    body: CalendarUpdate,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    ok = await jmap_calendar.update_calendar(account_id, calendar_id, updates)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update calendar")
    return {"ok": True}


@router.delete("/calendars/{calendar_id}", response_model=dict)
async def delete_calendar(calendar_id: str, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    ok = await jmap_calendar.delete_calendar(account_id, calendar_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to delete calendar")
    return {"ok": True}


# ─── Calendar Sharing ───


@router.get("/calendars/{calendar_id}/shares", response_model=list[CalendarShareInfo])
async def list_calendar_shares(
    calendar_id: str,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    shares = await jmap_calendar.get_calendar_shares(account_id, calendar_id)
    return [CalendarShareInfo(**s) for s in shares]


@router.post("/calendars/{calendar_id}/shares", response_model=dict)
async def set_calendar_shares(
    calendar_id: str,
    body: CalendarShareRequest,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    shares = [s.model_dump() for s in body.shares]
    ok = await jmap_calendar.share_calendar(account_id, calendar_id, shares)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to share calendar")
    return {"ok": True}


@router.delete("/calendars/{calendar_id}/shares/{email}", response_model=dict)
async def remove_calendar_share(
    calendar_id: str,
    email: str,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    ok = await jmap_calendar.unshare_calendar(account_id, calendar_id, email)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to remove share")
    return {"ok": True}


# ─── Events ───


@router.get("/events", response_model=EventListResponse)
async def list_events(
    start: str | None = Query(None, description="ISO 8601 start date"),
    end: str | None = Query(None, description="ISO 8601 end date"),
    calendar_id: str | None = Query(None),
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    events = await jmap_calendar.get_events(account_id, start, end, calendar_id)
    return {"events": [CalendarEvent(**e) for e in events]}


@router.get("/events/{event_id}", response_model=CalendarEvent)
async def get_event(event_id: str, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    event = await jmap_calendar.get_event(account_id, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return CalendarEvent(**event)


@router.post("/events", response_model=CalendarEvent)
async def create_event(body: EventCreate, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    result = await jmap_calendar.create_event(account_id, body.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create event")
    return CalendarEvent(**result)


@router.patch("/events/{event_id}", response_model=dict)
async def update_event(
    event_id: str,
    body: EventUpdate,
    user: User = Depends(get_current_user),
):
    account_id = await _get_account_id(user)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    ok = await jmap_calendar.update_event(account_id, event_id, updates)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update event")
    return {"ok": True}


@router.delete("/events/{event_id}", response_model=dict)
async def delete_event(event_id: str, user: User = Depends(get_current_user)):
    account_id = await _get_account_id(user)
    ok = await jmap_calendar.delete_event(account_id, event_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to delete event")
    return {"ok": True}


# ─── Sync Info ───


@router.get("/sync-info", response_model=SyncInfo)
async def sync_info(user: User = Depends(get_current_user)):
    return SyncInfo(
        caldav_url=f"https://mail.namgun.or.kr/dav/calendars/{user.email}/",
        description="Thunderbird, iOS, Android 등에서 CalDAV로 동기화할 수 있습니다.",
    )
