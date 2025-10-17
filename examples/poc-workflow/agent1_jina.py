#!/usr/bin/env python3
"""
Agent 1 - Version A: URL Finder with Custom Jina Tool

Tests: Custom in-process tool using Jina Reader API (FREE)

Goal: Find correct numeric courselisting URL from VSGA member directory
"""

import anyio
from typing import Any
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    SystemMessage,
)


# Custom tool using Jina Reader (FREE)
@tool(
    "fetch_webpage",
    "Fetches clean, LLM-friendly content from any URL",
    {"url": str}
)
async def fetch_webpage(args: dict[str, Any]) -> dict[str, Any]:
    """Fetch webpage using Jina Reader API"""
    import httpx

    url = args["url"]
    jina_url = f"https://r.jina.ai/{url}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(jina_url)
            response.raise_for_status()
            return {
                "content": [{"type": "text", "text": response.text}]
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "is_error": True
        }


async def test_agent(course_name: str, expected_url: str = None):
    """Test Agent 1 with a course name"""
    print(f"\n{'='*70}")
    print(f"🧪 TEST: {course_name}")
    print(f"{'='*70}")

    # Create MCP server
    server = create_sdk_mcp_server(name="fetcher", version="1.0.0", tools=[fetch_webpage])

    # Configure Agent 1
    options = ClaudeAgentOptions(
        agents={
            "url_finder": AgentDefinition(
                description="Finds golf course URLs from VSGA directory",
                prompt=(
                    "You are a URL finder specialist.\n\n"
                    "GOAL: Find the EXACT courselisting URL for a golf course from VSGA.\n\n"
                    "PROCESS:\n"
                    "1. Use fetch_webpage to get https://vsga.org/member-clubs\n"
                    "2. Search for the exact course name in the content\n"
                    "3. Extract the href link next to that course name\n"
                    "4. The URL will be in format: https://vsga.org/courselisting/[NUMBER]\n\n"
                    "CRITICAL REQUIREMENTS:\n"
                    "- Find the NUMERIC ID URL (e.g., /courselisting/11945)\n"
                    "- Do NOT return slug URLs (e.g., /courselisting/course-name)\n"
                    "- Look for the actual href/link in the HTML\n"
                    "- Return ONLY the complete URL with ?hsLang=en parameter\n\n"
                    "OUTPUT FORMAT:\n"
                    "URL: https://vsga.org/courselisting/[ID]?hsLang=en\n\n"
                    "Be precise. Double-check the URL is numeric."
                ),
                tools=["mcp__fetcher__fetch_webpage"],
                model="sonnet"
            )
        },
        mcp_servers={"fetcher": server},
        allowed_tools=["mcp__fetcher__fetch_webpage"],
        permission_mode="acceptEdits"
    )

    # The task
    prompt = f"""
    Find the courselisting URL for: "{course_name}"

    Use fetch_webpage to get https://vsga.org/member-clubs
    Then find the EXACT numeric ID URL for this course.

    Return ONLY the URL in this format:
    URL: https://vsga.org/courselisting/[ID]?hsLang=en
    """

    # Track results
    found_url = None
    tools_used = []

    start_time = anyio.current_time()

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
                print(f"   Tools: {len(tools_used)}")

                return {
                    "found_url": found_url,
                    "expected_url": expected_url,
                    "correct": found_url == expected_url if expected_url else None,
                    "duration": duration,
                    "cost": cost,
                    "turns": message.num_turns
                }


async def main():
    print("=" * 70)
    print("🧪 AGENT 1 BENCHMARK - VERSION A: Custom Jina Tool (FREE)")
    print("=" * 70)

    # Test cases
    results = []

    # Test 1
    result1 = await test_agent(
        "Raspberry Falls Golf & Hunt Club",
        "https://vsga.org/courselisting/11945?hsLang=en"
    )
    results.append(("Test 1", result1))

    # Test 2
    result2 = await test_agent(
        "Bristow Manor Golf Club",
        None  # We don't know the expected ID yet
    )
    results.append(("Test 2", result2))

    # Summary
    print(f"\n\n{'='*70}")
    print("📊 SUMMARY - VERSION A (Jina)")
    print(f"{'='*70}")

    total_cost = sum(r[1]['cost'] for r in results)
    avg_duration = sum(r[1]['duration'] for r in results) / len(results)
    accuracy = sum(1 for r in results if r[1].get('correct') == True) / sum(1 for r in results if r[1].get('correct') is not None)

    print(f"\nTotal Cost: ${total_cost:.4f}")
    print(f"Avg Duration: {avg_duration:.2f}s")
    if accuracy:
        print(f"Accuracy: {accuracy * 100:.0f}%")

    print(f"\nResults:")
    for name, result in results:
        print(f"  {name}: {result['found_url']}")


if __name__ == "__main__":
    anyio.run(main)
