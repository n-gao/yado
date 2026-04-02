"""End-to-end tests for poll CRUD and voting."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_poll(client: AsyncClient) -> dict:
    res = await client.post(
        "/api/polls",
        json={
            "title": "Team lunch",
            "date_options": [
                {"date": "2026-04-10"},
                {"date": "2026-04-11"},
                {"date": "2026-04-12"},
            ],
        },
    )
    assert res.status_code == 201
    return res.json()


async def test_create_poll(client: AsyncClient):
    data = await _create_poll(client)
    assert data["poll"]["title"] == "Team lunch"
    assert len(data["poll"]["date_options"]) == 3
    assert data["admin_token"]


async def test_get_poll(client: AsyncClient):
    created = await _create_poll(client)
    poll_id = created["id"]

    res = await client.get(f"/api/polls/{poll_id}")
    assert res.status_code == 200
    assert res.json()["title"] == "Team lunch"


async def test_get_nonexistent_poll(client: AsyncClient):
    res = await client.get("/api/polls/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


async def test_vote(client: AsyncClient):
    created = await _create_poll(client)
    poll_id = created["id"]
    opt_ids = [o["id"] for o in created["poll"]["date_options"]]

    res = await client.post(
        f"/api/polls/{poll_id}/vote",
        json={
            "name": "Alice",
            "votes": [
                {"date_option_id": opt_ids[0], "choice": "yes"},
                {"date_option_id": opt_ids[1], "choice": "maybe"},
            ],
        },
    )
    assert res.status_code == 200
    assert res.json()["edit_token"]

    # Verify vote appears in poll
    poll = (await client.get(f"/api/polls/{poll_id}")).json()
    assert len(poll["participants"]) == 1
    assert poll["participants"][0]["name"] == "Alice"
    assert len(poll["participants"][0]["votes"]) == 2


async def test_update_vote(client: AsyncClient):
    created = await _create_poll(client)
    poll_id = created["id"]
    opt_ids = [o["id"] for o in created["poll"]["date_options"]]

    # Initial vote
    res1 = await client.post(
        f"/api/polls/{poll_id}/vote",
        json={
            "name": "Bob",
            "votes": [{"date_option_id": opt_ids[0], "choice": "yes"}],
        },
    )
    edit_token = res1.json()["edit_token"]

    # Update vote using edit_token
    res2 = await client.post(
        f"/api/polls/{poll_id}/vote",
        json={
            "name": "Bob Updated",
            "edit_token": edit_token,
            "votes": [{"date_option_id": opt_ids[2], "choice": "maybe"}],
        },
    )
    assert res2.status_code == 200

    poll = (await client.get(f"/api/polls/{poll_id}")).json()
    assert len(poll["participants"]) == 1
    assert poll["participants"][0]["name"] == "Bob Updated"
    assert poll["participants"][0]["votes"][0]["date_option_id"] == opt_ids[2]


async def test_vote_invalid_option(client: AsyncClient):
    created = await _create_poll(client)
    poll_id = created["id"]

    res = await client.post(
        f"/api/polls/{poll_id}/vote",
        json={
            "name": "Eve",
            "votes": [
                {
                    "date_option_id": "00000000-0000-0000-0000-000000000000",
                    "choice": "yes",
                }
            ],
        },
    )
    assert res.status_code == 400


async def test_close_poll(client: AsyncClient):
    created = await _create_poll(client)
    poll_id = created["id"]
    admin_token = created["admin_token"]

    res = await client.post(f"/api/polls/{poll_id}/close", params={"admin_token": admin_token})
    assert res.status_code == 200
    assert res.json()["closed"] is True


async def test_close_poll_wrong_token(client: AsyncClient):
    created = await _create_poll(client)
    poll_id = created["id"]

    res = await client.post(f"/api/polls/{poll_id}/close", params={"admin_token": "wrong"})
    assert res.status_code == 403


async def test_vote_on_closed_poll(client: AsyncClient):
    created = await _create_poll(client)
    poll_id = created["id"]
    admin_token = created["admin_token"]
    opt_ids = [o["id"] for o in created["poll"]["date_options"]]

    await client.post(f"/api/polls/{poll_id}/close", params={"admin_token": admin_token})

    res = await client.post(
        f"/api/polls/{poll_id}/vote",
        json={
            "name": "Late",
            "votes": [{"date_option_id": opt_ids[0], "choice": "yes"}],
        },
    )
    assert res.status_code == 400


async def test_delete_poll(client: AsyncClient):
    created = await _create_poll(client)
    poll_id = created["id"]
    admin_token = created["admin_token"]

    res = await client.delete(f"/api/polls/{poll_id}", params={"admin_token": admin_token})
    assert res.status_code == 200

    res2 = await client.get(f"/api/polls/{poll_id}")
    assert res2.status_code == 404
