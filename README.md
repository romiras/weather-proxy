# Weather Proxy Service

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

A production-grade Weather Proxy API built with Python and FastAPI, following **Hexagonal Architecture (Ports and Adapters)**. This service acts as a resilient gateway to external providers (Open-Meteo), featuring caching and robust observability.

## 🏗 Architecture

The project follows a clean architecture approach to ensure the system is vendor-agnostic and testable.

- **Core (Domain Layer)**: Pure business logic and interfaces (`core/`). Zero external dependencies.
- **API (Inbound Adapter)**: FastAPI web layer (`api/`).
- **Infra (Outbound Adapter)**: External service integrations (Open-Meteo, Redis, Logging).

> 📖 **[Read the full Architecture Documentation](docs/architecture.md)**

## 📂 Project Structure

```
weather-proxy/
├── api/            # Inbound Adapters (FastAPI, Middleware)
├── core/           # The Hexagon (Domain Entities, Ports, Exceptions)
├── infra/          # Outbound Adapters (Open-Meteo, Redis, Logging)
├── scripts/        # Verification and utility scripts
├── docs/           # Specifications & Architecture docs
├── Dockerfile      # Production container definition
├── docker-compose.yml # Local development stack
├── main.py         # Application entrypoint & wiring
└── pyproject.toml  # Dependencies
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **uv** (recommended) or `pip`.
- **Redis 7+** (Required for caching).

### Development Setup

#### 1. Configuration
Copy the host configuration example to `.env`:
```bash
cp .env.host.example .env
```
Ensure your locally running Redis matches the `REDIS_URL`.

#### 2. Run Redis (Docker)
If you don't have Redis installed, start it via Docker:
```bash
docker run --name weather-redis -d -p 6379:6379 redis:7-alpine
```

#### 3. Run Application
Start the server with hot-reload enabled:
```bash
uv run uvicorn main:app --reload
```

### 🐳 Docker Compose Setup (Recommended)
You can run the full stack (App + Redis) with one command.

1. Configure environment:
   ```bash
   cp .env.docker.example .env
   ```
2. Start services:
   ```bash
   docker compose up --build
   ```

## 🔌 API Usage

After starting the server (default: `http://localhost:8000`), you can interact with it.

### 1. Get Weather (Cached)
Fetch weather data. Second request to the same city will be **Instant (<1ms)** due to Redis caching.
```bash
curl -v "http://localhost:8000/weather?city=London" | json_pp
```

**Response:**
```json
{
  "city_name": "London",
  "current_temperature": 15.2,
  "current_humidity": 60,
  "hourly_forecast": [
    { "time": "2023-10-27T10:00", "temperature": 15.5 },
    ...
  ]
}
```

### 2. Health Check
```bash
curl "http://localhost:8000/health"
```

### 3. Metrics (Prometheus)
```bash
curl "http://localhost:8000/metrics"
```

## ✅ Verification

Run the verification suite to ensure everything is working:

```bash
# Run Test Suite (37 tests, 96% coverage)
uv run pytest -v --cov

# Run Linter
uv run ruff check .

# Format Code
uv run ruff format .

# Verify Caching Performance
uv run scripts/verify_caching.py

# Verify Provider Integration
uv run scripts/verify_adapter.py
```

### Test Coverage Breakdown
- **Unit Tests**: Core business logic (WeatherService, domain models)
- **Integration Tests**: API endpoints with mocked dependencies
- **Infrastructure Tests**: Redis cache adapter, OpenMeteo provider  
- **Middleware Tests**: Request ID tracking, structured logging
- **Shutdown Tests**: Graceful connection cleanup

**Coverage: 96%** (185/185 statements in core, api, and infra layers)

For more details, see **[scripts/Verification.md](scripts/Verification.md)**.

## 🔄 CI/CD

> ⚠️ **IMPORTANT**: Always run `ruff check .` and `ruff format .` before committing changes!

Automated quality gates run on every push:
- **Linting**: Ruff enforces code style and quality
- **Testing**: Pytest with 37 unit and integration tests (96% coverage)
- **Docker Build**: Validates production image

See [.github/workflows/ci.yml](.github/workflows/ci.yml) for pipeline configuration.

## 🛠 Tech Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI
- **HTTP Client**: HTTPX (Async)
- **Caching**: Redis (Async)
- **Resilience**: Circuit Breaker pattern
- **Validation**: Pydantic v2
- **Testing**: Pytest with async support
- **Linting**: Ruff (fast Python linter)
- **Observability**: Structured JSON logging, Request ID tracing, Prometheus Metrics
- **Deployment**: Graceful shutdown with SIGTERM/SIGINT handling for zero-downtime deployments

## 📌 Status

**Milestone 2 (CI/CD & Quality)** is complete. See [docs/current_state.md](docs/current_state.md) for details.

**Next Objective: Security & Rate Limiting**

- Implement **Rate Limiting** (e.g., using Redis fixed-window or leaky-bucket).
- Consider security hardening (request validation, header sanitization).
- Ensure the rate limiter respects the `X-Request-ID` or Client IP.
