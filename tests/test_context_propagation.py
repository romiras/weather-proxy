import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware import RequestLoggingMiddleware, TraceIdMiddleware
from infra.request_context import request_id_ctx_var


@pytest.fixture
def test_app():
    """Create a test FastAPI app with middleware."""
    app = FastAPI()

    # Add middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TraceIdMiddleware)

    return app


@pytest.fixture
def client(test_app):
    """FastAPI test client with middleware."""
    return TestClient(test_app)


def test_context_var_propagation(test_app, client):
    """Test that the request ID is propagated via ContextVar."""

    # Define an endpoint that checks the ContextVar
    @test_app.get("/check-context")
    async def check_context():
        return {"request_id": request_id_ctx_var.get()}

    custom_id = "ctx-var-test-id"
    response = client.get("/check-context", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.json()["request_id"] == custom_id
