# Weather Proxy Service

A production-grade Weather Proxy API built with Python and FastAPI, following **Hexagonal Architecture (Ports and Adapters)**. This service mimics a backend environment where business logic is strictly decoupled from external providers (Open-Meteo).

## 🏗 Architecture

The project mimics a clean architecture approach to ensure the system is vendor-agnostic and testable.

- **Core (Domain Layer)**: Contains pure business logic, data entities, and interface definitions (Ports). It has *zero* dependencies on frameworks or external APIs.
- **API (Primary Adapter)**: The "Driving" side. Handles incoming HTTP requests via FastAPI and maps them to domain commands.
- **Infra (Secondary Adapter)**: The "Driven" side. Implements the interfaces defined in the core to talk to external services (like Open-Meteo) or databases.

## 📂 Project Structure

```
weather-proxy/
├── api/            # Inbound Adapters (FastAPI)
│   └── v1/         # Versioned API Schemas & Routes
├── core/           # The Hexagon (Business Logic)
│   ├── domain/     # Entities & Ports (Interfaces)
│   └── use_cases/  # Application Logic (Interactors)
├── infra/          # Outbound Adapters
│   └── logging.py  # Infrastructure concerns
├── docs/           # Documentation & Specifications
├── pyproject.toml  # Project Dependencies
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **uv** (recommended for package management) or standard `pip`.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd weather-proxy
    ```

2.  **Install dependencies:**
    Using `uv`:
    ```bash
    uv pip install -r pyproject.toml
    # OR if you just want to sync
    uv sync
    ```
    
    Using `pip`:
    ```bash
    pip install .
    ```

### Running the Project

*Note: The application is currently in the **Skeleton Phase** (Milestone 1). The web server is ready to be implemented.*

To verify the setup and environment:
```bash
python3 -c "import core.domain.models; print('Domain layer is accessible')"
```

## 🛠 Tech Stack

- **Language**: Python 3.12+
- **Web Framework**: FastAPI
- **HTTP Client**: HTTPX (Async)
- **Validation**: Pydantic v2
- **Logging**: Structured JSON logging

## 📌 Current Status

See [docs/current_state.md](docs/current_state.md) for a detailed breakdown of the implemented components and next steps.
