#!/usr/bin/env python3
"""
Test Agent 3 Email Confidence Filtering

Tests with contacts from production logs to verify 90% confidence threshold.

Expected:
- High-confidence emails (>90%): Kept
- Low-confidence emails (<90%): Discarded (blank)
"""

import anyio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

# Import Agent 3's find_email_linkedin function
from agent3_contact_enricher import find_email_linkedin


async def main():
    print("\n🧪 Testing Agent 3 - 90% Confidence Threshold")
    print("="*70)

    # Test contacts from production logs
    test_contacts = [
        {
            "name": "Abby Byrd",
            "title": "Director of Golf Instruction",
            "company": "Bald Head Island Club",
            "domain": "bhiclub.net",
            "expected": "Found (high confidence)",
            "prod_result": "abyrd@bhiclub.net"
        },
        {
            "name": "Andrew Kohn",
            "title": "Director of Golf",
            "company": "Bald Head Island Club",
            "domain": "bhiclub.net",
            "expected": "Found (high confidence)",
            "prod_result": "akohn@bhiclub.net"
        },
        {
            "name": "Andy Kohn",
            "title": "Director of Golf, PGA Professional",
            "company": "Bald Head Island Club",
            "domain": "bhiclub.net",
            "expected": "Uncertain (first run failed)",
            "prod_result": "Not found initially"
        },
        {
            "name": "Kyle Simpson",
            "title": "General Manager",
            "company": "Bear Trail Golf Club",
            "domain": "beartrailgolf.com",
            "expected": "Found (high confidence)",
            "prod_result": "kyle@beartrailgolf.com"
        }
    ]

    results = []

    for contact in test_contacts:
        print(f"\n{'-'*70}")
        print(f"Testing: {contact['name']} ({contact['title']})")
        print(f"Company: {contact['company']}")
        print(f"Domain: {contact['domain']}")
        print(f"Prod result: {contact['prod_result']}")
        print(f"{'-'*70}")

        # Test Agent 3
        result = await find_email_linkedin(contact, contact["company"], "NC")

        # Parse result (it returns SDK tool format)
        if result and "content" in result:
            import json
            data = json.loads(result["content"][0]["text"])

            email = data.get("email")
            confidence = data.get("email_confidence", 0)
            method = data.get("email_method", "none")

            if email:
                print(f"✅ FOUND: {email}")
                print(f"   Confidence: {confidence}%")
                print(f"   Method: {method}")

                if confidence < 90:
                    print(f"   ⚠️  WARNING: Below 90% threshold!")
            else:
                print(f"❌ NOT FOUND")
                print(f"   Steps tried: {data.get('steps_attempted', [])}")

            results.append({
                "contact": contact["name"],
                "email": email,
                "confidence": confidence,
                "meets_threshold": confidence >= 90 if email else None
            })

    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}\n")

    found_count = sum(1 for r in results if r['email'])
    high_confidence = sum(1 for r in results if r['email'] and r['meets_threshold'])

    print(f"Emails found: {found_count}/{len(test_contacts)}")
    print(f"High confidence (≥90%): {high_confidence}/{found_count if found_count > 0 else 0}")
    print()

    for r in results:
        status = "✅" if r['email'] else "❌"
        conf_status = ""
        if r['email']:
            conf_status = f" ({r['confidence']}% {'✅' if r['meets_threshold'] else '⚠️ LOW'})"
        print(f"{status} {r['contact']}: {r['email'] or 'Not found'}{conf_status}")

    # Check if any low-confidence emails got through
    low_conf_emails = [r for r in results if r['email'] and not r['meets_threshold']]

    if low_conf_emails:
        print(f"\n⚠️  WARNING: {len(low_conf_emails)} low-confidence emails found!")
        print("   These should be filtered out!")
        return False
    else:
        print(f"\n✅ All emails meet 90% confidence threshold!")
        return True


if __name__ == "__main__":
    success = anyio.run(main)
    sys.exit(0 if success else 1)
