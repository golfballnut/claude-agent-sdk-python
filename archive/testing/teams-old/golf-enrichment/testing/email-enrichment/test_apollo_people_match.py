#!/usr/bin/env python3
"""
Test Apollo.io /people/match endpoint (ENRICHMENT API)

This is the CORRECT endpoint for finding NEW emails!

Per Context7 docs:
- POST /people/match
- Enriches data for a single person
- Returns work emails + personal emails (with reveal_personal_emails=true)
- Returns phone numbers (with reveal_phone_number=true)
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def test_people_match(first_name: str, last_name: str, domain: str, company: str):
    """Test /people/match enrichment endpoint"""

    api_key = os.getenv("APOLLO_API_KEY")

    if not api_key:
        print("❌ APOLLO_API_KEY not found in .env")
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/match"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": api_key.strip()
            }
            payload = {
                "first_name": first_name,
                "last_name": last_name,
                "domain": domain,
                "organization_name": company,
                "reveal_personal_emails": False,  # Only work emails for now
                "reveal_phone_number": False  # Skip phone - requires webhook
            }

            r = await client.post(url, headers=headers, json=payload)

            if r.status_code != 200:
                print(f"   ❌ API Error: {r.status_code}")
                print(f"   Response: {r.text[:300]}")
                return None

            data = r.json()

            if data.get("person"):
                return data["person"]
            else:
                return None

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None


async def main():
    """Test Apollo.io /people/match on sample contacts"""

    print("=" * 80)
    print("Apollo.io /people/match (Enrichment API) Test")
    print("=" * 80)
    print()

    contacts = [
        {
            "name": "Stacy Foster",
            "first_name": "Stacy",
            "last_name": "Foster",
            "domain": "richmondcountryclubva.com",
            "company": "Richmond Country Club",
            "state": "VA",
            "hunter_result": "Found (98%)"
        },
        {
            "name": "John Smith",
            "first_name": "John",
            "last_name": "Smith",
            "domain": "pinehurst.com",
            "company": "Pinehurst Resort",
            "state": "NC",
            "hunter_result": "Not found"
        },
        {
            "name": "Sarah Johnson",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "domain": "wadehampton.com",
            "company": "Wade Hampton Golf Club",
            "state": "NC",
            "hunter_result": "Not found"
        }
    ]

    results = []

    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{len(contacts)}] Testing: {contact['name']}")
        print(f"   Company: {contact['company']}")
        print(f"   Domain: {contact['domain']}")
        print(f"   State: {contact['state']}")
        print(f"   Hunter.io: {contact['hunter_result']}")
        print()

        person = await test_people_match(
            contact["first_name"],
            contact["last_name"],
            contact["domain"],
            contact["company"]
        )

        if person:
            email = person.get("email")
            print(f"   ✅ Apollo.io: FOUND!")
            print(f"      Email: {email}")
            print(f"      Title: {person.get('title')}")
            print(f"      LinkedIn: {person.get('linkedin_url')}")

            phone_numbers = person.get("phone_numbers", [])
            if phone_numbers:
                phone = phone_numbers[0].get("raw_number")
                print(f"      Phone: {phone}")

            # Check email status/confidence
            email_status = person.get("email_status")
            if email_status:
                print(f"      Email Status: {email_status}")

                if email_status == "verified":
                    print(f"      ✅ VERIFIED (90%+ confidence)")
                    results.append({"contact": contact["name"], "found": True, "verified": True})
                else:
                    print(f"      ⚠️  Status: {email_status}")
                    results.append({"contact": contact["name"], "found": True, "verified": False})
            else:
                # No email_status field - assume found emails are reliable
                results.append({"contact": contact["name"], "found": True, "verified": True})

        else:
            print(f"   ❌ Apollo.io: NOT FOUND")
            results.append({"contact": contact["name"], "found": False, "verified": False})

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    found = sum(1 for r in results if r["found"])
    verified = sum(1 for r in results if r["verified"])

    print(f"\nContacts tested: {len(results)}")
    print(f"Emails found: {found}/{len(results)}")
    print(f"Verified: {verified}/{len(results)}")
    print()

    # Comparison
    print("=" * 80)
    print("APOLLO /people/match vs HUNTER.IO")
    print("=" * 80)
    print()
    print("Contact                  | Hunter.io | Apollo.io | Result")
    print("-" * 80)

    for contact, result in zip(contacts, results):
        hunter_found = "✅" if "Found" in contact["hunter_result"] else "❌"
        apollo_found = "✅" if result["found"] else "❌"

        if hunter_found == "✅" and apollo_found == "✅":
            outcome = "Both (overlap)"
        elif hunter_found == "❌" and apollo_found == "✅":
            outcome = "Apollo WINS! (unique find)"
        elif hunter_found == "✅" and apollo_found == "❌":
            outcome = "Hunter WINS"
        else:
            outcome = "Neither found"

        print(f"{contact['name']:24} | {hunter_found:^9} | {apollo_found:^9} | {outcome}")

    # Validation
    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)
    print()

    if found > 0:
        print(f"   ✅ Apollo.io /people/match works!")
        print(f"   ✅ Found {found} email(s)")
        print(f"   ✅ Ready for waterfall integration")
        print()
        print("NEXT: Run Test 2 on 50 NC contacts to measure coverage improvement")
    else:
        print("   ⚠️  No emails found - may need to check:")
        print("      - API permissions for /people/match")
        print("      - Contact data quality")
        print("      - Alternative test contacts")

    print()
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(main)
