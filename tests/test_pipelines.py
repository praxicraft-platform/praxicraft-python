from __future__ import annotations

from praxicraft import Client


def test_pipeline_enroll(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/pipelines/grad-2025/enroll/",
        status_code=201,
        json={
            "enrollment_id": "11111111-1111-1111-1111-111111111111",
            "status": "in_progress",
            "current_stage": 0,
        },
        match_json={"email": "alex@example.com", "name": "Alex Lee", "send_email": True},
    )
    data = client.pipelines.enroll(
        "grad-2025",
        email="alex@example.com",
        name="Alex Lee",
        send_email=True,
    )
    assert data["status"] == "in_progress"


def test_pipeline_list_retrieve_bulk_and_enrollment(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    enrollment_id = "11111111-1111-1111-1111-111111111111"

    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/pipelines/",
        json={"results": [{"slug": "grad-2025", "stage_count": 3}]},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/pipelines/grad-2025/",
        json={"slug": "grad-2025", "stages": []},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/pipelines/grad-2025/enroll/bulk/",
        json={"enrolled": [{"email": "a@example.com"}], "skipped": []},
        match_json={"candidates": [{"email": "a@example.com"}], "send_email": False},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"https://assess.example.com/api/v1/public/pipelines/enrollments/{enrollment_id}/",
        json={"enrollment_id": enrollment_id, "status_code": "in_progress"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/pipelines/grad-2025/enrollments/",
        json={"results": [{"id": enrollment_id}]},
    )

    assert client.pipelines.list()["results"][0]["slug"] == "grad-2025"
    assert client.pipelines.retrieve("grad-2025")["slug"] == "grad-2025"
    bulk = client.pipelines.bulk_enroll(
        "grad-2025",
        [{"email": "a@example.com"}],
        send_email=False,
    )
    assert len(bulk["enrolled"]) == 1
    assert client.pipelines.get_enrollment(enrollment_id)["status_code"] == "in_progress"
    assert client.pipelines.list_enrollments("grad-2025")["results"][0]["id"] == enrollment_id
