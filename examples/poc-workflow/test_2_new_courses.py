#!/usr/bin/env python3
"""
Test orchestrator on 2 NEW Virginia courses
- Different types (public vs private)
- Fresh data (no cache)
- Cost and data quality validation
"""

import anyio
import json
from pathlib import Path
import sys

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))

from orchestrator import enrich_course


async def main():
    print("🧪 Testing 2 NEW Virginia Courses")
    print("="*70)
    print("Goal: Validate refactored Agent 6/6.5 across course types\n")

    test_courses = [
        {
            "name": "Belmont Golf Course",
            "state": "VA",
            "expected_type": "PUBLIC (budget-oriented)",
            "location": "Richmond, VA"
        },
        {
            "name": "Stonehenge Golf & Country Club",
            "state": "VA",
            "expected_type": "PRIVATE (high-end)",
            "location": "Richmond, VA"
        }
    ]

    results = []

    for i, course_info in enumerate(test_courses, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}/2: {course_info['name']}")
        print(f"Expected Type: {course_info['expected_type']}")
        print(f"{'='*70}\n")

        try:
            result = await enrich_course(
                course_info["name"],
                course_info["state"]
            )

            results.append({
                "course_info": course_info,
                "result": result
            })

            # Quick summary
            if result["success"]:
                print(f"\n✅ {course_info['name']} - SUCCESS")
                print(f"   Cost: ${result['summary']['total_cost_usd']:.4f}")
                print(f"   Time: {result['summary']['total_duration_seconds']:.1f}s")
                print(f"   Contacts: {result['summary']['contacts_enriched']}")
            else:
                print(f"\n❌ {course_info['name']} - FAILED")
                print(f"   Error: {result['error']}")

        except Exception as e:
            print(f"\n❌ {course_info['name']} - EXCEPTION")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

            results.append({
                "course_info": course_info,
                "result": {
                    "success": False,
                    "error": str(e)
                }
            })

    # ========================================================================
    # Summary Report
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY REPORT")
    print(f"{'='*70}")

    successful = sum(1 for r in results if r["result"].get("success"))
    total = len(results)

    print(f"Success Rate: {successful}/{total} ({successful/total*100:.0f}%)")

    if successful > 0:
        total_cost = sum(r["result"]["summary"]["total_cost_usd"] for r in results if r["result"].get("success"))
        avg_cost = total_cost / successful
        print(f"Avg Cost: ${avg_cost:.4f} per course")

        total_time = sum(r["result"]["summary"]["total_duration_seconds"] for r in results if r["result"].get("success"))
        avg_time = total_time / successful
        print(f"Avg Time: {avg_time:.1f}s per course")

        total_contacts = sum(r["result"]["summary"]["contacts_enriched"] for r in results if r["result"].get("success"))
        print(f"Total Contacts: {total_contacts}")

    # Save summary
    output_file = Path(__file__).parent / "results" / "test_summary_2_courses.json"
    with open(output_file, "w") as f:
        json.dump({
            "test_date": "2025-01-17",
            "test_type": "refactored_agent6_validation",
            "results": results,
            "summary": {
                "total_courses": total,
                "successful": successful,
                "success_rate": f"{successful/total*100:.0f}%" if total > 0 else "0%"
            }
        }, f, indent=2)

    print(f"\n✅ Summary saved to: {output_file}")
    print(f"\n📁 JSON Files Location:")
    print(f"   results/enrichment/enrichment_*.json")

    print(f"\n{'='*70}")


if __name__ == "__main__":
    anyio.run(main)
