"""Tests for graceful shutdown behavior."""

from unittest.mock import AsyncMock, patch

import pytest

from core.domain.models import WeatherEntity
from infra.cache import RedisCacheAdapter


@pytest.mark.asyncio
async def test_redis_cache_close():
    """Test that Redis cache can be closed gracefully."""
    mock_redis = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")

        # Verify cache can be closed without errors
        await cache.close()
        mock_redis.aclose.assert_called_once()

        # Closing again should not raise an error
        await cache.close()
        assert mock_redis.aclose.call_count == 2


@pytest.mark.asyncio
async def test_redis_cache_operations_and_close():
    """Test that Redis cache operations work and can be closed gracefully."""
    import json
    from dataclasses import asdict

    mock_redis = AsyncMock()

    # Create a test weather entity
    weather = WeatherEntity(
        city="TestCity",
        temperature=20.0,
        humidity=50.0,
        forecast=[{"time": "2026-01-09T12:00", "temperature": 21.0}],
    )

    # Mock Redis responses
    weather_json = json.dumps(asdict(weather))
    mock_redis.get = AsyncMock(return_value=weather_json)
    mock_redis.set = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")

        try:
            # Set weather in cache
            await cache.set_weather("testcity", weather)
            mock_redis.set.assert_called_once()

            # Get weather from cache
            cached = await cache.get_weather("testcity")
            assert cached is not None
            assert cached.city == "TestCity"
            assert cached.temperature == 20.0
            mock_redis.get.assert_called_once_with("weather:testcity")

        finally:
            # Ensure cache is closed
            await cache.close()
            mock_redis.aclose.assert_called_once()
