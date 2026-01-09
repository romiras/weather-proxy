# Implementation Guide: Prometheus Metrics

**Status**: Draft
**Objective**: Enable observability by exposing a `/metrics` endpoint compatible with Prometheus.

## 1. Selected Solution
We will use **[prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)**.
*   **Why**: It is the standard, easy-to-integrate wrapper for FastAPI that provides default metrics (latency, request count, status codes) with minimal configuration.
*   **Key Features**:
    *   Automatic caching of metrics.
    *   Exposes `/metrics` endpoint.
    *   Tracks HTTP request duration (histogram) and counts (counter).

## 2. Implementation Steps

### Step 1: Add Dependency
Add the package using `uv`:

```bash
uv add prometheus-fastapi-instrumentator
```

### Step 2: Update `main.py`
Initialize the instrumentator and expose the endpoint. This should be done **after** the `FastAPI` app creation.

**File:** `main.py`

```python
from prometheus_fastapi_instrumentator import Instrumentator

# ... existing imports and app creation ...

app = FastAPI(title="Weather Proxy", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TraceIdMiddleware)

# --- ADD THIS SECTION ---
# Instrument the app to collect metrics
instrumentator = Instrumentator().instrument(app)

# Expose the /metrics endpoint
instrumentator.expose(app)
# ------------------------

# ... rest of the file ...
```

### Step 3: Verification
1.  **Start the app**:
    ```bash
    uv run uvicorn main:app --reload
    ```

2.  **Generate Traffic**:
    ```bash
    curl "http://localhost:8000/weather?city=London"
    curl "http://localhost:8000/weather?city=Paris"
    curl "http://localhost:8000/health"
    ```

3.  **Check Metrics**:
    ```bash
    curl http://localhost:8000/metrics
    ```
    *Expected Output*: A list of Prometheus-formatted metrics, including:
    *   `http_request_duration_seconds_bucket`
    *   `http_request_duration_seconds_count`
    *   `http_requests_total`

## 3. Advanced Configuration (Future Scope)
Once the base integration is working, consider adding custom metrics to tracking domain-specific events:

*   **Cache Hits/Misses**: Track `weather_cache_hits_total` inside `RedisCacheAdapter`.
*   **Provider Errors**: Track `weather_provider_errors_total` inside `OpenMeteoProvider`.

This can be done using the standard `prometheus_client` library (which is a dependency of the instrumentator).
