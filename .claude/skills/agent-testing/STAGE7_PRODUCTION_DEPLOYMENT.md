# Stage 7: Production Deployment & Validation

**Purpose:** Deploy tested agent code to production (Render) and validate it works correctly.

**When to use:** After completing Stages 1-6 (all testing passed in local + Docker + production database)

**Time estimate:** 30-60 minutes (including monitoring)

---

## Pre-Deployment Checklist: Code Coverage Audit ⭐

**Before deploying to Render, answer this question:**

### **Did Docker Tests Execute ALL Code Paths?**

**How to verify:**

#### **Step 1: Review Agent Code for Branches**
```python
# Example: Agent 4 has 3 paths
if tenure_in_description:
    # PATH 1: Extract from description
elif linkedin_url:
    # PATH 2: Scrape profile  ← Did this execute in Docker?
else:
    # PATH 3: Return NULL
```

#### **Step 2: Check Docker Logs**
```bash
docker-compose logs | grep "Scraping LinkedIn profile"

# If you DON'T see the message:
# → PATH 2 never executed
# → Bug could be hiding there
# → DON'T DEPLOY YET!
```

#### **Step 3: Add Test Data for Missing Paths**
```python
# If scraping path not tested:
test_additional_course = "Chantilly National"
# This course has contacts without tenure in descriptions
# Forces scraping path to execute
```

#### **Step 4: Verify All Paths Executed**
```bash
# After adding new test data:
docker-compose up
curl -X POST localhost:8000/enrich-course -d '{"course_name": "Chantilly National", ...}'

# Check logs for ALL expected messages:
✅ "Found LinkedIn URL"
✅ "Scraping LinkedIn profile"  ← This should appear now!
✅ "Tenure: X.X years"
```

---

### **Real-World Example: What We Missed**

**Agent 4 Consolidation (Oct 21):**

**What we tested:**
- 2 contacts with tenure in search descriptions
- 100% success rate in Docker
- Declared "Agent 4 complete!" ✅

**What we missed:**
- BrightData profile scraping code (PATH 2) never executed
- 400 Bad Request bug hiding in untested path
- Discovered only in production (0/4 success)

**What we should have done:**
```python
# Test BOTH paths:
test_contacts = [
    "Dustin Betthauser",    # PATH 1: Tenure in description
    "John Stutz"            # PATH 2: Need to scrape profile ← Would catch bug!
]
```

---

### **Pre-Deployment Sign-Off**

Before syncing to production, confirm:
```
□ All agent code branches identified
□ Docker logs show ALL branches executed
□ Test data covers happy path + fallback paths
□ No untested code going to production
□ If any path untested → added test data and re-tested
```

**Only proceed to production when ALL checkboxes checked!**

---

## ⚠️ STOP! Have You Completed Stage 6? ⭐

**Before proceeding to production deployment:**

**Stage 6 Checklist:**
```
□ Docker build succeeded
□ Tested with representative data (not just happy path!)
□ Docker logs show ALL agents running
□ Docker logs show ALL code paths executed
□ Comprehensive data validated in test database
□ No agents failing silently
□ Environment variables validated
```

**❌ DO NOT DEPLOY IF:**
- Haven't run Docker test
- Docker logs missing any agent
- Any agent returns null/error without logging why
- Comprehensive fields not extracted
- Only tested happy path data

**✅ Stage 6 exists to catch:**
- Orchestrator integration issues
- Missing environment variables
- Silent agent failures
- Incomplete data extraction
- Path coverage gaps

**Real example (Oct 21):**
- Deployed without Stage 6 ✗
- Agent 4 failed silently in production (missing env var)
- No LinkedIn/tenure data for 3 courses
- Could have been caught in Docker!

---

## Prerequisites

Before starting Stage 7, ensure:

- [x] **Stage 6 (Docker) passed** - Container tested successfully
- [x] **Production database tested** - Test tables or production tables validated
- [x] **All costs validated** - Under budget targets
- [x] **No errors in testing** - Clean test runs
- [x] **Backup files created** - Can rollback if needed

---

## Deployment Workflow

### **Step 1: Prepare Team Files for Production (5 min)**

**Remove test artifacts:**
```bash
cd teams/your-team-name/

# Clean up test files
rm -f test_*.py
rm -f agents/test_*.py

# Remove backup files (if any)
rm -f *.backup.py
rm -f agents/*.backup.py
```

**Clean up headers:**
```python
# Remove from orchestrator.py and agent files:
# ❌ DELETE THIS:
"""
⚠️ TEST VERSION - DO NOT USE IN PRODUCTION!
...
"""

# ✅ REPLACE WITH:
"""
Agent X: Production Description
...
"""
```

**Update imports:**
```python
# ❌ DELETE:
from agents.test_agent8_supabase_writer import write_to_supabase

# ✅ REPLACE WITH:
from agents.agent8_supabase_writer import write_to_supabase
```

---

### **Step 2: Verify Sync Script Completeness (5 min)**

**Critical: Ensure sync script copies ALL files!**

```python
# production/scripts/sync_to_production.py should copy:
✅ agents/*.py (all agent files)
✅ orchestrator.py
✅ api.py ⭐ (CRITICAL - often forgotten!)
✅ requirements.txt
✅ shared/utils/*.py
✅ config files (if any)
```

**Test sync script:**
```bash
# 1. Make a test change
echo "# sync test" >> teams/your-team/api.py

# 2. Run sync
python production/scripts/sync_to_production.py your-team

# 3. Verify file copied
diff teams/your-team/api.py production/your-team/api.py
# Should be identical!

# 4. Revert test change
git checkout teams/your-team/api.py
```

**If api.py not syncing:** Add to sync script (see Pattern 12)

---

### **Step 3: Sync to Production Folder (2 min)**

```bash
# From repo root
cd /path/to/project

# Run sync script
python production/scripts/sync_to_production.py your-team-name

# Expected output:
#   ✓ Copied agent: agent1.py
#   ✓ Copied agent: agent2.py
#   ...
#   ✓ Copied orchestrator.py to production root
#   ✓ Copied api.py to production root  ← Verify this appears!
#   ✓ Copied util: env_loader.py
#   ✓ Updated requirements.txt
```

**Verify sync worked:**
```bash
cd production/your-team-name

# Check key files exist
ls -la orchestrator.py api.py agents/agent*.py

# Spot check critical changes made it
grep "your_new_feature" api.py
grep "your_fix" agents/agent8.py
```

---

### **Step 4: Commit & Deploy to Render (10 min)**

**Commit with detailed message:**
```bash
cd production/your-team-name  # Or repo root, depending on setup

git add .

git commit -m "feat: Descriptive title of changes

CHANGES:
- Specific change 1
- Specific change 2
- Specific change 3

VALIDATION:
✅ Stage 1-6 complete
✅ Docker tested (X courses)
✅ Production database tested (Y contacts)
✅ Cost validated (\$X per course)

PRODUCTION TEST RESULTS:
- Metric 1: X
- Metric 2: Y
- Cost: \$Z

BREAKING CHANGES (if any):
- Change A removed
- Change B modified

🤖 Generated with Claude Code"

# Push to deploy (auto-deploys if render.yaml configured)
git push origin main
```

**Monitor deployment:**
```bash
# Option 1: Render dashboard
# Visit: https://dashboard.render.com
# Watch "Events" tab for deployment progress

# Option 2: Render CLI (if available)
render logs --tail --service your-service-name
```

**Wait for:** "Deploy live" or "Your service is live 🎉"

---

### **Step 5: Validate Deployment via Logs (10 min)**

**Fetch production logs:**
- Render Dashboard → Your Service → Logs tab
- Look for startup logs showing service version/agents

**Validate architectural changes:**

**Example - Agent count change (9 → 8):**
```
✅ Look for: "Service: Full Enrichment Pipeline (Agents 1-8)"
❌ Should NOT see: "Agents 1-9" or "Agent 6.5"
```

**Example - Parameter flow:**
```
✅ Look for: "✅ Using provided course_id: 133"
✅ Look for: "✅ Updated course ID: 133"
❌ Should NOT see: "✅ Created new course (ID: 445)" (duplicate!)
```

**Example - Agent logic:**
```
✅ Look for: "🔗 Agent 4: Finding LinkedIn + Tenure (specialist)..."
✅ Look for: "Method: firecrawl_search"
✅ Look for: "⚠️ Tenure: Not in search description"
❌ Should NOT see: Agent 6.5 logs
```

**Check for errors:**
```bash
# In logs, search for:
grep "ERROR" logs.txt
grep "Exception" logs.txt
grep "Failed" logs.txt

# Acceptable: Warnings about data not found
# Unacceptable: Agent crashes, database errors
```

---

### **Step 6: Test Production Endpoint (10 min)**

**Health check:**
```bash
curl https://your-service.onrender.com/health

# Expected: {"status": "healthy"}
```

**Test with known good input:**
```bash
curl -X POST https://your-service.onrender.com/enrich-course \
  -H 'Content-Type: application/json' \
  -d '{
    "course_id": 133,
    "course_name": "Known Good Course",
    "state_code": "VA",
    "use_test_tables": false
  }' | jq .

# Expected:
# {
#   "success": true,
#   "summary": {
#     "total_cost_usd": <0.20,
#     "contacts_enriched": 4
#   }
# }
```

**Validate response:**
- [x] success: true
- [x] No error field
- [x] Cost under budget
- [x] Agents executed in correct order
- [x] Expected data returned

---

### **Step 7: Validate Database Changes (10 min)**

**Query database for test course:**
```sql
-- Verify course updated (not new course created)
SELECT
  id,
  course_name,
  enrichment_completed_at,
  agent_cost_usd
FROM golf_courses
WHERE id = 133;

-- Should show:
-- - enrichment_completed_at: recent timestamp
-- - agent_cost_usd: your test cost
```

**Verify contacts written:**
```sql
SELECT
  contact_name,
  linkedin_url,
  tenure_years,
  contact_email,
  contact_phone
FROM golf_course_contacts
WHERE golf_course_id = 133
ORDER BY contact_id;

-- Should show all contacts with enriched data
```

**Check for duplicates:**
```sql
-- Ensure no duplicate courses created
SELECT id, course_name, enrichment_completed_at
FROM golf_courses
WHERE course_name ILIKE '%Chantilly%'
ORDER BY id;

-- Should show ONLY 1 course (not 2+)
```

---

## Validation Checklist

### **Deployment Success:**
- [ ] Git push completed
- [ ] Render shows "Deploy succeeded"
- [ ] Service shows "Live" status
- [ ] No build errors in Render logs
- [ ] Service restarted successfully

### **Architectural Changes:**
- [ ] Logs show new agent count (if changed)
- [ ] Logs show new agent logic executing
- [ ] Logs show old agent logic NOT executing
- [ ] Parameters flowing correctly (check logs)

### **Functionality:**
- [ ] Health endpoint returns 200 OK
- [ ] Test endpoint returns success: true
- [ ] No errors in response
- [ ] Cost under budget
- [ ] Duration acceptable

### **Database:**
- [ ] Correct course updated (not duplicate created)
- [ ] All contacts written
- [ ] All fields populated correctly
- [ ] NULL handling correct
- [ ] No constraint violations

### **Ready for Population:**
- [ ] All above checks passed
- [ ] Multiple test courses validated
- [ ] Edge cases handled
- [ ] Rollback plan ready

---

## Common Deployment Issues

### **Issue 1: "Fix didn't deploy"**

**Symptoms:**
- Code changed in teams/ folder
- Git pushed
- Render deployed
- Old behavior still happening

**Root Cause:** Sync script didn't copy the file

**Solution:**
```bash
# 1. Check what sync script copies
cat production/scripts/sync_to_production.py

# 2. Verify file was synced
diff teams/your-team/api.py production/your-team/api.py

# 3. If different, update sync script (Pattern 12)
# Add: shutil.copy2(team_dir / "api.py", prod_dir / "api.py")

# 4. Re-sync and redeploy
python production/scripts/sync_to_production.py your-team
cd production/your-team
git add . && git commit -m "fix: Re-sync with api.py"
git push origin main
```

---

### **Issue 2: "Parameter not working"**

**Symptoms:**
- Added parameter to agent
- Parameter always None in production
- No errors, just default behavior

**Root Cause:** Parameter not passed through all layers (Pattern 11)

**Solution:**
```bash
# Trace parameter through layers:
1. Check API model: grep "course_id" production/your-team/api.py
2. Check API endpoint: grep "course_id=request" production/your-team/api.py
3. Check orchestrator call: grep "course_id=" production/your-team/orchestrator.py
4. Check agent call: grep "course_id=" production/your-team/agents/agent8.py

# Fix missing layer and redeploy
```

---

### **Issue 3: "Duplicate records created"**

**Symptoms:**
- Expected: Update existing record
- Actual: New record created
- Database has duplicates

**Root Cause:** Name mismatch ("and" vs "&"), not using ID parameter (Pattern 13)

**Solution:**
```bash
# 1. Add ID parameter to API
class Request(BaseModel):
    id: int | None = None  # Add this

# 2. Pass through API → Orchestrator → Agent

# 3. Cleanup duplicates
DELETE FROM table WHERE id = duplicate_id;

# 4. Re-test with ID parameter
curl -d '{"id": 133, "name": "Course Name", ...}'
```

---

### **Issue 4: "Can't verify deployment worked"**

**Symptoms:**
- Deployment shows "Live"
- Not sure if changes working
- No errors but no confidence

**Root Cause:** Not validating via production logs (Pattern 14)

**Solution:**
```bash
# 1. Fetch production logs from Render
# Dashboard → Service → Logs → View recent logs

# 2. Search for evidence of changes
grep "new_agent_name" logs.txt
grep "new_parameter" logs.txt

# 3. Test endpoint with known input
curl -X POST https://api.../test-endpoint -d '{...}'

# 4. Query database for test record
SELECT * FROM table WHERE id = test_id;
```

---

## Rollback Procedure

**If deployment fails or causes issues:**

### **Quick Rollback (5 min):**
```bash
# 1. Restore backup files in teams/ folder
cd teams/your-team
cp orchestrator.backup.py orchestrator.py
cp agents/agent8.backup.py agents/agent8_supabase_writer.py

# 2. Re-sync to production
cd ../..
python production/scripts/sync_to_production.py your-team

# 3. Commit and push
cd production/your-team
git add .
git commit -m "revert: Rollback to previous version (issue with X)"
git push origin main

# 4. Monitor Render redeploy
# Watch for "Deploy live"

# 5. Test health endpoint
curl https://your-service.onrender.com/health
```

### **Git Rollback (if needed):**
```bash
# Find commit to revert
git log --oneline -5

# Revert specific commit
git revert <commit-hash>

# Or reset to previous commit (destructive!)
git reset --hard HEAD~1
git push --force origin main  # ⚠️ USE WITH CAUTION
```

---

## Production Monitoring

### **After Deployment:**

**First 24 hours:**
- Check logs every 2-4 hours
- Monitor error rates
- Track costs in database
- Validate data quality

**First week:**
- Daily cost analysis
- Review enrichment success rates
- Check for new error patterns
- Optimize if needed

### **Key Metrics to Monitor:**

**Performance:**
```sql
SELECT
  DATE(enrichment_completed_at) as day,
  COUNT(*) as courses_enriched,
  AVG(agent_cost_usd) as avg_cost,
  MAX(agent_cost_usd) as max_cost
FROM golf_courses
WHERE enrichment_completed_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(enrichment_completed_at);
```

**Success Rate:**
```sql
SELECT
  COUNT(*) as total_attempts,
  COUNT(CASE WHEN enrichment_completed_at IS NOT NULL THEN 1 END) as successful,
  COUNT(CASE WHEN enrichment_completed_at IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as success_rate
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '7 days';
```

**Data Quality:**
```sql
SELECT
  COUNT(*) as total_contacts,
  COUNT(contact_email) * 100.0 / COUNT(*) as email_coverage,
  COUNT(linkedin_url) * 100.0 / COUNT(*) as linkedin_coverage,
  COUNT(tenure_years) * 100.0 / COUNT(*) as tenure_coverage
FROM golf_course_contacts
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

## Real Example: Golf Enrichment Deployment (Oct 21, 2025)

### **Context:**
- **Change:** Agent 4 consolidation + course_id parameter fix
- **Scope:** 2 deployments in one session
- **Risk:** Breaking changes (Agent 6.5 removed)

### **Deployment 1: Agent 4 Consolidation**

**Preparation:**
```bash
# 1. Backed up production files
cp orchestrator.py orchestrator.backup.py
cp agents/agent8_supabase_writer.py agents/agent8_supabase_writer.backup.py

# 2. Promoted test files
cp test_orchestrator.py orchestrator.py
cp agents/test_agent8_supabase_writer.py agents/agent8_supabase_writer.py

# 3. Cleaned up headers (removed "⚠️ TEST" warnings)

# 4. Removed Agent 6.5 files
rm agents/agent65_contact_enrichment.py
rm agents/_deprecated_agent65_contact_enrichment.py

# 5. Cleaned up test files
rm test_orchestrator.py agents/test_agent8_supabase_writer.py
```

**Sync & Deploy:**
```bash
python production/scripts/sync_to_production.py golf-enrichment

cd production/golf-enrichment
git add .
git commit -m "feat: Consolidate Agent 4 tenure extraction, remove Agent 6.5"
git push origin main
```

**Validation:**
```
✅ Render logs: "Service: Full Enrichment Pipeline (Agents 1-8)"
✅ Agent 4 logs: "Finding LinkedIn + Tenure (specialist)..."
✅ No "Agent 6.5" in logs
✅ Cost: $0.1198 (under budget)
✅ Course 133 enriched successfully
```

### **Deployment 2: course_id Parameter Fix**

**Problem Found:** Course 133 not updated (duplicate 445 created)

**Root Cause:** API didn't have course_id field

**Fix Applied:**
```bash
# 1. Already in teams/api.py (from earlier work)
# 2. Updated sync script to include api.py
# 3. Re-synced and deployed
```

**Validation:**
```
✅ Logs: "✅ Using provided course_id: 133"
✅ Logs: "✅ Updated course ID: 133"
✅ Database: Course 133 updated (not 446 created)
✅ No duplicates
```

**Results:**
- Both deployments successful
- 4 courses tested in production
- 100% success rate
- No rollbacks needed
- Production ready for full population

---

## Best Practices

### **1. Deploy During Low-Traffic Times**
- Best: Weekends, evenings, early mornings
- Avoid: Peak business hours
- Reason: Easier to rollback if issues

### **2. Deploy One Change at a Time**
- ✅ Good: Agent 4 consolidation, then course_id fix (separate)
- ❌ Bad: 5 unrelated changes in one deploy
- Reason: Easier to identify what broke

### **3. Test in Production with Real Data**
- Use production tables with `use_test_tables: false`
- Test 1-3 courses first
- Validate before scaling up
- Reason: Catch production-only issues

### **4. Keep Backup Files Temporarily**
```bash
# Keep backups for 24-48 hours after deploy
orchestrator.backup.py
agents/agent8.backup.py

# Delete after validation period
rm *.backup.py
```

### **5. Document Deployments**
- Create session handoff docs
- Note what changed
- Record test results
- Document any issues
- Include rollback steps

---

## Stage 7 Success Criteria

**Before marking Stage 7 complete:**

✅ **Deployment Successful:**
- Render shows "Live" status
- No build errors
- Service healthy

✅ **Logs Validated:**
- Architectural changes confirmed
- New logic executing
- Old logic not executing
- Parameters flowing correctly

✅ **Endpoint Tested:**
- Health check passes
- Test enrichment succeeds
- Response structure correct
- Costs within budget

✅ **Database Validated:**
- Correct records updated
- No duplicates created
- Data quality high
- NULL handling correct

✅ **Monitoring Setup:**
- Error alerts configured
- Cost tracking queries ready
- Success rate dashboards updated

✅ **Documentation:**
- Deployment recorded
- Changes documented
- Rollback procedures tested

---

## Next Stage: Production Population

After Stage 7 passes, you're ready to:
- Populate full production database
- Set up automated enrichment
- Monitor at scale
- Optimize based on real usage

See: `docs/PRODUCTION_POPULATION.md` (if exists)

---

**Stage 7 completes the testing methodology! You now have a fully deployed, validated production system.** 🚀
