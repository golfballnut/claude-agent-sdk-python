# Docker Validation - Production-Like Testing

**Purpose:** Validate fixes in Docker container before production deployment.

**Key Principle:** Docker environment matches production. If it works in Docker, it works in production.

**Proven:** Oct 29, 2025 - Validated Apollo fixes (3/5 success) before deployment.

---

## 🎯 Docker Validation Process

### Phase 1: Docker Setup (15-30 min)

**1.1 Update Environment Config**
```bash
# Add missing keys to .env.example
vim .env.example
# Add: APOLLO_API_KEY, HUNTER_API_KEY, etc.

# Verify local .env has all keys
cat .env | grep -E "APOLLO|HUNTER|SUPABASE"
```

**1.2 Create Docker Compose Config**
```yaml
# docker-compose.[variant].yml
version: '3.8'
services:
  agent-service:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8001:8000"  # Avoid conflicts
    environment:
      - USE_[FEATURE]=true  # Feature flag
      - API_KEY=${API_KEY}
    volumes:
      - ./results:/app/results
```

**1.3 Update Dockerfile if Needed**
```dockerfile
# Ensure all files are copied
COPY orchestrator.py .
COPY orchestrator_apollo.py .  # Don't forget variants!
COPY agents/ ./agents/
COPY api.py .
```

---

### Phase 2: Build & Start (10-15 min)

```bash
# Build image (~2-3 min)
docker-compose -f docker-compose.[variant].yml build

# Expected output:
# ✅ Successfully built
# ✅ All dependencies installed
# ✅ No errors

# Start service
docker-compose -f docker-compose.[variant].yml up -d

# Wait for startup
sleep 10
```

---

### ⚠️ Common Issue: Environment Variables Not Loading

**Problem:** Health check shows `"apollo_api": "missing"` despite .env file existing in project.

**Root Cause:**
- docker-compose environment section uses `${VAR}` syntax to reference shell environment variables
- These variables must exist in the shell environment when docker-compose runs
- .env file must be **explicitly loaded** if not in the same directory as docker-compose.yml
- Docker Compose does NOT automatically load .env from parent directories

**Symptoms:**
```bash
# Health check shows APIs as "missing"
curl http://localhost:8001/health | jq '.dependencies'
# {"apollo_api": "missing", "hunter_api": "missing"}

# Container logs show: "API key not found"

# Python in container can't access vars:
docker exec container python -c "import os; print(os.getenv('APOLLO_API_KEY'))"
# None
```

**Solution:**

```bash
# ❌ WRONG - .env not loaded from parent directory
cd docker/
docker-compose -f docker-compose.apollo.yml up -d

# ✅ CORRECT - explicitly specify .env file path
cd docker/
docker-compose --env-file ../.env -f docker-compose.apollo.yml up -d

# Alternative: Load into shell first
export $(cat ../.env | xargs)
docker-compose -f docker-compose.apollo.yml up -d
```

**Verification:**

```bash
# 1. Check health endpoint shows APIs configured
curl http://localhost:8001/health | jq '.dependencies'

# Expected (correct):
{
  "apollo_api": "configured",
  "hunter_api": "configured",
  "perplexity_api": "configured"
}

# Not (wrong):
{
  "apollo_api": "missing",
  "hunter_api": "missing"
}

# 2. Test API actually works
curl -X POST http://localhost:8001/enrich-course \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Test Course", "state_code": "NC", "domain": "test.com", "use_test_tables": true}'

# Should return results, not "API key not found" error
```

**Project Structure Context:**
```
project/
├── .env                          # Main env file
├── docker/
│   ├── docker-compose.yml        # Needs --env-file ../.env
│   ├── docker-compose.apollo.yml # Needs --env-file ../.env
│   └── Dockerfile
└── golf-enrichment/
    ├── agents/
    └── orchestrators/
```

**Proven:** Oct 30, 2025 - Fixed 0% success → 100% working in golf enrichment Docker testing

---

### Phase 3: Health Check (2 min)

```bash
# 1. Basic health
curl http://localhost:8001/health

# Expected:
# {"status": "healthy", ...}

# 2. Feature verification
curl http://localhost:8001/orchestrator-info

# Expected (if using feature flags):
# {"active_orchestrator": "apollo", ...}

# 3. Check dependencies
curl http://localhost:8001/health | jq '.dependencies'

# Expected:
# {
#   "apollo_api": "configured",
#   "hunter_api": "configured",
#   ...
# }
```

---

### Phase 4: Single Case Test (5-10 min)

**Test one failed case first:**

```bash
# Test first failed case
curl -s -X POST http://localhost:8001/enrich-course \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "Cardinal Country Club",
    "state_code": "NC",
    "domain": "playcardinal.net",
    "use_test_tables": true
  }' | jq > /tmp/cardinal_docker.json

# Check result
cat /tmp/cardinal_docker.json | jq '{
  success,
  contacts: (.agent_results.agent2.contacts | length),
  cost: .agent_results.agent2.total_cost_usd
}'

# Expected:
# {
#   "success": true,
#   "contacts": 4,
#   "cost": 0.175
# }
```

**If single case succeeds → Proceed to full suite**
**If fails → Check Docker logs, debug, rebuild**

---

### Phase 5: Full Test Suite (30-60 min)

**Create test script:**

```bash
#!/bin/bash
# testing/docker/test_fixes.sh

COURSES=(
  '{"name":"Course 1","domain":"example1.com"}'
  '{"name":"Course 2","domain":"example2.com"}'
)

SUCCESS=0
FAILED=0

for course in "${COURSES[@]}"; do
  RESPONSE=$(curl -s -X POST http://localhost:8001/enrich-course \
    -H "Content-Type: application/json" \
    -d "$course,\"use_test_tables\":true}")

  # Parse result
  SUCCESS_FLAG=$(echo "$RESPONSE" | jq -r '.success')

  if [ "$SUCCESS_FLAG" = "true" ]; then
    SUCCESS=$((SUCCESS+1))
  else
    FAILED=$((FAILED+1))
  fi

  sleep 10  # Rate limiting
done

RATE=$(echo "scale=1; $SUCCESS * 100 / (${SUCCESS} + ${FAILED})" | bc)
echo "Success rate: $SUCCESS/$(($SUCCESS + $FAILED)) ($RATE%)"
```

**Run:**
```bash
chmod +x testing/docker/test_fixes.sh
./testing/docker/test_fixes.sh
```

**Oct 29 Results:**
```
Testing 5 courses...
Success rate: 3/5 (60.0%)
✅ Met projection (expected 60%)
```

---

## 📊 Results Analysis

### Success Rate Comparison

```bash
# Calculate improvement
baseline_rate=44
docker_rate=60
improvement=$((docker_rate - baseline_rate))

echo "Baseline: ${baseline_rate}%"
echo "After fixes: ${docker_rate}%"
echo "Improvement: +${improvement} points"

# Check if target met
target=80
if [ $docker_rate -ge $target ]; then
  echo "✅ Target met: ${docker_rate}% ≥ ${target}%"
else
  gap=$((target - docker_rate))
  echo "⚠️  Gap to target: ${gap} points"
fi
```

---

### Cost Analysis

```bash
# Extract costs from results
for i in 1 2 3 4 5; do
  cat results/docker/course_${i}.json | jq -r '.agent_results.agent2.total_cost_usd'
done | awk '{sum+=$1; count++} END {print "Average: $" sum/count}'

# Expected: Average: $0.175
# Budget: $0.20
# Status: ✅ Under budget
```

---

### Data Quality Validation

```bash
# Check email coverage
for file in results/docker/*.json; do
  echo "$file:"
  jq '.agent_results.agent2.email_coverage' "$file"
done

# Expected: "4/4", "100%", etc.
# All should be high coverage
```

---

## 🐛 Docker Debugging

### Check Logs

```bash
# Follow logs in real-time
docker-compose -f docker-compose.[variant].yml logs -f

# View recent logs
docker-compose logs --tail=100

# Search for errors
docker-compose logs | grep "ERROR\|FAILED"

# Check specific service
docker-compose logs agent-service
```

---

### Shell into Container

```bash
# Access running container
docker-compose exec agent-service bash

# Check environment
env | grep API_KEY

# Test Python imports
python -c "from orchestrator_apollo import enrich_course; print('✅ Import OK')"

# Check file presence
ls -la | grep orchestrator
```

---

### Common Docker Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| **File not copied** | ModuleNotFoundError | Add COPY to Dockerfile |
| **Env var not set** | API key errors | Check docker-compose env section |
| **Port conflict** | Can't bind port | Use different port (8001) |
| **Outdated code** | Old behavior | Rebuild with --no-cache |
| **Permission errors** | Write failures | Check user permissions |

---

## 📋 Docker Test Checklist

### Pre-Test Validation

- [ ] Dockerfile includes all files (orchestrators, agents, templates)
- [ ] docker-compose has all environment variables
- [ ] .env file has all required API keys
- [ ] Port doesn't conflict (use 8001 if 8000 taken)
- [ ] Test data fixtures ready

### Build Validation

- [ ] Build completes without errors
- [ ] All dependencies installed
- [ ] Claude CLI installed and working
- [ ] Image size reasonable (<2GB)

### Runtime Validation

- [ ] Service starts successfully
- [ ] Health endpoint returns healthy
- [ ] Feature flags work (if using)
- [ ] Logs show correct orchestrator active
- [ ] All dependencies configured

### Functional Validation

- [ ] Single test case succeeds
- [ ] Full test suite runs
- [ ] Success rate meets target
- [ ] Costs within budget
- [ ] Data quality validated

### Database Validation (if applicable)

- [ ] Test tables used (not production)
- [ ] Data written correctly
- [ ] No duplicates created
- [ ] Required fields populated
- [ ] Foreign keys valid

---

## 🎯 Success Criteria

### Minimum for Production Deployment

**Must have:**
- ✅ Health check passes
- ✅ Success rate ≥ 80% (or meets target)
- ✅ Average cost ≤ budget
- ✅ Data quality maintained
- ✅ No critical regressions

**Should have:**
- ✅ Tested on 5+ cases
- ✅ Both successes and edge cases tested
- ✅ Database writes validated
- ✅ Costs tracked and documented
- ✅ Results analyzed and documented

---

## 📊 Docker Test Report Template

```markdown
# Docker Validation Report: [Fix Name]

## Test Configuration
- **Date:** YYYY-MM-DD
- **Docker Image:** [name:tag]
- **Orchestrator:** [which orchestrator]
- **Test Environment:** docker-compose.[variant].yml
- **Database:** Test tables

## Test Results

### Success Metrics
| Metric | Baseline | Docker Test | Target | Status |
|--------|----------|-------------|--------|--------|
| Success rate | X% | Y% | Z% | ✅/❌ |
| Avg cost | $X | $Y | $Z | ✅/❌ |
| Contacts/case | X | Y | Z | ✅/❌ |

### Detailed Results
- **Cases tested:** X
- **Succeeded:** Y (Z%)
- **Failed:** A (B%)
- **Cost range:** $X - $Y
- **Average cost:** $Z

## Comparison to Baseline

**Improvement:**
- Success rate: +X points
- Cost: ±$Y
- Data quality: Maintained/Improved

## Issues Found

1. [Issue 1 if any]
2. [Issue 2 if any]

## Deployment Readiness

- [ ] Success rate meets target
- [ ] Costs within budget
- [ ] No critical issues
- [ ] **Status:** ✅ Ready / ❌ Not Ready

## Recommendations

[Next steps based on results]
```

---

## 🚀 Oct 29 Example

**Docker compose created:** `docker-compose.apollo.yml`
**Build time:** 30 seconds (cached layers)
**Startup time:** 10 seconds
**Test duration:** 8 minutes (5 courses × 10 sec + setup)

**Results:**
- Success: 3/5 (60%)
- Cost: $0.19/course avg
- Email coverage: 100%
- Contacts: 4/course

**Validation:** ✅ Ready for production with domain enrichment

---

**Next:** [EXAMPLES.md](EXAMPLES.md) - Complete walkthrough of Apollo debugging session
