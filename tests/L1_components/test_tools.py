import pytest
from unittest.mock import patch, MagicMock
from agents.utils.tools import _get_coordinates_tool as get_coordinates, _get_weather_tool as get_weather, _save_trip_params_tool as save_trip_params


# Helper

def _mock_tool_context():
    """Return a mock ToolContext whose .state behaves like a plain dict."""
    ctx = MagicMock()
    ctx.state = {}
    return ctx


#####################################
########## Get Coordinates ##########
#####################################
class TestGetCoordinates:

    @patch("agents.utils.tools.requests.get")
    def test_success_returns_lat_long_name(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [
                {"latitude": 37.7749, "longitude": -122.4194, "name": "San Francisco"}
            ]
        }
        mock_get.return_value = mock_resp

        result = get_coordinates("San Francisco")

        assert result == {"lat": 37.7749, "long": -122.4194, "name": "San Francisco"}

    @patch("agents.utils.tools.requests.get")
    def test_calls_geocoding_api_with_city(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"latitude": 0, "longitude": 0, "name": "X"}]
        }
        mock_get.return_value = mock_resp

        get_coordinates("Tokyo")

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "geocoding-api.open-meteo.com" in args[0]
        assert kwargs["params"]["name"] == "Tokyo"
        assert kwargs["params"]["count"] == 1
        assert kwargs["timeout"] == 10

    @patch("agents.utils.tools.requests.get")
    def test_strips_text_after_comma(self, mock_get):
        """'Paris, France' → query should be 'Paris'."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"latitude": 48.85, "longitude": 2.35, "name": "Paris"}]
        }
        mock_get.return_value = mock_resp

        get_coordinates("Paris, France")

        _, kwargs = mock_get.call_args
        assert kwargs["params"]["name"] == "Paris"

    @patch("agents.utils.tools.requests.get")
    def test_strips_whitespace(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"latitude": 0, "longitude": 0, "name": "Rome"}]
        }
        mock_get.return_value = mock_resp

        get_coordinates("  Rome  , Italy ")

        _, kwargs = mock_get.call_args
        assert kwargs["params"]["name"] == "Rome"

    @patch("agents.utils.tools.requests.get")
    def test_empty_results_returns_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_get.return_value = mock_resp

        result = get_coordinates("Atlantis")

        assert "error" in result
        assert "No results for" in result["error"]
        assert "Atlantis" in result["error"]

    @patch("agents.utils.tools.requests.get")
    def test_missing_results_key_returns_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_get.return_value = mock_resp

        result = get_coordinates("Nowhere")

        assert "error" in result

    @patch("agents.utils.tools.requests.get")
    def test_http_error_propagates(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("503 Service Unavailable")
        mock_get.return_value = mock_resp

        with pytest.raises(Exception, match="503"):
            get_coordinates("Berlin")

    @patch("agents.utils.tools.requests.get")
    def test_network_timeout_propagates(self, mock_get):
        mock_get.side_effect = Exception("Connection timed out")

        with pytest.raises(Exception, match="timed out"):
            get_coordinates("London")

    @patch("agents.utils.tools.requests.get")
    def test_raise_for_status_is_called(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_get.return_value = mock_resp

        get_coordinates("Lima")

        mock_resp.raise_for_status.assert_called_once()


#####################################
############ Get Weather ############
#####################################

SAMPLE_WEATHER_API_RESPONSE = {
    "current_weather": {"temperature": 20, "weathercode": 0},
    "daily": {
        "temperature_2m_max": [22, 23, 25, 21, 24, 26, 22],
        "temperature_2m_min": [15, 16, 17, 14, 15, 18, 14],
        "weathercode": [0, 1, 2, 51, 3, 0, 61],
        "time": [
            "2025-06-10", "2025-06-11", "2025-06-12", "2025-06-13",
            "2025-06-14", "2025-06-15", "2025-06-16",
        ],
    },
}


class TestGetWeather:

    @patch("agents.utils.tools.requests.get")
    def test_success_returns_full_api_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_WEATHER_API_RESPONSE
        mock_get.return_value = mock_resp

        ctx = _mock_tool_context()
        result = get_weather(48.85, 2.35, ctx)

        assert result == SAMPLE_WEATHER_API_RESPONSE

    @patch("agents.utils.tools.requests.get")
    def test_writes_weather_raw_to_state(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_WEATHER_API_RESPONSE
        mock_get.return_value = mock_resp

        ctx = _mock_tool_context()
        get_weather(48.85, 2.35, ctx)

        assert "weather_raw" in ctx.state
        raw = ctx.state["weather_raw"]
        assert raw["daily_max"] == SAMPLE_WEATHER_API_RESPONSE["daily"]["temperature_2m_max"]
        assert raw["daily_min"] == SAMPLE_WEATHER_API_RESPONSE["daily"]["temperature_2m_min"]
        assert raw["weather_codes"] == SAMPLE_WEATHER_API_RESPONSE["daily"]["weathercode"]
        assert raw["dates"] == SAMPLE_WEATHER_API_RESPONSE["daily"]["time"]

    @patch("agents.utils.tools.requests.get")
    def test_passes_correct_query_params(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_WEATHER_API_RESPONSE
        mock_get.return_value = mock_resp

        ctx = _mock_tool_context()
        get_weather(37.77, -122.42, ctx)

        _, kwargs = mock_get.call_args
        p = kwargs["params"]
        assert p["latitude"] == 37.77
        assert p["longitude"] == -122.42
        assert p["current_weather"] is True
        assert p["forecast_days"] == 7
        assert "temperature_2m_max" in p["daily"]
        assert "temperature_2m_min" in p["daily"]
        assert "weathercode" in p["daily"]

    @patch("agents.utils.tools.requests.get")
    def test_calls_forecast_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_WEATHER_API_RESPONSE
        mock_get.return_value = mock_resp

        ctx = _mock_tool_context()
        get_weather(0.0, 0.0, ctx)

        args, kwargs = mock_get.call_args
        assert "api.open-meteo.com/v1/forecast" in args[0]
        assert kwargs["timeout"] == 10

    @patch("agents.utils.tools.requests.get")
    def test_raise_for_status_is_called(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_WEATHER_API_RESPONSE
        mock_get.return_value = mock_resp

        ctx = _mock_tool_context()
        get_weather(0.0, 0.0, ctx)

        mock_resp.raise_for_status.assert_called_once()

    @patch("agents.utils.tools.requests.get")
    def test_http_error_propagates(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("HTTP 500")
        mock_get.return_value = mock_resp

        ctx = _mock_tool_context()
        with pytest.raises(Exception, match="HTTP 500"):
            get_weather(48.85, 2.35, ctx)

    @patch("agents.utils.tools.requests.get")
    def test_network_timeout_propagates(self, mock_get):
        mock_get.side_effect = Exception("Read timed out")

        ctx = _mock_tool_context()
        with pytest.raises(Exception, match="timed out"):
            get_weather(48.85, 2.35, ctx)

    @patch("agents.utils.tools.requests.get")
    def test_state_not_written_on_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("fail")
        mock_get.return_value = mock_resp

        ctx = _mock_tool_context()
        with pytest.raises(Exception):
            get_weather(0.0, 0.0, ctx)

        assert "weather_raw" not in ctx.state


#####################################
########## Save Trip Params #########
#####################################

class TestSaveTripParams:

    def test_writes_all_keys_to_state(self):
        ctx = _mock_tool_context()

        save_trip_params(
            origin="New York",
            destination="Paris",
            start_date="2025-06-10",
            end_date="2025-06-17",
            tool_context=ctx,
        )

        assert ctx.state["origin"] == "New York"
        assert ctx.state["destination"] == "Paris"
        assert ctx.state["start_date"] == "2025-06-10"
        assert ctx.state["end_date"] == "2025-06-17"
        assert ctx.state["dates"] == "2025-06-10 to 2025-06-17"

    def test_returns_confirmation_with_status(self):
        ctx = _mock_tool_context()

        result = save_trip_params(
            origin="NYC",
            destination="Tokyo",
            start_date="2025-07-01",
            end_date="2025-07-10",
            tool_context=ctx,
        )

        assert result["status"] == "success"
        assert "Saved trip" in result["message"]

    def test_dates_format(self):
        ctx = _mock_tool_context()

        save_trip_params(
            origin="A",
            destination="B",
            start_date="2025-12-25",
            end_date="2026-01-02",
            tool_context=ctx,
        )

        assert ctx.state["dates"] == "2025-12-25 to 2026-01-02"

    def test_exactly_five_keys_written(self):
        ctx = _mock_tool_context()

        save_trip_params(
            origin="A",
            destination="B",
            start_date="2025-01-01",
            end_date="2025-01-05",
            tool_context=ctx,
        )

        expected_keys = {"origin", "destination", "start_date", "end_date", "dates", "trip_params_summary"}
        assert set(ctx.state.keys()) == expected_keys