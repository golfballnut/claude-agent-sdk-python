#!/usr/bin/env python3
"""
Test Agent 4: LinkedIn Finder

Tests LinkedIn discovery for contacts missing LinkedIn from Agent 3
Target: 20-30% success rate on Hunter.io misses
"""

import json
import sys
from pathlib import Path

import anyio

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from agent4_linkedin_finder import find_linkedin_url


async def run_test():
    print("🧪 Agent 4: LinkedIn Finder Test")
    print("="*70)

    # Load Agent 3 results
    results_file = Path(__file__).parent.parent / "results" / "agent3_batch_test_results.json"

    with open(results_file) as f:
        agent3_data = json.load(f)

    # Filter contacts WITHOUT LinkedIn from Agent 3
    contacts_missing_linkedin = []

    for contact_result in agent3_data["results"]:
        contact = contact_result["contact"]
        if not contact_result.get("linkedin_url"):
            contacts_missing_linkedin.append(contact)

    print(f"Contacts missing LinkedIn from Agent 3: {len(contacts_missing_linkedin)}")
    print("Target: Find LinkedIn for these contacts\n")

    results = []
    linkedin_found = 0
    total_cost = 0

    for i, contact in enumerate(contacts_missing_linkedin, 1):
        print(f"\n[{i}/{len(contacts_missing_linkedin)}] {contact['name']} - {contact['title']}")
        print("-"*70)

        try:
            result = await find_linkedin_url(contact)

            linkedin = result.get("linkedin_url")
            method = result.get("method")
            cost = result.get("_agent4_cost", 0)

            if linkedin:
                linkedin_found += 1
                print(f"   ✅ Found: {linkedin}")
                print(f"   Method: {method}")
            else:
                print("   ❌ Not found (clean null)")

            print(f"   Cost: ${cost:.4f}")

            results.append(result)
            total_cost += cost

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({"contact": contact, "error": str(e)})

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print(f"\n{'='*70}")
    print("📊 AGENT 4 RESULTS")
    print(f"{'='*70}\n")

    success_rate = (linkedin_found / len(contacts_missing_linkedin)) * 100 if contacts_missing_linkedin else 0
    avg_cost = total_cost / len(contacts_missing_linkedin) if contacts_missing_linkedin else 0

    print(f"LinkedIn Found: {linkedin_found}/{len(contacts_missing_linkedin)} ({success_rate:.0f}%)")
    print(f"Average Cost: ${avg_cost:.4f}")
    print(f"Total Cost: ${total_cost:.4f}")

    print(f"\n{'='*70}")
    print("📈 COMBINED COVERAGE (Agent 3 + 4)")
    print(f"{'='*70}")

    # Load Agent 3 stats
    agent3_linkedin = agent3_data["linkedin_found"]
    agent3_total = agent3_data["total_contacts"]

    combined_linkedin = agent3_linkedin + linkedin_found
    combined_rate = (combined_linkedin / agent3_total) * 100

    print(f"   Agent 3 (Hunter.io): {agent3_linkedin}/{agent3_total} (25%)")
    print(f"   Agent 4 (BrightData): {linkedin_found}/{len(contacts_missing_linkedin)} ({success_rate:.0f}%)")
    print(f"   Combined Total: {combined_linkedin}/{agent3_total} ({combined_rate:.0f}%)")

    # Evaluation
    print(f"\n{'='*70}")
    if combined_rate >= 40:
        print("✅ EXCELLENT - Agent 4 adds meaningful value!")
    elif combined_rate >= 30:
        print("✅ GOOD - Agent 4 improves coverage")
    else:
        print("⚠️  LIMITED - Agent 4 impact minimal")
    print(f"{'='*70}")

    # Save
    output = {
        "test_date": "2025-10-16",
        "contacts_tested": len(contacts_missing_linkedin),
        "linkedin_found": linkedin_found,
        "success_rate": success_rate,
        "avg_cost": avg_cost,
        "total_cost": total_cost,
        "combined_coverage": combined_rate,
        "results": results,
    }

    output_file = Path(__file__).parent.parent / "results" / "agent4_test_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Saved to: {output_file}")


if __name__ == "__main__":
    anyio.run(run_test)
