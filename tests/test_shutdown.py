"""Tests for graceful shutdown behavior."""


import pytest

from infra.cache import RedisCacheAdapter


@pytest.mark.asyncio
async def test_redis_cache_close():
    """Test that Redis cache can be closed gracefully."""
    cache = RedisCacheAdapter("redis://localhost:6379/0")

    # Verify cache can be closed without errors
    await cache.close()

    # Closing again should not raise an error
    await cache.close()


@pytest.mark.asyncio
async def test_redis_cache_operations_and_close():
    """Test that Redis cache operations work and can be closed gracefully."""
    from core.domain.models import WeatherEntity

    cache = RedisCacheAdapter("redis://localhost:6379/0")

    try:
        # Create a test weather entity
        weather = WeatherEntity(
            city="TestCity",
            temperature=20.0,
            humidity=50.0,
            forecast=[{"time": "2026-01-09T12:00", "temperature": 21.0}],
        )

        # Set weather in cache
        await cache.set_weather("testcity", weather)

        # Get weather from cache
        cached = await cache.get_weather("testcity")
        assert cached is not None
        assert cached.city == "TestCity"

    finally:
        # Ensure cache is closed
        await cache.close()
