#!/usr/bin/env python3
"""
Test BrightData MCP Tools Directly

Check if BrightData search_engine MCP tool actually works
"""

import json

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


async def test_brightdata_email_search():
    """Test BrightData search for email"""
    print("Testing: BrightData search_engine for email")
    print("="*70)

    options = ClaudeAgentOptions(
        allowed_tools=["mcp__BrightData__search_engine"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash"],
        permission_mode="bypassPermissions",
        max_turns=3,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use mcp__BrightData__search_engine to search for the email address. "
            f"Query: \"{TEST_CONTACT['name']} {TEST_CONTACT['company']} {TEST_CONTACT['title']} email\" "
            "Extract any email addresses from the search results. Return the email or 'NOT_FOUND'."
        ),
    )

    tools_used = []
    email_found = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Search for email: {TEST_CONTACT['name']} {TEST_CONTACT['company']}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        tools_used.append(block.name)
                        print(f"   ✓ Used: {block.name}")
                    elif isinstance(block, TextBlock):
                        # Extract email
                        import re
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, block.text)
                        if emails:
                            email_found = emails[0]

            if isinstance(msg, ResultMessage):
                print(f"\n   Email: {email_found or 'Not found'}")
                print(f"   Tools: {tools_used}")
                print(f"   Cost: ${msg.total_cost_usd:.4f}")
                print(f"   Turns: {msg.num_turns}")

                return {
                    "email": email_found,
                    "tools_used": tools_used,
                    "cost": msg.total_cost_usd,
                    "turns": msg.num_turns,
                }


async def test_brightdata_linkedin_search():
    """Test BrightData search for LinkedIn"""
    print("\n\nTesting: BrightData search_engine for LinkedIn")
    print("="*70)

    options = ClaudeAgentOptions(
        allowed_tools=["mcp__BrightData__search_engine"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash"],
        permission_mode="bypassPermissions",
        max_turns=3,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use mcp__BrightData__search_engine to find the LinkedIn profile. "
            f"Query: \"{TEST_CONTACT['name']} {TEST_CONTACT['company']} site:linkedin.com/in/\" "
            "Extract the linkedin.com/in/ URL from results. Return the URL or 'NOT_FOUND'."
        ),
    )

    tools_used = []
    linkedin_found = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Search for LinkedIn: {TEST_CONTACT['name']} {TEST_CONTACT['company']}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        tools_used.append(block.name)
                        print(f"   ✓ Used: {block.name}")
                    elif isinstance(block, TextBlock):
                        # Extract LinkedIn URL
                        import re
                        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
                        urls = re.findall(linkedin_pattern, block.text)
                        if urls:
                            linkedin_found = urls[0]

            if isinstance(msg, ResultMessage):
                print(f"\n   LinkedIn: {linkedin_found or 'Not found'}")
                print(f"   Tools: {tools_used}")
                print(f"   Cost: ${msg.total_cost_usd:.4f}")
                print(f"   Turns: {msg.num_turns}")

                return {
                    "linkedin_url": linkedin_found,
                    "tools_used": tools_used,
                    "cost": msg.total_cost_usd,
                    "turns": msg.num_turns,
                }


async def test_hunter_io():
    """Test Hunter.io Email-Finder"""
    print("\n\nTesting: Hunter.io Email-Finder")
    print("="*70)

    options = ClaudeAgentOptions(
        allowed_tools=["mcp__hunter-io__Email-Finder"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use mcp__hunter-io__Email-Finder to find the email. "
            f"Parameters: full_name=\"{TEST_CONTACT['name']}\", domain=\"{TEST_CONTACT['company_domain']}\" "
            "Return the email or 'NOT_FOUND'."
        ),
    )

    tools_used = []
    email_found = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find email via Hunter.io: {TEST_CONTACT['name']} at {TEST_CONTACT['company_domain']}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        tools_used.append(block.name)
                        print(f"   ✓ Used: {block.name}")
                    elif isinstance(block, TextBlock):
                        # Extract email
                        import re
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, block.text)
                        if emails:
                            email_found = emails[0]

            if isinstance(msg, ResultMessage):
                print(f"\n   Email: {email_found or 'Not found'}")
                print(f"   Tools: {tools_used}")
                print(f"   Cost: ${msg.total_cost_usd:.4f}")
                print(f"   Turns: {msg.num_turns}")

                return {
                    "email": email_found,
                    "tools_used": tools_used,
                    "cost": msg.total_cost_usd,
                    "turns": msg.num_turns,
                }


async def main():
    print("🧪 Testing MCP Tools Individually")
    print("="*70)
    print(f"Contact: {TEST_CONTACT['name']}\n")

    results = {}

    # Test each tool individually
    results["hunter_io"] = await test_hunter_io()
    results["brightdata_email"] = await test_brightdata_email_search()
    results["brightdata_linkedin"] = await test_brightdata_linkedin_search()

    # Summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}\n")

    total_cost = sum(r.get("cost", 0) for r in results.values() if r.get("cost"))

    for name, result in results.items():
        success = "✅" if (result.get("email") or result.get("linkedin_url")) else "❌"
        tool_used = "✅" if result.get("tools_used") else "❌"
        print(f"{name}: {success} (Tool used: {tool_used})")

    print(f"\nTotal Cost: ${total_cost:.4f}")

    # Save
    with open("../results/agent3_mcp_individual_tests.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n💾 Saved to: ../results/agent3_mcp_individual_tests.json")


if __name__ == "__main__":
    anyio.run(main)
