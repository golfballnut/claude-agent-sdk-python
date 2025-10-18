#!/usr/bin/env python3
"""
Compare 3 JSON enrichment outputs to identify field mismatches and data patterns
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def load_json_files() -> List[Dict[str, Any]]:
    """Load the 3 most recent enrichment JSON files"""
    enrichment_dir = Path(__file__).parent / "results" / "enrichment"

    # Get 3 most recent files
    files = sorted(enrichment_dir.glob("enrichment_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:3]

    data = []
    for f in files:
        with open(f) as file:
            data.append({
                "filename": f.name,
                "data": json.load(file)
            })

    return data


def analyze_agent3_fields(jsons: List[Dict]) -> None:
    """Analyze Agent 3 email enrichment fields"""
    print("\n📧 AGENT 3: Email + LinkedIn")
    print("-" * 70)

    for j in jsons:
        course = j["data"]["course_name"]
        contacts = j["data"]["contacts"]

        print(f"\n{course}:")
        for contact in contacts:
            agent3 = contact.get("agent3", {})
            name = contact["name"]

            # Check field population
            email = agent3.get("email")
            email_conf_score = agent3.get("email_confidence_score")
            linkedin = agent3.get("linkedin_url")

            # Missing fields from Agent 3's actual output
            email_method = contact.get("email_method")  # Not in agent3 sub-object!
            email_confidence = contact.get("email_confidence")  # Not in agent3 sub-object!

            print(f"  {name}:")
            print(f"    email: {email or 'NULL'}")
            print(f"    email_confidence_score: {email_conf_score or '❌ NULL (ISSUE)'}")
            print(f"    email_method: {email_method or '❌ NOT MAPPED'}")
            print(f"    linkedin_url: {linkedin or 'NULL'}")


def analyze_agent65_fields(jsons: List[Dict]) -> None:
    """Analyze Agent 6.5 contact background fields"""
    print("\n📋 AGENT 6.5: Contact Background")
    print("-" * 70)

    for j in jsons:
        course = j["data"]["course_name"]
        contacts = j["data"]["contacts"]

        print(f"\n{course}:")
        for contact in contacts:
            agent65 = contact.get("agent65", {})
            name = contact["name"]

            tenure = agent65.get("tenure_years")
            prev_clubs = agent65.get("previous_clubs", [])
            industry_exp = agent65.get("industry_experience_years")
            responsibilities = agent65.get("responsibilities", [])

            print(f"  {name}:")
            print(f"    tenure_years: {tenure or 'NULL'}")
            print(f"    previous_clubs: {len(prev_clubs)} found")
            print(f"    industry_experience_years: {industry_exp or 'NULL'}")
            print(f"    responsibilities: {len(responsibilities)} found")


def create_field_comparison_table(jsons: List[Dict]) -> None:
    """Create comprehensive field comparison table"""
    print("\n📊 FIELD COMPARISON TABLE")
    print("="*70)

    # Course names
    course_names = [j["data"]["course_name"][:20] for j in jsons]

    # Header
    print(f"\n{'Field':<35} | {'Richmond CC':<15} | {'Belmont GC':<15} | {'Stonehenge':<15}")
    print("-" * 85)

    # Agent 6 (course-level)
    print(f"\n{'AGENT 6 (Course-Level)':}")
    for i, j in enumerate(jsons):
        agent6 = j["data"].get("agent6", {})
        seg = agent6.get("segmentation", {})
        opps = agent6.get("opportunities", {})

        if i == 0:  # First iteration, print field names
            print(f"{'  segment':<35} | {seg.get('primary_target', 'NULL'):<15} | ", end="")
        elif i == 1:
            print(f"{seg.get('primary_target', 'NULL'):<15} | ", end="")
        else:
            print(f"{seg.get('primary_target', 'NULL'):<15}")

    for i, j in enumerate(jsons):
        agent6 = j["data"].get("agent6", {})
        seg = agent6.get("segmentation", {})

        if i == 0:
            print(f"{'  segment_confidence':<35} | {seg.get('confidence', 'NULL'):<15} | ", end="")
        elif i == 1:
            print(f"{seg.get('confidence', 'NULL'):<15} | ", end="")
        else:
            print(f"{seg.get('confidence', 'NULL'):<15}")

    for i, j in enumerate(jsons):
        agent6 = j["data"].get("agent6", {})
        range_intel = agent6.get("range_intel", {})

        if i == 0:
            print(f"{'  has_range':<35} | {str(range_intel.get('has_range', 'NULL')):<15} | ", end="")
        elif i == 1:
            print(f"{str(range_intel.get('has_range', 'NULL')):<15} | ", end="")
        else:
            print(f"{str(range_intel.get('has_range', 'NULL')):<15}")

    # Agent 7
    print(f"\n{'AGENT 7 (Water Hazards)':}")
    for i, j in enumerate(jsons):
        agent7 = j["data"].get("agent7", {})

        if i == 0:
            print(f"{'  water_hazard_count':<35} | {agent7.get('water_hazard_count', 'NULL'):<15} | ", end="")
        elif i == 1:
            print(f"{str(agent7.get('water_hazard_count', 'NULL')):<15} | ", end="")
        else:
            print(f"{str(agent7.get('water_hazard_count', 'NULL')):<15}")

    # Agent 3 (first contact only)
    print(f"\n{'AGENT 3 (First Contact)':}")
    for i, j in enumerate(jsons):
        contact = j["data"]["contacts"][0] if j["data"]["contacts"] else {}
        agent3 = contact.get("agent3", {})

        if i == 0:
            email = agent3.get("email", "NULL")
            display = "FOUND" if email != "NULL" else "NULL"
            print(f"{'  email':<35} | {display:<15} | ", end="")
        elif i == 1:
            email = agent3.get("email", "NULL")
            display = "FOUND" if email != "NULL" else "NULL"
            print(f"{display:<15} | ", end="")
        else:
            email = agent3.get("email", "NULL")
            display = "FOUND" if email != "NULL" else "NULL"
            print(f"{display:<15}")

    for i, j in enumerate(jsons):
        contact = j["data"]["contacts"][0] if j["data"]["contacts"] else {}
        agent3 = contact.get("agent3", {})

        if i == 0:
            conf = agent3.get("email_confidence_score")
            display = str(conf) if conf else "❌ NULL"
            print(f"{'  email_confidence_score':<35} | {display:<15} | ", end="")
        elif i == 1:
            conf = agent3.get("email_confidence_score")
            display = str(conf) if conf else "❌ NULL"
            print(f"{display:<15} | ", end="")
        else:
            conf = agent3.get("email_confidence_score")
            display = str(conf) if conf else "❌ NULL"
            print(f"{display:<15}")

    # Check for email_method in contact root (not agent3)
    for i, j in enumerate(jsons):
        contact = j["data"]["contacts"][0] if j["data"]["contacts"] else {}
        method = contact.get("email_method")

        if i == 0:
            display = method if method else "❌ NOT MAPPED"
            print(f"{'  email_method':<35} | {display:<15} | ", end="")
        elif i == 1:
            display = method if method else "❌ NOT MAPPED"
            print(f"{display:<15} | ", end="")
        else:
            display = method if method else "❌ NOT MAPPED"
            print(f"{display:<15}")

    print("\n" + "="*70)


def identify_issues(jsons: List[Dict]) -> None:
    """Identify all field issues across JSONs"""
    print("\n🔍 IDENTIFIED ISSUES")
    print("="*70)

    issues = []

    # Check Agent 3 fields
    for j in jsons:
        for contact in j["data"]["contacts"]:
            agent3 = contact.get("agent3", {})

            # Issue 1: email_confidence_score always null
            if agent3.get("email") and agent3.get("email_confidence_score") is None:
                issues.append({
                    "agent": "Agent 3",
                    "field": "email_confidence_score",
                    "issue": "Always NULL even when email found",
                    "cause": "Agent 3 returns 'email_confidence' but Agent 8 looks for 'email_confidence_score'",
                    "fix": "Map contact['email_confidence'] → agent3['email_confidence_score']"
                })
                break
        if issues:
            break

    # Issue 2: email_method not mapped
    issues.append({
        "agent": "Agent 3",
        "field": "email_method",
        "issue": "Not included in agent3 output object",
        "cause": "Agent 3 returns 'email_method' at contact root, not in agent3 sub-object",
        "fix": "Map contact['email_method'] → agent3['email_method']"
    })

    # Issue 3: JSON parsing warnings
    issues.append({
        "agent": "Agent 6, 6.5",
        "field": "N/A",
        "issue": "⚠️ No valid JSON found in response (but data still extracted)",
        "cause": "extract_json_from_text() doesn't find JSON, but fallback parsing works",
        "fix": "Improve JSON extraction or update warning threshold"
    })

    # Print issues
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. [{issue['agent']}] {issue['field']}")
        print(f"   Issue: {issue['issue']}")
        print(f"   Cause: {issue['cause']}")
        print(f"   Fix: {issue['fix']}")


def main():
    print("🔍 JSON Output Comparison")
    print("="*70)

    jsons = load_json_files()

    print(f"\nLoaded {len(jsons)} JSON files:")
    for j in jsons:
        course_name = j["data"]["course_name"]
        cost = j["data"]["summary"]["total_cost_usd"]
        contacts = j["data"]["summary"]["contacts_enriched"]
        segment = j["data"].get("agent6", {}).get("segmentation", {}).get("primary_target", "unknown")

        print(f"  • {course_name:<30} | ${cost:.4f} | {contacts} contacts | {segment}")

    # Detailed field analysis
    analyze_agent3_fields(jsons)
    analyze_agent65_fields(jsons)
    create_field_comparison_table(jsons)
    identify_issues(jsons)

    print("\n" + "="*70)
    print("✅ Comparison Complete!")
    print("\nNext: Fix identified issues in Agent 8 field mappings")


if __name__ == "__main__":
    main()
