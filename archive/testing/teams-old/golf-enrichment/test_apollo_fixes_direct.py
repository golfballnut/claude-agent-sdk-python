#!/usr/bin/env python3
"""
Docker Test Script: Apollo Duplicate Contact Fixes (Direct API Testing)

Tests Apollo API tool function DIRECTLY without Claude SDK Client.
This allows testing in Docker without needing Claude Code CLI installed.

Exit codes:
  0 = Success (80%+ test cases passed)
  1 = Failure (< 80% success rate)
  2 = Error (couldn't run tests)
"""

import anyio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import the agent internal function (testable without SDK)
from agents.agent2_apollo_discovery import (
    find_contacts_apollo_internal,
    KNOWN_DUPLICATE_PERSON_IDS
)


async def load_test_cases() -> List[Dict[str, Any]]:
    """Load test cases from the fixture file"""
    fixture_path = Path("testing/data/apollo_duplicate_contacts.json")

    if not fixture_path.exists():
        print(f"❌ Test fixture not found: {fixture_path}")
        sys.exit(2)

    with open(fixture_path, 'r') as f:
        data = json.load(f)

    return data.get('test_cases', [])


def validate_contacts(
    contacts: List[Dict[str, Any]],
    test_case: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate that contacts meet the success criteria:
    1. No known duplicate person IDs
    2. Email domains match course domain
    3. At least 1 contact found (or Hunter fallback succeeded)
    """
    course_domain = test_case['domain']
    expected_exclude = test_case.get('expected_contacts_exclude', [])

    validation_results = {
        "has_contacts": len(contacts) > 0,
        "no_duplicate_ids": True,
        "email_domains_match": True,
        "no_excluded_emails": True,
        "duplicate_ids_found": [],
        "domain_mismatches": [],
        "excluded_emails_found": []
    }

    for contact in contacts:
        # Check for duplicate person IDs
        person_id = contact.get('person_id')
        if person_id in KNOWN_DUPLICATE_PERSON_IDS:
            validation_results["no_duplicate_ids"] = False
            validation_results["duplicate_ids_found"].append({
                "name": contact.get('name'),
                "person_id": person_id,
                "email": contact.get('email')
            })

        # Check email domain matches course domain
        email = contact.get('email', '')
        if email and '@' in email:
            email_domain = email.split('@')[1].lower()
            course_domain_base = course_domain.replace('www.', '').lower()

            # Check if domains match (exact, subdomain, or parent domain)
            email_parts = email_domain.split('.')
            course_parts = course_domain_base.split('.')

            # Check if last 2 parts match (company.com)
            domains_match = (
                email_domain == course_domain_base or
                course_domain_base in email_domain or
                email_domain in course_domain_base or
                (len(email_parts) >= 2 and len(course_parts) >= 2 and
                 email_parts[-2:] == course_parts[-2:])
            )

            if not domains_match:
                validation_results["email_domains_match"] = False
                validation_results["domain_mismatches"].append({
                    "name": contact.get('name'),
                    "email": email,
                    "email_domain": email_domain,
                    "expected_domain": course_domain_base
                })

        # Check for excluded emails (known bad contacts)
        if email in expected_exclude:
            validation_results["no_excluded_emails"] = False
            validation_results["excluded_emails_found"].append({
                "name": contact.get('name'),
                "email": email
            })

    return validation_results


async def run_tests():
    """Run Apollo fix tests on all test cases"""

    print(f"\n{'='*70}")
    print("🧪 DOCKER TEST: Apollo Duplicate Contact Fixes (Direct API)")
    print(f"{'='*70}\n")
    print(f"Test run: {datetime.now().isoformat()}")
    print(f"Known duplicate IDs: {len(KNOWN_DUPLICATE_PERSON_IDS)}")
    print()

    # Load test cases
    test_cases = await load_test_cases()
    print(f"Loaded {len(test_cases)} test cases\n")

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_cases)}: {test_case['course_name']}")
        print(f"{'='*70}")
        print(f"Domain: {test_case['domain']}")
        print(f"Expected to exclude: {test_case.get('expected_contacts_exclude', [])[:2]}...")
        print()

        try:
            # Call the Apollo internal function DIRECTLY (no SDK wrapper needed)
            result = await find_contacts_apollo_internal(
                course_name=test_case['course_name'],
                domain=test_case['domain'],
                state_code=test_case.get('state', 'NC')
            )

            contacts = result.get('contacts', [])
            credits_used = result.get('credits_used', 0)
            cost = result.get('cost_usd', 0)
            error = result.get('error')

            if error:
                raise Exception(f"Apollo error: {error}")

            print(f"\n📊 Agent Results:")
            print(f"   Contacts found: {len(contacts)}")
            print(f"   Credits used: {credits_used}")
            print(f"   Cost: ${cost:.4f}")

            # Validate contacts
            validation = validate_contacts(contacts, test_case)

            # Determine if test passed
            test_passed = (
                validation["has_contacts"] and
                validation["no_duplicate_ids"] and
                validation["email_domains_match"] and
                validation["no_excluded_emails"]
            )

            test_result = {
                "test_id": test_case['id'],
                "course_name": test_case['course_name'],
                "domain": test_case['domain'],
                "passed": test_passed,
                "contacts_found": len(contacts),
                "credits_used": credits_used,
                "cost": cost,
                "validation": validation,
                "contacts": contacts
            }

            results.append(test_result)

            # Print validation results
            print(f"\n✅ Validation Results:")
            print(f"   Has contacts: {'✅ YES' if validation['has_contacts'] else '❌ NO'}")
            print(f"   No duplicate IDs: {'✅ YES' if validation['no_duplicate_ids'] else '❌ NO'}")
            print(f"   Domains match: {'✅ YES' if validation['email_domains_match'] else '❌ NO'}")
            print(f"   No excluded emails: {'✅ YES' if validation['no_excluded_emails'] else '❌ NO'}")

            if validation["duplicate_ids_found"]:
                print(f"\n   🚨 Duplicate IDs found:")
                for dup in validation["duplicate_ids_found"]:
                    print(f"      - {dup['name']} ({dup['person_id']})")

            if validation["domain_mismatches"]:
                print(f"\n   ⚠️  Domain mismatches:")
                for mismatch in validation["domain_mismatches"]:
                    print(f"      - {mismatch['name']}: {mismatch['email_domain']} ≠ {mismatch['expected_domain']}")

            if validation["excluded_emails_found"]:
                print(f"\n   ❌ Excluded emails found:")
                for excluded in validation["excluded_emails_found"]:
                    print(f"      - {excluded['name']}: {excluded['email']}")

            # Print test status
            status = "✅ PASS" if test_passed else "❌ FAIL"
            print(f"\n{status}: {test_case['course_name']}")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

            test_result = {
                "test_id": test_case['id'],
                "course_name": test_case['course_name'],
                "domain": test_case['domain'],
                "passed": False,
                "error": str(e),
                "contacts_found": 0,
                "credits_used": 0,
                "cost": 0
            }
            results.append(test_result)

    # Calculate summary
    print(f"\n\n{'='*70}")
    print("📊 TEST SUMMARY")
    print(f"{'='*70}\n")

    passed = sum(1 for r in results if r.get('passed'))
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    total_cost = sum(r.get('cost', 0) for r in results)
    total_contacts = sum(r.get('contacts_found', 0) for r in results)
    total_credits = sum(r.get('credits_used', 0) for r in results)

    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {success_rate:.0f}%")
    print(f"Total contacts found: {total_contacts}")
    print(f"Total credits used: {total_credits}")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Avg cost per course: ${total_cost / total:.4f}" if total > 0 else "")
    print()

    # Pass/fail determination
    target_success_rate = 80
    if success_rate >= target_success_rate:
        print(f"✅ SUCCESS: {success_rate:.0f}% >= {target_success_rate}% target")
        print(f"✅ READY TO DEPLOY TO PRODUCTION")
        exit_code = 0
    else:
        print(f"❌ FAILURE: {success_rate:.0f}% < {target_success_rate}% target")
        print(f"❌ NEEDS MORE WORK - DO NOT DEPLOY")
        exit_code = 1

    print()

    # Save detailed results
    output_file = Path("/app/results/apollo_fix_docker_test.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "test_run": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": success_rate,
            "target_success_rate": target_success_rate,
            "ready_to_deploy": success_rate >= target_success_rate
        },
        "summary": {
            "total_contacts_found": total_contacts,
            "total_credits_used": total_credits,
            "total_cost_usd": total_cost,
            "avg_cost_per_course": total_cost / total if total > 0 else 0
        },
        "test_results": results
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"📝 Detailed results saved: {output_file}")
    print()

    return exit_code


async def main():
    """Main entry point"""
    try:
        exit_code = await run_tests()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    anyio.run(main)
