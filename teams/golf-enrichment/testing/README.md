# Golf Enrichment Testing

**Purpose:** Testing infrastructure for golf course enrichment agents

---

## Folder Structure

```
testing/
├── README.md (this file)
├── PROGRESS.md (main testing checklist)
│
├── email-enrichment/ (email enrichment testing)
│   ├── README.md
│   ├── progress.md
│   ├── test_apollo.py
│   ├── test_rocketreach.py
│   ├── test_waterfall.py
│   ├── data/ (sample contacts)
│   └── results/ (test outputs)
│
├── agents/ (unit tests for individual agents)
│   ├── test_agent1.py
│   ├── test_agent2.py
│   └── ...
│
├── integration/ (end-to-end workflow tests)
│   ├── test_contact_waterfall_full.py
│   └── test_fallback_sources.py
│
├── baselines/ (baseline test data)
│   └── course_108_baseline.json
│
├── data/ (shared test data)
│   ├── belmont.json
│   └── richmond.json
│
└── docker/ (Docker testing infrastructure)
    ├── test_failed_courses_docker.sh
    └── docker_waterfall_results_102825.md
```

---

## Running Tests

### Unit Tests (Individual Agents)
```bash
# Test specific agent
pytest testing/agents/test_agent3.py -v

# Test all agents
pytest testing/agents/ -v
```

### Integration Tests (Full Workflow)
```bash
# Test contact waterfall
pytest testing/integration/test_contact_waterfall_full.py -v

# Test all integration
pytest testing/integration/ -v
```

### Email Enrichment Tests
```bash
# Test Apollo.io
pytest testing/email-enrichment/test_apollo.py -v

# Test waterfall logic
pytest testing/email-enrichment/test_waterfall.py -v
```

### Docker Tests
```bash
# Run Docker test script
cd testing/docker
bash test_failed_courses_docker.sh
```

---

## Test Data

### Baselines
- `baselines/course_108_baseline.json` - Validated baseline for Course 108

### Sample Courses
- `data/belmont.json` - Belmont Golf Course test data
- `data/richmond.json` - Richmond Golf Course test data

### Email Enrichment Data
- `email-enrichment/data/` - Sample contacts for email testing

---

## Success Criteria

### Agent Tests
- All agents return valid data structures
- Cost per agent < $0.02
- Error handling works correctly

### Integration Tests
- Full workflow completes successfully
- Data written to database correctly
- Fallback logic triggers appropriately

### Email Enrichment Tests
- 90% coverage goal met
- 90%+ confidence for all emails
- Cost under $0.20/course

---

## Adding New Tests

1. **Unit Test:** Add to `testing/agents/test_agent{N}.py`
2. **Integration Test:** Add to `testing/integration/`
3. **Email Test:** Add to `testing/email-enrichment/`
4. **Update:** `testing/PROGRESS.md` with new test

---

## Monitoring Test Results

Track progress in:
- `testing/PROGRESS.md` - Main testing checklist
- `testing/email-enrichment/progress.md` - Email-specific progress
