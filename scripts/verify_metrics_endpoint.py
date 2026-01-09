import os
import signal
import subprocess
import sys
import time

import requests


def verify_metrics():
    print("Starting Uvicorn server...")
    # Start the server as a subprocess
    process = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(5)

        base_url = "http://localhost:8001"

        # Generate some traffic
        print("Generating traffic...")
        requests.get(f"{base_url}/health")
        requests.get(f"{base_url}/weather?city=London")
        requests.get(f"{base_url}/weather?city=Paris")

        # Check metrics
        print("Checking /metrics endpoint...")
        response = requests.get(f"{base_url}/metrics")

        if response.status_code != 200:
            print(f"FAILED: /metrics returned status code {response.status_code}")
            sys.exit(1)

        content = response.text

        # Verify specific metrics exist
        required_metrics = [
            "http_request_duration_seconds_bucket",
            "http_request_duration_seconds_count",
            "http_requests_total",
        ]

        for metric in required_metrics:
            if metric not in content:
                print(f"FAILED: Metric '{metric}' not found in response")
                sys.exit(1)

        print("SUCCESS: usage metrics found!")
        print("-" * 20)
        print(content[:500] + "...")  # Print first 500 chars
        print("-" * 20)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        print("Stopping server...")
        os.kill(process.pid, signal.SIGTERM)
        process.wait()


if __name__ == "__main__":
    verify_metrics()
