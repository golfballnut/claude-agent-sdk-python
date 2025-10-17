#!/usr/bin/env python3
"""
Agent 1 - Version B: URL Finder with Brightdata MCP

Tests: External Brightdata MCP server with PRO_MODE (60+ tools)

Goal: Find correct numeric courselisting URL from VSGA member directory
"""

import anyio
import os
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    SystemMessage,
)


async def test_agent(course_name: str, expected_url: str = None):
    """Test Agent 1 with Brightdata tools"""
    print(f"\n{'='*70}")
    print(f"🧪 TEST: {course_name}")
    print(f"{'='*70}")

    # Check API token
    api_token = os.environ.get("BRIGHTDATA_API_TOKEN")
    if not api_token:
        print("❌ BRIGHTDATA_API_TOKEN not set")
        return None

    # Configure Brightdata MCP server (matching Claude Desktop config)
    options = ClaudeAgentOptions(
        agents={
            "url_finder": AgentDefinition(
                description="Finds golf course URLs from VSGA directory using Brightdata tools",
                prompt=(
                    "You are a URL finder specialist using Brightdata's powerful scraping tools.\n\n"
                    "GOAL: Find the EXACT courselisting URL for a golf course from VSGA.\n\n"
                    "PROCESS:\n"
                    "1. Use Brightdata tools to scrape https://vsga.org/member-clubs\n"
                    "2. Search for the exact course name in the scraped content\n"
                    "3. Extract the href link next to that course name\n"
                    "4. The URL format is: https://vsga.org/courselisting/[NUMBER]\n\n"
                    "CRITICAL REQUIREMENTS:\n"
                    "- Find the NUMERIC ID URL (e.g., /courselisting/11945)\n"
                    "- Do NOT return slug URLs (e.g., /courselisting/course-name)\n"
                    "- Use Brightdata's scraping capabilities to get accurate data\n"
                    "- Return ONLY the complete URL with ?hsLang=en parameter\n\n"
                    "OUTPUT FORMAT:\n"
                    "URL: https://vsga.org/courselisting/[ID]?hsLang=en\n\n"
                    "You have access to 60+ Brightdata PRO_MODE tools. Use them wisely."
                ),
                tools=None,  # Inherits all tools (all Brightdata tools available)
                model="sonnet"
            )
        },
        mcp_servers={
            "brightdata": {
                "command": "npx",
                "args": ["@brightdata/mcp"],
                "env": {
                    "API_TOKEN": api_token,
                    "PRO_MODE": "1"
                }
            }
        },
        allowed_tools=["mcp__brightdata__*"],
        permission_mode="acceptEdits"
    )

    # The task
    prompt = f"""
    Find the courselisting URL for: "{course_name}"

    Use Brightdata tools to scrape https://vsga.org/member-clubs
    Find the EXACT numeric ID URL for this course.

    Return ONLY the URL in format:
    URL: https://vsga.org/courselisting/[ID]?hsLang=en
    """

    # Track results
    found_url = None
    tools_used = []

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        tools_used.append(block.name)
                    elif isinstance(block, TextBlock):
                        print(f"\n{block.text}")

                        # Extract URL
                        import re
                        urls = re.findall(r'https://vsga\.org/courselisting/\d+(?:\?hsLang=en)?', block.text)
                        if urls:
                            found_url = urls[0]

            elif isinstance(message, SystemMessage):
                if message.subtype == "init":
                    servers = message.data.get('mcp_servers', [])
                    for s in servers:
                        icon = "✅" if s['status'] == 'connected' else "❌"
                        print(f"{icon} {s['name']}: {s['status']}")

            elif isinstance(message, ResultMessage):
                duration = message.duration_ms / 1000
                cost = message.total_cost_usd or 0

                print(f"\n{'='*70}")
                print(f"📊 Results:")
                print(f"   Found URL: {found_url or 'NOT FOUND'}")
                if expected_url:
                    match = "✅ CORRECT" if found_url == expected_url else "❌ WRONG"
                    print(f"   Expected:  {expected_url}")
                    print(f"   Match: {match}")
                print(f"   Duration: {duration:.2f}s")
                print(f"   Cost: ${cost:.4f}")
                print(f"   Turns: {message.num_turns}")
                print(f"   Tools: {', '.join(set(tools_used))}")

                return {
                    "found_url": found_url,
                    "expected_url": expected_url,
                    "correct": found_url == expected_url if expected_url else None,
                    "duration": duration,
                    "cost": cost,
                    "turns": message.num_turns,
                    "tools": tools_used
                }


async def main():
    print("=" * 70)
    print("🧪 AGENT 1 BENCHMARK - VERSION B: Brightdata MCP (PAID)")
    print("=" * 70)

    results = []

    # Test 1
    result1 = await test_agent(
        "Raspberry Falls Golf & Hunt Club",
        "https://vsga.org/courselisting/11945?hsLang=en"
    )
    if result1:
        results.append(("Test 1", result1))

    # Test 2
    result2 = await test_agent(
        "Bristow Manor Golf Club",
        None
    )
    if result2:
        results.append(("Test 2", result2))

    # Summary
    if results:
        print(f"\n\n{'='*70}")
        print("📊 SUMMARY - VERSION B (Brightdata)")
        print(f"{'='*70}")

        total_cost = sum(r[1]['cost'] for r in results)
        avg_duration = sum(r[1]['duration'] for r in results) / len(results)
        correct_count = sum(1 for r in results if r[1].get('correct') == True)
        testable_count = sum(1 for r in results if r[1].get('correct') is not None)

        print(f"\nTotal Cost: ${total_cost:.4f}")
        print(f"Avg Duration: {avg_duration:.2f}s")
        if testable_count > 0:
            accuracy = (correct_count / testable_count) * 100
            print(f"Accuracy: {accuracy:.0f}% ({correct_count}/{testable_count})")

        print(f"\nResults:")
        for name, result in results:
            print(f"  {name}: {result['found_url']}")


if __name__ == "__main__":
    anyio.run(main)
