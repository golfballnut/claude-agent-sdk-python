# Test Results

This folder stores outputs from all test runs (local Docker and production Render).

## Purpose

- Track test outputs over time
- Compare local vs production behavior
- Debug issues by reviewing past runs
- Document performance and costs

## File Naming Convention

```
YYYY-MM-DD_HH-MM_{environment}_{test-name}.json
```

**Examples:**
- `2025-10-17_22-30_local_agent7-richmond.json`
- `2025-10-17_22-45_local_orchestrator-richmond.json`
- `2025-10-17_23-00_production_orchestrator-belmont.json`

**Components:**
- `YYYY-MM-DD_HH-MM`: Timestamp (sortable, easy to find recent tests)
- `environment`: `local` or `production`
- `test-name`: Descriptive name (endpoint + course name)

## How to Save Test Results

### Manual (Simple)
```bash
# Save full response to file
curl -X POST http://localhost:8000/enrich-course \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Richmond Country Club", "state_code": "VA"}' \
  > test_results/2025-10-17_22-30_local_orchestrator-richmond.json
```

### With Metadata (Recommended)
```bash
# Create wrapper with metadata
{
  echo '{'
  echo '  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",'
  echo '  "environment": "local",'
  echo '  "endpoint": "/enrich-course",'
  echo '  "response":'
  curl -s -X POST http://localhost:8000/enrich-course \
    -H "Content-Type: application/json" \
    -d '{"course_name": "Richmond Country Club", "state_code": "VA"}'
  echo '}'
} > test_results/2025-10-17_22-30_local_orchestrator-richmond.json
```

## What to Track

For each test, capture:
- **Full API response** (all agent results, costs, timing)
- **Environment** (local Docker or production Render)
- **Input parameters** (course name, state, options)
- **Timestamp** (when test was run)
- **Git commit** (optional: which code version)

## Comparing Results

### Quick Visual Comparison
```bash
# View two results side-by-side
diff test_results/2025-10-17_22-30_local_orchestrator-richmond.json \
     test_results/2025-10-17_23-00_production_orchestrator-richmond.json
```

### Extract Key Metrics
```bash
# Get cost from result
jq '.summary.total_cost' test_results/2025-10-17_22-30_local_orchestrator-richmond.json

# Get contact count
jq '.summary.contact_count' test_results/2025-10-17_22-30_local_orchestrator-richmond.json

# Get duration
jq '.summary.duration_seconds' test_results/2025-10-17_22-30_local_orchestrator-richmond.json
```

## .gitignore

Test result JSON files are **NOT committed to git** by default (see `.gitignore`).

**Why:**
- Test outputs can contain sensitive data
- Files can be large
- Results are environment-specific

**Exception:** You can commit specific results by force-adding:
```bash
git add -f test_results/important-baseline.json
```

## Directory Structure

```
test_results/
├── README.md                                           # This file
├── 2025-10-17_22-30_local_agent7-richmond.json        # Agent 7 test
├── 2025-10-17_22-45_local_orchestrator-richmond.json  # Full pipeline
└── 2025-10-17_23-00_production_orchestrator-richmond.json
```

## Tips

1. **Run tests in order:** Agent 7 first (regression), then orchestrator
2. **Save timestamps:** Helps track performance changes over time
3. **Compare before deploy:** Test locally, save result, deploy to production, compare
4. **Keep recent results:** Delete old test files after a few weeks
5. **Document issues:** If a test fails, save the output and add notes

## Example Test Session

```bash
# 1. Test Agent 7 (quick validation)
curl -X POST http://localhost:8000/count-hazards \
  -H "Content-Type: application/json" \
  -d @test_data/richmond.json \
  > test_results/$(date +%Y-%m-%d_%H-%M)_local_agent7-richmond.json

# 2. Test orchestrator (full pipeline)
curl -X POST http://localhost:8000/enrich-course \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Richmond Country Club", "state_code": "VA", "use_test_tables": true}' \
  > test_results/$(date +%Y-%m-%d_%H-%M)_local_orchestrator-richmond.json

# 3. Check results
ls -lt test_results/  # List most recent first
jq '.summary' test_results/2025-10-17_22-45_local_orchestrator-richmond.json
```

---

**Keep it simple:** Just save JSON files here with descriptive names and timestamps.
