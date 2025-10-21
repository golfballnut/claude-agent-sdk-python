#!/usr/bin/env python3
"""
Test Agent 4 Tenure Extraction with TEST Orchestrator

⚠️  Uses test_orchestrator.py (NOT production orchestrator.py!)

Purpose:
- Validate Agent 4 extracts tenure from Firecrawl search descriptions
- Confirm Agent 6.5 removal doesn't break workflow
- Establish baseline before Docker testing
"""

import anyio
from test_orchestrator import enrich_course

async def test():
    print("="*70)
    print("🧪 TESTING: Agent 4 Tenure Extraction (No Agent 6.5!)")
    print("="*70)
    print("Course: Brambleton Golf Course (ID 108)")
    print("Expected: Agent 4 finds LinkedIn + extracts 6.8 years tenure")
    print("="*70)
    print()

    result = await enrich_course(
        'Brambleton Golf Course',
        'VA',
        None,  # Don't pass course_id for test tables (they use UUID, not INT)
        use_test_tables=True
    )

    print(f'\n\n{"="*70}')
    print("📊 TEST ORCHESTRATOR RESULT:")
    print(f'{"="*70}')
    print(f'  Success: {result["success"]}')
    print(f'  Total Cost: ${result["summary"]["total_cost_usd"]:.4f}')
    print(f'  Contacts: {result["summary"]["contacts_enriched"]}')

    print(f'\n💰 Agent Costs:')
    for agent, cost in sorted(result["summary"]["agent_costs"].items()):
        print(f'  {agent}: ${cost:.4f}')

    # Check if tenure was extracted
    contacts = result.get("agent_results", {}).get("enriched_contacts", [])
    if contacts:
        print(f'\n👥 Contact Data Sample:')
        for i, contact in enumerate(contacts[:2], 1):
            print(f'\n  Contact {i}: {contact.get("name", "Unknown")}')
            print(f'    LinkedIn: {contact.get("linkedin_url", "Not found")}')
            print(f'    Tenure: {contact.get("tenure_years", "Not found")} years')
            print(f'    Start Date: {contact.get("start_date", "N/A")}')

    print(f'\n{"="*70}')
    if result["success"]:
        print("✅ TEST PASSED - Ready for Docker testing!")
    else:
        print("❌ TEST FAILED - Check errors above")
    print(f'{"="*70}')

if __name__ == "__main__":
    anyio.run(test)
