#!/usr/bin/env python3
"""
Test Apollo People Enrichment on discovered names

This tests whether Apollo can enrich names found via Jina web scraping
"""

import anyio
import httpx
import json
import os
from pathlib import Path
from dotenv import load_dotenv


# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")


async def apollo_people_enrichment(first_name: str, last_name: str, organization_name: str, domain: str = ""):
    """
    Test Apollo people enrichment (match) API

    Endpoint: POST /api/v1/people/match
    Unlocks email, LinkedIn, tenure for a specific person
    """

    if not APOLLO_API_KEY:
        print("   ❌ APOLLO_API_KEY not found")
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/match"

            payload = {
                "first_name": first_name,
                "last_name": last_name,
                "organization_name": organization_name,
            }

            if domain:
                payload["domain"] = domain

            headers = {
                "Content-Type": "application/json",
                "x-api-key": APOLLO_API_KEY
            }

            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

            if data.get("person"):
                person = data["person"]
                return {
                    "found": True,
                    "name": f"{person.get('first_name')} {person.get('last_name')}",
                    "email": person.get("email"),
                    "title": person.get("title"),
                    "linkedin": person.get("linkedin_url"),
                    "organization": person.get("organization", {}).get("name"),
                    "credits_used": 2  # Enrichment costs 2 credits
                }
            else:
                return {"found": False, "credits_used": 0}

    except Exception as e:
        print(f"   ⚠️  Apollo error: {e}")
        return {"found": False, "error": str(e)}


async def test_apollo_enrichment():
    """Test Apollo enrichment on all discovered names"""

    test_cases = [
        # Deercroft GC (currently names only)
        {
            "course": "Deercroft Golf & Country Club",
            "domain": "deercroft.com",
            "contacts": [
                {"first_name": "Jennifer", "last_name": "Byrd", "title": "General Manager"},
                {"first_name": "Rickey", "last_name": "David", "title": "Head Golf Professional"},
            ]
        },
        # Densons Creek (currently name only)
        {
            "course": "Densons Creek Golf Course",
            "domain": "densoncreekgolf.com",
            "contacts": [
                {"first_name": "Art", "last_name": "Colasanti", "title": "Owner/Manager"},
            ]
        },
        # Deep Springs (verify remaining contacts)
        {
            "course": "Deep Springs Country Club",
            "domain": "deepspringscc.com",
            "contacts": [
                {"first_name": "Dean", "last_name": "Farlow", "title": "Superintendent"},
                {"first_name": "Debbie", "last_name": "Lisi", "title": "Office Administrator"},
            ]
        },
    ]

    print("🔍 Testing Apollo People Enrichment on Discovered Names")
    print("=" * 70)

    total_tests = 0
    total_found = 0
    total_credits = 0

    results_by_course = {}

    for test in test_cases:
        course_name = test["course"]
        domain = test["domain"]

        print(f"\n📍 {course_name}")
        print("-" * 70)

        found_contacts = []

        for contact in test["contacts"]:
            total_tests += 1

            print(f"\n   Testing: {contact['first_name']} {contact['last_name']} - {contact['title']}")

            result = await apollo_people_enrichment(
                first_name=contact['first_name'],
                last_name=contact['last_name'],
                organization_name=course_name,
                domain=domain
            )

            if result and result.get("found"):
                total_found += 1
                total_credits += result.get("credits_used", 0)
                found_contacts.append(result)

                print(f"   ✅ FOUND!")
                print(f"      Email: {result.get('email')}")
                print(f"      LinkedIn: {result.get('linkedin')}")
                print(f"      Credits: {result.get('credits_used', 0)}")
            else:
                print(f"   ❌ Not found in Apollo")

        results_by_course[course_name] = {
            "found_count": len(found_contacts),
            "contacts": found_contacts
        }

    # Summary
    print("\n" + "=" * 70)
    print("APOLLO PEOPLE ENRICHMENT RESULTS")
    print("=" * 70)

    print(f"Found: {total_found}/{total_tests} contacts ({total_found/total_tests*100:.0f}%)")
    print(f"Credits used: {total_credits}")
    print(f"Cost: ${total_credits * 0.0197:.3f}")

    # Calculate new overall success rate
    print("\n" + "=" * 70)
    print("PROJECTED OVERALL SUCCESS RATE")
    print("=" * 70)

    current_success = 2  # Devils Ridge, Deer Brook (already have emails)

    # Add courses that now have emails via Apollo enrichment
    if results_by_course["Deercroft Golf & Country Club"]["found_count"] > 0:
        current_success += 1
        print("  ✅ Deercroft: NOW SUCCESS (via Apollo enrichment)")

    if results_by_course["Densons Creek Golf Course"]["found_count"] > 0:
        current_success += 1
        print("  ✅ Densons Creek: NOW SUCCESS (via Apollo enrichment)")

    if results_by_course["Deep Springs Country Club"]["found_count"] > 0:
        print("  ℹ️  Deep Springs: Additional contacts (already had 2)")

    print(f"\nDeep Springs: Already success (2 contacts)")
    print(f"Total: {current_success}/5 ({current_success/5*100:.0f}%)")

    if current_success / 5 >= 0.9:
        print("\n🎉 READY TO DEPLOY: Success rate ≥90%!")
        print("   This is the breakthrough we needed!")
    elif current_success / 5 >= 0.8:
        print("\n✅ READY TO DEPLOY: Success rate ≥80%!")
        print("   Significant improvement from 60%")
    else:
        print(f"\n⚠️  Still at {current_success/5*100:.0f}% - need more coverage")


if __name__ == "__main__":
    anyio.run(test_apollo_enrichment)
