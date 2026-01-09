"""Shared fixtures for pytest."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_cache():
    """Mock CachePort for testing."""
    cache = AsyncMock()
    cache.get.return_value = None
    cache.set.return_value = None
    return cache


@pytest.fixture
def mock_weather_provider():
    """Mock WeatherProviderPort for testing."""
    provider = AsyncMock()
    return provider


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing."""
    return {
        "temperature": 15.5,
        "humidity": 65,
        "wind_speed": 12.3,
        "conditions": "Partly cloudy",
    }
