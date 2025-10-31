# Email Enrichment Testing Progress

**Goal:** 90% coverage @ 90%+ confidence
**Budget:** <$0.20 per course
**Timeline:** 4 weeks

---

## Phase 1: Baseline Analysis ✅

- [x] Audit current email coverage (Oct 29, 2025)
- [x] VA coverage: 67% @ 96% confidence
- [x] NC coverage: 20% @ 96% confidence
- [x] Overall: ~60% coverage
- [x] Identified problem: NC significantly lower than VA
- [x] Root cause: Oct 28 threshold change (70% → 90%)

**Findings:**
- 239 contacts with <70% confidence (data cleanup needed)
- Hunter.io only covers ~30-40% at 90%+
- Need backup source for remaining 50%+

---

## Phase 2: Apollo.io Research & Setup

### Research (Completed)
- [x] Identify Apollo.io as top backup option
- [x] Cost analysis: $49/month = $0.01/email
- [x] Expected coverage: +15-25%
- [x] Confidence scoring: 80-95% (filter for 90%+)
- [x] Alternative researched: RocketReach ($0.23/email - too expensive)

### Account Setup
- [ ] Sign up for Apollo.io account
  - URL: https://www.apollo.io/
  - Plan: Basic ($49/month, 5,000 credits)
- [ ] Get API key
- [ ] Add to `.env.example`: `APOLLO_API_KEY=your_key_here`
- [ ] Test API connection
- [ ] Verify confidence scoring available

**Notes:**
- Apollo provides confidence scores (verified/likely/guessed)
- Only accept "verified" (95%+) and high "likely" (90%+)
- Reject "guessed" (<80%)

---

## Phase 3: Apollo.io Baseline Testing

### Test Data Preparation
- [ ] Query Supabase for 50 NC contacts without Hunter.io emails
- [ ] Export to `data/nc_contacts_no_hunter_emails.json`
- [ ] Verify contacts have:
  - Name
  - Title
  - Company name
  - Domain
  - golf_course_id (>= 1000 for NC)

### Test Script Development
- [ ] Create `test_apollo.py`
- [ ] Implement Apollo API call function
- [ ] Add confidence filtering (≥90% only)
- [ ] Add cost tracking
- [ ] Add error handling
- [ ] Add results logging

### Execute Baseline Test
- [ ] Run test on 50 NC contacts
- [ ] Track metrics:
  - [ ] Emails found: __ / 50 (__%)
  - [ ] Emails at 90%+: __ / __ (__%)
  - [ ] Emails at 80-89%: __ (rejected)
  - [ ] Total cost: $__.__
  - [ ] Cost per email: $__.__
  - [ ] API errors: __

### Baseline Test Results
```
Expected metrics:
- Apollo finds: 15-25 emails (30-50%)
- 90%+ confidence: 10-18 emails (70%+)
- Total cost: ~$0.50 (50 contacts × $0.01)
- Net NC coverage improvement: +10-18 contacts = +20-36%

Pass criteria:
✅ ≥15 emails found (30%+)
✅ ≥70% at 90%+ confidence
✅ <$1.00 total cost
✅ Zero API errors
```

**Test Date:** ____________
**Results:**
- Emails found: __ / 50
- 90%+ confidence: __
- Cost: $__
- Pass/Fail: __

---

## Phase 4: Agent 3.5 Development

### Agent Skeleton
- [ ] Create `agents/agent3_5_email_enrichment.py`
- [ ] Add docstring (purpose, inputs, outputs)
- [ ] Define function signature
- [ ] Add type hints
- [ ] Import dependencies (httpx, claude_agent_sdk)

### Implement Waterfall Logic
- [ ] Step 1: Hunter.io email finder (existing pattern)
- [ ] Step 2: Apollo.io fallback (if Step 1 fails)
- [ ] Step 3: Confidence filtering (≥90% only)
- [ ] Step 4: Return null if no 90%+ email found
- [ ] Add method tracking (which source found email)
- [ ] Add cost tracking (both Hunter + Apollo)

### Error Handling
- [ ] Hunter.io API errors → log and continue to Apollo
- [ ] Apollo.io API errors → log and return null
- [ ] Rate limit handling (backoff/retry)
- [ ] Quota exceeded handling (fallback to null)
- [ ] Invalid response handling (malformed data)

### Testing
- [ ] Create `testing/email-enrichment/test_waterfall.py`
- [ ] Test Case 1: Hunter finds → Apollo skipped ✅
- [ ] Test Case 2: Hunter fails → Apollo finds 90%+ ✅
- [ ] Test Case 3: Hunter fails → Apollo finds <90% → Reject ✅
- [ ] Test Case 4: Both fail → Return null ✅
- [ ] Test Case 5: API error → Graceful fallback ✅
- [ ] All tests pass: ☐ Yes ☐ No

### Cost Validation
- [ ] Run on 10 test contacts
- [ ] Verify cost tracking accurate
- [ ] Confirm under $0.02 per contact target
- [ ] Document actual costs

**Agent 3.5 Completion Date:** ____________

---

## Phase 5: Integration Testing

### Orchestrator Integration
- [ ] Import Agent 3.5 into `orchestrator.py`
- [ ] Add after Agent 3 (Contact Enrichment)
- [ ] Wire up inputs (contact name, title, company, domain)
- [ ] Wire up outputs (email, confidence, method, cost)
- [ ] Update cost aggregation

### Database Schema
- [ ] Create migration `migrations/013_email_tracking.sql`
- [ ] Add column: `email_discovery_method`
- [ ] Add column: `email_confidence_score`
- [ ] Run migration on test database
- [ ] Verify Agent 8 writes new fields

### End-to-End Test
- [ ] Create test: `testing/integration/test_email_enrichment_e2e.py`
- [ ] Test on 20 full courses (80 contacts)
- [ ] Track metrics:
  - [ ] Total contacts: 80
  - [ ] Emails found: __ (__%)
  - [ ] Hunter.io: __ emails
  - [ ] Apollo.io: __ emails
  - [ ] Avg confidence: __%
  - [ ] Avg cost/course: $__.__

### E2E Test Results
```
Target metrics:
- Email coverage: ≥85% (68/80 contacts)
- All emails: ≥90% confidence
- Avg cost/course: <$0.20
- Success rate: ≥95% (19/20 courses)

Pass criteria:
✅ ≥68 emails found (85%+)
✅ 100% at 90%+ confidence
✅ Avg cost <$0.20/course
✅ ≥19 courses succeed
```

**Test Date:** ____________
**Results:**
- Coverage: __% (__/80)
- Confidence: __%
- Cost: $__.__/course
- Pass/Fail: __

---

## Phase 6: Production Deployment

### Pre-Deployment Checklist
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Cost validated (<$0.20/course)
- [ ] Documentation updated
- [ ] Migration ready for production
- [ ] Apollo.io production account set up

### Deployment Steps
- [ ] Run migration on production database
- [ ] Sync Agent 3.5 to production
  ```bash
  python production/scripts/sync_to_production.py golf-enrichment
  ```
- [ ] Deploy to Render
  ```bash
  cd production/golf-enrichment
  git add .
  git commit -m "Add Agent 3.5: Email Enrichment Specialist"
  git push
  ```
- [ ] Verify deployment successful
- [ ] Test production endpoint

### Production Monitoring (First 100 Courses)

**Week 1 Metrics:**
- [ ] Courses enriched: __
- [ ] Email coverage: __%
- [ ] Avg confidence: __%
- [ ] Avg cost/course: $__.__
- [ ] Hunter.io %: __%
- [ ] Apollo.io %: __%
- [ ] Errors: __

**Week 2-4 Metrics:**
- [ ] Total courses: __
- [ ] Sustained coverage: __%
- [ ] Bounce rate (from outreach): __%
- [ ] Cost trend: $__.__ → $__.__
- [ ] API quota usage: __% Hunter, __% Apollo

### Success Validation
```
Goals:
✅ ≥90% email coverage
✅ ≥90% confidence for all
✅ <$0.20 avg cost/course
✅ <2% bounce rate
✅ Zero quota exceeded errors

Actual:
☐ __% coverage (target: 90%+)
☐ __% confidence (target: 90%+)
☐ $__.__ cost (target: <$0.20)
☐ __% bounce rate (target: <2%)
☐ __ quota errors (target: 0)
```

**Production Validation Date:** ____________
**Final Status:** ☐ Pass ☐ Needs Adjustment

---

## Phase 7: Documentation & Handoff

### Update Documentation
- [ ] `docs/2_OPERATIONS/COST_OPTIMIZATION.md`
  - Add Agent 3.5 costs
  - Update total cost per course
- [ ] `docs/2_OPERATIONS/RELIABILITY_PLAYBOOK.md`
  - Add Apollo.io error handling
  - Add rate limit procedures
- [ ] `START_HERE.md`
  - Update email coverage metrics
  - Add Agent 3.5 to agent list
- [ ] `testing/PROGRESS.md`
  - Mark email enrichment complete
  - Document final metrics

### Knowledge Transfer
- [ ] Create summary report
- [ ] Document learnings (what worked/didn't)
- [ ] Update edge case playbook if needed
- [ ] Share with team

---

## Rollback Plan (If Needed)

If Agent 3.5 doesn't meet goals:

1. **Disable Agent 3.5**
   - Comment out in orchestrator.py
   - Revert to Hunter.io only
   - Deploy rollback

2. **Investigate Issues**
   - Review error logs
   - Analyze coverage data
   - Check API reliability

3. **Consider Alternatives**
   - Try RocketReach (if cost acceptable)
   - Investigate Perplexity email extraction
   - Re-enable web scraping with better validation

---

## Notes & Learnings

**Date:** ____________
**Notes:**
-
-
-

**Key Learnings:**
-
-
-

**Recommendations for Future:**
-
-
-

---

## Final Sign-Off

**Email Enrichment Goal Achieved:** ☐ Yes ☐ No

**Final Metrics:**
- Coverage: __%
- Confidence: __%
- Cost: $__.__/course
- Bounce Rate: __%

**Completed By:** ____________
**Date:** ____________
