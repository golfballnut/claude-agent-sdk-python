# Fix Implementation & Local Testing

**Purpose:** Implement targeted fixes based on root cause analysis and validate locally before Docker testing.

**Key Principle:** Test fixes locally first (10x faster than Docker iteration).

---

## 🎯 Fix Implementation Process

### Step 1: Map Root Cause → Fix

| Root Cause | Fix Pattern | Example |
|------------|-------------|---------|
| **Wrong search strategy** | Update search parameters | Name → Domain search |
| **Missing input data** | Fix upstream agent OR add source | Run Agent 1 for missing domains |
| **No fallback** | Add fallback cascade | Apollo → Hunter → Website |
| **Skip logic wrong** | Fix conditional | Only skip if data actually exists |
| **Parameter not passed** | Update API model/signature | Add `domain` field to request |
| **Data type mismatch** | Fix type conversion | UUID vs int |

---

## 🔧 Common Fix Patterns

### Pattern 1: Search Strategy Improvement

**Before:**
```python
search_payload = {
    "q_organization_name": course_name  # Unreliable
}
```

**After:**
```python
# Domain-first (more reliable)
if domain:
    search_payload = {
        "organization_domain": domain
    }
else:
    # Fallback to name
    search_payload = {
        "q_organization_name": course_name
    }
```

**Impact:** Oct 29 - 0% → 100% success on courses with domains

---

### Pattern 2: Fallback Cascade

**Before:**
```python
result = await primary_source()
if not result:
    raise Exception("No data found")  # Give up
```

**After:**
```python
result = await primary_source()
if not result and has_fallback_data:
    result = await fallback_source()  # Try alternative
if not result:
    result = await final_fallback()  # Last resort
```

**Cost example:**
- Primary: $0.09
- Fallback: +$0.05 (only when needed)
- Total worst case: $0.14 (still under budget)

---

### Pattern 3: Fix Upstream Issues

**Before:**
```python
if state == "NC":
    domain = provided_domain  # May be null!
elif state == "VA":
    domain = await find_domain()
# NC courses can end up with no domain
```

**After:**
```python
# Run domain discovery if domain missing (any state)
if not domain or not domain.strip():
    domain = await find_domain()
```

**Impact:** Fixes 2/5 failures (40%)

---

### Pattern 4: Parameter Passing

**Before:**
```python
# API model
class Request(BaseModel):
    course_name: str
    state_code: str
    # Missing: domain field!

# Orchestrator call
result = await orchestrator(
    course_name=request.course_name,
    state_code=request.state_code
    # domain not passed!
)
```

**After:**
```python
# API model
class Request(BaseModel):
    course_name: str
    state_code: str
    domain: str | None = None  # Added

# Orchestrator call
result = await orchestrator(
    course_name=request.course_name,
    state_code=request.state_code,
    domain=request.domain  # Now passed
)
```

---

## 🧪 Local Testing Strategy

### Test 1: Unit Test Individual Fix

```python
# test_domain_first_search.py
async def test_domain_search_vs_name_search():
    """Validate domain search works better than name search"""

    # Test domain search
    result_domain = await apollo_search(domain="playcardinal.net")
    assert len(result_domain) > 0, "Domain search should find results"

    # Test name search (for comparison)
    result_name = await apollo_search(org_name="Cardinal Country Club")

    # Domain should be better
    assert len(result_domain) >= len(result_name)

    print(f"✅ Domain search: {len(result_domain)} contacts")
    print(f"   Name search: {len(result_name)} contacts")
```

---

### Test 2: Integration Test Full Workflow

```python
# test_agent2_apollo_fixes.py
async def test_failed_courses_with_fixes():
    """Test all 5 failed courses with fixes applied"""

    # Load test fixture
    with open("data/apollo_failures.json") as f:
        data = json.load(f)

    results = []
    for course in data["courses"]:
        result = await discover_contacts(
            course["course_name"],
            course["domain"]
        )

        results.append({
            "course": course["course_name"],
            "success": len(result["contacts"]) > 0,
            "contacts": len(result["contacts"])
        })

    # Calculate success rate
    success_count = sum(1 for r in results if r["success"])
    success_rate = success_count / len(results) * 100

    print(f"Success rate: {success_count}/{len(results)} ({success_rate}%)")

    # Validate improvement
    assert success_rate >= 60, f"Expected ≥60%, got {success_rate}%"
```

---

### Test 3: Cost Validation

```python
async def test_costs_within_budget():
    """Ensure fixes don't exceed cost budget"""

    budget_per_course = 0.20

    result = await enrich_course_with_fixes("Test Course", "NC", "domain.com")

    actual_cost = result["total_cost"]

    assert actual_cost <= budget_per_course, \
        f"Cost ${actual_cost} exceeds budget ${budget_per_course}"

    print(f"✅ Cost ${actual_cost} within budget")
```

---

## ⏱️ Local Testing Workflow

```bash
# 1. Implement fix in teams/
vim teams/my-team/agents/agent2.py

# 2. Run unit test (10 seconds)
python -m pytest testing/test_agent2_fixes.py::test_domain_search -v
# Result: ✅ Pass - fix works

# 3. Run integration test (30 seconds)
python testing/test_integration_with_fixes.py
# Result: 3/5 success (60%) - meets projection

# 4. Validate costs (10 seconds)
python -m pytest testing/test_costs.py -v
# Result: $0.19 < $0.20 budget ✅

# If all pass → Ready for Docker testing
# If any fail → Debug and iterate locally (still fast!)
```

**Total local testing time:** 1-2 minutes vs 2-3 min per Docker rebuild

---

## 📊 Fix Validation Criteria

### Before proceeding to Docker:

**Functionality:**
- [ ] Fix resolves root cause (not just symptom)
- [ ] Unit tests pass for fixed cases
- [ ] Integration tests show improvement
- [ ] Success rate meets projection

**Cost:**
- [ ] Cost per operation ≤ budget
- [ ] New APIs justified by improvement
- [ ] No unnecessary expensive calls

**Quality:**
- [ ] Data quality maintained or improved
- [ ] No false positives introduced
- [ ] Edge cases handled

**Regression:**
- [ ] Previously working cases still work
- [ ] No new failures introduced
- [ ] Backward compatible if possible

---

## 🚨 Red Flags During Implementation

**Stop and reassess if:**

❌ **Fix doesn't improve success rate locally**
- Re-check root cause analysis
- May have wrong root cause
- Try alternative fix approach

❌ **Costs exceed budget significantly**
- Optimize expensive operations
- Consider cheaper alternatives
- May need different approach

❌ **Breaking existing functionality**
- Regression detected
- Need backward compatibility
- Refactor fix to be non-breaking

❌ **Can't reproduce failures locally**
- Environment differences
- Missing configuration
- Need production data access

---

## 🎯 Real Example: Apollo Fixes

### Fix #1: Domain-First Search

**Root cause:** Name search unreliable
**Fix:** Search by domain when available

**Implementation (30 min):**
```python
# File: agent2_apollo_discovery.py, line 118-136

# Before
search_payload = {"q_organization_name": course_name}

# After
if domain and domain.strip():
    search_payload = {"organization_domain": domain.strip()}
else:
    search_payload = {"q_organization_name": course_name}
```

**Local test:**
```python
# Test on failed courses
test_courses = [
    ("Cardinal CC", "playcardinal.net"),
    ("Carolina Club", "thecarolinaclub.com"),
]

for name, domain in test_courses:
    result = await discover_contacts(name, domain)
    print(f"{name}: {len(result['contacts'])} contacts")

# Output:
# Cardinal CC: 4 contacts ✅
# Carolina Club: 4 contacts ✅
# Result: 100% success on courses with domains!
```

**Validation:**
- [✅] Root cause fixed (domain search works)
- [✅] Local test: 3/3 success
- [✅] Cost: $0.17 (under $0.20)
- [✅] Ready for Docker

---

### Fix #2: Domain Discovery

**Root cause:** Agent 1 skipped when shouldn't
**Fix:** Only skip if domain actually exists

**Implementation (30 min):**
```python
# File: orchestrator_apollo.py, line 140-160

# Before
if state_code == "VA" and not domain:
    domain = await find_domain()
elif not domain:  # BUG: Prints "SKIPPED" but domain still null!
    print("SKIPPED (NC course)")

# After
if not domain or not domain.strip():  # ANY state
    domain = await find_domain()
else:
    print(f"SKIPPED (domain provided: {domain})")
```

**Local test:**
```python
# Test on course without domain
result = await enrich_course(
    "Carolina Colours",
    "NC",
    domain=None  # Explicitly no domain
)

# Expect: Agent 1 runs
# Logs should show: "Agent 1: Finding URL..."
# Not: "Agent 1: SKIPPED"
```

---

### Fix #3: Hunter Fallback

**Root cause:** No fallback when Apollo fails
**Fix:** Add Hunter.io as secondary source

**Implementation (2 hours):**

**Function added:**
```python
async def hunter_domain_search_fallback(domain: str) -> List[Dict]:
    """Hunter.io fallback when Apollo returns 0"""
    # API call to Hunter
    # Filter for 90%+ confidence
    # Return contacts in same format
```

**Integration:**
```python
# In discover_contacts function
apollo_result = await apollo_search(...)

if len(apollo_result["contacts"]) == 0 and domain:
    print("Triggering Hunter fallback...")
    hunter_result = await hunter_domain_search_fallback(domain)
    if hunter_result:
        return hunter_result  # Use Hunter data
```

**Local test:**
```python
# Test on course Apollo might not have
result = await discover_contacts("Tiny Unknown Club", "example.com")

# Should see in logs:
# "Apollo found 0 contacts - triggering Hunter fallback..."
# "Hunter found X contacts"
```

---

## 📈 Projecting Improvement

### Calculate Expected Success Rate

```python
# Current metrics
baseline_success = 44  # 4/9 courses
total_failures = 5

# Fix impact estimates
fix1_will_help = 3  # Domain-first (courses with domains)
fix2_will_help = 0  # Domain discovery (courses still not findable)
fix3_will_help = 0  # Hunter (Apollo succeeded on all with domains)

# Projected
new_successes = baseline_success + fix1_will_help
new_total = 9
projected_rate = new_successes / new_total * 100

print(f"Projected: {new_successes}/{new_total} ({projected_rate}%)")
# Output: 7/9 (78%) - Close to 80% target!
```

---

## ✅ Implementation Quality Checklist

**Before committing fixes:**

### Code Quality
- [ ] Fix addresses root cause (not symptom)
- [ ] Code follows existing patterns
- [ ] Error handling added
- [ ] Logging for debugging
- [ ] Comments explain why

### Testing
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] Cost validation passing
- [ ] Tested on all fixture cases

### Documentation
- [ ] Fix documented in code comments
- [ ] Test results documented
- [ ] Before/after metrics captured
- [ ] Findings documented for future

### Safety
- [ ] Backward compatible
- [ ] No regressions
- [ ] Rollback plan exists
- [ ] Costs validated

**If all checked → Proceed to Docker validation**

---

**Next:** [DOCKER_VALIDATION.md](DOCKER_VALIDATION.md) - Validate fixes in production-like environment
