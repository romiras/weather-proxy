from abc import ABC, abstractmethod
from core.domain.models import WeatherEntity

class WeatherProviderPort(ABC):
    @abstractmethod
    async def get_weather(self, city_name: str) -> WeatherEntity:
        pass
