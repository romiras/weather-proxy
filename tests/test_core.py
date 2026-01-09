"""Unit tests for WeatherService core logic."""

import pytest

from core.domain.models import WeatherEntity
from core.services import WeatherService


@pytest.mark.asyncio
async def test_get_weather_cache_hit(mock_cache, mock_weather_provider, sample_weather_data):
    """Test that cached weather data is returned without calling the provider."""
    # Setup cached data
    cached_weather = WeatherEntity(
        city="London",
        temperature=sample_weather_data["temperature"],
        humidity=sample_weather_data["humidity"],
        forecast=[],
    )
    mock_cache.get_weather.return_value = cached_weather

    # Create service
    service = WeatherService(provider=mock_weather_provider, cache=mock_cache)

    # Execute
    result = await service.get_weather("London")

    # Verify
    assert result == cached_weather
    mock_cache.get_weather.assert_called_once_with("London")
    mock_weather_provider.get_weather.assert_not_called()


@pytest.mark.asyncio
async def test_get_weather_cache_miss(mock_cache, mock_weather_provider, sample_weather_data):
    """Test that weather is fetched from provider on cache miss and cached."""
    # Setup cache miss
    mock_cache.get_weather.return_value = None

    # Setup provider data
    provider_weather = WeatherEntity(
        city="Paris",
        temperature=sample_weather_data["temperature"],
        humidity=sample_weather_data["humidity"],
        forecast=[],
    )
    mock_weather_provider.get_weather.return_value = provider_weather

    # Create service
    service = WeatherService(provider=mock_weather_provider, cache=mock_cache)

    # Execute
    result = await service.get_weather("Paris")

    # Verify
    assert result == provider_weather
    mock_cache.get_weather.assert_called_once_with("Paris")
    mock_weather_provider.get_weather.assert_called_once_with("Paris")
    mock_cache.set_weather.assert_called_once_with("Paris", provider_weather)
