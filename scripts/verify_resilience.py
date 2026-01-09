import asyncio
import logging
import sys
import time
from unittest.mock import patch

from termcolor import colored

# Add project root to path
sys.path.append(".")


from core.domain.exceptions import ServiceUnavailable
from infra.cache import RedisCacheAdapter
from infra.open_meteo import OpenMeteoProvider

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("verify_resilience")


async def test_redis_circuit_breaker():
    print(colored("\n--- Testing Redis Circuit Breaker ---", "cyan"))

    # reset all breakers
    # for cb in CircuitBreaker.get_breakers():
    #     cb.close()

    # Use a non-existent host to force connection errors
    adapter = RedisCacheAdapter("redis://non-existent-host:6379/0")
    # Reduce timeout for faster test
    adapter.redis.connection_pool.connection_kwargs["socket_connect_timeout"] = 0.5

    city = "TestCity"

    print("Attempting to read from invalid Redis (expecting failures)...")
    start_time = time.time()

    # We configured failure_threshold=3 in infra/cache.py
    for i in range(1, 10):
        try:
            # Should return None (handled exception)
            result = await adapter.get_weather(city)
            print(f"Attempt {i}: Result={result}")
        except Exception as e:
            print(f"Attempt {i}: Unexpected Exception={e}")

    end_time = time.time()
    print(f"Drafting executed in {end_time - start_time:.2f}s")

    # We can't easily programmatically check if CB is open without accessing the decorated object's CB
    # But we should see logs "Cache Circuit Breaker OPEN" if we run this with logs visible.


async def test_provider_circuit_breaker():
    print(colored("\n--- Testing Provider Circuit Breaker ---", "cyan"))

    # reset all breakers
    # for cb in CircuitBreaker.get_breakers():
    #     cb.close()

    provider = OpenMeteoProvider()

    # Patch httpx to always fail
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("Network Error")

        print("Attempting to fetch from Provider (mocking failure)...")
        # We configured failure_threshold=5 in infra/open_meteo.py

        for i in range(1, 10):
            try:
                await provider.get_weather("London")
                print(f"Attempt {i}: Success (Unexpected)")
            except ServiceUnavailable:
                print(
                    colored(
                        f"Attempt {i}: Caught ServiceUnavailable (Circuit Breaker OPEN!)", "green"
                    )
                )
            except Exception as e:
                print(f"Attempt {i}: Caught expected underlying error: {e}")


if __name__ == "__main__":
    asyncio.run(test_redis_circuit_breaker())
    asyncio.run(test_provider_circuit_breaker())


def test_api_503():
    print(colored("\n--- Testing API 503 Mapping ---", "cyan"))
    from fastapi.testclient import TestClient

    from main import app

    # We need to mock the service.provider.get_weather to raise ServiceUnavailable
    # But service is initialized in lifespan, which TestClient handles.
    # However, we want to force the specific exception.

    with TestClient(app) as client:
        # We can patch the method on the instance injected into the service
        # But `service` in main is global.

        # Simpler approach: Patch the class method used by the provider
        with patch("infra.open_meteo.OpenMeteoProvider.get_weather") as mock_get:
            mock_get.side_effect = ServiceUnavailable("Simulated Failure")

            # We need to ensure the service uses this mocked provider or the mock works on the instance.
            # Since `service` global is created in lifespan, and lifespan runs on client startup.
            # The provider inside service is an instance of OpenMeteoProvider.
            # Patching the class method `get_weather` should work if we patch it where it's defined or used.

            # Actually, `main.service` is initialized with `provider=OpenMeteoProvider()`.
            # If we patch `infra.open_meteo.OpenMeteoProvider.get_weather`, it should affect the instance method.

            response = client.get("/weather?city=FailCity")
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.json()}")

            if response.status_code == 503:
                print(colored("SUCCESS: API returned 503 for ServiceUnavailable", "green"))
            else:
                print(colored(f"FAILURE: API returned {response.status_code}", "red"))


if __name__ == "__main__":
    asyncio.run(test_redis_circuit_breaker())
    asyncio.run(test_provider_circuit_breaker())
    test_api_503()
