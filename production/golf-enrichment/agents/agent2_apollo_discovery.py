#!/usr/bin/env python3
"""
Agent 2-Apollo: Contact Discovery & Enrichment (All-in-One)

REPLACES:
- Agent 2: Contact discovery (web scraping)
- Agent 3: Email enrichment (Hunter.io)
- Agent 4: LinkedIn & tenure extraction

Uses Apollo.io to find CURRENT employees with verified emails.

Performance Target:
- Email Success: 50-60% (verified, 90%+ confidence)
- Cost: <$0.20 per course (2-4 contacts × 2 credits = ~$0.16)
- Credits: 4-8 per course (within 4,020/month limit)
- Data Quality: Current employees (job change detection)

Pattern:
- 2-step Apollo API (search → enrich)
- Title filtering (GM, Director, Head Pro, Superintendent)
- Credit tracking
- Claude SDK with custom Apollo tool

Benefits vs Current:
- Current employees (not outdated data)
- Verified emails (90%+ confidence)
- LinkedIn included (100% coverage)
- Employment history (tenure, previous clubs, education)
- Simpler (1 agent vs 3)
"""

import anyio
import httpx
import json
import os
from typing import Any, Dict, List
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


# Apollo.io credit cost (from testing)
CREDITS_PER_EMAIL = 2  # Enrichment to unlock email
COST_PER_CREDIT = 79 / 4020  # $79/month ÷ 4,020 credits = $0.0197/credit
COST_PER_ENRICHMENT = CREDITS_PER_EMAIL * COST_PER_CREDIT  # ~$0.039


@tool("find_contacts_apollo", "Find current golf course staff with emails via Apollo.io", {
    "course_name": str,
    "domain": str
})
async def find_contacts_apollo_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Find current golf course staff using Apollo.io (replaces Agents 2, 3, 4)

    2-Step Process:
    1. Search Apollo for 4 key positions (GM, Director, Head Pro, Superintendent)
    2. Enrich each person found to unlock email

    Returns:
    - 2-4 current employees with verified emails, LinkedIn, employment history
    - All emails 90%+ confidence (verified status)
    - Cost tracking (credits used)
    """
    import httpx

    course_name = args["course_name"]
    domain = args.get("domain", "")

    # Load .env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "error": "APOLLO_API_KEY not found in .env",
                    "contacts": [],
                    "credits_used": 0,
                    "cost_usd": 0
                })
            }]
        }

    # Target positions (4 key decision-makers)
    target_positions = [
        "General Manager",
        "Director of Golf",
        "Head Golf Professional",
        "Superintendent"
    ]

    contacts = []
    credits_used = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": api_key.strip()
        }

        # STEP 1: Search for each position
        for position in target_positions:
            try:
                # Search Apollo
                search_url = "https://api.apollo.io/api/v1/people/search"
                search_payload = {
                    "q_organization_name": course_name,
                    "person_titles": [position],
                    "page": 1,
                    "per_page": 3  # Top 3 matches
                }

                search_r = await client.post(search_url, headers=headers, json=search_payload)

                if search_r.status_code != 200:
                    continue

                search_data = search_r.json()
                people = search_data.get("people", [])

                if not people:
                    continue

                # Get first match (best match)
                person = people[0]
                person_id = person.get("id")
                person_name = person.get("name")

                # STEP 2: Enrich to unlock email
                enrich_url = "https://api.apollo.io/api/v1/people/match"
                enrich_payload = {
                    "id": person_id,
                    "reveal_personal_emails": False,  # Work emails only
                    "reveal_phone_number": False  # Skip phone (8 credits!)
                }

                enrich_r = await client.post(enrich_url, headers=headers, json=enrich_payload)

                if enrich_r.status_code != 200:
                    continue

                enrich_data = enrich_r.json()
                enriched_person = enrich_data.get("person")

                if not enriched_person:
                    continue

                # Track credits (2 per enrichment based on testing)
                credits_used += CREDITS_PER_EMAIL

                # Extract data
                email = enriched_person.get("email")
                email_status = enriched_person.get("email_status")

                # Only include if verified (90%+ confidence)
                if email and email_status == "verified":
                    employment_history = enriched_person.get("employment_history", [])
                    current_job = next((j for j in employment_history if j.get("current")), {})

                    contact = {
                        "name": enriched_person.get("name"),
                        "title": enriched_person.get("title") or position,
                        "email": email,
                        "email_confidence": 95,  # Verified = 95%
                        "email_method": "apollo_verified",
                        "linkedin_url": enriched_person.get("linkedin_url"),
                        "linkedin_method": "apollo",
                        "tenure_years": None,  # Calculate from employment history
                        "tenure_start_date": current_job.get("start_date"),
                        "previous_clubs": [],  # Parse from employment_history
                        "source": "apollo",
                        "person_id": person_id
                    }

                    # Parse tenure (start_date → years)
                    if current_job.get("start_date"):
                        try:
                            from datetime import datetime
                            start_date = datetime.strptime(current_job["start_date"], "%Y-%m-%d")
                            tenure_days = (datetime.now() - start_date).days
                            contact["tenure_years"] = round(tenure_days / 365.25, 1)
                        except:
                            pass

                    # Parse previous clubs
                    for job in employment_history:
                        if not job.get("current") and "golf" in job.get("organization_name", "").lower():
                            contact["previous_clubs"].append({
                                "name": job.get("organization_name"),
                                "title": job.get("title"),
                                "start_date": job.get("start_date"),
                                "end_date": job.get("end_date")
                            })

                    contacts.append(contact)

            except Exception as e:
                print(f"   ⚠️ Error finding {position}: {e}")
                continue

    # Calculate cost
    cost_usd = credits_used * COST_PER_CREDIT

    # Calculate email coverage
    emails_found = len([c for c in contacts if c.get('email')])
    total_contacts = len(contacts)
    coverage = f"{emails_found}/{total_contacts}" if contacts else "0/0"

    result = {
        "contacts": contacts,
        "credits_used": credits_used,
        "cost_usd": round(cost_usd, 4),
        "source": "apollo",
        "email_coverage": coverage
    }

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(result)
        }]
    }


async def discover_contacts(course_name: str, domain: str = "") -> Dict[str, Any]:
    """
    Discover and enrich golf course contacts using Apollo.io

    Args:
        course_name: Golf course name (e.g., "Ballantyne Country Club")
        domain: Course domain (optional, for validation)

    Returns:
        Dict with contacts, cost, credits used
    """

    server = create_sdk_mcp_server("apollo", tools=[find_contacts_apollo_tool])

    options = ClaudeAgentOptions(
        mcp_servers={"apollo": server},
        allowed_tools=["mcp__apollo__find_contacts_apollo"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use find_contacts_apollo tool to find current golf course staff. "
            "It returns pure JSON with contacts, emails, LinkedIn, employment history. "
            "OUTPUT ONLY THE EXACT JSON - NO MARKDOWN, NO FORMATTING."
        ),
    )

    enrichment = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find current staff at: {course_name}, domain: {domain}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        import re
                        json_match = re.search(r'\{.*"contacts".*\}', block.text, re.DOTALL)
                        if json_match:
                            try:
                                enrichment = json.loads(json_match.group(0))
                            except json.JSONDecodeError:
                                pass

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Add SDK cost on top of Apollo credits
    if enrichment:
        apollo_cost = enrichment.get("cost_usd", 0)
        sdk_cost = result_message.total_cost_usd if result_message else 0
        enrichment["total_cost_usd"] = apollo_cost + sdk_cost
        enrichment["sdk_cost_usd"] = sdk_cost
        enrichment["apollo_cost_usd"] = apollo_cost

    return enrichment or {
        "contacts": [],
        "credits_used": 0,
        "cost_usd": 0,
        "error": "No response from agent"
    }


async def main():
    """Demo: Test Agent 2-Apollo on sample NC course"""
    print("🔍 Agent 2-Apollo: Contact Discovery & Enrichment")
    print("="*70)

    test_course = {
        "name": "Ballantyne Country Club",
        "domain": "ballantyneclub.com"
    }

    print(f"Course: {test_course['name']}")
    print(f"Domain: {test_course['domain']}\n")

    result = await discover_contacts(test_course['name'], test_course['domain'])

    print(f"\n📊 Results:")
    print(f"   Contacts found: {len(result.get('contacts', []))}")
    print(f"   Credits used: {result.get('credits_used', 0)}")
    print(f"   Apollo cost: ${result.get('apollo_cost_usd', 0):.4f}")
    print(f"   SDK cost: ${result.get('sdk_cost_usd', 0):.4f}")
    print(f"   Total cost: ${result.get('total_cost_usd', 0):.4f}")

    for contact in result.get('contacts', []):
        print(f"\n   Contact: {contact['name']}")
        print(f"      Title: {contact['title']}")
        print(f"      Email: {contact.get('email', 'None')} ({contact.get('email_confidence', 0)}%)")
        print(f"      LinkedIn: {contact.get('linkedin_url', 'None')}")
        if contact.get('tenure_years'):
            print(f"      Tenure: {contact['tenure_years']} years")
        if contact.get('previous_clubs'):
            print(f"      Previous clubs: {len(contact['previous_clubs'])}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
