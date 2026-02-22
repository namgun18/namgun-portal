"""Calendar API schemas."""

from pydantic import BaseModel


class CalendarInfo(BaseModel):
    id: str
    name: str
    color: str | None = None
    is_visible: bool = True
    sort_order: int = 0


class CalendarCreate(BaseModel):
    name: str
    color: str | None = None


class CalendarUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    is_visible: bool | None = None


class CalendarEvent(BaseModel):
    id: str
    calendar_id: str
    title: str
    description: str | None = None
    location: str | None = None
    start: str  # ISO 8601
    end: str  # ISO 8601
    all_day: bool = False
    color: str | None = None  # inherited from calendar
    status: str | None = None  # confirmed, tentative, cancelled
    created: str | None = None
    updated: str | None = None


class EventCreate(BaseModel):
    calendar_id: str
    title: str
    description: str | None = None
    location: str | None = None
    start: str
    end: str
    all_day: bool = False


class EventUpdate(BaseModel):
    calendar_id: str | None = None
    title: str | None = None
    description: str | None = None
    location: str | None = None
    start: str | None = None
    end: str | None = None
    all_day: bool | None = None


class CalendarSharee(BaseModel):
    email: str
    can_write: bool = False


class CalendarShareRequest(BaseModel):
    shares: list[CalendarSharee]


class CalendarShareInfo(BaseModel):
    email: str
    can_write: bool


class CalendarListResponse(BaseModel):
    calendars: list[CalendarInfo]


class EventListResponse(BaseModel):
    events: list[CalendarEvent]


class SyncInfo(BaseModel):
    caldav_url: str
    description: str
