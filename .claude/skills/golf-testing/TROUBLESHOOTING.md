# Troubleshooting Guide

Common issues encountered during golf enrichment testing and their solutions.

---

## 🚨 Critical Issues (MUST FIX)

### Issue 1: agent_cost_usd is NULL in Database

**Symptom:**
```sql
SELECT agent_cost_usd FROM golf_courses WHERE id = 108;
-- Returns: null
```

**Root Cause:**
- Orchestrator calculates `total_cost_usd` in summary AFTER Agent 8 runs
- Agent 8 doesn't receive the cost to write to database

**Fix:**
```python
# orchestrator.py - BEFORE Agent 8 call (around line 300)
# Calculate cost first
total_cost_usd = round(
    course_data.get("cost", 0) +
    course_intel.get("cost", 0) +
    water_data.get("cost", 0) +
    total_agent3_cost +
    total_agent5_cost +
    total_agent65_cost,
    4
)

# Pass to Agent 8
supabase_result = await write_to_supabase(
    ...,
    total_cost=total_cost_usd,  # ADD THIS
    ...
)

# agent8_supabase_writer.py - Accept parameter
async def write_to_supabase(
    ...,
    total_cost: float = 0.0,  # ADD THIS
    ...
):

# agent8_supabase_writer.py - Write to database
course_record = {
    ...,
    "agent_cost_usd": total_cost,  # ADD THIS
}
```

**Files to Update:**
- `teams/golf-enrichment/orchestrator.py`
- `teams/golf-enrichment/agents/agent8_supabase_writer.py`

**Test After Fix:**
```sql
SELECT agent_cost_usd FROM golf_courses WHERE id = [TEST_ID];
-- Should return: 0.1119 (or similar)
```

---

### Issue 2: contacts_page_url is Empty

**Symptom:**
```sql
SELECT contacts_page_url FROM golf_courses WHERE id = 108;
-- Returns: "" (empty string)
```

**Root Cause:**
- Agent 2 doesn't extract contacts/staff page URL
- Agent 8 tries to write it but gets empty value

**Fix:**
```python
# agent2_data_extractor.py - Update prompt
system_prompt=(
    "Use WebFetch to get the page content. "
    "Extract: course name, website, phone, contacts page URL, and all staff members. "
    "IMPORTANT: Also find the URL of the staff/contacts directory page if it exists (e.g., /staff, /about-us, /team). "
    "Return as JSON:\n"
    "{\n"
    '  "course_name": "...",\n'
    '  "website": "...",\n'
    '  "phone": "...",\n'
    '  "contacts_page_url": "..." or null,\n'  # ADD THIS
    '  "staff": [{...}]\n'
    "}"
)

# agent8_supabase_writer.py - Write fields
course_record = {
    ...,
    "contacts_page_url": course_data.get("data", {}).get("contacts_page_url"),
    "contacts_page_search_method": "agent2_extraction" if course_data.get("data", {}).get("contacts_page_url") else None,
    "contacts_page_found_at": datetime.utcnow().isoformat() if course_data.get("data", {}).get("contacts_page_url") else None
}
```

**Files to Update:**
- `teams/golf-enrichment/agents/agent2_data_extractor.py`
- `teams/golf-enrichment/agents/agent8_supabase_writer.py`

**Test After Fix:**
```bash
# Check Agent 2 output
cat /tmp/test-result.json | python -c "import json, sys; data = json.load(sys.stdin); print(data['agent_results']['agent2']['data'].get('contacts_page_url', 'MISSING'))"
# Should show: URL string

# Check database
mcp__supabase__execute_sql: SELECT contacts_page_url FROM golf_courses WHERE id = [ID]
# Should show: URL (not empty)
```

---

### Issue 3: Wrong Course ID Updated (Duplicate Created)

**Symptom:**
- Requested enrichment for Course 108
- Database shows Course 440 or 444 updated instead
- OR new duplicate course created

**Root Cause:**
- Agent 2 extracts course name from website: "Brambleton Golf Course"
- Database has different name: "Brambleton Regional Park Golf Course"
- Agent 8 looks up by extracted name, finds different course or creates new

**Example:**
```
Request: course_id=108, name="Brambleton Regional Park Golf Course"
Agent 2 extracts: "Brambleton Golf Course"
Agent 8 looks up: "Brambleton Golf Course" → finds Course 440
Result: Course 440 updated, Course 108 untouched ❌
```

**Fix:**
```python
# API: Add course_id parameter
class EnrichCourseRequest(BaseModel):
    course_id: int | None = None  # ADD THIS

# Orchestrator: Accept and pass through
async def enrich_course(..., course_id: int | None = None, ...):
    supabase_result = await write_to_supabase(..., course_id=course_id, ...)

# Agent 8: Use provided course_id
if course_id:
    # Skip name lookup, use provided ID
    supabase.table(course_table).update(course_record).eq("id", course_id).execute()
else:
    # Fallback: lookup by name (risky!)
```

**Prevention:** ALWAYS pass course_id parameter in tests

**Verify Fix:**
```sql
SELECT id, course_name FROM golf_courses WHERE id = [EXPECTED_ID];
-- Check id matches what you requested
```

---

### Issue 4: contact_source is NULL (Insert Fails)

**Symptom:**
```
Agent 8 error: new row for relation "golf_course_contacts" violates check constraint
```

**Root Cause:**
- Database has constraint: `contact_source` must be one of: 'website_scrape', 'linkedin_search', etc.
- Agent 8 not setting this field

**Fix:**
```python
# agent8_supabase_writer.py - Set for all contacts
contact_record = {
    ...,
    "contact_source": "website_scrape",  # REQUIRED
}
```

**Files:** `teams/golf-enrichment/agents/agent8_supabase_writer.py`

---

## ⚠️ Non-Critical Issues

### Issue 5: LinkedIn URL Not Found

**Symptom:** `linkedin_url` is null for all contacts

**Root Cause:** Agent 3 couldn't find LinkedIn profiles

**Fix:** Not blocking - Agent 3 doesn't always find LinkedIn
**Action:** Document, but don't block deployment

---

### Issue 6: Agent 6.5 Returns null tenure_years

**Symptom:** `tenure_years` and `previous_clubs` are null

**Root Cause:** Agent 6.5 background enrichment failed (no data found)

**Fix:** Not blocking - background data often unavailable
**Action:** Document, acceptable for deployment

---

### Issue 7: phone_source Inconsistent

**Symptom:**
- Contact 1: `phone_source` = "perplexity_ai"
- Contact 2: `phone_source` = null

**Root Cause:** Agent 5 not consistently setting phone_source

**Fix:** Update Agent 5 to always set phone_source
**Priority:** P2 - Not blocking, but should fix

---

## 🐛 Docker/Build Issues

### Issue 8: "Cannot find orchestrator.py"

**Symptom:** Docker build fails
```
ERROR: Could not find orchestrator.py
```

**Root Cause:**
- `orchestrator.py` not in teams/ folder
- OR docker-compose.yml building from wrong context

**Fix:**
```bash
# Check file exists
ls teams/golf-enrichment/orchestrator.py

# Check docker-compose context
grep "context:" teams/golf-enrichment/docker-compose.yml
# Should show: context: .

# If wrong context
# Edit docker-compose.yml:
# context: ../../production/golf-enrichment  ← WRONG
# context: .  ← CORRECT
```

---

### Issue 9: "Claude CLI not found"

**Symptom:** Container fails during agent execution
```
claude: command not found
```

**Root Cause:** Claude Code CLI not installed in Docker image

**Fix:** Verify Dockerfile has:
```dockerfile
RUN npm install -g @anthropic-ai/claude-code
RUN which claude && claude --version
```

---

### Issue 10: Missing Template Files

**Symptom:**
```
ModuleNotFoundError: No module named 'env_loader'
```

**Root Cause:** `template/utils/` folder not copied to teams

**Fix:**
```bash
cp -r production/golf-enrichment/template teams/golf-enrichment/
```

---

## 🔍 Testing Issues

### Issue 11: "Course URL not found for 'Test Course 123'"

**Symptom:** Agent 1 fails immediately

**Root Cause:** Fake course name not in VSGA directory

**Fix:** Use real course names from database
```sql
SELECT course_name FROM golf_courses WHERE enhancement_status = 'pending' LIMIT 5;
```

**Future Enhancement:** Implement Agent 1 fallback search

---

### Issue 12: Logs Show "Contacts: 0" But Enrichment Succeeded

**Symptom:**
- Database has 2 contacts
- Logs show "Contacts: 0"

**Root Cause:** api.py using wrong field name

**Fix:**
```python
# api.py line ~425
# Wrong:
f"Contacts: {result.get('summary', {}).get('contact_count', 0)}"

# Correct:
f"Contacts: {result.get('summary', {}).get('contacts_enriched', 0)}"
```

---

### Issue 13: 'int' object is not subscriptable

**Symptom:**
```
Error: 'int' object is not subscriptable
```

**Root Cause:** Trying to slice integer course_id like a string

**Fix:**
```python
# orchestrator.py
# Wrong:
print(f"Course ID: {result.get('course_id', 'N/A')[:8]}...")

# Correct:
course_id_display = result.get('course_id', 'N/A')
if isinstance(course_id_display, int):
    print(f"Course ID: {course_id_display}")
else:
    print(f"Course ID: {course_id_display}")
```

---

## 🔐 Authentication Issues

### Issue 14: Webhook 401 Unauthorized

**Symptom:**
```
❌ Webhook failed for course_id=108: Client error '401 Unauthorized'
```

**Root Cause:** Edge function requires authentication

**Fix:** Add Supabase anon key to webhook request
```python
# api.py - send_enrichment_webhook()
headers = {
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}
response = await client.post(webhook_url, json=payload, headers=headers)
```

**Priority:** P1 for ClickUp integration
**Workaround:** Webhook failure doesn't block enrichment

---

## 📊 Performance Issues

### Issue 15: Enrichment Takes > 3 Minutes

**Symptom:** Duration > 180 seconds

**Investigation:**
1. Check which agent is slow (see logs)
2. Check API response times in logs
3. Look for retry loops or excessive queries

**Common Causes:**
- Agent 6.5 taking too long (20-30s per contact)
- Multiple Perplexity retries
- Network timeouts

**Fix:** Optimize slow agent or reduce retries

---

## 🔄 Workflow Issues

### Issue 16: Docker Tests Pass, Render Deploy Fails

**Symptom:**
- Local Docker test works
- Render deployment fails with errors

**Root Cause:** Production code not synced

**Fix:**
```bash
# Always sync before deploying
python production/scripts/sync_to_production.py golf-enrichment

# Verify sync
diff teams/golf-enrichment/orchestrator.py production/golf-enrichment/orchestrator.py
```

---

### Issue 17: Teams Code Not Being Tested

**Symptom:** Fixes in teams/ don't appear in Docker tests

**Root Cause:** docker-compose.yml builds from production/

**Fix:**
```yaml
# docker-compose.yml
services:
  golf-enrichment-api:
    build:
      context: .  # Build from teams/, not ../../production
      dockerfile: Dockerfile
```

---

## 📝 Diagnostic Procedures

### Procedure 1: Trace Cost Flow

**If agent_cost_usd is null:**

1. Check orchestrator calculates cost:
   ```bash
   grep -n "total_cost_usd =" teams/golf-enrichment/orchestrator.py
   # Should show calculation BEFORE Agent 8
   ```

2. Check orchestrator passes cost:
   ```bash
   grep -n "total_cost=" teams/golf-enrichment/orchestrator.py
   # Should show in write_to_supabase() call
   ```

3. Check Agent 8 accepts cost:
   ```bash
   grep -n "total_cost:" teams/golf-enrichment/agents/agent8_supabase_writer.py
   # Should show in function signature
   ```

4. Check Agent 8 writes cost:
   ```bash
   grep -n "agent_cost_usd" teams/golf-enrichment/agents/agent8_supabase_writer.py
   # Should show in course_record
   ```

---

### Procedure 2: Trace contacts_page_url Flow

**If contacts_page_url is empty:**

1. Check Agent 2 prompt:
   ```bash
   grep -n "contacts_page_url" teams/golf-enrichment/agents/agent2_data_extractor.py
   # Should show in JSON format specification
   ```

2. Check Agent 2 output in test result:
   ```bash
   cat /tmp/test-result.json | python -c "import json, sys; data = json.load(sys.stdin); print(data['agent_results']['agent2']['data'].get('contacts_page_url', 'MISSING'))"
   # Should show: URL or null (not "MISSING")
   ```

3. Check Agent 8 writes it:
   ```bash
   grep -n "contacts_page_url" teams/golf-enrichment/agents/agent8_supabase_writer.py
   # Should show in course_record
   ```

---

### Procedure 3: Verify Correct Course Updated

**If wrong course enriched:**

1. Check course_id parameter sent:
   ```bash
   # In test command, verify:
   "course_id": 108  # Must be present
   ```

2. Check Agent 8 uses it:
   ```bash
   docker logs golf-enrichment-test | grep "Using provided course_id"
   # Should show: ✅ Using provided course_id: 108
   ```

3. Check database shows correct ID:
   ```sql
   SELECT id, course_name, enrichment_completed_at
   FROM golf_courses
   WHERE enrichment_completed_at > NOW() - INTERVAL '5 minutes'
   ORDER BY enrichment_completed_at DESC;
   -- ID should match your test course_id
   ```

---

## 🛠️ Quick Fixes

### Reset Course for Retesting

```sql
-- Reset course to pending status
UPDATE golf_courses
SET
  enhancement_status = 'pending',
  enrichment_completed_at = NULL,
  segment = NULL,
  water_hazards = NULL,
  agent_cost_usd = NULL,
  contacts_page_url = NULL
WHERE id = [TEST_COURSE_ID];

-- Delete contacts for fresh test
DELETE FROM golf_course_contacts
WHERE golf_course_id = [TEST_COURSE_ID];
```

---

### Force Docker Rebuild

```bash
# Stop and remove everything
docker-compose down
docker rmi golf-enrichment-golf-enrichment-api

# Rebuild from scratch
docker-compose up --build -d
```

---

### Check Which Code Docker is Using

```bash
# Should build from teams/, not production
grep "context:" teams/golf-enrichment/docker-compose.yml

# Expected: context: .
# Wrong: context: ../../production/golf-enrichment
```

---

## 📋 Known Issues List

**Discovered During Testing (2025-10-20):**

1. ✅ **FIXED:** agent_cost_usd null - orchestrator timing issue
2. ✅ **FIXED:** contacts_page_url empty - Agent 2 not extracting
3. ✅ **FIXED:** Wrong course updated - missing course_id parameter
4. ✅ **FIXED:** 'int' object not subscriptable - course_id display bug
5. ✅ **FIXED:** Logs show Contacts: 0 - wrong field name in api.py
6. ⚠️  **OPEN:** Agent 1 fails for non-VSGA courses - needs fallback (P1)
7. ⚠️  **OPEN:** Webhook 401 Unauthorized - needs auth header (P1)
8. ⚠️  **OPEN:** phone_source inconsistent - Agent 5 issue (P2)
9. ⚠️  **OPEN:** LinkedIn rarely found - Agent 3 limitation (P3)
10. ⚠️  **OPEN:** Tenure data missing - Agent 6.5 limitation (P3)

---

## 🎯 Before Asking for Help

**Run these diagnostics first:**

1. **Check Docker logs:**
   ```bash
   docker logs golf-enrichment-test --tail 100
   ```

2. **Verify teams code:**
   ```bash
   grep -n "course_id" teams/golf-enrichment/orchestrator.py
   grep -n "agent_cost_usd" teams/golf-enrichment/agents/agent8_supabase_writer.py
   ```

3. **Query database:**
   ```sql
   SELECT * FROM golf_courses WHERE id = [TEST_ID];
   ```

4. **Check API response:**
   ```bash
   cat /tmp/test-result.json | python -m json.tool | less
   ```

5. **Review recent changes:**
   ```bash
   git log --oneline -5 teams/golf-enrichment/
   ```

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Related:** SKILL.md, FIELD_VALIDATION.md, AUDIT_QUERIES.md
