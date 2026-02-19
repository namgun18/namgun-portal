"""BigBlueButton API client with SHA256 checksum authentication."""

import hashlib
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

import httpx

from app.config import get_settings

settings = get_settings()


def _checksum(method: str, query_string: str) -> str:
    """Generate SHA256 checksum for BBB API call."""
    raw = f"{method}{query_string}{settings.bbb_secret}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _build_url(method: str, params: dict | None = None) -> str:
    """Build full BBB API URL with checksum."""
    params = params or {}
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    query_string = urlencode(params)
    checksum = _checksum(method, query_string)
    if query_string:
        query_string += f"&checksum={checksum}"
    else:
        query_string = f"checksum={checksum}"
    return f"{settings.bbb_url}/{method}?{query_string}"


def _xml_to_dict(element: ET.Element) -> dict | str:
    """Recursively convert XML element to dict."""
    result = {}
    for child in element:
        tag = child.tag
        if len(child) > 0:
            value = _xml_to_dict(child)
        else:
            value = child.text or ""
        # Handle repeated tags (e.g., multiple <attendee>)
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(value)
        else:
            result[tag] = value
    return result if result else (element.text or "")


async def _api_call(method: str, params: dict | None = None) -> dict:
    """Make a BBB API call and parse XML response."""
    url = _build_url(method, params)
    async with httpx.AsyncClient(timeout=15.0, verify=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    root = ET.fromstring(resp.text)
    data = _xml_to_dict(root)
    if isinstance(data, str):
        return {"returncode": data}
    return data


async def get_meetings() -> list[dict]:
    """Get list of active meetings."""
    data = await _api_call("getMeetings")
    if data.get("returncode") != "SUCCESS":
        return []
    meetings = data.get("meetings", {})
    if not meetings:
        return []
    meeting_list = meetings.get("meeting", [])
    if isinstance(meeting_list, dict):
        meeting_list = [meeting_list]
    return meeting_list


async def get_meeting_info(meeting_id: str) -> dict | None:
    """Get detailed info about a specific meeting."""
    data = await _api_call("getMeetingInfo", {"meetingID": meeting_id})
    if data.get("returncode") != "SUCCESS":
        return None
    return data


async def create_meeting(
    name: str,
    meeting_id: str | None = None,
    *,
    record: bool = False,
    duration: int = 0,
    welcome: str | None = None,
    mute_on_start: bool = False,
    max_participants: int = 0,
    moderator_pw: str | None = None,
    attendee_pw: str | None = None,
) -> dict:
    """Create a new meeting."""
    if not meeting_id:
        meeting_id = str(uuid.uuid4())
    if not moderator_pw:
        moderator_pw = f"mod-{uuid.uuid4().hex[:8]}"
    if not attendee_pw:
        attendee_pw = f"att-{uuid.uuid4().hex[:8]}"

    params = {
        "name": name,
        "meetingID": meeting_id,
        "record": "true" if record else "false",
        "moderatorPW": moderator_pw,
        "attendeePW": attendee_pw,
    }
    if duration > 0:
        params["duration"] = str(duration)
    if welcome:
        params["welcome"] = welcome
    if mute_on_start:
        params["muteOnStart"] = "true"
    if max_participants > 0:
        params["maxParticipants"] = str(max_participants)

    data = await _api_call("create", params)
    return data


async def get_join_url(
    meeting_id: str, full_name: str, *, role: str = "VIEWER", password: str | None = None
) -> str | None:
    """Generate a join URL for a meeting."""
    # If no password, fetch meeting info to get the right one
    if not password:
        info = await get_meeting_info(meeting_id)
        if not info:
            return None
        if role == "MODERATOR":
            password = info.get("moderatorPW", "")
        else:
            password = info.get("attendeePW", "")

    params = {
        "meetingID": meeting_id,
        "fullName": full_name,
        "password": password,
        "redirect": "true",
    }
    return _build_url("join", params)


async def end_meeting(meeting_id: str) -> bool:
    """End a running meeting."""
    info = await get_meeting_info(meeting_id)
    if not info:
        return False
    password = info.get("moderatorPW", "")
    data = await _api_call("end", {"meetingID": meeting_id, "password": password})
    return data.get("returncode") == "SUCCESS"


async def get_recordings(meeting_id: str | None = None) -> list[dict]:
    """Get list of recordings, optionally filtered by meeting ID."""
    params = {}
    if meeting_id:
        params["meetingID"] = meeting_id
    data = await _api_call("getRecordings", params)
    if data.get("returncode") != "SUCCESS":
        return []
    recordings = data.get("recordings", {})
    if not recordings:
        return []
    rec_list = recordings.get("recording", [])
    if isinstance(rec_list, dict):
        rec_list = [rec_list]
    return rec_list


async def delete_recording(record_id: str) -> bool:
    """Delete a recording."""
    data = await _api_call("deleteRecordings", {"recordID": record_id})
    return data.get("returncode") == "SUCCESS"
