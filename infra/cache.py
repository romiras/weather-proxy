import json
import logging
from dataclasses import asdict

import redis.asyncio as redis
from circuitbreaker import CircuitBreakerError, circuit

from core.domain.models import WeatherEntity
from core.domain.ports import CachePort

logger = logging.getLogger(__name__)


class RedisCacheAdapter(CachePort):
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = 3600  # 1 hour

    @circuit(failure_threshold=3, recovery_timeout=30)
    async def _get_weather_impl(self, city_name: str) -> WeatherEntity | None:
        key = f"weather:{city_name.lower()}"
        data = await self.redis.get(key)
        if data:
            logger.info(f"Cache HIT for {city_name}")
            json_data = json.loads(data)
            return WeatherEntity(**json_data)
        logger.info(f"Cache MISS for {city_name}")
        return None

    async def get_weather(self, city_name: str) -> WeatherEntity | None:
        try:
            return await self._get_weather_impl(city_name)
        except CircuitBreakerError:
            logger.warning(f"Cache Circuit Breaker OPEN for {city_name}. Treating as MISS.")
            return None
        except Exception as e:
            logger.warning(f"Cache READ error: {e}")
            return None

    @circuit(failure_threshold=3, recovery_timeout=30)
    async def _set_weather_impl(self, city_name: str, weather: WeatherEntity):
        key = f"weather:{city_name.lower()}"
        # We use asdict to serialize the dataclass
        data = json.dumps(asdict(weather))
        await self.redis.set(key, data, ex=self.ttl)
        logger.debug(f"Cache SET for {city_name}")

    async def set_weather(self, city_name: str, weather: WeatherEntity):
        try:
            await self._set_weather_impl(city_name, weather)
        except CircuitBreakerError:
            logger.warning(f"Cache Circuit Breaker OPEN for {city_name}. skipping write.")
        except Exception as e:
            logger.warning(f"Cache WRITE error: {e}")
