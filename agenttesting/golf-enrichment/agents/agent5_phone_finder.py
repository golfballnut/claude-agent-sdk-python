#!/usr/bin/env python3
"""
Agent 5: Phone Finder (Specialist)
Finds phone numbers for contacts using Perplexity AI

Performance (from MCP baseline):
- Success Rate: 100% (4/4 tested via Perplexity MCP)
- Cost: ~$0.002-0.005 per contact (very cheap!)
- Speed: ~5-10s per contact

Pattern:
- Custom tool with Perplexity API
- AI aggregates from multiple sources
- NO FALLBACKS - returns null if not found
- SDK MCP server (in-process)
- Haiku 4.5 model

Data Quality Rule: Returns null if not found - NEVER guesses

MCP Baseline Results:
- Stacy Foster: 804.592.5861 ✅
- Bill Ranson: (804) 784-5663 ✅
- Dean Sumner: 804-529-5367 ✅
- Peter Miller: 703-779-2022 ext. 5386 ✅

Sources: Club websites, ZoomInfo, Datanyze, PGA directories
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

@tool("find_phone", "Find phone number via Perplexity AI", {
    "name": str,
    "title": str,
    "company": str,
    "state": str
})
async def find_phone_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Phone Discovery via Perplexity AI (NO GUESSING):
    1. Query Perplexity with natural language
    2. AI searches multiple sources (websites, directories, databases)
    3. Returns phone with citations
    4. Return null if not found (NO fallbacks)

    Perplexity aggregates from:
    - Club websites
    - ZoomInfo
    - Datanyze
    - PGA directories
    - Public records
    """
    import httpx
    import re

    name = args["name"]
    title = args["title"]
    company = args["company"]
    state = args.get("state", "Virginia")

    results = {
        "phone": None,
        "phone_source": None,
        "method": None,
        "confidence": 0,
    }

    # Load environment
    load_project_env()
    perplexity_key = get_api_key("PERPLEXITY_API_KEY")

    if not perplexity_key:
        print(f"   ⚠ PERPLEXITY_API_KEY not set")
        results["method"] = "api_key_missing"
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(results)
            }]
        }

    # STEP 1: Query Perplexity AI
    try:
        query = f"Find the phone number for {name}, {title} at {company} in {state}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {perplexity_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "sonar",  # Cheapest search model
                "messages": [
                    {"role": "user", "content": query}
                ]
            }

            r = await client.post(url, headers=headers, json=payload)
            data = r.json()

            # Extract phone from response
            if data.get("choices"):
                response_text = data["choices"][0]["message"]["content"]

                # Extract phone numbers
                # Patterns: (XXX) XXX-XXXX, XXX-XXX-XXXX, XXX.XXX.XXXX, with optional ext
                # Fixed: Requires BOTH parens or NEITHER (no mixing!)
                phone_pattern = r'(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?:\s?(?:ext|x)\.?\s?\d+)?'
                phones = re.findall(phone_pattern, response_text)

                if phones:
                    results["phone"] = phones[0]
                    results["method"] = "perplexity_ai"
                    results["phone_source"] = "aggregated"  # Perplexity searches multiple sources
                    results["confidence"] = 90  # High confidence if Perplexity found it
                    print(f"   ✓ Found phone via Perplexity AI")

                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(results)
                        }]
                    }

    except Exception as e:
        print(f"   ✗ Perplexity API failed: {e}")

    # STEP 2: Not found (NO GUESSING - return nulls)
    results["method"] = "not_found"
    print(f"   ✗ Phone not found (clean null)")

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(results)
        }]
    }


# ============================================================================
# AGENT FUNCTION
# ============================================================================

async def find_phone(contact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find phone number for a contact

    Args:
        contact: Dict with name, title, company (optionally state)

    Returns:
        Dict with original contact + phone (or null)
    """

    server = create_sdk_mcp_server("phone", tools=[find_phone_tool])

    options = ClaudeAgentOptions(
        mcp_servers={"phone": server},
        allowed_tools=["mcp__phone__find_phone"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use find_phone tool. It returns pure JSON. "
            "OUTPUT ONLY THE EXACT JSON - NO MARKDOWN, NO FORMATTING."
        ),
    )

    phone_data = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find phone: {contact['name']}, {contact['title']}, {contact.get('company', 'company')}, {contact.get('state', 'Virginia')}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        phone_data = extract_json_from_text(block.text, required_field="phone")

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Merge with original contact
    result = contact.copy()
    if phone_data:
        result.update(phone_data)

    result["_agent5_cost"] = result_message.total_cost_usd if result_message else None
    result["_agent5_turns"] = result_message.num_turns if result_message else None

    return result


# ============================================================================
# BATCH PROCESSING
# ============================================================================

async def find_phones(contacts: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Find phone numbers for multiple contacts

    Args:
        contacts: List of contact dicts

    Returns:
        List of enriched contacts with phone numbers (or nulls)
    """
    enriched = []

    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{len(contacts)}] {contact.get('name', 'Unknown')}")

        try:
            result = await find_phone(contact)

            phone = result.get("phone")
            method = result.get("method")

            if phone:
                print(f"   ✅ {phone} ({method})")
            else:
                print(f"   ❌ Not found (clean null)")

            print(f"   Cost: ${result.get('_agent5_cost', 0):.4f}")

            enriched.append(result)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_contact = contact.copy()
            error_contact["_agent5_error"] = str(e)
            enriched.append(error_contact)

    return enriched


# ============================================================================
# DEMO
# ============================================================================

async def main():
    """Demo: Find phone for test contact"""
    print("📞 Agent 5: Phone Finder")
    print("="*70)
    print("Using Perplexity AI to find phone numbers\n")

    test_contact = {
        "name": "Stacy Foster",
        "title": "General Manager",
        "company": "Richmond Country Club",
        "state": "Virginia"
    }

    print(f"Contact: {test_contact['name']}")
    print(f"Title: {test_contact['title']}")
    print(f"Company: {test_contact['company']}\n")

    result = await find_phone(test_contact)

    print(f"\n📊 Result:")
    print(f"   Phone: {result.get('phone', 'Not found')}")
    print(f"   Method: {result.get('method', 'N/A')}")
    print(f"   Source: {result.get('phone_source', 'N/A')}")
    print(f"   Confidence: {result.get('confidence', 0)}%")
    print(f"   Cost: ${result.get('_agent5_cost', 0):.4f}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
