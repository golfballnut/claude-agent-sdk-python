#!/usr/bin/env python3
"""
Quick test of Firecrawl fallback for failed courses

Tests the 3 courses that failed in Docker (Apollo + Hunter returned 0):
- Deep Springs CC (deepspringscc.com)
- Deercroft GC (deercroft.com)
- Densons Creek (densoncreekgolf.com)
"""

import anyio
from agents.agent2_apollo_discovery import firecrawl_website_scraping_fallback


async def test_firecrawl_fallback():
    """Test Firecrawl on the 3 failed courses"""

    test_courses = [
        {"name": "Deep Springs Country Club", "domain": "deepspringscc.com"},
        {"name": "Deercroft Golf & Country Club", "domain": "deercroft.com"},
        {"name": "Densons Creek Golf Course", "domain": "densoncreekgolf.com"},
    ]

    print("🔍 Testing Firecrawl Fallback on Failed Courses")
    print("=" * 70)

    results = []
    for course in test_courses:
        print(f"\n📍 Testing: {course['name']} ({course['domain']})")
        print("-" * 70)

        contacts = await firecrawl_website_scraping_fallback(
            domain=course['domain'],
            course_name=course['name']
        )

        result = {
            "course": course['name'],
            "domain": course['domain'],
            "contacts_found": len(contacts),
            "success": len(contacts) > 0,
            "contacts": contacts
        }
        results.append(result)

        if contacts:
            print(f"\n✅ SUCCESS: Found {len(contacts)} contacts")
            for contact in contacts:
                print(f"   - {contact['name']}: {contact['title']}")
                if contact.get('email'):
                    print(f"     Email: {contact['email']} ({contact['email_confidence']}% confidence)")
                else:
                    print(f"     Email: Not found on website")
        else:
            print(f"\n❌ FAILED: No contacts found via Firecrawl")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    successful = len([r for r in results if r['success']])
    total = len(results)
    success_rate = (successful / total * 100) if total > 0 else 0

    print(f"Success: {successful}/{total} ({success_rate:.0f}%)")
    print(f"\nProjected overall success rate with Firecrawl:")
    print(f"  - Apollo: 1/5 (20%)")
    print(f"  - Hunter: 1/5 (20%)")
    print(f"  - Firecrawl: {successful}/3 ({success_rate:.0f}% of previously failed)")
    print(f"  - TOTAL: {2 + successful}/5 ({(2 + successful)/5 * 100:.0f}%)")

    if (2 + successful) / 5 >= 0.9:
        print("\n✅ READY TO DEPLOY: Success rate ≥90%")
    else:
        print(f"\n⚠️  NOT READY: Need {5 * 0.9 - 2 - successful:.0f} more successes to reach 90%")


if __name__ == "__main__":
    anyio.run(test_firecrawl_fallback)
