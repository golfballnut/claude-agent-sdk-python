#!/usr/bin/env python3
"""
POC: Web Scraping with Custom Jina Tools (In-Process)

This demonstrates:
1. Creating custom tools that call external APIs
2. Using Jina Reader API (FREE, no API key needed)
3. In-process SDK MCP server (no subprocess issues)
4. Real web scraping with agent-based workflow

Key Difference from jina_scraper.py:
- This uses custom @tool functions calling Jina's API directly
- No external MCP server needed (no subprocess)
- Simpler, faster, more reliable
"""

import anyio
from typing import Any
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    SystemMessage,
    tool,
    create_sdk_mcp_server,
)


# Custom Jina tools using the Reader API
@tool(
    "jina_read",
    "Fetch and parse web page content using Jina Reader API. Returns clean, LLM-friendly markdown content.",
    {"url": str}
)
async def jina_read(args: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch web page content via Jina Reader API.

    Jina Reader API: https://r.jina.ai/
    - FREE, no API key required
    - Returns clean markdown optimized for LLMs
    - Fast (usually < 2 seconds)
    """
    import httpx

    url = args["url"]
    jina_url = f"https://r.jina.ai/{url}"

    print(f"   🌐 Fetching: {url}")
    print(f"   📡 Via: {jina_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(jina_url)
            response.raise_for_status()

            content = response.text
            print(f"   ✓ Retrieved {len(content)} characters")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Content from {url}:\n\n{content}"
                    }
                ]
            }

    except httpx.HTTPError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error fetching {url}: {str(e)}"
                }
            ],
            "is_error": True
        }


@tool(
    "jina_search",
    "Search the web and get content from top results using Jina Search API",
    {"query": str, "max_results": int}
)
async def jina_search(args: dict[str, Any]) -> dict[str, Any]:
    """
    Search the web via Jina Search API.

    Jina Search API: https://s.jina.ai/
    - Automatically fetches content from top search results
    - FREE, no API key required
    """
    import httpx

    query = args["query"]
    max_results = args.get("max_results", 5)

    jina_url = f"https://s.jina.ai/{query}"

    print(f"   🔍 Searching for: {query}")
    print(f"   📡 Via: {jina_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(jina_url)
            response.raise_for_status()

            content = response.text
            print(f"   ✓ Retrieved search results")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Search results for '{query}':\n\n{content}"
                    }
                ]
            }

    except httpx.HTTPError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error searching for '{query}': {str(e)}"
                }
            ],
            "is_error": True
        }


async def main():
    print("🌐 Starting Web Scraping POC with Custom Jina Tools")
    print("=" * 70)
    print("✨ Using in-process custom tools (no external MCP server needed)")
    print()

    # Create SDK MCP server with Jina tools
    jina_tools = create_sdk_mcp_server(
        name="jina-tools",
        version="1.0.0",
        tools=[jina_read, jina_search]
    )

    # Define scraper agent
    options = ClaudeAgentOptions(
        agents={
            "scraper": AgentDefinition(
                description="Scrapes websites and extracts specific information from web pages",
                prompt=(
                    "You are a web scraping specialist. Use the Jina tools to:\n"
                    "1. Fetch web page content (jina_read)\n"
                    "2. Search the web (jina_search)\n"
                    "3. Parse and analyze the content\n"
                    "4. Extract specific information requested\n\n"
                    "Be thorough in your search and provide exact information."
                ),
                tools=["mcp__jina-tools__jina_read", "mcp__jina-tools__jina_search"],
                model="sonnet"
            )
        },
        mcp_servers={"jina-tools": jina_tools},
        allowed_tools=["mcp__jina-tools__jina_read", "mcp__jina-tools__jina_search"],
        permission_mode="acceptEdits"
    )

    # The scraping task
    target_url = "https://vsga.org/member-clubs"
    course_name = "Raspberry Falls Golf & Hunt Club"

    workflow_prompt = f"""
    Please use the scraper agent to complete this task:

    1. Use jina_read to fetch the webpage: {target_url}
    2. Find the course named: "{course_name}"
    3. Extract the URL link for that course
    4. Return the complete URL

    The expected URL format should be:
    https://vsga.org/courselisting/[ID]?hsLang=en

    Please provide the exact URL you find.
    """

    print("📝 Task:")
    print(f"   URL: {target_url}")
    print(f"   Looking for: {course_name}")
    print("\n" + "=" * 70)
    print("🤖 Executing Scraper Agent...\n")

    found_url = None

    # Execute the workflow
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
                                import re
                                # Match both numeric IDs and slug-based URLs
                                urls = re.findall(r'https://vsga\.org/courselisting/[\w\-]+(?:\?hsLang=en)?', block.text)
                                if urls:
                                    found_url = urls[0]

                elif isinstance(message, SystemMessage):
                    if message.subtype == "init":
                        # Show MCP server status
                        mcp_servers = message.data.get('mcp_servers', [])
                        if mcp_servers:
                            print(f"🔧 MCP Servers: {mcp_servers}\n")

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
