"""Webhooks management resource (CRUD + test). Local verify lives in ``praxicraft.webhooks``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from praxicraft._paths import path_segment
from praxicraft.types import Page, WebhookEndpoint

if TYPE_CHECKING:
    from praxicraft._client import Client


class WebhooksResource:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(self, *, params: Mapping[str, Any] | None = None) -> Page:
        """``GET /webhooks/`` — list webhook endpoints."""
        return self._client.get("/webhooks/", params=params)

    def create(
        self,
        *,
        url: str,
        events: Sequence[str],
        **extra: Any,
    ) -> WebhookEndpoint:
        """``POST /webhooks/create/`` — register a webhook.

        Store ``secret_key`` (``whsec_…``) from the create response — shown once.
        New endpoints start inactive until a successful ``test()``.
        """
        if not str(url).strip():
            raise ValueError("url is required")
        if not events:
            raise ValueError("events must be a non-empty list")
        body: dict[str, Any] = {"url": url, "events": list(events), **extra}
        return self._client.post("/webhooks/create/", json=body)

    def retrieve(self, webhook_id: str) -> WebhookEndpoint:
        """``GET /webhooks/{id}/``."""
        key = path_segment(webhook_id, label="webhook_id")
        return self._client.get(f"/webhooks/{key}/")

    def update(self, webhook_id: str, **fields: Any) -> WebhookEndpoint:
        """``PATCH /webhooks/{id}/`` — update URL, events, or ``is_active``."""
        if not fields:
            raise ValueError("update() requires at least one field to change")
        key = path_segment(webhook_id, label="webhook_id")
        return self._client.patch(f"/webhooks/{key}/", json=fields)

    def delete(self, webhook_id: str) -> Any:
        """``DELETE /webhooks/{id}/``."""
        key = path_segment(webhook_id, label="webhook_id")
        return self._client.delete(f"/webhooks/{key}/")

    def deliveries(self, webhook_id: str) -> Any:
        """``GET /webhooks/{id}/deliveries/`` — recent delivery log."""
        key = path_segment(webhook_id, label="webhook_id")
        return self._client.get(f"/webhooks/{key}/deliveries/")

    def test(self, webhook_id: str) -> Any:
        """``POST /webhooks/{id}/test/`` — send a signed test ping."""
        key = path_segment(webhook_id, label="webhook_id")
        return self._client.post(f"/webhooks/{key}/test/")
