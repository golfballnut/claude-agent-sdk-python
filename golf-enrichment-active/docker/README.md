# Golf Enrichment V2 Validator - Docker Testing

**Purpose:** Test Render validator service in Docker before production deployment

**Location:** `agenttesting/golf-enrichment/docker/`

---

## Quick Start

### 1. Create `.env` file

```bash
cd agenttesting/golf-enrichment/docker
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 2. Run tests

```bash
./test_validator.sh
```

---

## What Gets Tested

- ✅ V2 JSON validation (all 5 sections)
- ✅ Database writes to Supabase
- ✅ Error handling for invalid data
- ✅ Validation flags (CRITICAL vs QUALITY)

---

## Directory Structure

```
agenttesting/golf-enrichment/
├── docker/                              # Docker test infrastructure
│   ├── docker-compose.validator.yml    # Services configuration
│   ├── Dockerfile.test                 # Test runner image
│   ├── test_validator.sh               # Main test script
│   ├── test_harness.py                 # Python test harness
│   ├── README.md                       # This file
│   └── .env.example                    # Environment template
└── testing/data/                        # Test data
    ├── v2_test_cases.json              # Test inputs
    └── expected_outputs.json           # Expected results
```

---

## Test Flow

1. Build validator service from `../render/validator/`
2. Start services (validator + test-runner)
3. Wait for validator health check ✅
4. Run test harness:
   - Load test cases from `../testing/data/`
   - Call validator API for each test
   - Verify database writes
   - Compare actual vs expected results
5. Generate test report → `./test_results/`
6. Clean up containers

---

## Success Criteria

**Deployment Ready If:**
- ✅ All valid tests pass (100%)
- ✅ Invalid tests fail as expected
- ✅ Database writes contain all expected fields
- ✅ Costs ≤ $0.20 per course

---

## Troubleshooting

### Validator fails to start
```bash
# Check logs
docker-compose -f docker-compose.validator.yml logs validator
```

### Tests fail
```bash
# Review test results
cat ./test_results/summary.txt
cat ./test_results/test_report.json
```

### Database writes fail
- Verify Supabase credentials in `.env`
- Check migrations 013 & 014 are applied
- Confirm tables exist: `llm_research_staging`, `golf_courses`, `golf_course_contacts`

---

## Next Steps

**After tests pass:**
1. Review `./test_results/summary.txt`
2. Document results in `../docs/PROGRESS.md`
3. Deploy to Render (see Session 4 deployment workflow)

---

**Reference:**
- Architecture: `../docs/ARCHITECTURE.md`
- Progress: `../docs/PROGRESS.md`
- Validator service: `../render/validator/README.md`
