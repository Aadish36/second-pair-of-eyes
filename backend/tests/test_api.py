"""API endpoint tests using static-analysis sample source."""


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "second-pair-of-eyes-api"}


def test_submit_retrieve_and_list_pull_request(client):
    response = client.post(
        "/api/reviews",
        json={
            "code": "def greet():\n    return missing_name\n",
            "filename": "sample.py",
            "pull_request_number": 42,
            "title": "Add greeting",
        },
    )
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["status"] == "completed"
    assert result["ai_review_status"] == "completed"
    assert result["ai_review_message"] is not None
    assert result["issue_count"] == len(result["issues"])
    assert any(issue["issue_type"] == "undefined-variable" for issue in result["issues"])
    assert all({"issue_type", "severity", "line_number", "message", "suggested_next_step"} <= issue.keys() for issue in result["issues"])
    assert all(issue["explanation"] and issue["risk"] and issue["fix_guidance"] for issue in result["issues"])
    assert all(issue["historical_examples"] == [] for issue in result["issues"])
    assert all(issue["history_message"] == "No relevant historical example was found." for issue in result["issues"])

    retrieved = client.get(f"/api/reviews/{result['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json() == result

    pull_requests = client.get("/api/pull-requests")
    assert pull_requests.status_code == 200
    assert pull_requests.json()["total"] == 1
    assert pull_requests.json()["items"][0]["number"] == 42


def test_invalid_request_is_rejected(client):
    response = client.post("/api/reviews", json={"code": "", "unknown": True})
    assert response.status_code == 422


def test_missing_review_returns_404(client):
    response = client.get("/api/reviews/does-not-exist")
    assert response.status_code == 404


def test_swagger_openapi_is_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/reviews" in response.json()["paths"]
