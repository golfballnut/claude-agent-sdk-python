#!/usr/bin/env python3
"""
Test Apollo.io /v1/contacts/search endpoint

This tests a DIFFERENT endpoint than /v1/people/search
to see if the API key works at all.

/v1/contacts/search = your team's contacts
/v1/people/search = Apollo's 275M database (what we need)
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def test_contacts_search():
    """Test /v1/contacts/search endpoint"""

    api_key = os.getenv("APOLLO_API_KEY")

    if not api_key:
        print("❌ APOLLO_API_KEY not found in .env")
        return

    print("Testing Apollo.io /v1/contacts/search endpoint...")
    print()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/contacts/search"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": api_key.strip()
            }
            payload = {
                "page": 1,
                "per_page": 10
            }

            print(f"Calling: POST {url}")
            print(f"Payload: {payload}")
            print()

            r = await client.post(url, headers=headers, json=payload)

            print(f"Status: {r.status_code}")
            print()

            if r.status_code == 200:
                data = r.json()
                print("✅ SUCCESS! /v1/contacts/search works")
                print()
                print(f"Response keys: {list(data.keys())}")

                if 'contacts' in data:
                    print(f"Contacts returned: {len(data.get('contacts', []))}")

                print()
                print("CONCLUSION:")
                print("✅ Your API key works with /v1/contacts/search")
                print("❌ But /v1/people/search still blocked")
                print()
                print("This means your API key needs DIFFERENT permissions.")
                print("Contact Apollo support or check for 'People Search' permission checkbox.")

            elif r.status_code == 403:
                print("❌ 403 Forbidden on /v1/contacts/search too!")
                print(f"Response: {r.text[:300]}")
                print()
                print("CONCLUSION:")
                print("Your API key doesn't have access to ANY search endpoints.")
                print("This suggests permissions weren't set correctly during key creation.")

            else:
                print(f"❌ Unexpected status: {r.status_code}")
                print(f"Response: {r.text[:300]}")

    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    anyio.run(test_contacts_search)
