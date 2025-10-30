#!/usr/bin/env python3
"""
Agent 2.1: LinkedIn Company Staff Finder

Purpose: Find golf course staff contacts via LinkedIn company pages when PGA.org has <2 contacts

Method:
1. Search for company LinkedIn page
2. Scrape employee section
3. Filter for relevant titles (GM, Director, Manager, Professional)
4. Return list of contacts with names + titles

Pattern: Based on Agent 4 (LinkedIn individual) but searches for company pages instead

Cost: ~$0.01 per course (BrightData search + scrape)
Success Rate: 33% (only works when company page exists)

Test Results (Oct 28, 2025):
- Alamance CC: ✅ Found 4 (Charlie Nolette - GM/COO, + 3 others)
- Mountain Aire: ❌ No company page (found individual profiles)
- Pine Ridge Classic: ❌ No LinkedIn presence

This is Fallback #1 in the cascade:
  Agent 2 (PGA.org) → <2 contacts?
    → Agent 2.1 (LinkedIn) → <2 contacts?
      → Agent 2.2 (Perplexity) → <1 contact?
        → Error
"""

import anyio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)


async def find_linkedin_company_staff(
    course_name: str,
    state_code: str
) -> List[Dict[str, Any]]:
    """
    Find staff contacts via LinkedIn company page

    Args:
        course_name: Name of golf course (e.g., "Alamance Country Club")
        state_code: Two-letter state code (e.g., "NC")

    Returns:
        List of dicts: [
            {"name": "Charlie Nolette", "title": "General Manager/COO", "linkedin_url": "..."},
            {"name": "Drake Woodside", "title": "Director of Golf", "linkedin_url": "..."}
        ]
        Returns empty list if no company page found

    Cost: ~$0.01 per call (BrightData search + scrape)
    """

    print(f"   🔗 Agent 2.1: Searching LinkedIn for {course_name}...")

    # Load environment
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    # Check for BrightData token
    brightdata_token = os.getenv('BRIGHTDATA_API_TOKEN', '')
    if not brightdata_token:
        print(f"      ❌ BRIGHTDATA_API_TOKEN not set - Agent 2.1 disabled")
        return []

    # Step 1: Search for company LinkedIn page
    state_name = _state_name(state_code)
    search_query = f"{course_name} golf {state_name} LinkedIn company"

    try:
        # Configure BrightData hosted MCP (same as Agent 4)
        brightdata_hosted_mcp = {
            "type": "http",
            "url": f"https://mcp.brightdata.com/mcp?token={brightdata_token}"
        }

        # Single SDK session with comprehensive system prompt (Agent 4 pattern)
        options = ClaudeAgentOptions(
            mcp_servers={"brightdata": brightdata_hosted_mcp},
            allowed_tools=[
                "mcp__brightdata__search_engine",
                "mcp__brightdata__scrape_as_markdown"
            ],
            disallowed_tools=["Task", "TodoWrite", "Bash", "Grep", "Glob", "WebSearch", "WebFetch"],
            permission_mode="bypassPermissions",
            max_turns=8,  # Need more turns for search + scrape + parse
            model="claude-haiku-4-5",
            system_prompt=(
                f"Find LinkedIn staff for {course_name} in {state_name}.\n\n"
                f"Steps:\n"
                f"1. search_engine: query='{search_query}'\n"
                f"2. Extract LinkedIn company URL (linkedin.com/company/SLUG)\n"
                f"3. scrape_as_markdown: url=<company URL>\n"
                f"4. Parse employees from markdown\n"
                f"5. Filter for: General Manager, Director of Golf, Head Professional, President, COO\n"
                f"6. Output ONLY this JSON array:\n"
                f'[{{"name":"John Doe","title":"General Manager","linkedin_url":"https://..."}}]\n\n'
                f"CRITICAL: Output ONLY the JSON array. NO extra text!"
            ),
        )

        print(f"   🔍 Searching LinkedIn for: {search_query}")

        staff = []
        async with ClaudeSDKClient(options=options) as client:
            await client.query(
                f"Find LinkedIn company staff for {course_name}. Output ONLY JSON array, no other text."
            )

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if hasattr(block, 'name'):  # ToolUseBlock
                            print(f"   🔧 Tool: {block.name}")
                        elif isinstance(block, TextBlock):
                            # Parse final JSON array output
                            json_match = re.search(r'\[\s*\{.*?"name".*?\}\s*\]', block.text, re.DOTALL)
                            if json_match:
                                try:
                                    staff = json.loads(json_match.group(0))
                                    print(f"   ✅ Parsed {len(staff)} contacts from LinkedIn")
                                except json.JSONDecodeError as e:
                                    print(f"   ⚠️  JSON parse error: {e}")

    except Exception as e:
        print(f"   ⚠️  LinkedIn search error: {e}")
        return []

    # Claude already filtered in system prompt, so just return
    print(f"   ✅ Found {len(staff)} relevant staff via LinkedIn")
    return staff


def _state_name(state_code: str) -> str:
    """Convert state code to full name"""
    states = {
        "NC": "North Carolina",
        "SC": "South Carolina",
        "VA": "Virginia"
    }
    return states.get(state_code, state_code)


def _extract_company_url(search_results: Dict[str, Any]) -> Optional[str]:
    """
    Extract LinkedIn company page URL from BrightData search results

    Looks for: linkedin.com/company/{slug}
    """
    if not search_results or 'organic' not in search_results:
        return None

    for result in search_results.get('organic', []):
        url = result.get('link', '')
        # Look for company pages (not individual profiles)
        if 'linkedin.com/company/' in url:
            # Clean URL (remove query params)
            clean_url = url.split('?')[0]
            return clean_url

    return None


def _parse_linkedin_employees(markdown: str, company_url: str) -> List[Dict[str, Any]]:
    """
    Parse LinkedIn company page markdown for employee names and titles

    Expected markdown structure from BrightData scraper:
    ### Employee Name
    #### Title at Company

    Also handles:
    - Links: [### Name](profile_url)
    - Combined: ### Name, Credentials \n #### Title

    Returns:
        [{name: "...", title: "...", linkedin_url: "..."}]
    """
    staff = []

    if not markdown:
        return staff

    # Pattern 1: ### Name followed by #### Title
    # Example:
    # ### Charlie Nolette, CCM
    # #### General Manager/COO
    lines = markdown.split('\n')

    for i, line in enumerate(lines):
        # Look for h3 heading (employee name)
        if line.strip().startswith('###') and not line.strip().startswith('####'):
            # Extract name
            name_text = line.replace('###', '').strip()

            # Remove markdown link syntax: [Name](url) -> Name
            name_match = re.search(r'\[([^\]]+)\]', name_text)
            if name_match:
                name = name_match.group(1)
                # Extract profile URL
                url_match = re.search(r'\(([^)]+)\)', name_text)
                profile_url = url_match.group(1) if url_match else ""
            else:
                name = name_text
                profile_url = ""

            # Remove credentials (CCM, PGA, etc.)
            name = re.sub(r',?\s*(CCM|PGA|MBA|CPA).*$', '', name).strip()

            # Look for title in next line (should be ####)
            title = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('####'):
                    title = next_line.replace('####', '').strip()

            # Only add if we found both name and title
            if name and title:
                staff.append({
                    "name": name,
                    "title": title,
                    "linkedin_url": profile_url if profile_url else company_url
                })

    return staff


# Test function
async def main():
    """Test LinkedIn company search"""
    print("🔍 Test Agent 2.1: LinkedIn Company Staff Finder")
    print("=" * 70)

    test_cases = [
        {"name": "Alamance Country Club", "state": "NC"},
        {"name": "Chantilly National Golf and Country Club", "state": "VA"},
        {"name": "Mountain Aire Golf Club", "state": "NC"}
    ]

    for test in test_cases:
        print(f"\n{'='*70}")
        print(f"Testing: {test['name']}")
        print(f"{'='*70}")

        staff = await find_linkedin_company_staff(test['name'], test['state'])

        if staff:
            print(f"✅ SUCCESS - Found {len(staff)} staff:")
            for s in staff:
                print(f"   - {s['name']}: {s['title']}")
        else:
            print("❌ FAILED - No company page found")


if __name__ == "__main__":
    anyio.run(main)
