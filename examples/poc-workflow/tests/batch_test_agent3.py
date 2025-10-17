#!/usr/bin/env python3
"""
Batch Test Agent 3

Tests email/LinkedIn enrichment for all contacts from Agent 2 results
Measures success rate vs 80% baseline from working system
"""

import json
import sys
from pathlib import Path

import anyio

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from agent3_email_finder import enrich_contact


async def run_batch_test():
    print("🧪 Agent 3 Batch Test")
    print("="*70)

    # Load Agent 2 results
    results_file = Path(__file__).parent.parent / "results" / "agent2_test_results.json"

    with open(results_file) as f:
        agent2_data = json.load(f)

    # Extract all staff contacts
    all_contacts = []
    for course_name, course_data in agent2_data["results"].items():
        course_info = course_data["data"]
        website = course_info.get("website", "")

        # Extract domain from website
        import re
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', website)
        domain = domain_match.group(1) if domain_match else "unknown.com"

        for staff in course_info.get("staff", []):
            all_contacts.append({
                "name": staff["name"],
                "title": staff["title"],
                "company": course_name,
                "domain": domain,
            })

    print(f"Total contacts to enrich: {len(all_contacts)}\n")

    results = []
    email_found = 0
    linkedin_found = 0
    total_cost = 0

    for i, contact in enumerate(all_contacts, 1):
        print(f"[{i}/{len(all_contacts)}] {contact['name']} - {contact['title']}")
        print("-"*70)

        try:
            result = await enrich_contact(contact)

            email = result.get("email")
            email_method = result.get("email_method")
            linkedin = result.get("linkedin_url")
            cost = result.get("_agent3_cost", 0)

            # Count successes (exclude general/manual fallbacks)
            if email and email_method not in ["course_general_email", "needs_manual_research"]:
                email_found += 1
                print(f"   ✅ Email: {email} ({email_method})")
            else:
                print("   ❌ Email: Not found")

            if linkedin:
                linkedin_found += 1
                print(f"   ✅ LinkedIn: {linkedin}")
            else:
                print("   ⚠️  LinkedIn: Not found")

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
    print("📊 SUMMARY")
    print(f"{'='*70}\n")

    print(f"Total Contacts: {len(all_contacts)}")
    print("\nSuccess Rates:")
    email_rate = (email_found / len(all_contacts)) * 100
    linkedin_rate = (linkedin_found / len(all_contacts)) * 100
    print(f"   Email: {email_found}/{len(all_contacts)} ({email_rate:.0f}%)")
    print(f"   LinkedIn: {linkedin_found}/{len(all_contacts)} ({linkedin_rate:.0f}%)")

    avg_cost = total_cost / len(all_contacts) if all_contacts else 0
    print("\nCosts:")
    print(f"   Per Contact: ${avg_cost:.4f}")
    print(f"   Total: ${total_cost:.4f}")
    print(f"   Budget: {'✅ Under' if avg_cost < 0.02 else '⚠️ Over'} ($0.02 target)")

    # Comparison to baseline
    print(f"\n{'='*70}")
    print("📈 VS BASELINE (Working System)")
    print(f"{'='*70}")
    print(f"   Email: {email_rate:.0f}% (baseline: 80%)")
    print(f"   Status: {'✅ Meets' if email_rate >= 70 else '⚠️ Below'} threshold")

    # Save
    output = {
        "test_date": "2025-10-16",
        "total_contacts": len(all_contacts),
        "email_found": email_found,
        "linkedin_found": linkedin_found,
        "email_success_rate": email_rate,
        "linkedin_success_rate": linkedin_rate,
        "avg_cost": avg_cost,
        "total_cost": total_cost,
        "results": results,
    }

    output_file = Path(__file__).parent.parent / "results" / "agent3_batch_test_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Saved to: {output_file}")

    # Final status
    if email_rate >= 70 and avg_cost < 0.02:
        print(f"\n{'='*70}")
        print("✅ AGENT 3 PRODUCTION READY")
        print(f"{'='*70}")
    else:
        print(f"\n{'='*70}")
        print("⚠️  NEEDS IMPROVEMENT")
        print(f"{'='*70}")


if __name__ == "__main__":
    anyio.run(run_batch_test)
