#!/usr/bin/env python3
"""
Agent 1 Ultra-Lean: URL Finder

TARGET: $0.02 or less per search
APPROACH: Minimal tools, direct prompt, no extras
"""

import anyio
from typing import Any
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


# Single custom tool
@tool("fetch", "Fetch web page", {"url": str})
async def fetch(args: dict[str, Any]) -> dict[str, Any]:
    """Fetch using Jina Reader"""
    import httpx
    url = f"https://r.jina.ai/{args['url']}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        return {"content": [{"type": "text", "text": response.text}]}


async def find_url(course_name: str, expected: str = None):
    """Test finding a course URL"""
    print(f"\n{'='*70}\n🎯 Finding: {course_name}\n{'='*70}")

    server = create_sdk_mcp_server("tools", tools=[fetch])

    options = ClaudeAgentOptions(
        mcp_servers={"tools": server},
        allowed_tools=["mcp__tools__fetch"],  # ONLY this tool
        disallowed_tools=["Task", "TodoWrite", "WebFetch", "Bash", "WebSearch"],  # Block these
        permission_mode="bypassPermissions",  # No asking
        max_turns=3,  # Limit turns to control cost
        system_prompt=f"""You find golf course URLs.

Use fetch tool to get https://vsga.org/member-clubs
Find "{course_name}" in the content.
Extract its numeric URL: https://vsga.org/courselisting/[NUMBER]?hsLang=en

Return only: URL: [the url]"""
    )

    found = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Find URL for {course_name}")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        import re
                        urls = re.findall(r'https://vsga\.org/courselisting/\d+(?:\?hsLang=en)?', block.text)
                        if urls:
                            found = urls[0]

            elif isinstance(msg, ResultMessage):
                match = "✅" if found == expected else "❌" if expected else "?"
                print(f"\n📊 Found: {found or 'NONE'}")
                if expected:
                    print(f"   Expected: {expected} {match}")
                print(f"   Cost: ${msg.total_cost_usd:.4f} | Time: {msg.duration_ms/1000:.1f}s | Turns: {msg.num_turns}")

                return {"url": found, "cost": msg.total_cost_usd, "time": msg.duration_ms/1000, "turns": msg.num_turns}


async def main():
    print("\n🧪 ULTRA-LEAN AGENT 1 TEST")

    r1 = await find_url("Raspberry Falls Golf & Hunt Club", "https://vsga.org/courselisting/11945?hsLang=en")
    r2 = await find_url("Bristow Manor Golf Club")

    total = (r1['cost'] if r1 else 0) + (r2['cost'] if r2 else 0)
    print(f"\n{'='*70}")
    print(f"💰 TOTAL COST: ${total:.4f}")
    print(f"🎯 TARGET: $0.02 or less")
    print(f"   Status: {'✅ PASS' if total <= 0.02 else '❌ OVER BUDGET'}")


if __name__ == "__main__":
    anyio.run(main)
