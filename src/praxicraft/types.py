"""Typed Public API response shapes (TypedDict).

Resource methods are annotated with these types. At runtime responses remain
plain dicts (JSON), but type checkers catch field misuse.
"""

from __future__ import annotations

from typing import Any, TypedDict


class Org(TypedDict, total=False):
    id: str
    name: str
    slug: str
    plan: str
    invites_remaining: int
    invites_used: int
    invites_limit: int


class Assessment(TypedDict, total=False):
    id: str
    slug: str
    title: str
    status: str


class Invite(TypedDict, total=False):
    id: str
    invite_token: str
    invite_url: str
    email: str
    name: str
    status: str
    assessment: str


class ResultRow(TypedDict, total=False):
    invite_token: str
    email: str
    name: str
    status: str
    score: float
    passed: bool


class WebhookEndpoint(TypedDict, total=False):
    id: str
    url: str
    events: list[str]
    is_active: bool
    secret_key: str


class Pipeline(TypedDict, total=False):
    id: str
    slug: str
    name: str
    status: str


class Enrollment(TypedDict, total=False):
    enrollment_id: str
    id: str
    email: str
    name: str
    status: str


class Page(TypedDict, total=False):
    # total=False makes every key optional (Python 3.10-safe; no NotRequired).
    results: list[Any]
    next: str | None
    previous: str | None
    next_cursor: str | None
    count: int
