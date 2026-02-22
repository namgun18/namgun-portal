"""Pydantic models for BBB meetings API."""

from pydantic import BaseModel


class Attendee(BaseModel):
    fullName: str
    role: str
    hasJoinedVoice: bool = False
    hasVideo: bool = False


class Meeting(BaseModel):
    meetingID: str
    meetingName: str
    running: bool = False
    participantCount: int = 0
    moderatorCount: int = 0
    createTime: str = ""
    hasBeenForciblyEnded: bool = False


class MeetingDetail(Meeting):
    attendees: list[Attendee] = []
    startTime: str = ""
    moderatorPW: str = ""
    attendeePW: str = ""
    internalMeetingID: str = ""


class CreateMeetingRequest(BaseModel):
    name: str
    meetingID: str | None = None
    record: bool = False
    duration: int = 0
    welcome: str | None = None
    muteOnStart: bool = False
    maxParticipants: int = 0


class JoinMeetingResponse(BaseModel):
    joinUrl: str


class GuestJoinRequest(BaseModel):
    name: str


class InviteLinkResponse(BaseModel):
    invite_url: str
    short_url: str


class Recording(BaseModel):
    recordID: str
    meetingID: str
    internalMeetingID: str = ""
    name: str = ""
    state: str = ""
    startTime: str = ""
    endTime: str = ""
    playbackUrl: str = ""
    size: int = 0
