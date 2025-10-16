#!/usr/bin/env python3
"""
POC: Web Scraping with Jina MCP Server

This demonstrates:
1. Using external MCP server (Jina)
2. Web scraping real websites
3. Extracting specific information
4. Agent-based workflow for data extraction
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
    SystemMessage,
)


async def main():
    print("🌐 Starting Web Scraping POC with Jina MCP")
    print("=" * 70)

    # Check for API key
    jina_api_key = os.environ.get("JINA_API_KEY")
    if not jina_api_key:
        print("❌ ERROR: JINA_API_KEY environment variable not set!")
        print("\n📝 To fix this:")
        print("   1. Get a free API key from: https://jina.ai/?sui=apikey")
        print("   2. Set the environment variable:")
        print("      export JINA_API_KEY='your_api_key_here'")
        print("   3. Run this script again\n")
        return

    print(f"✅ Jina API Key found: {jina_api_key[:10]}...")
    print()

    # Configure Jina MCP server with API key
    # CRITICAL: Use "jina-mcp-tools" package (matches Claude Desktop config)
    # KEY DIFFERENCE FROM CLI: SDK needs 'env' field for API keys
    mcp_servers = {
        "jina": {
            "command": "npx",
            "args": ["-y", "jina-mcp-tools"],
            "env": {
                "JINA_API_KEY": jina_api_key
            }
        }
    }

    # Define scraper agent
    options = ClaudeAgentOptions(
        agents={
            "scraper": AgentDefinition(
                description="Scrapes websites and extracts specific information from web pages",
                prompt=(
                    "You are a web scraping specialist. Use the Jina MCP tools to:\n"
                    "1. Fetch web page content\n"
                    "2. Parse and analyze the content\n"
                    "3. Extract specific information requested\n"
                    "4. Return results in a clear, structured format\n\n"
                    "Be thorough in your search and provide the exact information requested."
                ),
                tools=["mcp__jina__fetch", "mcp__jina__search"],
                model="sonnet"
            )
        },
        mcp_servers=mcp_servers,
        allowed_tools=["mcp__jina__fetch", "mcp__jina__search"],
        permission_mode="acceptEdits"
    )

    # The scraping task
    target_url = "https://vsga.org/member-clubs"
    course_name = "Raspberry Falls Golf & Hunt Club"

    workflow_prompt = f"""
    Please use the scraper agent to complete this task:

    1. Scrape the webpage: {target_url}
    2. Find the course named: "{course_name}"
    3. Extract the URL link for that course
    4. Return the complete URL

    The expected URL format should be something like:
    https://vsga.org/courselisting/[ID]?hsLang=en

    Please provide the exact URL you find.
    """

    print("\n📝 Task:")
    print(f"   URL: {target_url}")
    print(f"   Looking for: {course_name}")
    print("\n" + "=" * 70)
    print("🤖 Executing Scraper Agent...\n")

    found_url = None

    # Execute the workflow using streaming mode (required for MCP servers)
    try:
        async with ClaudeSDKClient(options=options) as client:
            # Send the query
            await client.query(workflow_prompt)

            # Receive and process the response
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"💬 Claude: {block.text}")
                            print()

                            # Try to extract URL from response
                            if "vsga.org/courselisting" in block.text:
                                # Simple extraction
                                import re
                                urls = re.findall(r'https://vsga\.org/courselisting/\d+\?hsLang=en', block.text)
                                if urls:
                                    found_url = urls[0]

                elif isinstance(message, SystemMessage):
                    print(f"🔧 System: {message.subtype}")
                    if message.data:
                        # Show MCP server status
                        mcp_servers = message.data.get('mcp_servers', [])
                        if mcp_servers:
                            print(f"   MCP Servers: {mcp_servers}")
                    print()

                elif isinstance(message, ResultMessage):
                    print("=" * 70)
                    print("✅ Scraping Complete!")
                    print(f"⏱️  Duration: {message.duration_ms / 1000:.2f}s")
                    print(f"🔄 Turns: {message.num_turns}")
                    if message.total_cost_usd:
                        print(f"💰 Cost: ${message.total_cost_usd:.4f}")

                    if found_url:
                        print("\n" + "=" * 70)
                        print("🎯 RESULT FOUND:")
                        print(f"   {found_url}")
                        print("=" * 70)
                    else:
                        print("\n⚠️  Could not extract URL from response")

    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    anyio.run(main)
