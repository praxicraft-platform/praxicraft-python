from __future__ import annotations

from praxicraft import Client


def test_list_assessments(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/",
        json={
            "next": None,
            "previous": None,
            "results": [{"slug": "senior-backend-screen", "status": "active"}],
        },
    )
    data = client.assessments.list()
    assert data["results"][0]["slug"] == "senior-backend-screen"


def test_retrieve_assessment(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/senior-backend-screen/",
        json={"slug": "senior-backend-screen", "title": "Senior Backend Screen"},
    )
    data = client.assessments.retrieve("senior-backend-screen")
    assert data["title"] == "Senior Backend Screen"


def test_create_assessment(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/assessments/create/",
        status_code=201,
        json={"slug": "new-screen", "status": "draft", "title": "New Screen"},
        match_json={"title": "New Screen"},
    )
    data = client.assessments.create(title="New Screen")
    assert data["slug"] == "new-screen"


def test_update_and_activate(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="PATCH",
        url="https://assess.example.com/api/v1/public/assessments/demo/update/",
        json={"slug": "demo", "status": "active", "title": "Demo"},
        match_json={"status": "active"},
    )
    data = client.assessments.activate("demo")
    assert data["status"] == "active"

    httpx_mock.add_response(
        method="PATCH",
        url="https://assess.example.com/api/v1/public/assessments/demo/update/",
        json={"slug": "demo", "passing_score": 75},
        match_json={"passing_score": 75},
    )
    assert client.assessments.update("demo", passing_score=75)["passing_score"] == 75


def test_attach_list_replace_remove_cases(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="POST",
        url="https://assess.example.com/api/v1/public/assessments/demo/cases/attach/",
        json={"attached": 1},
        match_json={"cases": [{"case_id": "case-1", "source": "platform"}]},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/demo/cases/",
        json={"results": [{"id": "row-1"}]},
    )
    httpx_mock.add_response(
        method="PUT",
        url="https://assess.example.com/api/v1/public/assessments/demo/cases/replace/",
        json={"replaced": True},
        match_json={"cases": [{"case_id": "case-2", "source": "org"}]},
    )
    httpx_mock.add_response(
        method="DELETE",
        url="https://assess.example.com/api/v1/public/assessments/demo/cases/remove/",
        status_code=204,
        match_json={"assessment_case_id": "row-1"},
    )

    assert client.assessments.attach_cases(
        "demo",
        cases=[{"case_id": "case-1", "source": "platform"}],
    )["attached"] == 1
    assert client.assessments.list_cases("demo")["results"][0]["id"] == "row-1"
    assert client.assessments.replace_cases(
        "demo",
        [{"case_id": "case-2", "source": "org"}],
    )["replaced"] is True
    assert client.assessments.remove_case("demo", assessment_case_id="row-1") is None
