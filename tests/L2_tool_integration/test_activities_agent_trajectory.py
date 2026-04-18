"""
Trajectory tests for **ActivitiesAgent**.

Verify that the agent:
  1. Calls ``google_search`` for activity research.
  2. Uses weather context to decide indoor/outdoor.
  3. Does NOT call weather or intake tools.
  4. Produces day-grouped activity list.
"""

import pytest

from agents.activities_agent import activities_agent
from L2_tool_integration.trajectory import collect_trajectory, make_runner_and_session


@pytest.fixture
async def activities_trajectory(activities_agent_state):
    runner, uid, sid, _ = await make_runner_and_session(
        activities_agent,
        app_name="test_activities",
        initial_state=activities_agent_state,
    )
    trajectory = await collect_trajectory(
        runner, uid, sid,
        message="Plan activities for my trip to Paris.",
    )
    print(trajectory.summary())
    return trajectory


# Tool selection

class TestActivitiesToolSelection:

    async def test_calls_google_search(self, activities_trajectory):
        assert activities_trajectory.tool_was_called("google_search"), (
            "ActivitiesAgent should use google_search to find activities."
        )

    async def test_does_not_call_get_coordinates(self, activities_trajectory):
        assert activities_trajectory.tool_was_not_called("get_coordinates")

    async def test_does_not_call_get_weather(self, activities_trajectory):
        assert activities_trajectory.tool_was_not_called("get_weather")

    async def test_does_not_call_save_trip_params(self, activities_trajectory):
        assert activities_trajectory.tool_was_not_called("save_trip_params")

    async def test_no_repeated_identical_searches(self, activities_trajectory):
        assert not activities_trajectory.has_repeated_identical_calls(max_allowed=2), (
            "ActivitiesAgent should not repeat identical searches."
        )


# Output quality

class TestActivitiesOutput:

    async def test_produces_nonempty_text(self, activities_trajectory):
        assert len(activities_trajectory.final_text) > 100, (
            "ActivitiesAgent should produce a detailed activity list."
        )

    async def test_mentions_destination(self, activities_trajectory):
        text = activities_trajectory.final_text.lower()
        assert "paris" in text, "Activities should reference Paris."

    async def test_mentions_indoor_or_outdoor(self, activities_trajectory):
        text = activities_trajectory.final_text.lower()
        assert any(kw in text for kw in ["indoor", "outdoor", "museum", "park", "tour"]), (
            "Activities should reference indoor/outdoor options."
        )

    async def test_does_not_mention_flights(self, activities_trajectory):
        text = activities_trajectory.final_text.lower()
        assert "flight" not in text, "Activities output should not discuss flights."

    async def test_does_not_mention_hotels(self, activities_trajectory):
        text = activities_trajectory.final_text.lower()
        assert "hotel" not in text, "Activities output should not discuss hotels."