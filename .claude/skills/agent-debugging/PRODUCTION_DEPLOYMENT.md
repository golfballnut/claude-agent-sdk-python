# Phase 5: Production Deployment

**Purpose:** Deploy Docker-validated agent fixes to production with verification that production environment exactly mirrors testing environment.

**When to use:** After Phase 4 (Docker validation) passes and you're ready to deploy to production Render.

**Critical principle:** Production must be a byte-for-byte mirror of Docker testing.

---

## Overview

Phase 5 ensures your Docker-validated fixes reach production correctly:

1. **Sync code** from teams/ (development) to production/ (deployment)
2. **Verify sync** with MD5 checksums (catch partial/incomplete syncs)
3. **Configure environment variables** (feature flags, API keys)
4. **Deploy to Render** (git push triggers rebuild)
5. **Validate production** (confirm it mirrors Docker testing)
6. **Monitor** (first 5-10 cases for confidence)

---

## Pre-Deployment Validation Checklist

Before syncing to production, confirm:

- [ ] **Docker tests passed** (Phase 4 complete)
- [ ] **Success rate acceptable** (e.g., 60%+ for Apollo)
- [ ] **Costs within budget** (e.g., <$0.20/course)
- [ ] **No critical issues** in Docker logs
- [ ] **Test fixtures validated** (real failure data)
- [ ] **Deployment approved** (if team workflow requires)

**If any item fails:** Debug in Docker (Phase 3-4) before deploying.

---

## Step 1: Code Sync (teams/ → production/)

### Using the Sync Script

The project has a sync script that copies development code to production:

```bash
cd /path/to/project

# Sync your agent team to production
python production/scripts/sync_to_production.py golf-enrichment
```

**What gets synced:**
- `teams/golf-enrichment/agents/*.py` → `production/golf-enrichment/agents/`
- `teams/golf-enrichment/orchestrator.py` → `production/golf-enrichment/`
- `teams/golf-enrichment/orchestrator_apollo.py` → `production/golf-enrichment/`
- `teams/golf-enrichment/api.py` → `production/golf-enrichment/`
- `teams/golf-enrichment/requirements.txt` → `production/golf-enrichment/`
- `shared/utils/*.py` → `production/golf-enrichment/template/utils/`

**What does NOT get synced:**
- Test files (test_*.py)
- Documentation (.md files)
- Docker configs (docker-compose.yml)
- .env files (security)

### Manual Sync (Fallback)

If sync script fails or for specific files:

```bash
cp teams/golf-enrichment/orchestrator_apollo.py \
   production/golf-enrichment/orchestrator_apollo.py
```

---

## Step 2: Sync Verification (CRITICAL)

**Why:** Partial syncs are common. One missing file breaks production.

### Method 1: MD5 Checksum Comparison

Verify critical files are byte-for-byte identical:

```bash
cd /path/to/project

# Check orchestrator
md5 teams/golf-enrichment/orchestrator_apollo.py
md5 production/golf-enrichment/orchestrator_apollo.py
# Checksums MUST match

# Check agent2
md5 teams/golf-enrichment/agents/agent2_apollo_discovery.py
md5 production/golf-enrichment/agents/agent2_apollo_discovery.py
# Checksums MUST match

# Check API
md5 teams/golf-enrichment/api.py
md5 production/golf-enrichment/api.py
# Checksums MUST match
```

**Expected:** All checksums identical.

**If different:** File is out of sync. Re-run sync or copy manually.

### Method 2: File Size + Modification Time

Quick sanity check:

```bash
ls -lh teams/golf-enrichment/orchestrator_apollo.py
ls -lh production/golf-enrichment/orchestrator_apollo.py
# Sizes MUST match (modification time may differ)
```

### Method 3: Git Status Check

After syncing, check what changed:

```bash
cd production/golf-enrichment
git status

# Should show:
# modified:   agents/agent2_apollo_discovery.py
# modified:   orchestrator_apollo.py
# modified:   api.py
```

**Verify:** All expected files show as modified.

**Red flag:** File that should be synced doesn't appear.

---

## Step 3: Environment Variables

### Understanding Feature Flags

Production uses environment variables to control features:

```python
# In api.py
USE_APOLLO = os.getenv("USE_APOLLO", "false").lower() == "true"
orchestrator_enrich_course = apollo_enrich_course if USE_APOLLO else old_enrich_course
```

**Without env var:** Feature is deployed but inactive (defaults to "false").

### Required Variables for Apollo

**On Render Dashboard:**

1. Go to: https://dashboard.render.com
2. Select your service (e.g., "golf-enrichment-api")
3. Click "Environment" tab
4. Add:

```
USE_APOLLO = true
APOLLO_API_KEY = [your Apollo API key]
HUNTER_API_KEY = [your Hunter API key] (optional fallback)
```

**Get values from:**

```bash
cat teams/golf-enrichment/.env | grep APOLLO_API_KEY
cat teams/golf-enrichment/.env | grep HUNTER_API_KEY
```

### Verify Variables After Save

After adding variables and service restarts:

```bash
curl https://your-service.onrender.com/orchestrator-info
```

**Expected response:**
```json
{
  "active_orchestrator": "apollo",
  "use_apollo_env": "true"
}
```

**If shows "standard":** Variable not set or not saved correctly.

---

## Step 4: Dockerfile Verification

Ensure Dockerfile includes all new files:

```dockerfile
# production/golf-enrichment/Dockerfile

# Example for Apollo orchestrator:
COPY orchestrator.py .
COPY orchestrator_apollo.py .  # ← Must be present!
COPY api.py .
COPY agents/ ./agents/
```

**Check:**

```bash
grep "orchestrator_apollo" production/golf-enrichment/Dockerfile
# Should return: COPY orchestrator_apollo.py .
```

**If missing:** Add line to Dockerfile before deploying.

---

## Step 5: Render Deployment

### Commit Changes

```bash
cd /path/to/project

# Stage production files
git add production/golf-enrichment/

# Commit with descriptive message
git commit -m "feat: Deploy Apollo orchestrator (domain-first search + Hunter fallback)

Synced from teams/ after Docker validation:
- agent2_apollo_discovery.py (domain-first search)
- orchestrator_apollo.py (Agent 1 fix)
- api.py (domain parameter support)

Docker results: 60% success, $0.19/course
Production env vars required: USE_APOLLO=true, APOLLO_API_KEY"

# Push to trigger deployment
git push origin main
```

### Monitor Render Deployment

1. **Render Dashboard:** Watch deployment progress
   - Build logs scroll
   - "Your service is live 🎉" appears
   - ~3-5 minutes

2. **Check deployment logs:**
   - Look for: "Successfully imported Apollo Orchestrator"
   - Look for: "Active orchestrator: APOLLO" (if env var set)
   - No import errors or missing file errors

3. **Health check:**
   ```bash
   curl https://your-service.onrender.com/health
   ```

---

## Step 6: Production Validation

### Verify Production Mirrors Docker

**1. Orchestrator Check:**
```bash
curl https://your-service.onrender.com/orchestrator-info
```

Expected (matching Docker):
```json
{
  "active_orchestrator": "apollo",
  "description": "Apollo orchestrator: domain-first search + Hunter fallback"
}
```

**2. Test Same Course as Docker:**

If Cardinal CC succeeded in Docker, test it in production:

```bash
curl -X POST https://your-service.onrender.com/enrich-course \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Cardinal Country Club", "state_code": "NC"}'
```

**Expected (matching Docker):**
- 4 contacts found
- 100% email coverage
- Cost: $0.17-0.19
- Same Apollo credits consumed

**3. Monitor First 5-10 Cases:**

Watch Render logs for:
- Correct orchestrator executing (Apollo, not Standard)
- Expected agent flow (Agents 1, 2-Apollo, 6, 7, 8)
- Success rates matching Docker
- Costs matching Docker

---

## Step 7: Rollback Procedure

### When to Rollback

- Success rate drops significantly (<40% when Docker showed 60%)
- Costs exceed budget (>$0.30 when Docker showed $0.19)
- Critical errors in production logs
- Wrong orchestrator active (Standard instead of Apollo)

### Quick Rollback (Environment Variables)

Disable feature without code changes:

1. Render Dashboard → Environment
2. Set `USE_APOLLO = false` (or remove variable)
3. Service restarts (~30 seconds)
4. Reverts to Standard orchestrator

### Full Rollback (Git Revert)

Revert code changes:

```bash
cd /path/to/project

# Revert last commit
git revert HEAD

# Push to redeploy previous version
git push origin main
```

### Validate Rollback

```bash
# Should show previous orchestrator
curl https://your-service.onrender.com/orchestrator-info

# Test enrichment works with previous version
curl -X POST https://your-service.onrender.com/enrich-course \
  -d '{"course_name": "Test Course", "state_code": "VA"}'
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Partial Sync (Missing orchestrator_apollo.py)

**Symptom:**
```
ERROR: Failed to import Apollo Orchestrator
```

**Root cause:** `orchestrator_apollo.py` not synced to production.

**Detection:**
```bash
md5 teams/golf-enrichment/orchestrator_apollo.py
md5 production/golf-enrichment/orchestrator_apollo.py
# Checksums different or production file missing
```

**Solution:**
```bash
# Re-sync the missing file
cp teams/golf-enrichment/orchestrator_apollo.py \
   production/golf-enrichment/orchestrator_apollo.py

# Verify
md5 teams/golf-enrichment/orchestrator_apollo.py
md5 production/golf-enrichment/orchestrator_apollo.py
# Now identical

# Commit and deploy
git add production/golf-enrichment/orchestrator_apollo.py
git commit -m "fix: Sync orchestrator_apollo.py (was missing)"
git push origin main
```

### Pitfall 2: Missing Environment Variables

**Symptom:**
```bash
curl /orchestrator-info
# Returns: "active_orchestrator": "standard"
```

**Root cause:** `USE_APOLLO` not set on Render.

**Solution:**
1. Render Dashboard → Environment
2. Add `USE_APOLLO = true`
3. Add `APOLLO_API_KEY = [key]`
4. Save (auto-restarts service)
5. Verify: `curl /orchestrator-info` → "apollo"

### Pitfall 3: Dockerfile Not Updated

**Symptom:**
```
ERROR: orchestrator_apollo.py not found
```

**Root cause:** Dockerfile doesn't include `COPY orchestrator_apollo.py .`

**Solution:**
```bash
# Edit production/golf-enrichment/Dockerfile
# Add line:
COPY orchestrator_apollo.py .

# Commit and deploy
git add production/golf-enrichment/Dockerfile
git commit -m "fix: Add orchestrator_apollo.py to Dockerfile"
git push origin main
```

### Pitfall 4: render.yaml Missing New Env Vars

**Symptom:** Variables set in dashboard but reset after deployment.

**Root cause:** `render.yaml` doesn't include new variables.

**Solution:**
```yaml
# In production/golf-enrichment/render.yaml
envVars:
  - key: USE_APOLLO
    value: true
  - key: APOLLO_API_KEY
    sync: false  # Secret - set in dashboard
```

### Pitfall 5: api.py Parameter Mismatch

**Symptom:**
```
TypeError: enrich_course() got an unexpected keyword argument 'domain'
```

**Root cause:** Standard orchestrator doesn't accept `domain` parameter.

**Detection:**
```bash
# Check function signature
grep "async def enrich_course" production/golf-enrichment/orchestrator.py
# Should include: domain: str = ""
```

**Solution:**
```python
# Update orchestrator.py to accept domain parameter
async def enrich_course(
    course_name: str,
    state_code: str = "VA",
    course_id: int | None = None,
    use_test_tables: bool = True,
    domain: str = ""  # Add this for compatibility
):
```

---

## Production Validation Checklist

After deployment, verify:

- [ ] **Code matches Docker** (MD5 checksums identical)
- [ ] **Dockerfile includes all files** (COPY lines present)
- [ ] **Environment variables set** (feature flags, API keys)
- [ ] **Orchestrator active** (curl /orchestrator-info)
- [ ] **Health check passes** (curl /health)
- [ ] **Test case succeeds** (same course as Docker)
- [ ] **Logs show correct flow** (expected agents executing)
- [ ] **Costs match Docker** (within 10% variance)
- [ ] **Success rate matches Docker** (within 10% variance)
- [ ] **No new errors** (no regressions)

---

## Example: Apollo Deployment (Oct 29, 2025)

**Context:** Deploy Apollo orchestrator after Docker validation showed 60% success.

### Issue Encountered: Partial Sync

**First deployment:**
```bash
python production/scripts/sync_to_production.py golf-enrichment
git push origin main
```

**Problem:** orchestrator_apollo.py was outdated.

**Detection:**
```bash
md5 teams/golf-enrichment/orchestrator_apollo.py
# Output: 0e77271335d99aa403ac5edfeb71d4c6

md5 production/golf-enrichment/orchestrator_apollo.py
# Output: f8b3e1c9d4a... (DIFFERENT!)
```

**Resolution:**
```bash
# Re-sync the file
cp teams/golf-enrichment/orchestrator_apollo.py \
   production/golf-enrichment/orchestrator_apollo.py

# Verify
md5 teams/golf-enrichment/orchestrator_apollo.py
md5 production/golf-enrichment/orchestrator_apollo.py
# Both: 0e77271335d99aa403ac5edfeb71d4c6 ✓

# Commit and deploy
git add production/golf-enrichment/orchestrator_apollo.py
git commit -m "fix: Sync orchestrator_apollo.py with Docker-tested version"
git push origin main
```

### Environment Variables

**Added on Render:**
```
USE_APOLLO = true
APOLLO_API_KEY = DPyR74ac7h9w2y9DMAE90g
```

### Production Validation

```bash
# Verified orchestrator
curl https://agent7-water-hazards.onrender.com/orchestrator-info
# Response: "active_orchestrator": "apollo" ✓

# Tested Cardinal CC (succeeded in Docker)
curl -X POST .../enrich-course -d '{"course_name": "Cardinal Country Club"}'
# Result: 4 contacts, 100% emails, $0.18 cost ✓
```

**Outcome:** Production mirrored Docker. Deployment successful.

---

## Best Practices

1. **Always verify sync with MD5 checksums** - catches partial syncs
2. **Test same course in production as Docker** - confirms identical behavior
3. **Set env vars before deploying** - features activate immediately
4. **Monitor first 5-10 cases closely** - catch issues early
5. **Have rollback plan ready** - disable via env var or git revert
6. **Document what changed** - commit messages reference Docker results
7. **Validate incrementally** - health → orchestrator-info → test case → monitor

---

## Success Metrics

Production deployment succeeds when:

- ✅ Code is byte-for-byte identical to Docker testing
- ✅ Environment variables correctly configured
- ✅ Health endpoint responds
- ✅ Correct orchestrator active
- ✅ Test case produces same results as Docker
- ✅ First 10 cases show expected success rate
- ✅ Costs match Docker predictions
- ✅ No new errors in logs

---

## Next Steps After Successful Deployment

1. **Monitor for 24 hours** - first 50-100 cases
2. **Track metrics** - success rate, costs, errors
3. **Update documentation** - record actual vs predicted results
4. **Plan next iteration** - address remaining failure modes
5. **Archive test fixtures** - keep for regression testing

---

## Related Documentation

- [DOCKER_VALIDATION.md](DOCKER_VALIDATION.md) - Phase 4 (comes before this)
- [EXAMPLES.md](EXAMPLES.md) - Apollo deployment case study
- [ROOT_CAUSE_ANALYSIS.md](ROOT_CAUSE_ANALYSIS.md) - If production issues arise
