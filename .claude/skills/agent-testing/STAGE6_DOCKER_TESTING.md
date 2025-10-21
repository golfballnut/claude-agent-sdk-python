# Stage 6: Docker Testing & Production Deployment

**Purpose:** Validate agents work in containerized environment (Docker) before deploying to production (Render).

**Critical Rule:** NEVER sync to production until Docker test passes!

---

## Why Docker Testing Matters

**Local testing proves:**
- ✅ Agents work on your machine
- ✅ MCP tools accessible
- ✅ Database writes succeed

**Docker testing proves:**
- ✅ Agents work in isolated container (like Render!)
- ✅ Dependencies packaged correctly
- ✅ Environment variables loaded properly
- ✅ No hidden dependencies on local environment
- ✅ API endpoints work as expected

**If it works in Docker → It works in Render!**

---

## The Docker Testing Workflow

### **Step 1: Prepare Docker Configuration (10 min)**

**Check `docker-compose.yml` uses test files:**

```yaml
services:
  golf-enrichment:
    build: .
    environment:
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
      - HUNTER_API_KEY=${HUNTER_API_KEY}
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    ports:
      - "8000:8000"
```

**Update Dockerfile (if needed):**

For testing, point to test_orchestrator:
```dockerfile
# Temporarily use test orchestrator
COPY test_orchestrator.py /app/orchestrator.py
COPY agents/test_agent8_supabase_writer.py /app/agents/agent8_supabase_writer.py

# Later: Copy production versions after validation
```

**Or** use environment variable:
```python
# In API wrapper
orchestrator_file = os.getenv("ORCHESTRATOR", "orchestrator.py")
```

### **Step 2: Build Docker Image (5 min)**

```bash
cd teams/golf-enrichment
docker-compose build
```

**Watch for:**
- ✅ Dependencies install successfully
- ✅ No missing packages
- ✅ Build completes without errors

**Common issues:**
- Missing requirements.txt entries
- Wrong Python version
- Path issues (agents/ folder not copied)

### **Step 3: Start Docker Container (2 min)**

```bash
docker-compose up
```

**Expected output:**
```
golf-enrichment_1  | Uvicorn running on http://0.0.0.0:8000
golf-enrichment_1  | Application startup complete
```

**Verify:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### **Step 4: Test Course Enrichment via Docker API (10 min)**

**Test Course 108 (Brambleton):**

```bash
curl -X POST http://localhost:8000/enrich-course \
  -H 'Content-Type: application/json' \
  -d '{
    "course_name": "Brambleton Golf Course",
    "state_code": "VA",
    "course_id": null,
    "use_test_tables": true
  }' | jq .
```

**Expected response:**
```json
{
  "success": true,
  "course_name": "Brambleton Golf Course",
  "summary": {
    "total_cost_usd": 0.04,
    "contacts_enriched": 2,
    "agent_costs": {
      "agent4": 0.0076  // ← Includes tenure!
    }
  }
}
```

**Watch for:**
- ✅ Status 200 OK
- ✅ success: true
- ✅ contacts_enriched: 2
- ✅ Cost < $0.20

### **Step 5: Validate Tenure in Database (5 min)**

**Query test tables to confirm Agent 4 tenure written:**

```python
mcp__supabase__execute_sql(
  project_id="xxx",
  query="""
    SELECT
      contact_name,
      linkedin_url,
      tenure_years,
      tenure_start_date
    FROM test_golf_course_contacts
    WHERE contact_name = 'Dustin Betthauser';
  """
)
```

**Expected:**
```json
{
  "contact_name": "Dustin Betthauser",
  "linkedin_url": "https://linkedin.com/in/dustin-betthauser",
  "tenure_years": 6.8,           ← AGENT 4 EXTRACTED THIS!
  "tenure_start_date": "Jan 2019"
}
```

✅ **If tenure is 6.8 → Agent 4 extraction works in Docker!**

### **Step 6: Compare Docker vs Local Baseline (10 min)**

**Run comparison script (if exists):**

```bash
python tests/local/compare_to_docker.py 108
```

**Manual comparison:**
```bash
# Local baseline
cat tests/baselines/course_108_baseline.json | jq '.enriched_contacts[0].tenure_years'
# Expected: 6.8

# Docker result (from database)
# Run SQL query above
# Expected: 6.8

# Match? ✅ Docker validated!
```

**Acceptance criteria:**
- ✅ Tenure values match (6.8 years)
- ✅ LinkedIn URLs match
- ✅ NULL handling matches
- ✅ Costs within 10% (API variability OK)

---

## Production Deployment (ONLY AFTER Docker Passes!)

### **Step 1: Backup Production Files (2 min)**

```bash
cd teams/golf-enrichment

# Backup production orchestrator
cp orchestrator.py orchestrator.backup.$(date +%Y%m%d).py

# Backup production Agent 8
cp agents/agent8_supabase_writer.py agents/agent8_supabase_writer.backup.$(date +%Y%m%d).py
```

### **Step 2: Sync Test → Production (5 min)**

**Replace production files with validated test files:**

```bash
# Copy test orchestrator to production
cp test_orchestrator.py orchestrator.py

# Copy test Agent 8 to production
cp agents/test_agent8_supabase_writer.py agents/agent8_supabase_writer.py

# Update headers (remove ⚠️ TEST warnings)
# Update comments to reflect production status
```

### **Step 3: Sync to Production Folder (5 min)**

**Use sync script:**

```bash
cd ../../  # Back to project root
python production/scripts/sync_to_production.py golf-enrichment
```

**This copies:**
- `teams/golf-enrichment/` → `production/golf-enrichment/`
- All agents, orchestrator, migrations
- Preserves production-specific files (api.py, Dockerfile, render.yaml)

### **Step 4: Git Commit & Deploy (10 min)**

```bash
cd production/golf-enrichment

# Check what changed
git status
git diff

# Commit with descriptive message
git add .
git commit -m "feat: Consolidate Agent 4 tenure extraction, remove Agent 6.5

- Agent 4 extracts tenure from Firecrawl search descriptions
- No separate LinkedIn scraping needed (Firecrawl blocks profiles)
- Faster: One API call vs two
- Cheaper: $0.004 vs $0.007+
- More reliable: Uses proven search method
- Eliminated Agent 6.5 completely

Validated:
- Local testing: ✅ Tenure 6.8 years extracted
- Database: ✅ Data written correctly
- Docker: ✅ Container test passed
- NULL handling: ✅ Works correctly

Cost savings: $0.003 per contact with tenure
Success rate: 40-50% tenure extraction (when LinkedIn found)

🤖 Generated with Claude Code"

# Push to deploy (Render auto-deploys on git push)
git push origin main
```

### **Step 5: Monitor Render Deployment (10 min)**

**Watch deployment logs:**
```bash
# Via Render dashboard or CLI
render logs -s golf-enrichment-service
```

**Check for:**
- ✅ Build succeeds
- ✅ Container starts
- ✅ Health check passes
- ✅ No import errors
- ✅ API endpoints accessible

**Test production endpoint:**
```bash
curl https://agent7-water-hazards.onrender.com/health

# Should return: {"status": "healthy"}
```

### **Step 6: Test One Course in Production (5 min)**

**Run on real production:**

```bash
curl -X POST https://your-service.onrender.com/enrich-course \
  -H 'Content-Type: application/json' \
  -d '{
    "course_name": "Test Course",
    "state_code": "VA",
    "use_test_tables": false  ← PRODUCTION TABLES!
  }'
```

**Validate in production database:**

```sql
SELECT
  contact_name,
  tenure_years,
  tenure_start_date
FROM golf_course_contacts
WHERE contact_name = 'Test Contact';
```

✅ **If tenure appears in production → DEPLOYMENT SUCCESS!**

---

## Rollback Plan

**If production deployment fails:**

```bash
cd production/golf-enrichment

# Restore from backup
git checkout HEAD~1 -- orchestrator.py agents/agent8_supabase_writer.py

# Re-deploy
git add .
git commit -m "rollback: Restore Agent 6.5 (Agent 4 tenure had issues)"
git push origin main
```

**Or restore from backup files:**

```bash
cp orchestrator.backup.20251020.py orchestrator.py
cp agents/agent8_supabase_writer.backup.20251020.py agents/agent8_supabase_writer.py
```

---

## Complete Validation Checklist

**Before declaring "ready for production":**

- [ ] **Stage 2:** MCP tests pass (3 tools agree)
- [ ] **Stage 3:** Agent code implements MCP pattern
- [ ] **Stage 4:** Cross-validation confirms accuracy
- [ ] **Stage 5:** Database integration succeeds
  - [ ] Test tables aligned with production
  - [ ] Data written correctly
  - [ ] SQL query validates expected values
- [ ] **Stage 6:** Docker test passes
  - [ ] Container builds
  - [ ] API endpoint works
  - [ ] Results match local baseline
- [ ] **Production:** Deployment successful
  - [ ] Render build succeeds
  - [ ] Health check passes
  - [ ] Test course enrichment works
  - [ ] Production database validates

**Only check final box after ALL preceding boxes checked!**

---

## Time & Cost Summary

**Full testing cycle (Stages 1-6):**
- Stage 2 (MCP): 30 min, <$0.10
- Stage 3 (Code): 20 min, $0
- Stage 4 (Validate): 20 min, <$0.10
- Stage 5 (Database): 50 min, $0
- Stage 6 (Docker): 30 min, ~$0.20
- **Total: 2.5 hours, <$0.50**

**Savings:**
- Avoided production incidents: Priceless
- Avoided debugging in production: Hours saved
- Confidence in deployment: 100%

**ROI: 10-20x** (prevents costly production bugs)

---

## Success Story: Agent 4 Tenure (Oct 20, 2025)

**Complete testing cycle:**
1. ✅ Stage 2: Firecrawl search tested with MCP (found tenure in description!)
2. ✅ Stage 3: Agent 4 code enhanced to extract tenure
3. ✅ Stage 4: Standalone agent test validated 6.8 years
4. ✅ Stage 5: Test orchestrator + database integration passed
5. ⏳ Stage 6: Docker testing (in progress...)
6. ⏳ Production: After Docker validation

**Confidence level:** HIGH (passed Stages 2-5)

---

**After Docker passes:** Sync to production and deploy to Render!
