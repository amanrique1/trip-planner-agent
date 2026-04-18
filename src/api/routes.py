from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request, status

from agents.trip_planner import TripPlannerAgent
from api.auth import authenticate_basic, create_access_token, get_current_user
from api.models import ErrorResponse, TokenResponse, TripRequest, TripResponse
from config import get_settings
from security.audit import (
    log_error,
    log_request,
    log_response,
    log_security_event,
    new_request_id,
)
from security.filters import filter_input, filter_output, sanitize_output
from security.rate_limiter import rate_limiter

settings = get_settings()
router = APIRouter()

# Auth
@router.post(
    "/auth/token",
    response_model=TokenResponse,
    summary="Exchange HTTP Basic credentials for a JWT bearer token",
    tags=["Auth"],
)
def login(username: str = Depends(authenticate_basic)) -> TokenResponse:
    token = create_access_token(username)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_expire_minutes,
    )


# Planning
agent = TripPlannerAgent()


async def _resolve_session(user_id: str, session_id: str | None) -> str:
    """
    Return a valid session_id.
    - If *session_id* is provided, verify it exists; if not, raise 404.
    - If *session_id* is None, create a brand-new session.
    """
    if session_id:
        try:
            await agent.session_service.get_session(
                app_name=agent.APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            return session_id
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found. "
                       f"Omit session_id to start a new conversation.",
            )
    # No session_id supplied → create one
    return await agent.create_session(user_id)


@router.post(
    "/plan",
    response_model=TripResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Generate a full trip itinerary",
    tags=["Planning"],
)
async def plan_trip(
    body: TripRequest,
    request: Request,
    username: str = Depends(get_current_user),
) -> TripResponse:
    request_id = new_request_id()
    t0 = time.perf_counter()

    # Rate limiting
    allowed, retry_after = rate_limiter.is_allowed(username)
    if not allowed:
        log_security_event(
            request_id=request_id,
            username=username,
            event_type="rate_limit_exceeded",
            detail=f"retry_after={retry_after}s",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    # Input filter
    input_result = filter_input(body.query)
    if not input_result.passed:
        log_security_event(
            request_id=request_id,
            username=username,
            event_type="input_blocked",
            detail=input_result.reason,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=input_result.reason,
        )

    log_request(
        request_id=request_id,
        username=username,
        endpoint="/plan",
        user_input=body.query,
    )

    # Resolve / create session
    try:
        session_id = await _resolve_session(username, body.session_id)
    except HTTPException:
        raise
    except Exception as exc:
        log_error(request_id=request_id, username=username, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialise session.",
        ) from exc

    # Run agent
    try:
        events = await agent.run(
            user_id=username,
            session_id=session_id,
            message=body.query,
        )

        final_output = ""
        async for event in events:
            if hasattr(event, "content") and event.content:
                final_output = str(event.content)

    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000
        log_error(
            request_id=request_id,
            username=username,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent execution failed. Try again later.",
        ) from exc

    # Output filter
    output_result = filter_output(final_output)
    if not output_result.passed:
        log_security_event(
            request_id=request_id,
            username=username,
            event_type="output_sanitized",
            detail=output_result.reason,
        )
        final_output = sanitize_output(final_output)

    latency_ms = (time.perf_counter() - t0) * 1000
    log_response(
        request_id=request_id,
        username=username,
        status="success",
        output_preview=final_output,
        latency_ms=latency_ms,
    )

    return TripResponse(
        request_id=request_id,
        session_id=session_id,
        itinerary=final_output,
        latency_ms=latency_ms,
    )


# Health
@router.get("/health", tags=["Ops"], summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}