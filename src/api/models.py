from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class TripRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=10,
        max_length=1_000,
        description="Natural-language travel planning request.",
        examples=["Plan a 5-day trip to Paris from Bogotá in July."],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional: pass an existing session ID to continue a conversation.",
    )


class TripResponse(BaseModel):
    request_id: str
    session_id: str
    itinerary: str
    latency_ms: float


class ErrorResponse(BaseModel):
    request_id: str
    detail: str
    code: str