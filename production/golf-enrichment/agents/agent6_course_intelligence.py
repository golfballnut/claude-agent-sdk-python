#!/usr/bin/env python3
"""
Agent 6: Course-Level Business Intelligence
Gathers business intelligence for the ENTIRE course (run ONCE, not per contact)

Target Performance:
- Cost: ~$0.010/course (2 Perplexity queries, not 3×contacts)
- Speed: ~15s per course
- Accuracy: 80%+ segmentation

Pattern:
- Direct Perplexity API
- 2 business-specific queries (company + competitive)
- Course-level segmentation and opportunity scoring
- NO conversation starters (sales team crafts these)
- SDK MCP server (in-process)
- Sonnet 4.5 model

Business Context:
- ONLY company worldwide that can clean + add protective coating to range balls
- High-end clubs: Buy their used balls (they currently throw away)
- Budget clubs: Sell reconditioned balls at 40-60% discount
- Lease program: 6-month swap cycle for all clubs
"""

import anyio
import json
import re
from typing import Any, Dict, Optional
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

@tool("gather_course_intel", "Gather course-level business intelligence", {
    "company": str,
    "website": str,
    "water_hazard_count": int
})
async def gather_course_intel_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Gather course-level business intelligence via 2 Perplexity API queries:
    1. Company reviews + range ball signals
    2. Competitive positioning

    Returns combined intelligence for segmentation + opportunity scoring
    """
    import httpx

    company = args["company"]
    website = args.get("website", "")
    water_hazard_count = args.get("water_hazard_count", 0)

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
- Recent facility upgrades or renovations?
- Practice facility details (size, bucket pricing, etc.)?"""

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
    # QUERY 2: Competitive Positioning
    # ========================================================================
    query2 = f"""Research {company} golf course:
- Is it a private club or public course?
- How is it positioned in the market (premium vs budget)?
- What are similar/competing courses in the area?
- What is its reputation and market positioning?
- Price range compared to area courses?"""

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
                    "messages": [{"role": "user", "content": query2}]
                }
            )
            data = r.json()

            if data.get("choices"):
                competitive_intel["raw_response"] = data["choices"][0]["message"]["content"]
                print(f"   ✓ Query 2: Competitive positioning gathered")
    except Exception as e:
        print(f"   ✗ Query 2 failed: {e}")
        competitive_intel["raw_response"] = ""

    # Combine all intelligence
    combined_intel = {
        "company_intel": company_intel.get("raw_response", ""),
        "competitive_intel": competitive_intel.get("raw_response", ""),
        "water_hazard_count": water_hazard_count
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

async def enrich_course(
    course_name: str,
    website: str,
    water_hazard_count: Optional[int] = 0
) -> Dict[str, Any]:
    """
    Enrich course with business intelligence (run ONCE per course)

    Args:
        course_name: Golf course name
        website: Course website URL
        water_hazard_count: Number of water hazards (from Agent 7)

    Returns:
        Dict with segmentation, range_intel, opportunity scores
    """

    server = create_sdk_mcp_server("course_intel", tools=[gather_course_intel_tool])

    # Build analysis prompt
    prompt = f"""
Use the gather_course_intel tool to fetch intelligence about {course_name}.

After receiving the intelligence data, analyze it and generate course-level business intelligence.

**BUSINESS CONTEXT:**
- We are the ONLY company worldwide that can clean + add protective coating to used range balls
- High-End Clubs: We BUY their used range balls (they currently throw away)
- Budget Clubs: We SELL reconditioned balls at 40-60% discount vs new
- Lease Program: 6-month swap cycle for all clubs (always fresh inventory)
- Ball Retrieval: We recover balls from water hazards (water_hazard_count: {water_hazard_count})

**TASK:**
The gather_course_intel tool will return intelligence. Analyze and create course-level business intel.

**AFTER RECEIVING DATA:**

1. **SEGMENTATION** - Classify course as high-end, budget, or both:

**High-End Indicators:**
- Private/exclusive/premium positioning
- Ratings 4.5+ stars
- Recent renovations/upgrades
- Member complaints about quality (they discard worn balls)
- "Expensive" or pricing complaints
- Competes with other high-end clubs

**Budget Indicators:**
- Public/affordable/value positioning
- Ratings 3.5-4.5 stars
- "Good value" or "reasonable prices" in reviews
- Cost-cutting or budget constraint mentions
- Older facilities without recent major upgrades

2. **OPPORTUNITY SCORING** (1-10 for each, course-level):

- **range_ball_buy** (High-end): Has range? High-end? Quality focus?
- **range_ball_sell** (Budget): Budget signals? Public? Cost concerns?
- **range_ball_lease** (All): Has range? Predictable costs? Capital constraints?
- **proshop_ecommerce** (Future): Pro shop mentioned?
- **superintendent_partnership** (Future): Large facility? Staff programs?
- **ball_retrieval**: Use water_hazard_count ({water_hazard_count} hazards):
  - 15+ hazards = 10/10 (premium opportunity)
  - 10-14 hazards = 8/10 (high opportunity)
  - 5-9 hazards = 6/10 (moderate opportunity)
  - 1-4 hazards = 3/10 (low opportunity)
  - 0 hazards = 1/10 (minimal opportunity)

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
  }}
}}

**CRITICAL:**
- Return ONLY the JSON object (no markdown, no code blocks, no explanations)
- Base segmentation on EVIDENCE from intelligence data
- Score opportunities conservatively (only 9-10 if strong evidence)
- Use water_hazard_count for ball_retrieval scoring
"""

    # Configure agent
    options = ClaudeAgentOptions(
        mcp_servers={"course_intel": server},
        allowed_tools=["mcp__course_intel__gather_course_intel"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=3,
        model="claude-sonnet-4-5",
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
                        enrichment = extract_json_from_text(block.text, required_field="segmentation")

                        if not enrichment:
                            print(f"   ⚠️ No valid JSON found in response")

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Build result
    result = {
        "segmentation": None,
        "range_intel": None,
        "opportunities": None,
        "cost": result_message.total_cost_usd if result_message else None,
        "turns": result_message.num_turns if result_message else None
    }

    if enrichment and isinstance(enrichment, dict) and "segmentation" in enrichment:
        result["segmentation"] = enrichment.get("segmentation")
        result["range_intel"] = enrichment.get("range_intel")
        result["opportunities"] = enrichment.get("opportunities")

    return result


async def main():
    """Demo: Enrich course with business intelligence"""
    print("🎯 Agent 6: Course-Level Business Intelligence")
    print("="*70)

    test_course = "Richmond Country Club"
    test_website = "https://www.richmondcountryclubva.com/"
    test_water_hazards = 7

    print(f"Course: {test_course}")
    print(f"Website: {test_website}")
    print(f"Water Hazards: {test_water_hazards}\n")

    result = await enrich_course(test_course, test_website, test_water_hazards)

    print(f"\n📊 Results:")

    seg = result.get("segmentation", {})
    if seg:
        print(f"   Segment: {seg.get('primary_target', 'unknown').upper()}")
        print(f"   Confidence: {seg.get('confidence', 0)}/10")

    range_intel = result.get("range_intel", {})
    if range_intel:
        print(f"   Has Range: {range_intel.get('has_range', 'unknown')}")

    opps = result.get("opportunities", {})
    if opps:
        print(f"\n🎯 Top Opportunities:")
        sorted_opps = sorted(opps.items(), key=lambda x: x[1], reverse=True)
        for opp, score in sorted_opps[:3]:
            print(f"      {opp}: {score}/10")

    print(f"\n💰 Cost: ${result.get('cost', 0):.4f}")
    print(f"⏱️  Turns: {result.get('turns', 0)}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
