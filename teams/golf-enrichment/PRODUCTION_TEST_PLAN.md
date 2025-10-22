# Production Testing Plan - Agent 4 Comprehensive Data

**Deployed:** Commit 4bc8b2e (comprehensive LinkedIn extraction)
**Render URL:** https://agent7-water-hazards.onrender.com
**Test Course:** 133 (Chantilly National - original failing case)

---

## Pre-Test: Verify Deployment Live

### Check Render Dashboard
1. Go to: https://dashboard.render.com
2. Service: `golf-enrichment-api`
3. Status should show: **Live** (green)
4. Latest Deploy: Should show commit `4bc8b2e`

### Check Environment Variables
1. Render Dashboard → Environment tab
2. Verify: `BRIGHTDATA_API_TOKEN` is set
3. Value should be: `80a23578-3a9e-41d8-9700-72d8034124f3`

---

## Test Execution

### Option A: Manual curl (Recommended - Fastest)

**Delete old Course 133 data first:**
```sql
DELETE FROM golf_course_contacts WHERE golf_course_id = 133;
```

**Trigger enrichment:**
```bash
curl -X POST https://agent7-water-hazards.onrender.com/enrich-course \
  -H 'Content-Type: application/json' \
  -d '{
    "course_id": 133,
    "course_name": "Chantilly National Golf and Country Club",
    "state_code": "VA",
    "use_test_tables": false
  }'
```

**Expected:** 3-4 minute response with success: true

---

### Option B: Supabase Trigger (Full Workflow)

```sql
-- In Supabase SQL editor
SELECT enrich_golf_course(133);

-- Or however your trigger is configured
```

---

## Validation Checklist

### 1. Check Render Logs

**Go to:** Render Dashboard → Logs tab

**Must see:**
```
✅ "🔗 Agent 4: Finding LinkedIn + Tenure (specialist)..."
✅ "🔧 Tool: mcp__brightdata__search_engine"
✅ "🔧 Tool: mcp__brightdata__scrape_as_markdown"
✅ "Method: brightdata_hosted_mcp"
```

**Must NOT see:**
```
❌ "BRIGHTDATA_API_TOKEN not set - Agent 4 disabled"
❌ "Profile scrape failed (status 400)"
❌ No Agent 4 mentions at all
```

---

### 2. Validate Database Results

```sql
SELECT
    contact_name,
    linkedin_url,
    tenure_years,
    linkedin_full_title,
    linkedin_company,
    previous_golf_roles,
    industry_experience_years,
    education,
    certifications
FROM golf_course_contacts
WHERE golf_course_id = 133
ORDER BY contact_name;
```

**Expected Results (4 contacts from Chantilly National):**

**John Stutz:**
- linkedin_url: `https://www.linkedin.com/in/john-stutz-2b30a133` ✅
- tenure_years: `0.6` (7 months) ✅
- linkedin_full_title: `"General Manager / COO"` ✅
- linkedin_company: `"Invited"` ✅
- industry_experience_years: `20-25` ✅
- education: `["Executive MBA - Loyola..."]` ✅
- certifications: `["Beta Gamma Sigma"]` ✅

**Brandon Roseth:**
- linkedin_url: Found ✅
- tenure_years: `2.7` (2 years 8 months) ✅
- Comprehensive fields populated ✅

**Peter Siemsen:** (similar)
**Joshua Alpaugh:** (similar)

**Success Criteria:**
- ✅ 3-4/4 contacts have LinkedIn URLs
- ✅ 3-4/4 contacts have tenure_years (not NULL!)
- ✅ 3-4/4 contacts have comprehensive data fields
- ✅ Cost per course < $0.20

---

### 3. Compare Before vs After

**Before Fix (Original Production Failure):**
```
Course 133:
- LinkedIn URLs: 4/4 found
- Tenure: 0/4 extracted (all NULL) ❌
- Error: "Profile scrape failed (status 400)"
- Comprehensive data: None
```

**After Fix (Expected):**
```
Course 133:
- LinkedIn URLs: 4/4 found ✅
- Tenure: 3-4/4 extracted ✅
- Method: brightdata_hosted_mcp ✅
- Comprehensive data: 6 fields per contact ✅
```

---

## If Test Fails

### Issue 1: Agent 4 Not in Logs

**Symptom:** No "Agent 4: Finding LinkedIn..." in Render logs

**Cause:** Orchestrator not calling Agent 4

**Fix:**
```bash
# Check orchestrator was synced/deployed
grep "from agents.agent4_linkedin_finder import" production/golf-enrichment/orchestrator.py

# Re-sync if needed
python production/scripts/sync_to_production.py golf-enrichment
git add . && git commit -m "fix: Sync orchestrator" && git push
```

---

### Issue 2: BRIGHTDATA_API_TOKEN Error

**Symptom:** "BRIGHTDATA_API_TOKEN not set - Agent 4 disabled"

**Cause:** Env var missing in Render

**Fix:**
1. Render Dashboard → Environment
2. Add: BRIGHTDATA_API_TOKEN = 80a23578-3a9e-41d8-9700-72d8034124f3
3. Save (auto-redeploys)

---

### Issue 3: All Tenure Still NULL

**Symptom:** Database shows tenure_years = NULL for all contacts

**Cause:** BrightData tools not being called

**Debug:**
```bash
# Check Render logs for tool calls
# Search for: "mcp__brightdata__"

# If not found:
# - Hosted MCP URL might be malformed
# - Token might be invalid
# - MCP server not starting
```

---

### Issue 4: Some Fields NULL

**Symptom:** Tenure works but education/certifications NULL

**Cause:** Agent extracted data but fields not in LinkedIn profile

**Expected:** Not all profiles have all fields - this is normal
- 100% should have: url, tenure, title, company
- 50-80% might have: education, certifications
- 30-50% might have: previous_golf_roles, industry_years

---

## Success Declaration

**✅ Declare SUCCESS if:**
- Agent 4 runs for all contacts (logs show activity)
- 3-4/4 contacts have tenure values (not 0/4!)
- Comprehensive fields extracted (at least title + company)
- No errors in Render logs
- Cost reasonable (~$0.15-0.20 per course)

**Then:**
- Agent 4 tenure extraction COMPLETE ✅
- Tenure coverage improved from 20% → 80% ✅
- Comprehensive LinkedIn intelligence captured ✅
- Production validated following SOP ✅

---

## Quick Test Commands

**Health check:**
```bash
curl https://agent7-water-hazards.onrender.com/health
```

**Enrich Course 133:**
```bash
curl -X POST https://agent7-water-hazards.onrender.com/enrich-course \
  -H 'Content-Type: application/json' \
  -d '{"course_id": 133, "course_name": "Chantilly National Golf and Country Club", "state_code": "VA"}'
```

**Check database:**
```sql
SELECT contact_name, tenure_years FROM golf_course_contacts WHERE golf_course_id = 133;
```

---

**Estimated Time:** 3-4 min for enrichment + 2 min validation = 6 minutes total

**Next:** Monitor Render deployment (should be live in 2-3 minutes), then run test!
