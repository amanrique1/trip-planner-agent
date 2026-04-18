import pytest
from pydantic import ValidationError
from api.models import TripRequest, TripResponse, TokenResponse

def test_trip_request_validation_success():
    valid_data = {"query": "Plan a 5-day trip to Paris.", "session_id": "123-456"}
    request = TripRequest(**valid_data)
    assert request.query == "Plan a 5-day trip to Paris."
    assert request.session_id == "123-456"

def test_trip_request_validation_invalid():
    # Empty query (too short)
    with pytest.raises(ValidationError):
        TripRequest(query="short")

    # Too long query
    with pytest.raises(ValidationError):
        TripRequest(query="a" * 1001)

def test_trip_response_validation_success():
    valid_data = {
        "request_id": "req-1",
        "session_id": "sess-1",
        "itinerary": "Your plan is...",
        "latency_ms": 123.45
    }
    response = TripResponse(**valid_data)
    assert response.request_id == "req-1"
    assert response.itinerary == "Your plan is..."

def test_token_response_validation():
    valid_data = {"access_token": "abc", "expires_in_minutes": 60}
    token = TokenResponse(**valid_data)
    assert token.access_token == "abc"
    assert token.token_type == "bearer"

def test_trip_response_missing_fields():
    # Missing required field request_id
    with pytest.raises(ValidationError):
        TripResponse(session_id="sess-1", itinerary="...")
