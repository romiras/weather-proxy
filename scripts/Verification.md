# Verification Scripts

The project includes scripts to verify the integrity of the adapters and the API layer. You can run these scripts to ensure the application is functioning correctly.

## Prerequisites

Ensure you have the dependencies installed:
```bash
uv sync
```

## Running Verification Scripts

### 1. Verify Internal Adapter Logic
This script tests the `OpenMeteoProvider` directly, ensuring that the geocoding and weather fetching logic works as expected without involving the HTTP layer.

```bash
uv run python3 scripts/verify_adapter.py
```

### 2. Verify API & Middleware
This script tests the full HTTP stack, including the FastAPI application and the observability middleware (e.g., `X-Request-ID` headers).

```bash
uv run python3 scripts/verify_middleware.py
```
