#!/usr/bin/env python3
"""
Apollo.io 2-Step Email Finding (CORRECT APPROACH)

Step 1: /people/search → Find person by name (fuzzy matching)
Step 2: /people/match → Enrich with person ID to unlock email (costs 1 credit)

This mimics what the UI does when you click "Access email"
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def find_email_two_step(name: str, company: str, domain: str):
    """
    Two-step email finding:
    1. Search for person by name
    2. Enrich person by ID to get email
    """

    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": api_key.strip()
            }

            # STEP 1: Search for person
            print(f"   Step 1: Searching for '{name}' at '{company}'...")

            # Parse name
            name_parts = name.replace(',', '').replace('.', '').split()
            first_name = name_parts[0]
            last_name = name_parts[-1] if len(name_parts) > 1 else ""

            search_url = "https://api.apollo.io/api/v1/people/search"
            search_payload = {
                "first_name": first_name,
                "last_name": last_name,
                "q_organization_name": company,
                "page": 1,
                "per_page": 10
            }

            search_r = await client.post(search_url, headers=headers, json=search_payload)

            if search_r.status_code != 200:
                print(f"   ❌ Search failed: {search_r.status_code}")
                return None

            search_data = search_r.json()

            if not search_data.get("people"):
                print(f"   ❌ No people found in search")
                return None

            # Find best match (exact name match preferred)
            person = None
            for p in search_data["people"]:
                if name.lower() in p.get("name", "").lower():
                    person = p
                    break

            if not person:
                person = search_data["people"][0]  # Fallback to first result

            person_id = person.get("id")
            found_name = person.get("name")
            found_title = person.get("title")

            print(f"   ✅ Found: {found_name}")
            print(f"      Title: {found_title}")
            print(f"      Person ID: {person_id}")

            # STEP 2: Enrich person by ID to get email
            print(f"   Step 2: Enriching person {person_id} to unlock email...")

            enrich_url = "https://api.apollo.io/api/v1/people/match"
            enrich_payload = {
                "id": person_id  # Use person ID from search!
            }

            enrich_r = await client.post(enrich_url, headers=headers, json=enrich_payload)

            if enrich_r.status_code != 200:
                print(f"   ❌ Enrichment failed: {enrich_r.status_code}")
                print(f"      Response: {enrich_r.text[:200]}")
                return None

            enrich_data = enrich_r.json()
            enriched_person = enrich_data.get("person")

            if enriched_person:
                email = enriched_person.get("email")
                email_status = enriched_person.get("email_status")

                print(f"   ✅ Email unlocked: {email}")
                print(f"      Status: {email_status}")

                return {
                    "email": email,
                    "email_status": email_status,
                    "linkedin_url": enriched_person.get("linkedin_url"),
                    "phone_numbers": enriched_person.get("phone_numbers"),
                    "person_id": person_id
                }

            return None

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None


async def main():
    """Test 2-step approach on Drake Woodside"""

    print("=" * 80)
    print("Apollo.io 2-Step Email Finding Test")
    print("=" * 80)
    print()

    contacts = [
        {
            "name": "Drake Woodside",
            "company": "Alamance Country Club",
            "domain": "alamancecountryclub.com",  # Wrong domain!
            "expected_email": "dwoodside@alamancecc.net"
        },
        {
            "name": "Philip J Shepherd",
            "company": "Mountain Aire Golf Club",
            "domain": "mountainaire.com",
            "expected_email": "golf@mountainaire.com"
        },
        {
            "name": "Jason A. York",
            "company": "Star Hill Golf Club",
            "domain": "starhillgolf.com",
            "expected_email": "Unknown"
        }
    ]

    results = []

    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{len(contacts)}] {contact['name']}")
        print(f"   Company: {contact['company']}")
        print(f"   Domain (our data): {contact['domain']}")
        print(f"   Expected: {contact['expected_email']}")
        print()

        result = await find_email_two_step(
            contact['name'],
            contact['company'],
            contact['domain']
        )

        if result:
            results.append({
                "contact": contact['name'],
                "found": True,
                "email": result['email'],
                "status": result['email_status']
            })
        else:
            results.append({
                "contact": contact['name'],
                "found": False
            })

        await anyio.sleep(1)  # Rate limit courtesy

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    found = sum(1 for r in results if r['found'])
    verified = sum(1 for r in results if r.get('status') == 'verified')

    print(f"\nContacts tested: {len(results)}")
    print(f"Emails found: {found}/{len(results)}")
    print(f"Verified: {verified}/{len(results)}")

    if found > 0:
        print()
        print("✅ 2-STEP APPROACH WORKS!")
        print()
        print("Workflow:")
        print("  1. /people/search (find person even with wrong domain)")
        print("  2. /people/match with person ID (unlock email)")
        print()
        print("This handles domain mismatch issues!")
    else:
        print()
        print("⚠️  2-step approach didn't find emails")
        print("Need to debug search parameters")

    print()
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(main)
