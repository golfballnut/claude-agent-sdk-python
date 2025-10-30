#!/usr/bin/env python3
"""
Test B: Apollo.io Organization Search with Title Filtering

Goal: Prove we can find ONLY key decision-makers (GM, Director) at each course
      NOT all 50 employees!

This is critical for credit efficiency:
- Search 50 employees = expensive
- Search 2-4 decision-makers = affordable

Tests on 5 NC golf courses to validate approach.
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def search_course_contacts(course_name: str, filter_titles=True):
    """
    Search for contacts at a golf course

    Args:
        course_name: Name of the golf course
        filter_titles: If True, filter to GM/Director only. If False, return all.
    """

    api_key = os.getenv("APOLLO_API_KEY")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/search"
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": api_key.strip()
            }

            payload = {
                "q_organization_name": course_name,
                "page": 1,
                "per_page": 50  # Get up to 50 to see total available
            }

            # Add title filter if requested
            if filter_titles:
                payload["person_titles"] = [
                    "General Manager",
                    "Director of Golf",
                    "Head Golf Professional",
                    "Golf Course Manager"
                ]

            r = await client.post(url, headers=headers, json=payload)

            if r.status_code == 200:
                data = r.json()
                people = data.get("people", [])
                pagination = data.get("pagination", {})

                return {
                    "found": len(people),
                    "total": pagination.get("total_entries", len(people)),
                    "people": people
                }
            else:
                return {"found": 0, "total": 0, "people": [], "error": r.status_code}

    except Exception as e:
        return {"found": 0, "total": 0, "people": [], "error": str(e)}


async def main():
    """Test organization search with and without filtering"""

    print("=" * 80)
    print("Apollo.io Organization Search with Title Filtering")
    print("=" * 80)
    print()

    test_courses = [
        "Alamance Country Club",
        "Mountain Aire Golf Club",
        "Star Hill Golf Club",
        "Bald Head Island Club",
        "Ballantyne Country Club"
    ]

    print("Testing 5 NC golf courses")
    print("Comparing: ALL employees vs FILTERED (GM/Director only)")
    print()

    results = []

    for i, course in enumerate(test_courses, 1):
        print(f"\n[{i}/{len(test_courses)}] {course}")
        print("-" * 80)

        # Test WITHOUT filter (all employees)
        print("   Searching: ALL employees...")
        all_results = await search_course_contacts(course, filter_titles=False)

        print(f"   Results: {all_results['found']} people (total: {all_results['total']})")

        if all_results['people']:
            titles = [p.get('title') for p in all_results['people'][:5]]
            print(f"   Sample titles: {titles[:3]}")

        # Test WITH filter (GM/Director only)
        print()
        print("   Searching: FILTERED (GM/Director/Head Pro only)...")
        filtered_results = await search_course_contacts(course, filter_titles=True)

        print(f"   Results: {filtered_results['found']} people ✅")

        if filtered_results['people']:
            for person in filtered_results['people']:
                print(f"      - {person.get('name')}: {person.get('title')}")

        results.append({
            "course": course,
            "all_employees": all_results['total'],
            "filtered_contacts": filtered_results['found'],
            "reduction": all_results['total'] - filtered_results['found']
        })

        await anyio.sleep(1)

    # Analysis
    print("\n" + "=" * 80)
    print("FILTERING EFFICIENCY ANALYSIS")
    print("=" * 80)
    print()

    total_all = sum(r['all_employees'] for r in results)
    total_filtered = sum(r['filtered_contacts'] for r in results)
    reduction = total_all - total_filtered

    print(f"Total people found:")
    print(f"   Without filter: {total_all} people")
    print(f"   With filter: {total_filtered} people")
    print(f"   Reduction: {reduction} people ({reduction/total_all*100:.1f}% fewer!)")
    print()

    avg_filtered = total_filtered / len(results)
    print(f"Average per course:")
    print(f"   Without filter: {total_all/len(results):.1f} people")
    print(f"   With filter: {avg_filtered:.1f} people ✅")
    print()

    # Credit projection
    print("=" * 80)
    print("CREDIT PROJECTION")
    print("=" * 80)
    print()
    print("Assumptions:")
    print("  - Search cost: 1 credit (TBD - check dashboard)")
    print("  - Enrich cost: 1 credit per person (TBD - check dashboard)")
    print()
    print(f"Per course (with filtering to {avg_filtered:.0f} people):")
    print(f"  - 1 search: 1 credit")
    print(f"  - {avg_filtered:.0f} enrichments: {avg_filtered:.0f} credits")
    print(f"  - Total: {1 + avg_filtered:.0f} credits per course")
    print()
    print(f"Monthly (500 courses):")
    print(f"  - Total credits: 500 × {1 + avg_filtered:.0f} = {500 * (1 + avg_filtered):.0f} credits")
    print(f"  - Your limit: 4,000 credits")
    print(f"  - Sufficient? {'✅ Yes' if 500 * (1 + avg_filtered) <= 4000 else '❌ No (need more credits)'}")
    print()

    # Comparison to current Agent 2
    print("=" * 80)
    print("APOLLO vs AGENT 2 (Contact Discovery)")
    print("=" * 80)
    print()
    print("Current Agent 2:")
    print("  - Cost: $0.013 per course")
    print("  - Method: Web scraping + LinkedIn")
    print("  - Accuracy: Unknown (may be outdated)")
    print()
    print("Apollo.io:")
    print(f"  - Cost: ~${79/500:.3f} per course (if {500*(1+avg_filtered):.0f} credits/month)")
    print(f"  - Method: Database lookup (current employees)")
    print(f"  - Accuracy: Real-time (job changes tracked)")
    print()

    decision = ""
    if 500 * (1 + avg_filtered) <= 4000:
        if avg_filtered <= 3:
            decision = "✅ RECOMMEND: Use Apollo for contact discovery (affordable + accurate)"
        else:
            decision = "⚠️  REVIEW: Filter is finding too many people per course"
    else:
        decision = "❌ NOT AFFORDABLE: Need to reduce contacts per course or get more credits"

    print(f"Decision: {decision}")
    print()

    # Instructions
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. ✅ Go to https://app.apollo.io/usage")
    print("2. ✅ Note 'Credits used' count AFTER this test")
    print("3. ✅ Calculate actual credit consumption:")
    print(f"   - Search credits = (current - before) ÷ {len(test_courses)} searches")
    print("4. ✅ Decide if Apollo is affordable for 500 courses/month")
    print()


if __name__ == "__main__":
    anyio.run(main)
