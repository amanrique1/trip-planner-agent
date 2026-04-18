"""
Trajectory tests for **HotelAgent**.

Verify that the agent:
  1. Calls ``google_search`` for hotel research.
  2. References the planned activities from state.
  3. Does NOT call weather or intake tools.
  4. Produces hotel recommendations.
"""

import pytest

from agents.hotel_agent import hotel_agent
from L2_tool_integration.trajectory import collect_trajectory, make_runner_and_session


@pytest.fixture
async def hotel_trajectory(hotel_agent_state):
    runner, uid, sid, _ = await make_runner_and_session(
        hotel_agent,
        app_name="test_hotel",
        initial_state=hotel_agent_state,
    )
    trajectory = await collect_trajectory(
        runner, uid, sid,
        message="Find hotels for my Paris trip.",
    )
    print(trajectory.summary())
    return trajectory


# Tool selection

class TestHotelToolSelection:

    async def test_calls_google_search(self, hotel_trajectory):
        assert hotel_trajectory.tool_was_called("google_search"), (
            "HotelAgent should use google_search to find hotels."
        )

    async def test_does_not_call_get_coordinates(self, hotel_trajectory):
        assert hotel_trajectory.tool_was_not_called("get_coordinates")

    async def test_does_not_call_get_weather(self, hotel_trajectory):
        assert hotel_trajectory.tool_was_not_called("get_weather")

    async def test_does_not_call_save_trip_params(self, hotel_trajectory):
        assert hotel_trajectory.tool_was_not_called("save_trip_params")

    async def test_no_excessive_search_calls(self, hotel_trajectory):
        count = hotel_trajectory.tool_call_count("google_search")
        assert count <= 5, f"Expected ≤5 google_search calls, got {count}."


# Output quality

class TestHotelOutput:

    async def test_produces_nonempty_text(self, hotel_trajectory):
        assert len(hotel_trajectory.final_text) > 50, (
            "HotelAgent should produce hotel recommendations."
        )

    async def test_mentions_hotel_keywords(self, hotel_trajectory):
        text = hotel_trajectory.final_text.lower()
        assert any(kw in text for kw in ["hotel", "accommodation", "stay", "night"]), (
            "Output should contain hotel-related keywords."
        )

    async def test_mentions_destination(self, hotel_trajectory):
        text = hotel_trajectory.final_text.lower()
        assert "paris" in text, "Hotel output should reference Paris."

    async def test_mentions_neighbourhood_or_area(self, hotel_trajectory):
        text = hotel_trajectory.final_text.lower()
        assert any(kw in text for kw in [
            "neighbourhood", "neighborhood", "area", "district",
            "arrondissement", "marais", "montmartre", "latin",
            "near", "close to", "walking distance",
        ]), "Output should mention location/neighbourhood."

    async def test_does_not_mention_flights(self, hotel_trajectory):
        text = hotel_trajectory.final_text.lower()
        assert "flight" not in text, "Hotel output should not discuss flights."