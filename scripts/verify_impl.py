import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from core.domain.exceptions import CityNotFound
from infra.open_meteo import OpenMeteoProvider


async def verify_provider():
    print("--- Verifying OpenMeteoProvider ---")
    provider = OpenMeteoProvider()

    # Test 1: Valid City
    try:
        city = "Paris"
        print(f"Fetching weather for: {city}")
        weather = await provider.get_weather(city)
        print(f"✅ Success! Got weather for {weather.city}")
        print(f"   Temp: {weather.temperature}°C, Humidity: {weather.humidity}%")
        print(f"   Forecast items: {len(weather.forecast)}")
    except Exception as e:
        print(f"❌ Failed to fetch weather for {city}: {e}")

    # Test 2: Invalid City
    try:
        city = "InvalidCityName12345"
        print(f"\nFetching weather for: {city}")
        await provider.get_weather(city)
        print(f"❌ Should have raised CityNotFound for {city}")
    except CityNotFound:
        print(f"✅ Correctly caught CityNotFound for {city}")
    except Exception as e:
        print(f"❌ Wrong exception type for {city}: {type(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(verify_provider())
    except ImportError:
        # Fallback if dependencies not installed globally, though they should be in venv
        print("Dependency error. Ensure httpx is installed.")
