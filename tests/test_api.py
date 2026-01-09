"""Integration tests for FastAPI endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from core.domain.exceptions import CityNotFound, ServiceUnavailable
from core.domain.models import WeatherEntity
from main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Mock WeatherService for testing."""
    return AsyncMock()


def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("main.service")
def test_get_weather_success(mock_service_global, client):
    """Test successful weather request."""
    # Setup mock
    mock_weather = WeatherEntity(
        city="London",
        temperature=15.5,
        humidity=65,
        forecast=[
            {"time": "2026-01-09T12:00", "temperature": 14.0},
            {"time": "2026-01-09T13:00", "temperature": 15.0},
        ],
    )
    # Make the async method return the mock weather
    mock_service_global.get_weather = AsyncMock(return_value=mock_weather)

    # Execute
    response = client.get("/weather?city=London")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["city_name"] == "London"
    assert data["current_temperature"] == 15.5
    assert data["current_humidity"] == 65
    assert len(data["hourly_forecast"]) == 2


@patch("main.service")
def test_get_weather_city_not_found(mock_service_global, client):
    """Test weather request for nonexistent city."""
    # Setup mock
    mock_service_global.get_weather = AsyncMock(side_effect=CityNotFound("UnknownCity"))

    # Execute
    response = client.get("/weather?city=UnknownCity")

    # Verify
    assert response.status_code == 404
    assert "UnknownCity" in response.json()["detail"]


@patch("main.service")
def test_get_weather_service_unavailable(mock_service_global, client):
    """Test weather request when service is unavailable."""
    # Setup mock
    mock_service_global.get_weather = AsyncMock(
        side_effect=ServiceUnavailable("Provider temporarily unavailable")
    )

    # Execute
    response = client.get("/weather?city=London")

    # Verify
    assert response.status_code == 503


def test_get_weather_missing_city(client):
    """Test weather request with missing city parameter."""
    response = client.get("/weather")
    assert response.status_code == 422  # Validation error
