import logging
import os
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator

from api.middleware import RequestLoggingMiddleware, TraceIdMiddleware
from api.v1.schemas import ForecastItem, WeatherResponse
from core.domain.exceptions import CityNotFound, ServiceUnavailable
from core.services import WeatherService
from infra.cache import RedisCacheAdapter
from infra.logging import setup_logging
from infra.open_meteo import OpenMeteoProvider

# Setup Logging
setup_logging()
logger = logging.getLogger("api")

# Application State (Dependency Injection)
service: WeatherService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    logger.info("Starting Weather Proxy...")

    # Initialize Adapters
    provider = OpenMeteoProvider()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache = RedisCacheAdapter(redis_url)

    # Initialize Service
    service = WeatherService(provider=provider, cache=cache)

    yield

    # Graceful shutdown: close resources
    logger.info("Shutting down Weather Proxy...")
    try:
        await cache.close()
    except Exception as e:
        logger.error(f"Error during cache shutdown: {e}")
    logger.info("Weather Proxy shutdown complete")


app = FastAPI(title="Weather Proxy", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TraceIdMiddleware)


# Instrument the app to collect metrics
instrumentator = Instrumentator().instrument(app)
# Expose the /metrics endpoint
instrumentator.expose(app)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/weather", response_model=WeatherResponse)
async def get_weather(city: str = Query(..., min_length=1)):
    try:
        weather = await service.get_weather(city)

        # Map Entity to response model
        hourly_mapped = [
            ForecastItem(time=item["time"], temperature=item["temperature"])
            for item in weather.forecast
        ]

        return WeatherResponse(
            city_name=weather.city,
            current_temperature=weather.temperature,
            current_humidity=weather.humidity,
            hourly_forecast=hourly_mapped,
        )

    except CityNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except ServiceUnavailable as e:
        logger.error(f"Service Unavailable: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Internal Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from None


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""

    def handle_signal(signum, frame):
        signame = signal.Signals(signum).name
        logger.info(f"Received signal {signame} ({signum}), initiating graceful shutdown...")

    # Register handlers for SIGTERM and SIGINT
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    logger.info("Signal handlers registered for SIGTERM and SIGINT")


if __name__ == "__main__":
    import uvicorn

    # Setup signal handlers before starting the server
    setup_signal_handlers()

    # Run with proper shutdown handling
    # Uvicorn will handle SIGTERM gracefully by default when using uvicorn.run()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None,  # Use our custom logging setup
    )
