#!/usr/bin/env python3
"""
Batch Test Agent 2

Runs Agent 2 against all 5 URLs from Agent 1 results.
Validates production readiness.
"""

import json
import sys
from pathlib import Path

import anyio

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from agent2_data_extractor import extract_contact_data


async def run_batch_test():
    print("🧪 Agent 2 Batch Test")
    print("=" * 70)

    # Load Agent 1 results
    results_file = Path(__file__).parent.parent / "results" / "agent1_test_results.json"

    with open(results_file) as f:
        agent1_results = json.load(f)

    urls = [data["url"] for data in agent1_results.values()]

    print(f"Testing {len(urls)} URLs from Agent 1\n")

    results = {}
    total_cost = 0
    total_time = 0
    successful = 0
    failed = 0

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] {url}")
        print("-" * 70)

        try:
            import time
            start = time.time()

            result = await extract_contact_data(url)
            elapsed = time.time() - start

            course_name = result["data"].get("course_name", "Unknown")

            print(f"   ✅ {course_name}")
            print(f"   Website: {result['data'].get('website', 'N/A')}")
            print(f"   Phone: {result['data'].get('phone', 'N/A')}")
            print(f"   Staff: {len(result['data'].get('staff', []))}")
            print(f"   Cost: ${result['cost']:.4f}")
            print(f"   Time: {elapsed:.2f}s")

            results[course_name] = {
                "url": url,
                "data": result["data"],
                "cost": result["cost"],
                "time_seconds": round(elapsed, 3),
                "turns": result["turns"],
                "status": "success",
            }

            total_cost += result["cost"] if result["cost"] else 0
            total_time += elapsed
            successful += 1

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed += 1

            results[url] = {
                "url": url,
                "error": str(e),
                "status": "failed",
            }

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("📊 SUMMARY")
    print(f"{'=' * 70}\n")

    print(f"Success Rate: {successful}/{len(urls)} ({successful/len(urls)*100:.0f}%)")

    if successful > 0:
        avg_cost = total_cost / successful
        avg_time = total_time / successful

        print("\nPerformance:")
        print(f"   Avg Cost: ${avg_cost:.4f}")
        print(f"   Total Cost: ${total_cost:.4f}")
        print(f"   Avg Time: {avg_time:.2f}s")
        print(f"   Total Time: {total_time:.2f}s")

        print("\nBudget Analysis:")
        if avg_cost < 0.02:
            under_by = ((0.02 - avg_cost) / 0.02) * 100
            print(f"   ✅ ${avg_cost:.4f} per extraction ({under_by:.0f}% under budget)")
        else:
            over_by = ((avg_cost - 0.02) / 0.02) * 100
            print(f"   ❌ ${avg_cost:.4f} per extraction ({over_by:.0f}% over budget)")

        print("\nProduction Projections (500 workflows/day):")
        daily_cost = avg_cost * 500
        monthly_cost = daily_cost * 30
        print(f"   Daily: ${daily_cost:.2f}")
        print(f"   Monthly: ${monthly_cost:.2f}")

    if failed > 0:
        print(f"\n⚠️  {failed} URL(s) failed")

    # Status check
    if successful == len(urls) and avg_cost < 0.02:
        print(f"\n{'=' * 70}")
        print("✅ AGENT 2 PRODUCTION READY")
        print(f"{'=' * 70}")
    else:
        print(f"\n{'=' * 70}")
        print("⚠️  AGENT 2 NEEDS OPTIMIZATION")
        print(f"{'=' * 70}")

    # Save results
    output = {
        "test_date": "2025-10-16",
        "total_tests": len(urls),
        "successful": successful,
        "failed": failed,
        "avg_cost": avg_cost if successful > 0 else None,
        "avg_time_seconds": avg_time if successful > 0 else None,
        "results": results,
    }

    output_file = Path(__file__).parent.parent / "results" / "agent2_test_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Saved to: {output_file}")


if __name__ == "__main__":
    anyio.run(run_batch_test)
