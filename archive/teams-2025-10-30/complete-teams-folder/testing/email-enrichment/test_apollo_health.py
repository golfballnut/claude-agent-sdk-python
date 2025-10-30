#!/usr/bin/env python3
"""
Apollo.io Health Check Test

Per Apollo.io docs: https://docs.apollo.io/docs/test-api-key
Test endpoint: GET https://api.apollo.io/v1/auth/health

Success = both values in response are true
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def test_health():
    """Test Apollo.io API key with health endpoint"""

    api_key = os.getenv("APOLLO_API_KEY")

    if not api_key:
        print("❌ APOLLO_API_KEY not found in .env")
        return

    print("Testing Apollo.io API key...")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")  # Show partial key
    print()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/v1/auth/health"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": api_key.strip()  # Remove any spaces
            }

            print(f"Calling: GET {url}")
            print(f"Headers: {list(headers.keys())}")
            print()

            r = await client.get(url, headers=headers)

            print(f"Status: {r.status_code}")
            print(f"Response: {r.text}")
            print()

            if r.status_code == 200:
                data = r.json()

                # Check if both values are true
                all_true = all(v == True for v in data.values() if isinstance(v, bool))

                if all_true:
                    print("✅ SUCCESS! API key is valid and ready to use")
                    print()
                    print("Next: Try people search endpoint")
                else:
                    print("⚠️  API key authenticated but some permissions may be missing")
                    print(f"Response: {data}")
            else:
                print(f"❌ Error: {r.status_code}")
                print(f"Response: {r.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    anyio.run(test_health)
