"""
Trajectory tests for **WeatherAgent**.

Verify that the agent:
  1. Calls ``get_coordinates`` with the destination city.
  2. Calls ``get_weather`` with the lat/long returned by step 1.
  3. Does NOT call tools that belong to other agents.
  4. Produces a textual weather summary.
"""

import pytest

from agents.weather_agent import weather_agent
from L2_tool_integration.trajectory import collect_trajectory, make_runner_and_session


@pytest.fixture
async def weather_trajectory(weather_agent_state):
    """Run WeatherAgent once with pre-seeded state and return the trajectory."""
    runner, uid, sid, _ = await make_runner_and_session(
        weather_agent,
        app_name="test_weather",
        initial_state=weather_agent_state,
    )
    trajectory = await collect_trajectory(
        runner, uid, sid,
        message="What's the weather like in Paris for the next week?",
    )
    print(trajectory.summary())
    return trajectory


# Tool selection

class TestWeatherToolSelection:

    async def test_calls_get_coordinates(self, weather_trajectory):
        assert weather_trajectory.tool_was_called("get_coordinates"), (
            "WeatherAgent should call get_coordinates to resolve the city."
        )

    async def test_calls_get_weather(self, weather_trajectory):
        assert weather_trajectory.tool_was_called("get_weather"), (
            "WeatherAgent should call get_weather after obtaining coordinates."
        )

    async def test_does_not_call_google_search(self, weather_trajectory):
        assert weather_trajectory.tool_was_not_called("google_search"), (
            "WeatherAgent must NOT use google_search."
        )

    async def test_does_not_call_save_trip_params(self, weather_trajectory):
        assert weather_trajectory.tool_was_not_called("save_trip_params"), (
            "WeatherAgent must NOT call save_trip_params."
        )

    async def test_calls_coordinates_before_weather(self, weather_trajectory):
        tools = weather_trajectory.tools_called()
        idx_coord = tools.index("get_coordinates")
        idx_weather = tools.index("get_weather")
        assert idx_coord < idx_weather, (
            "get_coordinates must be called before get_weather."
        )

    async def test_no_excessive_tool_calls(self, weather_trajectory):
        assert weather_trajectory.total_tool_calls() <= 4, (
            f"Expected ≤4 tool calls, got {weather_trajectory.total_tool_calls()}."
        )

    async def test_no_repeated_identical_calls(self, weather_trajectory):
        assert not weather_trajectory.has_repeated_identical_calls(max_allowed=1), (
            "WeatherAgent should not repeat the same call with identical args."
        )


# Tool arguments

class TestWeatherToolArguments:

    async def test_coordinates_receives_city_name(self, weather_trajectory):
        args = weather_trajectory.get_tool_arguments("get_coordinates")
        assert "city" in args, "get_coordinates must receive a 'city' argument."
        assert "paris" in args["city"].lower(), (
            f"Expected 'Paris' in city arg, got '{args['city']}'."
        )

    async def test_weather_receives_numeric_coordinates(self, weather_trajectory):
        args = weather_trajectory.get_tool_arguments("get_weather")
        assert "lat" in args and "long" in args, (
            "get_weather must receive 'lat' and 'long'."
        )
        assert isinstance(args["lat"], (int, float)), "lat must be numeric."
        assert isinstance(args["long"], (int, float)), "long must be numeric."

    async def test_coordinates_are_plausible_for_paris(self, weather_trajectory):
        args = weather_trajectory.get_tool_arguments("get_weather")
        assert 47.0 <= args["lat"] <= 50.0, f"lat {args['lat']} not near Paris"
        assert 1.0 <= args["long"] <= 4.0, f"long {args['long']} not near Paris"


# Output quality

class TestWeatherOutput:

    async def test_produces_nonempty_text(self, weather_trajectory):
        assert len(weather_trajectory.final_text) > 50, (
            "WeatherAgent should produce a substantive weather summary."
        )

    async def test_mentions_temperature(self, weather_trajectory):
        text = weather_trajectory.final_text.lower()
        assert any(kw in text for kw in ["°c", "°f", "temperature", "degrees"]), (
            "The weather summary should mention temperature."
        )

    async def test_mentions_destination(self, weather_trajectory):
        text = weather_trajectory.final_text.lower()
        assert "paris" in text, (
            "The weather summary should mention the destination city."
        )

    async def test_does_not_mention_flights_or_hotels(self, weather_trajectory):
        text = weather_trajectory.final_text.lower()
        assert "flight" not in text, "Weather summary should not mention flights."
        assert "hotel" not in text, "Weather summary should not mention hotels."