#!/usr/bin/env python3
"""
Test Fallback Data Sources for Golf Course Contacts

Purpose: Validate alternate data sources when PGA.org has no contacts

Test Courses (NC courses from test_agent2_firecrawl.py):
1. Course 1036 - Pine Ridge Classic
2. Course 1037 - Mountain Aire
3. Course 1039 - Alamance CC

Fallback Sources Tested:
1. LinkedIn Company Pages (via BrightData)
2. Course Website Staff Pages (via Jina Reader)

Success Criteria:
- Find 2+ contacts per course from at least one fallback source
- Cost < $0.02 per course per source
- Extract: name, title minimum
- Success rate > 60% across all 3 courses

Phase 1 Manual Test Results:
=================================
LinkedIn Company Fallback:
- Alamance CC (1039): ✅ EXCELLENT - 4 staff found (Charlie Nolette CCM - GM/COO, 3 others)
- Mountain Aire (1037): ⚠️ PARTIAL - Individual profiles (Andy Singleton - GM, Chris Parham - Head Pro)
- Pine Ridge Classic (1036): ❌ NONE - No LinkedIn presence

Website Fallback: TBD (Phase 1 continuing)

Next Steps:
1. Automate LinkedIn company search + scrape
2. Test website fallback for all 3
3. Calculate success rates and costs
4. Implement as Agent 4.5 and Agent 2.5
"""

import anyio
import json
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

# Test cases - NC courses that may have empty PGA.org contacts
TEST_COURSES = [
    {
        "id": 1036,
        "name": "Pine Ridge Classic",
        "pga_url": "https://directory.pga.org/facility/detail/996163459",
        "location": "North Carolina"
    },
    {
        "id": 1037,
        "name": "Mountain Aire",
        "pga_url": "https://directory.pga.org/facility/detail/988857706",
        "location": "North Carolina"
    },
    {
        "id": 1039,
        "name": "Alamance CC",
        "pga_url": "https://directory.pga.org/facility/detail/750795095",
        "location": "North Carolina"
    }
]


async def test_linkedin_company_fallback(course: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test LinkedIn company page as fallback source

    Steps:
    1. Search for "{course_name} golf {location} LinkedIn company"
    2. Extract company page URL from search results
    3. Scrape company page to get staff from "Employees" section
    4. Extract names + titles

    Returns:
        {
            "success": bool,
            "staff": [{"name": str, "title": str, "linkedin_url": str}],
            "company_url": str,
            "cost_usd": float,
            "method": "linkedin_company"
        }
    """
    print(f"\n{'='*70}")
    print(f"Testing LinkedIn Fallback: {course['name']}")
    print(f"{'='*70}")

    # TODO: Implement using mcp__BrightData__search_engine
    # TODO: Then mcp__BrightData__scrape_as_markdown on company page
    # TODO: Parse markdown for employee names and titles

    return {
        "success": False,
        "staff": [],
        "company_url": None,
        "cost_usd": 0.01,  # Estimated
        "method": "linkedin_company",
        "error": "Not implemented - use manual test results from Phase 1"
    }


async def test_website_fallback(course: Dict[str, Any], website_url: str) -> Dict[str, Any]:
    """
    Test golf course website as fallback source

    Steps:
    1. Try common staff page URLs: /staff, /about/team, /contact, /about-us
    2. Use Jina Reader to scrape each URL
    3. Look for patterns: names + titles in lists or cards
    4. Extract contact data

    Returns:
        {
            "success": bool,
            "staff": [{"name": str, "title": str}],
            "source_url": str,
            "cost_usd": float,
            "method": "course_website"
        }
    """
    print(f"\n{'='*70}")
    print(f"Testing Website Fallback: {course['name']}")
    print(f"Website: {website_url}")
    print(f"{'='*70}")

    # TODO: Implement using mcp__jina__jina_reader
    # TODO: Try /staff, /about/team, /contact pages
    # TODO: Parse markdown for staff listings

    return {
        "success": False,
        "staff": [],
        "source_url": None,
        "cost_usd": 0.0,  # Jina is free tier
        "method": "course_website",
        "error": "Not implemented - awaiting Phase 1 completion"
    }


async def main():
    """Test fallback data sources for all 3 NC courses"""
    print("🔍 Test Fallback Data Sources")
    print("=" * 70)
    print(f"Testing {len(TEST_COURSES)} NC courses with potential empty PGA.org contacts")
    print()

    results = []

    for course in TEST_COURSES:
        print(f"\n{'='*70}")
        print(f"Course {course['id']}: {course['name']}")
        print(f"{'='*70}")

        # Test LinkedIn fallback
        linkedin_result = await test_linkedin_company_fallback(course)
        results.append({
            "course": course['name'],
            "source": "linkedin_company",
            "result": linkedin_result
        })

        # Test website fallback (TODO: get website URL from Agent 2 first)
        # website_result = await test_website_fallback(course, website_url="TBD")
        # results.append({
        #     "course": course['name'],
        #     "source": "course_website",
        #     "result": website_result
        # })

    # Summary
    print(f"\n{'='*70}")
    print(f"TEST RESULTS SUMMARY")
    print(f"{'='*70}")

    linkedin_success = sum(1 for r in results if r['source'] == 'linkedin_company' and r['result']['success'])
    # website_success = sum(1 for r in results if r['source'] == 'course_website' and r['result']['success'])

    print(f"\nLinkedIn Company Fallback:")
    print(f"  Success Rate: {linkedin_success}/{len(TEST_COURSES)} ({linkedin_success/len(TEST_COURSES)*100:.0f}%)")

    for result in results:
        if result['source'] == 'linkedin_company':
            status = "✅" if result['result']['success'] else "❌"
            staff_count = len(result['result']['staff'])
            print(f"    {status} {result['course']}: {staff_count} staff")

    # print(f"\nCourse Website Fallback:")
    # print(f"  Success Rate: {website_success}/{len(TEST_COURSES)} ({website_success/len(TEST_COURSES)*100:.0f}%)")

    print(f"\n{'='*70}")
    print(f"PHASE 1 MANUAL TEST RESULTS (from interactive testing):")
    print(f"{'='*70}")
    print(f"LinkedIn Company:")
    print(f"  ✅ Alamance CC: 4 staff (Charlie Nolette CCM - GM/COO, + 3 others)")
    print(f"  ⚠️  Mountain Aire: Found individual profiles (Andy Singleton - GM)")
    print(f"  ❌ Pine Ridge Classic: No LinkedIn presence")
    print(f"\nSuccess Rate: 1-2/3 (33-66%) - VIABLE FALLBACK for courses with LinkedIn pages")
    print(f"Cost: ~$0.01 per scrape (BrightData)")
    print(f"\nRecommendation: Implement Agent 4.5 for LinkedIn company fallback")


if __name__ == "__main__":
    anyio.run(main)
