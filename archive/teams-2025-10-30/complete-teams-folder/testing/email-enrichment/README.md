# Email Enrichment Testing

**Goal:** Achieve 90% coverage @ 90%+ confidence for all golf course contacts

**Current Status:**
- VA: 67% coverage @ 96% confidence
- NC: 20% coverage @ 96% confidence
- Overall: ~60% coverage

**Target:** 90% coverage @ 90%+ confidence

---

## Problem Statement

After raising the email confidence threshold to 90% (Oct 28, 2025), email coverage dropped significantly:
- **Before:** ~79% coverage @ 93% confidence (Hunter.io + web scraping at 70%+)
- **After:** ~50% coverage @ 96% confidence (Hunter.io only at 90%+)
- **NC Impact:** Only 20% coverage (vs 67% for VA)

**Need:** Reliable backup email sources that maintain 90%+ confidence

---

## Proposed Solution: Agent 3.5 (Email Enrichment Specialist)

### Architecture
```
Agent 3.5: Email Waterfall Enrichment
├─ Step 1: Hunter.io (90-99% confidence) ✅ CURRENT
├─ Step 2: Apollo.io (filter for 90%+ confidence) ← NEW
├─ Step 3: RocketReach (filter for 90%+ confidence) ← OPTIONAL
└─ Step 4: Return null if no 90%+ email found
```

### Success Criteria
- **Coverage:** 90% of contacts get emails
- **Confidence:** All emails ≥ 90% confidence
- **Cost:** Under $0.20 per course (4 contacts)
- **Bounce Rate:** < 2% (validated after outreach)

---

## Testing Strategy

### Phase 1: Apollo.io Baseline (Week 1)
**File:** `test_apollo.py`

**Test Set:** 50 NC contacts without Hunter.io emails

**Metrics to Track:**
- Apollo coverage rate (% of contacts found)
- Confidence score distribution
- Percentage meeting 90%+ threshold
- Cost per email
- API reliability

**Expected Results:**
- Apollo finds 30-50% of missing emails
- 70%+ of Apollo emails meet 90% threshold
- Cost: $0.01 per email attempt
- Net improvement: +15-25% NC coverage

**Pass Criteria:**
- ≥30% additional coverage
- ≥70% of found emails at 90%+
- Zero API errors
- Cost under $0.02 per contact

### Phase 2: Agent Development (Week 2)
**File:** `test_waterfall.py`

**Test:** Agent 3.5 waterfall logic

**Test Cases:**
1. Hunter.io finds email → Apollo skipped ✅
2. Hunter.io fails → Apollo finds 90%+ email ✅
3. Hunter.io fails → Apollo finds <90% email → Reject ✅
4. Both fail → Return null ✅
5. API error handling → Graceful fallback ✅

**Pass Criteria:**
- All 5 test cases pass
- Confidence filtering works (≥90% only)
- Cost tracking accurate
- Error handling robust

### Phase 3: Integration Testing (Week 3)
**File:** `../integration/test_email_enrichment_e2e.py`

**Test:** Full orchestrator with Agent 3.5

**Test Set:** 20 full courses (80 contacts)

**Metrics:**
- Overall email coverage (target: 90%)
- Confidence distribution (all ≥90%)
- Cost per course (target: <$0.20)
- Time per enrichment
- Success/failure rate

**Pass Criteria:**
- ≥85% email coverage achieved
- 100% of emails ≥90% confidence
- Average cost <$0.20/course
- <5% failure rate

### Phase 4: Production Validation (Week 4)
**Monitoring:** First 100 courses in production

**Metrics:**
- Email coverage trend
- Bounce rate (from outreach)
- Cost actuals vs projections
- API quota usage
- Error rate

**Success Criteria:**
- ≥90% coverage sustained
- <2% bounce rate
- Cost stays under $0.20
- Zero quota exceeded errors

---

## Test Data

### Sample Contacts (data/)
Create sample NC contacts without Hunter.io emails:
```json
{
  "contact_id": "test-001",
  "contact_name": "John Smith",
  "contact_title": "Head Professional",
  "golf_course_id": 1145,
  "company_name": "Example Golf Club",
  "domain": "examplegolf.com"
}
```

### Test Results (results/)
Store test outputs:
- `apollo_baseline_results.json` - Apollo API test results
- `waterfall_logic_results.json` - Waterfall test results
- `integration_test_results.json` - E2E test results

---

## Running Tests

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys
export APOLLO_API_KEY=your_key_here
export HUNTER_API_KEY=your_key_here
```

### Run Apollo Baseline Test
```bash
pytest testing/email-enrichment/test_apollo.py -v
```

### Run Waterfall Logic Test
```bash
pytest testing/email-enrichment/test_waterfall.py -v
```

### Run All Email Enrichment Tests
```bash
pytest testing/email-enrichment/ -v
```

---

## API Services

### Hunter.io (Current)
- **Cost:** Free tier (covered)
- **Coverage:** ~30-40%
- **Confidence:** 90-99%
- **Status:** ✅ Active

### Apollo.io (Proposed)
- **Cost:** $49/month = $0.01/email
- **Coverage:** ~30-40% (estimate)
- **Confidence:** 80-95% (filter for 90%+)
- **Status:** ⏳ Testing

### RocketReach (Optional)
- **Cost:** $39/month = $0.23/email
- **Coverage:** ~25-35% (estimate)
- **Confidence:** 85-95%
- **Status:** 🔄 Backup option

---

## Cost Analysis

### Current (Hunter.io only)
```
Per contact: $0.00 (free tier)
Per course: $0.18 (other agents)
Coverage: 60%
```

### With Apollo.io
```
Hunter.io:  30% found × $0.00 = $0.00
Apollo.io:  30% found × $0.01 = $0.003
Total add:  $0.003 per contact
Per course: $0.18 + $0.012 = $0.192

Coverage: 60% + 21% = 81% (estimated)
Still under budget: ✅ $0.192 < $0.20
```

### With RocketReach (if needed)
```
Hunter.io:  30% × $0.00 = $0.000
Apollo.io:  30% × $0.01 = $0.003
RocketReach: 10% × $0.23 = $0.023
Total:      $0.026 per contact
Per course: $0.18 + $0.104 = $0.284

Coverage: 70% (estimated)
Over budget: ❌ $0.284 > $0.20
```

**Recommendation:** Start with Apollo only, add RocketReach only if coverage insufficient

---

## Progress Tracking

See `progress.md` for detailed testing checklist

---

## Documentation Updates

After testing complete, update:
- `docs/2_OPERATIONS/COST_OPTIMIZATION.md` - Add Agent 3.5 costs
- `docs/2_OPERATIONS/RELIABILITY_PLAYBOOK.md` - Add Apollo error handling
- `START_HERE.md` - Update coverage metrics
- `migrations/013_email_tracking.sql` - Track email discovery method
