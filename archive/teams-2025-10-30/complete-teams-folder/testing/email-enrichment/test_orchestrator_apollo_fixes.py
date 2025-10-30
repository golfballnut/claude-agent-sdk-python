#!/usr/bin/env python3
"""
Test Orchestrator Apollo Fixes - Full Workflow Validation

Tests the complete enrichment workflow with our fixes:
1. Domain-first Apollo search
2. Fixed domain discovery (Agent 1)
3. Hunter.io fallback

Runs on the 5 courses that failed in production (Oct 29, 2025)

Goal: Validate 80-100% success rate with all fixes in place

Created: Oct 29, 2025
"""

import anyio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator_apollo import enrich_course


async def run_test():
    """Run full orchestrator on Apollo failure courses"""

    print("=" * 80)
    print("Orchestrator Apollo Fixes - Full Workflow Test")
    print("=" * 80)
    print()
    print("Testing complete enrichment workflow with fixes:")
    print("  ✅ Domain-first Apollo search")
    print("  ✅ Fixed domain discovery (Agent 1)")
    print("  ✅ Hunter.io fallback")
    print()

    # Load test data
    data_file = Path(__file__).parent / "data" / "apollo_failure_courses.json"
    with open(data_file) as f:
        data = json.load(f)

    courses = data["courses"]

    print(f"📊 Test Plan:")
    print(f"   Courses to test: {len(courses)}")
    print(f"   Expected success: 4-5/5 (80-100%)")
    print(f"   Cost target: <$0.20/course average")
    print()

    # Track results
    results = []

    for i, course in enumerate(courses, 1):
        course_name = course["course_name"]
        domain = course.get("domain")
        course_id = course.get("course_id")

        print(f"\n{'='*70}")
        print(f"[{i}/{len(courses)}] Testing: {course_name}")
        print(f"{'='*70}")
        print(f"Domain: {domain or 'NOT PROVIDED'}")
        print(f"Course ID: {course_id}")
        print(f"Previous error: {course.get('apollo_error')}")
        print()

        try:
            # Run full orchestrator
            result = await enrich_course(
                course_name=course_name,
                state_code="NC",
                domain=domain,
                course_id=course_id,
                use_test_tables=True  # Don't write to production tables
            )

            success = result.get("success", False)
            contacts_count = len(result.get("summary", {}).get("contacts", []))
            total_cost = result.get("summary", {}).get("total_cost", 0)
            source = result.get("summary", {}).get("source", "unknown")

            results.append({
                "course_name": course_name,
                "course_id": course_id,
                "domain": domain,
                "success": success,
                "contacts_count": contacts_count,
                "total_cost": total_cost,
                "source": source,
                "error": result.get("error")
            })

            if success:
                print(f"\n✅ SUCCESS: {contacts_count} contacts found")
                print(f"   Source: {source}")
                print(f"   Cost: ${total_cost:.4f}")
            else:
                print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
                print(f"   Cost: ${total_cost:.4f}")

        except Exception as e:
            print(f"\n❌ EXCEPTION: {e}")
            results.append({
                "course_name": course_name,
                "course_id": course_id,
                "domain": domain,
                "success": False,
                "contacts_count": 0,
                "total_cost": 0,
                "source": "error",
                "error": str(e)
            })

        # Rate limiting between courses
        if i < len(courses):
            await anyio.sleep(2.0)

    # Analysis
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)

    success_count = sum(1 for r in results if r["success"])
    apollo_count = sum(1 for r in results if r["source"] == "apollo")
    hunter_count = sum(1 for r in results if r["source"] == "hunter_fallback")
    failed_count = sum(1 for r in results if not r["success"])

    total_tested = len(results)
    success_rate = (success_count / total_tested * 100) if total_tested > 0 else 0

    avg_cost = sum(r["total_cost"] for r in results) / len(results) if results else 0
    total_cost = sum(r["total_cost"] for r in results)

    print(f"\n📊 Success Metrics:")
    print(f"   Total courses: {total_tested}")
    print(f"   Succeeded: {success_count} ({success_rate:.1f}%)")
    print(f"   Failed: {failed_count} ({100 - success_rate:.1f}%)")
    print()
    print(f"📈 Source Breakdown:")
    print(f"   Apollo primary: {apollo_count}")
    print(f"   Hunter fallback: {hunter_count}")
    print()
    print(f"💰 Cost Analysis:")
    print(f"   Average cost/course: ${avg_cost:.4f}")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"   Target: <$0.20/course")
    print(f"   {'✅ Under budget!' if avg_cost < 0.20 else '⚠️  Over budget'}")

    # Detailed results
    print(f"\n📋 Detailed Results:")
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"\n   {status} {r['course_name']}")
        print(f"      Domain: {r['domain'] or 'None'}")
        print(f"      Contacts: {r['contacts_count']}")
        print(f"      Source: {r['source']}")
        print(f"      Cost: ${r['total_cost']:.4f}")
        if r.get("error"):
            print(f"      Error: {r['error']}")

    # Comparison to baseline
    print("\n" + "=" * 80)
    print("COMPARISON TO BASELINE")
    print("=" * 80)
    print()
    print(f"Before fixes:")
    print(f"   Success rate: 44% (4/9 courses in production)")
    print(f"   No fallback logic")
    print(f"   Domain issues not handled")
    print()
    print(f"After fixes:")
    print(f"   Success rate: {success_rate:.1f}% ({success_count}/{total_tested} courses)")
    print(f"   Hunter fallback: {hunter_count} uses")
    print(f"   Domain discovery: Fixed")
    print()
    if success_rate >= 80:
        print(f"   ✅ TARGET MET: {success_rate:.1f}% ≥ 80% goal")
        print()
        print("   🎯 Ready for production deployment!")
    elif success_rate >= 70:
        print(f"   ⚠️  CLOSE: {success_rate:.1f}% (need 80%+)")
        print()
        print("   💡 Consider:")
        print("      - Review failed courses for patterns")
        print("      - Adjust Hunter.io filters")
        print("      - Add website scraping fallback")
    else:
        print(f"   ❌ BELOW TARGET: {success_rate:.1f}% < 70%")
        print()
        print("   🔍 Debug required:")
        print("      - Check Apollo API responses")
        print("      - Verify domain discovery logic")
        print("      - Review error messages")

    # Save results
    results_file = Path(__file__).parent / "results" / "orchestrator_apollo_fixes.json"
    results_file.parent.mkdir(exist_ok=True)

    output = {
        "test_date": "2025-10-29",
        "test_type": "orchestrator_full_workflow",
        "fixes_applied": [
            "Domain-first Apollo search",
            "Fixed domain discovery (Agent 1)",
            "Hunter.io fallback"
        ],
        "courses_tested": total_tested,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": success_rate,
        "apollo_primary": apollo_count,
        "hunter_fallback": hunter_count,
        "average_cost": avg_cost,
        "total_cost": total_cost,
        "under_budget": avg_cost < 0.20,
        "target_met": success_rate >= 80,
        "results": results
    }

    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print(f"📁 Results saved to: {results_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(run_test)
