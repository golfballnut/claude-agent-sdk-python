#!/usr/bin/env python3
"""
Agent 3 Custom API Tool Test

Builds custom tool that calls APIs directly (like Agent 1 pattern)
Implements proven 5-step email + 2-step LinkedIn discovery
"""

import json
import os
import time
from typing import Any

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

TEST_CONTACT = {
    "name": "Stacy Foster",
    "title": "General Manager",
    "company": "Richmond Country Club",
    "company_domain": "richmondcountryclubva.com"
}


@tool("enrich_contact", "Find email and LinkedIn with proven 5-step fallback", {
    "name": str,
    "title": str,
    "company": str,
    "domain": str
})
async def enrich_contact_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Custom tool implementing 5-step email + 2-step LinkedIn discovery
    Uses direct API calls to avoid MCP routing issues
    """
    import re

    import httpx

    name = args["name"]
    title = args["title"]
    company = args["company"]
    domain = args["domain"]

    results = {
        "email": None,
        "email_method": None,
        "email_confidence": 0,
        "linkedin_url": None,
        "linkedin_method": None,
        "steps_log": [],
    }

    print(f"\n   🔍 Enriching: {name}")

    # ========================================================================
    # EMAIL DISCOVERY
    # ========================================================================

    # Load API key from project root .env
    from pathlib import Path
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print(f"   ℹ Loaded .env from {env_path}")

    # STEP 1: Hunter.io Email Finder (if API key available)
    hunter_api_key = os.getenv("HUNTER_API_KEY")
    if hunter_api_key:
        results["steps_log"].append("Trying Step 1: Hunter.io Email-Finder")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = "https://api.hunter.io/v2/email-finder"
                params = {
                    "domain": domain,
                    "first_name": name.split()[0],
                    "last_name": name.split()[-1],
                    "api_key": hunter_api_key
                }
                r = await client.get(url, params=params)
                data = r.json()

                if data.get("data") and data["data"].get("email"):
                    email = data["data"]["email"]
                    confidence = data["data"].get("score", 0)

                    if confidence >= 70:  # Hunter.io scale is 0-100
                        results["email"] = email
                        results["email_method"] = "hunter_io"
                        results["email_confidence"] = confidence
                        print(f"   ✓ Step 1: Found via Hunter.io (confidence: {confidence}%)")
        except Exception as e:
            print(f"   ✗ Step 1 failed: {e}")
            results["steps_log"].append(f"Step 1 failed: {str(e)}")

    # STEP 2: BrightData Search (via Jina scraping Google)
    if not results["email"]:
        results["steps_log"].append("Trying Step 2: BrightData Search")
        try:
            query = f'"{name}" "{company}" {title} email'
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"https://r.jina.ai/{search_url}")
                content = r.text[:8000]

                # Look for email at this domain
                email_pattern = r'\b[A-Za-z0-9._%+-]+@' + re.escape(domain) + r'\b'
                emails = re.findall(email_pattern, content, re.IGNORECASE)

                if emails:
                    results["email"] = emails[0]
                    results["email_method"] = "brightdata_search"
                    results["email_confidence"] = 70  # Estimated
                    print("   ✓ Step 2: Found via web search")
                else:
                    print("   ✗ Step 2: No email found in search results")
        except Exception as e:
            print(f"   ✗ Step 2 failed: {e}")
            results["steps_log"].append(f"Step 2 failed: {str(e)}")

    # STEP 3: Jina Search (focused query)
    if not results["email"]:
        results["steps_log"].append("Trying Step 3: Jina Search")
        try:
            query = f'{name} {company} contact email'
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"https://r.jina.ai/{search_url}")
                content = r.text[:8000]

                email_pattern = r'\b[A-Za-z0-9._%+-]+@' + re.escape(domain) + r'\b'
                emails = re.findall(email_pattern, content, re.IGNORECASE)

                if emails:
                    results["email"] = emails[0]
                    results["email_method"] = "jina_search"
                    results["email_confidence"] = 60  # Estimated
                    print("   ✓ Step 3: Found via Jina search")
                else:
                    print("   ✗ Step 3: No email found")
        except Exception as e:
            print(f"   ✗ Step 3 failed: {e}")
            results["steps_log"].append(f"Step 3 failed: {str(e)}")

    # STEP 4: Course General Email
    if not results["email"]:
        results["steps_log"].append("Step 4: Using general email fallback")
        results["email"] = f"info@{domain}"
        results["email_method"] = "course_general_email"
        results["email_confidence"] = 30
        print("   ⚠ Step 4: Using general email")

    # STEP 5: Flag for manual research
    if not results["email"]:
        results["steps_log"].append("Step 5: Flagged for manual research")
        results["email_method"] = "needs_manual_research"
        print("   ✗ Step 5: Manual research needed")

    # ========================================================================
    # LINKEDIN DISCOVERY
    # ========================================================================

    # STEP 1: Site-filtered search
    results["steps_log"].append("LinkedIn Step 1: Site-filtered search")
    try:
        query = f'"{name}" "{company}" site:linkedin.com/in/'
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"https://r.jina.ai/{search_url}")
            content = r.text

            linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
            urls = re.findall(linkedin_pattern, content)

            if urls:
                results["linkedin_url"] = urls[0]
                results["linkedin_method"] = "brightdata_site_filter"
                print("   ✓ LinkedIn Step 1: Found profile")
            else:
                print("   ✗ LinkedIn Step 1: No profile found")
    except Exception as e:
        print(f"   ✗ LinkedIn Step 1 failed: {e}")

    # STEP 2: Jina LinkedIn search
    if not results["linkedin_url"]:
        results["steps_log"].append("LinkedIn Step 2: Jina search")
        try:
            query = f'"{name}" {title} {company} LinkedIn'
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"https://r.jina.ai/{search_url}")
                content = r.text

                linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
                urls = re.findall(linkedin_pattern, content)

                if urls:
                    results["linkedin_url"] = urls[0]
                    results["linkedin_method"] = "jina_search"
                    print("   ✓ LinkedIn Step 2: Found profile")
                else:
                    print("   ✗ LinkedIn Step 2: No profile found")
        except Exception as e:
            print(f"   ✗ LinkedIn Step 2 failed: {e}")

    # Format response - return ONLY JSON for easy parsing
    result_json = json.dumps(results)

    return {
        "content": [{
            "type": "text",
            "text": result_json  # Just JSON, no extra text
        }]
    }


async def main():
    print("🧪 Agent 3 Custom API Tool Test")
    print("="*70)
    print("Pattern: Custom tool with direct API calls (like Agent 1)")
    print(f"Contact: {TEST_CONTACT['name']}\n")

    start_time = time.time()

    # Create SDK MCP server with custom tool
    server = create_sdk_mcp_server("enrich", tools=[enrich_contact_tool])

    options = ClaudeAgentOptions(
        mcp_servers={"enrich": server},
        allowed_tools=["mcp__enrich__enrich_contact"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use enrich_contact tool. It returns pure JSON. "
            "OUTPUT ONLY THE EXACT JSON - NO MARKDOWN, NO FORMATTING, NO EXPLANATION."
        ),
    )

    enrichment_data = None
    tools_used = []
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Enrich: {TEST_CONTACT['name']}, {TEST_CONTACT['title']}, "
            f"{TEST_CONTACT['company']}, {TEST_CONTACT['company_domain']}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        tools_used.append(block.name)
                    elif isinstance(block, TextBlock):
                        print(f"\n   📝 Agent response: {block.text[:200]}...")

                        # Try to parse JSON - be more flexible
                        import re
                        # Try to find any JSON object
                        json_match = re.search(r'\{.*"email".*\}', block.text, re.DOTALL)
                        if json_match:
                            try:
                                enrichment_data = json.loads(json_match.group(0))
                                print(f"   ✓ Parsed enrichment data")
                            except json.JSONDecodeError as e:
                                print(f"   ✗ JSON parse error: {e}")

            if isinstance(msg, ResultMessage):
                result_message = msg

    elapsed = time.time() - start_time

    # ========================================================================
    # RESULTS
    # ========================================================================

    print(f"\n{'='*70}")
    print("📊 FINAL RESULTS")
    print(f"{'='*70}\n")

    if enrichment_data:
        print(f"   Email: {enrichment_data.get('email', 'Not found')}")
        print(f"   Email Method: {enrichment_data.get('email_method', 'N/A')}")
        print(f"   Email Confidence: {enrichment_data.get('email_confidence', 0)}%")
        print(f"   LinkedIn: {enrichment_data.get('linkedin_url', 'Not found')}")
        print(f"   LinkedIn Method: {enrichment_data.get('linkedin_method', 'N/A')}")

        email_success = enrichment_data.get('email') and \
                       enrichment_data.get('email_method') not in ['course_general_email', 'needs_manual_research']
        linkedin_success = enrichment_data.get('linkedin_url') is not None

        print(f"\n   Email Success: {'✅' if email_success else '❌'}")
        print(f"   LinkedIn Success: {'✅' if linkedin_success else '❌'}")
    else:
        print("   ⚠️  No data extracted")

    print(f"\n   Cost: ${result_message.total_cost_usd:.4f}" if result_message else "   Cost: N/A")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Turns: {result_message.num_turns}" if result_message else "   Turns: N/A")
    print(f"   Tools Used: {tools_used}")

    # Save
    output = {
        "test": "custom_api_tool",
        "contact": TEST_CONTACT,
        "enrichment": enrichment_data,
        "cost": result_message.total_cost_usd if result_message else None,
        "time_seconds": round(elapsed, 3),
        "tools_used": tools_used,
    }

    with open("../results/agent3_custom_api_test.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n💾 Saved to: ../results/agent3_custom_api_test.json")


if __name__ == "__main__":
    anyio.run(main)
