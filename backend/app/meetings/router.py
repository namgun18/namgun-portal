"""BBB meetings API router."""

import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.auth.deps import get_current_user
from app.db.models import User
from app.meetings import bbb
from app.meetings.schemas import (
    Attendee,
    CreateMeetingRequest,
    GuestJoinRequest,
    InviteLinkResponse,
    JoinMeetingResponse,
    Meeting,
    MeetingDetail,
    Recording,
)

# In-memory short code → meeting_id mapping
_short_codes: dict[str, str] = {}
_meeting_codes: dict[str, str] = {}  # meeting_id → short_code


def _get_short_code(meeting_id: str) -> str:
    """Get or create a 6-char short code for a meeting."""
    if meeting_id in _meeting_codes:
        return _meeting_codes[meeting_id]
    raw = hashlib.sha256(f"{meeting_id}{time.time()}".encode()).hexdigest()
    code = raw[:6]
    _short_codes[code] = meeting_id
    _meeting_codes[meeting_id] = code
    return code

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


def _parse_bool(val: str | bool) -> bool:
    if isinstance(val, bool):
        return val
    return val.lower() == "true"


def _parse_int(val: str | int, default: int = 0) -> int:
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _parse_meeting(m: dict) -> Meeting:
    return Meeting(
        meetingID=m.get("meetingID", ""),
        meetingName=m.get("meetingName", ""),
        running=_parse_bool(m.get("running", False)),
        participantCount=_parse_int(m.get("participantCount", 0)),
        moderatorCount=_parse_int(m.get("moderatorCount", 0)),
        createTime=str(m.get("createTime", "")),
        hasBeenForciblyEnded=_parse_bool(m.get("hasBeenForciblyEnded", False)),
    )


def _parse_attendees(data: dict) -> list[Attendee]:
    attendees_data = data.get("attendees", {})
    if not attendees_data:
        return []
    att_list = attendees_data.get("attendee", [])
    if isinstance(att_list, dict):
        att_list = [att_list]
    return [
        Attendee(
            fullName=a.get("fullName", ""),
            role=a.get("role", "VIEWER"),
            hasJoinedVoice=_parse_bool(a.get("hasJoinedVoice", False)),
            hasVideo=_parse_bool(a.get("hasVideo", False)),
        )
        for a in att_list
    ]


def _parse_recording(r: dict) -> Recording:
    # Extract playback URL from nested structure
    playback = r.get("playback", {})
    playback_url = ""
    if isinstance(playback, dict):
        fmt = playback.get("format", {})
        if isinstance(fmt, dict):
            playback_url = fmt.get("url", "")
        elif isinstance(fmt, list) and fmt:
            playback_url = fmt[0].get("url", "")

    return Recording(
        recordID=r.get("recordID", ""),
        meetingID=r.get("meetingID", ""),
        internalMeetingID=r.get("internalMeetingID", ""),
        name=r.get("name", ""),
        state=r.get("state", ""),
        startTime=str(r.get("startTime", "")),
        endTime=str(r.get("endTime", "")),
        playbackUrl=playback_url,
        size=_parse_int(r.get("size", 0)),
    )


@router.get("/", response_model=list[Meeting])
async def list_meetings(user: User = Depends(get_current_user)):
    """Get list of active meetings."""
    raw = await bbb.get_meetings()
    return [_parse_meeting(m) for m in raw]


@router.get("/recordings", response_model=list[Recording])
async def list_recordings(
    meeting_id: str | None = None,
    user: User = Depends(get_current_user),
):
    """Get list of recordings."""
    raw = await bbb.get_recordings(meeting_id)
    return [_parse_recording(r) for r in raw]


@router.get("/{meeting_id}", response_model=MeetingDetail)
async def get_meeting(meeting_id: str, user: User = Depends(get_current_user)):
    """Get detailed info about a meeting."""
    info = await bbb.get_meeting_info(meeting_id)
    if not info:
        raise HTTPException(status_code=404, detail="Meeting not found")

    base = _parse_meeting(info)
    return MeetingDetail(
        **base.model_dump(),
        attendees=_parse_attendees(info),
        startTime=str(info.get("startTime", "")),
        moderatorPW=info.get("moderatorPW", ""),
        attendeePW=info.get("attendeePW", ""),
        internalMeetingID=info.get("internalMeetingID", ""),
    )


@router.post("/", response_model=Meeting)
async def create_meeting(
    body: CreateMeetingRequest,
    user: User = Depends(get_current_user),
):
    """Create a new meeting."""
    result = await bbb.create_meeting(
        name=body.name,
        meeting_id=body.meetingID,
        record=body.record,
        duration=body.duration,
        welcome=body.welcome,
        mute_on_start=body.muteOnStart,
        max_participants=body.maxParticipants,
    )
    if result.get("returncode") != "SUCCESS":
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Failed to create meeting"),
        )
    return Meeting(
        meetingID=result.get("meetingID", ""),
        meetingName=body.name,
        running=False,
        participantCount=0,
        moderatorCount=0,
        createTime=str(result.get("createTime", "")),
    )


@router.post("/{meeting_id}/join", response_model=JoinMeetingResponse)
async def join_meeting(
    meeting_id: str, request: Request, user: User = Depends(get_current_user)
):
    """Get join URL for a meeting."""
    display_name = user.display_name or user.username
    role = "MODERATOR" if user.is_admin else "VIEWER"
    # 회의 종료 시 탭 자동 닫힘 페이지로 리다이렉트
    origin = f"{request.url.scheme}://{request.url.hostname}"
    if request.url.port and request.url.port not in (80, 443):
        origin += f":{request.url.port}"
    logout_url = f"{origin}/meeting-closed"
    url = await bbb.get_join_url(
        meeting_id, display_name, role=role, logout_url=logout_url
    )
    if not url:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return JoinMeetingResponse(joinUrl=url)


@router.get("/{meeting_id}/invite", response_model=InviteLinkResponse)
async def get_invite_link(
    meeting_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Generate invite link with short URL for a meeting."""
    origin = f"{request.url.scheme}://{request.headers.get('host', request.url.hostname)}"
    code = _get_short_code(meeting_id)
    return InviteLinkResponse(
        invite_url=f"{origin}/join/{meeting_id}",
        short_url=f"{origin}/m/{code}",
    )


@router.post("/{meeting_id}/guest-join", response_model=JoinMeetingResponse)
async def guest_join_meeting(
    meeting_id: str,
    body: GuestJoinRequest,
    request: Request,
):
    """Get join URL for a guest (no auth required)."""
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="이름을 입력해주세요.")
    origin = f"{request.url.scheme}://{request.headers.get('host', request.url.hostname)}"
    logout_url = f"{origin}/meeting-closed"
    url = await bbb.get_join_url(
        meeting_id, body.name.strip(), role="VIEWER", logout_url=logout_url
    )
    if not url:
        raise HTTPException(status_code=404, detail="회의를 찾을 수 없습니다.")
    return JoinMeetingResponse(joinUrl=url)


@router.post("/{meeting_id}/end")
async def end_meeting(meeting_id: str, user: User = Depends(get_current_user)):
    """End a running meeting (admin only)."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    success = await bbb.end_meeting(meeting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found or already ended")
    return {"status": "ok"}


@router.delete("/recordings/{record_id}")
async def delete_recording(record_id: str, user: User = Depends(get_current_user)):
    """Delete a recording (admin only)."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    success = await bbb.delete_recording(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Recording not found")
    return {"status": "ok"}
