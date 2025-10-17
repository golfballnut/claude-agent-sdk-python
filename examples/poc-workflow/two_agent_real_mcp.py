#!/usr/bin/env python3
"""
Two-Agent Workflow with Real External MCP Servers

PROVEN PATTERN:
- Agent 1 (Fetcher): Uses custom in-process tool (Jina Reader)
- Agent 2 (Contact Extractor): Uses external Brightdata MCP server
- Sequential execution: Fetcher → Contact Extractor

This demonstrates:
1. Mixing custom tools (SDK MCP) with external MCP servers
2. Two sequential subagents working together
3. Real production-ready pattern
4. Configuration matching Claude Desktop setup
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
# AGENT 1: FETCHER - Custom In-Process Tool
# ============================================================================

@tool(
    "fetch_webpage",
    "Fetches clean, LLM-friendly content from any URL using Jina Reader",
    {"url": str}
)
async def fetch_webpage(args: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch webpage content using Jina Reader API (free, no auth).
    This is a custom in-process tool.
    """
    import httpx

    url = args["url"]
    jina_url = f"https://r.jina.ai/{url}"

    print(f"\n   🌐 [Fetcher Agent] Fetching: {url}")

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
                        "text": f"Webpage content from {url}:\n\n{content}"
                    }
                ]
            }
    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error fetching {url}: {str(e)}"}
            ],
            "is_error": True
        }


# ============================================================================
# WORKFLOW SETUP
# ============================================================================

async def main():
    print("=" * 70)
    print("🚀 Two-Agent Workflow: Custom Tools + External MCP")
    print("=" * 70)

    # Check for Brightdata API token
    api_token = os.environ.get("BRIGHTDATA_API_TOKEN")
    if not api_token:
        print("\n❌ ERROR: BRIGHTDATA_API_TOKEN environment variable not set!")
        print("\n📝 To fix this:")
        print("   Add to .env file: BRIGHTDATA_API_TOKEN=your_token_here")
        print("   Run: set -a && source .env && set +a\n")
        return

    print(f"\n✅ Brightdata API Token found: {api_token[:20]}...")

    # Create SDK MCP server for fetcher agent (in-process)
    fetcher_server = create_sdk_mcp_server(
        name="fetcher-tools",
        version="1.0.0",
        tools=[fetch_webpage]
    )

    # Configure external Brightdata MCP server (matching Claude Desktop config)
    mcp_servers = {
        "fetcher-tools": fetcher_server,  # In-process custom tools
        "brightdata": {                   # External MCP server
            "command": "npx",
            "args": ["@brightdata/mcp"],
            "env": {
                "API_TOKEN": api_token,   # Brightdata expects API_TOKEN not BRIGHTDATA_API_TOKEN
                "PRO_MODE": "1"           # Enable all 60+ tools
            }
        }
    }

    # Define the two subagents
    options = ClaudeAgentOptions(
        agents={
            "fetcher": AgentDefinition(
                description="Fetches webpage content from URLs",
                prompt=(
                    "You are a webpage fetcher agent. Your job is to:\n"
                    "1. Use the fetch_webpage tool to get content from URLs\n"
                    "2. Return the URL and content to the next agent\n"
                    "3. Always use fetch_webpage tool - do not use other web tools\n\n"
                    "Be concise and pass data to the contact_extractor agent."
                ),
                tools=["mcp__fetcher-tools__fetch_webpage"],
                model="sonnet"
            ),
            "contact_extractor": AgentDefinition(
                description="Extracts contact information, emails, and phone numbers from webpages using Brightdata",
                prompt=(
                    "You are a contact extraction specialist. Your job is to:\n"
                    "1. Take the URL from the fetcher agent\n"
                    "2. Use Brightdata MCP tools to extract contact information\n"
                    "3. Find emails, phone numbers, social links, contact forms\n"
                    "4. Present results in a structured format\n\n"
                    "You have access to 60+ Brightdata tools in PRO_MODE.\n"
                    "Use the appropriate tools for contact extraction."
                ),
                tools=None,  # Inherits all tools (will have access to all Brightdata tools)
                model="sonnet"
            )
        },
        mcp_servers=mcp_servers,
        allowed_tools=[
            "mcp__fetcher-tools__fetch_webpage",
            # Allow all Brightdata tools (PRO_MODE gives 60+ tools)
            "mcp__brightdata__*"
        ],
        permission_mode="acceptEdits"
    )

    # The workflow task
    target_url = "https://vsga.org/courselisting/11945"  # Raspberry Falls Golf Club

    workflow_prompt = f"""
    Complete this two-agent workflow sequentially:

    STEP 1 (Fetcher Agent):
    - Use fetch_webpage tool to get content from: {target_url}

    STEP 2 (Contact Extractor Agent):
    - Use Brightdata tools to extract contact information from that page
    - Find: emails, phone numbers, contact forms, social media links
    - Return structured contact data

    Execute in sequence: fetcher first, then contact extractor.
    """

    print("\n📋 Workflow:")
    print(f"   Agent 1: Fetcher (custom tool)")
    print(f"   Agent 2: Contact Extractor (Brightdata MCP - 60+ tools)")
    print(f"   Target: {target_url}")
    print("\n" + "=" * 70)
    print("🤖 Executing Workflow...\n")

    # Track execution
    tools_used = []
    agents_invoked = set()

    # Execute workflow
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(workflow_prompt)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                            print(f"\n🔧 Tool Invoked: {block.name}")

                            # Track agents
                            if "fetcher-tools" in block.name:
                                agents_invoked.add("fetcher")
                            elif "brightdata" in block.name:
                                agents_invoked.add("contact_extractor")

                        elif isinstance(block, TextBlock):
                            # Print meaningful text
                            if block.text.strip() and len(block.text) > 20:
                                print(f"\n💬 Claude: {block.text[:300]}...")

                elif isinstance(message, SystemMessage):
                    if message.subtype == "init":
                        mcp_servers_status = message.data.get('mcp_servers', [])
                        print(f"\n📡 MCP Servers Status:")
                        for server in mcp_servers_status:
                            status_icon = "✅" if server['status'] == 'connected' else "❌"
                            print(f"   {status_icon} {server['name']}: {server['status']}")

                elif isinstance(message, ResultMessage):
                    print("\n" + "=" * 70)
                    print("✅ Workflow Complete!")
                    print(f"⏱️  Duration: {message.duration_ms / 1000:.2f}s")
                    print(f"🔄 Turns: {message.num_turns}")
                    if message.total_cost_usd:
                        print(f"💰 Cost: ${message.total_cost_usd:.4f}")

                    print(f"\n📊 Workflow Analysis:")
                    print(f"   Total Tools Used: {len(tools_used)}")
                    print(f"   Agents Invoked: {', '.join(agents_invoked) if agents_invoked else 'None'}")

                    print(f"\n✓ Verification:")
                    if "fetcher" in agents_invoked:
                        print(f"   ✅ Fetcher agent invoked")
                    else:
                        print(f"   ❌ Fetcher agent NOT invoked")

                    if "contact_extractor" in agents_invoked:
                        print(f"   ✅ Contact Extractor agent invoked")
                    else:
                        print(f"   ❌ Contact Extractor agent NOT invoked")

                    # Show all tools used
                    print(f"\n📋 Tools Used:")
                    for tool_name in set(tools_used):
                        print(f"   - {tool_name}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    anyio.run(main)
