"""Tests for OpenMeteo weather provider infrastructure."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from circuitbreaker import CircuitBreakerError

from core.domain.exceptions import CityNotFound, ServiceUnavailable
from core.domain.models import WeatherEntity
from infra.open_meteo import OpenMeteoProvider


@pytest.fixture
def mock_geo_response():
    """Mock geocoding API response."""
    return {
        "results": [
            {
                "name": "London",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "timezone": "Europe/London",
            }
        ]
    }


@pytest.fixture
def mock_weather_response():
    """Mock weather API response."""
    return {
        "current": {
            "temperature_2m": 15.5,
            "relative_humidity_2m": 65,
        },
        "hourly": {
            "time": [
                "2026-01-09T12:00",
                "2026-01-09T13:00",
                "2026-01-09T14:00",
                "2026-01-09T15:00",
                "2026-01-09T16:00",
            ],
            "temperature_2m": [15.5, 16.0, 16.5, 16.0, 15.5],
        },
    }


@pytest.fixture
def mock_async_client():
    """Create a properly mocked async httpx client."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.mark.asyncio
async def test_get_weather_success(mock_geo_response, mock_weather_response, mock_async_client):
    """Test successful weather fetch from OpenMeteo."""
    # Mock geocoding response
    geo_resp = MagicMock()
    geo_resp.json.return_value = mock_geo_response
    geo_resp.raise_for_status = MagicMock()

    # Mock weather response
    weather_resp = MagicMock()
    weather_resp.json.return_value = mock_weather_response
    weather_resp.raise_for_status = MagicMock()

    # Configure mock client to return appropriate responses
    mock_async_client.get = AsyncMock(side_effect=[geo_resp, weather_resp])

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()
        result = await provider.get_weather("London")

    assert isinstance(result, WeatherEntity)
    assert result.city == "London"
    assert result.temperature == 15.5
    assert result.humidity == 65
    assert len(result.forecast) == 5
    assert result.forecast[0]["time"] == "2026-01-09T12:00"
    assert result.forecast[0]["temperature"] == 15.5


@pytest.mark.asyncio
async def test_get_weather_city_not_found(mock_async_client):
    """Test handling of city not found in geocoding."""
    # Mock empty geocoding response
    geo_resp = MagicMock()
    geo_resp.json.return_value = {"results": []}  # Empty results
    geo_resp.raise_for_status = MagicMock()

    mock_async_client.get = AsyncMock(return_value=geo_resp)

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()

        with pytest.raises(CityNotFound) as exc_info:
            await provider.get_weather("NonExistentCity")

        assert "NonExistentCity" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_weather_missing_results_key(mock_async_client):
    """Test handling of malformed geocoding response."""
    # Mock response without 'results' key
    geo_resp = MagicMock()
    geo_resp.json.return_value = {}
    geo_resp.raise_for_status = MagicMock()

    mock_async_client.get = AsyncMock(return_value=geo_resp)

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()

        with pytest.raises(CityNotFound):
            await provider.get_weather("SomeCity")


@pytest.mark.asyncio
async def test_get_weather_geocoding_http_error(mock_async_client):
    """Test handling of HTTP error during geocoding."""
    # Mock HTTP error response
    geo_resp = MagicMock()
    geo_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error", request=MagicMock(), response=MagicMock()
    )

    mock_async_client.get = AsyncMock(return_value=geo_resp)

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()

        with pytest.raises(httpx.HTTPStatusError):
            await provider.get_weather("London")


@pytest.mark.asyncio
async def test_get_weather_api_http_error(mock_geo_response, mock_async_client):
    """Test handling of HTTP error during weather fetch."""
    # Mock successful geocoding
    geo_resp = MagicMock()
    geo_resp.json.return_value = mock_geo_response
    geo_resp.raise_for_status = MagicMock()

    # Mock weather API error
    weather_resp = MagicMock()
    weather_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "503 Service Unavailable", request=MagicMock(), response=MagicMock()
    )

    mock_async_client.get = AsyncMock(side_effect=[geo_resp, weather_resp])

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()

        with pytest.raises(httpx.HTTPStatusError):
            await provider.get_weather("London")


@pytest.mark.asyncio
async def test_get_weather_circuit_breaker_open():
    """Test that circuit breaker raises ServiceUnavailable when open."""
    provider = OpenMeteoProvider()

    with patch.object(
        provider, "_get_weather_impl", side_effect=CircuitBreakerError("Circuit open")
    ):
        with pytest.raises(ServiceUnavailable) as exc_info:
            await provider.get_weather("London")

        assert "Weather Provider" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_weather_with_minimal_forecast(mock_geo_response, mock_async_client):
    """Test handling of weather response with fewer than 5 forecast hours."""
    # Mock geocoding response
    geo_resp = MagicMock()
    geo_resp.json.return_value = mock_geo_response
    geo_resp.raise_for_status = MagicMock()

    # Mock weather response with only 2 hours
    weather_resp = MagicMock()
    weather_resp.json.return_value = {
        "current": {
            "temperature_2m": 20.0,
            "relative_humidity_2m": 70,
        },
        "hourly": {
            "time": ["2026-01-09T12:00", "2026-01-09T13:00"],
            "temperature_2m": [20.0, 20.5],
        },
    }
    weather_resp.raise_for_status = MagicMock()

    mock_async_client.get = AsyncMock(side_effect=[geo_resp, weather_resp])

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()
        result = await provider.get_weather("SmallCity")

    assert len(result.forecast) == 2  # Should handle fewer hours


@pytest.mark.asyncio
async def test_get_weather_with_no_forecast(mock_geo_response, mock_async_client):
    """Test handling of weather response without forecast data."""
    # Mock geocoding response
    geo_resp = MagicMock()
    geo_resp.json.return_value = mock_geo_response
    geo_resp.raise_for_status = MagicMock()

    # Mock weather response without hourly data
    weather_resp = MagicMock()
    weather_resp.json.return_value = {
        "current": {
            "temperature_2m": 18.0,
            "relative_humidity_2m": 55,
        },
        "hourly": {},  # Empty hourly
    }
    weather_resp.raise_for_status = MagicMock()

    mock_async_client.get = AsyncMock(side_effect=[geo_resp, weather_resp])

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()
        result = await provider.get_weather("CityWithoutForecast")

    assert result.forecast == []  # Should handle missing forecast gracefully


@pytest.mark.asyncio
async def test_get_weather_with_missing_current_data(mock_geo_response, mock_async_client):
    """Test handling of weather response with missing current data."""
    # Mock geocoding response
    geo_resp = MagicMock()
    geo_resp.json.return_value = mock_geo_response
    geo_resp.raise_for_status = MagicMock()

    # Mock weather response with missing current fields
    weather_resp = MagicMock()
    weather_resp.json.return_value = {
        "current": {},  # Missing temperature and humidity
        "hourly": {
            "time": ["2026-01-09T12:00"],
            "temperature_2m": [15.0],
        },
    }
    weather_resp.raise_for_status = MagicMock()

    mock_async_client.get = AsyncMock(side_effect=[geo_resp, weather_resp])

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()
        result = await provider.get_weather("City")

    # Should use default values (0.0) for missing data
    assert result.temperature == 0.0
    assert result.humidity == 0.0


@pytest.mark.asyncio
async def test_geocoding_api_parameters(mock_async_client):
    """Test that geocoding API is called with correct parameters."""
    geo_resp = MagicMock()
    geo_resp.json.return_value = {
        "results": [
            {
                "name": "Paris",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "timezone": "Europe/Paris",
            }
        ]
    }
    geo_resp.raise_for_status = MagicMock()

    weather_resp = MagicMock()
    weather_resp.json.return_value = {
        "current": {"temperature_2m": 10.0, "relative_humidity_2m": 80},
        "hourly": {"time": [], "temperature_2m": []},
    }
    weather_resp.raise_for_status = MagicMock()

    mock_async_client.get = AsyncMock(side_effect=[geo_resp, weather_resp])

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()
        await provider.get_weather("Paris")

    # Check geocoding call
    geo_call = mock_async_client.get.call_args_list[0]
    assert provider.geo_base_url in geo_call[0]
    geo_params = geo_call[1]["params"]
    assert geo_params["name"] == "Paris"
    assert geo_params["count"] == 1
    assert geo_params["language"] == "en"
    assert geo_params["format"] == "json"


@pytest.mark.asyncio
async def test_weather_api_parameters(mock_geo_response, mock_async_client):
    """Test that weather API is called with correct parameters."""
    geo_resp = MagicMock()
    geo_resp.json.return_value = mock_geo_response
    geo_resp.raise_for_status = MagicMock()

    weather_resp = MagicMock()
    weather_resp.json.return_value = {
        "current": {"temperature_2m": 15.0, "relative_humidity_2m": 60},
        "hourly": {"time": [], "temperature_2m": []},
    }
    weather_resp.raise_for_status = MagicMock()

    mock_async_client.get = AsyncMock(side_effect=[geo_resp, weather_resp])

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        provider = OpenMeteoProvider()
        await provider.get_weather("London")

    # Check weather API call
    weather_call = mock_async_client.get.call_args_list[1]
    assert provider.weather_base_url in weather_call[0]
    weather_params = weather_call[1]["params"]
    assert weather_params["latitude"] == 51.5074
    assert weather_params["longitude"] == -0.1278
    assert weather_params["timezone"] == "Europe/London"
    assert weather_params["current"] == ["temperature_2m", "relative_humidity_2m"]
    assert weather_params["hourly"] == ["temperature_2m"]
    assert weather_params["forecast_days"] == 1
