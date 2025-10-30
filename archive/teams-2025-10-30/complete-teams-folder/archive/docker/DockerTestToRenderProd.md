# Docker Test → Render Production Workflow

**Purpose:** Safe, systematic workflow for testing in teams/, then deploying to Render.
**Strategy:** Test teams code locally, sync to production, deploy to Render.
**Last Updated:** 2025-10-20

---

## 🎯 Correct Development Workflow

```
┌─────────────────────────────────────────────────────┐
│  STEP 1: DEVELOP & EDIT                             │
│  Location: /teams/golf-enrichment/                  │
│  - Edit agents, orchestrator, api                   │
│  - Make fixes and improvements                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  STEP 2: TEST LOCALLY (Docker)                      │
│  Location: /teams/golf-enrichment/                  │
│  Command: docker-compose up --build                 │
│  - Builds FROM teams/ code (NOT production!)        │
│  - Tests with production Supabase tables            │
│  - Validates all fixes                              │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  STEP 3: SYNC TO PRODUCTION                         │
│  Command: python production/scripts/sync_to_production.py golf-enrichment  │
│  - Copies teams/agents/ → production/agents/        │
│  - Copies teams/orchestrator.py → production/       │
│  - Copies shared/utils/ → production/template/utils │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  STEP 4: DEPLOY TO RENDER                           │
│  Location: /production/golf-enrichment/             │
│  Command: git add . && git commit && git push       │
│  - Render auto-deploys from production/             │
│  - Live API at agent7-water-hazards.onrender.com    │
└─────────────────────────────────────────────────────┘
```

**Why This Order:**
- ✅ Test teams code BEFORE syncing (catch issues early)
- ✅ Production stays clean (only receives tested code)
- ✅ Render only deploys verified code
- ✅ Faster iteration (no deploy wait for testing)

---

## 🔧 Teams Testing Environment Setup

### Required Files in teams/golf-enrichment/

**Core Development Files:**
- ✅ `agents/` - All 8 agent implementations
- ✅ `orchestrator.py` - Workflow coordinator
- ✅ `.env` - API keys (gitignored)
- ✅ `.env.example` - Template for API keys

**Docker Testing Files (copied from production):**
- ✅ `Dockerfile` - Container build instructions
- ✅ `api.py` - FastAPI wrapper
- ✅ `requirements.txt` - Python dependencies
- ✅ `template/` - Shared utilities
- ✅ `docker-compose.yml` - Local testing config

**How to Setup (One-time):**

```bash
cd teams/golf-enrichment

# Copy deployment files from production (if not already present)
cp ../../production/golf-enrichment/Dockerfile .
cp ../../production/golf-enrichment/api.py .
cp ../../production/golf-enrichment/requirements.txt .
cp -r ../../production/golf-enrichment/template .

# Create .env from example
cp .env.example .env
# Edit .env with your API keys

# Verify docker-compose builds from teams
grep "context:" docker-compose.yml
# Should show: context: .
```

**These files should be gitignored in teams/ (only for local testing):**
- Dockerfile (synced from production)
- api.py (synced from production)
- requirements.txt (synced from production)
- template/ (synced from production)

---

## 📋 Pre-Testing Checklist

### Before You Start

- [ ] `.env` file exists in `teams/golf-enrichment/`
- [ ] All required API keys populated (ANTHROPIC, PERPLEXITY, HUNTER, SUPABASE)
- [ ] Deployment files copied to teams/ (Dockerfile, api.py, requirements.txt, template/)
- [ ] docker-compose.yml builds from teams: `context: .`
- [ ] Docker running on your machine
- [ ] Git status clean in teams/ (code ready to test)

### Verify Current Fixes

```bash
# Check orchestrator has agent8 result storage
grep -n "agent_results\[\"agent8\"\]" teams/golf-enrichment/orchestrator.py
# Should show line ~319

# Check api.py has correct field names
grep -n "contacts_enriched" teams/golf-enrichment/api.py
# Should show line ~425
```

---

## 🎯 Selecting a Test Course

### Use REAL Virginia Courses from Database

**Why:** Agent 1 searches VSGA directory - fake names will fail at Agent 1

**Query Database for Good Test Candidates:**

```sql
-- Find courses ready for enrichment
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
ORDER BY created_at DESC
LIMIT 10;
```

**Good Test Candidates (from Supabase):**

| ID | Course Name | Status | Contacts | Best For |
|----|-------------|--------|----------|----------|
| 432 | Waterfront Country Club, The | pending | 0 | Fresh enrichment test |
| 433 | Washington Golf and Country Club | pending | 0 | Fresh enrichment test |
| 428 | Westlake Golf and Country Club | pending | 0 | Fresh enrichment test |
| 435 | The Club at Glenmore | pending | 2 | Test with existing contacts |

**Recommended for Testing:** ID 428 - "Westlake Golf and Country Club"
- ✅ Status: pending (not enriched yet)
- ✅ No contacts (fresh test)
- ✅ Real course in VSGA directory

**Important:**
- Use the **exact course name** from database
- Include "The" if it's part of the name
- Match capitalization exactly

---

## 🐳 Phase 1: Docker Local Testing

### 1.1 Stop Old Container (if running)

```bash
cd teams/golf-enrichment

# Stop and remove old container
docker-compose down

# Remove old image to force rebuild
docker rmi golf-enrichment-golf-enrichment-api || true
```

**Why:** Ensures we're testing latest teams/ code, not cached production code

---

### 1.2 Start Docker Container

```bash
cd teams/golf-enrichment

# Build and start
docker-compose up --build
```

**Expected Output:**
```
✅ Successfully imported Agent 7
✅ Successfully imported Orchestrator
🏌️ Golf Course Enrichment API Starting...
Service: Full Enrichment Pipeline (Agents 1-8)
```

**If Build Fails:**
- Check Dockerfile exists at `production/golf-enrichment/Dockerfile`
- Check orchestrator.py exists at `production/golf-enrichment/orchestrator.py` (not in agents/)
- Check `.env` file has all required keys

---

### 1.2 Health Check

In another terminal:

```bash
# Check API is responding
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "service": "agent7-water-hazards",
  "timestamp": "2025-10-20T...",
  "dependencies": {
    "claude_cli": "installed",
    "perplexity_api": "configured"
  }
}
```

---

### 1.3 Run Test Enrichment

**IMPORTANT:** Use REAL course name from database (see "Selecting a Test Course" section)

```bash
# Recommended test course: ID 428
curl -X POST http://localhost:8000/enrich-course \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "Westlake Golf and Country Club",
    "state_code": "VA",
    "use_test_tables": false
  }' \
  -o /tmp/test-result.json
```

**Why `use_test_tables: false`?**
- Test tables have wrong schema (missing required fields)
- Production tables have correct constraints and enums
- Tests real production environment locally

**Why Real Course Names:**
- Agent 1 searches VSGA directory (fake names fail)
- See "Known Issues" section for Agent 1 fallback enhancement

---

### 1.4 Monitor Logs

Watch Docker logs for:

**✅ SUCCESS INDICATORS:**

```
🔍 [1/8] Agent 1: Finding course URL...
   ✅ Found: https://...
   💰 Cost: $0.0024 | ⏱️  2.1s

📄 [2/8] Agent 2: Extracting course data...
   ✅ Course: Docker Test Course 001
   👥 Staff: 2 contacts found
   💰 Cost: $0.0156 | ⏱️  8.3s

...

💾 [6/8] Agent 8: Writing to Supabase...
   🔌 Connecting to Supabase (PRODUCTION tables)...
   🏌️ Upserting course: Docker Test Course 001...
   👥 Inserting 2 contacts...
   ✅ Success! Course + 2 contacts written to Supabase

✅ SUCCESS: Docker Test Course 001
💰 Total Cost: $0.1234
⏱️  Total Time: 142.5s
👥 Contacts: 2
💾 Course ID: abc12345...
💾 Contacts Written: 2
```

**🔍 KEY VALIDATION:**
- ✅ `Contacts: 2` (NOT "Contacts: 0") - **FIX #1 VERIFIED**
- ✅ `Course ID: abc12345...` appears - **FIX #2 VERIFIED**
- ✅ `Contacts Written: 2` - **Agent 8 SUCCESS**

---

**❌ FAILURE INDICATORS:**

```
❌ FAILED: Docker Test Course 001
Error: new row for relation "golf_courses" violates check constraint "..."
```

**Common Failures:**
1. **Missing `contact_source`** - Agent 8 not setting required field
2. **Wrong `enrichment_status`** - Using invalid enum value
3. **Missing `state_code`** - Required field not passed through

**If Failed:** Stop here, fix the issue, rebuild Docker, retry Phase 1

---

## ✅ Phase 2: Validation

### 2.1 Check API Response

Save the curl response to a file:

```bash
curl -X POST http://localhost:8000/enrich-course \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Docker Test Course 001", "state_code": "VA", "use_test_tables": false}' \
  > test-result.json

# Pretty print
cat test-result.json | python -m json.tool
```

**Verify Response Structure:**

```json
{
  "success": true,
  "course_name": "Docker Test Course 001",
  "state_code": "VA",
  "json_file": null,
  "summary": {
    "total_cost_usd": 0.1234,
    "total_duration_seconds": 142.5,
    "contacts_enriched": 2,  // ✅ Should be 2, not 0
    "agent_costs": { ... }
  },
  "error": null,
  "agent_results": {
    "agent1": { ... },
    "agent2": { ... },
    "agent6": { ... },
    "agent7": { ... },
    "agent8": {  // ✅ CRITICAL: This should exist!
      "success": true,
      "course_id": "abc12345-...",
      "contacts_written": 2,
      "error": null
    }
  },
  "course_id": "abc12345-...",  // ✅ Should match agent8.course_id
  "contacts_written": 2
}
```

**Critical Checks:**
- [ ] `summary.contacts_enriched` = 2 (not 0)
- [ ] `agent_results.agent8` exists and has `course_id`
- [ ] `course_id` at top level matches `agent_results.agent8.course_id`
- [ ] `contacts_written` = 2

---

### 2.2 Verify Database Records

**Check Course Record:**

```sql
-- In Supabase SQL Editor or via psql
SELECT
  id,
  course_name,
  state_code,
  segment,
  segment_confidence,
  water_hazards,
  enhancement_status,
  enrichment_completed_at,
  created_at
FROM golf_courses
WHERE course_name LIKE 'Docker Test%'
ORDER BY created_at DESC
LIMIT 1;
```

**Expected:**
- ✅ One row returned
- ✅ `enhancement_status` = 'complete'
- ✅ `enrichment_completed_at` is NOT NULL
- ✅ `segment` = 'budget' or 'high-end' (from Agent 6)
- ✅ `water_hazards` = integer (from Agent 7)

---

**Check Contact Records:**

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
  phone_confidence,
  created_at
FROM golf_course_contacts
WHERE golf_course_id = (
  SELECT id FROM golf_courses
  WHERE course_name = 'Docker Test Course 001'
);
```

**Expected:**
- ✅ 2 rows returned (or however many contacts found)
- ✅ `contact_source` = 'website_scrape' (REQUIRED field set)
- ✅ `contact_email` populated for at least 1 contact
- ✅ `contact_phone` populated for at least 1 contact
- ✅ `email_confidence_score` between 0-100
- ✅ `phone_confidence` between 0-100

---

### 2.3 Verify Webhook (Optional)

Check Supabase Edge Function logs to see if webhook was received:

1. Go to Supabase Dashboard → Edge Functions → `receive-agent-enrichment`
2. Check logs for recent invocations
3. Should see payload with `course_id`, `contacts`, `success: true`

**If webhook didn't fire:**
- Check `api.py:430` condition: `if result.get('course_id'):`
- Verify `course_id` exists in orchestrator response (Phase 2.1)

---

## 🚀 Phase 3: Render Deployment

### 3.1 Pre-Deployment Checks

**All must pass:**

- [ ] Docker local test succeeded
- [ ] Database validation passed (Phase 2.2)
- [ ] Logs show correct contact counts
- [ ] `agent_results.agent8` exists in response
- [ ] No errors in Docker container logs

---

### 3.2 Commit Changes

```bash
cd production/golf-enrichment

# Check what changed
git status
git diff

# Stage changes
git add .

# Commit with descriptive message
git commit -m "fix: Correct field names and agent8 result storage

- Fix api.py: contact_count → contacts_enriched, total_cost → total_cost_usd
- Store Agent 8 result in orchestrator agent_results dict
- Fix sync script to copy orchestrator to correct location
- Remove duplicate orchestrator.py from agents/

Testing:
- Docker local test passed
- Database writes verified
- Logs show correct contact counts

Fixes issues from ENGINEERING_HANDOFF_OCT18.md"
```

---

### 3.3 Deploy to Render

```bash
# Push to trigger auto-deploy
git push origin main

# Monitor deployment
# Go to: https://dashboard.render.com
# Find: golf-enrichment-api service
# Watch: Deploy logs
```

**Expected Deploy Time:** 2-3 minutes

**Deploy Log Success Indicators:**
```
==> Building...
==> Installing dependencies...
==> Starting server...
✅ Successfully imported Orchestrator
🏌️ Golf Course Enrichment API Starting...
```

---

### 3.4 Health Check Production

```bash
# Wait ~30 seconds after deploy shows "Live"

curl https://agent7-water-hazards.onrender.com/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "agent7-water-hazards",
  "timestamp": "2025-10-20T...",
  "dependencies": {
    "claude_cli": "installed",
    "perplexity_api": "configured"
  }
}
```

---

## 🧪 Phase 4: Production Verification

### 4.1 Test Production Endpoint

**⚠️ WARNING:** This will write to production database!

```bash
# Use another unique test name
curl -X POST https://agent7-water-hazards.onrender.com/enrich-course \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "Render Test Course 001",
    "state_code": "VA",
    "use_test_tables": false
  }'
```

---

### 4.2 Monitor Render Logs

In Render Dashboard → Logs:

**Watch for:**
- ✅ `Orchestrator completed: Render Test Course 001 - Success: True, Contacts: 2` (not 0!)
- ✅ `Course ID: abc12345...`
- ✅ `Webhook sent successfully for course_id=...`

**If webhook fires:**
- 🎉 **FULL SUCCESS!** Webhook integration working
- Check ClickUp List 901413111587 for new task

---

### 4.3 Verify Database

Same SQL queries as Phase 2.2, but looking for "Render Test Course 001"

```sql
-- Check both test courses exist
SELECT id, course_name, enhancement_status, enrichment_completed_at
FROM golf_courses
WHERE course_name LIKE '%Test Course%'
ORDER BY created_at DESC;

-- Should show:
-- - Docker Test Course 001
-- - Render Test Course 001
```

---

## 🧹 Phase 5: Cleanup

### 5.1 Delete Test Records

**After successful validation:**

```sql
-- Delete contacts first (FK constraint)
DELETE FROM golf_course_contacts
WHERE golf_course_id IN (
  SELECT id FROM golf_courses
  WHERE course_name LIKE '%Test Course%'
);

-- Delete courses
DELETE FROM golf_courses
WHERE course_name LIKE '%Test Course%';

-- Verify cleanup
SELECT COUNT(*) FROM golf_courses WHERE course_name LIKE '%Test Course%';
-- Should return: 0
```

---

### 5.2 Stop Docker (Optional)

```bash
cd teams/golf-enrichment

# Stop containers
docker-compose down

# Remove volumes (optional - clears cached data)
docker-compose down -v
```

---

## 🔄 Rollback Procedures

### If Production Deploy Fails

**Option A: Revert Git Commit**

```bash
cd production/golf-enrichment

# Find last working commit
git log --oneline -5

# Revert to previous commit (replace <hash> with actual commit)
git revert <hash>
git push origin main

# Render will auto-deploy the revert
```

---

**Option B: Emergency Manual Fix**

If you need to quickly patch production:

```bash
# Edit production files directly (breaks normal workflow - emergency only!)
vim production/golf-enrichment/api.py

# Commit and push immediately
git add . && git commit -m "hotfix: Emergency fix" && git push
```

**⚠️ WARNING:** Only use this in emergencies. Normal workflow is teams → sync → production

---

### If Database Gets Corrupted

**Restore from Backup:**

1. Go to Supabase Dashboard → Database → Backups
2. Find backup from before testing
3. Click "Restore"
4. Wait ~5 minutes
5. Re-run Phase 4 verification

---

## 🐛 Troubleshooting

### Issue: "Contacts: 0" in logs

**Root Cause:** `api.py` using wrong field name

**Fix:**
```python
# Check line 425 in production/golf-enrichment/api.py
# Should be:
f"Contacts: {result.get('summary', {}).get('contacts_enriched', 0)}, "

# Not:
f"Contacts: {result.get('summary', {}).get('contact_count', 0)}, "
```

**Verify Fix:**
```bash
grep "contacts_enriched" production/golf-enrichment/api.py
```

---

### Issue: Webhook Not Firing

**Root Cause:** `agent_results.agent8` doesn't exist

**Check:**
```bash
# Should show line ~319
grep "agent_results\[\"agent8\"\]" teams/golf-enrichment/orchestrator.py
```

**Fix in orchestrator.py:**
```python
# After line 316, add:
result["agent_results"]["agent8"] = supabase_result
```

---

### Issue: Missing `contact_source` Error

**Error Message:**
```
new row for relation "golf_course_contacts" violates check constraint
```

**Root Cause:** Agent 8 not setting required `contact_source` field

**Check:** `teams/golf-enrichment/agents/agent8_supabase_writer.py:~163`

**Should have:**
```python
contact_record = {
    "contact_source": "website_scrape",  # REQUIRED
    ...
}
```

---

### Issue: Docker Build Fails

**Error:** `Cannot find orchestrator.py`

**Cause:** `orchestrator.py` not at production root

**Fix:**
```bash
# Re-sync
python production/scripts/sync_to_production.py golf-enrichment

# Verify file exists
ls -la production/golf-enrichment/orchestrator.py
```

---

### Issue: Claude CLI Not Found

**Error:** `claude: command not found`

**Cause:** Node.js or Claude CLI not installed in container

**Fix:** Check `Dockerfile:23-26`
```dockerfile
RUN npm install -g @anthropic-ai/claude-code
RUN which claude && claude --version
```

---

## 📊 Success Metrics

### Phase 1 (Docker) Complete When:
- [ ] Container builds without errors
- [ ] Health check returns 200
- [ ] Enrichment completes successfully
- [ ] Logs show `Contacts: 2` (not 0)
- [ ] Database has test course + contacts

### Phase 2 (Validation) Complete When:
- [ ] Response JSON has `agent_results.agent8`
- [ ] `course_id` exists at top level
- [ ] Database records verified in SQL
- [ ] All required fields populated

### Phase 3 (Deploy) Complete When:
- [ ] Git push succeeds
- [ ] Render deploy shows "Live"
- [ ] Health check passes on production URL
- [ ] No errors in Render logs

### Phase 4 (Production) Complete When:
- [ ] Production endpoint test succeeds
- [ ] Logs show correct contact counts
- [ ] Webhook fires (check Supabase logs)
- [ ] ClickUp task created (if webhook working)
- [ ] Database has production test course

### Phase 5 (Cleanup) Complete When:
- [ ] Test courses deleted from database
- [ ] `SELECT COUNT(*)` returns 0 for test courses
- [ ] Docker containers stopped (optional)

---

## 📝 Testing Log Template

Copy this for each test run:

```
## Test Run: [DATE/TIME]
**Tester:** [Your Name]
**Goal:** [What you're testing]

### Phase 1: Docker Local
- [ ] Build succeeded
- [ ] Health check: ✅ / ❌
- [ ] Enrichment: ✅ / ❌
- [ ] Contacts shown: ___ (should be > 0)
- [ ] Course ID: ________________
- **Notes:**

### Phase 2: Validation
- [ ] Response has agent_results.agent8: ✅ / ❌
- [ ] Database course record: ✅ / ❌
- [ ] Database contact records: ___ found
- **Notes:**

### Phase 3: Render Deploy
- [ ] Git push: ✅ / ❌
- [ ] Deploy status: ✅ / ❌
- [ ] Health check: ✅ / ❌
- **Commit hash:** ________________
- **Notes:**

### Phase 4: Production
- [ ] Endpoint test: ✅ / ❌
- [ ] Webhook fired: ✅ / ❌
- [ ] ClickUp task: ✅ / ❌
- **Notes:**

### Phase 5: Cleanup
- [ ] Test data deleted: ✅ / ❌
- **Notes:**

### Overall Result: ✅ SUCCESS / ❌ FAILED
**Next Actions:**
```

---

## 🎓 Best Practices

1. **Always test Docker first** - Never deploy without local validation
2. **Use unique test names** - Makes cleanup and identification easy
3. **Verify database records** - Don't trust logs alone
4. **Keep testing log** - Append test runs to this doc for history
5. **Clean up test data** - Don't pollute production with test courses
6. **Monitor costs** - Each test costs ~$0.12, track spending
7. **Test webhook separately** - Use `/test-agent8` endpoint if needed

---

## 📚 Related Documentation

- **Engineering Handoff:** `teams/golf-enrichment/ENGINEERING_HANDOFF_OCT18.md`
- **Agent 8 Schema:** `teams/golf-enrichment/agents/agent8_supabase_writer.py`
- **API Endpoints:** `production/golf-enrichment/api.py`
- **Orchestrator:** `teams/golf-enrichment/orchestrator.py`
- **Deployment Guide:** `teams/golf-enrichment/supabase/DEPLOYMENT_GUIDE.md` (if exists)

---

## 🔧 Known Issues & Future Improvements

### 🚨 CRITICAL: Agent 1 Fails for Courses Not in VSGA Directory

**Issue Discovered:** 2025-10-20
**Severity:** High - Blocks entire workflow

**Problem:**
- Agent 1 (URL Finder) searches VSGA directory for course URLs
- If course doesn't exist in VSGA, Agent 1 fails with: `"Course URL not found for '....'"`
- **Entire enrichment pipeline fails** (not just Agent 1)
- No fallback mechanism - workflow is all-or-nothing

**Impact:**
- Cannot test with fake course names ("Docker Test Course 001")
- Cannot enrich courses not listed in VSGA directory
- Prevents graceful degradation for edge cases

**Example Failure:**
```json
{
  "success": false,
  "error": "Agent 1 failed: Course URL not found for 'Docker Test Course 001'",
  "summary": {"total_duration_seconds": 8.6},
  "agent_results": {}
}
```

**Proposed Solution:**
1. **Agent 1 Fallback:** If not found in VSGA, try:
   - Google search: `"[course_name] [state_code] golf course"`
   - Perplexity search for official website
   - Return `null` URL instead of failing

2. **Agent 2 Adaptation:** If no URL from Agent 1:
   - Attempt to find course via Google Maps API
   - Search for course contact pages via web search
   - Mark as `discovery_difficulty: 'hard'` in database

3. **Human-in-Loop Fallback:**
   - If all automated discovery fails, create ClickUp task with:
     - Status: "manual_research_needed"
     - Custom field: `discovery_difficulty: 'impossible'`
     - Assignment: Human researcher
   - Do NOT fail entire workflow
   - Mark course as `enhancement_status: 'pending'` (not 'failed')

4. **Graceful Degradation:**
   - Allow enrichment to continue with partial data
   - Each agent should handle missing inputs gracefully
   - Store what we DO know (even if incomplete)

**Workaround for Testing (Current):**
- Use REAL golf course names from VSGA directory
- Examples: "Augustine Golf Club", "Brambleton Regional Park Golf Course"
- Avoid fake test names until Agent 1 fallback implemented

**Action Items:**
- [ ] Implement Agent 1 fallback search strategies
- [ ] Add graceful degradation to orchestrator
- [ ] Create human-in-loop ClickUp task creation
- [ ] Update Agent 2 to handle missing URLs
- [ ] Add `discovery_difficulty` tracking
- [ ] Update tests to verify fallback behavior

**Priority:** P1 - Implement in next sprint
**Assigned To:** TBD
**Related Docs:** `teams/golf-enrichment/agents/agent1_url_finder.py`

---

### 🔧 ENHANCEMENT: Add course_id Parameter to API

**Issue Discovered:** 2025-10-20
**Severity:** Low - Enhancement for edge function integration
**Status:** Future improvement (P2)

**Problem:**
- Current workflow: Supabase edge function triggers enrichment with only `course_name` and `state_code`
- Agent 8 must lookup course ID by course_name (potential for name mismatches)
- If course name changes or has variations, lookup might fail or match wrong course

**Proposed Enhancement:**

**API Changes:**
```python
# api.py - Add course_id parameter
class EnrichCourseRequest(BaseModel):
    course_name: str
    state_code: str
    course_id: int | None = None  # NEW: Optional course ID from edge function
    use_test_tables: bool = False
```

**Orchestrator Changes:**
```python
# orchestrator.py - Accept and pass through course_id
async def enrich_course(
    course_name: str,
    state_code: str = "VA",
    course_id: int | None = None,  # NEW
    use_test_tables: bool = True
):
    # Pass to Agent 8
    supabase_result = await write_to_supabase(
        course_data,
        course_intel,
        water_data,
        enriched_contacts,
        state_code=state_code,
        course_id=course_id,  # NEW
        use_test_tables=use_test_tables
    )
```

**Agent 8 Changes:**
```python
# agent8_supabase_writer.py - Use provided course_id if available
async def write_to_supabase(
    ...,
    course_id: int | None = None,  # NEW
    use_test_tables: bool = True
):
    if course_id:
        # Skip lookup, use provided ID directly
        print(f"   ✅ Using provided course_id: {course_id}")
    else:
        # Current behavior: lookup by course_name
        existing = supabase.table(course_table).select("id").eq("course_name", course_name).maybe_single().execute()
        course_id = existing.data["id"] if existing and existing.data else None
```

**Benefits:**
- ✅ Guaranteed correct course ID from edge function
- ✅ No name mismatch issues
- ✅ Faster (skip lookup query)
- ✅ Backwards compatible (course_id optional)

**Edge Function Update:**
```typescript
// supabase/functions/trigger-agent-enrichment/index.ts
const payload = {
  course_name: record.course_name,
  state_code: record.state_code,
  course_id: record.id,  // NEW: Pass course ID
  use_test_tables: false
};
```

**Testing:**
```bash
# Test with course_id parameter
curl -X POST http://localhost:8000/enrich-course \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "Westlake Golf and Country Club",
    "state_code": "VA",
    "course_id": 428,
    "use_test_tables": false
  }'
```

**Action Items:**
- [ ] Add course_id parameter to EnrichCourseRequest model
- [ ] Update orchestrator.py signature
- [ ] Update agent8_supabase_writer.py to use provided course_id
- [ ] Update edge function to pass course_id
- [ ] Add tests for course_id parameter
- [ ] Update API documentation

**Priority:** P2 - Implement after current fixes deployed
**Assigned To:** TBD
**Related Files:** `api.py`, `orchestrator.py`, `agent8_supabase_writer.py`, `supabase/functions/trigger-agent-enrichment/index.ts`

---

**Last Test Run:** [Add date/time after each successful test]
**Last Updated:** 2025-10-20 (Added course_id parameter enhancement, fixed teams testing environment)
**Maintained By:** Engineering Team
