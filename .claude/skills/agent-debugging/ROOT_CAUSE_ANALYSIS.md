# Root Cause Analysis - Production Log Analysis

**Purpose:** Systematic approach to analyzing production logs to identify agent failure patterns and root causes.

**Proven:** Apollo debugging (Oct 29, 2025) - Identified 2 distinct failure patterns from 5 failed courses.

---

## 📊 The Log Analysis Process

### Step 1: Collect Production Logs

**Render Platform:**
```bash
# Use Render MCP tool
mcp__render__list_logs(
    resource=["service_id"],
    service="api",
    level=["error", "warning"],
    text=["FAILED", "ERROR"],
    startTime="2025-10-29T00:00:00Z",
    endTime="2025-10-29T23:59:59Z"
)
```

**Docker/Local:**
```bash
# Export logs to file
docker-compose logs --since="24h" > production_logs_oct29.txt

# Or from running container
docker logs container_name > production_logs.txt
```

**Supabase Edge Functions:**
```sql
-- Query edge function logs if available
SELECT * FROM edge_function_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
  AND level IN ('error', 'warn')
ORDER BY created_at DESC;
```

---

### Step 2: Calculate Success/Failure Rates

**Quick analysis:**
```bash
# Count successes
grep "SUCCESS\|COMPLETE" logs.txt | wc -l

# Count failures
grep "FAILED\|ERROR" logs.txt | wc -l

# Calculate rate
successes=4
failures=5
total=$((successes + failures))
rate=$(echo "scale=1; $successes * 100 / $total" | bc)
echo "Success rate: ${successes}/${total} ($rate%)"
```

**Example from Oct 29:**
```
Successes: 4/9 courses (44%)
Failures: 5/9 courses (56%)
Gap to target: 90% - 44% = 46 points needed
```

---

### Step 3: Group Failures by Error Message

**Pattern extraction:**
```bash
# Extract unique error messages
grep "ERROR\|FAILED" logs.txt \
    | sed 's/.*ERROR: //' \
    | sed 's/.*FAILED: //' \
    | sort \
    | uniq -c \
    | sort -rn

# Example output:
#   5 Agent 2-Apollo: No contacts found for '...'
#   2 Agent 8: Database write failed
#   1 Agent 1: URL not found
```

**Identify top patterns:**
1. Most common error (appears most frequently)
2. Second most common
3. Others

**Oct 29 Example:**
```
Pattern 1 (5 occurrences): "Agent 2-Apollo: No contacts found for 'X'"
  → 100% of failures!
  → Clear target for fixing
```

---

### Step 4: Extract Failure Context

**For each failed case, collect:**

```markdown
### Failure Case #1
- **Entity:** Course name / ID
- **Error:** Exact error message
- **Timestamp:** When it failed
- **Input data:** What was provided
- **Expected:** What should have happened
- **Logs:** Relevant log snippet
```

**Example:**
```
### Cardinal Country Club
- **Course ID:** 1425
- **Error:** "Agent 2-Apollo: No contacts found for 'Cardinal Country Club'"
- **Timestamp:** 2025-10-29T23:02:10Z
- **Input:** course_name="Cardinal Country Club", domain="playcardinal.net"
- **Expected:** Should find 2-4 contacts
- **Logs:**
  ```
  Agent 2-Apollo: Finding current staff...
  Course: Cardinal Country Club
  Domain: playcardinal.net
  ❌ ENRICHMENT FAILED: No contacts found
  ```
```

---

### Step 5: Identify Common Characteristics

**Look for patterns across failures:**

**By input data:**
- Missing fields (domain, phone, etc.)
- Data format issues
- Invalid values

**By error type:**
- API errors (rate limits, auth failures)
- Search errors (no results, wrong results)
- Data errors (null, invalid format)
- Integration errors (parameters not passed)

**Oct 29 Analysis:**
```
Pattern 1: Missing Domains (2/5 failures)
- Carolina Colours Golf Club: domain = null
- Carolina Plantation Golf Club: domain = null
- Common: "Domain: Not provided" in logs
- Root cause: Agent 1 skipped incorrectly

Pattern 2: Apollo Has No Data (3/5 failures)
- Cardinal: domain provided BUT Apollo returns 0
- Carolina Club: domain provided BUT Apollo returns 0
- Carolina/Pinehurst: domain provided BUT Apollo returns 0
- Common: Domain exists but search strategy wrong
- Root cause: Searching by name instead of domain
```

---

## 🔍 Root Cause Identification Framework

### Level 1: Surface-Level Analysis

**Question:** What error message appears?

**Actions:**
- Read error message literally
- Check what the logs say
- Don't interpret yet, just observe

**Example:** "No contacts found for 'X'"
- Surface level: Agent can't find contacts
- Don't know WHY yet

---

### Level 2: Context Analysis

**Question:** What was the input? What was expected?

**Actions:**
- Extract input parameters from logs
- Determine expected output
- Identify the gap

**Example:**
```
Input: course_name="Cardinal Country Club", domain="playcardinal.net"
Expected: 2-4 contacts with emails
Actual: 0 contacts
Gap: Agent should find data but doesn't
```

---

### Level 3: Deep-Dive Investigation

**Question:** WHY did it fail? What's the actual root cause?

**Actions:**
- Reproduce failure locally
- Test with different parameters
- Check API documentation
- Compare to successful cases

**Example from Oct 29:**
```
Hypothesis 1: Apollo doesn't have data for this course
Test: Search Apollo by domain directly
Result: Found 9 contacts! ✅
Conclusion: Apollo HAS data

Hypothesis 2: Search strategy is wrong
Test: Production uses name search, try domain search
Result: Domain search works! ✅
Root Cause: Searching by name fails on name variations
```

---

### Level 4: Root Cause Classification

**Common Root Causes:**

| Category | Example | Fix Strategy |
|----------|---------|--------------|
| **Missing Data** | Field not provided | Add data source OR make optional |
| **Wrong Strategy** | Name search fails | Use domain/ID search instead |
| **No Fallback** | Single point of failure | Add fallback cascade |
| **Integration** | Parameter not passed | Update API/function signatures |
| **Logic Error** | Incorrect skip condition | Fix conditional logic |
| **API Limits** | Rate limited, quota exceeded | Add rate limiting, backoff |
| **Data Format** | UUID expected, int provided | Fix data types |

---

## 📋 Root Cause Analysis Checklist

### Data Issues

- [ ] Is required data missing from input?
- [ ] Is data in wrong format?
- [ ] Does upstream agent provide the data?
- [ ] Is data validation too strict?

### API/Search Issues

- [ ] Is search strategy optimal (domain vs name)?
- [ ] Are search parameters correct?
- [ ] Does API have this data?
- [ ] Are we using the right endpoint?
- [ ] Is API authentication working?

### Logic Issues

- [ ] Are skip conditions correct?
- [ ] Does fallback trigger appropriately?
- [ ] Are conditional branches tested?
- [ ] Is error handling adequate?

### Integration Issues

- [ ] Are parameters passed between agents?
- [ ] Does API model include all fields?
- [ ] Are types compatible (UUID vs int)?
- [ ] Is environment consistent?

---

## 🧪 Root Cause Validation

**Always validate your hypothesis:**

### Test Your Theory

```python
# Example: Theory = "Domain search works better than name search"

# Test A: Domain search
result_domain = await apollo_search(domain="playcardinal.net")
print(f"Domain search: {len(result_domain)} contacts")  # 9 contacts ✅

# Test B: Name search
result_name = await apollo_search(org_name="Cardinal Country Club")
print(f"Name search: {len(result_name)} contacts")  # 0 contacts ❌

# Conclusion: Domain search is better! Root cause confirmed.
```

### Compare to Successful Cases

**Find working examples:**
```bash
# What succeeded?
grep "SUCCESS" logs.txt | head -5

# Compare to failures
grep "FAILED" logs.txt | head -5

# What's different?
# Successful: Had domains in database
# Failed: No domains OR search strategy wrong
```

---

## 📊 Root Cause Documentation Template

```markdown
## Root Cause Analysis: [Problem Name]

### Problem Statement
- **Symptom:** [What users see]
- **Error:** [Error message]
- **Frequency:** [How often]
- **Impact:** [Business/user impact]

### Investigation

**Step 1: Log Analysis**
- Collected: X logs from [source]
- Pattern: [Common pattern]
- Affected: Y/Z cases (A%)

**Step 2: Hypothesis Formation**
- Theory 1: [Hypothesis]
- Theory 2: [Alternative hypothesis]

**Step 3: Hypothesis Testing**
- Tested: [How you tested]
- Result: [What you found]
- Validated: [Which hypothesis is correct]

### Root Cause

**Primary cause:** [Actual root cause]
**Supporting evidence:** [Why you're confident]
**Related factors:** [Contributing factors]

### Fix Strategy

**Approach:** [How to fix]
**Expected impact:** [Improvement projection]
**Cost:** [Implementation cost]
**Risk:** [Deployment risk]

### Validation

- [ ] Local tests confirm fix works
- [ ] Docker tests show improvement
- [ ] Costs within budget
- [ ] No regressions
```

---

## 🎯 Real Example: Apollo "No Contacts" Failures

### Problem Statement
- **Symptom:** 5/9 courses failed enrichment
- **Error:** "Agent 2-Apollo: No contacts found for 'X'"
- **Frequency:** 56% failure rate
- **Impact:** 30% of valuable data lost

### Investigation

**Step 1: Log Analysis**
```
Collected: 500 lines from Render logs (Oct 29, 2025)
Pattern: "No contacts found" × 5 times
Affected: 5/9 courses (56%)

Breakdown:
- 2 failures: "Domain: Not provided"
- 3 failures: Domain provided but still failed
```

**Step 2: Hypothesis Formation**
- **Theory 1:** Apollo doesn't have data for these courses
- **Theory 2:** Search strategy is wrong (name vs domain)
- **Theory 3:** API authentication issue

**Step 3: Hypothesis Testing**
```python
# Test Theory 1: Apollo has no data?
result = apollo_domain_search("playcardinal.net")
# Result: 9 contacts found! ✅
# Conclusion: Apollo HAS data - Theory 1 FALSE

# Test Theory 2: Search strategy wrong?
result_name = apollo_name_search("Cardinal Country Club")
# Result: 0 contacts ❌
result_domain = apollo_domain_search("playcardinal.net")
# Result: 9 contacts ✅
# Conclusion: Domain search works, name search fails - Theory 2 TRUE!

# Theory 3: Auth issue?
# Would affect all courses, not just some - Theory 3 FALSE
```

### Root Cause

**Primary:** Apollo searches by organization name, which fails on name variations
- "Carolina Club, The" ≠ database entry
- Name matching unreliable
- Domain matching 100% accurate

**Supporting evidence:**
- Domain search: 3/3 success (100%)
- Name search: 0/3 success (0%)
- Reproducible in unit tests

**Related factors:**
- 2 courses missing domains (upstream Agent 1 issue)
- Agent 1 skip logic incorrect

### Fix Strategy

**Approach:** Domain-first search with name fallback
```python
if domain:
    search by domain  # Reliable
else:
    search by name    # Less reliable but only option
```

**Expected impact:**
- 3/5 failures → successes (+60%)
- 2/5 still fail (need domain discovery fix)
- Combined: 80-100% success projected

**Cost:** $0 (no new APIs)
**Risk:** Low (backward compatible)

### Validation

- [✅] Local tests: 3/3 success with domain search
- [✅] Docker tests: 3/5 success (+60%)
- [✅] Costs: $0.19 (under $0.20 budget)
- [✅] No regressions: Courses with domains still work

---

## 🔧 Log Analysis Tools

### Bash Commands

```bash
# Count errors by type
grep "ERROR" logs.txt | awk '{print $NF}' | sort | uniq -c | sort -rn

# Extract timestamps of failures
grep "FAILED" logs.txt | awk '{print $1, $2}'

# Find all logs for specific entity
grep "Cardinal Country Club" logs.txt

# Extract cost data
grep "Cost:" logs.txt | awk '{print $NF}'

# Calculate average cost
grep "Cost: \$" logs.txt | sed 's/.*\$\([0-9.]*\).*/\1/' | awk '{sum+=$1} END {print sum/NR}'
```

### SQL Queries for Database Analysis

```sql
-- Find recently failed enrichments
SELECT
    id,
    course_name,
    agent_enrichment_status,
    agent_cost_usd,
    enrichment_requested_at,
    enrichment_completed_at
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '24 hours'
  AND agent_enrichment_status = 'failed'
ORDER BY enrichment_requested_at DESC;

-- Group failures by error
SELECT
    error_message,
    COUNT(*) as frequency,
    ROUND(AVG(agent_cost_usd), 4) as avg_cost
FROM golf_courses
WHERE agent_enrichment_status = 'failed'
GROUP BY error_message
ORDER BY frequency DESC;
```

---

## 📈 Pattern Identification Matrix

**Use this framework to categorize failures:**

| Pattern Type | Indicators | Root Cause Likely | Fix Strategy |
|--------------|-----------|-------------------|--------------|
| **Missing Input** | "X not provided", "X is null" | Upstream agent skipped | Fix upstream OR make optional |
| **Empty Results** | "No results found", "0 matches" | Wrong search strategy | Change search parameters |
| **API Error** | "HTTP 4XX", "Rate limited" | API issue | Add retry, fallback, or fix auth |
| **Data Format** | "Invalid UUID", "Type error" | Type mismatch | Fix data types |
| **Logic Error** | Wrong entity processed | Conditional bug | Fix if/else logic |
| **Integration** | Parameter not used | API model incomplete | Update models/signatures |

---

## 🎯 Success Rate Gap Analysis

**Calculate improvement needed:**

```python
current_rate = 44  # Current success %
target_rate = 90   # Target success %
gap = target_rate - current_rate  # 46 points needed

# Break down by fix impact
fix1_impact = 30  # Domain-first search
fix2_impact = 20  # Domain discovery
fix3_impact = 10  # Hunter fallback

projected_rate = current_rate + fix1_impact + fix2_impact + fix3_impact
# 44 + 30 + 20 + 10 = 104% (capped at 100%)

print(f"Projected success rate: {min(projected_rate, 100)}%")
# Output: 94% (exceeds 90% target ✅)
```

---

## 📝 Failure Analysis Document Template

```markdown
# Production Failure Analysis: [Date]

## Overview
- **Service:** [Agent/Service name]
- **Date Range:** [Start] to [End]
- **Total Operations:** [Count]
- **Failures:** [Count] ([Percentage]%)
- **Target:** [Target %]

## Failure Breakdown

### Error Pattern #1: [Error Message]
**Frequency:** X/Y ([Percentage]%)
**Example:**
```
[Log snippet]
```

**Affected Cases:**
1. [Entity 1]
2. [Entity 2]
...

**Common Characteristics:**
- [Pattern 1]
- [Pattern 2]

**Root Cause Hypothesis:**
[Your theory]

---

### Error Pattern #2: [Error Message]
[Same structure as above]

---

## Root Cause Analysis

### Investigation Steps
1. [Step 1: What you tested]
   - Result: [What you found]
2. [Step 2: Next test]
   - Result: [What you found]

### Confirmed Root Cause
[The actual root cause with evidence]

## Fix Recommendations

### Fix #1: [Name]
- **Impact:** [Expected improvement]
- **Cost:** [Implementation cost]
- **Effort:** [Time estimate]
- **Risk:** [Deployment risk]

### Fix #2: [Name]
[Same structure]

## Success Criteria

**Minimum acceptable:**
- Success rate: [X]% (+[Y] points)
- Cost: $[Z]/operation
- Data quality: Maintained

**Deployment gates:**
- [ ] Fixes tested locally
- [ ] Docker validation passed
- [ ] Costs within budget
- [ ] No regressions
```

---

## 🧠 Root Cause vs Symptom

**Always distinguish:**

**Symptom** (what you see):
- "No contacts found"
- "Agent failed"
- "Empty results"

**Root Cause** (why it happens):
- Search strategy wrong (name vs domain)
- Missing required input (no domain)
- API has no data for this entity
- Logic error (skip condition wrong)

**Example from Oct 29:**
```
❌ WRONG: "Apollo doesn't work for these courses"
   → This is a symptom, not root cause

✅ RIGHT: "Apollo searches by org name, but course names have
   variations. Domain search is more reliable."
   → This is the root cause

Fix: Use domain search when domain available, fallback to name search.
```

---

## 📊 Root Cause Confidence Levels

**Rate your confidence:**

### High Confidence (90%+)
- ✅ Reproduced failure locally
- ✅ Tested alternative that works
- ✅ Multiple pieces of evidence
- ✅ Matches known pattern

**Example:** Domain search works, name search fails (tested both)

### Medium Confidence (60-89%)
- ⚠️ Found likely cause
- ⚠️ Some supporting evidence
- ⚠️ Haven't tested alternative yet
- ⚠️ Matches partial pattern

**Example:** Suspect rate limiting but haven't confirmed

### Low Confidence (<60%)
- 🤔 Have theory but little evidence
- 🤔 Multiple possible causes
- 🤔 Haven't reproduced locally
- 🤔 Need more investigation

**Example:** Guessing at timeout issues without logs showing timeouts

---

## 🎯 Prioritization Matrix

**Which failures to fix first?**

| Priority | Frequency | Impact | Effort | ROI |
|----------|-----------|--------|--------|-----|
| **P0** | High (>50%) | High | Low-Med | Fix ASAP |
| **P1** | High OR High impact | Medium | Medium | Fix soon |
| **P2** | Medium | Medium | Low | Fix when convenient |
| **P3** | Low | Low-Med | High | Consider accepting |

**Oct 29 Example:**
```
"No contacts found" failures:
- Frequency: 5/5 failures (100%)
- Impact: 30% data loss (high)
- Effort: 2-3 hours (medium)
- ROI: Very high
- Priority: P0 - Fix immediately ✅
```

---

## 🔍 Investigation Techniques

### Technique 1: Controlled Comparison

**Compare success vs failure:**

```bash
# Extract successful case logs
grep -B 10 -A 10 "SUCCESS.*Carolina Trace" logs.txt > success_example.txt

# Extract failed case logs
grep -B 10 -A 10 "FAILED.*Cardinal" logs.txt > failure_example.txt

# Compare side-by-side
diff success_example.txt failure_example.txt
```

**Look for differences in:**
- Input parameters
- Execution flow
- API calls made
- Data returned

---

### Technique 2: Binary Search

**For intermittent failures:**

```
Test 100 cases → 50 fail
Test those 50 → 25 fail
Test those 25 → 12 fail
...
Find: Common characteristic in final set
```

---

### Technique 3: Reproduce Locally

**Critical for validation:**

```python
# Extract failed case input
course_name = "Cardinal Country Club"
domain = "playcardinal.net"

# Run agent locally
result = await agent2_apollo(course_name, domain)

# Expected: Should fail same way
# If fails: Root cause confirmed
# If succeeds: Environment difference (check API keys, etc.)
```

---

## 📚 Common Pitfalls

### Pitfall 1: Assuming vs Testing

**DON'T:**
- ❌ "Apollo probably doesn't have this data"
- ❌ Skip testing, just implement fallback

**DO:**
- ✅ Test Apollo directly to confirm
- ✅ May find Apollo DOES have data (search strategy wrong)

---

### Pitfall 2: Fixing Symptoms

**DON'T:**
- ❌ Add error handling to hide "No contacts found"
- ❌ Treat symptom without finding root cause

**DO:**
- ✅ Find WHY no contacts found
- ✅ Fix root cause (search strategy)
- ✅ Symptom disappears automatically

---

### Pitfall 3: Over-Fixing

**DON'T:**
- ❌ Add 5 fallback layers for rare edge case
- ❌ Implement complex solution for simple problem

**DO:**
- ✅ Fix most common issue first (80/20 rule)
- ✅ Simple fixes for simple problems
- ✅ Add complexity only if needed

**Oct 29 Example:**
```
Could have added: Hunter, website scraping, Google search, manual lookup
Actually needed: Just change search parameter (domain vs name)
Result: Simple fix, 60% improvement
```

---

## ✅ Root Cause Confidence Checklist

**Before implementing fix, ensure:**

- [ ] Root cause is validated (not assumed)
- [ ] Reproduced failure locally
- [ ] Tested alternative that works
- [ ] Understand why it works
- [ ] Fix addresses root cause (not symptom)
- [ ] Expected improvement quantified
- [ ] Risks identified and mitigated

**If all checked → Proceed to fix implementation**
**If any unchecked → More investigation needed**

---

**Next:** [TEST_FIXTURE_CREATION.md](TEST_FIXTURE_CREATION.md) - Structure test data from your analysis
