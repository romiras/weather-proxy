"""Tests for API middleware components."""

import json
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware import RequestLoggingMiddleware, TraceIdMiddleware


@pytest.fixture
def test_app():
    """Create a test FastAPI app with middleware."""
    app = FastAPI()

    # Add middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TraceIdMiddleware)

    # Add test endpoint
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/test-error")
    async def test_error_endpoint():
        raise ValueError("Test error")

    return app


@pytest.fixture
def client(test_app):
    """FastAPI test client with middleware."""
    return TestClient(test_app)


def test_trace_id_middleware_generates_id(client):
    """Test that TraceIdMiddleware generates request ID when not provided."""
    response = client.get("/test")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    # Verify it's a valid UUID format (36 characters with dashes)
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 36
    assert request_id.count("-") == 4


def test_trace_id_middleware_preserves_provided_id(client):
    """Test that TraceIdMiddleware uses provided X-Request-ID header."""
    custom_id = "custom-request-id-12345"
    response = client.get("/test", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


@patch("api.middleware.logger")
def test_request_logging_middleware_success(mock_logger, client):
    """Test that RequestLoggingMiddleware logs successful requests."""
    response = client.get("/test")

    assert response.status_code == 200

    # Verify logger.info was called
    mock_logger.info.assert_called_once()

    # Parse the logged JSON
    log_call = mock_logger.info.call_args[0][0]
    log_data = json.loads(log_call)

    assert log_data["message"] == "Request processed"
    assert log_data["path"] == "/test"
    assert log_data["method"] == "GET"
    assert log_data["status_code"] == 200
    assert "duration_ms" in log_data
    assert "request_id" in log_data
    assert isinstance(log_data["duration_ms"], (int, float))


@patch("api.middleware.logger")
def test_request_logging_middleware_error(mock_logger, client):
    """Test that RequestLoggingMiddleware logs failed requests."""
    # This should raise an error
    with pytest.raises(ValueError):
        client.get("/test-error")

    # Verify logger.error was called
    mock_logger.error.assert_called_once()

    # Parse the logged JSON
    log_call = mock_logger.error.call_args[0][0]
    log_data = json.loads(log_call)

    assert log_data["message"] == "Request failed"
    assert log_data["path"] == "/test-error"
    assert log_data["method"] == "GET"
    assert "duration_ms" in log_data
    assert "request_id" in log_data
    assert "error" in log_data
    assert "Test error" in log_data["error"]


@patch("api.middleware.logger")
def test_request_logging_includes_timing(mock_logger, client):
    """Test that request logging includes accurate timing information."""
    response = client.get("/test")

    assert response.status_code == 200
    log_call = mock_logger.info.call_args[0][0]
    log_data = json.loads(log_call)

    # Verify duration is a reasonable value (should be very small for test)
    assert log_data["duration_ms"] >= 0
    assert log_data["duration_ms"] < 10000  # Less than 10 seconds


def test_middleware_integration(client):
    """Test that both middlewares work together correctly."""
    custom_id = "integration-test-id"
    response = client.get("/test", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
