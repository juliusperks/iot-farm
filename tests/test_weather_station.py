import json
import pytest
from unittest.mock import patch, MagicMock
from weather_station import GippslandWeatherStation, parse_weather_response


class TestParseWeatherResponse:

    def test_valid_response_returns_dict(self):
        mock_response = {
            "current": {
                "temperature_2m": 8.5,
                "relative_humidity_2m": 72,
                "wind_speed_10m": 15.2,
                "weather_code": 3
            }
        }
        result = parse_weather_response(mock_response)
        assert isinstance(result, dict)

    def test_valid_response_has_required_fields(self):
        mock_response = {
            "current": {
                "temperature_2m": 8.5,
                "relative_humidity_2m": 72,
                "wind_speed_10m": 15.2,
                "weather_code": 3
            }
        }
        result = parse_weather_response(mock_response)
        assert {"temperature", "humidity", "wind_speed", "weather_code"}.issubset(result.keys())

    def test_temperature_is_float(self):
        mock_response = {
            "current": {
                "temperature_2m": 8.5,
                "relative_humidity_2m": 72,
                "wind_speed_10m": 15.2,
                "weather_code": 3
            }
        }
        result = parse_weather_response(mock_response)
        assert isinstance(result["temperature"], float)

    def test_missing_current_key_returns_none(self):
        result = parse_weather_response({})
        assert result is None

    def test_missing_temperature_returns_none(self):
        mock_response = {
            "current": {
                "relative_humidity_2m": 72,
                "wind_speed_10m": 15.2,
                "weather_code": 3
            }
        }
        result = parse_weather_response(mock_response)
        assert result is None

    def test_none_input_returns_none(self):
        result = parse_weather_response(None)
        assert result is None


class TestGippslandWeatherStation:

    @pytest.fixture
    def station(self):
        return GippslandWeatherStation(device_id="gippsland-weather-01")

    def test_station_initialises(self, station):
        assert station is not None
        assert station.device_id == "gippsland-weather-01"

    def test_get_telemetry_returns_none_before_fetch(self, station):
        assert station.get_telemetry() is None

    @patch("weather_station.requests.get")
    def test_fetch_updates_weather(self, mock_get, station):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "current": {
                "temperature_2m": 4.2,
                "relative_humidity_2m": 85,
                "wind_speed_10m": 22.0,
                "weather_code": 61
            }
        }
        station.fetch()
        assert station.current_weather is not None
        assert station.current_weather["temperature"] == 4.2

    @patch("weather_station.requests.get")
    def test_telemetry_has_hash_after_fetch(self, mock_get, station):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "current": {
                "temperature_2m": 4.2,
                "relative_humidity_2m": 85,
                "wind_speed_10m": 22.0,
                "weather_code": 61
            }
        }
        station.fetch()
        payload = station.get_telemetry()
        assert "hash" in payload
        assert len(payload["hash"]) == 64

    @patch("weather_station.requests.get")
    def test_telemetry_has_device_id(self, mock_get, station):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "current": {
                "temperature_2m": 4.2,
                "relative_humidity_2m": 85,
                "wind_speed_10m": 22.0,
                "weather_code": 61
            }
        }
        station.fetch()
        payload = station.get_telemetry()
        assert payload["device_id"] == "gippsland-weather-01"

    @patch("weather_station.requests.get")
    def test_failed_fetch_leaves_weather_unchanged(self, mock_get, station):
        mock_get.side_effect = Exception("network error")
        station.fetch()
        assert station.current_weather is None