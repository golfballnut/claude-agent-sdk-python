#!/usr/bin/env python3
"""
Agent 3 MCP Direct Test

Test using MCP tools directly with exact patterns from working system
Goal: Replicate 80% success rate
"""

import json
import time

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

TEST_CONTACT = {
    "name": "Stacy Foster",
    "title": "General Manager",
    "company": "Richmond Country Club",
    "company_domain": "richmondcountryclubva.com"
}


async def test_mcp_enrichment():
    """Test with MCP tools and exact working system pattern"""
    print("\n" + "="*70)
    print("Testing: MCP Tools Direct (Working System Pattern)")
    print("="*70)
    print(f"Contact: {TEST_CONTACT['name']}")
    print(f"Title: {TEST_CONTACT['title']}")
    print(f"Company: {TEST_CONTACT['company']}")
    print()

    start_time = time.time()

    # Exact system prompt pattern from working system
    system_prompt = f"""You are an elite contact enrichment specialist.

YOUR MISSION: Find email and LinkedIn URL for {TEST_CONTACT['name']}, {TEST_CONTACT['title']} at {TEST_CONTACT['company']}.

MANDATORY 5-STEP EMAIL DISCOVERY (DO NOT SKIP STEPS):

STEP 1: Hunter.io Email Finder
- Use mcp__hunter-io__Email-Finder
- Parameters: full_name="{TEST_CONTACT['name']}", domain="{TEST_CONTACT['company_domain']}"
- IF found → GO TO verification
- IF not found → LOG "Step 1 failed" → GO TO STEP 2

STEP 2: BrightData Web Search
- Use mcp__BrightData__search_engine
- Query: "{TEST_CONTACT['name']} {TEST_CONTACT['company']} {TEST_CONTACT['title']} email"
- Look for email addresses in results
- IF found → GO TO verification
- IF not found → LOG "Step 2 failed" → GO TO STEP 3

STEP 3: Jina Search
- Use mcp__jina__jina_search
- Query: "{TEST_CONTACT['name']} {TEST_CONTACT['company']} email contact"
- Extract email from results
- IF found → GO TO verification
- IF not found → LOG "Step 3 failed" → GO TO STEP 4

STEP 4: General Email
- Try: info@{TEST_CONTACT['company_domain']}
- Mark as: email_method='course_general_email'
- GO TO STEP 5

STEP 5: Manual Research Flag
- Mark as: email_method='needs_manual_research'

EMAIL VERIFICATION (After finding email):
- Use mcp__hunter-io__Email-Verifier
- ONLY accept if confidence ≥ 90%

LINKEDIN DISCOVERY (2-Step):

STEP 1: BrightData LinkedIn Search
- Use mcp__BrightData__search_engine
- Query: "{TEST_CONTACT['name']} {TEST_CONTACT['company']} site:linkedin.com/in/"
- Extract linkedin.com/in/ URLs
- IF found → Return it
- IF not found → GO TO STEP 2

STEP 2: Jina LinkedIn Search
- Use mcp__jina__jina_search
- Query: "{TEST_CONTACT['name']} {TEST_CONTACT['title']} {TEST_CONTACT['company']} LinkedIn"
- Extract linkedin.com/in/ URLs
- IF found → Return it
- IF not found → Return NULL

RETURN FORMAT (JSON):
{{
  "email": "...",
  "email_method": "hunter_io|brightdata_search|jina_search|course_general_email|needs_manual_research",
  "email_confidence": 0-100,
  "linkedin_url": "..." or null,
  "linkedin_method": "brightdata_site_filter|jina_search" or null,
  "steps_attempted": ["Step 1: ...", "Step 2: ..."]
}}

CRITICAL: Use ONLY the specified MCP tools. Do NOT use WebSearch or WebFetch."""

    options = ClaudeAgentOptions(
        allowed_tools=[
            "mcp__hunter-io__Email-Finder",
            "mcp__hunter-io__Email-Verifier",
            "mcp__BrightData__search_engine",
            "mcp__jina__jina_search",
        ],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=10,  # More turns for 5-step sequence
        model="claude-haiku-4-5",
        system_prompt=system_prompt,
    )

    enrichment_data = None
    tools_used = []
    result_message = None

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(
                f"Enrich contact: {TEST_CONTACT['name']}, {TEST_CONTACT['title']} at {TEST_CONTACT['company']}"
            )

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                            print(f"   🔧 Tool: {block.name}")
                        elif isinstance(block, TextBlock):
                            # Try to parse JSON
                            import re
                            json_match = re.search(r'\{.*\}', block.text, re.DOTALL)
                            if json_match:
                                try:
                                    enrichment_data = json.loads(json_match.group(0))
                                except json.JSONDecodeError:
                                    pass

                if isinstance(msg, ResultMessage):
                    result_message = msg

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    elapsed = time.time() - start_time

    # Results
    print(f"\n{'='*70}")
    print("📊 RESULTS")
    print(f"{'='*70}")

    if enrichment_data:
        print(f"\n   Email: {enrichment_data.get('email', 'Not found')}")
        print(f"   Email Method: {enrichment_data.get('email_method', 'N/A')}")
        print(f"   Email Confidence: {enrichment_data.get('email_confidence', 0)}%")
        print(f"   LinkedIn: {enrichment_data.get('linkedin_url', 'Not found')}")
        print(f"   LinkedIn Method: {enrichment_data.get('linkedin_method', 'N/A')}")
        print(f"   Steps Attempted: {len(enrichment_data.get('steps_attempted', []))}")
    else:
        print("   ⚠️  No structured data extracted")

    print(f"\n   Tools Used: {len(tools_used)}")
    for tool in set(tools_used):
        count = tools_used.count(tool)
        print(f"      - {tool}: {count}x")

    print(f"\n   Cost: ${result_message.total_cost_usd:.4f}" if result_message else "   Cost: N/A")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Turns: {result_message.num_turns}" if result_message else "   Turns: N/A")

    # Success evaluation
    print(f"\n{'='*70}")
    print("✅ SUCCESS CRITERIA")
    print(f"{'='*70}")

    email_found = enrichment_data and enrichment_data.get('email') and \
                  enrichment_data.get('email_method') not in ['course_general_email', 'needs_manual_research']
    linkedin_found = enrichment_data and enrichment_data.get('linkedin_url')

    print(f"   Email Found: {'✅' if email_found else '❌'}")
    print(f"   LinkedIn Found: {'✅' if linkedin_found else '❌'}")
    print(f"   Cost Under $0.03: {'✅' if result_message and result_message.total_cost_usd < 0.03 else '❌'}")

    # Tool usage analysis
    hunter_used = any('hunter-io' in tool for tool in tools_used)
    brightdata_used = any('BrightData' in tool for tool in tools_used)
    jina_used = any('jina' in tool for tool in tools_used)

    print(f"\n   Hunter.io Used: {'✅' if hunter_used else '❌ (Tool routing issue!)'}")
    print(f"   BrightData Used: {'✅' if brightdata_used else '❌ (Tool routing issue!)'}")
    print(f"   Jina Used: {'✅' if jina_used else '❌ (Tool routing issue!)'}")

    # Save results
    output = {
        "test_date": "2025-10-16",
        "contact": TEST_CONTACT,
        "enrichment_data": enrichment_data,
        "tools_used": tools_used,
        "cost": result_message.total_cost_usd if result_message else None,
        "time_seconds": round(elapsed, 3),
        "turns": result_message.num_turns if result_message else None,
        "email_found": email_found,
        "linkedin_found": linkedin_found,
    }

    with open("../results/agent3_mcp_direct_test.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n💾 Saved to: ../results/agent3_mcp_direct_test.json")

    return output


async def main():
    print("🧪 Agent 3 MCP Direct Test")
    print("="*70)
    print("Goal: Replicate working system's 80% success rate")
    print("Method: Direct MCP tool usage with exact patterns\n")

    result = await test_mcp_enrichment()

    print(f"\n{'='*70}")
    if result.get('email_found') or result.get('linkedin_found'):
        print("🎉 SUCCESS - Found contact data!")
    else:
        print("⚠️  PARTIAL - Need to debug tool routing")
    print(f"{'='*70}")


if __name__ == "__main__":
    anyio.run(main)
