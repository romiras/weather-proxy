"""Tests for Redis cache adapter infrastructure."""

import json
from dataclasses import asdict
from unittest.mock import AsyncMock, patch

import pytest
from circuitbreaker import CircuitBreakerError

from core.domain.models import WeatherEntity
from infra.cache import RedisCacheAdapter


@pytest.fixture
def sample_weather():
    """Sample weather entity for testing."""
    return WeatherEntity(
        city="TestCity",
        temperature=20.5,
        humidity=65.0,
        forecast=[
            {"time": "2026-01-09T12:00", "temperature": 21.0},
            {"time": "2026-01-09T13:00", "temperature": 22.0},
        ],
    )


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_cache_get_hit(mock_redis, sample_weather):
    """Test cache get operation with cache hit."""
    # Setup mock
    weather_json = json.dumps(asdict(sample_weather))
    mock_redis.get.return_value = weather_json

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")
        result = await cache.get_weather("TestCity")

    assert result is not None
    assert result.city == "TestCity"
    assert result.temperature == 20.5
    assert result.humidity == 65.0
    assert len(result.forecast) == 2
    mock_redis.get.assert_called_once_with("weather:testcity")


@pytest.mark.asyncio
async def test_cache_get_miss(mock_redis):
    """Test cache get operation with cache miss."""
    # Setup mock - return None for cache miss
    mock_redis.get.return_value = None

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")
        result = await cache.get_weather("NonExistentCity")

    assert result is None
    mock_redis.get.assert_called_once_with("weather:nonexistentcity")


@pytest.mark.asyncio
async def test_cache_get_handles_json_decode_error(mock_redis):
    """Test cache get handles invalid JSON gracefully."""
    # Setup mock with invalid JSON
    mock_redis.get.return_value = "invalid-json{["

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")
        # Should return None on error, not raise
        result = await cache.get_weather("TestCity")

    assert result is None


@pytest.mark.asyncio
async def test_cache_get_handles_circuit_breaker_open(mock_redis):
    """Test cache get returns None when circuit breaker is open."""
    # Mock the _get_weather_impl to raise CircuitBreakerError
    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")

        with patch.object(
            cache, "_get_weather_impl", side_effect=CircuitBreakerError("Circuit open")
        ):
            result = await cache.get_weather("TestCity")

    # Should gracefully return None when circuit is open
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_success(mock_redis, sample_weather):
    """Test cache set operation succeeds."""
    mock_redis.set.return_value = True

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")
        await cache.set_weather("TestCity", sample_weather)

    # Verify set was called with correct key, value, and TTL
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][0] == "weather:testcity"

    # Verify the value is valid JSON with correct data
    stored_json = call_args[0][1]
    stored_data = json.loads(stored_json)
    assert stored_data["city"] == "TestCity"
    assert stored_data["temperature"] == 20.5

    # Verify TTL is set (ex parameter)
    assert call_args[1]["ex"] == 3600


@pytest.mark.asyncio
async def test_cache_set_handles_errors_gracefully(mock_redis, sample_weather):
    """Test cache set handles Redis errors without raising."""
    mock_redis.set.side_effect = Exception("Redis connection error")

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")
        # Should not raise, just log warning
        await cache.set_weather("TestCity", sample_weather)

    # Verify set was attempted
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_cache_set_handles_circuit_breaker_open(mock_redis, sample_weather):
    """Test cache set handles circuit breaker gracefully."""
    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")

        with patch.object(
            cache, "_set_weather_impl", side_effect=CircuitBreakerError("Circuit open")
        ):
            # Should not raise exception
            await cache.set_weather("TestCity", sample_weather)


@pytest.mark.asyncio
async def test_cache_key_normalization(mock_redis, sample_weather):
    """Test that city names are normalized to lowercase in keys."""
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")

        # Test various casings
        await cache.get_weather("LONDON")
        mock_redis.get.assert_called_with("weather:london")

        await cache.get_weather("New York")
        mock_redis.get.assert_called_with("weather:new york")

        await cache.set_weather("PARIS", sample_weather)
        assert "weather:paris" in mock_redis.set.call_args[0][0]


@pytest.mark.asyncio
async def test_cache_close_success(mock_redis):
    """Test cache close operation succeeds."""
    mock_redis.aclose.return_value = None

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")
        await cache.close()

    mock_redis.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_cache_close_handles_errors(mock_redis):
    """Test cache close handles errors gracefully."""
    mock_redis.aclose.side_effect = Exception("Close error")

    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")
        # Should not raise
        await cache.close()

    mock_redis.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_cache_ttl_configuration(mock_redis):
    """Test that cache TTL is correctly configured."""
    with patch("infra.cache.redis.from_url", return_value=mock_redis):
        cache = RedisCacheAdapter("redis://localhost:6379/0")

        # Verify default TTL
        assert cache.ttl == 3600  # 1 hour
