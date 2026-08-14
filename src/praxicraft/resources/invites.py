"""Invitations resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from praxicraft._paths import path_segment
from praxicraft.types import Invite, Page

if TYPE_CHECKING:
    from praxicraft._client import Client


class InvitesResource:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(self, *, params: Mapping[str, Any] | None = None) -> Page:
        """``GET /invites/`` — list invitations for the organisation."""
        return self._client.get("/invites/", params=params)

    def retrieve(self, invite_token: str) -> Invite:
        """``GET /invites/{token}/`` — invitation status."""
        token = path_segment(invite_token, label="invite_token")
        return self._client.get(f"/invites/{token}/")

    def create(
        self,
        assessment: str,
        *,
        email: str,
        name: str | None = None,
        role: str | None = None,
        expires_days: int | None = None,
        send_email: bool | None = None,
        **extra: Any,
    ) -> Invite:
        """``POST /assessments/{slug}/invites/`` — invite one candidate.

        Idempotent on email: a repeat call returns the existing invitation.
        """
        if not str(email).strip():
            raise ValueError("email is required")
        body: dict[str, Any] = {"email": email, **extra}
        if name is not None:
            body["name"] = name
        if role is not None:
            body["role"] = role
        if expires_days is not None:
            body["expires_days"] = expires_days
        if send_email is not None:
            body["send_email"] = send_email
        key = path_segment(assessment, label="assessment")
        return self._client.post(f"/assessments/{key}/invites/", json=body)

    def bulk_create(
        self,
        assessment: str,
        candidates: Sequence[Mapping[str, Any]],
        *,
        send_email: bool | None = None,
        **extra: Any,
    ) -> Any:
        """``POST /assessments/{slug}/invites/bulk/`` — invite many candidates."""
        body: dict[str, Any] = {"candidates": list(candidates), **extra}
        if send_email is not None:
            body["send_email"] = send_email
        key = path_segment(assessment, label="assessment")
        return self._client.post(f"/assessments/{key}/invites/bulk/", json=body)

    def remind(self, invite_token: str) -> Any:
        """``POST /invites/{token}/remind/`` — resend invitation email."""
        token = path_segment(invite_token, label="invite_token")
        return self._client.post(f"/invites/{token}/remind/")

    def cancel(self, invite_token: str) -> Any:
        """``DELETE /invites/{token}/`` — cancel a pending invitation."""
        token = path_segment(invite_token, label="invite_token")
        return self._client.delete(f"/invites/{token}/")
