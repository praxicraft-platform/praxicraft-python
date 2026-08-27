"""Assessments resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from praxicraft._paths import path_segment
from praxicraft.types import Assessment, Page

if TYPE_CHECKING:
    from praxicraft._client import Client


class AssessmentsResource:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(self, *, params: Mapping[str, Any] | None = None) -> Page:
        """``GET /assessments/`` — list assessments for the organisation."""
        return self._client.get("/assessments/", params=params)

    def retrieve(self, assessment: str) -> Assessment:
        """``GET /assessments/{slug_or_id}/`` — fetch one assessment."""
        key = path_segment(assessment, label="assessment")
        return self._client.get(f"/assessments/{key}/")

    def create(self, **fields: Any) -> Assessment:
        """``POST /assessments/create/`` — create a draft assessment.

        Pass Public API body fields as keyword arguments (e.g. ``title=...``).
        """
        return self._client.post("/assessments/create/", json=fields)

    def update(self, assessment: str, **fields: Any) -> Assessment:
        """``PATCH /assessments/{slug}/update/`` — patch config / status.

        Example activate: ``client.assessments.update(slug, status="active")``.
        """
        if not fields:
            raise ValueError("update() requires at least one field to change")
        key = path_segment(assessment, label="assessment")
        return self._client.patch(f"/assessments/{key}/update/", json=fields)

    def activate(self, assessment: str) -> Assessment:
        """Activate an assessment (``status="active"``) so it can accept invites."""
        return self.update(assessment, status="active")

    def list_tasks(
        self,
        assessment: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        """``GET /assessments/{slug}/tasks/`` — tasks attached to the assessment."""
        key = path_segment(assessment, label="assessment")
        return self._client.get(f"/assessments/{key}/tasks/", params=params)

    def attach_tasks(
        self,
        assessment: str,
        tasks: Sequence[Mapping[str, Any]] | None = None,
        **fields: Any,
    ) -> Any:
        """``POST /assessments/{slug}/tasks/attach/`` — attach platform/org tasks.

        Pass either ``tasks=[{task_id, source, ...}, ...]`` or a single
        ``task_id=...`` / ``source=...`` via ``fields`` (Public API accepts both).
        """
        body: dict[str, Any] = dict(fields)
        if tasks is not None:
            body["tasks"] = list(tasks)
        if not body:
            raise ValueError("attach_tasks() requires tasks=... or task_id=...")
        key = path_segment(assessment, label="assessment")
        return self._client.post(f"/assessments/{key}/tasks/attach/", json=body)

    def replace_tasks(
        self,
        assessment: str,
        tasks: Sequence[Mapping[str, Any]],
        **extra: Any,
    ) -> Any:
        """``PUT /assessments/{slug}/tasks/replace/`` — replace the full task lineup."""
        body: dict[str, Any] = {"tasks": list(tasks), **extra}
        key = path_segment(assessment, label="assessment")
        return self._client.put(f"/assessments/{key}/tasks/replace/", json=body)

    def remove_task(self, assessment: str, *, assessment_task_id: str) -> Any:
        """``DELETE /assessments/{slug}/tasks/remove/`` — detach one task row."""
        key = path_segment(assessment, label="assessment")
        # Body IDs must stay raw (not URL-encoded); only path segments are encoded.
        task_id = str(assessment_task_id).strip()
        if not task_id:
            raise ValueError("assessment_task_id must be a non-empty string")
        return self._client.delete(
            f"/assessments/{key}/tasks/remove/",
            json={"assessment_task_id": task_id},
        )
