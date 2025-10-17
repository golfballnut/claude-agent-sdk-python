#!/usr/bin/env python3
"""
Real-World Test: Extract Data from Bristow Manor Golf Club

Let the agents do ALL the work:
- Agent 1: Find the course URL from member directory
- Agent 2: Extract important data from course page

This tests:
- Sequential agent execution
- Data passing between agents
- Real data extraction
- Accuracy of results
"""

import anyio
import os
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


# ============================================================================
# CUSTOM TOOL FOR FETCHING
# ============================================================================

@tool(
    "fetch_webpage",
    "Fetches clean content from any URL using Jina Reader",
    {"url": str}
)
async def fetch_webpage(args: dict[str, Any]) -> dict[str, Any]:
    """Fetch webpage content"""
    import httpx

    url = args["url"]
    jina_url = f"https://r.jina.ai/{url}"

    print(f"\n   🌐 Fetching: {url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(jina_url)
            response.raise_for_status()
            content = response.text
            print(f"   ✓ Retrieved {len(content)} characters")

            return {
                "content": [{"type": "text", "text": content}]
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "is_error": True
        }


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

async def main():
    print("=" * 70)
    print("🏌️  Bristow Manor Golf Club - Data Extraction")
    print("=" * 70)

    # Check API token
    api_token = os.environ.get("BRIGHTDATA_API_TOKEN")
    if not api_token:
        print("\n❌ ERROR: BRIGHTDATA_API_TOKEN not set")
        return

    print(f"\n✅ API Token found")

    # Create MCP servers
    fetcher_server = create_sdk_mcp_server(
        name="fetcher",
        version="1.0.0",
        tools=[fetch_webpage]
    )

    # Configure agents with VERY CLEAR instructions
    options = ClaudeAgentOptions(
        agents={
            "url_finder": AgentDefinition(
                description="Finds course URLs from VSGA member directory",
                prompt=(
                    "You are a URL finder agent.\n\n"
                    "TASK: Find the exact URL for a golf course from the VSGA directory.\n\n"
                    "STEPS:\n"
                    "1. Use fetch_webpage to get https://vsga.org/member-clubs\n"
                    "2. Search the content for the course name\n"
                    "3. Extract the courselisting URL (format: https://vsga.org/courselisting/[ID])\n"
                    "4. Return ONLY the URL - nothing else\n\n"
                    "IMPORTANT: Return the exact numeric ID URL, not a slug."
                ),
                tools=["mcp__fetcher__fetch_webpage"],
                model="sonnet"
            ),
            "data_extractor": AgentDefinition(
                description="Extracts contact and important information from golf course pages",
                prompt=(
                    "You are a data extraction agent.\n\n"
                    "TASK: Extract important information from a golf course webpage.\n\n"
                    "WHAT TO EXTRACT:\n"
                    "- Course name\n"
                    "- Full address (street, city, state, zip)\n"
                    "- Phone number\n"
                    "- Email address\n"
                    "- Website URL\n"
                    "- Social media links\n"
                    "- Any membership or contact information\n\n"
                    "STEPS:\n"
                    "1. Take the URL from the url_finder agent\n"
                    "2. Use fetch_webpage to get the course page\n"
                    "3. Use Brightdata tools if helpful for extraction\n"
                    "4. Present data in a clear, structured format\n\n"
                    "Focus on accuracy - only report data you actually find."
                ),
                tools=["mcp__fetcher__fetch_webpage", "mcp__brightdata__*"],
                model="sonnet"
            )
        },
        mcp_servers={
            "fetcher": fetcher_server,
            "brightdata": {
                "command": "npx",
                "args": ["@brightdata/mcp"],
                "env": {
                    "API_TOKEN": api_token,
                    "PRO_MODE": "1"
                }
            }
        },
        allowed_tools=[
            "mcp__fetcher__fetch_webpage",
            "mcp__brightdata__*"
        ],
        permission_mode="acceptEdits"
    )

    # The task
    course_name = "Bristow Manor Golf Club"

    workflow_prompt = f"""
    Find and extract data for: {course_name}

    STEP 1 (url_finder agent):
    Find the courselisting URL for "{course_name}" from https://vsga.org/member-clubs
    Return the exact URL.

    STEP 2 (data_extractor agent):
    Using the URL from Step 1, extract and present:
    - Course name and location
    - Address (complete)
    - Phone number
    - Email
    - Website
    - Any other contact information

    Present the data clearly and concisely. Focus on accuracy.
    """

    print(f"\n🎯 Target: {course_name}")
    print("\n" + "=" * 70)
    print("🤖 Executing Agents...\n")

    # Execute
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(workflow_prompt)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            print(f"🔧 {block.name}")
                        elif isinstance(block, TextBlock):
                            if "Bristow" in block.text or "http" in block.text or "Phone" in block.text or "Address" in block.text:
                                print(f"\n{block.text}")

                elif isinstance(message, SystemMessage):
                    if message.subtype == "init":
                        servers = message.data.get('mcp_servers', [])
                        for s in servers:
                            icon = "✅" if s['status'] == 'connected' else "❌"
                            print(f"{icon} {s['name']}")

                elif isinstance(message, ResultMessage):
                    print(f"\n{'='*70}")
                    print(f"⏱️  {message.duration_ms/1000:.2f}s | 💰 ${message.total_cost_usd:.4f}")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    anyio.run(main)
