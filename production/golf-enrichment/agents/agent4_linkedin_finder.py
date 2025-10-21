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

    # Check for BrightData token (required for hosted MCP)
    brightdata_token = os.getenv('BRIGHTDATA_API_TOKEN', '')
    if not brightdata_token:
        print(f"      ❌ BRIGHTDATA_API_TOKEN not set - Agent 4 disabled")
        return {
            "linkedin_url": None,
            "tenure_years": None,
            "start_date": None,
            "linkedin_method": "error",
            "linkedin_confidence": "low",
            "_agent4_cost": 0.0,
            "_agent4_turns": 0,
            "_agent4_duration_ms": 0,
            "_agent4_error": "BRIGHTDATA_API_TOKEN environment variable not set"
        }

    # Configure ONLY hosted HTTP MCP (proven working!)
    brightdata_hosted_mcp = {
        "type": "http",
        "url": f"https://mcp.brightdata.com/mcp?token={brightdata_token}"
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
            f"Extract comprehensive LinkedIn data for {name}, {title} at {company}.\n\n"
            f"1. search_engine: query='{name} {title} {company} LinkedIn'\n"
            "2. Get LinkedIn URL from results\n"
            "3. scrape_as_markdown: url=<LinkedIn URL>\n"
            "4. From profile extract:\n"
            "   - Tenure: 'Apr 2025-Present·7mo' → 0.6 years\n"
            "   - Full title: 'General Manager / COO'\n"
            "   - Company: 'Invited'\n"
            "   - Previous golf/hospitality roles (company names)\n"
            "   - Total industry years (sum all golf/hospitality experience)\n"
            "   - Education: degrees & schools\n"
            "   - Certifications: PGA, MBA, etc.\n"
            "5. Output ONLY this JSON (no markdown, no text, just the JSON):\n"
            '{"url":"https://linkedin.com/in/...","tenure":0.6,"start":"Apr 2025",'
            '"title":"Full Title","company":"Company Name","previous_clubs":["Club1"],'
            '"industry_years":25,"education":["Degree-School"],"certs":["PGA"]}\n\n'
            "CRITICAL: Output ONLY the JSON object above. NO extra text!"
        ),
    )

    # Initialize all result fields
    linkedin_url = None
    tenure_years = None
    start_date = None
    full_title = None
    company_name = None
    previous_golf_roles = []
    industry_experience_years = None
    education = []
    certifications = []
    linkedin_method = "hosted_mcp"

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find and extract comprehensive LinkedIn data for {name}. Output ONLY JSON, no other text."
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
                                data = json.loads(json_match.group(0))

                                # Core fields
                                linkedin_url = data.get("url")
                                tenure_years = data.get("tenure") or data.get("tenure_years")
                                start_date = data.get("start") or data.get("start_date")

                                # NEW: Comprehensive fields
                                full_title = data.get("title") or data.get("full_title")
                                company_name = data.get("company")
                                previous_golf_roles = data.get("previous_clubs") or data.get("previous_golf_roles") or []
                                industry_experience_years = data.get("industry_years") or data.get("industry_experience_years")
                                education = data.get("education") or []
                                certifications = data.get("certs") or data.get("certifications") or []

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
                    # Core fields
                    "linkedin_url": linkedin_url,
                    "tenure_years": tenure_years,
                    "start_date": start_date,

                    # NEW: Comprehensive career data
                    "linkedin_full_title": full_title,
                    "linkedin_company": company_name,
                    "previous_golf_roles": previous_golf_roles,
                    "industry_experience_years": industry_experience_years,
                    "education": education,
                    "certifications": certifications,

                    # Metadata
                    "linkedin_method": linkedin_method,
                    "linkedin_confidence": "high" if linkedin_url else "low",
                    "_agent4_cost": msg.total_cost_usd or 0.0,
                    "_agent4_turns": msg.num_turns,
                    "_agent4_duration_ms": msg.duration_ms
                }

    # No result message (shouldn't happen)
    return {
        "linkedin_url": None,
        "tenure_years": None,
        "start_date": None,
        "linkedin_full_title": None,
        "linkedin_company": None,
        "previous_golf_roles": [],
        "industry_experience_years": None,
        "education": [],
        "certifications": [],
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
        "name": "John Stutz",
        "title": "General Manager",
        "company": "Chantilly National Golf and Country Club"
    }

    print(f"Contact: {test_contact['name']}")
    print(f"Title: {test_contact['title']}")
    print(f"Company: {test_contact['company']}\n")

    result = await find_linkedin(test_contact, "Chantilly National Golf and Country Club", "VA")

    print(f"\n📊 Core Results:")
    print(f"   LinkedIn: {result.get('linkedin_url', 'Not found')}")
    print(f"   Tenure: {result.get('tenure_years', 'N/A')} years")
    print(f"   Start: {result.get('start_date', 'N/A')}")

    print(f"\n📋 Career Context:")
    print(f"   Full Title: {result.get('linkedin_full_title', 'N/A')}")
    print(f"   Company: {result.get('linkedin_company', 'N/A')}")
    print(f"   Previous Clubs: {result.get('previous_golf_roles', [])}")
    print(f"   Industry Exp: {result.get('industry_experience_years', 'N/A')} years")

    print(f"\n🎓 Qualifications:")
    print(f"   Education: {result.get('education', [])}")
    print(f"   Certifications: {result.get('certifications', [])}")

    print(f"\n💰 Performance:")
    print(f"   Cost: ${result.get('_agent4_cost', 0):.4f}")
    print(f"   Turns: {result.get('_agent4_turns', 0)}")

    if result.get('linkedin_url'):
        fields_extracted = sum([
            bool(result.get('tenure_years')),
            bool(result.get('linkedin_full_title')),
            bool(result.get('linkedin_company')),
            bool(result.get('industry_experience_years')),
            bool(result.get('education')),
            bool(result.get('certifications'))
        ])
        print(f"\n✅ LinkedIn found! Extracted {fields_extracted}/6 additional fields")
    else:
        print(f"\n❌ LinkedIn not found")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
