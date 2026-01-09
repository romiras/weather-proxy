from abc import ABC, abstractmethod
from core.domain.models import WeatherEntity

class WeatherProviderPort(ABC):
    @abstractmethod
    async def get_weather(self, city_name: str) -> WeatherEntity:
        pass

class CachePort(ABC):
    @abstractmethod
    async def get_weather(self, city_name: str) -> WeatherEntity | None:
        pass

    @abstractmethod
    async def set_weather(self, city_name: str, weather: WeatherEntity):
        pass
