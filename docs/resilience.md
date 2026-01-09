# Resilience & Circuit Breaking Implementation

## Overview
To improve the reliability and responsiveness of the Weather Proxy, we have implemented the **Circuit Breaker** pattern. This prevents the application from hanging or wasting resources on downstream services (Redis, Open-Meteo) that are experiencing outages.

## Architecture

We use the `circuitbreaker` library to decorate our outbound adapters. Each adapter manages its own circuit state.

### 1. Redis Cache Resilience (`infra/cache.py`)
- **Threshold**: 3 failures.
- **Recovery Timeout**: 30 seconds.
- **Fail-Fast Logic**: If the breaker is **Open**, calls to `get_weather` or `set_weather` return immediately (treating it as a cache miss or skipping the write).
- **Benefit**: Prevents connection timeouts from slowing down the primary request path when Redis is down.

### 2. Weather Provider Resilience (`infra/open_meteo.py`)
- **Threshold**: 5 failures.
- **Recovery Timeout**: 60 seconds.
- **Fail-Fast Logic**: If the breaker is **Open**, the adapter raises a `ServiceUnavailable` domain exception.
- **Benefit**: Protects the upstream API from being overwhelmed during incidents and provides instant feedback to the user.

## Error Handling & API Mapping

1. **Domain Exception**: Introduced `ServiceUnavailable` in `core/domain/exceptions.py`.
2. **API Mapping**: `main.py` catches `ServiceUnavailable` and returns an **HTTP 503 Service Unavailable** response.
3. **Graceful Degradation**: Cache failures are swallowed locally in the adapter to ensure the app remains functional as long as the provider is up.

## Verification

A dedicated verification script `scripts/verify_resilience.py` was created to test these scenarios:
- **Redis Down**: Verified that after 3 failures, the app "skips" Redis calls fast.
- **Provider Down**: Verified that after 5 failures, the API returns 503 instead of the underlying error.
- **API Mapping**: Verified using `TestClient` that `ServiceUnavailable` maps to a 503 response.

## Configuration
Circuit breakers are currently configured with static thresholds in the decorators. In a production environment, these could be moved to environment variables.
