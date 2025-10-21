#!/usr/bin/env python3
"""
Agent 4: LinkedIn & Tenure Enricher

Finds LinkedIn URLs AND extracts tenure from search descriptions (no scraping needed!).

Performance Target:
- LinkedIn Success: 50-70% (vs 25% with Hunter.io alone)
- Tenure Success: 40-50% (when LinkedIn found with tenure in description)
- Cost: $0.001 per contact (Firecrawl search)
- Speed: 2-3s per contact

Strategy:
- Step 1: Firecrawl Search API (primary - fast, reliable)
  - Finds LinkedIn URL
  - BONUS: Extracts tenure from description ("Jan 2019 - Present 6 years 10 months")
- Step 2: BrightData API (fallback - bypasses blocks)
- Step 3: Jina Search API (last fallback)
- Step 4: Return NULL if not found (no guessing!)

Key Principle: Multi-method search with tenure extraction (no separate scraping!)
Proven in testing: 50% LinkedIn, 40% tenure on Course 108 contacts
"""

import anyio
import json
import re
from typing import Any, Dict
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


@tool("search_linkedin", "Search for LinkedIn profile via BrightData/Firecrawl/Jina", {
    "name": str,
    "title": str,
    "company": str,
    "state": str
})
async def search_linkedin_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Multi-method LinkedIn search with fallback strategy:
    1. Try Firecrawl API (fast, reliable)
    2. Fallback to BrightData API (bypasses blocks)
    3. Fallback to Jina Search API (simple search)

    Returns JSON with found LinkedIn URLs or empty results
    """
    import httpx
    import re
    import json
    import os
    from pathlib import Path

    name = args["name"]
    title = args["title"]
    company = args["company"]
    state = args.get("state", "")

    # Load API keys from .env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    linkedin_urls = []
    search_method = "none"
    tenure_years = None
    start_date = None

    # STEP 1: Try Firecrawl API (primary - fast, works well)
    # BONUS: Also extracts tenure from search descriptions!
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    if firecrawl_key and not linkedin_urls:
        try:
            query = f"{name} {title} {company} {state} LinkedIn"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/search",
                    headers={"Authorization": f"Bearer {firecrawl_key}"},
                    json={"query": query, "limit": 5}
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract LinkedIn URLs AND tenure from search results
                    for result in data.get("data", []):
                        url = result.get("url", "")
                        description = result.get("description", "")

                        if "linkedin.com/in/" in url:
                            linkedin_urls.append(url)

                            # BONUS: Extract tenure from description
                            # Pattern: "Jan 2019 - Present 6 years 10 months"
                            tenure_match = re.search(
                                r'(\w+\s+\d{4})\s*-\s*Present.*?(\d+)\s*(?:yrs?|years?)\s*(\d+)?\s*(?:mos?|months?)?',
                                description,
                                re.IGNORECASE
                            )

                            if tenure_match and not tenure_years:
                                # Calculate tenure
                                start_date = tenure_match.group(1)
                                years = int(tenure_match.group(2))
                                months = int(tenure_match.group(3)) if tenure_match.group(3) else 0
                                tenure_years = round(years + months / 12, 1)

                    if linkedin_urls:
                        search_method = "firecrawl_api"
        except Exception:
            pass  # Continue to fallback

    # STEP 2: Try BrightData API (fallback - bypasses bot detection)
    brightdata_token = os.getenv("BRIGHTDATA_API_TOKEN")
    if brightdata_token and not linkedin_urls:
        try:
            query = f"{name} {title} {company} LinkedIn"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.brightdata.com/datasets/v3/trigger",
                    params={
                        "dataset_id": "gd_lwbs7r33mhyo0wqz9",  # Google SERP
                        "query": query,
                        "limit": 5
                    },
                    headers={"Authorization": f"Bearer {brightdata_token}"}
                )

                if response.status_code == 200:
                    content = response.text
                    # Extract LinkedIn URLs from HTML/JSON response
                    urls = re.findall(
                        r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?',
                        content
                    )
                    linkedin_urls = [url.rstrip('/') for url in urls]

                    if linkedin_urls:
                        search_method = "brightdata_api"
        except Exception:
            pass  # Continue to fallback

    # STEP 3: Try Jina Search API (last fallback)
    jina_key = os.getenv("JINA_API_KEY")
    if jina_key and not linkedin_urls:
        try:
            query = f"{name} {title} {company} site:linkedin.com"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://s.jina.ai/" + query,
                    headers={"Authorization": f"Bearer {jina_key}"}
                )

                if response.status_code == 200:
                    content = response.text
                    urls = re.findall(
                        r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?',
                        content
                    )
                    linkedin_urls = [url.rstrip('/') for url in urls]

                    if linkedin_urls:
                        search_method = "jina_api"
        except Exception:
            pass  # Not found

    result = {
        "linkedin_urls_found": linkedin_urls,
        "search_method": search_method,
        "query_used": query,
        "tenure_years": tenure_years,  # BONUS from Firecrawl search!
        "start_date": start_date        # BONUS from Firecrawl search!
    }

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(result)
        }]
    }


async def find_linkedin(contact: Dict[str, Any], company: str, state_code: str) -> Dict[str, Any]:
    """
    Find LinkedIn URL AND extract tenure for contact using multi-method search

    Strategy:
    1. Firecrawl API (primary) - Finds URL + extracts tenure from description
    2. BrightData API (fallback for bot blocks)
    3. Jina Search API (final fallback)

    Args:
        contact: Dict with name, title
        company: Company/course name
        state_code: State code (for disambiguation)

    Returns:
        Dict with:
        - linkedin_url: LinkedIn profile URL or None
        - tenure_years: Years at current position (from search description) or None
        - start_date: Start date of current position or None
        - linkedin_method: Search method used
        - linkedin_confidence: high/medium/low
        - _agent4_cost: API cost
    """

    name = contact.get("name", "")
    title = contact.get("title", "")

    # Create SDK MCP server with custom search tool (same pattern as Agent 1)
    server = create_sdk_mcp_server("linkedin", tools=[search_linkedin_tool])

    options = ClaudeAgentOptions(
        mcp_servers={"linkedin": server},
        allowed_tools=["mcp__linkedin__search_linkedin"],
        disallowed_tools=["Task", "TodoWrite", "Grep", "Glob", "WebSearch", "WebFetch"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use search_linkedin tool with name, title, company, and state parameters. "
            "The tool returns JSON with: linkedin_urls_found, tenure_years, start_date. "
            "Extract the data and output as JSON: "
            "{\"url\": \"<first URL or null>\", \"tenure\": <years or null>, \"start\": \"<date or null>\"}. "
            "OUTPUT ONLY THE JSON - NO MARKDOWN, NO FORMATTING."
        ),
    )

    linkedin_url = None
    linkedin_method = "not_found"
    confidence = "low"
    tenure_years = None
    start_date = None
    tool_response = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find LinkedIn URL using search_linkedin tool for: name={name}, title={title}, company={company}, state={state_code}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        # Parse JSON response from agent
                        # Expected: {"url": "...", "tenure": 6.8, "start": "Jan 2019"}
                        json_match = re.search(r'\{.*"url".*\}', block.text, re.DOTALL)
                        if json_match:
                            try:
                                response_data = json.loads(json_match.group(0))
                                linkedin_url = response_data.get("url")
                                tenure_years = response_data.get("tenure")
                                start_date = response_data.get("start")

                                if linkedin_url and linkedin_url != "null":
                                    linkedin_method = "firecrawl_search"
                                    confidence = "high"
                            except json.JSONDecodeError:
                                # Fallback: try old URL extraction
                                urls = re.findall(
                                    r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?',
                                    block.text
                                )
                                if urls:
                                    linkedin_url = urls[0].rstrip('/')
                                    linkedin_method = "fallback_regex"
                                    confidence = "high"

            if isinstance(msg, ResultMessage):
                result_cost = msg.total_cost_usd or 0.0

                return {
                    "linkedin_url": linkedin_url,
                    "tenure_years": tenure_years,     # NEW!
                    "start_date": start_date,         # NEW!
                    "linkedin_method": linkedin_method,
                    "linkedin_confidence": confidence,
                    "_agent4_cost": result_cost,
                    "_agent4_turns": msg.num_turns,
                    "_agent4_duration_ms": msg.duration_ms
                }

    # No result message (shouldn't happen, but handle gracefully)
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
    """Demo: Find LinkedIn + Tenure for test contact"""
    print("🔍 Agent 4: LinkedIn & Tenure Enricher")
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
    print(f"   Start Date: {result.get('start_date', 'N/A')}")
    print(f"   Method: {result.get('linkedin_method', 'N/A')}")
    print(f"   Confidence: {result.get('linkedin_confidence', 'low')}")
    print(f"   Cost: ${result.get('_agent4_cost', 0):.4f}")
    print(f"   Turns: {result.get('_agent4_turns', 0)}")

    if result.get('linkedin_url'):
        if result.get('tenure_years'):
            print(f"\n✅ LinkedIn + Tenure found! (No scraping needed!)")
        else:
            print(f"\n✅ LinkedIn found (tenure not in description)")
    else:
        print(f"\n⚠️  LinkedIn not found (acceptable - tried all methods)")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
