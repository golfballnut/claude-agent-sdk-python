#!/usr/bin/env python3
"""
MCP Hunter.io Validation Test

Quick test to validate Hunter.io MCP server before refactoring Agent 3.

Tests:
1. MCP tool works correctly
2. Response format matches expectations
3. Confidence scores available for 90% filtering
4. Compare to current Agent 3 API approach

Run on 10 NC contacts to get representative sample.
"""

import json
from pathlib import Path


def load_sample_contacts(count=10):
    """Load first N contacts from test data"""
    data_file = Path(__file__).parent / "data" / "nc_contacts_no_hunter.json"
    with open(data_file) as f:
        data = json.load(f)
    return data["contacts"][:count]


def test_hunter_mcp():
    """Test Hunter.io MCP on sample contacts"""

    print("=" * 80)
    print("Hunter.io MCP Validation Test")
    print("=" * 80)
    print()

    contacts = load_sample_contacts(10)

    print(f"Testing {len(contacts)} NC contacts with Hunter.io MCP")
    print()

    results = {
        "tested": 0,
        "found": 0,
        "not_found": 0,
        "errors": 0,
        "contacts": []
    }

    for i, contact in enumerate(contacts, 1):
        print(f"\n[{i}/{len(contacts)}] {contact['name']}")
        print(f"   Title: {contact['title']}")
        print(f"   Company: {contact['company']}")
        print(f"   Domain: {contact['domain']}")

        contact_result = {
            "name": contact["name"],
            "domain": contact["domain"],
            "email": None,
            "confidence": None,
            "status": None
        }

        try:
            # NOTE: This will be executed by Claude Code using the MCP tool
            # The actual MCP call will be made when this script runs
            print(f"   🔍 Calling mcp__hunter-io__Email-Finder...")
            print(f"      full_name: {contact['name']}")
            print(f"      domain: {contact['domain']}")

            # Placeholder - Claude Code will execute the actual MCP call
            # When running this script, Claude will need to use the tool
            contact_result["status"] = "mcp_call_needed"

            results["tested"] += 1
            results["contacts"].append(contact_result)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            contact_result["status"] = "error"
            contact_result["error"] = str(e)
            results["errors"] += 1
            results["contacts"].append(contact_result)

    # Save initial results (will be updated after MCP calls)
    results_file = Path(__file__).parent / "results" / "hunter_mcp_validation.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print("=" * 80)
    print("MANUAL MCP TEST REQUIRED")
    print("=" * 80)
    print()
    print("This script prepared the test data, but MCP calls must be made manually.")
    print()
    print("Next: Use Claude Code to call mcp__hunter-io__Email-Finder for each contact above")
    print()
    print("For each contact, call:")
    print("  mcp__hunter-io__Email-Finder(")
    print("    full_name='[name]',")
    print("    domain='[domain]'")
    print("  )")
    print()
    print("Then document:")
    print("  - Email found/not found")
    print("  - Confidence score (if available)")
    print("  - Response format")
    print("  - Any errors or issues")
    print()


if __name__ == "__main__":
    test_hunter_mcp()
