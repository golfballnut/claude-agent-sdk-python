#!/usr/bin/env python3
"""
Test Apollo /people/search with discovered names

Try searching for specific people by name at organization
"""

import anyio
import httpx
import json
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")


async def apollo_people_search_by_name(first_name: str, last_name: str, organization_name: str, domain: str = ""):
    """
    Test Apollo /people/search with specific person name

    Different from /people/match - might return different data
    """

    if not APOLLO_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/mixed_people/search"

            # Build search query
            payload = {
                "q_keywords": f"{first_name} {last_name}",
                "page": 1,
                "per_page": 10
            }

            # Add organization filter if domain available
            if domain:
                payload["q_organization_domains_list"] = [domain]
            else:
                payload["q_organization_name"] = organization_name

            headers = {
                "Content-Type": "application/json",
                "x-api-key": APOLLO_API_KEY
            }

            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

            if data.get("people") and len(data["people"]) > 0:
                # Find best match
                for person in data["people"]:
                    first = (person.get("first_name") or "").lower()
                    last = (person.get("last_name") or "").lower()

                    if first == first_name.lower() and last == last_name.lower():
                        return {
                            "found": True,
                            "name": f"{person.get('first_name')} {person.get('last_name')}",
                            "email": person.get("email"),
                            "email_status": person.get("email_status"),
                            "title": person.get("title"),
                            "linkedin": person.get("linkedin_url"),
                            "organization": person.get("organization", {}).get("name"),
                        }

                # If no exact match, return first result
                person = data["people"][0]
                return {
                    "found": True,
                    "exact_match": False,
                    "name": f"{person.get('first_name')} {person.get('last_name')}",
                    "email": person.get("email"),
                    "email_status": person.get("email_status"),
                    "title": person.get("title"),
                    "linkedin": person.get("linkedin_url"),
                }

            return {"found": False}

    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return {"found": False, "error": str(e)}


async def test_apollo_search():
    """Test Apollo search on discovered names"""

    tests = [
        ("Jennifer", "Byrd", "Deercroft Golf & Country Club", "deercroft.com"),
        ("Rickey", "David", "Deercroft Golf & Country Club", "deercroft.com"),
        ("Art", "Colasanti", "Densons Creek Golf Course", "densoncreekgolf.com"),
        ("Dean", "Farlow", "Deep Springs Country Club", "deepspringscc.com"),
        ("Debbie", "Lisi", "Deep Springs Country Club", "deepspringscc.com"),
    ]

    print("🔍 Testing Apollo /people/search with Discovered Names")
    print("=" * 70)

    found_with_emails = 0
    found_total = 0

    for first, last, org, domain in tests:
        print(f"\n📍 {first} {last} @ {org}")
        print("-" * 70)

        result = await apollo_people_search_by_name(first, last, org, domain)

        if result and result.get("found"):
            found_total += 1
            print(f"   ✅ FOUND in Apollo")
            print(f"      Email: {result.get('email') or 'None'}")
            print(f"      Email Status: {result.get('email_status') or 'N/A'}")
            print(f"      LinkedIn: {result.get('linkedin') or 'None'}")

            if result.get("email"):
                found_with_emails += 1
        else:
            print(f"   ❌ Not found")

    # Summary
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Found in Apollo: {found_total}/5")
    print(f"With emails: {found_with_emails}/5")

    # Calculate overall success
    current_success = 3  # Devils Ridge, Deer Brook, Deep Springs (partial)

    if found_with_emails >= 2:
        # Deercroft would succeed
        current_success += 1

    if found_with_emails >= 3:
        # Densons Creek would also succeed
        current_success += 1

    print(f"\nProjected overall: {current_success}/5 ({current_success/5*100:.0f}%)")

    if current_success >= 4.5:
        print("🎉 READY: ≥90%!")
    elif current_success >= 4:
        print("✅ GOOD: ≥80%!")
    else:
        print(f"⚠️  {current_success}/5 = {current_success/5*100:.0f}%")


if __name__ == "__main__":
    anyio.run(test_apollo_search)
