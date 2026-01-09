import httpx
from core.domain.ports import WeatherProviderPort
from core.domain.models import WeatherEntity
from core.domain.exceptions import CityNotFound
import logging

logger = logging.getLogger(__name__)

class OpenMeteoProvider(WeatherProviderPort):
    def __init__(self):
        self.geo_base_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_base_url = "https://api.open-meteo.com/v1/forecast"

    async def get_weather(self, city_name: str) -> WeatherEntity:
        async with httpx.AsyncClient() as client:
            # 1. Geocoding
            geo_params = {
                "name": city_name,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            logger.info(f"Geocoding city: {city_name}")
            resp = await client.get(self.geo_base_url, params=geo_params)
            resp.raise_for_status()
            data = resp.json()

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
                "forecast_days": 1
            }
            
            logger.info(f"Fetching weather for {city_name} at ({lat}, {lon})")
            w_resp = await client.get(self.weather_base_url, params=weather_params)
            w_resp.raise_for_status()
            w_data = w_resp.json()
            
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
                    forecast_list.append({
                        "time": times[i],
                        "temperature": temps[i]
                    })

            return WeatherEntity(
                city=location["name"],
                temperature=current.get("temperature_2m", 0.0),
                humidity=current.get("relative_humidity_2m", 0.0),
                forecast=forecast_list
            )
