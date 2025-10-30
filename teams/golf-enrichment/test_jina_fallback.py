#!/usr/bin/env python3
"""
Test Jina search+reader fallback on the 3 failed courses

This should achieve 100% success rate (5/5 courses)
"""

import anyio
from agents.agent2_apollo_discovery import jina_search_reader_fallback


async def test_jina_fallback():
    """Test Jina on the 3 failed courses"""

    test_courses = [
        {"name": "Deep Springs Country Club", "domain": "deepspringscc.com", "state": "NC"},
        {"name": "Deercroft Golf & Country Club", "domain": "deercroft.com", "state": "NC"},
        {"name": "Densons Creek Golf Course", "domain": "densoncreekgolf.com", "state": "NC"},
    ]

    print("🔍 Testing Jina Search+Reader Fallback")
    print("=" * 70)

    results = []
    for course in test_courses:
        print(f"\n📍 Testing: {course['name']}")
        print("-" * 70)

        contacts = await jina_search_reader_fallback(
            domain=course['domain'],
            course_name=course['name'],
            state_code=course['state']
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
        else:
            print(f"\n❌ FAILED: No contacts found")

    # Summary
    print("\n" + "=" * 70)
    print("JINA FALLBACK RESULTS")
    print("=" * 70)

    successful = len([r for r in results if r['success']])
    total = len(results)
    success_rate = (successful / total * 100) if total > 0 else 0

    print(f"Jina Success: {successful}/{total} ({success_rate:.0f}%)")
    print(f"\nProjected OVERALL success rate:")
    print(f"  - Apollo: 1/5 (20%) - Devils Ridge")
    print(f"  - Hunter: 1/5 (20%) - Deer Brook")
    print(f"  - Jina: {successful}/3 ({success_rate:.0f}%) - Small courses")
    print(f"  - TOTAL: {2 + successful}/5 ({(2 + successful)/5 * 100:.0f}%)")

    if (2 + successful) / 5 >= 0.9:
        print("\n🎉 READY TO DEPLOY: Success rate ≥90%!")
    else:
        print(f"\n⚠️  Need {int(5 * 0.9) - 2 - successful} more successes to reach 90%")

    return results


if __name__ == "__main__":
    anyio.run(test_jina_fallback)
