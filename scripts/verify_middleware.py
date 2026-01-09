import httpx
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path to allow imports from core/infra/api
sys.path.append(str(Path(__file__).parent.parent))

async def verify_middleware():
    print("--- Verifying Middleware ---")
    
    # We need the server running. Since we can't easily spawn uvicorn in background from this script 
    # and guarantee it's up, we will assume the user or a separate process runs it.
    # However, for this environment, I will try to use TestClient.
    
    from fastapi.testclient import TestClient
    from main import app
    
    with TestClient(app) as client:
        print("Sending request to /health...")
        response = client.get("/health")
        
        print(f"Status Code: {response.status_code}")
        
        request_id = response.headers.get("X-Request-ID")
        if request_id:
            print(f"✅ Found X-Request-ID: {request_id}")
        else:
            print("❌ X-Request-ID header MISSING")
        
        print("\nSending request to /weather...")
        try:
            response = client.get("/weather?city=London")
            print(f"Status Code: {response.status_code}")
            request_id = response.headers.get("X-Request-ID")
            if request_id:
                print(f"✅ Found X-Request-ID on /weather: {request_id}")
            else:
                print("❌ X-Request-ID header MISSING on /weather")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_middleware())
