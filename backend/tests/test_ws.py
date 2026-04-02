"""Test WebSocket broadcast on vote."""

import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient

from yado.main import app

pytestmark = pytest.mark.asyncio


async def _create_poll(client: AsyncClient) -> dict:
    res = await client.post(
        "/api/polls",
        json={
            "title": "WS test",
            "date_options": [{"date": "2026-05-01"}],
        },
    )
    assert res.status_code == 201
    return res.json()


def test_ws_broadcast():
    """Use sync TestClient for WebSocket, verify broadcast arrives after a vote."""
    sync_client = TestClient(app)

    # Create poll via HTTP
    res = sync_client.post(
        "/api/polls",
        json={"title": "WS test", "date_options": [{"date": "2026-05-01"}]},
    )
    assert res.status_code == 201
    data = res.json()
    poll_id = data["id"]
    opt_id = data["poll"]["date_options"][0]["id"]

    # Connect WebSocket
    with sync_client.websocket_connect(f"/api/polls/{poll_id}/ws") as ws:
        # Vote via HTTP (in another "session")
        vote_res = sync_client.post(
            f"/api/polls/{poll_id}/vote",
            json={
                "name": "Alice",
                "votes": [{"date_option_id": opt_id, "choice": "yes"}],
            },
        )
        assert vote_res.status_code == 200

        # Should receive broadcast
        msg = ws.receive_json()
        assert msg["type"] == "poll_updated"
        assert len(msg["poll"]["participants"]) == 1
        assert msg["poll"]["participants"][0]["name"] == "Alice"
