# Testing Utilities

Test scripts for validating agent performance.

## batch_test_agent1.py

**Purpose:** Test Agent 1 with multiple courses

**Usage:**
```bash
python tests/batch_test_agent1.py
```

**What it does:**
- Tests 5 different courses
- Measures cost, speed, accuracy
- Saves results to `results/agent1_test_results.json`

**Output:**
- Results table
- Performance statistics
- JSON file for Agent 2 testing

## Adding New Tests

Follow this pattern:
```python
async def test_agent(input_data, expected_output):
    # Run agent
    result = await run_agent(input_data)

    # Track metrics
    metrics = {
        "cost": result.total_cost_usd,
        "time": result.duration_ms / 1000,
        "accuracy": result.output == expected_output
    }

    # Save to results/
    save_results(metrics)

    return metrics
```

## Cost Targets

- Agent 1: < $0.02/search
- Agent 2: < $0.02/extraction
- Full workflow: < $0.04/complete

Test failures if cost exceeds targets.
