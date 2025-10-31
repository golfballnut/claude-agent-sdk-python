#!/usr/bin/env python3
"""
Apollo.io API Connection Test

Quick validation to ensure Apollo.io People Search API works correctly.

Tests:
1. API key is valid
2. Response format matches documentation
3. email_status field available for 90%+ filtering
4. Bonus data: phone numbers, LinkedIn URLs

Compares to Hunter.io results to measure unique value.
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def test_apollo_search(first_name: str, last_name: str, domain: str, company: str):
    """Test Apollo.io People Search API"""

    api_key = os.getenv("APOLLO_API_KEY")

    if not api_key:
        print("❌ APOLLO_API_KEY not found in .env")
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/search"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": api_key  # API key in header, not payload!
            }
            payload = {
                "first_name": first_name,
                "last_name": last_name,
                "organization_domains": [domain],
                "page": 1,
                "per_page": 1
            }

            r = await client.post(url, headers=headers, json=payload)

            # Check for errors
            if r.status_code != 200:
                print(f"   ❌ API Error: {r.status_code}")
                print(f"   Response: {r.text[:200]}")
                return None

            data = r.json()

            if data.get("people") and len(data["people"]) > 0:
                person = data["people"][0]
                return {
                    "name": person.get("name"),
                    "email": person.get("email"),
                    "email_status": person.get("email_status"),
                    "title": person.get("title"),
                    "linkedin_url": person.get("linkedin_url"),
                    "phone_numbers": person.get("phone_numbers", []),
                    "organization_name": person.get("organization_name")
                }
            else:
                return {
                    "name": f"{first_name} {last_name}",
                    "email": None,
                    "email_status": "not_found"
                }

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None


async def main():
    """Test Apollo.io on sample contacts"""

    print("=" * 80)
    print("Apollo.io API Connection Test")
    print("=" * 80)
    print()

    # Test contacts
    contacts = [
        {
            "name": "Stacy Foster",
            "first_name": "Stacy",
            "last_name": "Foster",
            "domain": "richmondcountryclubva.com",
            "company": "Richmond Country Club",
            "state": "VA",
            "hunter_result": "Found (98% confidence)"
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

        result = await test_apollo_search(
            contact["first_name"],
            contact["last_name"],
            contact["domain"],
            contact["company"]
        )

        if result:
            email = result.get("email")
            status = result.get("email_status")

            if email:
                print(f"   ✅ Apollo.io: FOUND")
                print(f"      Email: {email}")
                print(f"      Status: {status}")
                print(f"      Title: {result.get('title')}")

                if result.get("linkedin_url"):
                    print(f"      LinkedIn: {result['linkedin_url']}")

                if result.get("phone_numbers"):
                    phone = result["phone_numbers"][0].get("raw_number") if result["phone_numbers"] else None
                    if phone:
                        print(f"      Phone: {phone}")

                # Check if verified (90%+ confidence)
                if status == "verified":
                    print(f"      ✅ VERIFIED (90%+ confidence - meets threshold!)")
                elif status == "likely":
                    print(f"      ⚠️  LIKELY (80-90% confidence - below threshold)")
                elif status == "guessed":
                    print(f"      ⚠️  GUESSED (60-80% confidence - below threshold)")

                results.append({
                    "contact": contact["name"],
                    "apollo_found": True,
                    "email_status": status,
                    "meets_threshold": status == "verified"
                })
            else:
                print(f"   ❌ Apollo.io: NOT FOUND")
                results.append({
                    "contact": contact["name"],
                    "apollo_found": False,
                    "email_status": "not_found",
                    "meets_threshold": False
                })
        else:
            print(f"   ❌ Apollo.io: ERROR (check logs above)")
            results.append({
                "contact": contact["name"],
                "apollo_found": False,
                "email_status": "error",
                "meets_threshold": False
            })

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    found = sum(1 for r in results if r["apollo_found"])
    verified = sum(1 for r in results if r["meets_threshold"])

    print(f"\nContacts tested: {len(results)}")
    print(f"Emails found: {found}/{len(results)}")
    print(f"Verified (90%+): {verified}/{len(results)}")
    print()

    # Comparison to Hunter.io
    print("=" * 80)
    print("APOLLO.IO vs HUNTER.IO COMPARISON")
    print("=" * 80)
    print()
    print("Contact                  | Hunter.io | Apollo.io | Winner")
    print("-" * 80)

    for i, (contact, result) in enumerate(zip(contacts, results)):
        hunter_found = "✅" if "Found" in contact["hunter_result"] else "❌"
        apollo_found = "✅" if result["apollo_found"] else "❌"

        if hunter_found == "✅" and apollo_found == "✅":
            winner = "Both"
        elif hunter_found == "✅":
            winner = "Hunter"
        elif apollo_found == "✅":
            winner = "Apollo"
        else:
            winner = "Neither"

        print(f"{contact['name']:24} | {hunter_found:^9} | {apollo_found:^9} | {winner}")

    # Next steps
    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)
    print()

    validations = []

    if any(r["apollo_found"] for r in results):
        validations.append("✅ Apollo.io API connection working")
    else:
        validations.append("❌ No emails found - check API key or permissions")

    if any(r["meets_threshold"] for r in results):
        validations.append("✅ 'verified' status available for 90%+ filtering")
    else:
        validations.append("⚠️  No verified emails found in test set")

    if found > 0:
        validations.append(f"✅ Found {found} emails - ready for waterfall integration")
    else:
        validations.append("⚠️  No emails found - may need larger test set")

    for v in validations:
        print(f"   {v}")

    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()

    if any(r["apollo_found"] for r in results):
        print("✅ Apollo.io API is working correctly!")
        print()
        print("Ready for:")
        print("1. Test 2: Apollo.io NC baseline (50 contacts)")
        print("2. Build Agent 3.5 waterfall (Hunter.io → Apollo.io)")
        print("3. Integration testing (20 courses)")
    else:
        print("⚠️  Apollo.io API test inconclusive")
        print()
        print("Check:")
        print("1. API key is correct in .env")
        print("2. API permissions enabled: api/v1/people/search")
        print("3. Professional plan is active (not free tier)")

    print()
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(main)
