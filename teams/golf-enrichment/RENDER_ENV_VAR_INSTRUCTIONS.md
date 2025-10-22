# Add BRIGHTDATA_API_TOKEN to Render

## Issue

Agent 4 deployed to production but fails silently because `BRIGHTDATA_API_TOKEN` environment variable is not set in Render.

**Evidence from render logs:**
- Agents 1,2,3,5,6,8 all run ✅
- Agent 4 not called/fails silently ❌
- No BrightData API calls in logs

---

## Solution

### Step 1: Go to Render Dashboard

URL: https://dashboard.render.com/

### Step 2: Select Service

Navigate to: **golf-enrichment-api** service

### Step 3: Add Environment Variable

1. Click **Environment** tab
2. Click **Add Environment Variable**
3. Set:
   - **Key:** `BRIGHTDATA_API_TOKEN`
   - **Value:** `80a23578-3a9e-41d8-9700-72d8034124f3`
4. Click **Save**

### Step 4: Wait for Auto-Redeploy

Render will automatically redeploy the service (2-3 minutes).

Watch for:
- "Deploying..." status
- "Live" status when complete

---

## Validation

### Check Render Logs

After redeploy, check logs for Agent 4:

```bash
# Should now see:
✅ "🔗 Agent 4: Finding LinkedIn + Tenure (specialist)..."
✅ BrightData MCP tools being called
✅ Tenure values extracted
```

### Test Course 142

```bash
curl -X POST https://agent7-water-hazards.onrender.com/enrich-course \
  -H 'Content-Type: application/json' \
  -d '{
    "course_id": 142,
    "course_name": "Country Club of Fairfax",
    "state_code": "VA",
    "use_test_tables": false
  }'
```

**Expected:**
- Agent 4 runs successfully
- LinkedIn URLs found for contacts
- Tenure extracted
- Comprehensive data (title, company, education, etc.)

### Validate in Database

```sql
SELECT
    contact_name,
    linkedin_url,
    tenure_years,
    linkedin_full_title,
    linkedin_company,
    education,
    certifications
FROM golf_course_contacts
WHERE golf_course_id = 142;
```

**Expected:** 3 contacts with LinkedIn data and comprehensive fields populated

---

## Success Criteria

- ✅ Render logs show "Agent 4: Finding LinkedIn..."
- ✅ BrightData tools called (search_engine + scrape_as_markdown)
- ✅ At least 2/3 contacts have LinkedIn URLs
- ✅ At least 1/3 contacts have tenure data
- ✅ Comprehensive fields extracted (title, company, etc.)
- ✅ No errors in logs
- ✅ Cost per course < $0.20

---

**After validation:** Document this as Pattern 17 in our testing framework!
