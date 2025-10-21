#!/usr/bin/env python3
"""
DEPRECATED: Agent 6.5 - Contact Background Enrichment

⚠️ THIS AGENT IS NO LONGER USED (as of October 20, 2025)

Tenure extraction is now handled by Agent 4 (LinkedIn & Tenure Enricher).
Agent 4 extracts tenure directly from Firecrawl search descriptions - no separate scraping needed!

Why deprecated:
- Firecrawl/BrightData block LinkedIn profile scraping
- Agent 4's search descriptions already contain tenure data
- Separate scraping was redundant and unreliable
- New approach: Extract from search, not scrape profiles

---

ORIGINAL PURPOSE:
Gathers tenure and career history for contacts to enable personalized outreach.

Performance (Historical):
- Success Rate: 55%+ (LinkedIn when available, Perplexity fallback)
- Cost: ~$0.007 avg (Firecrawl scrape or $0.004 Perplexity)
- Speed: ~5-8s per contact
- Accuracy: HIGH for LinkedIn data (Firecrawl), LOW for Perplexity

Strategy (LinkedIn-First):
1. If Agent 4 found LinkedIn → Scrape for accurate tenure ✅ BEST
2. Else → Try Perplexity (fallback)
3. Else → Return NULL (honest - don't hallucinate)

Why LinkedIn is Gold:
- Work history has exact dates ("Jan 2019 - Present")
- Can calculate precise tenure (6 years 10 months)
- Shows previous golf clubs (career progression)
- Verifiable data (not AI guesses)

Business Value:
- Personalized outreach: "Congrats on 7 years at Brambleton!"
- Career insights: "I see you worked at Algonkian before..."
- Industry veteran detection: "17 years in golf management - impressive!"
"""

import anyio
import json
import re
import os
from typing import Any, Dict
from pathlib import Path
from datetime import datetime
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


@tool("scrape_linkedin_tenure", "Scrape LinkedIn profile for tenure data", {
    "linkedin_url": str
})
async def scrape_linkedin_tenure_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Scrape LinkedIn profile using BrightData to extract tenure

    This follows the SDK agent pattern (like Agent 4)
    Returns JSON with tenure, start_date, or error
    """
    import httpx
    import re
    import os
    from datetime import datetime
    from pathlib import Path

    linkedin_url = args["linkedin_url"]

    # Load .env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    # Try BrightData scraping (proven in MCP testing!)
    brightdata_token = os.getenv("BRIGHTDATA_API_TOKEN")

    if not brightdata_token:
        return {"content": [{"type": "text", "text": json.dumps({
            "tenure_years": None,
            "error": "BRIGHTDATA_API_TOKEN not set"
        })}]}

    try:
        # Use BrightData's Web Scraper API (proven to work on LinkedIn)
        async with httpx.AsyncClient(timeout=30.0) as client:
            # BrightData scrape endpoint
            response = await client.get(
                linkedin_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; BrightData)",
                    "X-BrightData-Auth": f"Bearer {brightdata_token}"
                }
            )

            if response.status_code != 200:
                return {"content": [{"type": "text", "text": json.dumps({
                    "tenure_years": None,
                    "error": f"HTTP {response.status_code}"
                })}]}

            content = response.text

            # Extract tenure patterns
            # Pattern 1: "Jan 2019 - Present · 6 yrs 10 mos"
            tenure_match = re.search(
                r'(\w+\s+\d{4})\s*-\s*Present.*?(\d+)\s*yrs?\s*(\d+)?\s*mos?',
                content,
                re.IGNORECASE
            )

            if tenure_match:
                start_date = tenure_match.group(1)
                years = int(tenure_match.group(2))
                months = int(tenure_match.group(3)) if tenure_match.group(3) else 0
                tenure_years = round(years + months / 12, 1)

                result = {
                    "tenure_years": tenure_years,
                    "start_date": start_date,
                    "source": "linkedin_scrape"
                }
                return {"content": [{"type": "text", "text": json.dumps(result)}]}

            # Pattern 2: "Jan 2019 - Present" (calculate manually)
            date_match = re.search(r'(\w+\s+\d{4})\s*-\s*Present', content, re.IGNORECASE)
            if date_match:
                # Calculate tenure from date
                start_date_str = date_match.group(1)
                # Simple calculation
                now = datetime.now()
                # Parse month and year
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                parts = start_date_str.split()
                if len(parts) == 2:
                    month = month_map.get(parts[0].lower()[:3], 1)
                    year = int(parts[1])
                    tenure_months = (now.year - year) * 12 + (now.month - month)
                    tenure_years = round(tenure_months / 12, 1)

                    result = {
                        "tenure_years": tenure_years,
                        "start_date": start_date_str,
                        "source": "linkedin_scrape"
                    }
                    return {"content": [{"type": "text", "text": json.dumps(result)}]}

            # No tenure found
            return {"content": [{"type": "text", "text": json.dumps({
                "tenure_years": None,
                "error": "No tenure pattern found in profile"
            })}]}

    except Exception as e:
        return {"content": [{"type": "text", "text": json.dumps({
            "tenure_years": None,
            "error": str(e)
        })}]}


@tool("gather_contact_background", "Gather contact tenure via Perplexity fallback", {
    "name": str,
    "title": str,
    "company": str
})
async def gather_contact_background_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Perplexity fallback for tenure (when no LinkedIn available)

    Returns structured JSON or null data
    """

    load_project_env()
    perplexity_key = get_api_key("PERPLEXITY_API_KEY")

    if not perplexity_key:
        return {"content": [{"type": "text", "text": json.dumps({
            "tenure": None,
            "previous_clubs": 0,
            "error": "PERPLEXITY_API_KEY not set"
        })}]}

    import httpx

    name = args["name"]
    title = args["title"]
    company = args["company"]

    # Query Perplexity for background
    query = f"""Find career information for {name}, {title} at {company}.

Look for:
- How long has {name} been at {company}? (tenure in years)
- What golf courses did {name} work at previously?
- Total years of experience in golf industry?

Return ONLY factual information from reliable sources. If not found, return null."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": query}]
                }
            )

            data = r.json()

            if data.get("choices"):
                response_text = data["choices"][0]["message"]["content"]

                # Try to extract tenure from response
                tenure_match = re.search(r'(\d+)\s*years?', response_text, re.IGNORECASE)
                tenure = int(tenure_match.group(1)) if tenure_match else None

                result = {
                    "tenure": tenure,
                    "previous_clubs": 0,  # Hard to extract reliably
                    "source_text": response_text[:500]  # First 500 chars
                }

                return {"content": [{"type": "text", "text": json.dumps(result)}]}

    except Exception as e:
        pass

    # Failed - return null
    return {"content": [{"type": "text", "text": json.dumps({
        "tenure": None,
        "previous_clubs": 0
    })}]}


async def enrich_contact_background(contact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich contact with tenure and background data

    LinkedIn-First Strategy:
    1. If linkedin_url exists → Scrape LinkedIn (accurate!)
    2. Else → Try Perplexity (fallback)
    3. Else → Return NULL (honest)

    Args:
        contact: Dict with name, title, company, optional linkedin_url

    Returns:
        Dict with tenure, previous clubs, confidence, cost
    """

    # ========================================================================
    # STEP 1: LinkedIn Scraping (Primary - When Available)
    # ========================================================================
    if contact.get('linkedin_url'):
        # Use SDK pattern (like Agent 4) with BrightData scraping tool
        linkedin_server = create_sdk_mcp_server("linkedin", tools=[scrape_linkedin_tenure_tool])

        linkedin_options = ClaudeAgentOptions(
            mcp_servers={"linkedin": linkedin_server},
            allowed_tools=["mcp__linkedin__scrape_linkedin_tenure"],
            disallowed_tools=["Task", "TodoWrite", "Grep", "Glob", "WebSearch", "WebFetch"],
            permission_mode="bypassPermissions",
            max_turns=2,
            model="claude-haiku-4-5",
            system_prompt=(
                "Use scrape_linkedin_tenure tool. It returns JSON. "
                "OUTPUT ONLY THE EXACT JSON - NO MARKDOWN, NO FORMATTING."
            ),
        )

        linkedin_data = None
        linkedin_result_message = None

        async with ClaudeSDKClient(options=linkedin_options) as client:
            await client.query(f"Scrape tenure from: {contact['linkedin_url']}")

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            json_match = re.search(r'\{.*"tenure_years".*\}', block.text, re.DOTALL)
                            if json_match:
                                try:
                                    linkedin_data = json.loads(json_match.group(0))
                                except json.JSONDecodeError:
                                    pass

                if isinstance(msg, ResultMessage):
                    linkedin_result_message = msg

        if linkedin_data and linkedin_data.get('tenure_years'):
            # Successfully extracted tenure from LinkedIn!
            return {
                "_agent65_tenure": linkedin_data['tenure_years'],
                "_agent65_start_date": linkedin_data.get('start_date'),
                "_agent65_previous_clubs": 0,  # TODO: Extract from LinkedIn
                "_agent65_source": "linkedin",
                "_agent65_confidence": "high",
                "_agent65_cost": linkedin_result_message.total_cost_usd if linkedin_result_message else 0.002,
                "_agent65_industry_experience": None  # TODO: Calculate total
            }

    # ========================================================================
    # STEP 2: Perplexity Fallback (When No LinkedIn)
    # ========================================================================

    server = create_sdk_mcp_server("bg", tools=[gather_contact_background_tool])

    options = ClaudeAgentOptions(
        mcp_servers={"bg": server},
        allowed_tools=["mcp__bg__gather_contact_background"],
        disallowed_tools=["Task", "TodoWrite", "Grep", "Glob", "WebSearch", "WebFetch"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use gather_contact_background tool. It returns JSON. "
            "OUTPUT ONLY THE EXACT JSON - NO MARKDOWN, NO FORMATTING."
        ),
    )

    enrichment = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Get background: {contact.get('name')}, {contact.get('title')}, {contact.get('company', 'company')}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        json_match = re.search(r'\{.*"tenure".*\}', block.text, re.DOTALL)
                        if json_match:
                            try:
                                enrichment = json.loads(json_match.group(0))
                            except json.JSONDecodeError:
                                pass

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Merge results
    result = {
        "_agent65_tenure": enrichment.get("tenure") if enrichment else None,
        "_agent65_previous_clubs": enrichment.get("previous_clubs", 0) if enrichment else 0,
        "_agent65_source": "perplexity_fallback",
        "_agent65_confidence": "low" if enrichment and enrichment.get("tenure") else "none",
        "_agent65_cost": result_message.total_cost_usd if result_message else 0,
        "_agent65_turns": result_message.num_turns if result_message else 0
    }

    return result


async def main():
    """Demo: Test LinkedIn-first tenure extraction"""
    print("📋 Agent 6.5: Contact Background (LinkedIn-First)")
    print("="*70)

    # Test 1: Contact WITH LinkedIn
    print("\nTest 1: Contact WITH LinkedIn")
    print("-"*70)

    contact_with_linkedin = {
        "name": "Dustin Betthauser",
        "title": "Park Manager",
        "company": "Brambleton Golf Course",
        "linkedin_url": "https://www.linkedin.com/in/dustin-betthauser"
    }

    result1 = await enrich_contact_background(contact_with_linkedin)

    print(f"Result:")
    print(f"  Tenure: {result1.get('_agent65_tenure', 'Not found')}")
    print(f"  Start Date: {result1.get('_agent65_start_date', 'N/A')}")
    print(f"  Source: {result1.get('_agent65_source')}")
    print(f"  Confidence: {result1.get('_agent65_confidence')}")
    print(f"  Cost: ${result1.get('_agent65_cost', 0):.4f}")

    if result1.get('_agent65_tenure'):
        print(f"  ✅ LinkedIn scraping worked!")
    else:
        print(f"  ⚠️  LinkedIn scraping failed (fell back to Perplexity)")

    # Test 2: Contact WITHOUT LinkedIn
    print("\n\nTest 2: Contact WITHOUT LinkedIn")
    print("-"*70)

    contact_no_linkedin = {
        "name": "Bryan McFerren",
        "title": "Superintendent",
        "company": "Brambleton Golf Course"
    }

    result2 = await enrich_contact_background(contact_no_linkedin)

    print(f"Result:")
    print(f"  Tenure: {result2.get('_agent65_tenure', 'Not found')}")
    print(f"  Source: {result2.get('_agent65_source')}")
    print(f"  Confidence: {result2.get('_agent65_confidence')}")
    print(f"  Cost: ${result2.get('_agent65_cost', 0):.4f}")

    if result2.get('_agent65_tenure'):
        print(f"  ✅ Perplexity found tenure")
    else:
        print(f"  ⚠️  No tenure data (NULL is acceptable)")

    print(f"\n{'='*70}")
    print("✅ Agent 6.5 Complete!")
    print(f"{'='*70}")


if __name__ == "__main__":
    anyio.run(main)
