#!/usr/bin/env python3
"""
Simplified Agent 3 Test - Direct Tool Testing

Problem: SDK agents are using WebSearch instead of specified tools
Solution: Test simpler patterns that work
"""

import json
import time

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)

TEST_CONTACT = {
    "name": "Stacy Foster",
    "title": "General Manager",
    "company": "Richmond Country Club",
    "company_domain": "richmondcountryclubva.com"
}


async def test_websearch_linkedin():
    """Test LinkedIn finding with WebFetch only (cheaper)"""
    print("\n" + "="*70)
    print("TEST: LinkedIn Discovery (WebFetch - Cheap)")
    print("="*70)

    start_time = time.time()

    # Use WebFetch to search Google directly (cheaper than WebSearch)
    google_query = f"{TEST_CONTACT['name']} {TEST_CONTACT['title']} {TEST_CONTACT['company']} LinkedIn"
    google_url = f"https://www.google.com/search?q={google_query.replace(' ', '+')}"

    options = ClaudeAgentOptions(
        allowed_tools=["WebFetch"],
        disallowed_tools=["WebSearch", "Task", "TodoWrite", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            f"Use WebFetch on {google_url}. "
            f"Extract the LinkedIn profile URL for {TEST_CONTACT['name']}. "
            f"Return only the URL."
        ),
    )

    linkedin_url = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Fetch {google_url} and find LinkedIn URL")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        # Extract LinkedIn URL
                        import re
                        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
                        urls = re.findall(linkedin_pattern, block.text)
                        if urls:
                            linkedin_url = urls[0]

            if isinstance(msg, ResultMessage):
                result_message = msg

    elapsed = time.time() - start_time

    print(f"\n   Result: {'✅ Found' if linkedin_url else '❌ Not found'}")
    if linkedin_url:
        print(f"   URL: {linkedin_url}")
    print(f"   Cost: ${result_message.total_cost_usd:.4f}")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Budget: {'✅' if result_message.total_cost_usd < 0.01 else '⚠️'}")

    return {
        "test": "linkedin_webfetch",
        "success": linkedin_url is not None,
        "linkedin_url": linkedin_url,
        "cost": result_message.total_cost_usd,
        "time_seconds": round(elapsed, 3),
    }


async def test_simple_enrichment():
    """Test basic enrichment without Hunter.io"""
    print("\n" + "="*70)
    print("TEST: Basic Enrichment (WebFetch Only)")
    print("="*70)
    print("Goal: Find email pattern from company website")

    start_time = time.time()

    options = ClaudeAgentOptions(
        allowed_tools=["WebFetch"],
        disallowed_tools=["WebSearch", "Task", "TodoWrite", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=3,
        model="claude-haiku-4-5",
        system_prompt=(
            f"Use WebFetch to get {TEST_CONTACT['company_website']}. "
            f"Look for contact information or email patterns. "
            f"Guess likely email for {TEST_CONTACT['name']} based on patterns found."
        ),
    )

    email_guess = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Fetch {TEST_CONTACT['company_website']} and infer email pattern for {TEST_CONTACT['name']}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        # Extract email
                        import re
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, block.text)
                        if emails:
                            email_guess = emails[0]

            if isinstance(msg, ResultMessage):
                result_message = msg

    elapsed = time.time() - start_time

    print(f"\n   Result: {'✅ Found' if email_guess else '❌ Not found'}")
    if email_guess:
        print(f"   Email: {email_guess}")
    print(f"   Cost: ${result_message.total_cost_usd:.4f}")
    print(f"   Time: {elapsed:.2f}s")

    return {
        "test": "email_pattern",
        "success": email_guess is not None,
        "email": email_guess,
        "cost": result_message.total_cost_usd,
        "time_seconds": round(elapsed, 3),
    }


async def main():
    print("🎯 Agent 3 Simplified Testing")
    print("="*70)
    print("Focus: Cheap, reliable enrichment")
    print(f"Contact: {TEST_CONTACT['name']}")
    print(f"Company: {TEST_CONTACT['company']}")

    results = {}

    # Test 1: LinkedIn via WebFetch
    results["linkedin"] = await test_websearch_linkedin()

    # Test 2: Email pattern inference
    results["email"] = await test_simple_enrichment()

    # Analysis
    print(f"\n{'='*70}")
    print("📊 RESULTS")
    print(f"{'='*70}\n")

    total_cost = sum(r.get("cost", 0) for r in results.values())
    successful = sum(1 for r in results.values() if r.get("success", False))

    print(f"Successful: {successful}/2")
    print(f"Total Cost: ${total_cost:.4f}")
    print("Budget Target: $0.02")
    print(f"Status: {'✅ Under budget' if total_cost < 0.02 else '⚠️ Over budget'}")

    if results["linkedin"].get("success"):
        print(f"\n✅ LinkedIn URL: {results['linkedin']['linkedin_url']}")

    if results["email"].get("success"):
        print(f"✅ Email: {results['email']['email']}")

    # Save
    with open("../results/agent3_simple_test.json", "w") as f:
        json.dump({
            "contact": TEST_CONTACT,
            "results": results,
            "total_cost": total_cost,
        }, f, indent=2)

    print("\n💾 Saved to: ../results/agent3_simple_test.json")


if __name__ == "__main__":
    anyio.run(main)
