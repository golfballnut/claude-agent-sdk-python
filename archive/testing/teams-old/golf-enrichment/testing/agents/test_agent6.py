#!/usr/bin/env python3
"""
Test Agent 6: Business Intelligence (Range Ball)

Tests business-specific intelligence gathering for 10 contacts:
- Segmentation (high-end vs budget classification)
- Opportunity scoring (6 opportunity types)
- Value-prop specific conversation starters
"""

import json
import sys
from pathlib import Path

import anyio

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from agent6_context_enrichment import enrich_context


async def run_test():
    print("🧪 Agent 6: Business Intelligence Test")
    print("="*70)

    # Load Agent 3 results (use first 10 contacts)
    results_file = Path(__file__).parent.parent / "results" / "agent3_batch_test_results.json"

    with open(results_file) as f:
        agent3_data = json.load(f)

    # Get first 10 contacts
    all_contacts = agent3_data["results"][:10]

    print(f"Testing {len(all_contacts)} contacts for range ball business intelligence\n")

    results = []
    total_cost = 0
    total_starters = 0

    # Segmentation tracking
    high_end_count = 0
    budget_count = 0
    both_count = 0
    unknown_count = 0

    # Opportunity tracking
    opportunity_scores = {
        "range_ball_buy": [],
        "range_ball_sell": [],
        "range_ball_lease": [],
        "proshop_ecommerce": [],
        "superintendent_partnership": [],
        "ball_retrieval": []
    }

    success_count = 0

    for i, contact in enumerate(all_contacts, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(all_contacts)}] {contact['name']} - {contact['title']}")
        print(f"Company: {contact['company']}")
        print("-"*70)

        try:
            result = await enrich_context(contact)

            # Extract metrics
            target = result.get("_agent6_primary_target", "unknown")
            confidence = result.get("_agent6_confidence", 0)
            starters_count = result.get("_agent6_starters_count", 0)
            top_opps = result.get("_agent6_top_opportunities", [])
            cost = result.get("_agent6_cost", 0)

            # Track segmentation
            if target == "high-end":
                high_end_count += 1
            elif target == "budget":
                budget_count += 1
            elif target == "both":
                both_count += 1
            else:
                unknown_count += 1

            # Track opportunities
            intel = result.get("business_intel", {})
            if intel:
                opps = intel.get("opportunities", {})
                for opp_type, score in opps.items():
                    if opp_type in opportunity_scores:
                        opportunity_scores[opp_type].append(score)

            # Count as success if we got segmentation + opportunities + starters
            if target != "unknown" and starters_count >= 5 and top_opps:
                success_count += 1
                print("\n✅ SUCCESS")
            else:
                print("\n⚠️  PARTIAL")

            print(f"   Segment: {target.upper()} ({confidence}/10 confidence)")

            if top_opps:
                print("   Top Opportunities:")
                for opp in top_opps:
                    print(f"      - {opp['type']}: {opp['score']}/10")

            print(f"   Starters: {starters_count}")
            print(f"   Cost: ${cost:.4f}")

            # Show sample conversation starters
            if intel:
                starters = intel.get("conversation_starters", [])
                if starters:
                    print("\n   💬 Sample Starters:")
                    for j, starter in enumerate(starters[:2], 1):
                        text = starter.get("text", "")
                        score = starter.get("relevance", 0)
                        value_prop = starter.get("value_prop", "unknown")
                        # Truncate long starters
                        display_text = text[:70] + "..." if len(text) > 70 else text
                        print(f"      {j}. [{score}/10 | {value_prop}] {display_text}")

            results.append(result)
            total_cost += cost
            total_starters += starters_count

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            results.append({"contact": contact, "_agent6_error": str(e)})

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print(f"\n{'='*70}")
    print("📊 SUMMARY - BUSINESS INTELLIGENCE")
    print(f"{'='*70}\n")

    print(f"Total Contacts Tested: {len(all_contacts)}")
    print(f"Successful Intel Gathering: {success_count}/{len(all_contacts)} ({(success_count/len(all_contacts)*100):.0f}%)")

    # Segmentation results
    print("\n🎯 SEGMENTATION RESULTS:")
    print(f"   High-End Clubs: {high_end_count} ({(high_end_count/len(all_contacts)*100):.0f}%)")
    print(f"   Budget Clubs: {budget_count} ({(budget_count/len(all_contacts)*100):.0f}%)")
    print(f"   Both: {both_count} ({(both_count/len(all_contacts)*100):.0f}%)")
    print(f"   Unknown: {unknown_count} ({(unknown_count/len(all_contacts)*100):.0f}%)")

    # Opportunity scoring results
    print("\n🎯 OPPORTUNITY SCORES (Average):")
    for opp_type, scores in opportunity_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            print(f"   {opp_type}: {avg_score:.1f}/10 (max: {max_score})")

    # Cost analysis
    avg_starters = total_starters / len(all_contacts)
    avg_cost = total_cost / len(all_contacts)

    print("\n💰 COST & PERFORMANCE:")
    print(f"   Avg Starters/Contact: {avg_starters:.1f} (target: 5+)")
    print(f"   Avg Cost/Contact: ${avg_cost:.4f} (target: <$0.05)")
    print(f"   Total Cost: ${total_cost:.4f}")

    # Status checks
    print(f"\n{'='*70}")
    print("✅ SUCCESS CRITERIA")
    print(f"{'='*70}")

    starters_ok = avg_starters >= 5
    cost_ok = avg_cost < 0.05
    success_rate_ok = (success_count / len(all_contacts)) >= 0.8
    segmentation_ok = (unknown_count / len(all_contacts)) < 0.3  # Less than 30% unknown

    print(f"   Starters: {'✅' if starters_ok else '❌'} {avg_starters:.1f} >= 5.0")
    print(f"   Cost: {'✅' if cost_ok else '❌'} ${avg_cost:.4f} < $0.05")
    print(f"   Success Rate: {'✅' if success_rate_ok else '❌'} {(success_count/len(all_contacts)*100):.0f}% >= 80%")
    print(f"   Segmentation: {'✅' if segmentation_ok else '❌'} {((len(all_contacts)-unknown_count)/len(all_contacts)*100):.0f}% classified")

    # Manual validation prompts
    print("\n📋 MANUAL VALIDATION NEEDED:")
    print("   1. Review segmentation: Do high-end clubs look premium? Budget clubs public/value?")
    print("   2. Check opportunity scores: Do top opportunities make sense per segment?")
    print("   3. Validate conversation starters: Are they value-prop specific?")

    # Save results
    output = {
        "test_date": "2025-01-17",
        "test_type": "business_intelligence",
        "total_contacts": len(all_contacts),
        "successful_intel": success_count,
        "success_rate": (success_count / len(all_contacts)) * 100,
        "segmentation": {
            "high_end": high_end_count,
            "budget": budget_count,
            "both": both_count,
            "unknown": unknown_count
        },
        "opportunity_averages": {
            opp_type: (sum(scores) / len(scores) if scores else 0)
            for opp_type, scores in opportunity_scores.items()
        },
        "avg_starters_per_contact": avg_starters,
        "avg_cost_per_contact": avg_cost,
        "total_cost": total_cost,
        "meets_criteria": {
            "starters": starters_ok,
            "cost": cost_ok,
            "success_rate": success_rate_ok,
            "segmentation": segmentation_ok
        },
        "results": results,
    }

    output_file = Path(__file__).parent.parent / "results" / "agent6_business_intel_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Saved to: {output_file}")

    # Final verdict
    all_pass = starters_ok and cost_ok and success_rate_ok and segmentation_ok
    if all_pass:
        print(f"\n{'='*70}")
        print("✅ AGENT 6 BUSINESS INTEL PRODUCTION READY")
        print(f"{'='*70}")
        print("\nNext: Review segmentation accuracy and opportunity relevance")
    else:
        print(f"\n{'='*70}")
        print("⚠️  NEEDS IMPROVEMENT")
        print(f"{'='*70}")
        if not starters_ok:
            print("   ⚠️  Not generating enough conversation starters")
        if not cost_ok:
            print("   ⚠️  Cost exceeds budget")
        if not success_rate_ok:
            print("   ⚠️  Success rate below 80%")
        if not segmentation_ok:
            print("   ⚠️  Too many contacts unclassified (segmentation issue)")


if __name__ == "__main__":
    anyio.run(run_test)
