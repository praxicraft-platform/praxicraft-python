"""Results resource."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Mapping
from urllib.parse import parse_qs, urlparse

from praxicraft._paths import path_segment
from praxicraft.types import Page, ResultRow

if TYPE_CHECKING:
    from praxicraft._client import Client

# Safety cap so a broken ``next`` cursor cannot spin forever.
_MAX_RESULT_PAGES = 10_000


class ResultsResource:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        assessment: str,
        *,
        cursor: str | None = None,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Page:
        """``GET /assessments/{slug}/results/`` — cohort results (cursor-paginated)."""
        query: dict[str, Any] = dict(params or {})
        if cursor is not None:
            query["cursor"] = cursor
        if page_size is not None:
            query["page_size"] = page_size
        key = path_segment(assessment, label="assessment")
        return self._client.get(f"/assessments/{key}/results/", params=query)

    def retrieve(self, invite_token: str) -> ResultRow:
        """``GET /invites/{token}/result/`` — single candidate result."""
        token = path_segment(invite_token, label="invite_token")
        return self._client.get(f"/invites/{token}/result/")

    def iter_all(
        self,
        assessment: str,
        *,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Iterator[ResultRow]:
        """Yield each result row, following cursor / ``next`` pagination links."""
        cursor: str | None = None
        seen: set[str] = set()
        for _ in range(_MAX_RESULT_PAGES):
            page = self.list(
                assessment,
                cursor=cursor,
                page_size=page_size,
                params=params,
            )
            if not isinstance(page, dict):
                return

            results = page.get("results")
            if isinstance(results, list):
                yield from results

            next_cursor = _next_cursor(page)
            if next_cursor is None:
                return
            if next_cursor in seen:
                # Guard against a stuck / cyclic cursor from a bad page link.
                return
            seen.add(next_cursor)
            cursor = next_cursor


def _next_cursor(page: Mapping[str, Any]) -> str | None:
    """Extract the next page cursor from a paginated Public API response."""
    next_cursor = page.get("next_cursor")
    if isinstance(next_cursor, str) and next_cursor:
        return next_cursor

    next_link = page.get("next")
    if not isinstance(next_link, str) or not next_link:
        return None

    query = parse_qs(urlparse(next_link).query)
    values = query.get("cursor") or []
    return values[0] if values else None
