from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from core.domain.ports import WeatherProviderPort
from core.domain.exceptions import CityNotFound
from infra.open_meteo import OpenMeteoProvider
from infra.logging import setup_logging
from api.v1.schemas import WeatherResponse, ForecastItem
from api.middleware import TraceIdMiddleware, RequestLoggingMiddleware
import logging

# Setup Logging
setup_logging()
logger = logging.getLogger("api")

# Application State (Dependency Injection)
provider: WeatherProviderPort = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global provider
    logger.info("Starting Weather Proxy...")
    provider = OpenMeteoProvider()
    yield
    logger.info("Shutting down Weather Proxy...")

app = FastAPI(title="Weather Proxy", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TraceIdMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/weather", response_model=WeatherResponse)
async def get_weather(city: str = Query(..., min_length=1)):
    try:
        weather = await provider.get_weather(city)
        
        # Map Entity to response model
        hourly_mapped = [
            ForecastItem(time=item["time"], temperature=item["temperature"])
            for item in weather.forecast
        ]
        
        return WeatherResponse(
            city_name=weather.city,
            current_temperature=weather.temperature,
            current_humidity=weather.humidity,
            hourly_forecast=hourly_mapped
        )
            
    except CityNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Internal Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
