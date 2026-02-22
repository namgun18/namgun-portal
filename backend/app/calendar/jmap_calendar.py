"""JMAP Calendar operations for Stalwart Mail Server.

Stalwart v0.15 supports JMAP for Calendars (RFC 8984).
JSCalendar uses `start` + `duration` format; we convert to start/end for the frontend.
"""

import re
from datetime import datetime, timedelta

from app.mail.jmap import jmap_call, resolve_account_id, USING_CALENDAR


def _parse_duration(dur: str) -> timedelta:
    """Parse ISO 8601 duration (e.g. PT1H30M, P1D) into timedelta."""
    if not dur:
        return timedelta(hours=1)  # default 1 hour

    pattern = re.compile(
        r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?"
    )
    m = pattern.match(dur)
    if not m:
        return timedelta(hours=1)

    days = int(m.group(1) or 0)
    hours = int(m.group(2) or 0)
    minutes = int(m.group(3) or 0)
    seconds = int(m.group(4) or 0)
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def _make_duration(start_iso: str, end_iso: str) -> str:
    """Convert start/end ISO strings to ISO 8601 duration."""
    try:
        fmt1 = "%Y-%m-%dT%H:%M:%S"
        fmt2 = "%Y-%m-%d"
        for fmt in [fmt1, fmt2]:
            try:
                s = datetime.strptime(start_iso[:19], fmt)
                e = datetime.strptime(end_iso[:19], fmt)
                break
            except ValueError:
                continue
        else:
            return "PT1H"

        delta = e - s
        total_seconds = int(delta.total_seconds())
        if total_seconds <= 0:
            return "PT1H"

        days = total_seconds // 86400
        remaining = total_seconds % 86400
        hours = remaining // 3600
        remaining %= 3600
        minutes = remaining // 60

        parts = ["P"]
        if days:
            parts.append(f"{days}D")
        time_parts = []
        if hours:
            time_parts.append(f"{hours}H")
        if minutes:
            time_parts.append(f"{minutes}M")
        if time_parts:
            parts.append("T" + "".join(time_parts))
        elif not days:
            parts.append("T1H")

        return "".join(parts)
    except Exception:
        return "PT1H"


def _jscal_to_event(item: dict, calendars: dict | None = None) -> dict:
    """Convert a JSCalendar object to our CalendarEvent format."""
    # Extract calendar_id from calendarIds
    calendar_ids = item.get("calendarIds") or {}
    calendar_id = next(iter(calendar_ids), "")

    # Compute end from start + duration
    start = item.get("start", "")
    duration = item.get("duration", "PT1H")
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = start_dt + _parse_duration(duration)
        end = end_dt.isoformat()
    except Exception:
        end = start

    # Extract location name
    locations = item.get("locations") or {}
    location = ""
    if locations:
        first_loc = next(iter(locations.values()), {})
        location = first_loc.get("name", "")

    # Calendar color
    color = None
    if calendars and calendar_id in calendars:
        color = calendars[calendar_id].get("color")

    # showWithoutTime → all_day
    show_without_time = item.get("showWithoutTime", False)

    return {
        "id": item.get("id", ""),
        "calendar_id": calendar_id,
        "title": item.get("title", ""),
        "description": item.get("description", ""),
        "location": location,
        "start": start,
        "end": end,
        "all_day": show_without_time,
        "color": color,
        "status": item.get("status", "confirmed"),
        "created": item.get("created"),
        "updated": item.get("updated"),
    }


# ─── Calendar CRUD ───


async def get_calendars(account_id: str) -> list[dict]:
    """Get all calendars for an account."""
    result = await jmap_call(
        [["Calendar/get", {"accountId": account_id}, "c0"]],
        using=USING_CALENDAR,
    )
    calendars = []
    for resp in result.get("methodResponses", []):
        if resp[0] == "Calendar/get":
            for cal in resp[1].get("list", []):
                calendars.append({
                    "id": cal.get("id", ""),
                    "name": cal.get("name", ""),
                    "color": cal.get("color"),
                    "is_visible": cal.get("isVisible", True),
                    "sort_order": cal.get("sortOrder", 0),
                })
    return calendars


async def create_calendar(account_id: str, name: str, color: str | None = None) -> dict | None:
    """Create a new calendar."""
    props: dict = {"name": name}
    if color:
        props["color"] = color

    result = await jmap_call(
        [["Calendar/set", {
            "accountId": account_id,
            "create": {"new": props},
        }, "c0"]],
        using=USING_CALENDAR,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "Calendar/set":
            created = resp[1].get("created", {})
            if "new" in created:
                return {"id": created["new"]["id"], "name": name, "color": color}
    return None


async def update_calendar(account_id: str, calendar_id: str, updates: dict) -> bool:
    """Update calendar properties."""
    jmap_updates = {}
    if "name" in updates and updates["name"] is not None:
        jmap_updates["name"] = updates["name"]
    if "color" in updates and updates["color"] is not None:
        jmap_updates["color"] = updates["color"]
    if "is_visible" in updates and updates["is_visible"] is not None:
        jmap_updates["isVisible"] = updates["is_visible"]

    if not jmap_updates:
        return False

    result = await jmap_call(
        [["Calendar/set", {
            "accountId": account_id,
            "update": {calendar_id: jmap_updates},
        }, "c0"]],
        using=USING_CALENDAR,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "Calendar/set":
            return resp[1].get("updated") is not None
    return False


async def delete_calendar(account_id: str, calendar_id: str) -> bool:
    """Delete a calendar."""
    result = await jmap_call(
        [["Calendar/set", {
            "accountId": account_id,
            "destroy": [calendar_id],
        }, "c0"]],
        using=USING_CALENDAR,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "Calendar/set":
            return calendar_id in resp[1].get("destroyed", [])
    return False


# ─── Event CRUD ───


async def get_events(
    account_id: str,
    start: str | None = None,
    end: str | None = None,
    calendar_id: str | None = None,
) -> list[dict]:
    """Query calendar events, optionally filtering by date range and calendar."""
    # First get calendars for color info
    calendars_list = await get_calendars(account_id)
    calendars_map = {c["id"]: c for c in calendars_list}

    # Build filter
    jmap_filter: dict = {}
    if start:
        jmap_filter["after"] = start
    if end:
        jmap_filter["before"] = end
    if calendar_id:
        jmap_filter["inCalendars"] = [calendar_id]

    query_params: dict = {
        "accountId": account_id,
        "sort": [{"property": "start", "isAscending": True}],
        "limit": 500,
    }
    if jmap_filter:
        query_params["filter"] = jmap_filter

    method_calls = [
        ["CalendarEvent/query", query_params, "q0"],
        ["CalendarEvent/get", {
            "accountId": account_id,
            "#ids": {
                "resultOf": "q0",
                "name": "CalendarEvent/query",
                "path": "/ids",
            },
            "properties": [
                "id", "calendarIds", "title", "description",
                "start", "duration", "locations", "showWithoutTime",
                "status", "created", "updated",
            ],
        }, "g0"],
    ]

    result = await jmap_call(method_calls, using=USING_CALENDAR)

    events = []
    for resp in result.get("methodResponses", []):
        if resp[0] == "CalendarEvent/get":
            for item in resp[1].get("list", []):
                events.append(_jscal_to_event(item, calendars_map))
    return events


async def get_event(account_id: str, event_id: str) -> dict | None:
    """Get a single event by ID."""
    calendars_list = await get_calendars(account_id)
    calendars_map = {c["id"]: c for c in calendars_list}

    result = await jmap_call(
        [["CalendarEvent/get", {
            "accountId": account_id,
            "ids": [event_id],
            "properties": [
                "id", "calendarIds", "title", "description",
                "start", "duration", "locations", "showWithoutTime",
                "status", "created", "updated",
            ],
        }, "g0"]],
        using=USING_CALENDAR,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "CalendarEvent/get":
            items = resp[1].get("list", [])
            if items:
                return _jscal_to_event(items[0], calendars_map)
    return None


async def create_event(account_id: str, data: dict) -> dict | None:
    """Create a calendar event."""
    duration = _make_duration(data["start"], data["end"])

    jscal: dict = {
        "calendarIds": {data["calendar_id"]: True},
        "title": data.get("title", ""),
        "start": data["start"],
        "duration": duration,
    }
    if data.get("description"):
        jscal["description"] = data["description"]
    if data.get("location"):
        jscal["locations"] = {"loc1": {"name": data["location"]}}
    if data.get("all_day"):
        jscal["showWithoutTime"] = True

    result = await jmap_call(
        [["CalendarEvent/set", {
            "accountId": account_id,
            "create": {"new": jscal},
        }, "c0"]],
        using=USING_CALENDAR,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "CalendarEvent/set":
            created = resp[1].get("created", {})
            if "new" in created:
                return {"id": created["new"]["id"], **data}
    return None


async def update_event(account_id: str, event_id: str, data: dict) -> bool:
    """Update a calendar event."""
    jscal_updates: dict = {}

    if "title" in data and data["title"] is not None:
        jscal_updates["title"] = data["title"]
    if "description" in data:
        jscal_updates["description"] = data.get("description") or ""
    if "calendar_id" in data and data["calendar_id"] is not None:
        jscal_updates["calendarIds"] = {data["calendar_id"]: True}
    if "start" in data and data["start"] is not None:
        jscal_updates["start"] = data["start"]
    if "start" in data and "end" in data and data["start"] and data["end"]:
        jscal_updates["duration"] = _make_duration(data["start"], data["end"])
    if "location" in data:
        loc = data.get("location")
        jscal_updates["locations"] = {"loc1": {"name": loc}} if loc else {}
    if "all_day" in data and data["all_day"] is not None:
        jscal_updates["showWithoutTime"] = data["all_day"]

    if not jscal_updates:
        return False

    result = await jmap_call(
        [["CalendarEvent/set", {
            "accountId": account_id,
            "update": {event_id: jscal_updates},
        }, "u0"]],
        using=USING_CALENDAR,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "CalendarEvent/set":
            return resp[1].get("updated") is not None
    return False


async def delete_event(account_id: str, event_id: str) -> bool:
    """Delete a calendar event."""
    result = await jmap_call(
        [["CalendarEvent/set", {
            "accountId": account_id,
            "destroy": [event_id],
        }, "d0"]],
        using=USING_CALENDAR,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "CalendarEvent/set":
            return event_id in resp[1].get("destroyed", [])
    return False


# ─── Calendar Sharing ───


async def get_calendar_shares(account_id: str, calendar_id: str) -> list[dict]:
    """Get share list for a calendar using the shareWith property."""
    result = await jmap_call(
        [["Calendar/get", {
            "accountId": account_id,
            "ids": [calendar_id],
            "properties": ["id", "shareWith"],
        }, "s0"]],
        using=USING_CALENDAR,
    )
    shares = []
    for resp in result.get("methodResponses", []):
        if resp[0] == "Calendar/get":
            items = resp[1].get("list", [])
            if items:
                share_with = items[0].get("shareWith") or {}
                for email, perms in share_with.items():
                    can_write = perms.get("mayWriteAll", False) or perms.get("mayWrite", False)
                    shares.append({"email": email, "can_write": can_write})
    return shares


async def share_calendar(
    account_id: str,
    calendar_id: str,
    shares: list[dict],
) -> bool:
    """Set shares on a calendar. Each share: {email, can_write}."""
    # Build shareWith object
    share_with: dict = {}
    for s in shares:
        email = s["email"]
        can_write = s.get("can_write", False)
        share_with[email] = {
            "mayReadFreeBusy": True,
            "mayReadItems": True,
            "mayWriteAll": can_write,
            "mayUpdatePrivate": can_write,
            "mayRSVP": True,
        }

    result = await jmap_call(
        [["Calendar/set", {
            "accountId": account_id,
            "update": {calendar_id: {"shareWith": share_with}},
        }, "s0"]],
        using=USING_CALENDAR,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "Calendar/set":
            return resp[1].get("updated") is not None
    return False


async def unshare_calendar(
    account_id: str,
    calendar_id: str,
    email: str,
) -> bool:
    """Remove a single user from calendar sharing."""
    # First get current shares
    current = await get_calendar_shares(account_id, calendar_id)
    share_with: dict = {}
    for s in current:
        if s["email"] == email:
            continue
        share_with[s["email"]] = {
            "mayReadFreeBusy": True,
            "mayReadItems": True,
            "mayWriteAll": s.get("can_write", False),
            "mayUpdatePrivate": s.get("can_write", False),
            "mayRSVP": True,
        }

    result = await jmap_call(
        [["Calendar/set", {
            "accountId": account_id,
            "update": {calendar_id: {"shareWith": share_with if share_with else None}},
        }, "s0"]],
        using=USING_CALENDAR,
    )
    for resp in result.get("methodResponses", []):
        if resp[0] == "Calendar/set":
            return resp[1].get("updated") is not None
    return False
