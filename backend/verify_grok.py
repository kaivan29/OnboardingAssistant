import httpx
import asyncio
import os

from app.config import get_settings

settings = get_settings()
API_KEY = settings.xai_api_key
BASE_URL = "https://api.x.ai/v1"

async def test_grok():
    print(f"Testing Grok API at {BASE_URL}...")
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "grok-4-1-fast-reasoning",
        "messages": [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "Hello, world!"}
        ],
        "stream": False
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_grok())
