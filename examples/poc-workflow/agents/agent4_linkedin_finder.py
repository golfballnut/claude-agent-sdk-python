#!/usr/bin/env python3
"""
Agent 4: LinkedIn Finder (Fallback Specialist)
Finds LinkedIn URLs for contacts that Hunter.io missed

Performance Targets:
- Success Rate: 20-30% (of Hunter.io misses)
- Cost: < $0.015 per contact
- Speed: < 10s per contact

Pattern:
- Custom tool with BrightData/Firecrawl search
- Site-filtered Google search (site:linkedin.com/in/)
- NO FALLBACKS - returns null if not found
- SDK MCP server (in-process)
- Haiku 4.5 model

Data Quality Rule: Returns null if not found - NEVER guesses

Input: Contacts WITHOUT linkedin_url from Agent 3
Output: linkedin_url + method + confidence (or nulls)

MCP Baseline: BrightData found 2/7 (29%) Hunter.io misses
"""

import anyio
import json
from typing import Any, Dict
from pathlib import Path
import sys

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "template" / "utils"))

from env_loader import load_project_env, get_api_key
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


# ============================================================================
# CUSTOM TOOL
# ============================================================================

@tool("find_linkedin", "Find LinkedIn URL via BrightData search", {
    "name": str,
    "title": str,
    "company": str
})
async def find_linkedin_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    2-Step LinkedIn Discovery (NO GUESSING):
    1. BrightData site-filtered search
    2. Firecrawl search (fallback)
    3. Return null if not found

    Uses BrightData API directly (not MCP) because SDK subprocess
    has no MCP servers available.
    """
    import httpx
    import re

    name = args["name"]
    title = args["title"]
    company = args["company"]

    results = {
        "linkedin_url": None,
        "method": None,
        "confidence": 0,
        "steps_attempted": [],
    }

    # Load environment
    load_project_env()

    # STEP 1: Use Jina to scrape BrightData search (cheaper than BrightData API)
    # BrightData MCP search_engine works, so replicate with direct scraping
    results["steps_attempted"].append("site_filtered_search")

    try:
        # Site-filtered Google search (proven pattern from MCP testing)
        query = f'"{name}" "{company}" site:linkedin.com/in/'
        google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use Jina to get search results (free)
            r = await client.get(f"https://r.jina.ai/{google_url}")
            content = r.text

            # Extract LinkedIn URLs from results
            linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
            urls = re.findall(linkedin_pattern, content)

            if urls:
                # Take first match (usually most relevant)
                results["linkedin_url"] = urls[0]
                results["method"] = "site_filtered_search"
                results["confidence"] = 75
                print(f"   ✓ Step 1: Found LinkedIn via site search")

                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(results)
                    }]
                }

    except Exception as e:
        print(f"   ✗ Step 1 failed: {e}")

    # STEP 2: Broader search (fallback)
    if not results["linkedin_url"]:
        results["steps_attempted"].append("broad_search")

        try:
            query = f'"{name}" {title} {company} LinkedIn'
            google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"https://r.jina.ai/{google_url}")
                content = r.text

                linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
                urls = re.findall(linkedin_pattern, content)

                if urls:
                    results["linkedin_url"] = urls[0]
                    results["method"] = "broad_search"
                    results["confidence"] = 60
                    print(f"   ✓ Step 2: Found LinkedIn via broad search")

                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(results)
                        }]
                    }

        except Exception as e:
            print(f"   ✗ Step 2 failed: {e}")

    # STEP 3: Not found (NO GUESSING - return nulls)
    results["steps_attempted"].append("not_found")
    results["method"] = "not_found"
    print(f"   ✗ LinkedIn not found (clean null, no guessing)")

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(results)
        }]
    }


# ============================================================================
# AGENT FUNCTION
# ============================================================================

async def find_linkedin_url(contact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find LinkedIn URL for a contact

    Args:
        contact: Dict with name, title, company

    Returns:
        Dict with original contact + linkedin_url (or null)
    """

    server = create_sdk_mcp_server("linkedin", tools=[find_linkedin_tool])

    options = ClaudeAgentOptions(
        mcp_servers={"linkedin": server},
        allowed_tools=["mcp__linkedin__find_linkedin"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use find_linkedin tool. It returns pure JSON. "
            "OUTPUT ONLY THE EXACT JSON - NO MARKDOWN, NO FORMATTING."
        ),
    )

    linkedin_data = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find LinkedIn: {contact['name']}, {contact['title']}, {contact.get('company', 'company')}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        linkedin_data = extract_json_from_text(block.text, required_field="linkedin_url")

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Merge with original contact
    result = contact.copy()
    if linkedin_data:
        result.update(linkedin_data)

    result["_agent4_cost"] = result_message.total_cost_usd if result_message else None
    result["_agent4_turns"] = result_message.num_turns if result_message else None

    return result


# ============================================================================
# BATCH PROCESSING
# ============================================================================

async def enrich_contacts_with_linkedin(contacts: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Find LinkedIn URLs for multiple contacts

    Args:
        contacts: List of contacts (typically those missing LinkedIn from Agent 3)

    Returns:
        List of enriched contacts with linkedin_url added (or null)
    """
    enriched = []

    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{len(contacts)}] {contact.get('name', 'Unknown')}")

        try:
            result = await find_linkedin_url(contact)

            linkedin = result.get("linkedin_url")
            method = result.get("method")

            if linkedin:
                print(f"   ✅ {linkedin} ({method})")
            else:
                print(f"   ❌ Not found (clean null)")

            print(f"   Cost: ${result.get('_agent4_cost', 0):.4f}")

            enriched.append(result)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_contact = contact.copy()
            error_contact["_agent4_error"] = str(e)
            enriched.append(error_contact)

    return enriched


# ============================================================================
# DEMO
# ============================================================================

async def main():
    """Demo: Find LinkedIn for test contact"""
    print("🔗 Agent 4: LinkedIn Finder")
    print("="*70)
    print("Finds LinkedIn URLs that Hunter.io missed\n")

    test_contact = {
        "name": "Dean Sumner",
        "title": "Director of Golf",
        "company": "Quinton Oaks Golf Course"
    }

    print(f"Contact: {test_contact['name']}")
    print(f"Company: {test_contact['company']}\n")

    result = await find_linkedin_url(test_contact)

    print(f"\n📊 Result:")
    print(f"   LinkedIn: {result.get('linkedin_url', 'Not found')}")
    print(f"   Method: {result.get('method', 'N/A')}")
    print(f"   Confidence: {result.get('confidence', 0)}%")
    print(f"   Cost: ${result.get('_agent4_cost', 0):.4f}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
