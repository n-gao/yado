"""Request/response schemas."""

import uuid
from datetime import date, datetime, time

from pydantic import BaseModel

from yado.models import VoteChoice

# --- Poll ---


class DateOptionCreate(BaseModel):
    date: date
    start_time: time | None = None
    end_time: time | None = None


class PollCreate(BaseModel):
    title: str
    description: str = ""
    timezone: str = "UTC"
    date_options: list[DateOptionCreate]


class DateOptionOut(BaseModel):
    id: uuid.UUID
    date: date
    start_time: time | None
    end_time: time | None


class VoteOut(BaseModel):
    id: uuid.UUID
    participant_id: uuid.UUID
    date_option_id: uuid.UUID
    choice: VoteChoice


class ParticipantOut(BaseModel):
    id: uuid.UUID
    name: str
    votes: list[VoteOut]


class PollOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    timezone: str
    created_at: datetime
    closed: bool
    date_options: list[DateOptionOut]
    participants: list[ParticipantOut]


class PollCreated(BaseModel):
    """Returned only to the creator — includes admin_token."""

    id: uuid.UUID
    admin_token: str
    poll: PollOut


# --- Voting ---


class VoteInput(BaseModel):
    date_option_id: uuid.UUID
    choice: VoteChoice


class VoteRequest(BaseModel):
    name: str
    edit_token: str | None = None
    votes: list[VoteInput]


class VoteResponse(BaseModel):
    participant_id: uuid.UUID
    edit_token: str
