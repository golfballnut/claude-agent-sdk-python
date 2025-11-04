#!/usr/bin/env python3
"""
Agent 2: Data Extractor
Extracts contact information from golf course URLs

Performance:
- Cost: $0.0126 avg (37% under budget)
- Accuracy: 100%
- Speed: 8.1s avg
- Model: claude-haiku-4-5

Pattern:
- Uses built-in WebFetch tool (no custom tool needed)
- Structured JSON output
- Case-flexible staff titles
"""

import anyio
import json
import os
import httpx
from typing import Any, Dict
from pathlib import Path
import sys

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "template" / "utils"))

from json_parser import extract_json_from_text

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


@tool("scrape_pga", "Scrape PGA directory page with Firecrawl", {"url": str})
async def scrape_pga(args: dict[str, Any]) -> dict[str, Any]:
    """
    Custom SDK tool: Scrape PGA page via Firecrawl API

    Calls Firecrawl /v1/scrape endpoint directly (no hosted MCP needed)
    Handles JavaScript rendering and cookie walls
    """
    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={
                "url": args["url"],
                "formats": ["markdown"]
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        if response.status_code != 200:
            error_text = response.text
            raise ValueError(f"Firecrawl API error {response.status_code}: {error_text}")

        data = response.json()
        markdown = data.get("data", {}).get("markdown", "")

        print(f"   ✓ Scraped {len(markdown)} chars from Firecrawl")

        return {"content": [{"type": "text", "text": markdown}]}


async def extract_contact_data(url: str) -> Dict[str, Any]:
    """
    Extract contact data from a golf course URL

    Supports both static HTML (VSGA) and JavaScript SPAs (PGA directory).
    For PGA URLs, uses Firecrawl hosted MCP to handle dynamic content.

    Args:
        url: Golf course listing URL

    Returns:
        Dict with: course_name, website, phone, staff[]
    """

    # Load env for API keys
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    # Detect PGA directory URLs (JavaScript SPA - needs Firecrawl)
    is_pga_url = "directory.pga.org" in url

    # Choose appropriate tool and MCP config based on URL type
    if is_pga_url:
        # Create custom SDK server with Firecrawl tool (pattern from Agent 3)
        firecrawl_server = create_sdk_mcp_server("fc", tools=[scrape_pga])

        allowed_tools = ["mcp__fc__scrape_pga"]
        mcp_servers = {"fc": firecrawl_server}
        disallowed_tools = ["Task", "TodoWrite", "Bash", "Grep", "Glob", "WebSearch", "WebFetch"]
        system_prompt = (
            "Use mcp__fc__scrape_pga to scrape the PGA directory page. "
            "The page shows 'PGA Professionals' section with staff cards. "
            "Each card has: membership badge (PGA MEMBER or ASSOCIATE), name, title, city. "
            "Also extract: course name, website, phone from top of page. "
            "Return as JSON in this EXACT format:\n"
            "{\n"
            '  "course_name": "...",\n'
            '  "website": "...",\n'
            '  "phone": "...",\n'
            '  "staff": [\n'
            '    {"name": "Philip J Shepherd", "title": "General Manager", "pga_membership": "PGA MEMBER"},\n'
            '    {"name": "Wrenn M Johnson", "title": "Assistant Professional", "pga_membership": "ASSOCIATE"}\n'
            '  ]\n'
            "}"
        )
    else:
        # VSGA and other static HTML sites
        allowed_tools = ["WebFetch"]
        mcp_servers = None
        disallowed_tools = ["Task", "TodoWrite"]
        system_prompt = (
            "Use WebFetch to get the page content. "
            "Extract: course name, website, phone, and all staff members (name + title). "
            "Return as JSON in this exact format:\n"
            "{\n"
            '  "course_name": "...",\n'
            '  "website": "...",\n'
            '  "phone": "...",\n'
            '  "staff": [{"name": "...", "title": "..."}]\n'
            "}"
        )

    options = ClaudeAgentOptions(
        mcp_servers=mcp_servers,
        allowed_tools=allowed_tools,
        disallowed_tools=disallowed_tools,
        permission_mode="bypassPermissions",
        max_turns=4,
        model="claude-haiku-4-5",
        system_prompt=system_prompt,
    )

    extracted_data = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Extract contact data from: {url}")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        # Use utility function for robust JSON extraction
                        extracted_data = extract_json_from_text(block.text, required_field="course_name")

                        if not extracted_data:
                            print(f"   ⚠️ No valid JSON found, response: {block.text[:200]}...")

            if isinstance(msg, ResultMessage):
                result_message = msg

    if not extracted_data:
        raise ValueError("Failed to extract data from URL")

    # Return data with metadata
    return {
        "url": url,
        "data": extracted_data,
        "cost": result_message.total_cost_usd if result_message else None,
        "turns": result_message.num_turns if result_message else None,
    }


async def main():
    """Demo: Extract from one URL"""
    print("🔍 Agent 2: Data Extractor")
    print("=" * 70)

    # Example URL
    test_url = "https://vsga.org/courselisting/11950?hsLang=en"

    print(f"Extracting from: {test_url}\n")

    result = await extract_contact_data(test_url)

    print(f"\n📊 Results:")
    print(f"   Course: {result['data'].get('course_name', 'N/A')}")
    print(f"   Website: {result['data'].get('website', 'N/A')}")
    print(f"   Phone: {result['data'].get('phone', 'N/A')}")
    print(f"   Staff: {len(result['data'].get('staff', []))} members")

    for staff in result['data'].get('staff', []):
        print(f"      - {staff.get('name')}: {staff.get('title')}")

    print(f"\n   Cost: ${result['cost']:.4f}")
    print(f"   Turns: {result['turns']}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
