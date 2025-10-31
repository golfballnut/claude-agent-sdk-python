#!/usr/bin/env python3
"""
Test Hunter.io Fallback Integration - Apollo → Hunter Cascade

Tests the fallback logic when Apollo.io fails to find contacts.
Uses real production failures from 2025-10-29 logs.

Test Flow:
1. Test Apollo.io /people/search (primary)
2. If Apollo fails → Test Hunter.io Domain-Search (fallback)
3. Measure success rate improvement

Goal: Achieve 80-90% success rate with Hunter fallback

Created: Oct 29, 2025
"""

import anyio
import httpx
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def test_apollo_domain_search(course_name: str, domain: str) -> Dict:
    """
    Test Apollo.io /people/search endpoint

    Returns dict with: {found: bool, contacts: List, cost: float}
    """
    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        return {"found": False, "contacts": [], "cost": 0, "error": "No API key"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/search"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": api_key.strip()
            }

            # Search for people at domain with golf-related titles
            payload = {
                "organization_domain": domain,
                "person_titles": [
                    "general manager",
                    "director of golf",
                    "head golf professional",
                    "superintendent",
                    "club manager"
                ],
                "page": 1,
                "per_page": 10
            }

            r = await client.post(url, headers=headers, json=payload)

            if r.status_code == 200:
                data = r.json()
                people = data.get("people", [])

                contacts = []
                for person in people:
                    if person.get("email") and person.get("email_status") in ["verified", "guessed"]:
                        contacts.append({
                            "name": person.get("name"),
                            "title": person.get("title"),
                            "email": person.get("email"),
                            "email_status": person.get("email_status"),
                            "linkedin": person.get("linkedin_url")
                        })

                # Apollo cost: ~$0.023/credit, typically 2-4 credits per search
                cost = 0.023 * 4  # Approximate

                return {
                    "found": len(contacts) > 0,
                    "contacts": contacts,
                    "cost": cost,
                    "credits_used": 4
                }

            return {"found": False, "contacts": [], "cost": 0, "error": f"HTTP {r.status_code}"}

    except Exception as e:
        return {"found": False, "contacts": [], "cost": 0, "error": str(e)}


async def test_hunter_domain_search(domain: str) -> Dict:
    """
    Test Hunter.io Domain-Search endpoint (fallback)

    Note: Tests use direct HTTP calls (not MCP) for simpler debugging.
    Production agents use MCP tools (mcp__hunter-io__Domain-Search).

    Returns dict with: {found: bool, contacts: List, cost: float}
    """
    api_key = os.getenv("HUNTER_API_KEY")
    if not api_key:
        return {"found": False, "contacts": [], "cost": 0, "error": "No API key"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.hunter.io/v2/domain-search"
            params = {
                "domain": domain,
                "api_key": api_key,
                "limit": 10
            }

            r = await client.get(url, params=params)
            data = r.json()

            if data.get("data") and data["data"].get("emails"):
                emails = data["data"]["emails"]

                # Filter: Only verified emails (90%+ confidence) with relevant titles
                relevant_titles = [
                    "general manager", "gm", "director", "manager",
                    "professional", "superintendent", "president",
                    "head professional", "golf"
                ]

                contacts = []
                for email_data in emails:
                    confidence = email_data.get("confidence", 0)
                    position = (email_data.get("position") or "").lower()

                    # Check if title is relevant
                    is_relevant = any(title in position for title in relevant_titles)

                    if confidence >= 90 and is_relevant:
                        contacts.append({
                            "name": f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip(),
                            "title": email_data.get("position"),
                            "email": email_data.get("value"),
                            "confidence": confidence,
                            "type": email_data.get("type")
                        })

                # Hunter cost: Free tier = 25 requests/month, Paid = $49/month (1,000 requests) = $0.049/request
                cost = 0.049

                return {
                    "found": len(contacts) > 0,
                    "contacts": contacts,
                    "cost": cost,
                    "requests_used": 1
                }

            return {"found": False, "contacts": [], "cost": 0.049, "error": "No emails found"}

    except Exception as e:
        return {"found": False, "contacts": [], "cost": 0, "error": str(e)}


async def test_course_fallback(course: Dict) -> Dict:
    """
    Test Apollo → Hunter fallback for a single course

    Returns detailed results including which service succeeded
    """
    course_name = course["course_name"]
    domain = course.get("domain")

    print(f"\n{'='*70}")
    print(f"Testing: {course_name}")
    print(f"Domain: {domain or 'NOT PROVIDED'}")
    print(f"{'='*70}")

    result = {
        "course_name": course_name,
        "course_id": course.get("course_id"),
        "domain": domain,
        "apollo_result": None,
        "hunter_result": None,
        "success": False,
        "source": None,
        "contacts_found": 0,
        "total_cost": 0
    }

    if not domain:
        print("❌ SKIP: No domain provided (need to fix domain discovery first)")
        result["error"] = "No domain provided"
        return result

    # Step 1: Try Apollo (primary)
    print(f"\n🔍 Step 1: Testing Apollo.io...")
    apollo_result = await test_apollo_domain_search(course_name, domain)
    result["apollo_result"] = apollo_result
    result["total_cost"] += apollo_result["cost"]

    if apollo_result["found"]:
        print(f"✅ Apollo SUCCESS: {len(apollo_result['contacts'])} contacts")
        for i, contact in enumerate(apollo_result['contacts'][:3], 1):  # Show first 3
            print(f"   {i}. {contact['name']} - {contact['title']}")
            print(f"      Email: {contact['email']} ({contact['email_status']})")

        result["success"] = True
        result["source"] = "apollo"
        result["contacts_found"] = len(apollo_result['contacts'])
        return result

    print(f"❌ Apollo FAILED: {apollo_result.get('error', 'No contacts found')}")

    # Step 2: Try Hunter (fallback)
    print(f"\n🔄 Step 2: Triggering Hunter.io fallback...")
    await anyio.sleep(0.5)  # Rate limiting

    hunter_result = await test_hunter_domain_search(domain)
    result["hunter_result"] = hunter_result
    result["total_cost"] += hunter_result["cost"]

    if hunter_result["found"]:
        print(f"✅ Hunter SUCCESS: {len(hunter_result['contacts'])} contacts")
        for i, contact in enumerate(hunter_result['contacts'][:3], 1):  # Show first 3
            print(f"   {i}. {contact['name']} - {contact['title']}")
            print(f"      Email: {contact['email']} ({contact['confidence']}% confidence)")

        result["success"] = True
        result["source"] = "hunter"
        result["contacts_found"] = len(hunter_result['contacts'])
        return result

    print(f"❌ Hunter FAILED: {hunter_result.get('error', 'No contacts found')}")
    print(f"\n💔 BOTH FAILED - No contacts found")

    return result


async def main():
    """Run fallback integration test on Apollo failure courses"""

    print("=" * 80)
    print("Hunter.io Fallback Integration Test")
    print("=" * 80)
    print()
    print("Testing Apollo → Hunter cascade on courses where Apollo failed")
    print()

    # Load test data
    data_file = Path(__file__).parent / "data" / "apollo_failure_courses.json"
    with open(data_file) as f:
        data = json.load(f)

    courses = data["courses"]

    # Filter to only courses with domains (skip the 2 without domains for now)
    courses_with_domains = [c for c in courses if c.get("domain")]

    print(f"📊 Test Summary:")
    print(f"   Total courses: {len(courses)}")
    print(f"   Courses with domains: {len(courses_with_domains)}")
    print(f"   Courses without domains: {len(courses) - len(courses_with_domains)}")
    print()

    # Run tests
    results = []

    for course in courses_with_domains:
        result = await test_course_fallback(course)
        results.append(result)

        # Rate limiting between courses
        await anyio.sleep(1.0)

    # Analysis
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)

    apollo_success = sum(1 for r in results if r["source"] == "apollo")
    hunter_success = sum(1 for r in results if r["source"] == "hunter")
    both_failed = sum(1 for r in results if not r["success"])

    total_tested = len(results)
    total_success = apollo_success + hunter_success

    print(f"\n📈 Success Rates:")
    print(f"   Total courses tested: {total_tested}")
    print(f"   Apollo succeeded: {apollo_success} ({apollo_success/total_tested*100:.1f}%)")
    print(f"   Hunter succeeded: {hunter_success} ({hunter_success/total_tested*100:.1f}%) ← Fallback value!")
    print(f"   Both failed: {both_failed} ({both_failed/total_tested*100:.1f}%)")
    print()
    print(f"✅ COMBINED SUCCESS RATE: {total_success}/{total_tested} ({total_success/total_tested*100:.1f}%)")

    # Cost analysis
    avg_cost = sum(r["total_cost"] for r in results) / len(results) if results else 0
    total_cost = sum(r["total_cost"] for r in results)

    print(f"\n💰 Cost Analysis:")
    print(f"   Average cost per course: ${avg_cost:.4f}")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"   Apollo only cost: ~$0.092")
    print(f"   Apollo + Hunter cost: ~${0.092 + 0.049:.3f}")

    # Decision matrix
    print("\n" + "=" * 80)
    print("DECISION MATRIX")
    print("=" * 80)
    print()

    improvement_pct = (hunter_success / total_tested) * 100

    if hunter_success >= 2:  # 40%+ improvement on 5 courses
        print(f"   ✅ RECOMMEND: Add Hunter.io to fallback waterfall")
        print(f"   📈 Improvement: +{improvement_pct:.1f} percentage points")
        print(f"   💰 Additional cost: $0.049/course when Apollo fails")
        print(f"   🎯 Expected final success rate: 80-90%")
        print()
        print("   Next steps:")
        print("   1. Implement fallback logic in Agent 2")
        print("   2. Add domain discovery for courses without domains")
        print("   3. Add website scraping as final fallback (tier 3)")
        print("   4. Integration test full orchestrator")
        print("   5. Deploy to production")
    elif hunter_success >= 1:
        print(f"   ⚠️  BORDERLINE: Hunter adds {hunter_success} courses (+{improvement_pct:.1f}%)")
        print(f"   💭 Consider:")
        print(f"      - Test on larger sample (10-15 courses)")
        print(f"      - Evaluate Hunter confidence thresholds")
        print(f"      - Consider alternative: Website scraping")
    else:
        print(f"   ❌ DISAPPOINTING: Hunter found 0 additional contacts")
        print(f"   🤔 Alternatives:")
        print(f"      1. Add domain discovery for missing domains")
        print(f"      2. Try website scraping (Firecrawl + regex)")
        print(f"      3. Adjust Apollo search strategy (try company name variants)")

    # Save results
    results_file = Path(__file__).parent / "results" / "hunter_fallback_integration.json"
    results_file.parent.mkdir(exist_ok=True)

    output = {
        "test_date": "2025-10-29",
        "test_type": "hunter_fallback_integration",
        "courses_tested": total_tested,
        "apollo_success": apollo_success,
        "hunter_success": hunter_success,
        "both_failed": both_failed,
        "combined_success_rate": (total_success/total_tested*100) if total_tested > 0 else 0,
        "improvement_percentage": improvement_pct,
        "average_cost": avg_cost,
        "total_cost": total_cost,
        "results": results
    }

    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print(f"📁 Results saved to: {results_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(main)
