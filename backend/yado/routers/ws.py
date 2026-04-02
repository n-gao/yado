"""WebSocket endpoint for real-time poll updates."""

import uuid
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# In-memory poll subscribers: poll_id -> set of websockets
_subscribers: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)


async def broadcast(poll_id: uuid.UUID, message: dict) -> None:
    """Send a message to all subscribers of a poll."""
    dead: list[WebSocket] = []
    for ws in _subscribers[poll_id]:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _subscribers[poll_id].discard(ws)


@router.websocket("/api/polls/{poll_id}/ws")
async def poll_ws(websocket: WebSocket, poll_id: uuid.UUID) -> None:
    await websocket.accept()
    _subscribers[poll_id].add(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        _subscribers[poll_id].discard(websocket)
