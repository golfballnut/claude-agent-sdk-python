# Testing Framework

Test scripts for validating agent performance before production.

---

## Test Files

### test_agent1.py
**Purpose:** Batch test Agent 1 (URL Finder)

**Usage:**
```bash
python tests/test_agent1.py
```

**What it does:**
- Tests 5 different golf courses
- Measures: cost, speed, accuracy
- Validates 100% URL discovery rate
- Saves to `results/agent1_results.json`

**Target:** < $0.02/search, 100% accuracy

---

### test_agent2.py
**Purpose:** Batch test Agent 2 (Contact Extractor)

**Usage:**
```bash
python tests/test_agent2.py
```

**What it does:**
- Tests contact extraction from 5 course URLs
- Uses URLs from Agent 1 results
- Measures: cost, accuracy, contacts found
- Saves to `results/agent2_results.json`

**Target:** < $0.02/extraction, 100% accuracy

---

### test_agent3.py
**Purpose:** Batch test Agent 3 (Contact Enricher)

**Usage:**
```bash
python tests/test_agent3.py
```

**What it does:**
- Enriches 12 contacts from Agent 2 results
- Tests Hunter.io email + LinkedIn discovery
- Measures: success rate, cost per contact
- Tracks: email found, LinkedIn found, confidence scores
- Saves to `results/agent3_batch_test_results.json`

**Target:** < $0.02/contact, 50%+ success rate

---

## Test Configuration Files

### test_agent2_configs.py
**Purpose:** Compare different Agent 2 configurations

Tests multiple tool/model combinations to find optimal setup.

### test_agent2_simple.py
**Purpose:** Quick validation test for Agent 2

Single-case test with known ground truth.

---

## Running All Tests

```bash
# Run in sequence
python tests/test_agent1.py
python tests/test_agent2.py
python tests/test_agent3.py

# Or individually as needed
```

---

## Test Output

All tests save to `results/` folder:
- `agent1_results.json` - URLs for Agent 2 input
- `agent2_results.json` - Contacts for Agent 3 input
- `agent3_batch_test_results.json` - Enrichment results

**Format:**
```json
{
  "test_date": "2025-10-16",
  "total_tests": 12,
  "successful": 6,
  "success_rate": 50,
  "avg_cost": 0.0116,
  "results": [...]
}
```

---

## Creating New Tests

**Use template:**
```bash
cp ../template/test_template.py test_agent4.py
# Follow template comments to customize
```

**Or reference existing:**
- `test_agent1.py` - Simple pattern
- `test_agent2.py` - Data extraction pattern
- `test_agent3.py` - Enrichment pattern with success rate tracking

---

## Cost Targets

| Agent | Target | Actual | Status |
|-------|--------|--------|--------|
| Agent 1 | $0.02 | $0.0153 | ✅ |
| Agent 2 | $0.02 | $0.0123 | ✅ |
| Agent 3 | $0.02 | $0.0116 | ✅ |
| **Per Course** | **$0.05** | **$0.0392** | **✅** |

Tests fail if agents exceed targets.

---

## Testing Best Practices

1. **Use ground truth** - Validate against known correct data
2. **Test edge cases** - Not just happy path
3. **Track costs** - Every test logs `ResultMessage.total_cost_usd`
4. **Batch test** - Single success != production ready
5. **Save results** - JSON files for analysis and next agent input
6. **No fallbacks** - Tests should verify clean nulls, not guesses

---

## Reference

- `../template/test_template.py` - Complete test template
- `../template/DEVELOPMENT.md` - Testing guidelines
- Working tests in this folder - Real examples
