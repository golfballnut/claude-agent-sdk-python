#!/usr/bin/env python3
"""
Agent 3 Approach Testing

Test different search strategies to find email + LinkedIn
Goal: < $0.01 per contact, high accuracy
"""

import json
import time
from typing import Any

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

TEST_CONTACT = {
    "name": "Stacy Foster",
    "title": "General Manager",
    "company": "Richmond Country Club",
    "company_domain": "richmondcountryclubva.com"
}


# ============================================================================
# APPROACH A: WebSearch (Baseline)
# ============================================================================

async def test_websearch_approach() -> dict[str, Any]:
    """Test using built-in WebSearch tool"""
    print("\n" + "="*70)
    print("APPROACH A: WebSearch (Baseline)")
    print("="*70)

    start_time = time.time()

    options = ClaudeAgentOptions(
        allowed_tools=["WebSearch"],
        disallowed_tools=["Task", "TodoWrite", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=4,
        model="claude-haiku-4-5",
        system_prompt=(
            f"Use WebSearch to find:\n"
            f"1. Email address for {TEST_CONTACT['name']} at {TEST_CONTACT['company']}\n"
            f"2. LinkedIn URL for {TEST_CONTACT['name']} at {TEST_CONTACT['company']}\n"
            f"Return JSON: {{'email': '...', 'linkedin_url': '...'}}"
        ),
    )

    email = None
    linkedin_url = None
    result_message = None
    tools_used = []

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find email and LinkedIn for {TEST_CONTACT['name']}, "
            f"{TEST_CONTACT['title']} at {TEST_CONTACT['company']}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        tools_used.append(block.name)
                    elif isinstance(block, TextBlock):
                        # Try to parse JSON
                        import re
                        json_match = re.search(r'\{.*\}', block.text, re.DOTALL)
                        if json_match:
                            try:
                                data = json.loads(json_match.group(0))
                                email = data.get('email')
                                linkedin_url = data.get('linkedin_url')
                            except json.JSONDecodeError:
                                pass

                        # Fallback: extract with regex
                        if not email:
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            emails = re.findall(email_pattern, block.text)
                            if emails:
                                email = emails[0]

                        if not linkedin_url:
                            linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
                            urls = re.findall(linkedin_pattern, block.text)
                            if urls:
                                linkedin_url = urls[0]

            if isinstance(msg, ResultMessage):
                result_message = msg

    elapsed = time.time() - start_time

    result = {
        "approach": "websearch",
        "email": email,
        "linkedin_url": linkedin_url,
        "cost": result_message.total_cost_usd if result_message else None,
        "time_seconds": round(elapsed, 3),
        "turns": result_message.num_turns if result_message else None,
        "tools_used": tools_used,
        "success": email is not None or linkedin_url is not None,
    }

    print(f"\n   Email: {'✅ ' + email if email else '❌ Not found'}")
    print(f"   LinkedIn: {'✅ ' + linkedin_url if linkedin_url else '❌ Not found'}")
    print(f"   Cost: ${result['cost']:.4f}" if result['cost'] else "   Cost: N/A")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Turns: {result['turns']}")
    print(f"   Tools: {tools_used}")

    return result


# ============================================================================
# APPROACH B: Custom Search Tool
# ============================================================================

@tool("search", "Search web for contact info", {"query": str})
async def custom_search(args: dict[str, Any]) -> dict[str, Any]:
    """Custom search tool - uses Jina search (cheaper than WebSearch)"""
    import httpx

    query = args['query']

    # Use Jina Search API (free tier)
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Search via Google (Jina can scrape it)
        google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        r = await client.get(f"https://r.jina.ai/{google_url}")
        content = r.text

        # Return first 1000 chars (enough for contact info)
        print(f"   ✓ Searched: {query[:50]}...")
        return {"content": [{"type": "text", "text": content[:1000]}]}


async def test_custom_tool_approach() -> dict[str, Any]:
    """Test using custom search tool"""
    print("\n" + "="*70)
    print("APPROACH B: Custom Search Tool (Jina)")
    print("="*70)

    start_time = time.time()

    server = create_sdk_mcp_server("search", tools=[custom_search])

    options = ClaudeAgentOptions(
        mcp_servers={"search": server},
        allowed_tools=["mcp__search__search"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=4,
        model="claude-haiku-4-5",
        system_prompt=(
            f"Use the search tool to find:\n"
            f"1. Email for {TEST_CONTACT['name']} at {TEST_CONTACT['company']}\n"
            f"2. LinkedIn URL for {TEST_CONTACT['name']}\n"
            f"Return JSON: {{'email': '...', 'linkedin_url': '...'}}"
        ),
    )

    email = None
    linkedin_url = None
    result_message = None
    tools_used = []

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find email and LinkedIn for {TEST_CONTACT['name']}, "
            f"{TEST_CONTACT['title']} at {TEST_CONTACT['company']}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        tools_used.append(block.name)
                    elif isinstance(block, TextBlock):
                        # Parse JSON or extract
                        import re
                        json_match = re.search(r'\{.*\}', block.text, re.DOTALL)
                        if json_match:
                            try:
                                data = json.loads(json_match.group(0))
                                email = data.get('email')
                                linkedin_url = data.get('linkedin_url')
                            except json.JSONDecodeError:
                                pass

                        if not email:
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            emails = re.findall(email_pattern, block.text)
                            if emails:
                                email = emails[0]

                        if not linkedin_url:
                            linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
                            urls = re.findall(linkedin_pattern, block.text)
                            if urls:
                                linkedin_url = urls[0]

            if isinstance(msg, ResultMessage):
                result_message = msg

    elapsed = time.time() - start_time

    result = {
        "approach": "custom_tool",
        "email": email,
        "linkedin_url": linkedin_url,
        "cost": result_message.total_cost_usd if result_message else None,
        "time_seconds": round(elapsed, 3),
        "turns": result_message.num_turns if result_message else None,
        "tools_used": tools_used,
        "success": email is not None or linkedin_url is not None,
    }

    print(f"\n   Email: {'✅ ' + email if email else '❌ Not found'}")
    print(f"   LinkedIn: {'✅ ' + linkedin_url if linkedin_url else '❌ Not found'}")
    print(f"   Cost: ${result['cost']:.4f}" if result['cost'] else "   Cost: N/A")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Turns: {result['turns']}")
    print(f"   Tools: {tools_used}")

    return result


# ============================================================================
# MAIN
# ============================================================================

async def main():
    print("🧪 Agent 3 Approach Testing")
    print("="*70)
    print(f"Contact: {TEST_CONTACT['name']}")
    print(f"Company: {TEST_CONTACT['company']}")
    print("Goal: Find email + LinkedIn, cost < $0.01\n")

    results = {}

    # Test Approach A
    results["websearch"] = await test_websearch_approach()

    # Test Approach B
    results["custom_tool"] = await test_custom_tool_approach()

    # ========================================================================
    # ANALYSIS
    # ========================================================================

    print(f"\n{'='*70}")
    print("📊 COMPARISON")
    print(f"{'='*70}\n")

    for name, result in results.items():
        print(f"{name.upper()}:")
        print(f"   Success: {'✅' if result['success'] else '❌'}")
        print(f"   Cost: ${result['cost']:.4f}" if result['cost'] else "   Cost: N/A")
        print(f"   Time: {result['time_seconds']}s")
        print(f"   Email: {'✅' if result['email'] else '❌'}")
        print(f"   LinkedIn: {'✅' if result['linkedin_url'] else '❌'}")
        print()

    # Winner
    valid_results = [r for r in results.values() if r['success'] and r['cost']]
    if valid_results:
        winner = min(valid_results, key=lambda x: x['cost'])

        print(f"{'='*70}")
        print("🏆 WINNER")
        print(f"{'='*70}\n")
        print(f"Approach: {winner['approach'].upper()}")
        print(f"Cost: ${winner['cost']:.4f}")
        print(f"Budget: {'✅ Under' if winner['cost'] < 0.01 else '⚠️ Over'} ($0.01 target)")

        if winner['email'] and winner['linkedin_url']:
            print("Data: ✅ Complete (email + LinkedIn)")
        elif winner['email'] or winner['linkedin_url']:
            print("Data: ⚠️ Partial")
        else:
            print("Data: ❌ None found")
    else:
        print("❌ No successful approach")

    # Save
    output = {
        "test_date": "2025-10-16",
        "contact": TEST_CONTACT,
        "results": results,
        "winner": winner['approach'] if valid_results else None,
    }

    with open("../results/agent3_approach_test.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n💾 Saved to: ../results/agent3_approach_test.json")


if __name__ == "__main__":
    anyio.run(main)
