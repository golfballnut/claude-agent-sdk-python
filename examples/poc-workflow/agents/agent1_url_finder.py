#!/usr/bin/env python3
"""
Debug Agent: See what's actually happening

This script adds debugging to understand:
1. What command is actually being run
2. What stderr output shows
3. Which tools Claude actually tries to use
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
    ToolUseBlock,
)


@tool("fetch", "Get golf course listing links from VSGA directory", {"url": str})
async def fetch(args: dict[str, Any]) -> dict[str, Any]:
    """Smart fetch - extracts only course links to save tokens"""
    import httpx
    import re

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"https://r.jina.ai/{args['url']}")
        content = r.text

        # Extract ONLY course listing links (reduces 78K → ~2K tokens)
        # Format in Jina markdown: [Club Name XYZ](https://vsga.org/courselisting/12345?hsLang=en)
        links = re.findall(
            r'\[Club Name ([^\]]+)\]\((https://vsga\.org/courselisting/\d+[^\)]*)\)',
            content
        )

        if links:
            # Return formatted list of course name: URL
            result = "VSGA Golf Courses:\n\n"
            for name, url in links:
                result += f"{name}: {url}\n"

            print(f"\n   ✓ Extracted {len(links)} course links")
            return {"content": [{"type": "text", "text": result}]}
        else:
            # Fallback: return first 1000 chars if no links found
            print(f"\n   ⚠ No course links found, returning first 1000 chars")
            return {"content": [{"type": "text", "text": content[:1000]}]}


async def find_url(course_name: str, state_code: str = "VA") -> dict[str, Any]:
    """
    Find VSGA URL for a golf course

    Args:
        course_name: Name of golf course
        state_code: State (currently only VA supported)

    Returns:
        dict with: url, cost, turns
    """
    import re

    server = create_sdk_mcp_server("t", tools=[fetch])

    options = ClaudeAgentOptions(
        mcp_servers={"t": server},
        allowed_tools=["mcp__t__fetch"],
        disallowed_tools=["Task", "TodoWrite", "Grep", "Glob", "WebSearch", "WebFetch"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt="Use fetch tool to get https://vsga.org/member-clubs. It returns a list of courses. Find the requested course and return ONLY its URL."
    )

    found_url = None
    result_msg = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Find the URL for: {course_name}")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        urls = re.findall(r'https://vsga\.org/courselisting/\d+(?:\?hsLang=en)?', block.text)
                        if urls:
                            found_url = urls[0]

            elif isinstance(msg, ResultMessage):
                result_msg = msg

    return {
        "url": found_url,
        "cost": result_msg.total_cost_usd if result_msg else None,
        "turns": result_msg.num_turns if result_msg else None
    }


async def main():
    print("🔍 DEBUG AGENT - See What's Actually Happening")
    print("=" * 70)

    # Stderr callback to see what Claude Code is doing
    def log_stderr(line: str):
        print(f"[STDERR] {line}")

    server = create_sdk_mcp_server("t", tools=[fetch])

    options = ClaudeAgentOptions(
        mcp_servers={"t": server},
        allowed_tools=["mcp__t__fetch"],  # ONLY this tool
        disallowed_tools=["Task", "TodoWrite", "Grep", "Glob"],  # Block these explicitly
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt="Use fetch tool to get https://vsga.org/member-clubs. It returns a list of courses. Find the requested course and return ONLY its URL.",
        stderr=log_stderr  # Debug callback
    )

    print("\n📋 Configuration:")
    print(f"   allowed_tools: {options.allowed_tools}")
    print(f"   disallowed_tools: {options.disallowed_tools}")
    print(f"   permission_mode: {options.permission_mode}")
    print(f"   model: {options.model}")
    print("\n" + "=" * 70)
    print("🤖 Executing...\n")

    tools_used = []
    found_url = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Find the URL for: Bristow Manor Golf Club")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        tools_used.append(block.name)
                        print(f"\n🔧 TOOL USED: {block.name}")
                    elif isinstance(block, TextBlock):
                        if block.text.strip():
                            print(f"\n💬 {block.text[:200]}")
                            # Try to extract URL
                            import re
                            urls = re.findall(r'https://vsga\.org/courselisting/\d+(?:\?hsLang=en)?', block.text)
                            if urls:
                                found_url = urls[0]

            elif isinstance(msg, ResultMessage):
                print(f"\n{'='*70}")
                print(f"📊 Results:")
                print(f"   Found URL: {found_url or 'NOT FOUND'}")
                print(f"   Target: Bristow Manor Golf Club")
                if found_url:
                    print(f"   Status: ✅ FOUND")
                print(f"   Tools used: {tools_used}")
                print(f"   Cost: ${msg.total_cost_usd:.4f} (target: $0.02)")
                print(f"   Turns: {msg.num_turns}")

                # Analysis
                print(f"\n✓ Analysis:")
                if tools_used == ["mcp__t__fetch"]:
                    print(f"   ✅ Tool restriction - Only used allowed tool")
                if found_url:
                    print(f"   ✅ Accuracy - Found URL")
                if msg.total_cost_usd and msg.total_cost_usd <= 0.02:
                    print(f"   ✅ Cost - Under budget")
                else:
                    print(f"   ⚠️  Cost - Slightly over (${msg.total_cost_usd:.4f})")


if __name__ == "__main__":
    anyio.run(main)
