# LLM API Cost Comparison Matrix

**Updated:** November 1, 2025
**Context:** Automating 15,000 NC/SC golf course enrichment

---

## Executive Summary

| API | Cost/Course | Total (15k) | Quality Expected | Recommendation |
|-----|-------------|-------------|------------------|----------------|
| **Perplexity Sonar Pro** | $0.005 | **$75** | Unknown - TEST FIRST | ✅ PRIMARY |
| **OpenAI GPT-4o** | $0.045 | $675 | Identical to manual | ✅ FALLBACK #2 |
| **Claude Sonnet 4.5** | $0.06 | $900 | High reasoning | ⚠️ FALLBACK #1 |
| **Manual ChatGPT-5 Pro** | N/A | $125k (opportunity cost) | Proven 100% | ❌ UNSUSTAINABLE |

**Savings vs Manual:** $124,100 - $124,925 (any API option)

---

## Detailed Cost Breakdown

### Perplexity Sonar Pro (PRIMARY TEST)

**Pricing Model:** Flat rate per request (~$0.005/request)

**Per Course:**
- API request: $0.005
- No token-based pricing
- Web search included
- **Total:** ~$0.005 per course

**15,000 Courses:**
- 15,000 × $0.005 = **$75 total**

**Rate Limits:**
- Free tier: 50 requests/day → 300 days (unacceptable)
- Pro tier ($20/month): 1,000 requests/day → 15 days
- **Recommendation:** Upgrade to Pro tier immediately
- **Total cost with Pro:** $75 + $20 = **$95**

**Advantages:**
- ✅ Cheapest option (15x cheaper than Claude)
- ✅ Built-in web search (no scraping needed)
- ✅ `return_citations` parameter (automatic source attribution)
- ✅ Fast processing (<5 seconds per course)

**Disadvantages:**
- ❌ Unknown quality (must test first)
- ❌ Citation format may differ from manual
- ❌ Free tier too slow (requires Pro upgrade)

---

### OpenAI GPT-4o (FALLBACK #2)

**Pricing Model:** Token-based

**Rates:**
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens

**Per Course:**
- Input: V2 prompt (1k) + course context (9k) = 10k tokens × $2.50/1M = $0.025
- Output: V2 JSON response (~2k tokens) × $10/1M = $0.020
- **Total:** ~$0.045 per course

**15,000 Courses:**
- 15,000 × $0.045 = **$675 total**

**Rate Limits:**
- Tier 1 (Free): 500 RPM, 200k TPM
- Tier 2 ($50+ spend): 5,000 RPM, 2M TPM
- **Our usage:** 12 requests/hour = well within Tier 1

**Advantages:**
- ✅ Same model as manual ChatGPT-5 Pro (proven quality)
- ✅ Should produce identical results
- ✅ `response_format: json_object` for structured output
- ✅ No rate limit concerns

**Disadvantages:**
- ❌ 9x more expensive than Perplexity ($675 vs $75)
- ❌ No built-in citations parameter (requires prompt engineering)
- ❌ No web search built-in (manual baseline uses ChatGPT interface which has web access)

---

### Claude Sonnet 4.5 (FALLBACK #1)

**Pricing Model:** Token-based

**Rates:**
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

**Per Course:**
- Input: V2 prompt (1k) + course context (9k) = 10k tokens × $3/1M = $0.03
- Output: V2 JSON response (~2k tokens) × $15/1M = $0.03
- **Total:** ~$0.06 per course

**15,000 Courses:**
- 15,000 × $0.06 = **$900 total**

**Rate Limits:**
- Standard tier: No hard limits (usage-based)
- Burst: 4,000 RPM
- **Our usage:** 12 requests/hour = no concerns

**Advantages:**
- ✅ Best reasoning and analysis capabilities
- ✅ Better instruction following than GPT-4o
- ✅ 200k context window (can include full website if needed)
- ✅ No rate limit concerns

**Disadvantages:**
- ❌ 12x more expensive than Perplexity ($900 vs $75)
- ❌ 1.3x more expensive than OpenAI ($900 vs $675)
- ❌ No built-in web search
- ❌ No citations parameter (requires prompt engineering)

---

## ROI Analysis

### Baseline: Manual Approach

**Effort:**
- 15,000 courses × 10 minutes per course = 2,500 hours
- 2,500 hours ÷ 8 hours/day = 312 working days
- 312 days ÷ 21 working days/month = **15 months**

**Opportunity Cost:**
- 2,500 hours × $50/hour labor = **$125,000**

**Risk:**
- Human error compounding over 15 months
- Burnout and quality degradation
- Inconsistent data entry

---

### Automated Approach: Any API

**Effort:**
- Build time: 6 hours (one-time)
- Monitoring: 1 hour/week × 8 weeks = 8 hours
- **Total:** 14 hours vs 2,500 hours manual

**Time Savings:**
- 2,486 hours = 311 working days = **14.8 months**

**Cost Comparison:**

| Scenario | Build | API Costs | Monitoring | Total | Savings vs Manual |
|----------|-------|-----------|------------|-------|-------------------|
| **Perplexity** | $0 | $75 | $0 | **$75** | **$124,925** |
| **OpenAI** | $0 | $675 | $0 | **$675** | **$124,325** |
| **Claude** | $0 | $900 | $0 | **$900** | **$124,100** |

**Break-even:** After 1 course (any API)

**ROI:**
- Perplexity: **166,567% ROI** ($124,925 / $75)
- OpenAI: **18,419% ROI** ($124,325 / $675)
- Claude: **13,789% ROI** ($124,100 / $900)

---

## Timeline Comparison

### Manual
- **Start:** Day 0
- **Milestone 1 (1,000 courses):** Day 21 (1 month)
- **Milestone 2 (5,000 courses):** Day 104 (5 months)
- **Milestone 3 (10,000 courses):** Day 208 (10 months)
- **Complete (15,000 courses):** Day 312 (15 months)

### Automated (Any API)
- **Start:** Day 0
- **Build & Test:** Days 0-3
- **Milestone 1 (1,000 courses):** Day 7
- **Milestone 2 (5,000 courses):** Day 21
- **Milestone 3 (10,000 courses):** Day 42
- **Complete (15,000 courses):** Day 52 (**52 days vs 15 months**)

**Time savings:** 260 days = **8.7 months faster**

---

## Risk-Adjusted Budget Recommendation

### Conservative Approach
**Primary:** Test Perplexity ($75)
**Fallback:** Have $675 budgeted for OpenAI if Perplexity fails
**Max exposure:** $750 total

**Rationale:**
- Test cheapest option first (Perplexity $75)
- If fails, fall back to proven option (OpenAI = same as manual)
- Claude skipped unless OpenAI also fails (unlikely)

### Aggressive Approach
**Primary:** Go straight to OpenAI ($675)
**Rationale:** Same model as manual baseline, guaranteed quality
**Risk:** Spend 9x more than necessary if Perplexity would have worked

**Recommendation:** **Conservative approach** (test Perplexity first)

---

## Budget Approval Framework

### For User Decision

**Option A: Perplexity Passes Testing**
- **Cost:** $75 (+$20 Pro tier = $95 total)
- **Timeline:** 15 days (with Pro tier 1k/day limit)
- **Risk:** Low (citations validated in 3-course pilot)
- **Approval needed:** ✅ $95 budget

**Option B: Perplexity Fails, OpenAI Selected**
- **Cost:** $75 (Perplexity test) + $675 (OpenAI automation) = $750
- **Timeline:** 52 days (slower rate limit)
- **Risk:** Very low (same model as manual)
- **Approval needed:** ✅ $750 budget

**Option C: Both Fail, Claude Selected**
- **Cost:** $75 + $675 + $900 = $1,650 (tested all 3)
- **Timeline:** 52 days
- **Risk:** Low (best reasoning model)
- **Approval needed:** ✅ $1,650 budget

### Maximum Budget Request

**Worst case:** All APIs tested = $1,650
**vs Manual:** $125,000 opportunity cost
**Savings:** $123,350 (7,454% ROI even in worst case)

**Recommended approval:** Up to $2,000 budget (includes buffer)

---

## Monitoring Costs During Automation

### Daily Cost Tracking Query

```sql
SELECT
  api_provider,
  COUNT(*) as courses_processed,
  SUM(cost_usd) as total_cost,
  AVG(cost_usd) as avg_cost_per_course,
  SUM(cost_usd) * (15000 / COUNT(*)) as projected_total_cost
FROM llm_api_test_results
GROUP BY api_provider
ORDER BY total_cost;
```

### Alert Thresholds

**Set alerts if:**
- Average cost > $0.10 per course (2x estimate)
- Daily spend > $50 (suggests rate issue)
- Projected total > $1,000 (budget overrun risk)

**Action:** Pause automation, investigate, adjust

---

## Decision Matrix

| Quality | Citations | Cost | Decision |
|---------|-----------|------|----------|
| ≥90% | ✅ Present | $75 | ✅ Use Perplexity |
| ≥90% | ❌ Missing | $75 | ❌ Test Claude |
| ≥90% | ✅ Present | $900 | ⚠️ Consider Claude vs OpenAI cost |
| 100% | ✅ Present | $675 | ✅ Use OpenAI (matches manual) |
| <90% | N/A | N/A | 🚨 Debug prompt, not API issue |

---

**Recommendation:** Start with Perplexity testing. If quality + citations pass → save $600-825 vs alternatives.
