from __future__ import annotations

import pytest

from praxicraft import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    Client,
    InsufficientScopeError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


@pytest.fixture
def client(httpx_mock) -> Client:
    # httpx_mock is unused here but ensures pytest-httpx is loaded for siblings
    _ = httpx_mock
    return Client(api_key="ct_live_test", base_url="https://assess.example.com")


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PRAXICRAFT_API_KEY", raising=False)
    with pytest.raises(APIError) as exc:
        Client()
    assert exc.value.code == "MISSING_API_KEY"


def test_request_success_flat_json(httpx_mock, client: Client) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/",
        json={"name": "Acme", "plan": "starter"},
    )
    data = client.get("/org/")
    assert data == {"name": "Acme", "plan": "starter"}


def test_authentication_error(httpx_mock, client: Client) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/",
        status_code=401,
        json={
            "error": {
                "code": "INVALID_API_KEY",
                "message": "Invalid or revoked API Key.",
            }
        },
    )
    with pytest.raises(AuthenticationError) as exc:
        client.get("/org/")
    assert exc.value.code == "INVALID_API_KEY"
    assert exc.value.status_code == 401


def test_insufficient_scope(httpx_mock, client: Client) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/",
        status_code=403,
        json={
            "error": {
                "code": "INSUFFICIENT_SCOPE",
                "message": "This API key does not have the 'assessments:read' scope.",
            }
        },
    )
    with pytest.raises(InsufficientScopeError) as exc:
        client.get("/assessments/")
    assert exc.value.code == "INSUFFICIENT_SCOPE"


def test_not_found(httpx_mock, client: Client) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/missing/",
        status_code=404,
        json={"error": {"code": "NOT_FOUND", "message": "Not found."}},
    )
    with pytest.raises(NotFoundError) as exc:
        client.get("/assessments/missing/")
    assert exc.value.code == "NOT_FOUND"


def test_validation_error_with_details(httpx_mock, client: Client) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/assessments/demo/invites/",
        status_code=400,
        json={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "One or more fields are invalid.",
                "details": {"email": "Must be a valid email address."},
            }
        },
    )
    with pytest.raises(ValidationError) as exc:
        client.post("/assessments/demo/invites/", json={"email": "bad"})
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"email": "Must be a valid email address."}


def test_rate_limit_retry_after(httpx_mock, client: Client) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/",
        status_code=429,
        headers={"Retry-After": "12"},
        json={"error": {"code": "RATE_LIMITED", "message": "Too many requests."}},
    )
    with pytest.raises(RateLimitError) as exc:
        client.get("/assessments/")
    assert exc.value.code == "RATE_LIMITED"
    assert exc.value.retry_after == 12.0


def test_invalid_json_body(httpx_mock, client: Client) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/org/",
        status_code=200,
        text="not-json",
        headers={"Content-Type": "text/plain"},
    )
    with pytest.raises(APIError) as exc:
        client.get("/org/")
    assert exc.value.code == "INVALID_JSON"


def test_connection_error(httpx_mock, client: Client) -> None:
    import httpx

    httpx_mock.add_exception(httpx.ConnectError("boom"))
    with pytest.raises(APIConnectionError):
        client.get("/org/")
