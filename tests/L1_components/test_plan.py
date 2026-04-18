from unittest.mock import patch
from api.routes import rate_limiter

async def mock_run_async(*args, **kwargs):
    """Drop-in async-generator replacing Runner.run_async."""

    class Event:
        content = "Mocked itinerary response"

    yield Event()


PATCH_TARGET = "api.routes.agent.runner.run_async"


# Happy path
def test_post_plan_with_valid_token_and_valid_query(client, valid_auth_headers):
    payload = {"query": "Plan a 5-day trip to Tokyo in May."}

    with patch(PATCH_TARGET, side_effect=mock_run_async):
        response = client.post("/plan", headers=valid_auth_headers, json=payload)

    assert response.status_code == 200, f"/plan request failed: {response.text}"

    plan_json = response.json()
    assert "request_id" in plan_json and plan_json["request_id"]
    assert "session_id" in plan_json and plan_json["session_id"]
    assert "itinerary" in plan_json and plan_json["itinerary"]
    assert "latency_ms" in plan_json


# Missing auth header
def test_post_plan_without_authorization_header(client):
    payload = {"query": "Plan a weekend in NYC."}

    with patch(PATCH_TARGET, side_effect=mock_run_async):
        response = client.post("/plan", json=payload)

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    resp_json = response.json()
    detail = resp_json.get("detail")
    assert detail is not None
    assert (
        "missing" in detail.lower()
        or "invalid" in detail.lower()
        or "token" in detail.lower()
        or "authorization" in detail.lower()
        or detail == "Not authenticated"
    )


# Input filter violation
def test_post_plan_with_input_violating_filters(client, valid_auth_headers):
    violating_query = "A" * 6000
    payload = {"query": violating_query}

    with patch(PATCH_TARGET, side_effect=mock_run_async):
        response = client.post("/plan", headers=valid_auth_headers, json=payload)

    assert response.status_code in (400, 422), (
        f"Expected 400 or 422, got {response.status_code}"
    )

    error_json = response.json()
    assert "detail" in error_json
    assert error_json["detail"]


# Rate-limit exhaustion
def test_post_plan_exceeding_rate_limit(client, valid_auth_headers):
    rate_limiter.reset("admin")

    payload = {"query": "Plan a 1-day trip to Paris."}

    with patch(PATCH_TARGET, side_effect=mock_run_async):
        max_requests = 50
        got_rate_limited = False
        rate_limit_resp = None

        for _ in range(max_requests):
            resp = client.post("/plan", headers=valid_auth_headers, json=payload)
            if resp.status_code == 429:
                got_rate_limited = True
                rate_limit_resp = resp
                break
            assert resp.status_code == 200, (
                f"Unexpected status before rate limit: "
                f"{resp.status_code} - {resp.text}"
            )

        assert got_rate_limited, "Did not receive 429 Too Many Requests"
        assert "Retry-After" in rate_limit_resp.headers

        resp_json = rate_limit_resp.json()
        detail = resp_json.get("detail") or resp_json.get("message") or ""
        assert "rate limit" in detail.lower()

    rate_limiter.reset("admin")


# Internal server error
def test_post_plan_internal_server_error(client, valid_auth_headers):
    rate_limiter.reset("admin")
    payload = {"query": "Plan a 5-day trip to Tokyo in May."}

    async def mock_run_async_error(*args, **kwargs):
        raise Exception("Simulated internal error")
        yield  # noqa: keeps this an async generator so the signature matches

    with patch(PATCH_TARGET, side_effect=mock_run_async_error):
        response = client.post("/plan", headers=valid_auth_headers, json=payload)

    assert response.status_code == 500, (
        f"Expected 500 Internal Server Error, got {response.status_code}"
    )
    error_json = response.json()
    assert isinstance(error_json, dict)
    assert "detail" in error_json