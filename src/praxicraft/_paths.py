"""Shared helpers for resource path building."""

from __future__ import annotations

from urllib.parse import quote


def path_segment(value: str, *, label: str = "id") -> str:
    """Validate and URL-encode a single path segment (slug, UUID, token)."""
    if value is None:
        raise ValueError(f"{label} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return quote(text, safe="")
