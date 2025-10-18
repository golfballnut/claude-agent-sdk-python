#!/usr/bin/env python3
"""
Agent 6.5: Contact-Level Enrichment
Gathers tenure and background information for individual contacts

Target Performance:
- Cost: ~$0.004/contact (1 Perplexity query)
- Speed: ~8s per contact
- Data: Tenure, previous clubs, industry experience

Pattern:
- Direct Perplexity API
- Single focused query per contact
- Returns structured background data
- NO business intelligence (Agent 6 handles that at course-level)

Purpose:
- Understand contact's history and tenure
- Identify career progression
- Find previous clubs worked at
- Calculate total industry experience
"""

import anyio
import json
import re
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

@tool("gather_contact_background", "Gather contact tenure and background", {
    "name": str,
    "title": str,
    "company": str
})
async def gather_contact_background_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Gather contact background via single Perplexity query

    Focus:
    - Tenure at current course
    - Previous golf courses/clubs worked at
    - Total industry experience
    - Career progression
    """
    import httpx

    name = args["name"]
    title = args["title"]
    company = args["company"]

    # Load environment
    load_project_env()
    perplexity_key = get_api_key("PERPLEXITY_API_KEY")

    if not perplexity_key:
        print(f"   ⚠ PERPLEXITY_API_KEY not set")
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({"error": "API key missing"})
            }]
        }

    # ========================================================================
    # Single Query: Contact Background
    # ========================================================================
    query = f"""Find information about {name}, {title} at {company} golf course:

Please research:
1. How long has {name} worked at {company}? (tenure in years)
2. What previous golf courses or clubs has {name} worked at?
3. How many total years has {name} been in the golf course industry?
4. What are {name}'s specific responsibilities as {title}?
5. Any career progression? (e.g., started as assistant, promoted to head role)

Focus on:
- LinkedIn profiles
- Golf industry publications
- Course websites and staff pages
- Professional golf associations
- News articles about staff changes"""

    background_intel = {}

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
                background_intel["raw_response"] = data["choices"][0]["message"]["content"]
                print(f"   ✓ Background intel gathered")
    except Exception as e:
        print(f"   ✗ Query failed: {e}")
        background_intel["raw_response"] = ""

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(background_intel)
        }]
    }


# ============================================================================
# AGENT FUNCTION
# ============================================================================

async def enrich_contact_background(contact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich contact with tenure and background information

    Args:
        contact: Dict with name, title, company

    Returns:
        Dict with original contact + background enrichment
    """

    server = create_sdk_mcp_server("contact_bg", tools=[gather_contact_background_tool])

    name = contact.get("name", "Unknown")
    title = contact.get("title", "Unknown")
    company = contact.get("company", "Unknown")

    # Build analysis prompt
    prompt = f"""
Use the gather_contact_background tool to fetch background info about {name}.

After receiving the data, analyze it and extract structured information.

**TASK:**
Parse the background intelligence and extract:

1. **Tenure at current course** - How many years at {company}?
2. **Previous clubs** - List of previous golf courses/clubs worked at
3. **Industry experience** - Total years in golf course industry
4. **Responsibilities** - What does a {title} typically handle?
5. **Career notes** - Any interesting career progression or background

**OUTPUT FORMAT** (pure JSON, no markdown, no code blocks):
{{
  "tenure_years": number or null,
  "tenure_confidence": "high" | "medium" | "low" | "unknown",
  "previous_clubs": ["Club Name 1", "Club Name 2", ...] or [],
  "industry_experience_years": number or null,
  "responsibilities": ["duty 1", "duty 2", ...],
  "career_notes": "brief summary of career progression"
}}

**CRITICAL:**
- Return ONLY the JSON object
- Use null for unknown values (don't guess)
- Empty array [] if no previous clubs found
- Extract numbers from text (e.g., "five years" → 5)
"""

    # Configure agent
    options = ClaudeAgentOptions(
        mcp_servers={"contact_bg": server},
        allowed_tools=["mcp__contact_bg__gather_contact_background"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=3,
        model="claude-haiku-4-5",  # Haiku for cost efficiency
        system_prompt=(
            "You are a data extraction API that returns ONLY pure JSON. "
            "NEVER add markdown formatting, code blocks, or explanatory text. "
            "Output the exact JSON object specified, nothing else."
        ),
    )

    enrichment = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        enrichment = extract_json_from_text(block.text, required_field="tenure_years")

                        if not enrichment:
                            print(f"   ⚠️ No valid JSON found in response")

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Build result
    result = contact.copy()

    if enrichment and isinstance(enrichment, dict):
        result["background"] = enrichment
        result["_agent65_tenure"] = enrichment.get("tenure_years")
        result["_agent65_previous_clubs"] = len(enrichment.get("previous_clubs", []))
    else:
        result["background"] = None
        result["_agent65_tenure"] = None
        result["_agent65_previous_clubs"] = 0

    result["_agent65_cost"] = result_message.total_cost_usd if result_message else None
    result["_agent65_turns"] = result_message.num_turns if result_message else None

    return result


async def main():
    """Demo: Enrich contact with background"""
    print("📋 Agent 6.5: Contact Background Enrichment")
    print("="*70)

    test_contact = {
        "name": "Stacy Foster",
        "title": "General Manager",
        "company": "Richmond Country Club"
    }

    print(f"Contact: {test_contact['name']}")
    print(f"Title: {test_contact['title']}")
    print(f"Company: {test_contact['company']}\n")

    result = await enrich_contact_background(test_contact)

    print(f"\n📊 Results:")

    bg = result.get("background", {})
    if bg:
        print(f"   Tenure: {bg.get('tenure_years', 'Unknown')} years ({bg.get('tenure_confidence', 'unknown')} confidence)")
        print(f"   Industry Experience: {bg.get('industry_experience_years', 'Unknown')} years")

        prev_clubs = bg.get("previous_clubs", [])
        if prev_clubs:
            print(f"   Previous Clubs: {', '.join(prev_clubs)}")
        else:
            print(f"   Previous Clubs: None found")

        responsibilities = bg.get("responsibilities", [])
        if responsibilities:
            print(f"   Responsibilities: {len(responsibilities)} identified")

        notes = bg.get("career_notes", "")
        if notes:
            print(f"   Career Notes: {notes[:100]}...")

    print(f"\n💰 Cost: ${result.get('_agent65_cost', 0):.4f}")
    print(f"⏱️  Turns: {result.get('_agent65_turns', 0)}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
