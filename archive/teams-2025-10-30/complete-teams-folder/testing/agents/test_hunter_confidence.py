#!/usr/bin/env python3
"""
Direct Hunter.io Confidence Test

Tests what confidence scores Hunter.io actually returns for contacts
from production logs to verify 90% threshold is appropriate.
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


async def test_hunter_confidence():
    """Test Hunter.io confidence scores for production contacts"""

    hunter_key = os.getenv('HUNTER_API_KEY', '')
    if not hunter_key:
        print("❌ HUNTER_API_KEY not set")
        return

    print("\n🧪 Hunter.io Confidence Score Test")
    print("="*70)
    print("User requirement: Only use emails with ≥90% confidence\n")

    # Contacts from production logs
    test_cases = [
        ("Abby", "Byrd", "bhiclub.net", "Prod: Found abyrd@bhiclub.net"),
        ("Andrew", "Kohn", "bhiclub.net", "Prod: Found akohn@bhiclub.net"),
        ("Andy", "Kohn", "bhiclub.net", "Prod: Initially not found"),
        ("Kyle", "Simpson", "beartrailgolf.com", "Prod: Found kyle@beartrailgolf.com"),
        ("Jason", "Franklin", "bhiclub.net", "Prod: Found jfranklin@bhiclub.net"),
        ("Gerard", "Hall", "bhiclub.net", "Prod: Found ghall@bhiclub.net"),
    ]

    results = []

    for first, last, domain, note in test_cases:
        print(f"\nTesting: {first} {last} @ {domain}")
        print(f"  {note}")

        try:
            url = "https://api.hunter.io/v2/email-finder"
            params = {
                "domain": domain,
                "first_name": first,
                "last_name": last,
                "api_key": hunter_key
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(url, params=params)
                data = r.json()

                if data.get("data") and data["data"].get("email"):
                    email = data["data"]["email"]
                    confidence = data["data"].get("score", 0)

                    print(f"  ✅ Found: {email}")
                    print(f"  📊 Confidence: {confidence}%")

                    if confidence >= 90:
                        print(f"  ✅ PASS - Meets 90% threshold")
                        status = "KEEP"
                    else:
                        print(f"  ⚠️  FAIL - Below 90% threshold (would be discarded)")
                        status = "DISCARD"

                    results.append({
                        "name": f"{first} {last}",
                        "email": email,
                        "confidence": confidence,
                        "status": status
                    })
                else:
                    print(f"  ❌ Not found in Hunter.io database")
                    results.append({
                        "name": f"{first} {last}",
                        "email": None,
                        "confidence": 0,
                        "status": "NOT_IN_DB"
                    })

        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            results.append({
                "name": f"{first} {last}",
                "email": None,
                "confidence": 0,
                "status": "ERROR"
            })

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY - 90% Confidence Threshold")
    print(f"{'='*70}\n")

    kept = [r for r in results if r['status'] == 'KEEP']
    discarded = [r for r in results if r['status'] == 'DISCARD']
    not_found = [r for r in results if r['status'] == 'NOT_IN_DB']

    print(f"Total tested: {len(results)}")
    print(f"  ✅ Kept (≥90%): {len(kept)}")
    print(f"  ⚠️  Discarded (<90%): {len(discarded)}")
    print(f"  ❌ Not in database: {len(not_found)}\n")

    if kept:
        print("KEPT (≥90% confidence):")
        for r in kept:
            print(f"  ✅ {r['name']}: {r['email']} ({r['confidence']}%)")

    if discarded:
        print(f"\nDISCARDED (<90% confidence):")
        for r in discarded:
            print(f"  ⚠️  {r['name']}: {r['email']} ({r['confidence']}%)")

    if not_found:
        print(f"\nNOT IN DATABASE:")
        for r in not_found:
            print(f"  ❌ {r['name']}")

    print(f"\n{'='*70}")
    print("CONCLUSION")
    print(f"{'='*70}")

    if len(kept) > 0:
        print(f"✅ Hunter.io provides {len(kept)} emails with ≥90% confidence")
        print(f"✅ 90% threshold is working correctly")
    else:
        print(f"⚠️  No emails met 90% threshold")

    if len(discarded) > 0:
        print(f"\n⚠️  {len(discarded)} emails would be discarded (below 90%)")
        print(f"   This is CORRECT behavior per user requirement")


if __name__ == "__main__":
    anyio.run(test_hunter_confidence)
