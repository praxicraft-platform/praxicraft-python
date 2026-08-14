"""Exception types for the Praxicraft Assess Public API."""

from __future__ import annotations

from typing import Any


class PraxicraftError(Exception):
    """Base exception for all SDK errors."""


class APIError(PraxicraftError):
    """Raised for unexpected API / client failures without an HTTP status."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class APIConnectionError(APIError):
    """Raised when the HTTP request could not be completed."""

    def __init__(self, message: str = "Failed to connect to the Praxicraft API.") -> None:
        super().__init__(message, code="CONNECTION_ERROR")


class APIStatusError(APIError):
    """Raised when the API returns a non-success HTTP status."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: str | None = None,
        details: Any | None = None,
        response_body: Any | None = None,
        headers: dict[str, str] | None = None,
        required_plan: str | None = None,
    ) -> None:
        super().__init__(message, code=code)
        self.status_code = status_code
        self.details = details
        self.response_body = response_body
        self.headers = headers or {}
        self.required_plan = required_plan


class AuthenticationError(APIStatusError):
    """401 — invalid, missing, or expired API key."""


class InsufficientScopeError(APIStatusError):
    """403 — valid key missing required scope (or related permission denial)."""


class NotFoundError(APIStatusError):
    """404 — resource not found or not accessible with this key."""


class ValidationError(APIStatusError):
    """400 — request validation / business-rule failure."""


class RateLimitError(APIStatusError):
    """429 — rate limited; honor ``retry_after`` when present."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 429,
        code: str | None = "RATE_LIMITED",
        details: Any | None = None,
        response_body: Any | None = None,
        headers: dict[str, str] | None = None,
        required_plan: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            code=code,
            details=details,
            response_body=response_body,
            headers=headers,
            required_plan=required_plan,
        )
        self.retry_after = retry_after


def raise_for_status(
    *,
    status_code: int,
    body: Any,
    headers: dict[str, str],
) -> None:
    """Map a Public API error envelope to a typed exception and raise it."""
    error: dict[str, Any] = {}
    if isinstance(body, dict):
        maybe_error = body.get("error")
        if isinstance(maybe_error, dict):
            error = maybe_error

    code = error.get("code") if isinstance(error.get("code"), str) else None
    message = error.get("message") if isinstance(error.get("message"), str) else None
    details = error.get("details")
    required_plan = error.get("required_plan") if isinstance(error.get("required_plan"), str) else None

    if not message:
        if isinstance(body, str) and body.strip():
            message = body.strip()[:500]
        else:
            message = f"API request failed with status {status_code}."

    common = {
        "status_code": status_code,
        "code": code,
        "details": details,
        "response_body": body,
        "headers": headers,
        "required_plan": required_plan,
    }

    if status_code == 401:
        raise AuthenticationError(message, **common)
    if status_code == 403:
        raise InsufficientScopeError(message, **common)
    if status_code == 404:
        raise NotFoundError(message, **common)
    if status_code == 429:
        retry_after = _parse_retry_after(headers.get("retry-after"))
        raise RateLimitError(message, retry_after=retry_after, **common)
    if 400 <= status_code < 500:
        raise ValidationError(message, **common)
    raise APIStatusError(message, **common)


def _parse_retry_after(value: str | None) -> float | None:
    from praxicraft._retry import parse_retry_after_seconds

    return parse_retry_after_seconds(value)
