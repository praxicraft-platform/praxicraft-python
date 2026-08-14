"""HTTP client for the Praxicraft Assess Public API."""

from __future__ import annotations

import os
from typing import Any, Mapping

import httpx

from praxicraft._errors import (
    APIConnectionError,
    APIError,
    APIStatusError,
    raise_for_status,
)
from praxicraft._retry import (
    DEFAULT_MAX_RETRIES,
    retry_delay_seconds,
    should_retry_status,
    sleep_fn,
)
from praxicraft.resources.assessments import AssessmentsResource
from praxicraft.resources.invites import InvitesResource
from praxicraft.resources.org import OrgResource
from praxicraft.resources.pipelines import PipelinesResource
from praxicraft.resources.results import ResultsResource
from praxicraft.resources.webhooks import WebhooksResource

DEFAULT_BASE_URL = "https://assess.praxicraft.com"
DEFAULT_API_PREFIX = "/api/v1/public"
DEFAULT_TIMEOUT = 30.0
USER_AGENT = "praxicraft-python/0.1.0"


class Client:
    """Synchronous client for the Assess Public API.

    Authentication uses organisation API keys as Bearer tokens
    (``ct_live_…``). Pass ``api_key`` or set ``PRAXICRAFT_API_KEY``.

    Optional ``base_url`` / ``PRAXICRAFT_API_BASE_URL`` override the host
    (default ``https://assess.praxicraft.com``).

    Transient ``429`` / ``5xx`` / transport failures are retried up to
    ``max_retries`` times (default 2 → 3 total attempts), honouring
    ``Retry-After`` when present.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        resolved_key = (api_key if api_key is not None else os.environ.get("PRAXICRAFT_API_KEY")) or ""
        resolved_key = resolved_key.strip()
        if not resolved_key:
            raise APIError(
                "No API key provided. Pass api_key=... or set PRAXICRAFT_API_KEY.",
                code="MISSING_API_KEY",
            )

        resolved_base = (
            base_url
            or os.environ.get("PRAXICRAFT_API_BASE_URL")
            or DEFAULT_BASE_URL
        ).strip().rstrip("/")
        if not resolved_base:
            raise APIError("base_url must be a non-empty URL.", code="INVALID_BASE_URL")

        self.api_key = resolved_key
        self.base_url = resolved_base
        self.api_prefix = DEFAULT_API_PREFIX
        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
        )

        self.assessments = AssessmentsResource(self)
        self.invites = InvitesResource(self)
        self.results = ResultsResource(self)
        self.org = OrgResource(self)
        self.webhooks = WebhooksResource(self)
        self.pipelines = PipelinesResource(self)

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send a request to a Public API path (e.g. ``/assessments/``).

        Success responses are returned as parsed JSON (flat dict/list).
        Empty 204 bodies return ``None``.
        """
        url_path = self._normalize_path(path)
        attempts = self.max_retries + 1
        last_exc: BaseException | None = None

        for attempt in range(attempts):
            if attempt > 0:
                retry_after = None
                if isinstance(last_exc, APIStatusError):
                    retry_after = last_exc.headers.get("retry-after")
                sleep_fn(retry_delay_seconds(attempt - 1, retry_after))

            try:
                return self._request_once(
                    method,
                    url_path,
                    params=params,
                    json=json,
                    headers=headers,
                )
            except APIConnectionError as exc:
                last_exc = exc
                if attempt >= attempts - 1:
                    raise
            except APIStatusError as exc:
                last_exc = exc
                if should_retry_status(exc.status_code) and attempt < attempts - 1:
                    continue
                raise

        assert last_exc is not None
        raise last_exc

    def _request_once(
        self,
        method: str,
        url_path: str,
        *,
        params: Mapping[str, Any] | None,
        json: Any | None,
        headers: Mapping[str, str] | None,
    ) -> Any:
        # Custom headers first; auth / UA are forced so callers cannot strip them.
        request_headers: dict[str, str] = {
            "Accept": "application/json",
        }
        if headers:
            request_headers.update(dict(headers))
        request_headers["Authorization"] = f"Bearer {self.api_key}"
        request_headers["User-Agent"] = USER_AGENT
        if json is not None:
            request_headers.setdefault("Content-Type", "application/json")

        try:
            response = self._http.request(
                method.upper(),
                url_path,
                params=_clean_params(params),
                json=json,
                headers=request_headers,
            )
        except httpx.TimeoutException as exc:
            raise APIConnectionError(f"Request timed out: {exc}") from exc
        except httpx.TransportError as exc:
            raise APIConnectionError(f"Transport error: {exc}") from exc

        header_map = {k.lower(): v for k, v in response.headers.items()}

        if response.status_code == 204:
            return None

        body: Any
        if not response.content:
            body = None
        else:
            try:
                body = response.json()
            except ValueError:
                raw_text = response.text
                if response.is_success:
                    raise APIError(
                        f"Invalid JSON response (HTTP {response.status_code}).",
                        code="INVALID_JSON",
                    )
                body = raw_text

        if response.is_success:
            return body

        raise_for_status(
            status_code=response.status_code,
            body=body,
            headers=header_map,
        )
        raise AssertionError("unreachable")

    def get(self, path: str, *, params: Mapping[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        json: Any | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        return self.request("POST", path, json=json, params=params)

    def patch(
        self,
        path: str,
        *,
        json: Any | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        return self.request("PATCH", path, json=json, params=params)

    def put(
        self,
        path: str,
        *,
        json: Any | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        return self.request("PUT", path, json=json, params=params)

    def delete(
        self,
        path: str,
        *,
        json: Any | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        return self.request("DELETE", path, json=json, params=params)

    def _normalize_path(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = f"/{path}"
        if path.startswith(self.api_prefix):
            relative = path
        else:
            relative = f"{self.api_prefix}{path}"

        if self._owns_client:
            return relative
        return f"{self.base_url}{relative}"


def _clean_params(params: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if params is None:
        return None
    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            cleaned[key] = "true" if value else "false"
        else:
            cleaned[key] = value
    return cleaned
