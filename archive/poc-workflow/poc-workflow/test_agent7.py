#!/usr/bin/env python3
"""Test Agent 7 on 5 courses from previous water hazard test"""

import anyio
import json
from pathlib import Path
import sys

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))

from agent7_water_hazard_counter import count_multiple_courses


async def main():
    print("🌊 Agent 7 Testing: 5 Virginia Courses")
    print("="*70)

    # Test courses from water_hazard_test_results.json
    test_courses = [
        {
            "course_name": "Quinton Oaks Golf Course",
            "state": "Virginia",
            "website": "https://quintonoaks.com/"
        },
        {
            "course_name": "Red Wing Lake Golf Course",
            "state": "Virginia",
            "website": "https://www.redwinglakegolf.com/"
        },
        {
            "course_name": "Richmond Country Club",
            "state": "Virginia",
            "website": "https://www.richmondcountryclubva.com/"
        },
        {
            "course_name": "River Creek Club",
            "state": "Virginia",
            "website": "https://www.invitedclubs.com/clubs/river-creek-club"
        },
        {
            "course_name": "Riverfront Golf Club",
            "state": "Virginia",
            "website": "https://www.riverfrontgolf.com/"
        }
    ]

    results = await count_multiple_courses(test_courses)

    # Calculate success metrics
    total = len(results)
    found = sum(1 for r in results if r.get("found"))
    high_conf = sum(1 for r in results if r.get("confidence") == "high")
    medium_conf = sum(1 for r in results if r.get("confidence") == "medium")
    low_conf = sum(1 for r in results if r.get("confidence") == "low")
    total_cost = sum(r.get("cost", 0) for r in results)
    avg_cost = total_cost / total if total > 0 else 0

    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"Total Courses: {total}")
    print(f"Found: {found} ({found/total*100:.0f}% success rate)")
    print(f"  - High Confidence: {high_conf}")
    print(f"  - Medium Confidence: {medium_conf}")
    print(f"  - Low Confidence: {low_conf}")
    print(f"  - Not Found: {total - found}")
    print(f"\nTotal Cost: ${total_cost:.4f}")
    print(f"Avg Cost: ${avg_cost:.4f} per course")

    # Save results
    output_file = Path(__file__).parent / "results" / "agent7_test_results.json"
    output_file.parent.mkdir(exist_ok=True)

    output_data = {
        "test_date": "2025-01-17",
        "agent": "agent7_water_hazard_counter",
        "total_courses": total,
        "successful_finds": found,
        "success_rate": round(found / total * 100, 1),
        "avg_cost": round(avg_cost, 4),
        "total_cost": round(total_cost, 4),
        "confidence_distribution": {
            "high": high_conf,
            "medium": medium_conf,
            "low": low_conf,
            "none": total - found
        },
        "results": results
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")

    # Comparison to previous test
    print("\n📈 COMPARISON TO PREVIOUS TEST:")
    print("  Previous: 60% success rate (3/5 courses)")
    print(f"  Current: {found/total*100:.0f}% success rate ({found}/{total} courses)")
    if found > 3:
        print(f"  🎉 IMPROVEMENT: +{found - 3} more courses found!")
    elif found == 3:
        print("  ✓ Same success rate")
    else:
        print(f"  ⚠️  REGRESSION: -{3 - found} fewer courses found")


if __name__ == "__main__":
    anyio.run(main)
