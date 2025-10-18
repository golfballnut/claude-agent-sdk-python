#!/usr/bin/env python3
"""
Agent 7: Water Hazard Counter
Counts water hazards on golf courses for ball retrieval opportunity scoring

Target Performance:
- Success Rate: 80%+ (text-based queries)
- Cost: ~$0.006/course (2-3 Perplexity API queries)
- Speed: ~8-12s per course
- Future: 90%+ with visual fallback (Google Maps screenshots)

Pattern:
- Direct Perplexity API (proven pattern from Agent 5/6)
- Multiple query approaches for better coverage
- Structured response parsing
- Confidence scoring based on source quality

Business Value:
- 15+ hazards = PREMIUM ball retrieval opportunity ($30K-60K lost balls/year)
- 10-14 hazards = HIGH opportunity
- 5-9 hazards = MODERATE opportunity
- <5 hazards = LOW opportunity (still valuable)
"""

import anyio
import json
import re
from typing import Any, Dict, Optional
from pathlib import Path
import sys

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "template" / "utils"))

from env_loader import load_project_env, get_api_key


async def count_water_hazards(
    course_name: str,
    state: str,
    website: Optional[str] = None
) -> Dict[str, Any]:
    """
    Count water hazards on a golf course using Perplexity web search

    Args:
        course_name: Name of golf course
        state: State where course is located
        website: Optional course website URL for better search context

    Returns:
        Dict with: water_hazard_count, confidence, details, cost
    """

    # Load environment
    load_project_env()
    perplexity_key = get_api_key("PERPLEXITY_API_KEY")

    if not perplexity_key:
        return {
            "water_hazard_count": None,
            "confidence": "none",
            "details": ["PERPLEXITY_API_KEY not set"],
            "query_approach": "error",
            "cost": 0,
            "found": False
        }

    import httpx

    # Track costs (Perplexity sonar model: ~$0.003 per query)
    total_cost = 0.0
    query_cost = 0.003

    # ========================================================================
    # QUERY 1: Direct Water Hazard Count Search
    # ========================================================================
    query1 = f"""How many water hazards are on the {course_name} golf course in {state}?

Please search for:
- Exact number of holes with water hazards
- Number of ponds, lakes, or creeks on the course
- Course scorecards that show water hazard symbols
- Course descriptions mentioning water features

Sources to check:
- foretee.com course guides
- worldgolfer.blog reviews
- Course website scorecards
- Golf course reviews mentioning water

Return the specific number if found, or describe water features in detail."""

    approach1_count = None
    approach1_confidence = "low"
    approach1_details = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": query1}]
                }
            )
            data = r.json()
            total_cost += query_cost

            if data.get("choices"):
                response_text = data["choices"][0]["message"]["content"]
                approach1_details.append(response_text)

                # Parse response for number
                count, confidence = _parse_water_hazard_response(response_text)
                approach1_count = count
                approach1_confidence = confidence

                print(f"   ✓ Query 1: {'Found ' + str(count) if count else 'No count found'}")

    except Exception as e:
        print(f"   ✗ Query 1 failed: {e}")
        approach1_details.append(f"Query 1 error: {str(e)}")

    # ========================================================================
    # QUERY 2: Scorecard and Course Layout Search
    # ========================================================================
    # Only run if Query 1 didn't find a confident count
    if not approach1_count or approach1_confidence == "low":

        website_context = f" Website: {website}" if website else ""

        query2 = f"""Find the course layout and scorecard for {course_name} in {state}.{website_context}

Specifically look for:
- Official scorecard PDF or image showing water hazard symbols
- Hole-by-hole descriptions mentioning water
- Course map showing ponds, lakes, creeks
- How many holes mention "water hazard", "pond", "lake", or "creek"

Sources to prioritize:
- {website if website else "Course official website"}
- foretee.com course pages
- USGA course rating documents
- Golf course architecture reviews

Count how many of the 18 holes have water features."""

        approach2_count = None
        approach2_confidence = "low"
        approach2_details = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {perplexity_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar",
                        "messages": [{"role": "user", "content": query2}]
                    }
                )
                data = r.json()
                total_cost += query_cost

                if data.get("choices"):
                    response_text = data["choices"][0]["message"]["content"]
                    approach2_details.append(response_text)

                    # Parse response
                    count, confidence = _parse_water_hazard_response(response_text)
                    approach2_count = count
                    approach2_confidence = confidence

                    print(f"   ✓ Query 2: {'Found ' + str(count) if count else 'No count found'}")

        except Exception as e:
            print(f"   ✗ Query 2 failed: {e}")
            approach2_details.append(f"Query 2 error: {str(e)}")
    else:
        # Skip Query 2 if Query 1 was confident
        approach2_count = None
        approach2_confidence = "skipped"
        approach2_details = ["Query 2 skipped (Query 1 high confidence)"]
        print(f"   ⊘ Query 2: Skipped (high confidence from Query 1)")

    # ========================================================================
    # RESULT SYNTHESIS
    # ========================================================================

    # Choose best result (prioritize high/medium confidence, then any count)
    if approach1_count and approach1_confidence in ["high", "medium"]:
        final_count = approach1_count
        final_confidence = approach1_confidence
        final_details = approach1_details
        query_approach = "direct"
    elif approach2_count and approach2_confidence in ["high", "medium"]:
        final_count = approach2_count
        final_confidence = approach2_confidence
        final_details = approach2_details
        query_approach = "scorecard"
    elif approach1_count and approach1_confidence == "low":
        # Low confidence from Query 1
        final_count = approach1_count
        final_confidence = "low"
        final_details = approach1_details + ["Low confidence: use with caution"]
        query_approach = "direct"
    elif approach2_count and approach2_confidence == "low":
        # Low confidence from Query 2
        final_count = approach2_count
        final_confidence = "low"
        final_details = approach2_details + ["Low confidence: use with caution"]
        query_approach = "scorecard"
    elif approach1_count or approach2_count:
        # At least one query found something
        final_count = approach1_count or approach2_count
        final_confidence = "low"
        final_details = (approach1_details if approach1_count else []) + (approach2_details if approach2_count else [])
        final_details.append("Low confidence: use with caution")
        query_approach = "direct" if approach1_count else "scorecard"
    else:
        # No count found
        final_count = None
        final_confidence = "none"
        final_details = approach1_details + approach2_details
        final_details.append("Water mentioned but no specific count found")
        query_approach = "failed"

    return {
        "water_hazard_count": final_count,
        "confidence": final_confidence,
        "details": final_details,
        "query_approach": query_approach,
        "cost": round(total_cost, 4),
        "found": final_count is not None,
        # Debug info
        "approach1_count": approach1_count,
        "approach1_confidence": approach1_confidence,
        "approach2_count": approach2_count,
        "approach2_confidence": approach2_confidence,
    }


def _parse_water_hazard_response(response_text: str) -> tuple[Optional[int], str]:
    """
    Parse Perplexity response for water hazard count

    Returns:
        (count, confidence) where confidence is 'high', 'medium', or 'low'
    """

    # Number word to digit mapping
    number_words = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18
    }

    # High confidence patterns (explicit counts with numbers or words)
    high_confidence_patterns = [
        r'water hazards on (\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen) (?:of (?:its )?18 )?holes',
        r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen) holes (?:have|feature|include) water',
        r'water (?:hazards|features) on (\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen) holes',
        r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen) of (?:the )?18 holes have water',
        r'has \*\*water hazards on (\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen) holes',
    ]

    for pattern in high_confidence_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            count_str = match.group(1).lower()
            # Convert word to number if needed
            count = number_words.get(count_str, None)
            if count is None:
                try:
                    count = int(count_str)
                except ValueError:
                    continue
            # Validate reasonable range (1-18 holes)
            if 1 <= count <= 18:
                return count, "high"

    # Medium confidence patterns (derived counts)
    medium_confidence_patterns = [
        r'(\d+) ponds?,? (\d+) lakes?,? and (\d+) creeks?',  # Sum multiple features
        r'(\d+) water (?:hazards|features)',
        r'approximately (\d+) holes with water',
        r'about (\d+) holes (?:have|include) water',
        r'nearly all holes except (\d+)',  # 18 - exception count
    ]

    for pattern in medium_confidence_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            if 'except' in pattern:
                # "all holes except 3" = 18 - 3 = 15
                exceptions = int(match.group(1))
                count = 18 - exceptions
            elif len(match.groups()) > 1:
                # Sum multiple groups (ponds + lakes + creeks)
                count = sum(int(g) for g in match.groups())
            else:
                count = int(match.group(1))

            if 1 <= count <= 18:
                return count, "medium"

    # Low confidence patterns (vague mentions)
    low_confidence_patterns = [
        r'most holes',
        r'nearly all holes',
        r'majority of holes',
        r'several holes',
        r'many holes',
        r'multiple water features',
    ]

    for pattern in low_confidence_patterns:
        if re.search(pattern, response_text, re.IGNORECASE):
            # Estimate based on vague language
            if 'most' in pattern or 'nearly all' in pattern or 'majority' in pattern:
                return 12, "low"  # Assume 2/3 of holes
            elif 'several' in pattern or 'many' in pattern:
                return 7, "low"  # Assume ~1/3 of holes
            elif 'multiple' in pattern:
                return 5, "low"  # Conservative estimate

    # No count found
    return None, "none"


async def count_multiple_courses(courses: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Count water hazards for multiple courses

    Args:
        courses: List of dicts with course_name, state, website (optional)

    Returns:
        List of results with water hazard counts
    """
    results = []

    for i, course in enumerate(courses, 1):
        course_name = course.get("course_name", "Unknown")
        state = course.get("state", "Unknown")
        website = course.get("website")

        print(f"\n[{i}/{len(courses)}] {course_name}")

        try:
            result = await count_water_hazards(course_name, state, website)

            count = result.get("water_hazard_count")
            confidence = result.get("confidence")
            cost = result.get("cost", 0)

            if count:
                print(f"   ✅ Found: {count} water hazards ({confidence} confidence)")
            else:
                print(f"   ⚠️  Not found ({confidence})")

            print(f"   💰 Cost: ${cost:.4f}")

            # Merge with course data
            result_data = course.copy()
            result_data.update(result)
            results.append(result_data)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_result = course.copy()
            error_result.update({
                "water_hazard_count": None,
                "confidence": "error",
                "details": [str(e)],
                "cost": 0,
                "found": False
            })
            results.append(error_result)

    return results


async def main():
    """Demo: Count water hazards for test course"""
    print("🌊 Agent 7: Water Hazard Counter")
    print("="*70)

    test_course = {
        "course_name": "Richmond Country Club",
        "state": "Virginia",
        "website": "https://www.richmondcountryclubva.com/"
    }

    print(f"Course: {test_course['course_name']}")
    print(f"State: {test_course['state']}")
    print(f"Website: {test_course['website']}\n")

    result = await count_water_hazards(
        test_course["course_name"],
        test_course["state"],
        test_course["website"]
    )

    print(f"\n📊 Results:")
    print(f"   Water Hazards: {result.get('water_hazard_count', 'Not found')}")
    print(f"   Confidence: {result.get('confidence', 'unknown').upper()}")
    print(f"   Approach: {result.get('query_approach', 'unknown')}")
    print(f"   Cost: ${result.get('cost', 0):.4f}")

    if result.get('details'):
        print(f"\n📝 Details:")
        for detail in result['details'][:2]:  # Show first 2 details
            # Truncate if too long
            display = detail[:150] + "..." if len(detail) > 150 else detail
            print(f"   - {display}")

    # Opportunity classification
    count = result.get('water_hazard_count')
    if count:
        if count >= 15:
            category = "PREMIUM (15+ hazards)"
            value = "$30K-60K lost balls/year"
        elif count >= 10:
            category = "HIGH (10-14 hazards)"
            value = "$15K-30K lost balls/year"
        elif count >= 5:
            category = "MODERATE (5-9 hazards)"
            value = "$5K-15K lost balls/year"
        else:
            category = "LOW (<5 hazards)"
            value = "Still valuable"

        print(f"\n💎 Opportunity: {category}")
        print(f"   Estimated Value: {value}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
