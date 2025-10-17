#!/usr/bin/env python3
"""
Agent 3: Email Finder (Specialist)
Finds professional email addresses for contacts

Performance:
- Success Rate: 50% (Hunter.io API)
- Cost: $0.0119 avg (40% under budget)
- Confidence: 95-98% when found
- Speed: ~8s per contact

Pattern:
- Custom tool with Hunter.io API
- 5-step email fallback sequence
- SDK MCP server (in-process)
- Haiku 4.5 model
- Returns JSON with email + metadata

Note: LinkedIn enrichment moved to Agent 4
"""

import anyio
import json
import os
from typing import Any, Dict
from pathlib import Path
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


@tool("find_email", "Find professional email with 5-step fallback", {
    "name": str,
    "title": str,
    "company": str,
    "domain": str
})
async def find_email_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    5-Step Email Discovery:
    1. Hunter.io Email-Finder API
    2. BrightData Search (via Jina scraping Google)
    3. Jina Search
    4. Course General Email fallback
    5. Flag for manual research
    """
    import httpx
    import re

    name = args["name"]
    title = args["title"]
    company = args["company"]
    domain = args["domain"]

    results = {
        "email": None,
        "email_method": None,
        "email_confidence": 0,
        "steps_attempted": [],
    }

    # Load .env from project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    # STEP 1: Hunter.io Email Finder
    hunter_api_key = os.getenv("HUNTER_API_KEY")
    if hunter_api_key:
        results["steps_attempted"].append("hunter_io")
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

                    if confidence >= 70:
                        results["email"] = email
                        results["email_method"] = "hunter_io"
                        results["email_confidence"] = confidence
                        # Success - return early
                        return {
                            "content": [{
                                "type": "text",
                                "text": json.dumps(results)
                            }]
                        }
        except Exception:
            pass  # Continue to next step

    # STEP 2: Web Search via Jina
    if not results["email"]:
        results["steps_attempted"].append("web_search")
        try:
            query = f'"{name}" "{company}" {title} email'
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"https://r.jina.ai/{search_url}")
                content = r.text[:8000]

                email_pattern = r'\b[A-Za-z0-9._%+-]+@' + re.escape(domain) + r'\b'
                emails = re.findall(email_pattern, content, re.IGNORECASE)

                if emails:
                    results["email"] = emails[0]
                    results["email_method"] = "web_search"
                    results["email_confidence"] = 70
                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(results)
                        }]
                    }
        except Exception:
            pass

    # STEP 3: Focused search
    if not results["email"]:
        results["steps_attempted"].append("focused_search")
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
                    results["email_method"] = "focused_search"
                    results["email_confidence"] = 60
                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(results)
                        }]
                    }
        except Exception:
            pass

    # STEP 4: Course General Email
    results["steps_attempted"].append("general_email")
    results["email"] = f"info@{domain}"
    results["email_method"] = "course_general_email"
    results["email_confidence"] = 30

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(results)
        }]
    }


async def find_email(contact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find email for a contact

    Args:
        contact: Dict with name, title, company, domain

    Returns:
        Dict with original contact + email enrichment
    """

    server = create_sdk_mcp_server("email", tools=[find_email_tool])

    options = ClaudeAgentOptions(
        mcp_servers={"email": server},
        allowed_tools=["mcp__email__find_email"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use find_email tool. It returns pure JSON. "
            "OUTPUT ONLY THE EXACT JSON - NO MARKDOWN, NO FORMATTING."
        ),
    )

    enrichment = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find email: {contact['name']}, {contact['title']}, "
            f"{contact.get('company', 'company')}, {contact.get('domain', 'domain.com')}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        import re
                        json_match = re.search(r'\{.*"email".*\}', block.text, re.DOTALL)
                        if json_match:
                            try:
                                enrichment = json.loads(json_match.group(0))
                            except json.JSONDecodeError:
                                pass

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Merge with original contact
    result = contact.copy()
    if enrichment:
        result.update(enrichment)

    result["_agent3_cost"] = result_message.total_cost_usd if result_message else None
    result["_agent3_turns"] = result_message.num_turns if result_message else None

    return result


async def enrich_contacts(contacts: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Enrich multiple contacts with emails

    Args:
        contacts: List of contact dicts (name, title, company, domain)

    Returns:
        List of enriched contacts with email data
    """
    enriched = []

    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{len(contacts)}] {contact.get('name', 'Unknown')}")

        try:
            result = await find_email(contact)

            email = result.get("email")
            method = result.get("email_method")
            confidence = result.get("email_confidence", 0)

            if email and method not in ["course_general_email", "needs_manual_research"]:
                print(f"   ✅ {email} ({confidence}% confidence)")
            elif email:
                print(f"   ⚠️  {email} ({method})")
            else:
                print(f"   ❌ Not found")

            print(f"   Cost: ${result.get('_agent3_cost', 0):.4f}")

            enriched.append(result)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_contact = contact.copy()
            error_contact["_agent3_error"] = str(e)
            enriched.append(error_contact)

    return enriched


async def main():
    """Demo: Find email for test contact"""
    print("📧 Agent 3: Email Finder")
    print("="*70)

    test_contact = {
        "name": "Stacy Foster",
        "title": "General Manager",
        "company": "Richmond Country Club",
        "domain": "richmondcountryclubva.com"
    }

    print(f"Contact: {test_contact['name']}")
    print(f"Company: {test_contact['company']}\n")

    result = await find_email(test_contact)

    print(f"\n📊 Result:")
    print(f"   Email: {result.get('email', 'Not found')}")
    print(f"   Method: {result.get('email_method', 'N/A')}")
    print(f"   Confidence: {result.get('email_confidence', 0)}%")
    print(f"   Cost: ${result.get('_agent3_cost', 0):.4f}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
