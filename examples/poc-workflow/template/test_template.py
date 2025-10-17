#!/usr/bin/env python3
"""
Test Template for Claude SDK Agents

Provides standard testing framework for validating agent performance.
Tracks: cost, accuracy, speed, success rate

Usage:
    1. Copy this file to tests/test_agent{N}.py
    2. Replace {placeholders} with your values
    3. Define ground truth data
    4. Run: python tests/test_agent{N}.py
"""

import anyio
import json
import time
from pathlib import Path
import sys

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

# Import your agent
from agent{N}_{name} import {agent_function}


# ============================================================================
# TEST DATA
# ============================================================================

# Ground truth for validation
GROUND_TRUTH = {
    "input_id": "test_case_1",
    "expected_field1": "expected value",
    "expected_field2": "expected value",
    # Add expected outputs
}

# Test inputs
TEST_CASES = [
    {
        "param1": "test value 1",
        "param2": "test value 2",
    },
    # Add more test cases
]


# ============================================================================
# ACCURACY CHECKER
# ============================================================================

def check_accuracy(result: Dict, ground_truth: Dict) -> Dict[str, Any]:
    """
    Compare result against ground truth

    Args:
        result: Agent output
        ground_truth: Expected values

    Returns:
        Dict with accuracy metrics
    """
    accuracy = {
        "field1_match": False,
        "field2_match": False,
        "score": 0,
    }

    # Check each field
    if result.get("field1") == ground_truth.get("expected_field1"):
        accuracy["field1_match"] = True
        accuracy["score"] += 50

    if result.get("field2") == ground_truth.get("expected_field2"):
        accuracy["field2_match"] = True
        accuracy["score"] += 50

    return accuracy


# ============================================================================
# SINGLE TEST
# ============================================================================

async def test_single_case(test_input: Dict) -> Dict[str, Any]:
    """Test agent with single input"""
    print(f"\n{'='*70}")
    print(f"Testing: {test_input}")
    print(f"{'='*70}")

    start_time = time.time()

    try:
        result = await {agent_function}(test_input)
        elapsed = time.time() - start_time

        # Check if data found
        found = result.get("field1") is not None

        print(f"\n   Result: {'✅ Found' if found else '❌ Not found (null)'}")
        if found:
            print(f"   Field1: {result['field1']}")
            print(f"   Method: {result.get('method', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 0)}%")

        print(f"   Cost: ${result.get('_cost', 0):.4f}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Turns: {result.get('_turns', 0)}")

        return {
            "input": test_input,
            "output": result,
            "success": found,
            "cost": result.get("_cost", 0),
            "time_seconds": round(elapsed, 3),
        }

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "input": test_input,
            "error": str(e),
            "success": False,
        }


# ============================================================================
# BATCH TEST
# ============================================================================

async def test_batch():
    """Test agent with all test cases"""
    print("🧪 Agent {N} Batch Test")
    print("="*70)
    print(f"Test Cases: {len(TEST_CASES)}\n")

    results = []
    total_cost = 0
    successful = 0

    for test_case in TEST_CASES:
        result = await test_single_case(test_case)
        results.append(result)

        if result.get("success"):
            successful += 1

        total_cost += result.get("cost", 0)

        # Small delay between tests
        await anyio.sleep(0.5)

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}\n")

    success_rate = (successful / len(TEST_CASES)) * 100 if TEST_CASES else 0
    avg_cost = total_cost / len(TEST_CASES) if TEST_CASES else 0

    print(f"Success Rate: {successful}/{len(TEST_CASES)} ({success_rate:.0f}%)")
    print(f"Average Cost: ${avg_cost:.4f}")
    print(f"Total Cost: ${total_cost:.4f}")

    # Evaluation
    TARGET_SUCCESS = 50  # Adjust based on agent type
    TARGET_COST = 0.02   # Adjust based on budget

    print(f"\n{'='*70}")
    print("✅ EVALUATION")
    print(f"{'='*70}")
    print(f"   Success: {'✅' if success_rate >= TARGET_SUCCESS else '❌'} (target: {TARGET_SUCCESS}%)")
    print(f"   Cost: {'✅' if avg_cost < TARGET_COST else '❌'} (target: ${TARGET_COST})")

    if success_rate >= TARGET_SUCCESS and avg_cost < TARGET_COST:
        print(f"\n🎉 AGENT {N} PRODUCTION READY!")
    else:
        print(f"\n⚠️  NEEDS OPTIMIZATION")

    # Save results
    output_file = Path(__file__).parent.parent / "results" / f"agent{N}_test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "test_date": "2025-10-16",
            "total_tests": len(TEST_CASES),
            "successful": successful,
            "success_rate": success_rate,
            "avg_cost": avg_cost,
            "total_cost": total_cost,
            "results": results,
        }, f, indent=2)

    print(f"\n💾 Saved to: {output_file}")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run tests"""
    await test_batch()


if __name__ == "__main__":
    anyio.run(main)
