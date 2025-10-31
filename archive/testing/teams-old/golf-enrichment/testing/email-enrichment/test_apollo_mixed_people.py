#!/usr/bin/env python3
"""
Test Apollo.io /api/v1/mixed_people/search endpoint

Per Context7 docs: This endpoint searches Apollo's database
BUT "does not return new email addresses or phone numbers"

Let's test to see what it DOES return.
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def test_mixed_people():
    """Test /api/v1/mixed_people/search endpoint"""

    api_key = os.getenv("APOLLO_API_KEY")

    if not api_key:
        print("❌ APOLLO_API_KEY not found in .env")
        return

    print("Testing Apollo.io /api/v1/mixed_people/search endpoint...")
    print()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/mixed_people/search"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": api_key.strip()
            }
            payload = {
                "first_name": "Stacy",
                "last_name": "Foster",
                "q_organization_domains_list": ["richmondcountryclubva.com"],
                "page": 1,
                "per_page": 1
            }

            print(f"Calling: POST {url}")
            print(f"Searching for: Stacy Foster @ Richmond Country Club")
            print()

            r = await client.post(url, headers=headers, json=payload)

            print(f"Status: {r.status_code}")
            print()

            if r.status_code == 200:
                data = r.json()
                print("✅ SUCCESS! /api/v1/mixed_people/search works")
                print()
                print(f"Response keys: {list(data.keys())}")

                if 'contacts' in data:
                    contacts = data.get('contacts', [])
                    print(f"Contacts returned: {len(contacts)}")

                    if contacts:
                        contact = contacts[0]
                        print()
                        print("First contact data:")
                        print(f"   Name: {contact.get('name')}")
                        print(f"   Email: {contact.get('email')}")
                        print(f"   Phone: {contact.get('phone_numbers')}")
                        print(f"   LinkedIn: {contact.get('linkedin_url')}")
                        print(f"   Title: {contact.get('title')}")
                        print()
                        print("IMPORTANT: Docs say this endpoint 'does not return NEW emails'")
                        print("Checking if email is returned anyway...")

                        if contact.get('email'):
                            print("   ✅ Email IS returned!")
                            print("   🤔 Maybe docs are outdated?")
                        else:
                            print("   ❌ Email NOT returned (as docs stated)")

            elif r.status_code == 403:
                print("❌ 403 Forbidden")
                print(f"Response: {r.text[:500]}")
                print()
                print("Still blocked - this endpoint also requires special permissions")

            else:
                print(f"❌ Unexpected status: {r.status_code}")
                print(f"Response: {r.text[:500]}")

    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    anyio.run(test_mixed_people)
