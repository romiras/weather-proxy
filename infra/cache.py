import json
import logging
from typing import Optional
import redis.asyncio as redis
from core.domain.ports import CachePort
from core.domain.models import WeatherEntity
from dataclasses import asdict

logger = logging.getLogger(__name__)

class RedisCacheAdapter(CachePort):
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = 3600  # 1 hour

    async def get_weather(self, city_name: str) -> Optional[WeatherEntity]:
        key = f"weather:{city_name.lower()}"
        try:
            data = await self.redis.get(key)
            if data:
                logger.info(f"Cache HIT for {city_name}")
                json_data = json.loads(data)
                return WeatherEntity(**json_data)
        except Exception as e:
            logger.warning(f"Cache READ error: {e}")
        
        logger.info(f"Cache MISS for {city_name}")
        return None

    async def set_weather(self, city_name: str, weather: WeatherEntity):
        key = f"weather:{city_name.lower()}"
        try:
            # We use asdict to serialize the dataclass
            data = json.dumps(asdict(weather))
            await self.redis.set(key, data, ex=self.ttl)
            logger.debug(f"Cache SET for {city_name}")
        except Exception as e:
            logger.warning(f"Cache WRITE error: {e}")
