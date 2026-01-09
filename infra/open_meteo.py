import json
import logging
import time

import httpx
from circuitbreaker import CircuitBreakerError, circuit

from core.domain.exceptions import CityNotFound, ServiceUnavailable
from core.domain.models import WeatherEntity
from core.domain.ports import WeatherProviderPort

logger = logging.getLogger(__name__)


class OpenMeteoProvider(WeatherProviderPort):
    def __init__(self):
        self.geo_base_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_base_url = "https://api.open-meteo.com/v1/forecast"

    async def _fetch_with_metrics(
        self, client: httpx.AsyncClient, url: str, params: dict, endpoint_type: str
    ):
        """Helper to perform HTTP request with timing and observability logging."""
        start_time = time.time()
        status_code = 0
        try:
            response = await client.get(url, params=params)
            status_code = response.status_code
            response.raise_for_status()

            # Success Log
            duration_ms = (time.time() - start_time) * 1000
            log_data = {
                "event": "upstream_call",
                "provider": "open_meteo",
                "endpoint": endpoint_type,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "url": str(response.url),
            }
            logger.info(json.dumps(log_data))

            return response.json()

        except httpx.HTTPError as e:
            # Failure Log
            duration_ms = (time.time() - start_time) * 1000
            log_data = {
                "event": "upstream_call_error",
                "provider": "open_meteo",
                "endpoint": endpoint_type,
                "status_code": status_code,  # Might be 0 if connection error
                "duration_ms": round(duration_ms, 2),
                "error": str(e),
            }
            logger.error(json.dumps(log_data))
            raise

    @circuit(failure_threshold=5, recovery_timeout=60)
    async def _get_weather_impl(self, city_name: str) -> WeatherEntity:
        async with httpx.AsyncClient() as client:
            # 1. Geocoding
            geo_params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
            logger.info(f"Geocoding city: {city_name}")

            data = await self._fetch_with_metrics(
                client, self.geo_base_url, geo_params, "geocoding"
            )

            if not data.get("results"):
                logger.warning(f"City not found: {city_name}")
                raise CityNotFound(city_name)

            location = data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            timezone = location.get("timezone", "UTC")

            # 2. Weather Fetch
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": ["temperature_2m", "relative_humidity_2m"],
                "hourly": ["temperature_2m"],
                "timezone": timezone,
                "forecast_days": 1,
            }

            logger.info(f"Fetching weather for {city_name} at ({lat}, {lon})")

            w_data = await self._fetch_with_metrics(
                client, self.weather_base_url, weather_params, "forecast"
            )

            # 3. Map to Entity
            current = w_data.get("current", {})
            hourly = w_data.get("hourly", {})

            # Construct forecast list
            forecast_list = []
            if "time" in hourly and "temperature_2m" in hourly:
                times = hourly["time"]
                temps = hourly["temperature_2m"]
                # Take next 5 hours
                for i in range(min(5, len(times))):
                    forecast_list.append({"time": times[i], "temperature": temps[i]})

            return WeatherEntity(
                city=location["name"],
                temperature=current.get("temperature_2m", 0.0),
                humidity=current.get("relative_humidity_2m", 0.0),
                forecast=forecast_list,
            )

    async def get_weather(self, city_name: str) -> WeatherEntity:
        try:
            return await self._get_weather_impl(city_name)
        except CircuitBreakerError:
            logger.error("Circuit Breaker OPEN for Provider. Service Unavailable.")
            raise ServiceUnavailable("Weather Provider") from None
