from __future__ import annotations

import pytest

from praxicraft import APIStatusError, Client, APIError
from praxicraft.webhooks import verify_signature


def test_blank_api_key_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAXICRAFT_API_KEY", "   ")
    with pytest.raises(APIError) as exc:
        Client()
    assert exc.value.code == "MISSING_API_KEY"


def test_whitespace_api_key_arg_rejected() -> None:
    with pytest.raises(APIError):
        Client(api_key="  \n")


def test_html_error_body_still_raises_status(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com", max_retries=0)
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/",
        status_code=502,
        text="<html>Bad Gateway</html>",
        headers={"Content-Type": "text/html"},
    )
    with pytest.raises(APIStatusError) as exc:
        client.org.retrieve()
    assert exc.value.status_code == 502
    assert "Bad Gateway" in exc.value.message


def test_plan_required_exposes_required_plan(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/stats/",
        status_code=403,
        json={
            "error": {
                "code": "PLAN_REQUIRED",
                "message": "Starter plan required.",
                "required_plan": "starter",
            }
        },
    )
    with pytest.raises(APIStatusError) as exc:
        client.org.stats()
    assert exc.value.code == "PLAN_REQUIRED"
    assert exc.value.required_plan == "starter"


def test_empty_assessment_slug_rejected() -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    with pytest.raises(ValueError):
        client.assessments.retrieve("  ")


def test_path_encodes_special_slug(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/a%2Fb/",
        json={"slug": "a/b"},
    )
    assert client.assessments.retrieve("a/b")["slug"] == "a/b"


def test_iter_all_stops_on_repeated_cursor(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/demo/results/",
        json={
            "next": "https://assess.example.com/api/v1/public/assessments/demo/results/?cursor=stuck",
            "results": [{"email": "a@example.com"}],
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/demo/results/?cursor=stuck",
        json={
            "next": "https://assess.example.com/api/v1/public/assessments/demo/results/?cursor=stuck",
            "results": [{"email": "b@example.com"}],
        },
    )
    rows = list(client.results.iter_all("demo"))
    assert [r["email"] for r in rows] == ["a@example.com", "b@example.com"]


def test_verify_signature_mismatched_length_returns_false() -> None:
    assert verify_signature("whsec_x", b"{}", "sha256=ab") is False


def test_update_requires_fields() -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    with pytest.raises(ValueError):
        client.assessments.update("demo")
    with pytest.raises(ValueError):
        client.webhooks.update("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


def test_invite_requires_email() -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    with pytest.raises(ValueError):
        client.invites.create("demo", email="  ")


def test_retry_after_http_date(httpx_mock, monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import datetime, timedelta, timezone

    import praxicraft._retry as retry_mod

    monkeypatch.setattr(retry_mod, "sleep_fn", lambda _s: None)
    when = (datetime.now(timezone.utc) + timedelta(seconds=2)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com", max_retries=0)
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/",
        status_code=429,
        json={"error": {"code": "RATE_LIMITED", "message": "slow"}},
        headers={"Retry-After": when},
    )
    with pytest.raises(APIStatusError) as exc:
        client.org.retrieve()
    assert exc.value.status_code == 429
    assert exc.value.retry_after is not None
    assert 0 <= exc.value.retry_after <= 5


def test_retries_on_429_then_succeeds(httpx_mock, monkeypatch: pytest.MonkeyPatch) -> None:
    import praxicraft._retry as retry_mod

    monkeypatch.setattr(retry_mod, "sleep_fn", lambda _s: None)
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com", max_retries=2)
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/",
        status_code=429,
        json={"error": {"code": "RATE_LIMITED", "message": "slow"}},
        headers={"Retry-After": "0"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/",
        json={"name": "Acme", "plan": "starter"},
    )
    assert client.org.retrieve()["name"] == "Acme"


def test_no_retry_on_400(httpx_mock, monkeypatch: pytest.MonkeyPatch) -> None:
    import praxicraft._retry as retry_mod

    monkeypatch.setattr(retry_mod, "sleep_fn", lambda _s: None)
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com", max_retries=3)
    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/assessments/demo/invites/",
        status_code=400,
        json={"error": {"code": "VALIDATION_ERROR", "message": "bad"}},
    )
    with pytest.raises(APIStatusError) as exc:
        client.invites.create("demo", email="x@example.com")
    assert exc.value.status_code == 400
    assert len(httpx_mock.get_requests()) == 1


def test_auth_forced_over_custom_headers(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/",
        json={"ok": True},
    )
    client.request(
        "GET",
        "/org/",
        headers={"Authorization": "Bearer stolen", "User-Agent": "evil"},
    )
    req = httpx_mock.get_requests()[0]
    assert req.headers["Authorization"] == "Bearer ct_live_test"
    assert req.headers["User-Agent"].startswith("praxicraft-python/")
