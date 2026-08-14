"""Hiring pipelines resource (list / enroll)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from praxicraft._paths import path_segment
from praxicraft.types import Enrollment, Page, Pipeline

if TYPE_CHECKING:
    from praxicraft._client import Client


class PipelinesResource:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(self, *, params: Mapping[str, Any] | None = None) -> Page:
        """``GET /pipelines/`` — list hiring pipelines."""
        return self._client.get("/pipelines/", params=params)

    def retrieve(self, pipeline: str) -> Pipeline:
        """``GET /pipelines/{slug}/`` — pipeline detail + stages."""
        key = path_segment(pipeline, label="pipeline")
        return self._client.get(f"/pipelines/{key}/")

    def enroll(
        self,
        pipeline: str,
        *,
        email: str,
        name: str | None = None,
        send_email: bool | None = None,
        **extra: Any,
    ) -> Enrollment:
        """``POST /pipelines/{slug}/enroll/`` — enroll one candidate.

        Idempotent on email for the same pipeline.
        """
        if not str(email).strip():
            raise ValueError("email is required")
        body: dict[str, Any] = {"email": email, **extra}
        if name is not None:
            body["name"] = name
        if send_email is not None:
            body["send_email"] = send_email
        key = path_segment(pipeline, label="pipeline")
        return self._client.post(f"/pipelines/{key}/enroll/", json=body)

    def bulk_enroll(
        self,
        pipeline: str,
        candidates: Sequence[Mapping[str, Any]],
        *,
        send_email: bool | None = None,
        **extra: Any,
    ) -> Any:
        """``POST /pipelines/{slug}/enroll/bulk/`` — enroll many candidates."""
        body: dict[str, Any] = {"candidates": list(candidates), **extra}
        if send_email is not None:
            body["send_email"] = send_email
        key = path_segment(pipeline, label="pipeline")
        return self._client.post(f"/pipelines/{key}/enroll/bulk/", json=body)

    def list_enrollments(
        self,
        pipeline: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        """``GET /pipelines/{slug}/enrollments/``."""
        key = path_segment(pipeline, label="pipeline")
        return self._client.get(f"/pipelines/{key}/enrollments/", params=params)

    def get_enrollment(self, enrollment_id: str) -> Any:
        """``GET /pipelines/enrollments/{id}/`` — enrollment status + history."""
        key = path_segment(enrollment_id, label="enrollment_id")
        return self._client.get(f"/pipelines/enrollments/{key}/")
