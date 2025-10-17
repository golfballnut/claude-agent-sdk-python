#!/usr/bin/env python3
"""
Two-Agent Workflow with Custom Tools

Proves the core pattern:
1. Two sequential subagents
2. Each with custom tools
3. Data flows from agent 1 → agent 2
4. End-to-end working example

Workflow:
- Fetcher Agent: Fetches data from URL using custom fetch tool
- Processor Agent: Processes fetched data using custom process tool
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


# ============================================================================
# CUSTOM TOOLS FOR FETCHER AGENT
# ============================================================================

@tool(
    "fetch_url",
    "Fetches content from a URL and returns clean text",
    {"url": str}
)
async def fetch_url(args: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch content from a URL using Jina Reader API (free, no auth needed).
    This is the fetcher agent's primary tool.
    """
    import httpx

    url = args["url"]
    jina_url = f"https://r.jina.ai/{url}"

    print(f"   📡 Fetcher Tool: Fetching {url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(jina_url)
            response.raise_for_status()
            content = response.text

            print(f"   ✓ Fetched {len(content)} characters")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Successfully fetched content from {url}:\n\n{content[:1000]}..."
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
# CUSTOM TOOLS FOR PROCESSOR AGENT
# ============================================================================

@tool(
    "extract_info",
    "Extracts specific information from text using keywords",
    {"text": str, "search_term": str}
)
async def extract_info(args: dict[str, Any]) -> dict[str, Any]:
    """
    Process text to extract specific information.
    This is the processor agent's primary tool.
    """
    text = args["text"]
    search_term = args["search_term"]

    print(f"   🔍 Processor Tool: Searching for '{search_term}'")

    # Simple extraction: find lines containing the search term
    lines = text.split('\n')
    matches = [line for line in lines if search_term.lower() in line.lower()]

    if matches:
        result = f"Found {len(matches)} matches for '{search_term}':\n\n"
        result += "\n".join(matches[:5])  # Top 5 matches
        print(f"   ✓ Found {len(matches)} matches")
    else:
        result = f"No matches found for '{search_term}'"
        print(f"   ✗ No matches found")

    return {
        "content": [
            {"type": "text", "text": result}
        ]
    }


@tool(
    "format_result",
    "Formats extracted data into a structured report",
    {"data": str, "title": str}
)
async def format_result(args: dict[str, Any]) -> dict[str, Any]:
    """
    Format data into a nice report.
    Secondary tool for processor agent.
    """
    data = args["data"]
    title = args["title"]

    print(f"   📝 Processor Tool: Formatting report '{title}'")

    report = f"""
# {title}

## Data

{data}

## Summary

Report generated successfully.
"""

    print(f"   ✓ Report formatted")

    return {
        "content": [
            {"type": "text", "text": report}
        ]
    }


# ============================================================================
# WORKFLOW SETUP
# ============================================================================

async def main():
    print("🚀 Two-Agent Workflow with Custom Tools")
    print("=" * 70)

    # Create MCP servers for each agent's tools
    fetcher_server = create_sdk_mcp_server(
        name="fetcher-tools",
        version="1.0.0",
        tools=[fetch_url]
    )

    processor_server = create_sdk_mcp_server(
        name="processor-tools",
        version="1.0.0",
        tools=[extract_info, format_result]
    )

    # Define the two subagents
    options = ClaudeAgentOptions(
        agents={
            "fetcher": AgentDefinition(
                description="Fetches content from URLs and retrieves web data",
                prompt=(
                    "You are a data fetcher agent. Your job is to:\n"
                    "1. Use the fetch_url tool to get content from URLs\n"
                    "2. Return the fetched data for the next agent to process\n"
                    "3. Be concise and pass data to the processor agent\n\n"
                    "Always use your fetch_url tool."
                ),
                tools=["mcp__fetcher-tools__fetch_url"],
                model="sonnet"
            ),
            "processor": AgentDefinition(
                description="Processes fetched data and extracts specific information",
                prompt=(
                    "You are a data processor agent. Your job is to:\n"
                    "1. Take data from the fetcher agent\n"
                    "2. Use extract_info tool to find specific information\n"
                    "3. Use format_result tool to create a formatted report\n"
                    "4. Present the final result clearly\n\n"
                    "Always use your tools to process data."
                ),
                tools=["mcp__processor-tools__extract_info", "mcp__processor-tools__format_result"],
                model="sonnet"
            )
        },
        mcp_servers={
            "fetcher-tools": fetcher_server,
            "processor-tools": processor_server
        },
        allowed_tools=[
            "mcp__fetcher-tools__fetch_url",
            "mcp__processor-tools__extract_info",
            "mcp__processor-tools__format_result"
        ],
        permission_mode="acceptEdits"
    )

    # The workflow task
    target_url = "https://vsga.org/member-clubs"
    search_term = "Raspberry Falls"

    workflow_prompt = f"""
    Complete this two-step workflow:

    STEP 1: Use the fetcher agent to:
    - Fetch content from: {target_url}

    STEP 2: Use the processor agent to:
    - Extract information about: "{search_term}"
    - Format the results into a report titled "VSGA Club Search Results"

    Execute these steps in sequence.
    """

    print("\n📋 Workflow:")
    print(f"   Step 1: Fetcher agent fetches {target_url}")
    print(f"   Step 2: Processor agent extracts '{search_term}'")
    print("\n" + "=" * 70)
    print("🤖 Executing...\n")

    # Track which tools were used
    tools_used = []

    # Execute workflow
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(workflow_prompt)

            async for message in client.receive_response():
                # Track tool usage
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                            print(f"🔧 Tool Used: {block.name}")
                        elif isinstance(block, TextBlock):
                            print(f"💬 Claude: {block.text}")
                            print()

                elif isinstance(message, SystemMessage):
                    if message.subtype == "init":
                        mcp_servers = message.data.get('mcp_servers', [])
                        print(f"📡 MCP Servers: {mcp_servers}\n")

                elif isinstance(message, ResultMessage):
                    print("=" * 70)
                    print("✅ Workflow Complete!")
                    print(f"⏱️  Duration: {message.duration_ms / 1000:.2f}s")
                    print(f"🔄 Turns: {message.num_turns}")
                    if message.total_cost_usd:
                        print(f"💰 Cost: ${message.total_cost_usd:.4f}")

                    print(f"\n🔧 Tools Used: {', '.join(set(tools_used))}")

                    # Verify both agents were used
                    if "mcp__fetcher-tools__fetch_url" in tools_used:
                        print("   ✅ Fetcher agent tools used")
                    else:
                        print("   ❌ Fetcher agent tools NOT used")

                    if any("processor-tools" in t for t in tools_used):
                        print("   ✅ Processor agent tools used")
                    else:
                        print("   ❌ Processor agent tools NOT used")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    anyio.run(main)
