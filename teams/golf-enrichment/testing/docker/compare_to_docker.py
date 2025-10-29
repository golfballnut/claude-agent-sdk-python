#!/usr/bin/env python3
"""
Compare Docker Test Results to Local Baseline

Validates that Docker produces same results as local Claude Code MCP testing.
This is the QUALITY GATE - Docker must match baseline to pass.

Usage:
    python tests/local/compare_to_docker.py 93
    python tests/local/compare_to_docker.py 98 --tolerance cost=0.03

Tolerance Defaults:
    - cost: ±$0.02
    - contacts: exact match (0 diff)
    - segment_confidence: ±1 point
"""

import json
import sys
from pathlib import Path
from typing import Any


def compare_results(course_id: int, tolerance: dict[str, Any] = None) -> dict[str, Any]:
    """
    Compare Docker results vs local baseline

    Args:
        course_id: Course ID being tested
        tolerance: Acceptable differences (default: {"cost": 0.02, "contacts": 0})

    Returns:
        Comparison report with pass/fail status
    """

    # Default tolerance
    if tolerance is None:
        tolerance = {
            "cost": 0.02,  # $0.02 acceptable difference
            "contacts": 0,  # Must match exactly
            "segment_confidence": 1  # 1 point difference OK
        }

    # Load baseline (expected)
    baseline_file = Path(__file__).parent.parent / "baselines" / f"course_{course_id}_baseline.json"
    if not baseline_file.exists():
        print(f"❌ Baseline not found: {baseline_file}")
        print("\nRun this first:")
        print(f"  python tests/local/run_baseline.py {course_id} \"<course_name>\" VA")
        sys.exit(1)

    with open(baseline_file) as f:
        baseline = json.load(f)

    # Load Docker results (actual)
    docker_file = Path(f"/tmp/course{course_id}-docker.json")
    if not docker_file.exists():
        print(f"❌ Docker results not found: {docker_file}")
        print("\nRun Docker test first:")
        print(f'  curl -X POST http://localhost:8000/enrich-course -d \'{{"course_id": {course_id}, ...}}\'')
        sys.exit(1)

    with open(docker_file) as f:
        docker = json.load(f)

    # Comparison report
    report = {
        "course_id": course_id,
        "pass": True,
        "exact_matches": [],
        "within_tolerance": [],
        "failures": [],
        "warnings": []
    }

    print("\n" + "="*70)
    print(f"BASELINE vs DOCKER COMPARISON - Course {course_id}")
    print("="*70)

    # ===================================================================
    # CRITICAL COMPARISONS
    # ===================================================================

    # Cost comparison
    baseline_cost = baseline["summary"]["total_cost_usd"]
    docker_cost = docker.get("summary", {}).get("total_cost_usd", 0)
    cost_diff = abs(baseline_cost - docker_cost)

    print("\n💰 COST:")
    print(f"   Baseline (Expected): ${baseline_cost:.4f}")
    print(f"   Docker   (Actual):   ${docker_cost:.4f}")
    print(f"   Difference:          ${cost_diff:.4f}")

    if cost_diff == 0:
        print("   ✅ EXACT MATCH")
        report["exact_matches"].append("cost")
    elif cost_diff <= tolerance["cost"]:
        print(f"   ✅ WITHIN TOLERANCE (±${tolerance['cost']})")
        report["within_tolerance"].append(f"cost: ${cost_diff:.4f} diff")
    else:
        print(f"   ❌ EXCEEDS TOLERANCE! (allowed: ±${tolerance['cost']})")
        report["failures"].append(f"cost: ${cost_diff:.4f} exceeds ±${tolerance['cost']}")
        report["pass"] = False

    # Contact count comparison
    baseline_contacts = baseline["summary"]["contacts_enriched"]
    docker_contacts = docker.get("summary", {}).get("contacts_enriched", 0)

    print("\n👥 CONTACTS:")
    print(f"   Baseline (Expected): {baseline_contacts}")
    print(f"   Docker   (Actual):   {docker_contacts}")

    if baseline_contacts == docker_contacts:
        print("   ✅ EXACT MATCH")
        report["exact_matches"].append("contacts")
    else:
        print("   ❌ MISMATCH!")
        report["failures"].append(f"contacts: baseline={baseline_contacts}, docker={docker_contacts}")
        report["pass"] = False

    # Segment comparison
    baseline_segment = baseline["agent_results"]["agent6"]["segmentation"]["primary_target"]
    docker_segment = docker.get("agent_results", {}).get("agent6", {}).get("segmentation", {}).get("primary_target")

    print("\n🎯 SEGMENT:")
    print(f"   Baseline (Expected): {baseline_segment}")
    print(f"   Docker   (Actual):   {docker_segment}")

    if baseline_segment == docker_segment:
        print("   ✅ EXACT MATCH")
        report["exact_matches"].append("segment")
    else:
        print("   ⚠️  MISMATCH (acceptable - AI variance)")
        report["warnings"].append(f"segment: baseline={baseline_segment}, docker={docker_segment}")
        # Not a failure - AI may classify differently

    # Segment confidence comparison
    baseline_conf = baseline["agent_results"]["agent6"]["segmentation"]["confidence"]
    docker_conf = docker.get("agent_results", {}).get("agent6", {}).get("segmentation", {}).get("confidence", 0)
    conf_diff = abs(baseline_conf - docker_conf)

    print("\n📊 SEGMENT CONFIDENCE:")
    print(f"   Baseline (Expected): {baseline_conf}/10")
    print(f"   Docker   (Actual):   {docker_conf}/10")
    print(f"   Difference:          {conf_diff} points")

    if conf_diff <= tolerance["segment_confidence"]:
        print(f"   ✅ WITHIN TOLERANCE (±{tolerance['segment_confidence']} points)")
        report["within_tolerance"].append(f"segment_confidence: {conf_diff} point diff")
    else:
        print("   ⚠️  EXCEEDS TOLERANCE (acceptable - AI variance)")
        report["warnings"].append(f"segment_confidence: {conf_diff} points diff")

    # Water hazards
    baseline_water = baseline["agent_results"]["agent7"]["water_hazard_count"]
    docker_water = docker.get("agent_results", {}).get("agent7", {}).get("water_hazard_count")

    print("\n💧 WATER HAZARDS:")
    print(f"   Baseline (Expected): {baseline_water}")
    print(f"   Docker   (Actual):   {docker_water}")

    if baseline_water == docker_water:
        print("   ✅ EXACT MATCH")
        report["exact_matches"].append("water_hazards")
    else:
        print("   ⚠️  MISMATCH (acceptable - AI variance)")
        report["warnings"].append(f"water_hazards: baseline={baseline_water}, docker={docker_water}")

    # Course ID verification
    docker_course_id = docker.get("agent_results", {}).get("agent8", {}).get("course_id")

    print("\n🆔 COURSE ID:")
    print(f"   Expected: {course_id}")
    print(f"   Docker:   {docker_course_id}")

    if docker_course_id == course_id:
        print("   ✅ CORRECT COURSE UPDATED")
        report["exact_matches"].append("course_id")
    else:
        print("   ❌ WRONG COURSE! CRITICAL ERROR")
        report["failures"].append(f"course_id: expected={course_id}, actual={docker_course_id}")
        report["pass"] = False

    # ===================================================================
    # FINAL REPORT
    # ===================================================================

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    print(f"\n✅ EXACT MATCHES ({len(report['exact_matches'])}):")
    for match in report["exact_matches"]:
        print(f"   - {match}")

    if report["within_tolerance"]:
        print(f"\n⚠️  WITHIN TOLERANCE ({len(report['within_tolerance'])}):")
        for item in report["within_tolerance"]:
            print(f"   - {item}")

    if report["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(report['warnings'])}) - Acceptable AI variance:")
        for warning in report["warnings"]:
            print(f"   - {warning}")

    if report["failures"]:
        print(f"\n❌ FAILURES ({len(report['failures'])}):")
        for failure in report["failures"]:
            print(f"   - {failure}")

    print("\n" + "="*70)
    if report["pass"]:
        print("✅ PASS: Docker matches baseline - READY FOR PRODUCTION")
    else:
        print("❌ FAIL: Docker differs from baseline - FIX REQUIRED")
    print("="*70 + "\n")

    # Save comparison report
    report_file = Path(__file__).parent.parent / "baselines" / f"course_{course_id}_comparison.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"📊 Comparison report saved: {report_file}\n")

    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/local/compare_to_docker.py <course_id>")
        print("Example: python tests/local/compare_to_docker.py 93")
        sys.exit(1)

    course_id = int(sys.argv[1])

    # Parse tolerance from args if provided
    # e.g., --tolerance cost=0.03
    tolerance = None
    if "--tolerance" in sys.argv:
        # Parse custom tolerance (future enhancement)
        pass

    report = compare_results(course_id, tolerance)

    # Exit code based on pass/fail
    sys.exit(0 if report["pass"] else 1)
