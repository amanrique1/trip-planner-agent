"""
Trajectory tests for **IntakeAgent**.

Verify that the agent:
  1. Calls ``save_trip_params`` exactly once.
  2. Extracts origin, destination, start_date, end_date.
  3. Does NOT call any other tools.
  4. Produces a confirmation message.
"""

import pytest

from agents.intake_agent import intake_agent
from L2_tool_integration.trajectory import collect_trajectory, make_runner_and_session


@pytest.fixture
async def intake_trajectory():
    """Run IntakeAgent with no pre-seeded state (it IS the first agent)."""
    runner, uid, sid, _ = await make_runner_and_session(
        intake_agent,
        app_name="test_intake",
    )
    trajectory = await collect_trajectory(
        runner, uid, sid,
        message="Plan a trip from New York to Paris, June 10 to June 17 2025.",
    )
    print(trajectory.summary())
    return trajectory


@pytest.fixture
async def intake_trajectory_vague():
    """Run IntakeAgent with a vague message to test defaults."""
    runner, uid, sid, _ = await make_runner_and_session(
        intake_agent,
        app_name="test_intake_vague",
    )
    trajectory = await collect_trajectory(
        runner, uid, sid,
        message="I want to visit Tokyo next week.",
    )
    print(trajectory.summary())
    return trajectory


# Tool selection

class TestIntakeToolSelection:

    async def test_calls_save_trip_params(self, intake_trajectory):
        assert intake_trajectory.tool_was_called("save_trip_params"), (
            "IntakeAgent must call save_trip_params."
        )

    async def test_calls_save_trip_params_exactly_once(self, intake_trajectory):
        assert intake_trajectory.tool_call_count("save_trip_params") == 1, (
            "IntakeAgent should call save_trip_params exactly once."
        )

    async def test_does_not_call_weather_tools(self, intake_trajectory):
        assert intake_trajectory.tool_was_not_called("get_coordinates")
        assert intake_trajectory.tool_was_not_called("get_weather")

    async def test_does_not_call_google_search(self, intake_trajectory):
        assert intake_trajectory.tool_was_not_called("google_search")


# Tool arguments

class TestIntakeToolArguments:

    async def test_extracts_origin(self, intake_trajectory):
        args = intake_trajectory.get_tool_arguments("save_trip_params")
        assert "origin" in args
        assert "new york" in args["origin"].lower()

    async def test_extracts_destination(self, intake_trajectory):
        args = intake_trajectory.get_tool_arguments("save_trip_params")
        assert "destination" in args
        assert "paris" in args["destination"].lower()

    async def test_extracts_start_date(self, intake_trajectory):
        args = intake_trajectory.get_tool_arguments("save_trip_params")
        assert "start_date" in args
        assert "2025-06-10" in args["start_date"]

    async def test_extracts_end_date(self, intake_trajectory):
        args = intake_trajectory.get_tool_arguments("save_trip_params")
        assert "end_date" in args
        assert "2025-06-17" in args["end_date"]

    async def test_all_four_params_present(self, intake_trajectory):
        args = intake_trajectory.get_tool_arguments("save_trip_params")
        required = {"origin", "destination", "start_date", "end_date"}
        assert required.issubset(args.keys()), (
            f"Missing keys: {required - args.keys()}"
        )


# Vague input handling

class TestIntakeVagueInput:

    async def test_still_calls_save_trip_params(self, intake_trajectory_vague):
        assert intake_trajectory_vague.tool_was_called("save_trip_params"), (
            "IntakeAgent should call save_trip_params even with vague input."
        )

    async def test_extracts_destination_tokyo(self, intake_trajectory_vague):
        args = intake_trajectory_vague.get_tool_arguments("save_trip_params")
        assert "tokyo" in args["destination"].lower()

    async def test_dates_are_valid_format(self, intake_trajectory_vague):
        args = intake_trajectory_vague.get_tool_arguments("save_trip_params")
        import re
        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        assert re.match(date_pattern, args["start_date"]), (
            f"start_date '{args['start_date']}' is not YYYY-MM-DD."
        )
        assert re.match(date_pattern, args["end_date"]), (
            f"end_date '{args['end_date']}' is not YYYY-MM-DD."
        )


# Output quality

class TestIntakeOutput:

    async def test_produces_confirmation_text(self, intake_trajectory):
        assert len(intake_trajectory.final_text) > 10, (
            "IntakeAgent should produce a confirmation message."
        )

    async def test_confirmation_mentions_destination(self, intake_trajectory):
        text = intake_trajectory.final_text.lower()
        assert "paris" in text, (
            "Confirmation should mention the destination."
        )