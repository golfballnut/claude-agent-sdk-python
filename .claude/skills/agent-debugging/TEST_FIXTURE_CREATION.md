# Test Fixture Creation - Real Failure Data

**Purpose:** Create test data from production failures for validating fixes.

**Key Principle:** Use REAL failure data, not synthetic test cases.

**Proven:** Oct 29, 2025 - `apollo_failure_courses.json` captured 5 real failures, validated fixes.

---

## Why Real Failure Data Matters

### Real Data Benefits

✅ **Authentic:** Actual production conditions
✅ **Complete:** All edge cases captured
✅ **Validated:** Fix that works on real data works in production
✅ **Regression prevention:** Save for future testing

### Synthetic Data Problems

❌ **Incomplete:** Miss edge cases
❌ **Unrealistic:** Don't match production patterns
❌ **False confidence:** Pass tests but fail in production
❌ **Waste time:** Debug issues that don't exist in production

---

## 📋 Test Fixture Structure

### Standard JSON Format

```json
{
  "test_name": "Brief description of test scenario",
  "description": "Why these cases failed and what we're testing",
  "date_captured": "YYYY-MM-DD",
  "source": "Where this data came from (e.g., Production logs, Render)",
  "cases": [
    {
      "id": "unique_identifier",
      "input_field_1": "value",
      "input_field_2": "value",
      "error": "Exact error message from production",
      "context": {
        "relevant_field_1": "value",
        "relevant_field_2": "value"
      },
      "notes": "Additional context or observations"
    }
  ],
  "test_strategy": {
    "priority_1": "What to test first",
    "priority_2": "Secondary test",
    "expected_improvement": "Success rate projection"
  }
}
```

---

## 🏗️ Creation Process

### Step 1: Extract Failed Cases from Logs

**From text logs:**
```bash
# Find all failures
grep "FAILED" production_logs.txt > failures.txt

# Extract entity names/IDs
grep -oP 'course_name=\K[^,]+' failures.txt > failed_entities.txt

# Or use structured extraction
awk '/FAILED.*course:/ {print $NF}' production_logs.txt
```

**From API logs:**
```python
import re

# Parse logs
with open("production_logs.txt") as f:
    logs = f.read()

# Extract failures
failures = re.findall(r'FAILED: (.*?) - Error: (.*?)\n', logs)

# Structure
test_cases = []
for course_name, error in failures:
    test_cases.append({
        "course_name": course_name,
        "error": error
    })
```

---

### Step 2: Gather Complete Context

**For each failed case, collect:**

1. **Input Parameters**
   - What was sent to the agent?
   - All required + optional fields
   - Values at time of failure

2. **Error Details**
   - Exact error message
   - Stack trace if available
   - Agent/step that failed

3. **Environment Context**
   - Timestamp
   - Which service/container
   - Any relevant state

4. **Expected Outcome**
   - What should have happened?
   - Why did it fail?

---

### Step 3: Structure as JSON

**Example from Oct 29 Apollo debugging:**

```json
{
  "test_name": "Apollo Failure Cases - Hunter.io Fallback Test",
  "description": "5 courses where Apollo.io failed to find contacts. These courses should be used to test Hunter.io fallback logic.",
  "date_captured": "2025-10-29",
  "source": "Production logs from render.com",
  "courses": [
    {
      "course_id": 1425,
      "course_name": "Cardinal Country Club",
      "state": "NC",
      "domain": "playcardinal.net",
      "apollo_error": "No contacts found for 'Cardinal Country Club'",
      "has_domain": true,
      "notes": "Apollo searched but returned 0 results despite valid domain"
    },
    {
      "course_id": 1639,
      "course_name": "Carolina Colours Golf Club",
      "state": "NC",
      "domain": null,
      "apollo_error": "No contacts found for 'Carolina Colours Golf Club'",
      "has_domain": false,
      "notes": "Agent 1 was skipped, no domain provided. Need to fix domain discovery first."
    }
  ],
  "test_strategy": {
    "priority_1": "Test Hunter.io fallback on courses with domains (3 courses)",
    "priority_2": "Fix domain discovery for courses without domains (2 courses)",
    "expected_hunter_success_rate": "60-80% for courses with domains",
    "expected_overall_success_rate": "80-90% after all improvements"
  }
}
```

---

### Step 4: Prioritize by Impact

**Categorize failures:**

**High Priority (Fix First):**
- High frequency (>50% of failures)
- High business impact
- Clear root cause
- Low-medium fix effort

**Medium Priority (Fix Next):**
- Medium frequency (20-50%)
- Medium impact
- Understood root cause
- Medium effort

**Low Priority (Fix Later):**
- Low frequency (<20%)
- Low impact
- OR: Complex/unclear root cause
- OR: High effort required

**Oct 29 Example:**
```
High Priority:
- "No contacts found" (5/5 failures = 100%)
- Impact: 30% data loss
- Root cause: Search strategy
- Effort: 30 min (domain-first search)
→ Fix immediately ✅

Medium Priority:
- Missing domains (2/5 failures = 40%)
- Impact: Moderate
- Root cause: Agent 1 skip logic
- Effort: 30 min
→ Fix second ✅

Low Priority:
- Edge cases (0/5 this batch)
→ Monitor, fix if pattern emerges
```

---

## 📂 Test Fixture Organization

### Directory Structure

```
teams/[team]/testing/
├── data/
│   ├── [failure_type]_test_data.json
│   ├── apollo_failures_oct29.json
│   ├── hunter_failures_oct15.json
│   └── regression_suite.json  # Historical failures
├── [specific_tests]/
│   ├── test_apollo_fixes.py
│   └── test_hunter_fallback.py
└── docker/
    ├── test_fixes.sh
    └── results/
```

### File Naming Convention

**Format:** `[failure_type]_[date].json`

**Examples:**
- `apollo_failures_oct29.json` - Apollo-specific failures
- `missing_domains_oct29.json` - Domain discovery failures
- `email_enrichment_failures_oct15.json` - Email enrichment issues
- `regression_suite.json` - All historical failures for regression testing

---

## 🎯 Test Fixture Best Practices

### 1. Capture Complete Context

**Good:**
```json
{
  "course_id": 1425,
  "course_name": "Cardinal Country Club",
  "domain": "playcardinal.net",
  "error": "No contacts found",
  "timestamp": "2025-10-29T23:02:10Z",
  "agent": "agent2_apollo",
  "expected_contacts": "2-4",
  "notes": "Has domain, Apollo should find data"
}
```

**Bad (incomplete):**
```json
{
  "course_name": "Cardinal",
  "error": "failed"
}
```

---

### 2. Include Both Positives and Negatives

```json
{
  "positive_cases": [
    {"name": "Worked correctly", "expected_behavior": true}
  ],
  "negative_cases": [
    {"name": "Failed", "error": "...", "expected_behavior": false}
  ]
}
```

**Why:** Ensures fix doesn't break working cases (regression prevention)

---

### 3. Document Expected Outcomes

```json
{
  "course_name": "Cardinal Country Club",
  "domain": "playcardinal.net",
  "expected_before_fix": {
    "success": false,
    "contacts": 0,
    "error": "No contacts found"
  },
  "expected_after_fix": {
    "success": true,
    "contacts": "2-4",
    "emails": "100%"
  }
}
```

---

### 4. Version Your Test Fixtures

```json
{
  "fixture_version": "1.0",
  "created_date": "2025-10-29",
  "last_updated": "2025-10-29",
  "test_name": "Apollo Failures",
  "changes": [
    {
      "date": "2025-10-29",
      "change": "Initial creation from Oct 29 failures"
    }
  ],
  "cases": [...]
}
```

---

## 🧪 Test Fixture Validation

### Checklist Before Using Fixture

- [ ] All required fields present for agent input
- [ ] Error messages match production exactly
- [ ] Expected outcomes documented
- [ ] Prioritization clear
- [ ] Context sufficient for debugging
- [ ] Real data (not synthetic)

### Self-Test Questions

1. **Can someone reproduce the failure with this data?**
   - If NO: Add more context

2. **Is the root cause hypothesis included?**
   - If NO: Document your theory

3. **Are expected outcomes clear?**
   - If NO: Define success criteria

4. **Is this representative of production?**
   - If NO: Get real production data

---

## 📊 Example: apollo_failure_courses.json

**Complete real-world fixture from Oct 29, 2025:**

```json
{
  "test_name": "Apollo Failure Cases - Hunter.io Fallback Test",
  "description": "5 courses where Apollo.io failed to find contacts in production. Used to test domain-first search and Hunter.io fallback.",
  "date_captured": "2025-10-29",
  "source": "Production logs from render.com",
  "courses": [
    {
      "course_id": 1425,
      "course_name": "Cardinal Country Club",
      "state": "NC",
      "domain": "playcardinal.net",
      "apollo_error": "No contacts found for 'Cardinal Country Club'",
      "has_domain": true,
      "notes": "Apollo searched but returned 0 results despite valid domain"
    }
  ],
  "test_strategy": {
    "priority_1": "Test domain-first search on courses with domains (3 courses)",
    "priority_2": "Fix domain discovery for courses without domains (2 courses)",
    "expected_improvement": "60-80% success rate"
  },
  "results": {
    "after_fix": {
      "success_rate": "60% (3/5)",
      "domain_first_search": "100% (3/3 with domains)",
      "missing_domains": "0% (2/2 failed)",
      "conclusion": "Domain-first search works perfectly"
    }
  }
}
```

**Why this fixture is excellent:**
- ✅ Real production failures
- ✅ Complete context (IDs, domains, errors)
- ✅ Prioritization clear
- ✅ Expected outcomes defined
- ✅ Results documented (can compare to future)
- ✅ Reusable for regression testing

---

## 🎯 Creating Your First Test Fixture

**Quick start template:**

```json
{
  "test_name": "TODO: Name your test scenario",
  "description": "TODO: Why did these cases fail?",
  "date_captured": "TODO: YYYY-MM-DD",
  "source": "TODO: production logs / Render / Docker",
  "cases": [
    {
      "id": "TODO: unique identifier",
      "TODO_field_1": "TODO: value from logs",
      "TODO_field_2": "TODO: value from logs",
      "error": "TODO: exact error message",
      "expected": "TODO: what should have happened",
      "notes": "TODO: any relevant observations"
    }
  ],
  "test_strategy": {
    "priority_1": "TODO: Most impactful fix to test",
    "expected_improvement": "TODO: X% success rate"
  }
}
```

**Fill in TODOs with data from your root cause analysis.**

---

## 📚 Test Fixture Templates

### For API/Search Failures

```json
{
  "test_name": "[API] Search Failures",
  "api": "apollo.io",
  "endpoint": "/people/search",
  "cases": [
    {
      "search_params": {
        "organization_name": "...",
        "domain": "..."
      },
      "expected": "2-4 results",
      "actual": "0 results",
      "error": "No matches found"
    }
  ]
}
```

### For Missing Data Failures

```json
{
  "test_name": "Missing Domain Failures",
  "root_cause": "Agent 1 skipped, no domain discovered",
  "cases": [
    {
      "entity_name": "...",
      "domain_provided": null,
      "agent1_should_run": true,
      "agent1_actually_ran": false,
      "error": "No domain for Agent 2"
    }
  ]
}
```

### For Data Quality Issues

```json
{
  "test_name": "Email Confidence Too Low",
  "threshold": 90,
  "cases": [
    {
      "contact_name": "...",
      "email_found": "...",
      "confidence": 75,
      "expected_minimum": 90,
      "action": "Reject or use fallback"
    }
  ]
}
```

---

## ✅ Fixture Quality Checklist

**Before using fixture:**

### Completeness
- [ ] All input parameters captured
- [ ] Error messages exact (not paraphrased)
- [ ] Expected outcomes defined
- [ ] Context sufficient for reproduction

### Accuracy
- [ ] Data from real production (not made up)
- [ ] Timestamps match log entries
- [ ] IDs/identifiers correct
- [ ] Error messages verbatim

### Usefulness
- [ ] Prioritization clear (what to fix first)
- [ ] Test strategy defined
- [ ] Expected improvements quantified
- [ ] Can be used for regression testing

### Documentation
- [ ] Source documented
- [ ] Date captured
- [ ] Notes explain context
- [ ] Versioned if updated

---

## 🔄 Maintaining Test Fixtures

### When to Update

**Add new cases when:**
- New failure patterns emerge
- Edge cases discovered
- Production conditions change
- Fixes incomplete (still failing in some scenarios)

**Update existing cases when:**
- Fix deployed and validated
- Root cause better understood
- Expected outcomes change
- Additional context learned

### Versioning

```json
{
  "fixture_version": "2.0",
  "changes": [
    {
      "version": "1.0",
      "date": "2025-10-29",
      "change": "Initial creation - 5 Apollo failures"
    },
    {
      "version": "2.0",
      "date": "2025-11-05",
      "change": "Added 3 new failures found in production"
    }
  ],
  "cases": [...]
}
```

---

## 🎯 Real Example Walkthrough

### Oct 29 Apollo Debugging - Step by Step

**1. Collected logs:**
```bash
mcp__render__list_logs(resource=["service_id"])
# Saved to: production_logs_oct29.txt
```

**2. Identified failures:**
```
Found: 5 courses failed with "No contacts found"
Pattern: All have same error message
Rate: 5/9 failures (56%)
```

**3. Extracted data per failure:**

**Cardinal Country Club:**
```
Log entry:
2025-10-29T23:02:20.026Z Agent 2-Apollo: Finding current staff...
   Course: Cardinal Country Club
   Domain: playcardinal.net
❌ ENRICHMENT FAILED: No contacts found

Extracted to JSON:
{
  "course_id": 1425,
  "course_name": "Cardinal Country Club",
  "state": "NC",
  "domain": "playcardinal.net",
  "apollo_error": "No contacts found for 'Cardinal Country Club'",
  "has_domain": true,
  "notes": "Apollo searched but returned 0 results despite valid domain"
}
```

**4. Grouped by characteristic:**
```
Group A (3 courses): Have domain, Apollo failed
  → Test: Does domain-first search work?

Group B (2 courses): No domain provided
  → Test: Does Agent 1 discovery work?
```

**5. Created test fixture:**
```json
{
  "test_name": "Apollo Failure Cases",
  "courses": [...],  // All 5 courses
  "test_strategy": {
    "priority_1": "Test Apollo domain-first search (Group A)",
    "priority_2": "Fix Agent 1 domain discovery (Group B)",
    "expected_improvement": "60-80%"
  }
}
```

**6. Saved for testing:**
- Location: `testing/email-enrichment/data/apollo_failure_courses.json`
- Used by: `test_hunter_fallback_integration.py`
- Result: Found root cause, validated fix

---

## 🛠️ Automation Scripts

### Extract Failures Script

```python
#!/usr/bin/env python3
"""
Extract failed cases from production logs and create test fixture
"""
import re
import json
from datetime import datetime

def extract_failures(log_file, pattern):
    """Extract all cases matching failure pattern"""
    with open(log_file) as f:
        logs = f.read()

    # Extract failures using regex
    matches = re.findall(pattern, logs, re.MULTILINE)

    cases = []
    for match in matches:
        case = parse_failure(match)  # Custom parsing
        cases.append(case)

    return cases

def create_fixture(cases, test_name, description):
    """Structure cases as test fixture"""
    fixture = {
        "test_name": test_name,
        "description": description,
        "date_captured": datetime.now().strftime("%Y-%m-%d"),
        "source": "Production logs",
        "cases": cases,
        "test_strategy": {
            "priority_1": "TODO: Define priority",
            "expected_improvement": "TODO: X%"
        }
    }

    return fixture

# Usage
failures = extract_failures("production_logs.txt", r"FAILED: (.*)")
fixture = create_fixture(failures, "My Test", "Description")

with open("test_fixture.json", "w") as f:
    json.dump(fixture, f, indent=2)

print(f"Created fixture with {len(failures)} cases")
```

---

## 📈 Test Coverage Strategy

### Minimum Viable Fixture

**For initial testing:**
- 3-5 representative failures
- Cover most common error pattern
- Include context for reproduction

**Example:** 3 courses with domains (test domain-first search)

### Comprehensive Fixture

**For thorough validation:**
- 10-20 failures
- Multiple error patterns
- Edge cases included
- Both successes and failures

**Example:** All failures from past month + representative successes

### Regression Suite

**For long-term quality:**
- All historical failures
- Fixed issues (ensure no regression)
- Edge cases discovered over time
- Updated as new patterns emerge

---

## 🎓 Lessons Learned

### From Oct 29 Apollo Debugging

**What Worked:**
1. ✅ Captured exact data from logs (course IDs, domains, errors)
2. ✅ Grouped by characteristic (has domain vs no domain)
3. ✅ Prioritized by impact (most common first)
4. ✅ Documented expected outcomes
5. ✅ Saved for regression testing

**What We'd Do Differently:**
1. Could have captured more metadata (timestamps, costs)
2. Could have included successful cases for comparison
3. Could have documented API responses more thoroughly

### General Principles

1. **More context = better debugging**
   - Don't assume you have enough info
   - Capture everything that might be relevant
   - Can always remove later, hard to add back

2. **Structure reveals patterns**
   - JSON structure forces you to think systematically
   - Patterns become obvious when structured
   - Easier to spot commonalities

3. **Test fixtures are living documents**
   - Update as you learn more
   - Add new failures as discovered
   - Mark resolved issues
   - Reuse for regression prevention

---

## ✅ Fixture Validation Checklist

**Before using fixture for testing:**

### Completeness Check
- [ ] All failed cases from logs included
- [ ] Input parameters complete
- [ ] Expected outcomes defined
- [ ] Error messages verbatim

### Quality Check
- [ ] Real production data (not synthetic)
- [ ] Representative of failure population
- [ ] Edge cases included
- [ ] Prioritization makes sense

### Usability Check
- [ ] Clear test strategy
- [ ] Can reproduce failures with this data
- [ ] Improvement projections reasonable
- [ ] Documentation sufficient

**If all checked → Use for fix validation**
**If any missing → Enhance fixture first**

---

**Next:** [FIX_IMPLEMENTATION.md](FIX_IMPLEMENTATION.md) - Implement fixes based on root cause analysis and test with your fixtures
