#!/usr/bin/env python3
"""
Agent 4: LinkedIn & Tenure Enricher (Hosted MCP Solution)

Uses BrightData Hosted HTTP MCP for LinkedIn enrichment:
1. search_engine - Find LinkedIn URL
2. scrape_as_markdown - Extract tenure from profile

Performance Target:
- LinkedIn Success: 70-100%
- Tenure Success: 80-100% (when LinkedIn found)
- Cost: ~$0.006 per contact
- Speed: 5-10s per contact

Proven Solution (Oct 21): Hosted HTTP MCP works, custom SDK tools don't!
"""

import anyio
import json
import re
import os
from typing import Any, Dict
from pathlib import Path
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


async def find_linkedin(contact: Dict[str, Any], company: str, state_code: str) -> Dict[str, Any]:
    """
    Find LinkedIn URL AND extract tenure using BrightData Hosted MCP

    Strategy:
    - Use hosted MCP search_engine to find LinkedIn URL
    - Use hosted MCP scrape_as_markdown to extract tenure from profile
    - No custom SDK tools (they conflict with hosted MCP!)

    Args:
        contact: Dict with name, title
        company: Company/course name
        state_code: State code

    Returns:
        Dict with linkedin_url, tenure_years, start_date, cost, etc.
    """
    # Load env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    name = contact.get("name", "")
    title = contact.get("title", "")

    # Configure ONLY hosted HTTP MCP (proven working!)
    brightdata_hosted_mcp = {
        "type": "http",
        "url": f"https://mcp.brightdata.com/mcp?token={os.getenv('BRIGHTDATA_API_TOKEN', '')}"
    }

    options = ClaudeAgentOptions(
        mcp_servers={"brightdata": brightdata_hosted_mcp},  # ONLY hosted MCP
        allowed_tools=[
            "mcp__brightdata__search_engine",      # Find URL
            "mcp__brightdata__scrape_as_markdown"  # Extract tenure
        ],
        disallowed_tools=["Task", "TodoWrite", "Bash", "Grep", "Glob", "WebSearch", "WebFetch"],
        permission_mode="bypassPermissions",
        max_turns=6,
        model="claude-haiku-4-5",
        system_prompt=(
            f"Task: Find LinkedIn and tenure for {name}, {title} at {company}.\n\n"
            f"Step 1: search_engine tool with query='{name} {title} {company} LinkedIn'\n"
            "Step 2: Find LinkedIn URL in results (linkedin.com/in/...)\n"
            "Step 3: scrape_as_markdown tool with url=<that LinkedIn URL>\n"
            "Step 4: Extract tenure: 'MMM YYYY - Present · X months/years'\n"
            "Step 5: Calculate years (7 months=0.6, 2yr 8mo=2.7)\n"
            f"Step 6: Output JSON: {{\"url\":\"...\",\"tenure\":<number>,\"start\":\"MMM YYYY\"}}\n"
            "USE BOTH TOOLS!"
        ),
    )

    linkedin_url = None
    tenure_years = None
    start_date = None
    linkedin_method = "hosted_mcp"

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find LinkedIn URL and tenure for {name}, {title} at {company}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if hasattr(block, 'name'):  # ToolUseBlock
                        print(f"   🔧 Tool: {block.name}")
                    elif isinstance(block, TextBlock):
                        print(f"   💬 {block.text[:200]}...")
                        # Parse final JSON output
                        json_match = re.search(r'\{.*"url".*\}', block.text, re.DOTALL)
                        if json_match:
                            try:
                                response_data = json.loads(json_match.group(0))
                                linkedin_url = response_data.get("url")
                                tenure_years = response_data.get("tenure")
                                start_date = response_data.get("start")

                                if linkedin_url and linkedin_url != "null":
                                    linkedin_method = "brightdata_hosted_mcp"
                            except json.JSONDecodeError:
                                # Fallback: extract URL via regex
                                urls = re.findall(
                                    r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?',
                                    block.text
                                )
                                if urls:
                                    linkedin_url = urls[0].rstrip('/')

            if isinstance(msg, ResultMessage):
                return {
                    "linkedin_url": linkedin_url,
                    "tenure_years": tenure_years,
                    "start_date": start_date,
                    "linkedin_method": linkedin_method,
                    "linkedin_confidence": "high" if linkedin_url else "low",
                    "_agent4_cost": msg.total_cost_usd or 0.0,
                    "_agent4_turns": msg.num_turns,
                    "_agent4_duration_ms": msg.duration_ms
                }

    # No result message
    return {
        "linkedin_url": None,
        "tenure_years": None,
        "start_date": None,
        "linkedin_method": "not_found",
        "linkedin_confidence": "low",
        "_agent4_cost": 0.0,
        "_agent4_turns": 0,
        "_agent4_duration_ms": 0
    }


async def main():
    """Test with John Stutz (Course 133 - needs scraping)"""
    print("🔍 Agent 4: LinkedIn & Tenure Enricher (Hosted MCP)")
    print("="*70)

    test_contact = {
        "name": "Dustin Betthauser",
        "title": "General Manager",
        "company": "Brambleton Golf Course"
    }

    print(f"Contact: {test_contact['name']}")
    print(f"Title: {test_contact['title']}")
    print(f"Company: {test_contact['company']}\n")

    result = await find_linkedin(test_contact, "Brambleton Golf Course", "VA")

    print(f"\n📊 Result:")
    print(f"   LinkedIn: {result.get('linkedin_url', 'Not found')}")
    print(f"   Tenure: {result.get('tenure_years', 'Not found')} years")
    print(f"   Start: {result.get('start_date', 'N/A')}")
    print(f"   Method: {result.get('linkedin_method')}")
    print(f"   Cost: ${result.get('_agent4_cost', 0):.4f}")
    print(f"   Turns: {result.get('_agent4_turns', 0)}")

    if result.get('linkedin_url') and result.get('tenure_years'):
        print(f"\n✅✅✅ SUCCESS! LinkedIn + Tenure found!")
        print(f"   Hosted MCP solution works perfectly!")
    elif result.get('linkedin_url'):
        print(f"\n⚠️  LinkedIn found but no tenure")
    else:
        print(f"\n❌ LinkedIn not found")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
