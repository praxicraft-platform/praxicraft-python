from __future__ import annotations

from praxicraft import Client


def test_webhook_crud_and_test(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    webhook_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/webhooks/create/",
        status_code=201,
        json={
            "id": webhook_id,
            "url": "https://example.com/hooks",
            "secret_key": "whsec_abc",
            "events": ["assessment.completed"],
            "is_active": False,
        },
        match_json={
            "url": "https://example.com/hooks",
            "events": ["assessment.completed", "candidate.passed"],
        },
    )
    created = client.webhooks.create(
        url="https://example.com/hooks",
        events=["assessment.completed", "candidate.passed"],
    )
    assert created["secret_key"] == "whsec_abc"

    httpx_mock.add_response(
        method="GET",
        url=f"https://assess.example.com/api/v1/public/webhooks/{webhook_id}/",
        json={"id": webhook_id, "is_verified": False},
    )
    assert client.webhooks.retrieve(webhook_id)["id"] == webhook_id

    httpx_mock.add_response(
        method="POST",
        url=f"https://assess.example.com/api/v1/public/webhooks/{webhook_id}/test/",
        json={"ok": True},
    )
    assert client.webhooks.test(webhook_id)["ok"] is True

    httpx_mock.add_response(
        method="PATCH",
        url=f"https://assess.example.com/api/v1/public/webhooks/{webhook_id}/",
        json={"id": webhook_id, "is_active": True},
        match_json={"is_active": True},
    )
    assert client.webhooks.update(webhook_id, is_active=True)["is_active"] is True

    httpx_mock.add_response(
        method="GET",
        url=f"https://assess.example.com/api/v1/public/webhooks/{webhook_id}/deliveries/",
        json={"results": []},
    )
    assert client.webhooks.deliveries(webhook_id)["results"] == []

    httpx_mock.add_response(
        method="DELETE",
        url=f"https://assess.example.com/api/v1/public/webhooks/{webhook_id}/",
        status_code=204,
    )
    assert client.webhooks.delete(webhook_id) is None

    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/webhooks/",
        json={"results": []},
    )
    assert client.webhooks.list()["results"] == []
