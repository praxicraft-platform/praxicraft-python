from __future__ import annotations

from praxicraft import Client


def test_org_retrieve(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/",
        json={
            "name": "Acme",
            "plan": "starter",
            "invite_limit": 100,
            "invites_used": 12,
            "invites_remaining": 88,
        },
    )
    org = client.org.retrieve()
    assert org["invites_remaining"] == 88


def test_org_stats(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/stats/",
        json={"pass_rate": 0.42, "total_invites": 10},
    )
    assert client.org.stats()["pass_rate"] == 0.42
