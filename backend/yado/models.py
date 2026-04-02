"""Database models for Yado."""

import enum
import uuid
from datetime import UTC, date, datetime, time

from sqlmodel import Field, Relationship, SQLModel


class VoteChoice(enum.StrEnum):
    yes = "yes"
    no = "no"
    maybe = "maybe"


class Poll(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str = ""
    timezone: str = "UTC"
    admin_token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    closed: bool = False

    date_options: list["DateOption"] = Relationship(back_populates="poll", cascade_delete=True)
    participants: list["Participant"] = Relationship(back_populates="poll", cascade_delete=True)


class DateOption(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    poll_id: uuid.UUID = Field(foreign_key="poll.id")
    date: date
    start_time: time | None = None
    end_time: time | None = None

    poll: Poll = Relationship(back_populates="date_options")
    votes: list["Vote"] = Relationship(back_populates="date_option", cascade_delete=True)


class Participant(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    poll_id: uuid.UUID = Field(foreign_key="poll.id")
    name: str
    edit_token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    poll: Poll = Relationship(back_populates="participants")
    votes: list["Vote"] = Relationship(back_populates="participant", cascade_delete=True)


class Vote(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    participant_id: uuid.UUID = Field(foreign_key="participant.id")
    date_option_id: uuid.UUID = Field(foreign_key="dateoption.id")
    choice: VoteChoice

    participant: Participant = Relationship(back_populates="votes")
    date_option: DateOption = Relationship(back_populates="votes")
