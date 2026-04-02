"""Poll CRUD and voting endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from yado.database import get_session
from yado.models import DateOption, Participant, Poll, Vote
from yado.routers.ws import broadcast
from yado.schemas import (
    PollCreate,
    PollCreated,
    PollOut,
    VoteRequest,
    VoteResponse,
)

router = APIRouter(prefix="/api/polls", tags=["polls"])


async def _get_poll(poll_id: uuid.UUID, session: AsyncSession) -> Poll:
    stmt = (
        select(Poll)
        .where(Poll.id == poll_id)
        .options(
            selectinload(Poll.date_options).selectinload(DateOption.votes),  # type: ignore[arg-type]
            selectinload(Poll.participants).selectinload(Participant.votes),  # type: ignore[arg-type]
        )
    )
    result = await session.execute(stmt)
    poll = result.scalars().first()
    if not poll:
        raise HTTPException(404, "Poll not found")
    return poll


@router.post("", status_code=201)
async def create_poll(
    body: PollCreate, session: AsyncSession = Depends(get_session)
) -> PollCreated:
    poll = Poll(title=body.title, description=body.description, timezone=body.timezone)
    session.add(poll)
    for opt in body.date_options:
        session.add(
            DateOption(
                poll_id=poll.id,
                date=opt.date,
                start_time=opt.start_time,
                end_time=opt.end_time,
            )
        )
    await session.commit()

    poll = await _get_poll(poll.id, session)
    return PollCreated(
        id=poll.id,
        admin_token=poll.admin_token,
        poll=PollOut.model_validate(poll, from_attributes=True),
    )


@router.get("/{poll_id}")
async def get_poll(poll_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> PollOut:
    poll = await _get_poll(poll_id, session)
    return PollOut.model_validate(poll, from_attributes=True)


@router.post("/{poll_id}/vote")
async def vote(
    poll_id: uuid.UUID,
    body: VoteRequest,
    session: AsyncSession = Depends(get_session),
) -> VoteResponse:
    poll = await _get_poll(poll_id, session)
    if poll.closed:
        raise HTTPException(400, "Poll is closed")

    valid_option_ids = {opt.id for opt in poll.date_options}
    for v in body.votes:
        if v.date_option_id not in valid_option_ids:
            raise HTTPException(400, f"Invalid date option: {v.date_option_id}")

    # Find or create participant
    participant: Participant | None = None
    if body.edit_token:
        stmt = select(Participant).where(
            Participant.poll_id == poll_id,
            Participant.edit_token == body.edit_token,
        )
        result = await session.execute(stmt)
        participant = result.scalars().first()

    if participant:
        # Update: delete old votes
        old_result = await session.execute(
            select(Vote).where(Vote.participant_id == participant.id)
        )
        for old in old_result.scalars():
            await session.delete(old)
        participant.name = body.name
    else:
        participant = Participant(poll_id=poll_id, name=body.name)
        session.add(participant)
        await session.flush()

    for v in body.votes:
        session.add(
            Vote(
                participant_id=participant.id,
                date_option_id=v.date_option_id,
                choice=v.choice,
            )
        )

    # Save before commit+expire since expire_all clears cached attributes
    result = VoteResponse(participant_id=participant.id, edit_token=participant.edit_token)

    await session.commit()

    # Expire cached objects so the next query returns fresh data including new votes
    session.expire_all()

    # Broadcast update to all connected clients
    poll = await _get_poll(poll_id, session)
    await broadcast(
        poll_id,
        {
            "type": "poll_updated",
            "poll": PollOut.model_validate(poll, from_attributes=True).model_dump(mode="json"),
        },
    )

    return result


@router.post("/{poll_id}/close")
async def close_poll(
    poll_id: uuid.UUID,
    admin_token: str,
    session: AsyncSession = Depends(get_session),
) -> PollOut:
    poll = await _get_poll(poll_id, session)
    if poll.admin_token != admin_token:
        raise HTTPException(403, "Invalid admin token")
    poll.closed = True
    session.add(poll)
    await session.commit()
    poll = await _get_poll(poll_id, session)
    return PollOut.model_validate(poll, from_attributes=True)


@router.delete("/{poll_id}")
async def delete_poll(
    poll_id: uuid.UUID,
    admin_token: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    poll = await _get_poll(poll_id, session)
    if poll.admin_token != admin_token:
        raise HTTPException(403, "Invalid admin token")
    await session.delete(poll)
    await session.commit()
    return {"status": "deleted"}
