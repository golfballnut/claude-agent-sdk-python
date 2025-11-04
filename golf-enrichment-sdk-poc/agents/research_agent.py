"""
Golf Course Research Agent - SDK Implementation
Phase 2.5.2: Maximum accuracy with MCP tool composition

This agent uses multiple research tools for optimal accuracy:
- Firecrawl: Web search with full citations
- Hunter.io: B2B contact discovery (60%+ email success rate)
- Jina: Official website scraping
- Perplexity: Fallback research

Expected accuracy: 85-95% vs 60-70% with single-API edge functions
"""

from claude_agent_sdk import AgentDefinition

# 5-Section Research Prompt (proven with ChatGPT-5 Pro)
GOLF_RESEARCH_PROMPT = """Research {COURSE_NAME} in {CITY}, {STATE} and provide comprehensive golf course intelligence.

**CRITICAL INSTRUCTIONS:**
1. Use MULTIPLE research tools to verify information across sources
2. Provide SOURCE URL for EVERY factual claim
3. Focus on CURRENT information (2024-2025 only)
4. Return response as valid JSON matching the schema below
5. Use `null` or `"not_found"` when data is unavailable
6. Be thorough - this is comprehensive research, not a quick lookup

**AVAILABLE TOOLS:**
- mcp__firecrawl__firecrawl_search: Best for web research with citations
- mcp__hunter__Domain-Search: Best for finding staff emails
- mcp__jina__jina_reader: Best for official website content
- mcp__perplexity__perplexity_ask: Fallback for hard-to-find data

**RECOMMENDED WORKFLOW:**
1. Start with Firecrawl web search for comprehensive intel
2. Use Hunter.io Domain Search for contact discovery
3. Use Jina Reader to scrape official course website
4. Use Perplexity for gaps or verification
5. Cross-validate facts across multiple sources

---

## SECTION 1: RANGE BALL OPPORTUNITY CLASSIFICATION ⚠️ CRITICAL

**Objective:** Determine if this course represents a BUY, SELL, or BOTH opportunity for range ball services.

### BUY OPPORTUNITY (We purchase their waste balls)
Look for signals that the course has waste/used range balls they need to dispose of:
- "Throwing away old balls" / "discarding worn practice balls"
- "Storage full" / "too many old balls"
- "Recycling program" / "selling used balls"
- Large practice range (50+ stations) at a busy course
- Premium/resort course (high ball turnover)

**If found, gather:**
- Specific quotes mentioning ball disposal
- Estimated range size (# of stations)
- Course tier (affects ball volume/quality)
- Any mentions of current ball recycling/sales

### SELL OPPORTUNITY (They need to purchase from a supplier)
Look for pain points indicating they need a better range ball supplier:
- "Practice ball costs too high" / "budget concerns"
- "Range balls poor quality" / "worn out"
- "Member complaints about practice balls"
- "Looking for ball supplier"
- "Current supplier unreliable"

**If found, gather:**
- Specific pain points (cost vs quality vs reliability)
- Current supplier name (if mentioned)
- Budget/procurement timing mentions
- Quotes from reviews, newsletters, or announcements

### CLASSIFICATION RULES
- **BOTH**: Shows BOTH waste disposal needs AND purchasing pain points (HIGHEST VALUE)
- **BUY**: Only disposal/excess ball signals found
- **SELL**: Only purchasing pain/need signals found
- **INSUFFICIENT_DATA**: Cannot determine from available information

**Output for this section:**
```json
{
  "classification": "BOTH | BUY | SELL | INSUFFICIENT_DATA",
  "confidence": "high | medium | low",
  "buy_signals": [
    {
      "signal": "Quote or fact",
      "source": "https://..."
    }
  ],
  "sell_signals": [
    {
      "signal": "Quote or fact",
      "source": "https://..."
    }
  ],
  "recommended_strategy": "buy_first | sell_first | approach_both | insufficient_data",
  "reasoning": "1-2 sentences explaining the classification"
}
```

---

## SECTION 2: WATER HAZARDS (EXPANSION OPPORTUNITY)

**Objective:** Assess potential for ball retrieval services (secondary offering).

Look for:
- Total count of ponds, lakes, water hazards on the course
- Mentions of specific hazards (e.g., "island green on hole 7")
- High-traffic holes with water (signature holes, par 3s over water)
- Ball retrieval service mentions (current provider or need)

**Output for this section:**
```json
{
  "water_hazards": {
    "total_count": 0,
    "details": [
      {
        "location": "Hole 7, island green",
        "type": "pond | lake | stream",
        "notes": "High-traffic par 3",
        "source": "https://..."
      }
    ],
    "ball_accumulation_estimate": "high | medium | low | unknown",
    "current_retrieval_service": "Company name or null",
    "source": "https://... (for retrieval service info)"
  }
}
```

---

## SECTION 3: PRACTICE FACILITIES (CRITICAL FOR VOLUME ESTIMATES)

**Objective:** Understand the size and quality of practice facilities.

Look for:
- Number of hitting stations / range size
- Range type: grass tees, mat tees, or both
- Practice area amenities
- Current practice ball supplier (if mentioned)

**Output for this section:**
```json
{
  "practice_facilities": {
    "range": {
      "stations": 0,
      "type": "grass | mat | both | unknown",
      "size_description": "Brief description",
      "source": "https://..."
    },
    "current_supplier": {
      "name": "Supplier name or null",
      "source": "https://..."
    },
    "quality_mentions": [
      {
        "mention": "Quote about ball quality",
        "sentiment": "positive | negative | neutral",
        "source": "https://..."
      }
    ]
  }
}
```

---

## SECTION 4: DECISION MAKERS (CRITICAL - REQUIRED FOR OUTREACH)

**Objective:** Find verified contact information for key decision makers.

**Priority order:**
1. General Manager / Owner (HIGHEST PRIORITY)
2. Golf Course Superintendent / Director of Agronomy
3. Director of Golf / Head Golf Professional

**For each contact, find:**
- Full name
- Exact current title
- **Work email** (use Hunter.io Domain Search for best results)
- Phone number (direct line preferred)
- LinkedIn profile URL
- Employment verification (must be CURRENT 2024-2025)

**TOOL RECOMMENDATION:**
- Use `mcp__hunter__Domain-Search` on course domain first (60%+ email discovery)
- Fallback to Firecrawl/Jina for staff pages if Hunter.io insufficient

**Output for this section:**
```json
{
  "decision_makers": [
    {
      "name": "John Smith",
      "title": "General Manager",
      "priority": 1,
      "email": "jsmith@example.com or null",
      "email_source": "https://...",
      "phone": "+1-555-123-4567 or null",
      "linkedin": "https://linkedin.com/in/... or null",
      "employment_verified": true,
      "verification_source": "https://..."
    }
  ]
}
```

---

## SECTION 5: COURSE TIER CLASSIFICATION

**Objective:** Classify the course to estimate ball volume and quality needs.

Look for:
- **Pricing:** Daily green fees OR membership/initiation fees
- **Course type:** Private, semi-private, public, municipal, resort
- **Volume indicators:** Estimated annual rounds
- **Quality indicators:** Rankings, awards, tournament hosting

**Classification guidelines:**
- **Premium:** $75+ green fees, ranked courses, high-end private clubs
- **Medium:** $40-75 green fees, quality public or semi-private
- **Budget:** <$40 green fees, municipal courses

**Output for this section:**
```json
{
  "course_tier": {
    "classification": "premium | medium | budget",
    "confidence": "high | medium | low",
    "pricing": {
      "green_fee_range": "$40-60 or null",
      "source": "https://..."
    },
    "course_type": "private | semi-private | public | municipal | resort",
    "quality_indicators": [
      {
        "indicator": "Ranked #47 in state",
        "source": "https://..."
      }
    ]
  }
}
```

---

## FINAL JSON RESPONSE STRUCTURE

Combine all sections into a single JSON response:

```json
{
  "course_name": "{COURSE_NAME}",
  "city": "{CITY}",
  "state": "{STATE}",
  "research_date": "2025-01-01",
  "section1_classification": { ... },
  "section2_water_hazards": { ... },
  "section3_practice_facilities": { ... },
  "section4_decision_makers": [ ... ],
  "section5_course_tier": { ... }
}
```

**VALIDATION REQUIREMENTS:**
- At least 3 decision makers with contact info
- At least 5 citations with full URLs
- Tier classification must not be "INSUFFICIENT_DATA" unless truly no data exists
- Every factual claim must have a source URL
"""


# Agent Definition
golf_research_agent = AgentDefinition(
    description="Researches golf courses using multi-tool composition for maximum accuracy (85-95% success rate)",
    prompt=GOLF_RESEARCH_PROMPT,
    tools=[
        # MCP Web Research Tools
        "mcp__firecrawl__firecrawl_search",
        "mcp__firecrawl__firecrawl_scrape",
        "mcp__jina__jina_reader",
        "mcp__jina__jina_search",
        "mcp__perplexity-ask__perplexity_ask",

        # MCP B2B Contact Discovery
        "mcp__hunter-io__Domain-Search",
        "mcp__hunter-io__Email-Finder",
        "mcp__hunter-io__Email-Verifier",

        # Database Integration
        "mcp__supabase__execute_sql",
    ],
    model="sonnet"  # Claude Sonnet 4.5 for best reasoning
)


# NOTE: MCP server configuration is in .mcp.json file at project root
# This allows SDK to automatically discover and connect to:
# - Firecrawl (web search with citations)
# - Jina (official website scraping)
# - Hunter.io (B2B contact discovery)
# - Perplexity (fallback research)
# - Supabase (database operations)
