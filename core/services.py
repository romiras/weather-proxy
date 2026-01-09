from core.domain.models import WeatherEntity
from core.domain.ports import CachePort, WeatherProviderPort


class WeatherService:
    def __init__(self, provider: WeatherProviderPort, cache: CachePort):
        self.provider = provider
        self.cache = cache

    async def get_weather(self, city_name: str) -> WeatherEntity:
        # 1. Try Cache
        cached = await self.cache.get_weather(city_name)
        if cached:
            return cached

        # 2. Fetch from Provider
        weather = await self.provider.get_weather(city_name)

        # 3. Update Cache
        # We perform this asynchronously/concurrently in a real app,
        # but for now we await to ensure it's written.
        # Errors in cache writing are swallowed by the adapter to prevent crashing the request.
        await self.cache.set_weather(city_name, weather)

        return weather
