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

    def list_cases(
        self,
        assessment: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        """``GET /assessments/{slug}/cases/`` — tasks attached to the assessment."""
        key = path_segment(assessment, label="assessment")
        return self._client.get(f"/assessments/{key}/cases/", params=params)

    def attach_cases(
        self,
        assessment: str,
        cases: Sequence[Mapping[str, Any]] | None = None,
        **fields: Any,
    ) -> Any:
        """``POST /assessments/{slug}/cases/attach/`` — attach platform/org cases.

        Pass either ``cases=[{case_id, source, ...}, ...]`` or a single
        ``case_id=...`` / ``source=...`` via ``fields`` (Public API accepts both).
        """
        body: dict[str, Any] = dict(fields)
        if cases is not None:
            body["cases"] = list(cases)
        if not body:
            raise ValueError("attach_cases() requires cases=... or case_id=...")
        key = path_segment(assessment, label="assessment")
        return self._client.post(f"/assessments/{key}/cases/attach/", json=body)

    def replace_cases(
        self,
        assessment: str,
        cases: Sequence[Mapping[str, Any]],
        **extra: Any,
    ) -> Any:
        """``PUT /assessments/{slug}/cases/replace/`` — replace the full case lineup."""
        body: dict[str, Any] = {"cases": list(cases), **extra}
        key = path_segment(assessment, label="assessment")
        return self._client.put(f"/assessments/{key}/cases/replace/", json=body)

    def remove_case(self, assessment: str, *, assessment_case_id: str) -> Any:
        """``DELETE /assessments/{slug}/cases/remove/`` — detach one case row."""
        key = path_segment(assessment, label="assessment")
        # Body IDs must stay raw (not URL-encoded); only path segments are encoded.
        case_id = str(assessment_case_id).strip()
        if not case_id:
            raise ValueError("assessment_case_id must be a non-empty string")
        return self._client.delete(
            f"/assessments/{key}/cases/remove/",
            json={"assessment_case_id": case_id},
        )
