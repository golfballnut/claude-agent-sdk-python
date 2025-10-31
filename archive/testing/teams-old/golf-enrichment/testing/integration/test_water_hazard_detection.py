#!/usr/bin/env python3
"""
Test: Water Hazard Detection via Perplexity API

Tests Perplexity's ability to find water hazard counts for golf courses.
Tries two query approaches:
1. Direct water hazard query
2. Scorecard-focused query
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import anyio
import httpx

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "template" / "utils"))
from env_loader import get_api_key, load_project_env


async def query_perplexity(query: str, api_key: str) -> str:
    """Query Perplexity AI and return response text"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": query}]
                }
            )
            data = r.json()

            if data.get("choices"):
                return data["choices"][0]["message"]["content"]
            return ""
    except Exception as e:
        print(f"   ✗ Perplexity query failed: {e}")
        return ""


def extract_water_count(text: str) -> tuple[int | None, str, list[str]]:
    """
    Extract water hazard count from Perplexity response

    Returns: (count, confidence, details)
    """
    if not text:
        return None, "none", []

    # Patterns to look for
    patterns = [
        r'(\d+)\s+water\s+hazards?',
        r'water\s+on\s+(\d+)\s+holes?',
        r'(\d+)\s+holes?\s+(?:feature|have|with)\s+water',
        r'(\d+)\s+ponds?',
        r'(\d+)\s+lakes?',
    ]

    counts = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            counts.extend([int(m) for m in matches])

    if counts:
        # Use the most common count, or max if tie
        from collections import Counter
        count = Counter(counts).most_common(1)[0][0]

        # Determine confidence based on explicit mentions
        if "water hazard" in text.lower() and any(str(count) in text for count in [count]):
            confidence = "high"
        elif any(word in text.lower() for word in ["pond", "lake", "creek", "water"]):
            confidence = "medium"
        else:
            confidence = "low"

        # Extract detail sentences mentioning water
        sentences = text.split('.')
        details = [s.strip() for s in sentences if any(word in s.lower() for word in ["water", "pond", "lake", "creek", "hazard"])][:3]

        return count, confidence, details

    # Check for qualitative mentions without numbers
    if any(word in text.lower() for word in ["water hazard", "pond", "lake"]):
        # Found mentions but no count
        details = [s.strip() for s in text.split('.') if "water" in s.lower()][:2]
        return None, "low", details + ["Water mentioned but no specific count found"]

    return None, "none", ["No water hazard information found"]


async def test_water_hazards():
    """Test water hazard detection on multiple courses"""
    print("🌊 Water Hazard Detection Test")
    print("="*70)

    # Load courses from Agent 2 results
    agent2_file = Path(__file__).parent.parent / "results" / "agent2_test_results.json"

    with open(agent2_file) as f:
        agent2_data = json.load(f)

    # Extract course names
    courses = []
    for course_name, course_result in agent2_data["results"].items():
        courses.append({
            "course_name": course_name,
            "state": "Virginia",  # All test courses are in VA
            "website": course_result["data"].get("website", "")
        })

    print(f"Testing {len(courses)} courses\n")

    # Load Perplexity API key
    load_project_env()
    api_key = get_api_key("PERPLEXITY_API_KEY")

    if not api_key:
        print("❌ PERPLEXITY_API_KEY not set")
        return

    results = []
    successful_finds = 0
    total_cost = 0

    for i, course in enumerate(courses, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(courses)}] {course['course_name']}")
        print("-"*70)

        course_name = course["course_name"]
        state = course["state"]

        # ====================================================================
        # APPROACH 1: Direct Water Hazard Query
        # ====================================================================
        print("   Approach 1: Direct water hazard query...")

        query1 = f"""How many water hazards are on {course_name} golf course in {state}?
Include ponds, lakes, creeks. Which holes have water?
Check scorecard, course guide, hole descriptions, and reviews."""

        response1 = await query_perplexity(query1, api_key)
        count1, conf1, details1 = extract_water_count(response1)

        if count1 is not None:
            print(f"   ✓ Found: {count1} water hazards ({conf1} confidence)")
        else:
            print("   ✗ Not found via direct query")

        # ====================================================================
        # APPROACH 2: Scorecard-Focused Query
        # ====================================================================
        print("   Approach 2: Scorecard-focused query...")

        query2 = f"""Find the scorecard or hole-by-hole guide for {course_name} in {state}.
How many holes have water hazards marked?
What water features (ponds, lakes, creeks) are on the course?"""

        response2 = await query_perplexity(query2, api_key)
        count2, conf2, details2 = extract_water_count(response2)

        if count2 is not None:
            print(f"   ✓ Found: {count2} water hazards ({conf2} confidence)")
        else:
            print("   ✗ Not found via scorecard query")

        # ====================================================================
        # DETERMINE BEST RESULT
        # ====================================================================

        # Prefer higher confidence, then higher count
        if conf1 == "high" or (count1 and not count2):
            final_count = count1
            final_confidence = conf1
            final_details = details1
            approach_used = "direct"
        elif conf2 == "high" or count2:
            final_count = count2
            final_confidence = conf2
            final_details = details2
            approach_used = "scorecard"
        else:
            final_count = count1 or count2
            final_confidence = conf1 if count1 else conf2
            final_details = details1 if count1 else details2
            approach_used = "direct" if count1 else "scorecard"

        found = final_count is not None
        if found:
            successful_finds += 1

        # Estimate cost (2 queries @ ~$0.003 each)
        cost = 0.006
        total_cost += cost

        result = {
            "course_name": course_name,
            "state": state,
            "website": course["website"],
            "water_hazard_count": final_count,
            "confidence": final_confidence,
            "details": final_details,
            "query_approach": approach_used,
            "cost": cost,
            "found": found,
            "approach1_count": count1,
            "approach1_confidence": conf1,
            "approach2_count": count2,
            "approach2_confidence": conf2,
        }

        results.append(result)

        print("\n   📊 Final Result:")
        print(f"      Count: {final_count if final_count else 'Not found'}")
        print(f"      Confidence: {final_confidence}")
        print(f"      Approach: {approach_used}")
        print(f"      Cost: ${cost:.4f}")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}\n")

    success_rate = (successful_finds / len(courses)) * 100
    avg_cost = total_cost / len(courses)

    print(f"Total Courses: {len(courses)}")
    print(f"Successful Finds: {successful_finds}/{len(courses)} ({success_rate:.0f}%)")
    print(f"Avg Cost: ${avg_cost:.4f}")
    print(f"Total Cost: ${total_cost:.4f}")

    # Count distribution
    counts_found = [r["water_hazard_count"] for r in results if r["water_hazard_count"] is not None]
    if counts_found:
        print(f"\nWater Hazard Range: {min(counts_found)}-{max(counts_found)}")
        print(f"Average Hazards (when found): {sum(counts_found) / len(counts_found):.1f}")

    # Confidence distribution
    confidence_dist = {}
    for r in results:
        conf = r["confidence"]
        confidence_dist[conf] = confidence_dist.get(conf, 0) + 1

    print("\nConfidence Distribution:")
    for conf, count in confidence_dist.items():
        print(f"   {conf}: {count}")

    # Data sources mentioned
    print("\nSample Details Found:")
    for r in results[:3]:
        if r["found"]:
            print(f"\n   {r['course_name']}:")
            for detail in r["details"][:2]:
                print(f"      - {detail[:100]}...")

    # Save results
    output = {
        "test_date": datetime.now().isoformat(),
        "test_type": "water_hazard_detection",
        "total_courses": len(courses),
        "successful_finds": successful_finds,
        "success_rate": success_rate,
        "avg_cost": avg_cost,
        "total_cost": total_cost,
        "results": results,
        "summary": {
            "success_rate": f"{success_rate:.0f}%",
            "avg_cost": f"${avg_cost:.4f}",
            "water_hazard_range": f"{min(counts_found)}-{max(counts_found)}" if counts_found else "N/A",
            "avg_hazards_when_found": f"{sum(counts_found) / len(counts_found):.1f}" if counts_found else "N/A",
            "confidence_distribution": confidence_dist
        },
        "notes": [
            "Scorecard data often mentions water hazards",
            "Google Maps URL available in Supabase for visual fallback if needed",
            "foretee.com, worldgolfer.blog, course websites are good sources"
        ]
    }

    output_file = Path(__file__).parent.parent / "results" / "water_hazard_test_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Saved to: {output_file}")

    # Verdict
    if success_rate >= 70:
        print(f"\n{'='*70}")
        print("✅ WATER HAZARD DETECTION VIABLE")
        print(f"{'='*70}")
        print("\nRecommendation: Build Agent 7 with Perplexity approach")
        print(f"Expected performance: {success_rate:.0f}% success, ${avg_cost:.4f} per course")
    elif success_rate >= 40:
        print(f"\n{'='*70}")
        print("⚠️  PARTIAL SUCCESS - CONSIDER HYBRID APPROACH")
        print(f"{'='*70}")
        print("\nRecommendation: Perplexity + visual fallback (Google Maps)")
        print(f"Expected: {success_rate:.0f}% text, 30% visual = ~90% total")
    else:
        print(f"\n{'='*70}")
        print("❌ TEXT APPROACH INSUFFICIENT")
        print(f"{'='*70}")
        print("\nRecommendation: Use visual analysis (Google Maps satellite + Claude Vision)")

    print("\nNote: Google Maps URLs available in Supabase for enhancement")


if __name__ == "__main__":
    anyio.run(test_water_hazards)
