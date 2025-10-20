---
name: Golf Enrichment Testing SOP
description: Complete testing workflow for golf enrichment agents - from development in teams/ through Docker testing to Render deployment. Use when testing agent code changes, validating enrichment results, auditing database writes, fixing bugs, or preparing for production deployment. Includes field validation, database audit queries, and multi-course testing procedures.
allowed-tools: Read, Bash, Edit, Grep, Glob, mcp__supabase__execute_sql, mcp__supabase__list_tables, TodoWrite
---

# Golf Enrichment Testing SOP

## Purpose

Systematic testing workflow to ensure golf enrichment agents work correctly before deploying to Render production.

**Key Principle:** Test thoroughly in teams/ environment, then sync to production/, then deploy to Render.

---

## 🔄 Development Workflow

```
┌──────────────────────────────┐
│  1. DEVELOP in /teams        │
│  - Edit agents               │
│  - Update orchestrator       │
│  - Fix bugs                  │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│  2. TEST with Docker         │
│  - Build from teams/         │
│  - Test with real courses    │
│  - Validate ALL fields       │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│  3. AUDIT with Supabase MCP  │
│  - Query database records    │
│  - Verify all fields present │
│  - Compare expected results  │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│  4. TEST 3+ Courses          │
│  - Ensure consistency        │
│  - No regressions            │
│  - Document results          │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│  5. SYNC to /production      │
│  - Copy tested code          │
│  - Verify sync complete      │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│  6. DEPLOY to Render         │
│  - git commit + push         │
│  - Monitor deployment        │
│  - Test production endpoint  │
└──────────────────────────────┘
```

---

## 📋 Pre-Testing Checklist

### Environment Setup

- [ ] `.env` file exists in `teams/golf-enrichment/`
- [ ] All required API keys populated:
  - [ ] ANTHROPIC_API_KEY
  - [ ] PERPLEXITY_API_KEY
  - [ ] HUNTER_API_KEY
  - [ ] SUPABASE_URL
  - [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] Docker running on machine
- [ ] `docker-compose.yml` builds from teams (context: `.`)
- [ ] Required files in teams/:
  - [ ] Dockerfile
  - [ ] api.py
  - [ ] requirements.txt
  - [ ] template/
  - [ ] agents/ (all 8 agents)
  - [ ] orchestrator.py

### Code Verification

```bash
cd teams/golf-enrichment

# Verify key fixes present
grep -n 'course_id: int' orchestrator.py  # Should show course_id parameter
grep -n 'total_cost' orchestrator.py  # Should show total_cost passing
grep -n 'agent_cost_usd' agents/agent8_supabase_writer.py  # Should show cost writing
grep -n 'contacts_page_url' agents/agent2_data_extractor.py  # Should show URL extraction
```

---

## 🎯 Test Course Selection

### Query Database for Test Candidates

```sql
SELECT
  id,
  course_name,
  state_code,
  enhancement_status,
  (SELECT COUNT(*) FROM golf_course_contacts WHERE golf_course_id = golf_courses.id) as contact_count
FROM golf_courses
WHERE
  enhancement_status = 'pending'
  AND state_code = 'VA'
ORDER BY id
LIMIT 10;
```

### Selection Criteria

**Good test courses:**
- ✅ Status: 'pending' (not already enriched)
- ✅ Real course name (exists in VSGA directory)
- ✅ Different naming patterns (test edge cases)

**Use MCP tool:**
```
mcp__supabase__execute_sql with above query
```

**Record course details:**
- Course ID
- Exact course name (copy from database)
- Current status
- Existing contact count

---

## 🐳 Docker Testing Procedure

### Step 1: Start Docker

```bash
cd teams/golf-enrichment

# Stop old container if running
docker-compose down

# Rebuild from teams code
docker-compose up --build -d

# Wait for startup
sleep 5

# Verify healthy
curl http://localhost:8000/health
```

**Expected:** `{"status": "healthy"}`

---

### Step 2: Run Enrichment

**CRITICAL:** Always include `course_id` parameter to prevent duplicates!

```bash
curl -X POST http://localhost:8000/enrich-course \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "[Exact name from database]",
    "state_code": "VA",
    "course_id": [ID from database],
    "use_test_tables": false
  }' \
  -o /tmp/course[ID]-test.json \
  -w "\n\nHTTP Status: %{http_code}\nTotal Time: %{time_total}s\n"
```

**Why these parameters:**
- `course_name`: Exact name from database (critical for Agent 1)
- `course_id`: Ensures correct course updated (prevents name mismatch duplicates)
- `use_test_tables: false`: Test tables have wrong schema, use production schema

---

### Step 3: Monitor Logs

**In another terminal:**

```bash
docker logs golf-enrichment-test -f
```

**Watch For Success Indicators:**

```
✅ Using provided course_id: [ID]
✅ Orchestrator completed: ... - Success: True, Contacts: X, Cost: $0.XX
💾 Course ID: [ID]
💾 Contacts Written: X
✅ Webhook sent successfully for course_id=[ID]
```

**Watch For Failure Indicators:**

```
❌ Agent 1 failed: Course URL not found
❌ Agent 8 failed: [constraint violation]
Error: 'int' object is not subscriptable
```

---

## ✅ Validation Checklist

### API Response Validation

```bash
# Pretty print response
cat /tmp/course[ID]-test.json | python -m json.tool

# Check key fields
cat /tmp/course[ID]-test.json | python -c "
import json, sys
data = json.load(sys.stdin)
print(f'Success: {data.get(\"success\")}')
print(f'Course ID: {data.get(\"course_id\")}')
print(f'Contacts: {data.get(\"summary\", {}).get(\"contacts_enriched\")}')
print(f'Cost: \${data.get(\"summary\", {}).get(\"total_cost_usd\")}')
print(f'agent8 exists: {\"agent8\" in data.get(\"agent_results\", {})}')
print(f'agent8.course_id: {data.get(\"agent_results\", {}).get(\"agent8\", {}).get(\"course_id\")}')
"
```

**Required Checks:**

- [ ] `success`: true
- [ ] `summary.contacts_enriched` > 0
- [ ] `summary.total_cost_usd` < 0.20
- [ ] `agent_results.agent8` exists
- [ ] `agent_results.agent8.course_id` = [expected ID]
- [ ] `course_id` at top level = [expected ID]
- [ ] `contacts_written` > 0
- [ ] `error`: null

---

### Database Validation with Supabase MCP

**Query Course Record:**

Use `mcp__supabase__execute_sql` with:

```sql
SELECT
  id,
  course_name,
  state_code,
  website,
  phone,
  segment,
  segment_confidence,
  water_hazards,
  water_hazard_confidence,
  enhancement_status,
  enrichment_completed_at,
  agent_cost_usd,
  contacts_page_url,
  contacts_page_search_method,
  contacts_page_found_at
FROM golf_courses
WHERE id = [TEST_COURSE_ID];
```

**Required Field Checks:**

- [ ] `id` = [TEST_COURSE_ID] (correct course updated)
- [ ] `enhancement_status` = 'complete'
- [ ] `enrichment_completed_at` = recent timestamp
- [ ] `segment` = 'budget' or 'high-end'
- [ ] `segment_confidence` = 1-10
- [ ] `water_hazards` = integer
- [ ] **`agent_cost_usd` = NOT NULL** ← CRITICAL
- [ ] **`contacts_page_url` = URL string (not empty)** ← CRITICAL
- [ ] `contacts_page_search_method` = "agent2_extraction"
- [ ] `contacts_page_found_at` = timestamp

**If ANY field is null/empty that should have data → STOP, FIX, RETEST**

---

**Query Contact Records:**

```sql
SELECT
  contact_id,
  golf_course_id,
  contact_name,
  contact_title,
  contact_email,
  contact_phone,
  contact_source,
  email_confidence_score,
  email_discovery_method,
  phone_confidence,
  phone_source,
  linkedin_url,
  tenure_years
FROM golf_course_contacts
WHERE golf_course_id = [TEST_COURSE_ID]
ORDER BY contact_name;
```

**Required Contact Checks:**

For EACH contact:

- [ ] `golf_course_id` = [TEST_COURSE_ID]
- [ ] `contact_source` = 'website_scrape' (REQUIRED)
- [ ] `contact_email` populated (for most contacts)
- [ ] `email_confidence_score` between 0-100
- [ ] `email_discovery_method` populated
- [ ] `contact_phone` populated (for most contacts)
- [ ] `phone_confidence` between 0-100
- [ ] `phone_source` populated

**Acceptable if null:**
- `linkedin_url` (Agent 3 may not find)
- `tenure_years` (Agent 6.5 may fail)

---

## 🔍 Detailed Field Audit

### Critical Fields (Must Fix if Missing)

#### agent_cost_usd
**Location:** `golf_courses.agent_cost_usd`
**Should Be:** Dollar amount (e.g., 0.1119)
**If Null:**
1. Check orchestrator calculates total_cost_usd BEFORE Agent 8
2. Check orchestrator passes total_cost to Agent 8
3. Check Agent 8 signature accepts total_cost parameter
4. Check Agent 8 writes to course_record["agent_cost_usd"]

#### contacts_page_url
**Location:** `golf_courses.contacts_page_url`
**Should Be:** URL to staff directory page
**If Empty:**
1. Check Agent 2 prompt includes contacts page extraction
2. Check Agent 2 returns contacts_page_url in data dict
3. Check Agent 8 writes course_data["data"]["contacts_page_url"]

#### contact_source
**Location:** `golf_course_contacts.contact_source`
**Should Be:** 'website_scrape'
**If Null:** Database constraint will reject insert - fix Agent 8

---

## 🧪 Multi-Course Testing

### Test Sequence

**Test at least 3 courses before deploying:**

1. **Course with no contacts** - Fresh enrichment
2. **Course with different naming** - Test name matching
3. **Course with existing contacts** - Test upsert logic

### For Each Course:

```bash
# 1. Query course details
mcp__supabase__execute_sql: SELECT id, course_name, enhancement_status FROM golf_courses WHERE id = [ID]

# 2. Run enrichment
curl -X POST http://localhost:8000/enrich-course \
  -d '{"course_name": "[NAME]", "state_code": "VA", "course_id": [ID], "use_test_tables": false}' \
  -o /tmp/course[ID]-test.json

# 3. Validate response (checklist above)

# 4. Audit database (SQL queries above)

# 5. Document results
```

### Testing Log Template

```markdown
## Test Run [ID]: Course [NAME]
**Date:** [YYYY-MM-DD HH:MM]
**Course ID:** [ID]

### Pre-Test State:
- enhancement_status: [pending/complete]
- Existing contacts: [count]

### Test Results:
- HTTP Status: [200/500]
- Duration: [seconds]
- Cost: $[amount]
- Contacts Enriched: [count]
- Success: [true/false]

### Field Validation:
- [ ] agent_cost_usd: [value or NULL]
- [ ] contacts_page_url: [URL or EMPTY]
- [ ] segment: [value]
- [ ] water_hazards: [count]
- [ ] Correct course_id updated: [yes/no]

### Issues Found:
- [List any issues]

### Passed: [YES/NO]
```

---

## 🚨 Common Issues & Quick Fixes

### Issue: agent_cost_usd is null

**Root Cause:** Cost calculated after Agent 8 runs
**Fix:** Move cost calculation BEFORE Agent 8 call
**Files:** `orchestrator.py` (calculate total_cost_usd before line ~315)

---

### Issue: contacts_page_url is empty

**Root Cause:** Agent 2 not extracting staff page URL
**Fix:** Update Agent 2 prompt to extract contacts page
**Files:** `agents/agent2_data_extractor.py` (system_prompt)

---

### Issue: Wrong course ID updated (duplicate created)

**Root Cause:** Missing course_id parameter, name mismatch
**Example:** Request "Brambleton Regional Park" but Agent 2 extracts "Brambleton Golf Course"
**Fix:** ALWAYS pass course_id parameter
**Prevention:** Never test without course_id

---

### Issue: Agent 1 fails "Course not found"

**Root Cause:** Course name not in VSGA directory
**Fix:** Use real course name from database
**Future:** Implement Agent 1 fallback (Google search, Perplexity)

---

### Issue: Logs show "Contacts: 0" but enrichment succeeded

**Root Cause:** api.py using wrong field name
**Fix:** Use `contacts_enriched` not `contact_count`
**File:** `teams/golf-enrichment/api.py` line ~425

---

## 🔧 Sync to Production

### When to Sync

**Only sync when:**
- [ ] All Docker tests pass
- [ ] 3+ courses tested successfully
- [ ] All critical fields populated
- [ ] No errors in logs
- [ ] Team reviews changes

### Sync Command

```bash
# From repo root
python production/scripts/sync_to_production.py golf-enrichment
```

### Verify Sync

```bash
# Check files synced
ls -la production/golf-enrichment/

# Verify key changes present
grep -n "course_id" production/golf-enrichment/orchestrator.py
grep -n "agent_cost_usd" production/golf-enrichment/agents/agent8_supabase_writer.py
grep -n "contacts_page_url" production/golf-enrichment/agents/agent2_data_extractor.py

# Compare critical files
diff teams/golf-enrichment/orchestrator.py production/golf-enrichment/orchestrator.py
# Should show: "Files are identical" or "Identical"
```

---

## 🚀 Render Deployment

### Pre-Deployment Checks

- [ ] Production code synced and verified
- [ ] Git status clean in production/
- [ ] Edge function updated (if API changes made)
- [ ] All tests passed
- [ ] DockerTestToRenderProd.md updated with test results

### Edge Function Update (If Needed)

**If API signature changed (e.g., added course_id parameter):**

Update `supabase/functions/trigger-agent-enrichment/index.ts`:

```typescript
// Add course_id to payload
const payload = {
  course_name: record.course_name,
  state_code: record.state_code,
  course_id: record.id,  // ADD THIS
  use_test_tables: false
};
```

### Deploy Command

```bash
cd production/golf-enrichment

# Check what changed
git status
git diff

# Stage changes
git add .

# Commit with detailed message
git commit -m "feat: [description of changes]

- [List key changes]
- [Testing results]
- [Fields fixed]

Tested: Courses [IDs] enriched successfully
All required fields validated"

# Deploy (auto-deploys to Render if autoDeploy: true)
git push origin main
```

### Monitor Deployment

1. Go to https://dashboard.render.com
2. Find `golf-enrichment-api` service
3. Watch deploy logs
4. Wait for "Live" status (~2-3 minutes)

### Post-Deployment Validation

```bash
# Health check
curl https://agent7-water-hazards.onrender.com/health

# Test with real course (will cost ~$0.12)
curl -X POST https://agent7-water-hazards.onrender.com/enrich-course \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "[COURSE_NAME]",
    "state_code": "VA",
    "course_id": [ID],
    "use_test_tables": false
  }'

# Check Render logs for success
# Verify database updated correctly
# Check webhook fired
# Verify ClickUp task created
```

---

## 📊 Quality Metrics

### Per-Course Thresholds

- **Cost:** < $0.20 (target: $0.12-$0.15)
- **Duration:** < 3 minutes (target: 2-2.5 minutes)
- **Contact Success Rate:** > 80% have email
- **Phone Success Rate:** > 70% have phone

### Aggregate Metrics

After testing 3+ courses:

- **Average Cost:** < $0.15
- **Success Rate:** 100% (all courses complete)
- **Field Completeness:** 100% for critical fields
- **No Duplicates:** 0 duplicate courses created

---

## 🎓 Best Practices

### DO:
- ✅ Always use real course names from database
- ✅ Always pass course_id parameter
- ✅ Test 3+ courses before deploying
- ✅ Audit with Supabase MCP after each test
- ✅ Document issues in DockerTestToRenderProd.md
- ✅ Validate ALL critical fields
- ✅ Keep testing log

### DON'T:
- ❌ Test without course_id parameter
- ❌ Use fake course names
- ❌ Deploy after only 1 test
- ❌ Skip database validation
- ❌ Ignore null fields
- ❌ Test production endpoint before Docker passes
- ❌ Sync to production with failing tests

---

## 📚 Supporting Documentation

For detailed information, see:

- **Field Requirements:** [FIELD_VALIDATION.md](FIELD_VALIDATION.md)
- **Audit Queries:** [AUDIT_QUERIES.md](AUDIT_QUERIES.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Workflow Details:** `teams/golf-enrichment/DockerTestToRenderProd.md`

---

## 🔄 Typical Testing Session

```
1. Query database for test course → mcp__supabase__execute_sql
2. Note course ID and exact name
3. Start Docker → docker-compose up --build -d
4. Run enrichment with course_id
5. Monitor logs → docker logs -f
6. Validate response → check JSON structure
7. Audit database → mcp__supabase__execute_sql
8. Check ALL fields from FIELD_VALIDATION.md
9. Document results
10. Repeat for 2-3 more courses
11. If all pass → Sync to production
12. Deploy to Render
13. Test production endpoint
14. Verify automation (webhook, ClickUp)
```

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Maintained By:** Engineering Team
