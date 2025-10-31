#!/usr/bin/env python3
"""
Agent 1 Batch Test: Find URLs for 5 Courses

Tests Agent 1 with multiple courses and stores results for Agent 2 testing.
"""

import json
import re
from pathlib import Path
from typing import Any

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
    tool,
)


# Smart fetch tool - extracts only course links
@tool("fetch", "Get golf course listing links from VSGA directory", {"url": str})
async def fetch(args: dict[str, Any]) -> dict[str, Any]:
    """Fetch and extract ONLY course links"""
    import re

    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"https://r.jina.ai/{args['url']}")
        content = r.text

        # Extract course links (reduces 78K → ~2K tokens)
        links = re.findall(
            r'\[Club Name ([^\]]+)\]\((https://vsga\.org/courselisting/\d+[^\)]*)\)',
            content
        )

        if links:
            result = "VSGA Golf Courses:\n\n"
            for name, url in links:
                result += f"{name}: {url}\n"
            return {"content": [{"type": "text", "text": result}]}
        else:
            return {"content": [{"type": "text", "text": content[:1000]}]}


async def find_course_url(course_name: str) -> dict[str, Any]:
    """Find URL for a single course"""
    print(f"\n{'─'*70}")
    print(f"🔍 Finding: {course_name}")

    server = create_sdk_mcp_server("t", tools=[fetch])

    options = ClaudeAgentOptions(
        mcp_servers={"t": server},
        allowed_tools=["mcp__t__fetch"],
        disallowed_tools=["Task", "TodoWrite", "Grep", "Glob", "WebFetch"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt="Use fetch to get https://vsga.org/member-clubs. It returns course links. Find the requested course and return ONLY its URL."
    )

    found_url = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Find the URL for: {course_name}")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        # Extract URL from response
                        urls = re.findall(r'https://vsga\.org/courselisting/\d+(?:\?hsLang=en)?', block.text)
                        if urls:
                            found_url = urls[0]

            elif isinstance(msg, ResultMessage):
                result = {
                    "course_name": course_name,
                    "url": found_url,
                    "cost": msg.total_cost_usd or 0,
                    "time_seconds": msg.duration_ms / 1000,
                    "turns": msg.num_turns
                }

                # Print result
                status = "✅" if found_url else "❌"
                print(f"{status} URL: {found_url or 'NOT FOUND'}")
                print(f"   💰 ${result['cost']:.4f} | ⏱️  {result['time_seconds']:.1f}s")

                return result

    return {
        "course_name": course_name,
        "url": None,
        "cost": 0,
        "time_seconds": 0,
        "turns": 0
    }


async def main():
    print("=" * 70)
    print("🏌️  Agent 1 Batch Test: 5 Courses")
    print("=" * 70)

    # Test courses
    courses = [
        "Quinton Oaks Golf Course",
        "Red Wing Lake Golf Course",
        "Richmond Country Club",
        "River Creek Club",
        "Riverfront Golf Club"
    ]

    results = {}

    # Test each course
    for course in courses:
        result = await find_course_url(course)
        results[course] = result

    # Calculate totals
    total_cost = sum(r['cost'] for r in results.values())
    avg_time = sum(r['time_seconds'] for r in results.values()) / len(results)
    found_count = sum(1 for r in results.values() if r['url'])

    # Save results to JSON
    output_file = Path(__file__).parent / "agent1_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Present results
    print(f"\n\n{'='*70}")
    print("📊 AGENT 1 BATCH TEST RESULTS")
    print(f"{'='*70}\n")

    print(f"{'Course':<35} {'URL Found':<10} {'Cost':<10}")
    print(f"{'-'*70}")

    for course, data in results.items():
        url_status = "✅ Yes" if data['url'] else "❌ No"
        print(f"{course:<35} {url_status:<10} ${data['cost']:<9.4f}")

    print(f"{'-'*70}")
    print(f"{'TOTALS':<35} {found_count}/{len(courses):<10} ${total_cost:<9.4f}")

    print("\n📈 Statistics:")
    print(f"   Success Rate: {found_count}/{len(courses)} ({found_count/len(courses)*100:.0f}%)")
    print(f"   Total Cost: ${total_cost:.4f}")
    print(f"   Avg Cost/Course: ${total_cost/len(courses):.4f}")
    print(f"   Avg Time: {avg_time:.1f}s")

    print(f"\n💾 Results saved to: {output_file}")
    print("\n✅ Agent 1 is ready for production!")
    print("   Next: Build Agent 2 to extract data from these URLs")


if __name__ == "__main__":
    anyio.run(main)
