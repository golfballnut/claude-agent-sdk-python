---
name: agent-debugging
description: Systematic methodology for debugging production agent failures. Analyze logs to identify failure patterns, create test fixtures from real failures, implement targeted fixes, validate in Docker, then deploy. Proven Oct 29, 2025 with Apollo email enrichment (0% → 60% success). Use when agents fail in production, success rates drop, or costs exceed budget.
allowed-tools: Read, Bash, Edit, Write, Glob, Grep, mcp__supabase__execute_sql, mcp__render__list_logs, TodoWrite, Skill
---

# Agent Debugging - Production Failure Analysis SOP

## Purpose

Systematic approach to debugging agent failures in production. Transform production failures into validated fixes using real failure data, local testing, and Docker validation.

**Proven:** Oct 29, 2025 - Improved golf enrichment from 0% → 60% success in 5 hours.

---

## 🎯 The 5-Phase Debugging Framework

```
┌────────────────────────────────────────────────┐
│  PHASE 1: Production Log Analysis             │
│  Duration: 15-30 minutes                       │
│  Cost: Free                                    │
│                                                │
│  → Collect production logs                     │
│  → Identify failure patterns                   │
│  → Calculate success/failure rates             │
│  → Extract error messages & context            │
└────────────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────┐
│  PHASE 2: Test Fixture Creation               │
│  Duration: 15-30 minutes                       │
│  Cost: Free                                    │
│                                                │
│  → Extract failed cases from logs              │
│  → Structure as JSON test data                 │
│  → Prioritize by impact                        │
│  → Document failure context                    │
└────────────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────┐
│  PHASE 3: Fix Implementation & Local Testing  │
│  Duration: 1-3 hours                           │
│  Cost: <$0.10 (local testing)                  │
│                                                │
│  → Map root cause → targeted fix               │
│  → Implement fix in teams/ folder              │
│  → Test locally with unit tests                │
│  → Validate improvement projection             │
└────────────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────┐
│  PHASE 4: Docker Validation                    │
│  Duration: 1-2 hours                           │
│  Cost: $0.50-2.00 (testing)                    │
│                                                │
│  → Build Docker with fixes                     │
│  → Test on all failed cases                    │
│  → Measure success rate improvement            │
│  → Validate costs within budget                │
└────────────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────┐
│  PHASE 5: Production Deployment                │
│  Duration: 30-60 minutes                       │
│  Cost: Deployment cost                         │
│                                                │
│  → Sync to production/ folder                  │
│  → Deploy to cloud (Render/AWS)                │
│  → Monitor first deployments                   │
│  → Validate success rate improvement           │
└────────────────────────────────────────────────┘
```

---

## 🚀 When to Use This Skill

### ✅ Use When:

- Agents failing in production (success rate drop)
- Specific error patterns appearing in logs
- Costs exceeding budget
- Data quality issues detected
- Need to debug multi-agent workflows
- Success rate below target (e.g., <80%)

### 📋 Especially For:

- External API integration failures
- Search/discovery agents returning empty results
- Database write failures
- Cost optimization needs
- Workflow orchestration issues

---

## 📊 Quick Reference: 5-Phase Checklist

### Phase 1: Log Analysis ✅
- [ ] Collect logs from production
- [ ] Group failures by error message
- [ ] Calculate success/failure rates
- [ ] Identify common patterns
- [ ] Document root causes
- [ ] **Output:** Failure pattern analysis

### Phase 2: Test Fixtures ✅
- [ ] Extract failed cases from logs
- [ ] Structure as JSON test data
- [ ] Include all relevant context
- [ ] Prioritize by impact
- [ ] **Output:** `[failure_type]_test_data.json`

### Phase 3: Fix & Local Test ✅
- [ ] Map root cause to fix
- [ ] Implement fix in teams/ folder
- [ ] Write unit tests for fix
- [ ] Test locally (fast iteration)
- [ ] Project success rate improvement
- [ ] **Output:** Tested fixes in teams/

### Phase 4: Docker Validation ✅
- [ ] Create/update docker-compose.[variant].yml
- [ ] Build Docker with fixes
- [ ] Run test suite on failed cases
- [ ] Measure before/after success rate
- [ ] Validate costs within budget
- [ ] **Output:** Docker test results

### Phase 5: Production Deploy ✅
- [ ] Sync fixes to production/ folder
- [ ] Deploy to cloud platform
- [ ] Monitor first 5-10 cases
- [ ] Validate improvement
- [ ] **Output:** Production metrics

---

## 💡 Debugging Principles

### 1. Start with Real Failure Data

**DON'T:**
- ❌ Guess at failure causes
- ❌ Use synthetic test data
- ❌ Skip log analysis

**DO:**
- ✅ Analyze actual production logs
- ✅ Use real failed cases as test data
- ✅ Understand failure context

### 2. Test Locally First

**DON'T:**
- ❌ Fix code and immediately deploy Docker
- ❌ Skip unit testing
- ❌ Iterate in Docker (slow, expensive)

**DO:**
- ✅ Test fixes locally (10x faster)
- ✅ Write unit tests for fixes
- ✅ Validate improvement projection

### 3. Validate in Docker Before Production

**DON'T:**
- ❌ Deploy to production without Docker test
- ❌ Assume local tests = production behavior
- ❌ Skip Docker validation

**DO:**
- ✅ Test in production-like Docker environment
- ✅ Run full test suite on failed cases
- ✅ Measure actual improvement

### 4. Measure Everything

**Track:**
- Success rate (before/after)
- Cost per operation (before/after)
- Data quality metrics
- Time to fix
- Deployment confidence

---

## 🔍 Common Failure Patterns

### Pattern 1: Missing Input Data
**Symptoms:** "No X provided", "X is null"
**Root Cause:** Upstream agent skipped or failed
**Fix:** Fix upstream agent OR add data source
**Example:** Domain not provided → Agent 1 skipped incorrectly

### Pattern 2: Wrong Search Strategy
**Symptoms:** "No results found" but data exists
**Root Cause:** Search parameters don't match API's data
**Fix:** Adjust search strategy (domain vs name, exact vs fuzzy)
**Example:** Apollo name search fails, domain search succeeds

### Pattern 3: No Fallback Logic
**Symptoms:** Single point of failure, no graceful degradation
**Root Cause:** No fallback when primary source fails
**Fix:** Add fallback cascade (primary → secondary → tertiary)
**Example:** Apollo only → Apollo + Hunter fallback

### Pattern 4: Integration Issues
**Symptoms:** Data found but not passed between agents
**Root Cause:** API model missing fields, parameters not passed
**Fix:** Update API models, pass parameters through chain
**Example:** domain field missing from EnrichCourseRequest

---

## 🛠️ Tools & Techniques

### Log Collection

**Render:**
```bash
# Use Render MCP tool
mcp__render__list_logs(
    resource=["service_id"],
    service="api"
)
```

**Docker:**
```bash
docker-compose logs --tail=500 | grep "ERROR\|FAILED"
```

**Supabase Edge Functions:**
```bash
# Via Supabase dashboard or API
```

### Failure Pattern Analysis

```bash
# Group by error message
cat logs.txt | grep "ERROR" | sort | uniq -c | sort -rn

# Calculate failure rate
successes=$(grep "SUCCESS" logs.txt | wc -l)
failures=$(grep "FAILED" logs.txt | wc -l)
total=$((successes + failures))
rate=$(echo "scale=1; $successes * 100 / $total" | bc)
echo "Success rate: $rate%"
```

### Test Data Creation

```json
{
  "test_name": "Description of failure scenario",
  "description": "Why these cases failed",
  "date_captured": "2025-10-29",
  "source": "Production logs from Render",
  "cases": [
    {
      "id": "unique_id",
      "name": "Entity name",
      "error": "Exact error message",
      "context": {...}
    }
  ],
  "test_strategy": {
    "priority_1": "Most common failures",
    "expected_fix_impact": "Percentage improvement"
  }
}
```

---

## 📚 Supporting Documentation

**Detailed Guides:**
- [ROOT_CAUSE_ANALYSIS.md](ROOT_CAUSE_ANALYSIS.md) - Log analysis techniques
- [TEST_FIXTURE_CREATION.md](TEST_FIXTURE_CREATION.md) - Test data patterns
- [FIX_IMPLEMENTATION.md](FIX_IMPLEMENTATION.md) - Fix patterns & local testing
- [DOCKER_VALIDATION.md](DOCKER_VALIDATION.md) - Docker testing workflow

**Real Examples:**
- [EXAMPLES.md](EXAMPLES.md) - Complete Apollo debugging case study (Oct 29, 2025)

---

## ⏱️ Time & Cost Efficiency

### Typical Debugging Session

**Traditional Approach:**
```
Guess fix → Deploy Docker → Test → Fails → Guess again → Repeat
  1 hr      2-3 min       $0.50   ❌      1 hr      $0.50...

Total: 4-6 hours, $2-4, low confidence
```

**Framework Approach:**
```
Analyze logs → Create tests → Fix locally → Docker once → Deploy
   30 min        30 min       1-2 hrs      1 hr        30 min

Total: 3-4 hours, $0.50-1.00, high confidence
```

**Savings:**
- ⏱️ 30-40% time reduction
- 💰 50-75% cost reduction
- 📈 Higher success rate (data-driven fixes)

---

## 🎯 Success Criteria

### Before Deployment

**Minimum Requirements:**
- [ ] Root cause identified from logs (not guessed)
- [ ] Test fixtures created from real failures
- [ ] Fixes tested locally first
- [ ] Docker tests show improvement
- [ ] Success rate meets target (typically 80%+)
- [ ] Costs within budget

**Quality Gates:**
- [ ] Success rate improvement ≥ 20 percentage points
- [ ] Average cost per operation ≤ budget
- [ ] Data quality maintained or improved
- [ ] No new regressions introduced

---

## 🚨 Red Flags

**Stop and reassess if:**
- ❌ Can't identify clear failure pattern in logs
- ❌ Fixes don't improve success rate in tests
- ❌ Costs increase beyond budget
- ❌ Docker tests show regressions
- ❌ Can't reproduce failures locally

**Do this instead:**
1. Re-analyze logs for different patterns
2. Test alternative fix approaches
3. Consider if problem is upstream
4. Validate test data is representative
5. Check if issue is environmental

---

## 📖 Complete Example

**Case Study:** Apollo Email Enrichment (Oct 29, 2025)

**Problem:** 5/9 golf courses failed enrichment (44% success, need 90%)

**Solution in 5 hours:**
1. **Log Analysis (30 min):** Found "No contacts found" pattern
2. **Test Fixtures (30 min):** Created JSON with 5 failed courses
3. **Fix & Test (2.5 hrs):** Domain-first search + Hunter fallback
4. **Docker Validation (1 hr):** 3/5 succeeded (60% success)
5. **Deploy Ready:** Documented, validated, ready for production

**Results:**
- Success: 0/5 (0%) → 3/5 (60%)
- Contacts: 0 → 4 per course
- Email coverage: 0% → 100%
- Cost: $0.19/course (under $0.20 target)

See [EXAMPLES.md](EXAMPLES.md) for complete walkthrough.

---

## 🔄 Using This Skill

### Invocation

```bash
# In Claude Code
/skill agent-debugging

# Or via Skill tool
Skill(command="agent-debugging")
```

### What Happens

1. This SKILL.md loads (debugging framework)
2. Follow 5-phase process
3. Reference supporting docs as needed
4. Use templates and checklists
5. Document your debugging session

### Expected Outcome

- Clear understanding of failure root cause
- Test data capturing real failures
- Validated fixes that improve success rate
- Docker-tested before production
- Documented for future reference

---

## 📋 Debugging Workflow Template

### 1. Start Debugging Session

```markdown
## Debugging Session: [Agent/Feature Name]
**Date:** YYYY-MM-DD
**Problem:** [Description of failure]
**Target:** [Success rate goal, e.g., 90%]

### Current Metrics
- Success rate: X/Y (Z%)
- Failure rate: A/Y (B%)
- Common error: "Error message"
```

### 2. Log Analysis

Use [ROOT_CAUSE_ANALYSIS.md](ROOT_CAUSE_ANALYSIS.md) methodology:
- Collect logs
- Group by error
- Identify patterns
- Calculate rates

### 3. Create Test Fixtures

Use [TEST_FIXTURE_CREATION.md](TEST_FIXTURE_CREATION.md) templates:
- Extract failed cases
- Structure as JSON
- Prioritize by impact
- Document context

### 4. Implement Fixes

Use [FIX_IMPLEMENTATION.md](FIX_IMPLEMENTATION.md) patterns:
- Map root cause to fix
- Implement in teams/ folder
- Test locally first
- Project improvement

### 5. Validate in Docker

Use [DOCKER_VALIDATION.md](DOCKER_VALIDATION.md) workflow:
- Build with fixes
- Test failed cases
- Measure improvement
- Validate costs

---

## 💰 ROI Analysis

### Golf Enrichment Example (Oct 29, 2025)

**Investment:**
- Time: 5 hours
- Cost: ~$1-2 (testing)

**Return:**
- Success rate: 0% → 60% (+60 points)
- Data quality: 0 contacts → 4 verified contacts per course
- Email coverage: 0% → 100%
- Unblocked: 30% of "gold data" now enrichable

**Monthly Value:**
- 3 courses/week × 4 weeks = 12 courses
- 12 courses × 4 contacts = 48 new verified contacts/month
- 48 contacts × $500 avg deal value = $24,000 potential revenue
- ROI: 12,000x return on debugging investment

---

## 🎓 Best Practices

### DO:
- ✅ Analyze logs BEFORE coding fixes
- ✅ Create test fixtures from REAL failures
- ✅ Test locally first (fast iteration)
- ✅ Validate in Docker before production
- ✅ Measure before/after metrics
- ✅ Document root causes and fixes
- ✅ Track costs throughout

### DON'T:
- ❌ Guess at root causes
- ❌ Use synthetic test data
- ❌ Skip local testing
- ❌ Deploy without Docker validation
- ❌ Ignore cost implications
- ❌ Forget to document findings

---

## 🔧 Quick Start

**Step 1: Collect Logs**
```bash
# Render logs
mcp__render__list_logs(resource=["service_id"])

# Docker logs
docker-compose logs --tail=500 > production_logs.txt
```

**Step 2: Analyze**
```bash
# See ROOT_CAUSE_ANALYSIS.md for detailed methodology
grep "FAILED\|ERROR" production_logs.txt | sort | uniq -c
```

**Step 3: Create Test Fixture**
```bash
# See TEST_FIXTURE_CREATION.md for template
vim testing/[agent]/data/failure_test_cases.json
```

**Step 4: Fix & Test**
```bash
# Edit agent in teams/ folder
vim teams/[team]/agents/agent_X.py

# Test locally
python -m pytest testing/[agent]/test_fixes.py
```

**Step 5: Docker Validate**
```bash
# See DOCKER_VALIDATION.md for complete workflow
docker-compose -f docker-compose.[variant].yml up --build
./testing/docker/test_fixes.sh
```

---

## 📈 Success Metrics Template

**Track for every debugging session:**

| Metric | Before | After | Target | Status |
|--------|--------|-------|--------|--------|
| Success rate | X% | Y% | 90% | ✅/❌ |
| Avg cost/operation | $X | $Y | $Z | ✅/❌ |
| Data quality | Low/Med/High | High | High | ✅/❌ |
| Time to fix | - | X hrs | - | - |

**Minimum for deployment:**
- Success rate improvement ≥ 20 points
- Costs within budget
- Data quality maintained or improved

---

## 🚨 Debugging Decision Tree

```
Is success rate < target?
  ├─ YES → Continue with Phase 1 (Log Analysis)
  └─ NO → Skip debugging, focus on optimization

Can you identify failure pattern in logs?
  ├─ YES → Phase 2 (Create test fixtures)
  └─ NO → Collect more logs, review with domain expert

Can you reproduce failures locally?
  ├─ YES → Phase 3 (Implement fix)
  └─ NO → Check environment differences, API keys, data access

Do local tests show improvement?
  ├─ YES → Phase 4 (Docker validation)
  └─ NO → Re-analyze root cause, try different fix

Do Docker tests meet success criteria?
  ├─ YES → Phase 5 (Production deployment)
  └─ NO → Debug Docker environment, check for regressions

Does production show improvement?
  ├─ YES → Success! Document and close
  └─ NO → Rollback, re-analyze production differences
```

---

## 📚 Reference Materials

### Supporting Documentation
- **ROOT_CAUSE_ANALYSIS.md** - Log analysis techniques, pattern identification
- **TEST_FIXTURE_CREATION.md** - Test data structure, prioritization
- **FIX_IMPLEMENTATION.md** - Fix patterns, local testing
- **DOCKER_VALIDATION.md** - Docker testing workflow, success criteria

### Real-World Examples
- **EXAMPLES.md** - Complete Apollo debugging case study (Oct 29, 2025)
  - 0% → 60% success improvement
  - Domain-first search fix
  - Hunter.io fallback implementation
  - Docker validation workflow

### Related Skills
- **agent-testing** - Building new agents from scratch
- **agent-workflow-testing** - Testing multi-agent workflows
- **golf-testing** - Domain-specific testing procedures

---

## 🎯 Typical Debugging Session Flow

```bash
# 1. Collect and analyze logs
mcp__render__list_logs(...) > production_logs.txt
grep "FAILED" production_logs.txt | wc -l  # Count failures

# 2. Create test fixture
vim testing/data/apollo_failures.json
# Structure: {test_name, cases[], test_strategy}

# 3. Implement fix
vim teams/my-team/agents/agent2.py
# Add: if-else fallback, search strategy change, etc.

# 4. Test locally
python testing/test_agent2_fixes.py
# Validate: Fixes work, costs acceptable

# 5. Docker validate
docker-compose -f docker-compose.fixes.yml up --build
./testing/docker/test_fixes.sh
# Result: 80%+ success → Ready to deploy!

# 6. Deploy
python production/scripts/sync_to_production.py my-team
cd production/my-team && git push
```

---

## 📊 Debugging Metrics Dashboard

**Track these metrics:**

```
BEFORE Debugging:
├─ Success Rate: X%
├─ Failure Rate: Y%
├─ Avg Cost: $Z
├─ Common Errors: [List top 3]
└─ Impact: [Business impact]

AFTER Debugging:
├─ Success Rate: X% (+N points)
├─ Failure Rate: Y% (-N points)
├─ Avg Cost: $Z (±change)
├─ Fixed Errors: [Which ones]
└─ Remaining Issues: [What's left]

DEPLOYMENT READINESS:
├─ Local Tests: ✅ Pass
├─ Docker Tests: ✅ Pass
├─ Success Target: ✅ Met (≥80%)
├─ Cost Budget: ✅ Within limits
└─ Ready: ✅ YES / ❌ NO
```

---

## 🚀 Advanced Techniques

### Parallel Fix Testing

Test multiple fix approaches simultaneously:
```bash
# Test approach A
vim teams/my-team/agents/agent2_approach_a.py
python testing/test_approach_a.py

# Test approach B
vim teams/my-team/agents/agent2_approach_b.py
python testing/test_approach_b.py

# Compare results, pick best approach
```

### A/B Testing in Docker

```yaml
# docker-compose.ab-test.yml
services:
  agent-approach-a:
    build: ...
    environment:
      - USE_APPROACH=a

  agent-approach-b:
    build: ...
    environment:
      - USE_APPROACH=b
```

### Regression Prevention

Save test fixtures for future regression testing:
```bash
testing/
├── data/
│   ├── apollo_failures_oct29.json
│   ├── hunter_failures_oct15.json
│   └── regression_suite.json  # All historical failures
└── regression/
    └── test_all_historical_failures.py
```

---

## 🎓 Lessons from the Field

### From Golf Enrichment (Oct 29, 2025)

**What Worked:**
1. Log analysis revealed clear pattern ("No contacts found")
2. Test fixtures from real failures (not synthetic)
3. Unit tests discovered Apollo CAN find courses (search strategy issue)
4. Domain-first search: Simple fix, huge impact (+60% success)
5. Docker validation caught integration bug (domain parameter)
6. Iterative testing: Fix → test → fix → test

**What We Learned:**
1. Real API behavior ≠ assumptions (test to find truth)
2. Simple fixes often have biggest impact (domain vs name search)
3. Docker catches integration issues local tests miss
4. Document everything - debugging insights are valuable
5. Success rate improvements compound (60% → 80% → 90%)

---

## 📞 Getting Help

**If stuck:**
1. Review supporting docs for detailed guidance
2. Check EXAMPLES.md for similar scenarios
3. Use related skills (agent-testing, agent-workflow-testing)
4. Consult with domain experts
5. Try alternative fix approaches

**Common issues:**
- Can't reproduce locally → Check environment/API keys
- Docker doesn't match local → Rebuild, check sync
- Fixes don't improve → Re-analyze root cause
- Costs too high → Optimize, use cheaper alternatives

---

**Version:** 1.0.0
**Created:** 2025-10-29
**Proven:** Apollo email enrichment debugging (0% → 60% success)
**Maintained By:** Engineering Team
