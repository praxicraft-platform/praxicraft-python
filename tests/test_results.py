from __future__ import annotations

from praxicraft import Client


def test_retrieve_result(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    token = "11111111-1111-1111-1111-111111111111"
    httpx_mock.add_response(
        method="GET",
        url=f"https://assess.example.com/api/v1/public/invites/{token}/result/",
        json={"status": "completed", "score_percentage": 85.0, "passed": True},
    )
    data = client.results.retrieve(token)
    assert data["passed"] is True


def test_list_results(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/demo/results/?page_size=2",
        json={
            "next": "https://assess.example.com/api/v1/public/assessments/demo/results/?cursor=abc&page_size=2",
            "previous": None,
            "results": [{"email": "a@example.com"}],
        },
    )
    data = client.results.list("demo", page_size=2)
    assert data["results"][0]["email"] == "a@example.com"


def test_iter_all_follows_cursor(httpx_mock) -> None:
    client = Client(api_key="ct_live_test", base_url="https://assess.example.com")
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/demo/results/",
        json={
            "next": "https://assess.example.com/api/v1/public/assessments/demo/results/?cursor=page2",
            "results": [{"email": "a@example.com"}],
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="https://assess.example.com/api/v1/public/assessments/demo/results/?cursor=page2",
        json={
            "next": None,
            "results": [{"email": "b@example.com"}],
        },
    )
    rows = list(client.results.iter_all("demo"))
    assert [row["email"] for row in rows] == ["a@example.com", "b@example.com"]
