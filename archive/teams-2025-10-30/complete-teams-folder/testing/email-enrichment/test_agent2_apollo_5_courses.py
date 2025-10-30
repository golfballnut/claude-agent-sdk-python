#!/usr/bin/env python3
"""
Test Agent 2-Apollo on 5 Diverse NC Courses

Validates:
- Consistent performance across different courses
- Email coverage stays 50-60%
- Credits 4-8 per course
- Total cost < $0.20/course

Note credits BEFORE and AFTER this test!
"""

import anyio
import sys
from pathlib import Path

# Add agents directory to path
agents_dir = Path(__file__).parent.parent.parent / "agents"
sys.path.insert(0, str(agents_dir))

from agent2_apollo_discovery import discover_contacts


TEST_COURSES = [
    {"name": "Brook Valley Country Club", "domain": "brookvalleycc.com"},
    {"name": "Balsam Mountain Preserve", "domain": "balsammountainpreserve.com"},
    {"name": "Bright's Creek Golf Club", "domain": "brightscreek.com"},
    {"name": "Birkdale Golf Club", "domain": "birkdale.com"},
    {"name": "Black Mountain Golf Course", "domain": "blackmountaingolf.org"}
]


async def main():
    """Test on 5 courses"""

    print("=" * 80)
    print("Agent 2-Apollo: 5-Course Validation Test")
    print("=" * 80)
    print()
    print("⚠️  BEFORE: Note credits at https://app.apollo.io/usage")
    print()

    results = []
    total_contacts = 0
    total_emails = 0
    total_credits = 0
    total_cost = 0

    for i, course in enumerate(TEST_COURSES, 1):
        print(f"\n[{i}/5] {course['name']}")
        print("-" * 80)

        result = await discover_contacts(course['name'], course['domain'])

        contacts = result.get('contacts', [])
        credits = result.get('credits_used', 0)
        cost = result.get('total_cost_usd', 0)
        emails = len([c for c in contacts if c.get('email')])

        print(f"   Contacts: {len(contacts)}")
        print(f"   Emails: {emails}/{len(contacts)}")
        print(f"   Credits: {credits}")
        print(f"   Cost: ${cost:.4f}")

        for contact in contacts:
            print(f"\n   ✅ {contact['name']} ({contact['title']})")
            print(f"      Email: {contact.get('email', 'None')}")
            if contact.get('tenure_years'):
                print(f"      Tenure: {contact['tenure_years']} years")

        results.append(result)
        total_contacts += len(contacts)
        total_emails += emails
        total_credits += credits
        total_cost += cost

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    avg_contacts = total_contacts / len(TEST_COURSES)
    avg_credits = total_credits / len(TEST_COURSES)
    avg_cost = total_cost / len(TEST_COURSES)
    email_coverage = (total_emails / total_contacts * 100) if total_contacts else 0

    print(f"\nCourses tested: {len(TEST_COURSES)}")
    print(f"Total contacts: {total_contacts}")
    print(f"Total emails: {total_emails}")
    print(f"Email coverage: {email_coverage:.1f}%")
    print()
    print(f"Average per course:")
    print(f"   Contacts: {avg_contacts:.1f}")
    print(f"   Credits: {avg_credits:.1f}")
    print(f"   Cost: ${avg_cost:.4f}")
    print()
    print(f"Total credits used: {total_credits}")
    print(f"Total cost: ${total_cost:.2f}")
    print()

    # Projections
    print("=" * 80)
    print("MONTHLY PROJECTIONS (500 courses)")
    print("=" * 80)
    print()
    print(f"Credits per course: {avg_credits:.1f}")
    print(f"Monthly credits: 500 × {avg_credits:.1f} = {500 * avg_credits:.0f}")
    print(f"Your limit: 4,020 credits")
    print(f"Sufficient? {'✅ Yes' if 500 * avg_credits <= 4020 else '❌ No'}")
    print()
    print(f"Cost per course: ${avg_cost:.4f}")
    print(f"Monthly cost: 500 × ${avg_cost:.4f} = ${500 * avg_cost:.2f}")
    print()

    # Validation
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)
    print()

    validations = []

    if email_coverage >= 50:
        validations.append(f"✅ Email coverage {email_coverage:.1f}% meets >50% target")
    else:
        validations.append(f"⚠️  Email coverage {email_coverage:.1f}% below 50% target")

    if avg_cost < 0.20:
        validations.append(f"✅ Cost ${avg_cost:.4f} under $0.20 budget")
    else:
        validations.append(f"❌ Cost ${avg_cost:.4f} exceeds $0.20 budget")

    if 500 * avg_credits <= 4020:
        validations.append(f"✅ Monthly credits {500 * avg_credits:.0f} within 4,020 limit")
    else:
        validations.append(f"❌ Monthly credits {500 * avg_credits:.0f} exceeds limit")

    if total_emails == total_contacts:
        validations.append(f"✅ 100% email coverage on found contacts")
    elif total_emails / total_contacts >= 0.8:
        validations.append(f"✅ {total_emails/total_contacts*100:.0f}% email coverage - excellent")
    else:
        validations.append(f"⚠️  {total_emails/total_contacts*100:.0f}% email coverage - review")

    for v in validations:
        print(f"   {v}")

    print()
    print("⚠️  AFTER: Check https://app.apollo.io/usage for actual credits consumed")
    print()
    print("=" * 80)

    if all("✅" in v for v in validations):
        print("\n✅ READY FOR PRODUCTION!")
        print("\nNext steps:")
        print("1. Update orchestrator to use Agent 2-Apollo")
        print("2. Sync to production/")
        print("3. Add APOLLO_API_KEY to Render")
        print("4. Deploy and monitor")
    else:
        print("\n⚠️  REVIEW NEEDED")
        print("\nAddress validation issues before production deployment")

    print()
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(main)
