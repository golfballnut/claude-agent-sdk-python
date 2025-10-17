#!/usr/bin/env python3
"""
Agent 3 Capability Testing Framework

Tests each enrichment capability independently:
- Email finding (Hunter.io)
- Email verification (Hunter.io)
- LinkedIn URL discovery (WebSearch / Hunter.io)
- LinkedIn profile scraping (Firecrawl / BrightData)
- Phone enrichment
"""

import json
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
)

# Test data from Agent 2 results (Stacy Foster)
TEST_CONTACT = {
    "name": "Stacy Foster",
    "title": "General Manager",
    "company": "Richmond Country Club",
    "company_website": "https://www.richmondcountryclubva.com/",
    "company_domain": "richmondcountryclubva.com"
}


# ============================================================================
# TEST A: Email Finding (Hunter.io)
# ============================================================================

async def test_email_finding() -> dict[str, Any]:
    """Test Hunter.io Email Finder"""
    print("\n" + "="*70)
    print("TEST A: Email Finding (Hunter.io)")
    print("="*70)

    start_time = time.time()

    options = ClaudeAgentOptions(
        allowed_tools=["mcp__hunter-io__Email-Finder"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            f"Use Email-Finder to find the email address for {TEST_CONTACT['name']} "
            f"at {TEST_CONTACT['company_domain']}. Return only the email address."
        ),
    )

    found_email = None
    result_message = None
    tools_used = []

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(
                f"Find email for {TEST_CONTACT['name']} at {TEST_CONTACT['company_domain']}"
            )

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                        elif isinstance(block, TextBlock):
                            # Extract email from response
                            import re
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            emails = re.findall(email_pattern, block.text)
                            if emails:
                                found_email = emails[0]

                if isinstance(msg, ResultMessage):
                    result_message = msg

        elapsed = time.time() - start_time

        result = {
            "test": "email_finding",
            "success": found_email is not None,
            "email": found_email,
            "cost": result_message.total_cost_usd if result_message else None,
            "time_seconds": round(elapsed, 3),
            "turns": result_message.num_turns if result_message else None,
            "tools_used": tools_used,
        }

        print(f"\n   Result: {'✅ Found' if found_email else '❌ Not found'}")
        if found_email:
            print(f"   Email: {found_email}")
        print(f"   Cost: ${result['cost']:.4f}" if result['cost'] else "   Cost: N/A")
        print(f"   Time: {elapsed:.2f}s")

        return result

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "test": "email_finding",
            "success": False,
            "error": str(e),
        }


# ============================================================================
# TEST B: Email Verification (Hunter.io)
# ============================================================================

async def test_email_verification(email: str) -> dict[str, Any]:
    """Test Hunter.io Email Verifier"""
    print("\n" + "="*70)
    print("TEST B: Email Verification (Hunter.io)")
    print("="*70)

    if not email:
        print("   ⚠️  Skipping - no email to verify")
        return {"test": "email_verification", "success": False, "skipped": True}

    start_time = time.time()

    options = ClaudeAgentOptions(
        allowed_tools=["mcp__hunter-io__Email-Verifier"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=f"Use Email-Verifier to check deliverability of {email}. Return the status.",
    )

    verification_result = None
    result_message = None
    tools_used = []

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(f"Verify email: {email}")

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                        elif isinstance(block, TextBlock):
                            verification_result = block.text

                if isinstance(msg, ResultMessage):
                    result_message = msg

        elapsed = time.time() - start_time

        result = {
            "test": "email_verification",
            "success": True,
            "verification": verification_result,
            "cost": result_message.total_cost_usd if result_message else None,
            "time_seconds": round(elapsed, 3),
            "turns": result_message.num_turns if result_message else None,
            "tools_used": tools_used,
        }

        print("\n   Result: ✅ Verified")
        print(f"   Status: {verification_result[:100] if verification_result else 'N/A'}...")
        print(f"   Cost: ${result['cost']:.4f}" if result['cost'] else "   Cost: N/A")
        print(f"   Time: {elapsed:.2f}s")

        return result

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "test": "email_verification",
            "success": False,
            "error": str(e),
        }


# ============================================================================
# TEST C: LinkedIn URL Discovery
# ============================================================================

async def test_linkedin_discovery() -> dict[str, Any]:
    """Test LinkedIn URL finding with WebSearch"""
    print("\n" + "="*70)
    print("TEST C: LinkedIn URL Discovery (WebSearch)")
    print("="*70)

    start_time = time.time()

    options = ClaudeAgentOptions(
        allowed_tools=["WebSearch"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            f"Search for the LinkedIn profile of {TEST_CONTACT['name']}, "
            f"{TEST_CONTACT['title']} at {TEST_CONTACT['company']}. "
            f"Return only the LinkedIn URL (https://linkedin.com/in/...)."
        ),
    )

    linkedin_url = None
    result_message = None
    tools_used = []

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(
                f"Find LinkedIn profile for {TEST_CONTACT['name']} {TEST_CONTACT['title']} {TEST_CONTACT['company']}"
            )

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                        elif isinstance(block, TextBlock):
                            # Extract LinkedIn URL
                            import re
                            linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
                            urls = re.findall(linkedin_pattern, block.text)
                            if urls:
                                linkedin_url = urls[0]

                if isinstance(msg, ResultMessage):
                    result_message = msg

        elapsed = time.time() - start_time

        result = {
            "test": "linkedin_discovery",
            "success": linkedin_url is not None,
            "linkedin_url": linkedin_url,
            "cost": result_message.total_cost_usd if result_message else None,
            "time_seconds": round(elapsed, 3),
            "turns": result_message.num_turns if result_message else None,
            "tools_used": tools_used,
        }

        print(f"\n   Result: {'✅ Found' if linkedin_url else '❌ Not found'}")
        if linkedin_url:
            print(f"   URL: {linkedin_url}")
        print(f"   Cost: ${result['cost']:.4f}" if result['cost'] else "   Cost: N/A")
        print(f"   Time: {elapsed:.2f}s")

        return result

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "test": "linkedin_discovery",
            "success": False,
            "error": str(e),
        }


# ============================================================================
# TEST D: LinkedIn Profile Scraping
# ============================================================================

async def test_linkedin_scraping(linkedin_url: str) -> dict[str, Any]:
    """Test LinkedIn profile scraping with Firecrawl"""
    print("\n" + "="*70)
    print("TEST D: LinkedIn Profile Scraping (Firecrawl)")
    print("="*70)

    if not linkedin_url:
        print("   ⚠️  Skipping - no LinkedIn URL to scrape")
        return {"test": "linkedin_scraping", "success": False, "skipped": True}

    start_time = time.time()

    options = ClaudeAgentOptions(
        allowed_tools=["mcp__firecrawl__firecrawl_scrape"],
        permission_mode="bypassPermissions",
        max_turns=3,
        model="claude-haiku-4-5",
        system_prompt=(
            f"Scrape {linkedin_url} and extract job history. "
            f"Return JSON array of jobs with: title, company, dates."
        ),
    )

    job_history = None
    result_message = None
    tools_used = []

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(f"Scrape LinkedIn profile: {linkedin_url}")

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                        elif isinstance(block, TextBlock):
                            # Try to parse JSON job history
                            import re
                            json_match = re.search(r'\[.*\]', block.text, re.DOTALL)
                            if json_match:
                                try:
                                    job_history = json.loads(json_match.group(0))
                                except json.JSONDecodeError:
                                    pass

                if isinstance(msg, ResultMessage):
                    result_message = msg

        elapsed = time.time() - start_time

        result = {
            "test": "linkedin_scraping",
            "success": job_history is not None and len(job_history) > 0,
            "job_history": job_history,
            "cost": result_message.total_cost_usd if result_message else None,
            "time_seconds": round(elapsed, 3),
            "turns": result_message.num_turns if result_message else None,
            "tools_used": tools_used,
        }

        print(f"\n   Result: {'✅ Found' if job_history else '❌ Not found'}")
        if job_history:
            print(f"   Jobs: {len(job_history)}")
        print(f"   Cost: ${result['cost']:.4f}" if result['cost'] else "   Cost: N/A")
        print(f"   Time: {elapsed:.2f}s")

        return result

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "test": "linkedin_scraping",
            "success": False,
            "error": str(e),
        }


# ============================================================================
# TEST E: Phone Enrichment
# ============================================================================

async def test_phone_enrichment(email: str) -> dict[str, Any]:
    """Test phone finding via Hunter.io Email Enrichment"""
    print("\n" + "="*70)
    print("TEST E: Phone Enrichment (Hunter.io)")
    print("="*70)

    if not email:
        print("   ⚠️  Skipping - no email for enrichment")
        return {"test": "phone_enrichment", "success": False, "skipped": True}

    start_time = time.time()

    options = ClaudeAgentOptions(
        allowed_tools=["mcp__hunter-io__Email-Enrichment"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=f"Use Email-Enrichment on {email}. Extract phone number if available.",
    )

    phone_number = None
    enrichment_data = None
    result_message = None
    tools_used = []

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(f"Enrich email: {email}")

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                        elif isinstance(block, TextBlock):
                            enrichment_data = block.text
                            # Try to extract phone number
                            import re
                            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                            phones = re.findall(phone_pattern, block.text)
                            if phones:
                                phone_number = phones[0]

                if isinstance(msg, ResultMessage):
                    result_message = msg

        elapsed = time.time() - start_time

        result = {
            "test": "phone_enrichment",
            "success": phone_number is not None,
            "phone": phone_number,
            "enrichment_data": enrichment_data,
            "cost": result_message.total_cost_usd if result_message else None,
            "time_seconds": round(elapsed, 3),
            "turns": result_message.num_turns if result_message else None,
            "tools_used": tools_used,
        }

        print(f"\n   Result: {'✅ Found' if phone_number else '❌ Not found'}")
        if phone_number:
            print(f"   Phone: {phone_number}")
        print(f"   Cost: ${result['cost']:.4f}" if result['cost'] else "   Cost: N/A")
        print(f"   Time: {elapsed:.2f}s")

        return result

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "test": "phone_enrichment",
            "success": False,
            "error": str(e),
        }


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all capability tests"""
    print("🧪 Agent 3 Capability Testing")
    print("="*70)
    print(f"Test Contact: {TEST_CONTACT['name']}")
    print(f"Company: {TEST_CONTACT['company']}")
    print(f"Domain: {TEST_CONTACT['company_domain']}")

    results = {}

    # Test A: Email Finding
    results["email_finding"] = await test_email_finding()
    found_email = results["email_finding"].get("email")

    # Test B: Email Verification
    if found_email:
        results["email_verification"] = await test_email_verification(found_email)

    # Test C: LinkedIn Discovery
    results["linkedin_discovery"] = await test_linkedin_discovery()
    linkedin_url = results["linkedin_discovery"].get("linkedin_url")

    # Test D: LinkedIn Scraping
    if linkedin_url:
        results["linkedin_scraping"] = await test_linkedin_scraping(linkedin_url)

    # Test E: Phone Enrichment
    if found_email:
        results["phone_enrichment"] = await test_phone_enrichment(found_email)

    # ========================================================================
    # ANALYSIS
    # ========================================================================

    print(f"\n{'='*70}")
    print("📊 ANALYSIS")
    print(f"{'='*70}\n")

    total_cost = sum(
        r.get("cost", 0) for r in results.values()
        if r.get("cost") is not None
    )

    successful_tests = sum(
        1 for r in results.values()
        if r.get("success", False)
    )

    print(f"Tests Run: {len(results)}")
    print(f"Successful: {successful_tests}/{len(results)}")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"\nPer-Contact Budget: ${total_cost:.4f} {'✅' if total_cost < 0.02 else '⚠️'}")

    # Architecture recommendation
    print(f"\n{'='*70}")
    print("💡 ARCHITECTURE RECOMMENDATION")
    print(f"{'='*70}\n")

    if total_cost < 0.02 and successful_tests >= 3:
        print("✅ Single Agent 3 - All enrichments in one agent")
        print(f"   Cost: ${total_cost:.4f} (under budget)")
        print(f"   Features: {successful_tests} working capabilities")
    elif total_cost < 0.04:
        print("⚠️  Split into Micro-Agents")
        print(f"   Cost: ${total_cost:.4f} (over single agent budget)")
        print("   Recommend: Agent 3a (email), Agent 3b (LinkedIn)")
    else:
        print("❌ Needs Optimization")
        print(f"   Cost: ${total_cost:.4f} (too expensive)")
        print("   Recommend: Review tool choices, simplify features")

    # Save results
    output = {
        "test_date": "2025-10-16",
        "test_contact": TEST_CONTACT,
        "results": results,
        "total_cost": total_cost,
        "successful_tests": successful_tests,
    }

    output_file = "../results/agent3_capability_test_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Saved to: {output_file}")


if __name__ == "__main__":
    anyio.run(run_all_tests)
