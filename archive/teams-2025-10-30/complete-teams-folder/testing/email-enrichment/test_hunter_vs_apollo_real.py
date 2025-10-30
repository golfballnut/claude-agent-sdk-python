#!/usr/bin/env python3
"""
Test 2: Hunter.io vs Apollo.io on Real NC Contacts

Compares Hunter.io and Apollo.io on REAL production NC contacts.

Goal: Determine if Apollo.io adds value (finds emails Hunter misses)

Expected:
- Hunter.io: ~20% success (baseline)
- Apollo.io: Test if it finds emails Hunter missed
- Decision: If Apollo adds 15%+, build waterfall. If <10%, reconsider.
"""

import anyio
import httpx
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def test_hunter(first_name: str, last_name: str, domain: str):
    """Test Hunter.io Email-Finder"""

    api_key = os.getenv("HUNTER_API_KEY")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.hunter.io/v2/email-finder"
            params = {
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": api_key
            }

            r = await client.get(url, params=params)
            data = r.json()

            if data.get("data") and data["data"].get("email"):
                email = data["data"]["email"]
                confidence = data["data"].get("score", 0)

                if confidence >= 90:
                    return {
                        "email": email,
                        "confidence": confidence,
                        "found": True
                    }

        return {"email": None, "confidence": 0, "found": False}

    except Exception as e:
        return {"email": None, "confidence": 0, "found": False, "error": str(e)}


async def test_apollo(first_name: str, last_name: str, domain: str, company: str):
    """Test Apollo.io /people/match"""

    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
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
                "organization_name": company
            }

            r = await client.post(url, headers=headers, json=payload)

            if r.status_code == 200:
                data = r.json()
                person = data.get("person")

                if person and person.get("email"):
                    email_status = person.get("email_status")
                    confidence = 95 if email_status == "verified" else 80

                    return {
                        "email": person.get("email"),
                        "confidence": confidence,
                        "email_status": email_status,
                        "found": True,
                        "linkedin": person.get("linkedin_url")
                    }

        return {"email": None, "confidence": 0, "found": False}

    except Exception as e:
        return {"email": None, "confidence": 0, "found": False, "error": str(e)}


async def main():
    """Compare Hunter.io vs Apollo.io on real NC contacts"""

    print("=" * 80)
    print("Hunter.io vs Apollo.io - Real NC Contacts Test")
    print("=" * 80)
    print()

    # Load real contacts
    data_file = Path(__file__).parent / "data" / "nc_contacts_real_production.json"
    with open(data_file) as f:
        data = json.load(f)

    contacts = data["contacts"]
    print(f"Testing {len(contacts)} real NC contacts from production")
    print()

    results = []

    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{len(contacts)}] {contact['name']}")
        print(f"   Title: {contact['title']}")
        print(f"   Company: {contact['company']}")
        print(f"   Domain: {contact['domain']}")

        # Parse name
        name_parts = contact['name'].replace(',', '').split()
        first_name = name_parts[0]
        last_name = name_parts[-1] if len(name_parts) > 1 else name_parts[0]

        # Test Hunter.io
        print(f"\n   Testing Hunter.io...")
        hunter_result = await test_hunter(first_name, last_name, contact['domain'])

        if hunter_result and hunter_result['found']:
            print(f"   ✅ Hunter: {hunter_result['email']} ({hunter_result['confidence']}%)")
        else:
            print(f"   ❌ Hunter: Not found")

        # Test Apollo.io
        print(f"   Testing Apollo.io...")
        apollo_result = await test_apollo(
            first_name,
            last_name,
            contact['domain'],
            contact['company']
        )

        if apollo_result and apollo_result['found']:
            print(f"   ✅ Apollo: {apollo_result['email']} ({apollo_result.get('email_status', 'unknown')})")
            if apollo_result.get('linkedin'):
                print(f"   🔗 LinkedIn: {apollo_result['linkedin']}")
        else:
            print(f"   ❌ Apollo: Not found")

        # Save results
        results.append({
            "contact": contact,
            "hunter": hunter_result,
            "apollo": apollo_result
        })

        # Brief pause to respect rate limits
        await anyio.sleep(0.5)

    # Analysis
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)

    hunter_found = sum(1 for r in results if r['hunter'] and r['hunter']['found'])
    apollo_found = sum(1 for r in results if r['apollo'] and r['apollo']['found'])
    both_found = sum(1 for r in results if
                      r['hunter'] and r['hunter']['found'] and
                      r['apollo'] and r['apollo']['found'])
    hunter_only = sum(1 for r in results if
                       r['hunter'] and r['hunter']['found'] and
                       not (r['apollo'] and r['apollo']['found']))
    apollo_only = sum(1 for r in results if
                       r['apollo'] and r['apollo']['found'] and
                       not (r['hunter'] and r['hunter']['found']))
    neither = sum(1 for r in results if
                   not (r['hunter'] and r['hunter']['found']) and
                   not (r['apollo'] and r['apollo']['found']))

    print(f"\n📊 Coverage:")
    print(f"   Total contacts: {len(results)}")
    print(f"   Hunter.io found: {hunter_found} ({hunter_found/len(results)*100:.1f}%)")
    print(f"   Apollo.io found: {apollo_found} ({apollo_found/len(results)*100:.1f}%)")
    print()
    print(f"📈 Overlap Analysis:")
    print(f"   Both found (overlap): {both_found}")
    print(f"   Hunter.io ONLY: {hunter_only}")
    print(f"   Apollo.io ONLY: {apollo_only} ← Apollo's unique value!")
    print(f"   Neither found: {neither}")
    print()
    print(f"💡 Combined Coverage:")
    combined = hunter_found + apollo_only
    print(f"   Hunter.io + Apollo.io = {combined} ({combined/len(results)*100:.1f}%)")
    print(f"   Improvement: +{apollo_only} emails (+{apollo_only/len(results)*100:.1f} percentage points)")

    # Decision
    print()
    print("=" * 80)
    print("DECISION MATRIX")
    print("=" * 80)
    print()

    improvement_pct = (apollo_only / len(results)) * 100

    if apollo_only >= 3:  # 25%+ improvement on 12 contacts
        print(f"   ✅ RECOMMEND: Add Apollo.io to waterfall")
        print(f"   📈 Improvement: +{improvement_pct:.1f} percentage points")
        print(f"   💰 ROI: Finding {apollo_only} additional emails justifies $79/month")
        print()
        print("   Next steps:")
        print("   1. Build Agent 3.5 waterfall (Hunter → Apollo → null)")
        print("   2. Integration test on 20 courses")
        print("   3. Deploy to production")
    elif apollo_only >= 1:  # Some improvement
        print(f"   ⚠️  BORDERLINE: Apollo adds {apollo_only} emails (+{improvement_pct:.1f}%)")
        print(f"   💭 Consider:")
        print(f"      - Test on larger sample (50 contacts)")
        print(f"      - Calculate monthly ROI: {apollo_only} emails × 42 batches/month = {apollo_only * 42} emails/month")
        print(f"      - Cost: $79/month ÷ {apollo_only * 42} emails = ${79/(apollo_only * 42 if apollo_only > 0 else 1):.2f}/email")
        print()
        print("   Next steps:")
        print("   1. Run larger test (50 contacts)")
        print("   2. Re-evaluate ROI")
    else:
        print(f"   ❌ NOT RECOMMENDED: Apollo found 0 additional emails")
        print(f"   💰 ROI: $79/month not justified")
        print()
        print("   Alternatives:")
        print("   1. Try Snov.io ($0.0074/email, cheaper)")
        print("   2. Re-enable web scraping with lower confidence threshold (70%+)")
        print("   3. Accept 60% coverage as baseline")

    # Save results
    results_file = Path(__file__).parent / "results" / "hunter_vs_apollo_real_nc.json"
    results_file.parent.mkdir(exist_ok=True)

    output = {
        "test_date": "2025-10-29",
        "contacts_tested": len(results),
        "hunter_found": hunter_found,
        "apollo_found": apollo_found,
        "both_found": both_found,
        "hunter_only": hunter_only,
        "apollo_only": apollo_only,
        "neither": neither,
        "improvement_percentage": improvement_pct,
        "details": results
    }

    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print(f"📁 Results saved to: {results_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(main)
