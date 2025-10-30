# Email Enrichment v1 - Hunter.io Only

**Version:** 1.0
**Last Updated:** October 29, 2025
**Status:** Current production flow

---

## Overview

Email enrichment v1 uses **Hunter.io only** with a strict 90% confidence threshold. This is our baseline before adding additional data sources.

---

## Current Flow

```
Contact Input (name, title, company, domain)
    ↓
Agent 3: Contact Enricher
    ↓
Step 1: Hunter.io Email-Finder API
    ↓
    ├─ Found + 90%+ confidence → Return email
    ├─ Found + <90% confidence → Skip (null)
    └─ Not found → Return null
    ↓
Output: { email, email_method, email_confidence, linkedin_url }
```

---

## Implementation

**Agent:** `agents/agent3_contact_enricher.py`

**Tool:** `enrich_contact_tool()`

**API:** Hunter.io Email-Finder
- Endpoint: `https://api.hunter.io/v2/email-finder`
- Parameters: domain, first_name, last_name, api_key
- Returns: email, score (confidence), linkedin_url

**Confidence Filter:**
```python
if confidence >= 90:
    results["email"] = email
    results["email_method"] = "hunter_io"
    results["email_confidence"] = confidence
```

**Quality Rule:** Better to return `null` than unreliable email (<90% confidence)

---

## Current Performance

### Coverage

| Region | Success Rate | Confidence (when found) |
|--------|--------------|------------------------|
| VA     | 67%          | 96% avg                |
| NC     | 20%          | 96% avg                |
| Overall| ~60%         | 96% avg                |

### Cost

- **Per contact:** $0.0116 avg
- **Per email found:** ~$0.0193
- **Budget compliance:** ✅ Under $0.02 target

### Speed

- **Average:** 8.1 seconds per contact
- **Model:** Claude Haiku 4.5

---

## What Works Well

✅ **High Confidence:** 90-99% confidence scores enable quality filtering
✅ **Verified Data:** Hunter.io verifies emails (not guessed patterns)
✅ **Bonus Data:** Returns LinkedIn URLs (25% success)
✅ **Cost Effective:** $0.0116/contact, 42% under budget
✅ **API Reliability:** Excellent uptime, good error handling
✅ **VA Coverage:** 67% success in Virginia

---

## What Needs Improvement

❌ **NC Coverage:** Only 20% success in North Carolina (50 percentage point gap!)
❌ **Overall Coverage:** 60% overall (need 90%)
❌ **Single Source:** No fallback if Hunter.io doesn't have contact
❌ **Missing Contacts:** 40% of contacts get `null` (lost opportunity)

---

## Test 1: NC Baseline Validation

**Goal:** Prove Hunter.io performance on NC contacts before adding new tools

**Hypothesis:** NC contacts have 20% email discovery rate (vs 67% VA)

**Test Plan:**
1. Query Supabase for 50 NC contacts without emails
2. Run Agent 3 (Hunter.io) on these contacts
3. Measure actual success rate
4. Validate 90%+ confidence on found emails
5. Document baseline performance

**Expected Results:**
- Success rate: ~20% (10 out of 50 contacts)
- Confidence: 90-99% for all found emails
- Cost: 50 × $0.0116 = $0.58

**Test File:** `testing/email-enrichment/test_hunter_nc_baseline.py`
**Test Data:** `testing/email-enrichment/data/nc_contacts_no_hunter.json`

---

## Disabled Features

**Web Scraping (Steps 2-3):**
Disabled as of October 28, 2025

```python
if False:  # Disabled - doesn't meet 90% confidence requirement
    # STEP 2: Web Search via Jina (70% confidence)
    # STEP 3: Focused search (60% confidence)
```

**Rationale:**
- Web scraping only achieved 60-70% confidence
- Below 90% threshold required for quality
- Reduced overall coverage from ~79% to 50%
- But improved confidence from 93% to 96%

**Trade-off accepted:** Quality over quantity

---

## Future Evolution

### v2: Hunter.io + Apollo.io Waterfall (Planned)

```
Step 1: Hunter.io (90%+ confidence)
    ↓
    Not found?
    ↓
Step 2: Apollo.io People Search API (verified only)
    ↓
    Not found?
    ↓
Return null
```

**Apollo.io Integration:**
- API: People Search API (275M contacts)
- Endpoint: `POST https://api.apollo.io/v1/people/search`
- Documentation: https://docs.apollo.io/reference/people-search
- Setup guide: `testing/email-enrichment/apollo_setup.md`
- Filter: `email_status: "verified"` only (90%+ confidence)
- Cost: ~$0.013/email lookup

**Expected Improvement:**
- Coverage: 60% → 65-75% (+5-15 percentage points)
- Cost: $0.0116 → $0.012 avg (actually SAVES money)
- Quality: Maintained at 90%+

**Why Apollo.io:**
- 2.75x larger database than Hunter.io (275M vs 100M)
- 60-70% different data sources (minimal overlap)
- Verified emails meet 90%+ threshold
- Bonus: Returns phone numbers + LinkedIn URLs

**Status:**
- ✅ Research completed (Oct 29, 2025)
- ✅ Apollo.io account created
- ⬜ Test 1: Hunter.io NC baseline (in progress)
- ⬜ Test 2: Apollo.io NC validation (pending)

---

### v3: Hunter.io + Apollo.io + Snov.io (Optional)

```
Step 1: Hunter.io (90%+)
Step 2: Apollo.io (verified)
Step 3: Snov.io (verified 94%+)
```

**Expected Improvement:**
- Coverage: 60% → 75% (+15 percentage points)
- Cost: $0.0116 → $0.0113 avg (Snov.io cheaper)
- Quality: Maintained at 90%+

**Status:** Deferred until v2 proven

---

## Success Criteria

**For v1 (Current):**
- ✅ Maintain 90%+ confidence on all emails
- ✅ Cost < $0.02 per contact
- ⚠️ Coverage: 60% (target: 90%) - **NEEDS IMPROVEMENT**

**For v2 (Hunter + Apollo):**
- 65%+ email coverage
- 90%+ confidence maintained
- <$0.02 average cost per contact
- API reliability >99%

**For v3 (3-tier waterfall):**
- 75%+ email coverage
- 90%+ confidence maintained
- <$0.02 average cost per contact
- Graceful degradation if any tier fails

---

## Testing Strategy

### Phase 1: Baseline Validation ← **CURRENT**
**Test 1:** Hunter.io on NC contacts
**Goal:** Validate current performance
**Status:** In progress

### Phase 2: Apollo.io Evaluation
**Test 2:** Apollo.io on same NC contacts
**Goal:** Measure incremental coverage
**Status:** Pending Test 1 completion

### Phase 3: Waterfall Development
**Test 3:** Build Agent 3.5 waterfall
**Goal:** Production-ready waterfall agent
**Status:** Pending Test 2 results

### Phase 4: E2E Validation
**Test 4:** 20 courses with Agent 3.5
**Goal:** Prove waterfall in production
**Status:** Pending Test 3 completion

### Phase 5: Production Deployment
**Test 5:** Deploy and monitor
**Goal:** Validate at scale
**Status:** Pending Test 4 success

---

## Key Decisions

### October 28, 2025: Disable Web Scraping
**Decision:** Disable Steps 2-3 (web scraping) due to <90% confidence
**Impact:** Coverage dropped from 79% to 60%, but confidence improved 93% → 96%
**Rationale:** Quality > quantity for deliverability

### October 29, 2025: Research Email Data Sources
**Decision:** Evaluate Hunter.io, Apollo.io, Snov.io, RocketReach, ZoomInfo
**Result:** Apollo.io recommended for Tier 2 (best ROI + coverage)
**Next:** Validate Hunter.io baseline on NC before adding Apollo.io

### October 29, 2025: Test 1 First
**Decision:** Run Hunter.io on NC contacts before adding new tools
**Rationale:** Prove baseline performance, ensure Agent 3 works correctly
**Timeline:** Test 1 this week, Test 2 (Apollo) next week

---

## API Configuration

**Hunter.io:**
- API Key: `HUNTER_API_KEY` (in .env)
- Plan: Growth ($149/mo, 10,000 searches)
- Rate Limit: Generous (not an issue)
- Timeout: 30 seconds

**Future (Apollo.io):**
- API Key: `APOLLO_API_KEY` (pending signup)
- Plan: Professional ($79/mo, 6,000 credits)
- Rate Limit: 5,000/day
- Timeout: 30 seconds

---

## Error Handling

**Current (Hunter.io only):**
```python
try:
    r = await client.get(url, params=params)
    data = r.json()
    # Process response
except Exception:
    pass  # Continue to next step (currently returns null)
```

**Future (Waterfall):**
- Try Hunter.io → catch exception → try Apollo.io
- Log all API failures for monitoring
- Graceful degradation (if Hunter.io down, use Apollo.io)
- Return null only if all tiers fail

---

## Monitoring

**Current Metrics:**
- Email discovery rate by region (VA vs NC)
- Confidence score distribution
- Cost per contact
- API latency

**Future Metrics (v2+):**
- Discovery rate per tier (Hunter vs Apollo vs Snov.io)
- Tier utilization (% falling through to Tier 2/3)
- Overlap between tiers (how much duplication?)
- Bounce rate by tier (email quality validation)

---

## Version History

**v1.0 (October 28, 2025):**
- Hunter.io only, 90% confidence threshold
- Web scraping disabled
- 60% coverage, 96% confidence
- Production deployment

**v2.0 (Planned):**
- Add Apollo.io waterfall
- Target 65% coverage
- Maintain 90%+ confidence

**v3.0 (Future):**
- Add Snov.io Tier 3
- Target 75% coverage
- Cost optimization

---

## Related Documentation

- **Agent Code:** `agents/agent3_contact_enricher.py`
- **Testing Progress:** `testing/PROGRESS.md`
- **Email Testing:** `testing/email-enrichment/progress.md`
- **Research:** Email data source comparison (Oct 29, 2025)

---

**Next Steps:**
1. ✅ Document v1 flow (this file)
2. Query Supabase for NC contacts without emails
3. Run Test 1: Hunter.io NC baseline
4. Analyze results
5. Decide on Apollo.io integration (Test 2)
