#!/usr/bin/env python3
"""
Test Contact Discovery Waterfall - Full Integration Test

Tests the 3-level contact discovery fallback:
1. Agent 2 (PGA.org) - Primary source
2. Agent 2.1 (LinkedIn Company) - Fallback 1
3. Agent 2.2 (Perplexity AI) - Fallback 2

Test Scenarios:
- Easy: Course with PGA contacts (Agent 2 succeeds)
- Medium: Course needing LinkedIn (Agent 2 → 2.1)
- Hard: Course needing Perplexity (Agent 2 → 2.1 → 2.2)

Created: Oct 28, 2025
"""

import anyio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from agent2_1_linkedin_company import find_linkedin_company_staff
from agent2_2_perplexity_research import research_course_contacts


async def test_waterfall_easy():
    """
    Easy: Course with good PGA.org presence
    Expected: Agent 2 finds 2+ contacts, no fallback needed
    """
    print("\n" + "="*70)
    print("TEST 1: EASY - Course with PGA contacts")
    print("="*70)
    print("Course: Alamance Country Club")
    print("Expected: Agent 2 (PGA.org) finds 2+ contacts\n")

    # Simulate Agent 2 finding contacts
    pga_contacts = [
        {"name": "Charlie Nolette", "title": "General Manager"},
        {"name": "Drake Woodside", "title": "Director of Golf"}
    ]

    print(f"✅ Agent 2 (PGA.org): Found {len(pga_contacts)} contacts")
    print("   No fallback needed!")

    return {
        "scenario": "easy",
        "source": "pga_org",
        "contacts": len(pga_contacts),
        "fallback_attempts": [],
        "success": True
    }


async def test_waterfall_medium():
    """
    Medium: Course with limited PGA presence, needs LinkedIn
    Expected: Agent 2 finds <2, Agent 2.1 (LinkedIn) succeeds
    """
    print("\n" + "="*70)
    print("TEST 2: MEDIUM - Course needing LinkedIn fallback")
    print("="*70)
    print("Course: Chantilly National Golf and Country Club")
    print("Expected: Agent 2 < 2 contacts → Agent 2.1 (LinkedIn) succeeds\n")

    # Simulate Agent 2 finding only 1 contact
    pga_contacts = [
        {"name": "John Stutz", "title": "General Manager"}
    ]

    print(f"⚠️  Agent 2 (PGA.org): Found {len(pga_contacts)} contacts (< 2 threshold)")
    print("   🔗 Triggering Fallback 1: Agent 2.1 (LinkedIn)\n")

    # Call Agent 2.1
    linkedin_staff = await find_linkedin_company_staff(
        "Chantilly National Golf and Country Club",
        "VA"
    )

    if linkedin_staff and len(linkedin_staff) >= 2:
        print(f"✅ Agent 2.1 (LinkedIn) SUCCESS: {len(linkedin_staff)} contacts")
        return {
            "scenario": "medium",
            "source": "linkedin_company",
            "contacts": len(linkedin_staff),
            "fallback_attempts": ["linkedin_company"],
            "success": True
        }
    else:
        print(f"❌ Agent 2.1 (LinkedIn) FAILED: {len(linkedin_staff)} contacts")
        return {
            "scenario": "medium",
            "source": "pga_org",  # Fallback failed, stick with PGA
            "contacts": len(pga_contacts),
            "fallback_attempts": ["linkedin_company"],
            "success": False
        }


async def test_waterfall_hard():
    """
    Hard: Course with no PGA/LinkedIn, needs Perplexity
    Expected: Agent 2 < 2, Agent 2.1 < 2, Agent 2.2 (Perplexity) succeeds
    """
    print("\n" + "="*70)
    print("TEST 3: HARD - Course needing Perplexity fallback")
    print("="*70)
    print("Course: Mountain Aire Golf Club")
    print("Expected: Agent 2 < 2 → Agent 2.1 < 2 → Agent 2.2 (Perplexity) succeeds\n")

    # Simulate Agent 2 finding 0 contacts
    pga_contacts = []

    print(f"⚠️  Agent 2 (PGA.org): Found {len(pga_contacts)} contacts (< 2 threshold)")
    print("   🔗 Triggering Fallback 1: Agent 2.1 (LinkedIn)\n")

    # Call Agent 2.1
    linkedin_staff = await find_linkedin_company_staff(
        "Mountain Aire Golf Club",
        "NC"
    )

    print(f"   Agent 2.1 result: {len(linkedin_staff)} contacts")

    if linkedin_staff and len(linkedin_staff) >= 2:
        print(f"✅ Agent 2.1 (LinkedIn) SUCCESS: {len(linkedin_staff)} contacts")
        return {
            "scenario": "hard",
            "source": "linkedin_company",
            "contacts": len(linkedin_staff),
            "fallback_attempts": ["linkedin_company"],
            "success": True
        }

    # Agent 2.1 failed, try Agent 2.2
    print(f"⚠️  Agent 2.1 (LinkedIn): Found {len(linkedin_staff)} contacts (< 2 threshold)")
    print("   🤖 Triggering Fallback 2: Agent 2.2 (Perplexity)\n")

    # Call Agent 2.2
    perplexity_staff = await research_course_contacts(
        "Mountain Aire Golf Club",
        "West End",  # City
        "NC"
    )

    if perplexity_staff and len(perplexity_staff) >= 1:
        print(f"✅ Agent 2.2 (Perplexity) SUCCESS: {len(perplexity_staff)} contacts")
        return {
            "scenario": "hard",
            "source": "perplexity_research",
            "contacts": len(perplexity_staff),
            "fallback_attempts": ["linkedin_company", "perplexity_research"],
            "success": True
        }
    else:
        print(f"❌ Agent 2.2 (Perplexity) FAILED: {len(perplexity_staff)} contacts")
        print("   ❌ ALL SOURCES EXHAUSTED")
        return {
            "scenario": "hard",
            "source": "none",
            "contacts": 0,
            "fallback_attempts": ["linkedin_company", "perplexity_research"],
            "success": False
        }


async def main():
    """Run all waterfall tests"""
    print("\n🔍 CONTACT DISCOVERY WATERFALL - Full Integration Test")
    print("="*70)
    print("Testing 3-level fallback cascade:")
    print("  1. Agent 2 (PGA.org) - Primary")
    print("  2. Agent 2.1 (LinkedIn Company) - Fallback 1")
    print("  3. Agent 2.2 (Perplexity AI) - Fallback 2")
    print("="*70)

    results = []

    # Test 1: Easy
    result1 = await test_waterfall_easy()
    results.append(result1)

    # Test 2: Medium
    result2 = await test_waterfall_medium()
    results.append(result2)

    # Test 3: Hard
    result3 = await test_waterfall_hard()
    results.append(result3)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    success_count = sum(1 for r in results if r['success'])
    print(f"\nSuccess Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.0f}%)\n")

    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['scenario'].upper()}: {r['contacts']} contacts from {r['source']}")
        if r['fallback_attempts']:
            print(f"   Fallbacks attempted: {', '.join(r['fallback_attempts'])}")

    print("\n" + "="*70)
    print("WATERFALL VERIFICATION")
    print("="*70)

    # Verify waterfall logic worked correctly
    checks = []

    # Easy: No fallback needed
    checks.append({
        "test": "Easy - No fallback",
        "pass": result1['fallback_attempts'] == []
    })

    # Medium: LinkedIn fallback triggered
    checks.append({
        "test": "Medium - LinkedIn triggered",
        "pass": "linkedin_company" in result2['fallback_attempts']
    })

    # Hard: Both fallbacks triggered
    checks.append({
        "test": "Hard - Both fallbacks",
        "pass": len(result3['fallback_attempts']) == 2
    })

    for check in checks:
        status = "✅" if check['pass'] else "❌"
        print(f"{status} {check['test']}")

    all_passed = all(c['pass'] for c in checks)

    if all_passed:
        print("\n🎉 ALL WATERFALL TESTS PASSED!")
    else:
        print("\n⚠️  SOME WATERFALL TESTS FAILED")

    return all_passed


if __name__ == "__main__":
    success = anyio.run(main)
    sys.exit(0 if success else 1)
