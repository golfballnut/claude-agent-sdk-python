# MCP Context Enrichment Testing Results
**Date:** 2025-01-17
**Test Subject:** Richmond Country Club + Stacy Foster (GM)
**Objective:** Evaluate MCP tools for conversation starters and outreach context

---

## Executive Summary

**Recommendation:** ✅ **BUILD AGENT 6** (with strategic focus)

**High-Value Sources:**
1. ✅ Google Reviews & Sentiment (Perplexity)
2. ✅ Industry Pain Points (Perplexity)
3. ⚠️ Competitive Landscape (Perplexity)

**Skip:**
- ❌ Course-Specific News (Firecrawl)
- ❌ Individual Background Deep Dive (Perplexity)
- ⚠️ LinkedIn Activity (BrightData - paywall issues)

---

## Test Results by Source

### Test 1: Google Reviews & Sentiment ✅ **SUCCESS**
**Tool:** `mcp__perplexity-ask__perplexity_ask`
**Query:** Richmond Country Club reviews, ratings, sentiment

**Data Quality:** 9/10
**Outreach Value:** 8/10
**Est. Cost:** ~$0.005-0.01/query

**Findings:**
- 4.8/5 rating (64 reviews)
- Course condition: 4.6/5 (excellent maintenance)
- Recent clubhouse/bar renovations
- Friendly staff, good value
- **Pain point identified:** Overbooking issues during tournaments

**Conversation Starters:**
- "Congrats on the 4.8 rating - clearly doing something right!"
- "Saw the recent clubhouse renovations - how's that been received?"
- "Noticed some overbooking challenges mentioned - solved that yet?"

---

### Test 2: Recent Course News/Updates ❌ **MISS**
**Tool:** `mcp__firecrawl__firecrawl_search`
**Query:** Richmond Country Club Virginia news tournament renovation 2024 2025

**Data Quality:** 3/10
**Outreach Value:** 2/10
**Est. Cost:** ~$0.01-0.02/search

**Findings:**
- Found news about OTHER Richmond courses (The Crossings, CCV)
- No specific Richmond Country Club news
- General market context only

**Learning:** Generic web searches don't reliably find specific club news. Would need direct site scraping or more targeted approach.

**Recommendation:** SKIP for Agent 6

---

### Test 3: LinkedIn Activity - Stacy Foster ⚠️ **PARTIAL**
**Tool:** `mcp__BrightData__scrape_as_markdown`
**Target:** https://www.linkedin.com/in/stacy-foster-20b79448

**Data Quality:** 4/10
**Outreach Value:** 5/10
**Est. Cost:** ~$0.02-0.05/scrape

**Findings:**
- General Manager since March 2007 (**18+ years tenure!**)
- VCU graduate
- Limited public activity visible
- Login wall blocked most content (no recent posts, engagement details)
- Engagement themes (from visible likes): diversity, leadership, motivation

**Useful Insight:**
- 18+ years tenure = deep institutional knowledge

**Conversation Starter:**
- "18+ years at RCC - you've seen the evolution firsthand!"

**Limitation:** Public LinkedIn profiles heavily restricted without authentication.

**Recommendation:** SKIP for Agent 6 (low ROI vs. cost)

---

### Test 4: Professional Background Deep Dive ❌ **MISS**
**Tool:** `mcp__perplexity-ask__perplexity_ask`
**Query:** Stacy Foster career history, certifications, recognition

**Data Quality:** 2/10
**Outreach Value:** 1/10
**Est. Cost:** ~$0.005-0.01/query

**Findings:**
- Confirmed GM role (already knew from LinkedIn)
- No certifications found
- No previous positions
- No industry recognition
- No additional education details

**Learning:** Generic searches for individual professionals rarely yield deeper info than LinkedIn already provides.

**Recommendation:** SKIP for Agent 6

---

### Test 5: Industry Pain Points ✅ **EXCELLENT**
**Tool:** `mcp__perplexity-ask__perplexity_ask`
**Query:** Golf course GM challenges 2024-2025: staffing, budget, retention, tech

**Data Quality:** 10/10
**Outreach Value:** 9/10
**Est. Cost:** ~$0.005-0.01/query

**Findings:**
- **Acute labor shortages** (agronomy, chefs, all departments)
- **Rising wage pressure** vs. membership fee constraints
- **Member retention challenges** (Millennials/Gen Z expect experiences, not just access)
- **Operational efficiency solutions:** grab-and-go, micro-markets, unmanned systems
- **Technology adoption pressures** (CRM, AI chatbots, digital booking)
- **Sustainability/compliance** requirements

**Universal GM Pain Points:**
1. Can't raise wages high enough without hiking membership fees
2. High turnover after peak summer season
3. Housing costs making it hard for staff to live near facility
4. Balancing traditional service with modern efficiency demands

**Conversation Starters:**
- "Labor shortages hitting you hard too? Agronomy or F&B?"
- "How are you balancing wage increases with membership fee sensitivity?"
- "Explored grab-and-go or micro-markets to reduce labor needs?"
- "Gen Z members pushing for more experience-based programming?"

**Why This Works:** Empathy + relevance. Shows you understand their world.

---

### Test 6: Competitive Landscape ✅ **GOOD**
**Tool:** `mcp__perplexity-ask__perplexity_ask`
**Query:** Best golf courses Richmond VA, RCC comparison, market positioning

**Data Quality:** 7/10
**Outreach Value:** 6/10
**Est. Cost:** ~$0.005-0.01/query

**Findings:**

**Top Competitors:**
- Independence Golf Club (Top 100 VA, two courses, public)
- Royal New Kent (most challenging in VA, Irish links-style)
- The Club at Viniterra (Top 100 VA, winery setting)
- Brickshire Golf Club (inclusive, semi-private)
- Belmont Golf Course (historic Donald Ross design, affordable)

**Richmond Country Club Positioning:**
- **NOT in top-100 public lists** (by design - it's private)
- Positioned as: **Traditional, exclusive, member-focused**
- Competitors emphasize: **Destination appeal, unique features, public access**
- Market positioning: **Exclusivity/tradition vs. experience/amenities**

**Conversation Starter:**
- "Independence and Royal New Kent get a lot of buzz - how do you differentiate your member experience?"

**Why This Works:** Shows you've done homework on their market, respects their positioning.

---

## Cost Analysis

| Test | Tool | Estimated Cost | Worth It? |
|------|------|----------------|-----------|
| Test 1: Reviews | Perplexity | ~$0.01/query | ✅ Yes |
| Test 2: News | Firecrawl | ~$0.02/search | ❌ No |
| Test 3: LinkedIn | BrightData | ~$0.05/scrape | ⚠️ Maybe |
| Test 4: Background | Perplexity | ~$0.01/query | ❌ No |
| Test 5: Pain Points | Perplexity | ~$0.01/query | ✅ YES |
| Test 6: Competitive | Perplexity | ~$0.01/query | ✅ Yes |

**Total Cost Per Lead (3 queries):** ~$0.03
**Value Generated:** High (3-5 actionable conversation starters)

---

## Recommended Agent 6 Architecture

### Core Function
**Context Enrichment Agent** - Fetch conversation starters and pain points for outreach

### MCP Tools to Use
1. ✅ `mcp__perplexity-ask__perplexity_ask` (primary workhorse)
   - Google reviews & sentiment
   - Industry pain points (by role)
   - Competitive landscape

2. ⚠️ `mcp__BrightData__scrape_as_markdown` (optional, use sparingly)
   - Only if specific site scraping needed
   - Not for LinkedIn (paywall issues)

3. ❌ Skip: Firecrawl search (low hit rate for specific clubs)

### Workflow
```
Input: Company name + Contact name + Role
↓
Query 1: Google reviews + sentiment (company-specific)
Query 2: Industry pain points (role-specific)
Query 3: Competitive landscape (company-specific)
↓
Output: 5-7 conversation starters ranked by relevance
```

### Output Format
```json
{
  "company": "Richmond Country Club",
  "contact": "Stacy Foster",
  "role": "General Manager",
  "context_enrichment": {
    "google_reviews": {
      "rating": "4.8/5",
      "positive_themes": ["excellent maintenance", "friendly staff"],
      "pain_points": ["overbooking during tournaments"]
    },
    "industry_pain_points": [
      "Labor shortages (agronomy, F&B)",
      "Wage pressure vs membership fees",
      "Member retention (Gen Z expectations)"
    ],
    "competitive_landscape": {
      "top_competitors": ["Independence Golf Club", "Royal New Kent"],
      "positioning": "Traditional exclusivity vs destination appeal"
    },
    "conversation_starters": [
      {
        "text": "Congrats on the 4.8 rating - clearly doing something right!",
        "source": "google_reviews",
        "relevance_score": 9
      },
      {
        "text": "Labor shortages hitting you hard too? Agronomy or F&B?",
        "source": "industry_pain_points",
        "relevance_score": 10
      },
      {
        "text": "How are you differentiating from Independence and Royal New Kent?",
        "source": "competitive_landscape",
        "relevance_score": 7
      }
    ]
  }
}
```

### Query Templates

**Query 1: Google Reviews (Company-Specific)**
```
"Find information about {company_name} in {location}, specifically: Google reviews rating, overall sentiment from reviews, recent feedback about staff and services, and any notable positive or negative themes from customer reviews. Focus on recent reviews from 2024-2025 if available."
```

**Query 2: Industry Pain Points (Role-Specific)**
```
"What are the biggest challenges and pain points facing {role} in {industry} in 2024-2025? Focus on: staffing issues, budget pressures, retention challenges, technology adoption, and operational efficiency concerns."
```

**Query 3: Competitive Landscape (Company-Specific)**
```
"What are the best {industry_type} in {location} area? Looking for ratings, rankings, how {company_name} compares to competitors, market positioning, and any notable differences in amenities or reputation among top {industry_type} in the {location} market."
```

---

## Risk Mitigation

### Data Quality Concerns
- **False positives:** Perplexity may confuse similar-named companies
- **Solution:** Always include location + industry in queries

### Cost Control
- **Risk:** Agents running too many queries per lead
- **Solution:** Limit to 3 queries max per lead, cache results

### Privacy/Ethics
- **Avoid:** Personal social media deep-dives, invasive scraping
- **Focus:** Public business info, industry trends, public reviews

---

## Next Steps

1. ✅ **Build Agent 6** using recommended architecture
2. Test with 10-20 real leads from Agent 1-5 outputs
3. Measure: Conversation starter quality, outreach response rate improvement
4. Iterate: Refine query templates based on what resonates

---

## Appendix: Sample Output for Richmond Country Club

**Company:** Richmond Country Club
**Contact:** Stacy Foster, General Manager
**Location:** Manakin-Sabot, Virginia

**Context Enrichment Results:**

✅ **Google Reviews & Sentiment**
- Rating: 4.8/5 (64 reviews)
- Positive: Excellent course condition (4.6/5), friendly staff, good value, recent clubhouse renovations
- Pain Point: Overbooking issues during tournaments

✅ **Industry Pain Points (Golf Course GMs)**
- Acute labor shortages (agronomy, chefs, all departments)
- Rising wage pressure vs. membership fee constraints
- Member retention challenges (Millennials/Gen Z expect experiences)
- Operational efficiency solutions (grab-and-go, micro-markets)

✅ **Competitive Landscape**
- Top Competitors: Independence Golf Club, Royal New Kent, Viniterra
- RCC Positioning: Traditional exclusivity vs. destination appeal
- Not in top-100 public lists (by design - private club)

**Top 5 Conversation Starters:**
1. "Congrats on the 4.8 rating - clearly doing something right!" (Positive reinforcement)
2. "Labor shortages hitting you hard too? Agronomy or F&B?" (Empathy)
3. "How are you balancing wage increases with membership fee sensitivity?" (Pain point)
4. "Noticed some overbooking challenges mentioned - solved that yet?" (Problem-solving)
5. "18+ years at RCC - you've seen the evolution firsthand!" (Respect for tenure)

**Outreach Angle:** Position solution as helping with operational efficiency, labor reduction, or member experience enhancement.

---

## Conclusion

**MCP context enrichment is HIGHLY VIABLE for Agent 6.**

The combination of:
- Perplexity for reviews, pain points, and competitive landscape
- Strategic, limited queries (3 per lead)
- Low cost (~$0.03/lead)
- High-quality conversation starters

...makes this a strong addition to the agent workflow.

**Next:** Build Agent 6 prototype and test with real leads.
