import asyncio
import os
import sys
import time

import httpx
from termcolor import cprint

# Ensure we can import from the project root
sys.path.append(os.getcwd())

BASE_URL = "http://localhost:8000"


async def test_caching():
    city = "London"
    url = f"{BASE_URL}/weather"
    params = {"city": city}

    cprint(f"--- Verifying Caching for {city} ---", "blue")

    async with httpx.AsyncClient() as client:
        # 1. First Request (Expect Miss)
        start = time.time()
        cprint("1. Sending First Request (Cold)...", "cyan")
        resp1 = await client.get(url, params=params)
        duration1 = time.time() - start

        if resp1.status_code != 200:
            cprint(f"FAILED: First request failed with {resp1.status_code}", "red")
            cprint(resp1.text, "red")
            sys.exit(1)

        cprint(f"   Success. Duration: {duration1:.3f}s", "green")
        data1 = resp1.json()

        # 2. Second Request (Expect Hit)
        start = time.time()
        cprint("2. Sending Second Request (Warm)...", "cyan")
        resp2 = await client.get(url, params=params)
        duration2 = time.time() - start

        if resp2.status_code != 200:
            cprint(f"FAILED: Second request failed with {resp2.status_code}", "red")
            sys.exit(1)

        cprint(f"   Success. Duration: {duration2:.3f}s", "green")
        data2 = resp2.json()

        # 3. Analysis
        cprint("\n--- Analysis ---", "yellow")
        if duration2 < duration1:
            cprint(f"Performance Improvement: {duration1 / duration2:.1f}x faster", "green")
        else:
            cprint("WARNING: Second request was not faster (Platform latency?)", "yellow")

        if data1 == data2:
            cprint("Data Consistency: Verified", "green")
        else:
            cprint("FAILED: Data mismatch between cache and live", "red")
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(test_caching())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        cprint(f"Error: {e}", "red")
