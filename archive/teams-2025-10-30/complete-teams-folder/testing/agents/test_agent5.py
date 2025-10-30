#!/usr/bin/env python3
"""
Test Agent 5: Phone Finder

Tests phone discovery for contacts using Perplexity AI
Target: 70-100% success rate based on MCP baseline (4/4 = 100%)
"""

import json
import sys
from pathlib import Path

import anyio

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from agent5_phone_finder import find_phone


async def run_test():
    print("🧪 Agent 5: Phone Finder Test")
    print("="*70)
    print("Using Perplexity AI for phone discovery\n")

    # Load Agent 3 results (has contact info + state from course data)
    results_file = Path(__file__).parent.parent / "results" / "agent3_batch_test_results.json"

    with open(results_file) as f:
        agent3_data = json.load(f)

    # Get first 10 contacts
    contacts = agent3_data["results"][:10]

    print(f"Testing {len(contacts)} contacts\n")

    results = []
    phones_found = 0
    total_cost = 0

    for i, contact_data in enumerate(contacts, 1):
        # Prepare contact for Agent 5
        contact = {
            "name": contact_data["name"],
            "title": contact_data["title"],
            "company": contact_data["company"],
            "state": "Virginia"  # All our test contacts are in VA
        }

        print(f"\n[{i}/{len(contacts)}] {contact['name']} - {contact['title']}")
        print("-"*70)

        try:
            result = await find_phone(contact)

            phone = result.get("phone")
            method = result.get("method")
            source = result.get("phone_source")
            cost = result.get("_agent5_cost", 0)

            if phone:
                phones_found += 1
                print(f"   ✅ {phone}")
                print(f"   Source: {source}")
            else:
                print("   ❌ Not found (clean null)")

            print(f"   Method: {method}")
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
    print("📊 AGENT 5 RESULTS")
    print(f"{'='*70}\n")

    success_rate = (phones_found / len(contacts)) * 100 if contacts else 0
    avg_cost = total_cost / len(contacts) if contacts else 0

    print(f"Phones Found: {phones_found}/{len(contacts)} ({success_rate:.0f}%)")
    print(f"Average Cost: ${avg_cost:.4f}")
    print(f"Total Cost: ${total_cost:.4f}")

    print(f"\n{'='*70}")
    if success_rate >= 70:
        print("✅ EXCELLENT - Perplexity phone discovery works!")
    elif success_rate >= 50:
        print("✅ GOOD - Solid phone coverage")
    else:
        print("⚠️  LIMITED - Phone discovery challenging")
    print(f"{'='*70}")

    # Save results
    output = {
        "test_date": "2025-10-17",
        "contacts_tested": len(contacts),
        "phones_found": phones_found,
        "success_rate": success_rate,
        "avg_cost": avg_cost,
        "total_cost": total_cost,
        "results": results,
    }

    output_file = Path(__file__).parent.parent / "results" / "agent5_test_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Saved to: {output_file}")

    # Print detailed results
    print(f"\n{'='*70}")
    print("📋 DETAILED RESULTS")
    print(f"{'='*70}\n")

    for i, result in enumerate(results, 1):
        name = result.get("name", "Unknown")
        phone = result.get("phone", "Not found")
        print(f"{i}. {name}: {phone}")

    print(f"\n{'='*70}")
    print("MCP Baseline: 100% (4/4)")
    print(f"Agent 5 SDK: {success_rate:.0f}% ({phones_found}/{len(contacts)})")
    print(f"{'='*70}")


if __name__ == "__main__":
    anyio.run(run_test)
