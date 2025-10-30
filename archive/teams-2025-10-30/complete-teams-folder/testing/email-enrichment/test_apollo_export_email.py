#!/usr/bin/env python3
"""
Test Apollo.io Email Export/Unlock

Goal: Figure out how to get the REAL email (not email_not_unlocked@domain.com)

From UI: Drake Woodside has dwoodside@alamancecc.net
From API: Need to find the right endpoint/parameter to unlock it
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def test_people_search_export():
    """
    Try /people/search with different parameters to unlock email
    """

    api_key = os.getenv("APOLLO_API_KEY")

    print("=" * 80)
    print("Apollo.io Email Export Test - Drake Woodside")
    print("=" * 80)
    print()
    print("Testing different approaches to unlock email...")
    print()

    # Test 1: Basic search (what we tried before)
    print("Test 1: Basic /people/search")
    print("-" * 80)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/search"
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": api_key.strip()
            }
            payload = {
                "q_keywords": "Drake Woodside Alamance",
                "page": 1,
                "per_page": 1
            }

            r = await client.post(url, headers=headers, json=payload)
            data = r.json()

            if data.get("people"):
                person = data["people"][0]
                print(f"✅ Found: {person.get('name')}")
                print(f"   Email: {person.get('email')}")
                print(f"   Email Status: {person.get('email_status')}")
                print(f"   Person ID: {person.get('id')}")
                print()

                # Try to enrich this person by ID
                if person.get('id'):
                    person_id = person['id']

                    print("Test 2: Enrich by person ID to unlock email")
                    print("-" * 80)

                    enrich_url = f"https://api.apollo.io/api/v1/people/{person_id}"
                    enrich_r = await client.get(enrich_url, headers=headers)

                    if enrich_r.status_code == 200:
                        enrich_data = enrich_r.json()
                        print(f"✅ Enrichment response:")
                        print(f"   Email: {enrich_data.get('person', {}).get('email')}")
                        print(f"   Status: {enrich_data.get('person', {}).get('email_status')}")
                    else:
                        print(f"❌ Enrichment failed: {enrich_r.status_code}")
                        print(f"   Response: {enrich_r.text[:300]}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print()
    print("=" * 80)
    print("FINDINGS")
    print("=" * 80)
    print()
    print("If email still shows 'email_not_unlocked@domain.com':")
    print("  → Need to call a separate 'export' or 'reveal' endpoint")
    print("  → May need to add person to saved list first")
    print("  → Or use /people/match with exact domain match")
    print()
    print("Next: Check Apollo.io docs for 'export contacts' or 'reveal email' API")


if __name__ == "__main__":
    anyio.run(test_people_search_export)
