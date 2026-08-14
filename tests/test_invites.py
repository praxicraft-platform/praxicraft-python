from __future__ import annotations

import pytest

from praxicraft import Client, ValidationError


def test_create_invite(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/assessments/demo/invites/",
        status_code=201,
        json={
            "token": "11111111-1111-1111-1111-111111111111",
            "email": "jane@example.com",
            "status": "pending",
        },
        match_json={
            "email": "jane@example.com",
            "name": "Jane Doe",
            "send_email": True,
        },
    )
    data = client.invites.create(
        "demo",
        email="jane@example.com",
        name="Jane Doe",
        send_email=True,
    )
    assert data["status"] == "pending"


def test_create_invite_idempotent_200(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/assessments/demo/invites/",
        status_code=200,
        json={
            "token": "11111111-1111-1111-1111-111111111111",
            "email": "jane@example.com",
            "status": "pending",
        },
    )
    data = client.invites.create("demo", email="jane@example.com")
    assert data["email"] == "jane@example.com"


def test_bulk_create(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/assessments/demo/invites/bulk/",
        json={"invited": [{"email": "a@example.com"}], "skipped": []},
        match_json={
            "candidates": [{"email": "a@example.com"}],
            "send_email": False,
        },
    )
    data = client.invites.bulk_create(
        "demo",
        [{"email": "a@example.com"}],
        send_email=False,
    )
    assert len(data["invited"]) == 1


def test_list_and_retrieve_and_cancel(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    token = "11111111-1111-1111-1111-111111111111"

    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/invites/",
        json={"results": [{"token": token}]},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"https://assess.example.com/api/v1/public/invites/{token}/",
        json={"invite_token": token, "status": "pending"},
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"https://assess.example.com/api/v1/public/invites/{token}/",
        status_code=204,
    )

    assert client.invites.list()["results"][0]["token"] == token
    assert client.invites.retrieve(token)["status"] == "pending"
    assert client.invites.cancel(token) is None


def test_remind_cooldown(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    token = "11111111-1111-1111-1111-111111111111"
    httpx_mock.add_response(
        method="POST",
        url=f"https://assess.example.com/api/v1/public/invites/{token}/remind/",
        status_code=400,
        json={
            "error": {
                "code": "REMINDER_COOLDOWN",
                "message": "Wait 24 hours between reminders.",
            }
        },
    )
    with pytest.raises(ValidationError) as exc:
        client.invites.remind(token)
    assert exc.value.code == "REMINDER_COOLDOWN"
