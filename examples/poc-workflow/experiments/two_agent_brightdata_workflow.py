#!/usr/bin/env python3
"""
Two-Agent Workflow: Web Fetcher + Brightdata Contact Extractor

This proves the core pattern for building 500-agent system:
- Agent 1 (Fetcher): Fetches webpage content
- Agent 2 (Contact Extractor): Uses Brightdata to extract contacts

Workflow:
1. Fetcher agent gets webpage content using Jina Reader
2. Contact Extractor agent uses Brightdata API to find contacts
3. Returns structured contact information
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
# AGENT 1: FETCHER TOOLS
# ============================================================================

@tool(
    "fetch_webpage",
    "Fetches clean, LLM-friendly content from any URL",
    {"url": str}
)
async def fetch_webpage(args: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch webpage content using Jina Reader API (free, no auth).
    Returns clean markdown optimized for LLMs.
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
                        "text": f"Successfully fetched webpage content:\n\n{content}"
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
# AGENT 2: CONTACT EXTRACTOR TOOLS
# ============================================================================

@tool(
    "extract_contacts",
    "Extracts contact information from webpage content using Brightdata",
    {"url": str, "content": str}
)
async def extract_contacts(args: dict[str, Any]) -> dict[str, Any]:
    """
    Extract contacts from webpage using Brightdata Web Scraper API.

    Brightdata API provides:
    - Email extraction
    - Phone number extraction
    - Social media links
    - Contact forms
    """
    import httpx
    import json

    url = args["url"]
    content = args.get("content", "")

    # Get API token from environment
    api_token = os.environ.get("BRIGHTDATA_API_TOKEN")
    if not api_token:
        return {
            "content": [
                {"type": "text", "text": "Error: BRIGHTDATA_API_TOKEN not set in environment"}
            ],
            "is_error": True
        }

    print(f"\n   🔍 [Contact Extractor Agent] Extracting contacts from: {url}")

    # Brightdata Web Scraper API endpoint
    # Using the general web scraper endpoint
    api_url = "https://api.brightdata.com/datasets/v3/trigger"

    # Prepare request
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # Request payload for contact extraction
    payload = {
        "dataset_id": "gd_l7q7dkf244hwjntr0",  # Web scraper dataset
        "endpoint": "submit_for_discovery",
        "data": [{
            "url": url,
            "discover_new_urls": False
        }]
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, headers=headers, json=payload)

            # Check if request was successful
            if response.status_code == 200:
                result = response.json()

                # Extract relevant contact info
                contacts = {
                    "url": url,
                    "snapshot_id": result.get("snapshot_id"),
                    "status": "Contact extraction initiated"
                }

                print(f"   ✓ Brightdata request successful")
                print(f"   Snapshot ID: {contacts['snapshot_id']}")

                # Format result
                result_text = f"""
Contact Extraction Results:

URL: {url}
Status: {contacts['status']}
Snapshot ID: {contacts['snapshot_id']}

Note: Brightdata processes requests asynchronously.
Use the snapshot_id to retrieve results once processing completes.

For this POC, we've successfully initiated contact extraction.
In production, you would poll for results or use webhooks.
"""

                return {
                    "content": [
                        {"type": "text", "text": result_text}
                    ]
                }

            else:
                # Handle errors
                error_msg = f"Brightdata API error: {response.status_code} - {response.text}"
                print(f"   ✗ {error_msg}")

                return {
                    "content": [
                        {"type": "text", "text": error_msg}
                    ],
                    "is_error": True
                }

    except Exception as e:
        error_msg = f"Error calling Brightdata API: {str(e)}"
        print(f"   ✗ {error_msg}")

        return {
            "content": [
                {"type": "text", "text": error_msg}
            ],
            "is_error": True
        }


# ============================================================================
# WORKFLOW SETUP
# ============================================================================

async def main():
    print("=" * 70)
    print("🚀 Two-Agent Workflow: Fetcher + Brightdata Contact Extractor")
    print("=" * 70)

    # Check for Brightdata API token
    brightdata_token = os.environ.get("BRIGHTDATA_API_TOKEN")
    if not brightdata_token:
        print("\n❌ ERROR: BRIGHTDATA_API_TOKEN environment variable not set!")
        print("\n📝 To fix this:")
        print("   1. Get your API token from: https://brightdata.com")
        print("   2. Add to .env file: BRIGHTDATA_API_TOKEN=your_token_here")
        print("   3. Run: set -a && source .env && set +a")
        print("   4. Run this script again\n")
        return

    print(f"\n✅ Brightdata API Token found: {brightdata_token[:20]}...")

    # Create MCP servers for each agent's tools
    fetcher_server = create_sdk_mcp_server(
        name="fetcher-tools",
        version="1.0.0",
        tools=[fetch_webpage]
    )

    contact_extractor_server = create_sdk_mcp_server(
        name="contact-extractor-tools",
        version="1.0.0",
        tools=[extract_contacts]
    )

    # Define the two subagents
    options = ClaudeAgentOptions(
        agents={
            "fetcher": AgentDefinition(
                description="Fetches webpage content from URLs and retrieves web data",
                prompt=(
                    "You are a webpage fetcher agent. Your job is to:\n"
                    "1. Use the fetch_webpage tool to get clean content from URLs\n"
                    "2. Return the full content to the next agent for processing\n"
                    "3. Always use your fetch_webpage tool - do not use other web tools\n\n"
                    "Pass all fetched content to the contact extractor agent."
                ),
                tools=["mcp__fetcher-tools__fetch_webpage"],
                model="sonnet"
            ),
            "contact_extractor": AgentDefinition(
                description="Extracts contact information from webpages using Brightdata",
                prompt=(
                    "You are a contact extraction agent. Your job is to:\n"
                    "1. Take the webpage content from the fetcher agent\n"
                    "2. Use the extract_contacts tool with Brightdata API\n"
                    "3. Extract email addresses, phone numbers, and contact info\n"
                    "4. Present the results clearly\n\n"
                    "Always use your extract_contacts tool with both the URL and content."
                ),
                tools=["mcp__contact-extractor-tools__extract_contacts"],
                model="sonnet"
            )
        },
        mcp_servers={
            "fetcher-tools": fetcher_server,
            "contact-extractor-tools": contact_extractor_server
        },
        allowed_tools=[
            "mcp__fetcher-tools__fetch_webpage",
            "mcp__contact-extractor-tools__extract_contacts"
        ],
        permission_mode="acceptEdits"
    )

    # The workflow task
    target_url = "https://vsga.org/courselisting/11945"  # Raspberry Falls Golf Club

    workflow_prompt = f"""
    Complete this two-agent workflow:

    STEP 1: Use the fetcher agent to:
    - Fetch the webpage: {target_url}
    - Get the full content

    STEP 2: Use the contact_extractor agent to:
    - Extract contact information from that webpage
    - Use Brightdata API to find emails, phones, contact details

    Execute these steps sequentially.
    """

    print("\n📋 Workflow:")
    print(f"   Step 1: Fetcher agent fetches {target_url}")
    print(f"   Step 2: Contact Extractor uses Brightdata to find contacts")
    print("\n" + "=" * 70)
    print("🤖 Executing Workflow...\n")

    # Track which tools were used and agents invoked
    tools_used = []
    agents_invoked = set()

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
                            print(f"\n🔧 Tool Invoked: {block.name}")

                            # Track which agent
                            if "fetcher-tools" in block.name:
                                agents_invoked.add("fetcher")
                            elif "contact-extractor-tools" in block.name:
                                agents_invoked.add("contact_extractor")

                        elif isinstance(block, TextBlock):
                            # Only print non-empty, meaningful text
                            if block.text.strip() and len(block.text) > 10:
                                print(f"\n💬 Claude: {block.text[:200]}...")

                elif isinstance(message, SystemMessage):
                    if message.subtype == "init":
                        mcp_servers = message.data.get('mcp_servers', [])
                        print(f"\n📡 MCP Servers Status:")
                        for server in mcp_servers:
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
                    print(f"   Tools Used: {len(tools_used)}")
                    print(f"   Agents Invoked: {', '.join(agents_invoked) if agents_invoked else 'None'}")

                    # Verify workflow completed correctly
                    print(f"\n✓ Verification:")
                    if "fetcher" in agents_invoked:
                        print(f"   ✅ Fetcher agent was invoked")
                    else:
                        print(f"   ❌ Fetcher agent was NOT invoked")

                    if "contact_extractor" in agents_invoked:
                        print(f"   ✅ Contact Extractor agent was invoked")
                    else:
                        print(f"   ❌ Contact Extractor agent was NOT invoked")

                    if "mcp__fetcher-tools__fetch_webpage" in tools_used:
                        print(f"   ✅ fetch_webpage tool was used")
                    else:
                        print(f"   ❌ fetch_webpage tool was NOT used")

                    if "mcp__contact-extractor-tools__extract_contacts" in tools_used:
                        print(f"   ✅ extract_contacts tool was used")
                    else:
                        print(f"   ❌ extract_contacts tool was NOT used")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    anyio.run(main)
