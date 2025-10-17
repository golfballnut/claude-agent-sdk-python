#!/usr/bin/env python3
"""
Simplified Agent 2 Test - Focus on Winning Pattern

Based on initial tests, mcp_brightdata performed best.
This test validates it with strict controls.
"""

import anyio
import json
import time
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

# Ground truth
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


def check_accuracy(extracted: dict, ground_truth: dict) -> dict:
    """Case-insensitive accuracy check"""
    results = {
        "website_match": False,
        "phone_match": False,
        "staff_match": False,
        "score": 0,
    }

    if not extracted:
        return results

    # Website
    if extracted.get("website") == ground_truth["website"]:
        results["website_match"] = True
        results["score"] += 33

    # Phone
    if extracted.get("phone") == ground_truth["phone"]:
        results["phone_match"] = True
        results["score"] += 33

    # Staff (case-insensitive)
    extracted_staff = extracted.get("staff", [])
    ground_staff = ground_truth["staff"]

    if len(extracted_staff) == len(ground_staff):
        extracted_set = {
            (s["name"].lower(), s["title"].lower())
            for s in extracted_staff
            if "name" in s and "title" in s
        }
        ground_set = {
            (s["name"].lower(), s["title"].lower())
            for s in ground_staff
        }

        if extracted_set == ground_set:
            results["staff_match"] = True
            results["score"] += 34

    return results


async def test_webfetch_directly():
    """Test using WebFetch tool directly (fallback if BrightData unavailable)"""
    print("Testing: WebFetch (fallback)")
    print("="*70)

    start_time = time.time()

    options = ClaudeAgentOptions(
        allowed_tools=["WebFetch"],
        permission_mode="bypassPermissions",
        max_turns=4,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use WebFetch to get the page content. "
            "Extract: course name, website, phone, and all staff members (name + title). "
            "Return as JSON in this exact format:\n"
            "{\n"
            '  "course_name": "...",\n'
            '  "website": "...",\n'
            '  "phone": "...",\n'
            '  "staff": [{"name": "...", "title": "..."}]\n'
            "}"
        ),
    )

    extracted_data = None
    tools_used = []

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Extract contact data from: {TEST_URL}")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        tools_used.append(block.name)
                    elif isinstance(block, TextBlock):
                        # Try to parse JSON
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

                print(f"\n📊 Results:")
                print(f"   Cost: ${msg.total_cost_usd:.4f}")
                print(f"   Time: {elapsed:.2f}s")
                print(f"   Accuracy: {accuracy['score']}/100")
                print(f"   Turns: {msg.num_turns}")
                print(f"   Tools: {tools_used}")
                print(f"\n   Website: {'✅' if accuracy['website_match'] else '❌'}")
                print(f"   Phone: {'✅' if accuracy['phone_match'] else '❌'}")
                print(f"   Staff: {'✅' if accuracy['staff_match'] else '❌'}")

                if extracted_data:
                    print(f"\n   Extracted Data:")
                    print(f"   {json.dumps(extracted_data, indent=2)}")

                return {
                    "config": "webfetch_haiku_4turns",
                    "cost": msg.total_cost_usd,
                    "time_seconds": round(elapsed, 3),
                    "turns": msg.num_turns,
                    "accuracy_score": accuracy["score"],
                    "under_budget": msg.total_cost_usd < 0.02,
                    "perfect_accuracy": accuracy["score"] == 100,
                    "extracted_data": extracted_data,
                }


async def main():
    print("🎯 Agent 2 Simplified Test")
    print("="*70)
    print(f"URL: {TEST_URL}")
    print(f"Target: < $0.02, 100% accuracy\n")

    result = await test_webfetch_directly()

    print(f"\n{'='*70}")
    print("📈 RESULT")
    print(f"{'='*70}")

    if result["under_budget"] and result["perfect_accuracy"]:
        print(f"✅ SUCCESS!")
        print(f"   Cost: ${result['cost']:.4f} (under budget)")
        print(f"   Accuracy: {result['accuracy_score']}/100 (perfect)")
        print(f"   Time: {result['time_seconds']}s")
    elif result["perfect_accuracy"]:
        print(f"⚠️  Perfect accuracy but over budget")
        print(f"   Cost: ${result['cost']:.4f} (${result['cost'] - 0.02:.4f} over)")
    elif result["under_budget"]:
        print(f"⚠️  Under budget but imperfect accuracy")
        print(f"   Accuracy: {result['accuracy_score']}/100")
    else:
        print(f"❌ Failed both criteria")

    # Save
    with open("../results/agent2_simple_test.json", "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    anyio.run(main)
