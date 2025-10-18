#!/usr/bin/env python3
"""
Agent 2 Configuration Testing Framework

Tests different tool/model/config combinations to find optimal pattern.
Goal: < $0.02 per extraction, 100% accuracy
"""

import json
import time
from typing import Any

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

# Ground truth from screenshot (Richmond Country Club)
GROUND_TRUTH = {
    "course_name": "Richmond Country Club",
    "website": "https://www.richmondcountryclubva.com/",
    "phone": "(804) 784-5663",
    "staff": [
        {"name": "Stacy Foster", "title": "GENERAL MANAGER"},
        {"name": "Bill Ranson", "title": "HEAD GOLF PROFESSIONAL"},
        {"name": "Greg McCue", "title": "SUPERINTENDENT"}
    ]
}

TEST_URL = "https://vsga.org/courselisting/11950?hsLang=en"


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

@tool("extract_contacts", "Extract contact info from golf course page", {"url": str})
async def extract_contacts_custom(args: dict[str, Any]) -> dict[str, Any]:
    """Custom tool - Agent 1's winning pattern"""
    import re

    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"https://r.jina.ai/{args['url']}")
        content = r.text

        # Extract contact section (reduce tokens)
        contact_section = ""

        # Find Contact Info section
        contact_match = re.search(r'Contact Info.*?(?=\n\n[A-Z]|\Z)', content, re.DOTALL | re.IGNORECASE)
        if contact_match:
            contact_section += contact_match.group(0) + "\n\n"

        # Find Club Staff section
        staff_match = re.search(r'Club Staff.*?(?=\n\n[A-Z]|\Z)', content, re.DOTALL | re.IGNORECASE)
        if staff_match:
            contact_section += staff_match.group(0)

        if contact_section:
            print(f"   ✓ Extracted contact sections ({len(contact_section)} chars)")
            return {"content": [{"type": "text", "text": contact_section}]}
        else:
            # Fallback: return first 2000 chars
            print("   ⚠ Sections not found, returning first 2000 chars")
            return {"content": [{"type": "text", "text": content[:2000]}]}


# ============================================================================
# TEST CONFIGURATIONS
# ============================================================================

CONFIGS = {
    "custom_tool_haiku_2turns": {
        "tool_type": "custom",
        "model": "claude-haiku-4-5",
        "max_turns": 2,
        "system_prompt": "Extract contact info: website, phone, and all staff (name + title). Return as JSON."
    },
    "custom_tool_haiku_3turns": {
        "tool_type": "custom",
        "model": "claude-haiku-4-5",
        "max_turns": 3,
        "system_prompt": "Extract contact info: website, phone, and all staff (name + title). Return as JSON."
    },
    "custom_tool_sonnet_2turns": {
        "tool_type": "custom",
        "model": "claude-sonnet-4-5",
        "max_turns": 2,
        "system_prompt": "Extract contact info: website, phone, and all staff (name + title). Return as JSON."
    },
    "mcp_jina_haiku_2turns": {
        "tool_type": "mcp_jina",
        "model": "claude-haiku-4-5",
        "max_turns": 2,
        "system_prompt": "Use jina_reader to get page content. Extract: website, phone, staff (name + title). Return as JSON."
    },
    "mcp_brightdata_haiku_2turns": {
        "tool_type": "mcp_brightdata",
        "model": "claude-haiku-4-5",
        "max_turns": 2,
        "system_prompt": "Use scrape_as_markdown to get page. Extract: website, phone, staff (name + title). Return as JSON."
    },
}


# ============================================================================
# ACCURACY CHECKER
# ============================================================================

def check_accuracy(extracted: dict, ground_truth: dict) -> dict[str, Any]:
    """Compare extracted data against ground truth"""
    results = {
        "website_match": False,
        "phone_match": False,
        "staff_count_match": False,
        "staff_names_match": False,
        "staff_titles_match": False,
        "score": 0,
    }

    if not extracted:
        return results

    # Check website
    if extracted.get("website") == ground_truth["website"]:
        results["website_match"] = True
        results["score"] += 20

    # Check phone
    if extracted.get("phone") == ground_truth["phone"]:
        results["phone_match"] = True
        results["score"] += 20

    # Check staff
    extracted_staff = extracted.get("staff", [])
    ground_staff = ground_truth["staff"]

    if len(extracted_staff) == len(ground_staff):
        results["staff_count_match"] = True
        results["score"] += 20

    # Check staff names and titles (case-insensitive)
    extracted_names = {s["name"].lower() for s in extracted_staff if "name" in s}
    ground_names = {s["name"].lower() for s in ground_staff}

    if extracted_names == ground_names:
        results["staff_names_match"] = True
        results["score"] += 20

    extracted_titles = {s["title"].lower() for s in extracted_staff if "title" in s}
    ground_titles = {s["title"].lower() for s in ground_staff}

    if extracted_titles == ground_titles:
        results["staff_titles_match"] = True
        results["score"] += 20

    return results


# ============================================================================
# TEST RUNNER
# ============================================================================

async def test_config(config_name: str, config: dict) -> dict[str, Any]:
    """Test a single configuration"""
    print(f"\n{'='*70}")
    print(f"Testing: {config_name}")
    print(f"  Model: {config['model']}")
    print(f"  Tool: {config['tool_type']}")
    print(f"  Max Turns: {config['max_turns']}")
    print(f"{'='*70}")

    start_time = time.time()

    # Setup options based on tool type
    if config["tool_type"] == "custom":
        server = create_sdk_mcp_server("extract", tools=[extract_contacts_custom])
        options = ClaudeAgentOptions(
            mcp_servers={"extract": server},
            allowed_tools=["mcp__extract__extract_contacts"],
            disallowed_tools=["Task", "TodoWrite", "Grep", "Glob", "WebSearch"],
            permission_mode="bypassPermissions",
            max_turns=config["max_turns"],
            model=config["model"],
            system_prompt=config["system_prompt"],
        )
    elif config["tool_type"] == "mcp_jina":
        options = ClaudeAgentOptions(
            allowed_tools=["mcp__jina__jina_reader"],
            disallowed_tools=["Task", "TodoWrite", "Grep", "Glob", "WebSearch"],
            permission_mode="bypassPermissions",
            max_turns=config["max_turns"],
            model=config["model"],
            system_prompt=config["system_prompt"],
        )
    elif config["tool_type"] == "mcp_brightdata":
        options = ClaudeAgentOptions(
            allowed_tools=["mcp__BrightData__scrape_as_markdown"],
            disallowed_tools=["Task", "TodoWrite", "Grep", "Glob", "WebSearch"],
            permission_mode="bypassPermissions",
            max_turns=config["max_turns"],
            model=config["model"],
            system_prompt=config["system_prompt"],
        )
    else:
        raise ValueError(f"Unknown tool type: {config['tool_type']}")

    extracted_data = None
    tools_used = []

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(f"Extract contact data from: {TEST_URL}")

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                        elif isinstance(block, TextBlock):
                            # Try to parse JSON from response
                            import re
                            json_match = re.search(r'\{.*\}', block.text, re.DOTALL)
                            if json_match:
                                try:
                                    extracted_data = json.loads(json_match.group(0))
                                except json.JSONDecodeError:
                                    pass

                if isinstance(msg, ResultMessage):
                    elapsed = time.time() - start_time
                    accuracy = check_accuracy(extracted_data, GROUND_TRUTH)

                    result = {
                        "config_name": config_name,
                        "cost": msg.total_cost_usd,
                        "time_seconds": round(elapsed, 3),
                        "turns": msg.num_turns,
                        "tools_used": tools_used,
                        "accuracy_score": accuracy["score"],
                        "accuracy_details": accuracy,
                        "extracted_data": extracted_data,
                        "under_budget": msg.total_cost_usd < 0.02 if msg.total_cost_usd else False,
                        "perfect_accuracy": accuracy["score"] == 100,
                    }

                    # Print summary
                    print("\n📊 Results:")
                    print(f"   Cost: ${msg.total_cost_usd:.4f} {'✅' if result['under_budget'] else '❌'}")
                    print(f"   Time: {elapsed:.2f}s")
                    print(f"   Accuracy: {accuracy['score']}/100 {'✅' if result['perfect_accuracy'] else '❌'}")
                    print(f"   Turns: {msg.num_turns}")
                    print(f"   Tools: {tools_used}")

                    return result

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "config_name": config_name,
            "error": str(e),
            "cost": None,
            "accuracy_score": 0,
        }


# ============================================================================
# MAIN
# ============================================================================

async def main():
    print("🧪 Agent 2 Configuration Testing")
    print("="*70)
    print(f"Test URL: {TEST_URL}")
    print("Target: < $0.02, 100% accuracy")
    print("")

    results = []

    # Test each configuration
    for config_name, config in CONFIGS.items():
        result = await test_config(config_name, config)
        results.append(result)

        # Small delay between tests
        await anyio.sleep(1)

    # ========================================================================
    # ANALYSIS
    # ========================================================================

    print(f"\n{'='*70}")
    print("📈 FINAL ANALYSIS")
    print(f"{'='*70}\n")

    # Sort by accuracy then cost
    successful = [r for r in results if r.get("accuracy_score", 0) == 100 and r.get("under_budget", False)]

    if successful:
        winner = min(successful, key=lambda x: x.get("cost", 999))

        print(f"🏆 WINNER: {winner['config_name']}")
        print(f"   Cost: ${winner['cost']:.4f}")
        print(f"   Accuracy: {winner['accuracy_score']}/100")
        print(f"   Time: {winner['time_seconds']}s")
        print(f"   Turns: {winner['turns']}")
    else:
        print("⚠️  No configuration met all criteria (< $0.02, 100% accuracy)")
        print("\nClosest:")
        best = max(results, key=lambda x: (x.get("accuracy_score", 0), -x.get("cost", 999)))
        print(f"   {best['config_name']}")
        print(f"   Cost: ${best.get('cost', 'N/A')}")
        print(f"   Accuracy: {best.get('accuracy_score', 0)}/100")

    # Save results
    output = {
        "test_date": "2025-10-16",
        "test_url": TEST_URL,
        "ground_truth": GROUND_TRUTH,
        "results": results,
        "winner": winner['config_name'] if successful else None,
    }

    output_file = "../results/agent2_config_test_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    anyio.run(main)
