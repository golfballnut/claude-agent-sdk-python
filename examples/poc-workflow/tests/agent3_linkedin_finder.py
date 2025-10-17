#!/usr/bin/env python3
"""
Agent 3: LinkedIn Finder (Minimal)
Finds LinkedIn profile URLs for contacts

Performance Target:
- Cost: < $0.01 per contact
- Accuracy: > 80%
- Speed: < 5s per contact

Pattern:
- WebFetch only (cheaper than WebSearch)
- Haiku 4.5 model
- max_turns=2
- Direct Google search scraping
"""

from typing import Any

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)


async def find_linkedin_url(contact: dict[str, Any]) -> dict[str, Any]:
    """
    Find LinkedIn profile URL for a contact

    Args:
        contact: Dict with name, title, company

    Returns:
        Dict with original contact + linkedin_url (or None)
    """

    name = contact.get("name", "")
    title = contact.get("title", "")
    company = contact.get("company", "")

    if not name or not company:
        raise ValueError("Contact must have name and company")

    # Build Google search query
    search_query = f"{name} {title} {company} LinkedIn site:linkedin.com/in"
    google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"

    options = ClaudeAgentOptions(
        allowed_tools=["WebFetch"],
        disallowed_tools=["WebSearch", "Task", "TodoWrite", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            f"Use WebFetch to get {google_url}. "
            f"Extract the LinkedIn profile URL for {name}. "
            f"Return ONLY the LinkedIn URL (https://linkedin.com/in/...) or 'NOT_FOUND' if none found."
        ),
    )

    linkedin_url = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Fetch Google search and find LinkedIn URL for {name}")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        # Extract LinkedIn URL
                        import re
                        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
                        urls = re.findall(linkedin_pattern, block.text)
                        if urls:
                            # Take first match
                            linkedin_url = urls[0]

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Return enriched contact
    enriched = contact.copy()
    enriched["linkedin_url"] = linkedin_url
    enriched["_agent3_cost"] = result_message.total_cost_usd if result_message else None
    enriched["_agent3_turns"] = result_message.num_turns if result_message else None

    return enriched


async def enrich_contacts(contacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Enrich multiple contacts with LinkedIn URLs

    Args:
        contacts: List of contact dicts from Agent 2

    Returns:
        List of enriched contacts with linkedin_url added
    """
    enriched = []

    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{len(contacts)}] Enriching: {contact.get('name', 'Unknown')}")

        try:
            result = await find_linkedin_url(contact)

            if result.get("linkedin_url"):
                print(f"   ✅ Found: {result['linkedin_url']}")
            else:
                print("   ⚠️  Not found")

            print(f"   Cost: ${result.get('_agent3_cost', 0):.4f}")

            enriched.append(result)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            # Return original contact on error
            error_contact = contact.copy()
            error_contact["linkedin_url"] = None
            error_contact["_agent3_error"] = str(e)
            enriched.append(error_contact)

    return enriched


async def main():
    """Demo: Enrich test contact"""
    print("🔍 Agent 3: LinkedIn Finder")
    print("=" * 70)

    # Test contact
    test_contact = {
        "name": "Stacy Foster",
        "title": "General Manager",
        "company": "Richmond Country Club",
    }

    print(f"Contact: {test_contact['name']}")
    print(f"Title: {test_contact['title']}")
    print(f"Company: {test_contact['company']}\n")

    result = await find_linkedin_url(test_contact)

    print("\n📊 Result:")
    if result.get("linkedin_url"):
        print(f"   ✅ LinkedIn: {result['linkedin_url']}")
    else:
        print("   ⚠️  LinkedIn: Not found")

    print(f"   Cost: ${result.get('_agent3_cost', 0):.4f}")
    print(f"   Turns: {result.get('_agent3_turns', 0)}")

    print("\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
