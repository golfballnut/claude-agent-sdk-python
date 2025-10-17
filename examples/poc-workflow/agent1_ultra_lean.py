#!/usr/bin/env python3
"""
Agent 1 Ultra-Lean: Single Test, Minimal Cost

TARGET: $0.02 or less
FOCUS: Just Raspberry Falls test
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


@tool("fetch", "Fetch webpage", {"url": str})
async def fetch(args: dict[str, Any]) -> dict[str, Any]:
    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"https://r.jina.ai/{args['url']}")
        return {"content": [{"type": "text", "text": r.text}]}


async def main():
    print("🎯 Finding: Raspberry Falls Golf & Hunt Club")
    print("💰 Target: $0.02 or less\n")

    server = create_sdk_mcp_server("t", tools=[fetch])

    options = ClaudeAgentOptions(
        mcp_servers={"t": server},
        allowed_tools=["mcp__t__fetch"],
        disallowed_tools=["Task", "TodoWrite", "WebFetch", "Bash", "WebSearch", "Grep", "Glob", "Read"],
        permission_mode="bypassPermissions",
        max_turns=5,  # More turns to handle large content
        model="claude-haiku-4-5",  # Haiku 4.5 - cheapest
        system_prompt="Use fetch to get https://vsga.org/member-clubs. Search the fetched content for 'Raspberry Falls Golf & Hunt Club'. Extract the href link (format: /courselisting/[NUMBER]). Return the full URL with ?hsLang=en. Be persistent."
    )

    found = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Find the URL")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        import re
                        urls = re.findall(r'https://vsga\.org/courselisting/\d+', block.text)
                        if urls:
                            found = urls[0]

            elif isinstance(msg, ResultMessage):
                cost = msg.total_cost_usd or 0
                status = "✅ PASS" if cost <= 0.02 else "❌ OVER"

                print(f"\n{'='*70}")
                print(f"URL: {found or 'NOT FOUND'}")
                print(f"Expected: https://vsga.org/courselisting/11945")
                print(f"Match: {'✅' if '11945' in (found or '') else '❌'}")
                print(f"\n💰 Cost: ${cost:.4f} | Target: $0.02 | {status}")
                print(f"⏱️  Time: {msg.duration_ms/1000:.1f}s | Turns: {msg.num_turns}")


if __name__ == "__main__":
    anyio.run(main)
