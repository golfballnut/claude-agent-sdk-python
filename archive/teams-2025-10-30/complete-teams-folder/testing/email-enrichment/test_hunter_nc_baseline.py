#!/usr/bin/env python3
"""
Test 1: Hunter.io NC Baseline Validation

Goal: Validate Agent 3 (Hunter.io) performance on NC contacts before adding new tools

Expected Results:
- Success rate: ~20% (10 out of 50 contacts)
- Confidence: 90-99% for all found emails
- Cost: 50 × $0.0116 = $0.58

This establishes baseline before adding Apollo.io (Test 2).
"""

import anyio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add agents directory to path
agents_dir = Path(__file__).parent.parent.parent / "agents"
sys.path.insert(0, str(agents_dir))

from agent3_contact_enricher import enrich_contact


async def load_test_data():
    """Load NC contacts from test data file"""
    data_file = Path(__file__).parent / "data" / "nc_contacts_no_hunter.json"
    with open(data_file) as f:
        data = json.load(f)
    return data["contacts"]


async def run_hunter_baseline():
    """Run Hunter.io on all NC contacts and track results"""

    print("=" * 80)
    print("Test 1: Hunter.io NC Baseline Validation")
    print("=" * 80)
    print()

    # Load test contacts
    contacts = await load_test_data()
    total = len(contacts)

    print(f"Loaded {total} NC contacts from test data")
    print(f"Expected success rate: ~20% ({total * 0.2:.0f} emails)")
    print(f"Expected cost: ${total * 0.0116:.2f}")
    print()

    # Track results
    results = {
        "test_name": "hunter_nc_baseline",
        "test_date": datetime.now().isoformat(),
        "total_contacts": total,
        "contacts_tested": 0,
        "emails_found": 0,
        "emails_not_found": 0,
        "total_cost": 0.0,
        "confidence_scores": [],
        "contacts": []
    }

    # Test each contact
    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{total}] {contact['name']} - {contact['title']}")
        print(f"   Company: {contact['company']}")
        print(f"   Domain: {contact['domain']}")

        try:
            # Run Agent 3 (Hunter.io)
            result = await enrich_contact(contact)

            # Track results
            results["contacts_tested"] += 1
            cost = result.get("_agent3_cost", 0)
            results["total_cost"] += cost

            email = result.get("email")
            method = result.get("email_method")
            confidence = result.get("email_confidence", 0)
            linkedin = result.get("linkedin_url")

            if email and method == "hunter_io":
                results["emails_found"] += 1
                results["confidence_scores"].append(confidence)
                print(f"   ✅ Email: {email}")
                print(f"   📊 Confidence: {confidence}%")
                if linkedin:
                    print(f"   🔗 LinkedIn: {linkedin}")
                print(f"   💰 Cost: ${cost:.4f}")

                # Save contact result
                results["contacts"].append({
                    "contact_id": contact["contact_id"],
                    "name": contact["name"],
                    "email": email,
                    "confidence": confidence,
                    "linkedin": linkedin,
                    "cost": cost,
                    "found": True
                })

            else:
                results["emails_not_found"] += 1
                print(f"   ❌ Not found (Hunter.io returned null)")
                print(f"   💰 Cost: ${cost:.4f}")

                # Save contact result
                results["contacts"].append({
                    "contact_id": contact["contact_id"],
                    "name": contact["name"],
                    "email": None,
                    "confidence": 0,
                    "linkedin": None,
                    "cost": cost,
                    "found": False
                })

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results["contacts"].append({
                "contact_id": contact["contact_id"],
                "name": contact["name"],
                "error": str(e),
                "found": False
            })

    # Calculate summary statistics
    success_rate = (results["emails_found"] / results["contacts_tested"]) * 100 if results["contacts_tested"] > 0 else 0
    avg_confidence = sum(results["confidence_scores"]) / len(results["confidence_scores"]) if results["confidence_scores"] else 0
    avg_cost = results["total_cost"] / results["contacts_tested"] if results["contacts_tested"] > 0 else 0

    results["summary"] = {
        "success_rate": round(success_rate, 1),
        "avg_confidence": round(avg_confidence, 1),
        "avg_cost_per_contact": round(avg_cost, 4),
        "total_cost": round(results["total_cost"], 2),
        "linkedin_found": sum(1 for c in results["contacts"] if c.get("linkedin")),
    }

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n📊 Results:")
    print(f"   Total contacts tested: {results['contacts_tested']}")
    print(f"   Emails found: {results['emails_found']}")
    print(f"   Emails not found: {results['emails_not_found']}")
    print(f"   Success rate: {success_rate:.1f}%")
    print()
    print(f"📈 Quality:")
    print(f"   Average confidence: {avg_confidence:.1f}%")
    print(f"   Confidence range: {min(results['confidence_scores']) if results['confidence_scores'] else 0}% - {max(results['confidence_scores']) if results['confidence_scores'] else 0}%")
    print(f"   All above 90%: {'✅ Yes' if all(c >= 90 for c in results['confidence_scores']) else '❌ No'}")
    print()
    print(f"💰 Cost:")
    print(f"   Total cost: ${results['total_cost']:.2f}")
    print(f"   Average per contact: ${avg_cost:.4f}")
    print(f"   Within budget (<$0.02): {'✅ Yes' if avg_cost < 0.02 else '❌ No'}")
    print()
    print(f"🎁 Bonus:")
    print(f"   LinkedIn URLs found: {results['summary']['linkedin_found']}")

    # Compare to expected
    print()
    print("=" * 80)
    print("COMPARISON TO EXPECTED")
    print("=" * 80)
    print(f"   Expected success rate: 20% (10 emails)")
    print(f"   Actual success rate: {success_rate:.1f}% ({results['emails_found']} emails)")
    print(f"   Difference: {success_rate - 20:.1f} percentage points")
    print()
    print(f"   Expected cost: ${total * 0.0116:.2f}")
    print(f"   Actual cost: ${results['total_cost']:.2f}")
    print(f"   Difference: ${results['total_cost'] - (total * 0.0116):.2f}")

    # Save results
    results_file = Path(__file__).parent / "results" / "hunter_nc_baseline_results.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print(f"📁 Results saved to: {results_file}")

    # Validation
    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)

    validations = []

    # Check success rate is reasonable (10-30% range)
    if 10 <= success_rate <= 30:
        validations.append("✅ Success rate within expected range (10-30%)")
    else:
        validations.append(f"⚠️  Success rate {success_rate:.1f}% outside expected range (10-30%)")

    # Check all found emails have 90%+ confidence
    if all(c >= 90 for c in results['confidence_scores']) if results['confidence_scores'] else False:
        validations.append("✅ All emails meet 90%+ confidence threshold")
    else:
        validations.append("❌ Some emails below 90% confidence")

    # Check cost per contact is reasonable
    if avg_cost < 0.02:
        validations.append(f"✅ Average cost ${avg_cost:.4f} under $0.02 budget")
    else:
        validations.append(f"❌ Average cost ${avg_cost:.4f} exceeds $0.02 budget")

    for v in validations:
        print(f"   {v}")

    # Next steps
    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    if success_rate < 30:
        print("✅ NC success rate is low (as expected)")
        print("✅ Agent 3 (Hunter.io) working correctly")
        print("✅ Ready for Test 2: Apollo.io evaluation")
        print()
        print("Next:")
        print("1. Sign up for Apollo.io Professional trial")
        print("2. Run Test 2: Apollo.io on same NC contacts")
        print("3. Compare Hunter.io vs Apollo.io coverage")
        print("4. Decide on waterfall strategy")
    else:
        print("⚠️  NC success rate higher than expected!")
        print("⚠️  May indicate NC coverage has improved")
        print("⚠️  Review production data before proceeding")

    print()
    print("=" * 80)
    print("✅ Test 1 Complete!")
    print("=" * 80)
    print()


async def main():
    """Run the baseline test"""
    await run_hunter_baseline()


if __name__ == "__main__":
    anyio.run(main)
