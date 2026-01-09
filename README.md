# Weather Proxy Service

A production-grade Weather Proxy API built with Python and FastAPI, following **Hexagonal Architecture (Ports and Adapters)**. This service mimics a backend environment where business logic is strictly decoupled from external providers (Open-Meteo).

## 🏗 Architecture

The project follows a clean architecture approach to ensure the system is vendor-agnostic and testable.

- **Core (Domain Layer)**: Pure business logic and interfaces (`core/`). Zero external dependencies.
- **API (Inbound Adapter)**: FastAPI web layer (`api/`).
- **Infra (Outbound Adapter)**: External service integrations (`infra/`).

> 📖 **[Read the full Architecture Documentation](docs/architecture.md)**

## 📂 Project Structure

```
weather-proxy/
├── api/            # Inbound Adapters (FastAPI, Middleware)
├── core/           # The Hexagon (Domain Entities, Ports, Exceptions)
├── infra/          # Outbound Adapters (Open-Meteo, Logging)
├── scripts/        # Verification and utility scripts
├── docs/           # Specifications & Architecture docs
├── Dockerfile      # Production container definition
├── main.py         # Application entrypoint & wiring
└── pyproject.toml  # Dependencies
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **uv** (recommended) or `pip`.

### API Usage

#### 1. Run Locally
Start the server with hot-reload enabled:
```bash
uv run uvicorn main:app --reload
```

### API Usage

Once the server is running, you can interact with it using `curl` or any HTTP client.

#### 1. Get Weather for a City
Fetch the current weather and hourly forecast for a specific city.
```bash
curl -v "http://localhost:8000/weather?city=London" | json_pp
```
**Response Preview:**
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

#### 2. Health Check
Verify the service is up and running.
```bash
curl "http://localhost:8000/health"
```

#### 3. Error Handling
Try requesting a non-existent city to see the error handling.
```bash
curl -v "http://localhost:8000/weather?city=Bu-Ga-Gu"
```
*Returns `404 Not Found` with `{"detail": "City 'Bu-Ga-Gu' not found."}`*

## ✅ Verification

For detailed instructions on how to verify the application using the included scripts, please refer to **[scripts/Verification.md](scripts/Verification.md)**.


## 🛠 Tech Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI
- **HTTP Client**: HTTPX (Async)
- **Validation**: Pydantic v2
- **Observability**: Structured JSON logging, Request ID tracing

## 📌 Current Status

See [docs/current_state.md](docs/current_state.md) for a detailed report on Milestone 1 completion.
