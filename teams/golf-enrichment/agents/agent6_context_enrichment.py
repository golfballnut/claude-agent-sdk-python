#!/usr/bin/env python3
"""
Agent 6: Business Intelligence (Range Ball Reconditioning)
Gathers actionable business intelligence for range ball program targeting

Target Performance:
- Segmentation Accuracy: 80%+ (high-end vs budget classification)
- Opportunity Scoring: 6 opportunity types (1-10 scale)
- Cost: ~$0.015/contact (3 Perplexity API queries)
- Speed: ~20s per contact

Pattern:
- Direct Perplexity API (like Agent 5 proven pattern)
- Custom tool with 3 business-specific queries
- Segmentation logic (high-end vs budget)
- Opportunity scoring (buy/sell/lease programs)
- Value-prop specific conversation starters
- SDK MCP server (in-process)
- Sonnet 4.5 model (better instruction following)

Business Context:
- ONLY company worldwide that can clean + add protective coating to range balls
- High-end clubs: Buy their used balls (they throw away)
- Budget clubs: Sell reconditioned balls at 40-60% discount
- Lease program: 6-month swap cycle for all clubs
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

@tool("gather_business_intel", "Gather range ball business intelligence", {
    "company": str,
    "title": str,
    "name": str
})
async def gather_business_intel_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Gather business intelligence via 3 Perplexity API queries:
    1. Company reviews + range ball signals
    2. Industry pain points (role-specific)
    3. Competitive positioning

    Returns combined intelligence for segmentation + opportunity scoring
    """
    import httpx

    company = args["company"]
    title = args["title"]
    name = args["name"]

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
    # QUERY 1: Company Reviews + Range Ball Signals
    # ========================================================================
    query1 = f"""Find information about {company} golf course:
- Does it have a practice range or driving range?
- What are the Google reviews and ratings?
- Are there member complaints about range ball quality?
- Is it positioned as premium/private or public/affordable?
- Any mentions of budget constraints or cost-cutting?
- Any sustainability or environmental initiatives?
- Recent facility upgrades or renovations?"""

    company_intel = {}

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
                    "messages": [{"role": "user", "content": query1}]
                }
            )
            data = r.json()

            if data.get("choices"):
                company_intel["raw_response"] = data["choices"][0]["message"]["content"]
                print(f"   ✓ Query 1: Company intel gathered")
    except Exception as e:
        print(f"   ✗ Query 1 failed: {e}")
        company_intel["raw_response"] = ""

    # ========================================================================
    # QUERY 2: Industry Pain Points (Role-Specific)
    # ========================================================================
    query2 = f"""What are the biggest challenges for a {title} in golf course management in 2024-2025?
Focus on:
- Range ball costs and management
- Practice facility maintenance
- Budget pressures for consumables
- Member satisfaction with practice facilities
- Waste disposal and sustainability concerns"""

    industry_intel = {}

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
                    "messages": [{"role": "user", "content": query2}]
                }
            )
            data = r.json()

            if data.get("choices"):
                industry_intel["raw_response"] = data["choices"][0]["message"]["content"]
                print(f"   ✓ Query 2: Industry pain points gathered")
    except Exception as e:
        print(f"   ✗ Query 2 failed: {e}")
        industry_intel["raw_response"] = ""

    # ========================================================================
    # QUERY 3: Competitive Positioning
    # ========================================================================
    query3 = f"""Research {company} golf course:
- Is it a private club or public course?
- How is it positioned in the market (premium vs budget)?
- What are similar/competing courses in the area?
- What is its reputation and market positioning?"""

    competitive_intel = {}

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
                    "messages": [{"role": "user", "content": query3}]
                }
            )
            data = r.json()

            if data.get("choices"):
                competitive_intel["raw_response"] = data["choices"][0]["message"]["content"]
                print(f"   ✓ Query 3: Competitive positioning gathered")
    except Exception as e:
        print(f"   ✗ Query 3 failed: {e}")
        competitive_intel["raw_response"] = ""

    # Combine all intelligence
    combined_intel = {
        "company_intel": company_intel.get("raw_response", ""),
        "industry_intel": industry_intel.get("raw_response", ""),
        "competitive_intel": competitive_intel.get("raw_response", "")
    }

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(combined_intel)
        }]
    }


# ============================================================================
# AGENT FUNCTION
# ============================================================================

async def enrich_context(contact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich contact with business intelligence for range ball targeting

    Args:
        contact: Dict with name, title, company, domain

    Returns:
        Dict with segmentation, opportunity scores, and conversation starters
    """

    server = create_sdk_mcp_server("business_intel", tools=[gather_business_intel_tool])

    name = contact.get("name", "Unknown")
    title = contact.get("title", "Unknown")
    company = contact.get("company", "Unknown")
    domain = contact.get("domain", "unknown.com")

    # Build analysis prompt (after data gathered)
    prompt = f"""
Use the gather_business_intel tool to fetch intelligence about {company}.

After receiving the intelligence data, analyze it and generate business intelligence for range ball targeting.

**BUSINESS CONTEXT:**
- We are the ONLY company worldwide that can clean + add protective coating to used range balls
- High-End Clubs: We BUY their used range balls (they currently throw away)
- Budget Clubs: We SELL reconditioned balls at 40-60% discount vs new
- Lease Program: 6-month swap cycle for all clubs (always fresh inventory)

**CONTACT INFORMATION:**
- Company: {company}
- Contact: {name}, {title}

**TASK:**
The gather_business_intel tool will return 3 types of intelligence. Analyze and create business intel.

**AFTER RECEIVING DATA:**

1. **SEGMENTATION** - Classify as high-end, budget, or both:

**High-End Indicators:**
- Private/exclusive/premium positioning
- Ratings 4.5+ stars
- Recent renovations/upgrades ($ indicates capital)
- Member complaints about ball quality (they discard worn balls)
- "Expensive" or pricing complaints
- Competes with other high-end clubs

**Budget Indicators:**
- Public/affordable/value positioning
- Ratings 3.5-4.5 stars
- "Good value" or "reasonable prices" in reviews
- Cost-cutting or budget constraint mentions
- Older facilities without recent major upgrades
- No practice range or small facility

2. **OPPORTUNITY SCORING** (1-10 for each):

- **range_ball_buy** (High-end clubs): Do they have a range? Are they high-end? Quality complaints?
- **range_ball_sell** (Budget clubs): Budget signals? Public course? Cost concerns?
- **range_ball_lease** (All): Have a range? Member satisfaction focus? Capital constraints?
- **proshop_ecommerce** (Future): Pro shop mentioned? Online ordering capability?
- **superintendent_partnership** (Future): Large maintenance team? Staff programs?
- **ball_retrieval** (Core): Water hazards? Ponds? Lakes mentioned?

3. **CONVERSATION STARTERS** - Generate 5-7 value-prop specific openers:

**For High-End (range_ball_buy):**
- "Are you currently disposing of used range balls once they show wear?"
- "We're the only company that can recondition your used balls to like-new quality - turn waste into revenue"
- "Many premium clubs are exploring range ball recycling to reduce waste while maintaining member expectations"

**For Budget (range_ball_sell):**
- "Budget pressures are affecting every club - have you explored alternatives to buying new range balls?"
- "We provide reconditioned range balls at half the cost of new, with quality members can't tell apart"
- "Maintain practice facility quality while controlling costs"

**For Lease (All):**
- "Interested in a range ball subscription where you always have fresh inventory?"
- "Eliminate the hassle of tracking ball wear - we swap them every 6 months"
- "No upfront investment, predictable monthly cost, always happy members"

**OUTPUT FORMAT** (pure JSON, no markdown, no code blocks):
{{
  "segmentation": {{
    "primary_target": "high-end" | "budget" | "both" | "unknown",
    "confidence": 1-10,
    "signals": ["specific indicator 1", "specific indicator 2", ...]
  }},
  "range_intel": {{
    "has_range": true | false | "unknown",
    "volume_signals": ["large facility", "200+ capacity", etc.],
    "quality_complaints": ["worn balls mentioned", "member feedback", etc.],
    "budget_signals": ["cost-cutting", "affordable", etc.],
    "sustainability_signals": ["waste reduction", "environmental", etc.]
  }},
  "opportunities": {{
    "range_ball_buy": 1-10,
    "range_ball_sell": 1-10,
    "range_ball_lease": 1-10,
    "proshop_ecommerce": 1-10,
    "superintendent_partnership": 1-10,
    "ball_retrieval": 1-10
  }},
  "conversation_starters": [
    {{
      "text": "conversation starter text",
      "value_prop": "range_ball_buy|range_ball_sell|range_ball_lease|other",
      "relevance": 1-10
    }}
  ]
}}

**CRITICAL:**
- Return ONLY the JSON object (no markdown, no code blocks, no explanations)
- Base segmentation on EVIDENCE from intelligence data (not assumptions)
- Score opportunities conservatively (only 9-10 if strong evidence)
- Generate 5-7 conversation starters ranked by relevance
"""

    # Configure agent with custom tool + Sonnet
    options = ClaudeAgentOptions(
        mcp_servers={"business_intel": server},
        allowed_tools=["mcp__business_intel__gather_business_intel"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=5,  # Tool call + analysis
        model="claude-sonnet-4-5",  # Sonnet for better JSON compliance
        system_prompt=(
            "You are a business intelligence API that returns ONLY pure JSON. "
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
                        # Use utility function for robust JSON extraction
                        enrichment = extract_json_from_text(block.text, required_field="segmentation")

                        if not enrichment:
                            print(f"   ⚠️ No valid JSON found in response")
                            print(f"   First 500 chars: {block.text[:500]}...")

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Build result
    result = contact.copy()

    if enrichment and isinstance(enrichment, dict) and "segmentation" in enrichment:
        result["business_intel"] = enrichment

        # Calculate metrics
        segmentation = enrichment.get("segmentation", {})
        opportunities = enrichment.get("opportunities", {})
        starters = enrichment.get("conversation_starters", [])

        result["_agent6_primary_target"] = segmentation.get("primary_target", "unknown")
        result["_agent6_confidence"] = segmentation.get("confidence", 0)
        result["_agent6_starters_count"] = len(starters)

        # Calculate top 2 opportunities
        if opportunities:
            sorted_opps = sorted(opportunities.items(), key=lambda x: x[1], reverse=True)
            result["_agent6_top_opportunities"] = [
                {"type": opp[0], "score": opp[1]} for opp in sorted_opps[:2]
            ]
        else:
            result["_agent6_top_opportunities"] = []

        # Average conversation starter relevance
        if starters:
            avg_relevance = sum(s.get("relevance", 0) for s in starters) / len(starters)
            result["_agent6_avg_relevance"] = round(avg_relevance, 1)
        else:
            result["_agent6_avg_relevance"] = 0

    else:
        # Failed to get proper business intel
        result["business_intel"] = None
        result["_agent6_primary_target"] = "unknown"
        result["_agent6_confidence"] = 0
        result["_agent6_starters_count"] = 0
        result["_agent6_top_opportunities"] = []
        result["_agent6_avg_relevance"] = 0

    result["_agent6_cost"] = result_message.total_cost_usd if result_message else None
    result["_agent6_turns"] = result_message.num_turns if result_message else None

    return result


async def enrich_contacts(contacts: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Enrich multiple contacts with business intelligence

    Args:
        contacts: List of contact dicts (name, title, company, domain)

    Returns:
        List of enriched contacts with business intel
    """
    enriched = []

    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{len(contacts)}] {contact.get('name', 'Unknown')}")
        print(f"   {contact.get('title', 'Unknown')} @ {contact.get('company', 'Unknown')}")

        try:
            result = await enrich_context(contact)

            target = result.get("_agent6_primary_target", "unknown")
            confidence = result.get("_agent6_confidence", 0)
            starters_count = result.get("_agent6_starters_count", 0)
            top_opps = result.get("_agent6_top_opportunities", [])
            cost = result.get("_agent6_cost", 0)

            if target != "unknown" and starters_count >= 5:
                print(f"   ✅ Target: {target.upper()} ({confidence}/10 confidence)")
            else:
                print(f"   ⚠️  Target: {target} ({confidence}/10 confidence)")

            if top_opps:
                print(f"   🎯 Top Opportunities:")
                for opp in top_opps:
                    print(f"      - {opp['type']}: {opp['score']}/10")

            print(f"   💬 Starters: {starters_count}")
            print(f"   💰 Cost: ${cost:.4f}")

            enriched.append(result)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_contact = contact.copy()
            error_contact["_agent6_error"] = str(e)
            enriched.append(error_contact)

    return enriched


async def main():
    """Demo: Enrich test contact with business intelligence"""
    print("🎯 Agent 6: Business Intelligence (Range Ball)")
    print("="*70)

    test_contact = {
        "name": "Stacy Foster",
        "title": "General Manager",
        "company": "Richmond Country Club",
        "domain": "richmondcountryclubva.com"
    }

    print(f"Contact: {test_contact['name']}")
    print(f"Title: {test_contact['title']}")
    print(f"Company: {test_contact['company']}\n")

    result = await enrich_context(test_contact)

    print(f"\n📊 Results:")
    print(f"   Target: {result.get('_agent6_primary_target', 'unknown').upper()}")
    print(f"   Confidence: {result.get('_agent6_confidence', 0)}/10")
    print(f"   Conversation Starters: {result.get('_agent6_starters_count', 0)}")
    print(f"   Avg Relevance: {result.get('_agent6_avg_relevance', 0)}/10")
    print(f"   Cost: ${result.get('_agent6_cost', 0):.4f}")

    # Print top opportunities
    top_opps = result.get("_agent6_top_opportunities", [])
    if top_opps:
        print(f"\n🎯 Top Opportunities:")
        for opp in top_opps:
            print(f"   {opp['type']}: {opp['score']}/10")

    # Print top 3 conversation starters
    intel = result.get("business_intel", {})
    if intel:
        starters = intel.get("conversation_starters", [])
        if starters:
            print(f"\n💬 Top Conversation Starters:")
            for i, starter in enumerate(starters[:3], 1):
                text = starter.get("text", "")
                value_prop = starter.get("value_prop", "unknown")
                score = starter.get("relevance", 0)
                # Truncate if too long
                display_text = text[:100] + "..." if len(text) > 100 else text
                print(f"   {i}. [{score}/10] {display_text}")
                print(f"      Value Prop: {value_prop}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
