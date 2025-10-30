#!/usr/bin/env python3
"""
Test Agent 2 with Firecrawl Custom SDK Tool

Purpose: Validate Firecrawl can extract PGA directory data before deploying to production

Pattern: Custom SDK tool (like Agent 3 uses for Hunter.io)
- Direct API call to Firecrawl
- No hosted HTTP MCP needed
- Works in Docker/Render with just API key

Test Cases:
1. Course 1036 - Pine Ridge Classic (NC)
2. Course 1037 - Mountain Aire (NC)
3. Course 1039 - Alamance CC (NC)

Success Criteria:
- Extract course name, website, phone
- Extract 2+ staff with names, titles, PGA membership types
- Valid JSON output
- Cost < $0.02 per page
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
)


@tool("scrape_pga", "Scrape PGA directory page with Firecrawl", {"url": str})
async def scrape_pga(args: dict[str, Any]) -> dict[str, Any]:
    """
    Custom SDK tool: Scrape PGA page via Firecrawl API

    Calls Firecrawl /v1/scrape endpoint directly (no MCP server needed)
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


async def extract_pga_contacts(url: str) -> Dict[str, Any]:
    """
    Test extraction from PGA URL using custom Firecrawl SDK tool
    """
    # Load env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    # Create custom SDK server with Firecrawl tool
    firecrawl_server = create_sdk_mcp_server("fc", tools=[scrape_pga])

    options = ClaudeAgentOptions(
        mcp_servers={"fc": firecrawl_server},
        allowed_tools=["mcp__fc__scrape_pga"],
        disallowed_tools=["Task", "TodoWrite", "Bash", "Grep", "Glob", "WebSearch", "WebFetch"],
        permission_mode="bypassPermissions",
        max_turns=4,
        model="claude-haiku-4-5",
        system_prompt=(
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
        ),
    )

    extracted_data = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Extract contact data from: {url}")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        extracted_data = extract_json_from_text(block.text, required_field="course_name")

                        if not extracted_data:
                            print(f"   ⚠️ No valid JSON found, response: {block.text[:200]}...")

            if isinstance(msg, ResultMessage):
                result_message = msg

    if not extracted_data:
        raise ValueError("Failed to extract data from URL")

    return {
        "url": url,
        "data": extracted_data,
        "cost": result_message.total_cost_usd if result_message else None,
        "turns": result_message.num_turns if result_message else None,
    }


async def main():
    """Test Firecrawl extraction on multiple PGA URLs"""
    print("🔍 Test Agent 2: Firecrawl Custom SDK Tool")
    print("=" * 70)

    test_cases = [
        {
            "id": 1036,
            "name": "Pine Ridge Classic",
            "url": "https://directory.pga.org/facility/detail/996163459"
        },
        {
            "id": 1037,
            "name": "Mountain Aire",
            "url": "https://directory.pga.org/facility/detail/988857706"
        },
        {
            "id": 1039,
            "name": "Alamance CC",
            "url": "https://directory.pga.org/facility/detail/750795095"
        }
    ]

    results = []
    total_cost = 0.0

    for test in test_cases:
        print(f"\n{'='*70}")
        print(f"Testing Course {test['id']}: {test['name']}")
        print(f"{'='*70}")
        print(f"URL: {test['url']}\n")

        try:
            result = await extract_pga_contacts(test['url'])

            data = result['data']
            print(f"\n✅ SUCCESS!")
            print(f"   Course: {data.get('course_name', 'N/A')}")
            print(f"   Website: {data.get('website', 'N/A')}")
            print(f"   Phone: {data.get('phone', 'N/A')}")
            print(f"   Staff: {len(data.get('staff', []))} members")

            for staff in data.get('staff', []):
                membership = staff.get('pga_membership', 'N/A')
                print(f"      - {staff.get('name')}: {staff.get('title')} ({membership})")

            print(f"\n   💰 Cost: ${result['cost']:.4f}")
            print(f"   ⏱️  Turns: {result['turns']}")

            total_cost += result['cost']
            results.append({"test": test['name'], "success": True, "staff_count": len(data.get('staff', []))})

        except Exception as e:
            print(f"\n❌ FAILED: {e}")
            results.append({"test": test['name'], "success": False, "error": str(e)})

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    success_count = sum(1 for r in results if r['success'])
    print(f"Success Rate: {success_count}/{len(test_cases)}")
    print(f"Total Cost: ${total_cost:.4f} (avg: ${total_cost/len(test_cases):.4f} per course)")

    for result in results:
        status = "✅" if result['success'] else "❌"
        details = f"{result.get('staff_count', 0)} staff" if result['success'] else result.get('error', '')
        print(f"  {status} {result['test']}: {details}")

    if success_count == len(test_cases):
        print(f"\n🎉 All tests passed! Ready to deploy to production.")
    else:
        print(f"\n⚠️  {len(test_cases) - success_count} tests failed. Fix before deploying.")


if __name__ == "__main__":
    anyio.run(main)
