"""
Trajectory tests for **FlightAgent**.

Verify that the agent:
  1. Calls ``google_search`` at least once.
  2. Does NOT call weather or intake tools.
  3. Produces flight-related output.
"""

import pytest

from agents.flight_agent import flight_agent
from L2_tool_integration.trajectory import collect_trajectory, make_runner_and_session


@pytest.fixture
async def flight_trajectory(flight_agent_state):
    runner, uid, sid, _ = await make_runner_and_session(
        flight_agent,
        app_name="test_flight",
        initial_state=flight_agent_state,
    )
    trajectory = await collect_trajectory(
        runner, uid, sid,
        message="Find flights from New York to Paris for June 10-17.",
    )
    print(trajectory.summary())
    return trajectory


# Tool selection

class TestFlightToolSelection:

    async def test_calls_google_search(self, flight_trajectory):
        assert flight_trajectory.tool_was_called("google_search"), (
            "FlightAgent should use google_search to find flights."
        )

    async def test_does_not_call_get_coordinates(self, flight_trajectory):
        assert flight_trajectory.tool_was_not_called("get_coordinates")

    async def test_does_not_call_get_weather(self, flight_trajectory):
        assert flight_trajectory.tool_was_not_called("get_weather")

    async def test_does_not_call_save_trip_params(self, flight_trajectory):
        assert flight_trajectory.tool_was_not_called("save_trip_params")

    async def test_no_excessive_search_calls(self, flight_trajectory):
        count = flight_trajectory.tool_call_count("google_search")
        assert count <= 5, f"Expected ≤5 google_search calls, got {count}."


# Output quality

class TestFlightOutput:

    async def test_produces_nonempty_text(self, flight_trajectory):
        assert len(flight_trajectory.final_text) > 50, (
            "FlightAgent should produce a substantive flight summary."
        )

    async def test_mentions_flight_keywords(self, flight_trajectory):
        text = flight_trajectory.final_text.lower()
        assert any(kw in text for kw in ["flight", "airline", "direct", "connecting"]), (
            "Output should contain flight-related keywords."
        )

    async def test_does_not_mention_weather(self, flight_trajectory):
        text = flight_trajectory.final_text.lower()
        assert "forecast" not in text, "Flight output should not discuss weather."

    async def test_mentions_origin_or_destination(self, flight_trajectory):
        text = flight_trajectory.final_text.lower()
        assert "paris" in text or "new york" in text, (
            "Output should reference the origin or destination."
        )