#!/usr/bin/env python3
"""
Agent 8: JSON Writer
Writes enriched course and contact data to timestamped JSON files

Purpose:
- Output structured data for schema design review
- No database dependencies (design schema after seeing real data)
- Timestamped files for historical tracking
- Clean, readable JSON format

Output Location: results/enrichment_{course_name}_{timestamp}.json
"""

import anyio
import json
from typing import Any, Dict, List
from pathlib import Path
from datetime import datetime
import re


def sanitize_filename(name: str) -> str:
    """Convert course name to safe filename"""
    # Remove special characters, replace spaces with underscores
    safe = re.sub(r'[^\w\s-]', '', name)
    safe = re.sub(r'[-\s]+', '_', safe)
    return safe.lower()


async def write_to_json(
    course_data: Dict[str, Any],
    course_intel: Dict[str, Any],
    water_hazard_data: Dict[str, Any],
    enriched_contacts: List[Dict[str, Any]],
    output_dir: str = None
) -> Dict[str, Any]:
    """
    Write enriched course and contact data to JSON file

    Args:
        course_data: Output from Agent 2 (course name, website, phone, staff)
        course_intel: Output from Agent 6 (segmentation, opportunities) - COURSE LEVEL
        water_hazard_data: Output from Agent 7 (water_hazard_count, confidence)
        enriched_contacts: List of contacts enriched by Agents 3, 5, 6.5
        output_dir: Optional custom output directory

    Returns:
        Dict with: success, file_path, records_written
    """

    try:
        # ====================================================================
        # STEP 1: Prepare output directory
        # ====================================================================
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "results" / "enrichment"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # ====================================================================
        # STEP 2: Extract course info
        # ====================================================================
        course_name = course_data.get("data", {}).get("course_name", "Unknown")
        safe_name = sanitize_filename(course_name)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # ====================================================================
        # STEP 3: Structure output data
        # ====================================================================
        output_data = {
            "course_name": course_name,
            "enrichment_timestamp": datetime.utcnow().isoformat() + "Z",
            "success": True,

            # Agent 1 data (embedded in course_data)
            "agent1": {
                "url": course_data.get("url"),
                "cost_usd": course_data.get("cost"),
                "turns": course_data.get("turns"),
                "success": course_data.get("url") is not None
            },

            # Agent 2 data
            "agent2": {
                "course_name": course_data.get("data", {}).get("course_name"),
                "website": course_data.get("data", {}).get("website"),
                "phone": course_data.get("data", {}).get("phone"),
                "staff_count": len(course_data.get("data", {}).get("staff", [])),
                "staff_raw": course_data.get("data", {}).get("staff", []),
                "cost_usd": course_data.get("cost"),
                "turns": course_data.get("turns"),
                "success": True
            },

            # Agent 6 data (course-level - run ONCE)
            "agent6": {
                "segmentation": course_intel.get("segmentation"),
                "range_intel": course_intel.get("range_intel"),
                "opportunities": course_intel.get("opportunities"),
                "cost_usd": course_intel.get("cost"),
                "turns": course_intel.get("turns"),
                "success": course_intel.get("segmentation") is not None
            },

            # Agent 7 data
            "agent7": {
                "water_hazard_count": water_hazard_data.get("water_hazard_count"),
                "confidence": water_hazard_data.get("confidence"),
                "details": water_hazard_data.get("details", []),
                "query_approach": water_hazard_data.get("query_approach"),
                "cost_usd": water_hazard_data.get("cost"),
                "success": water_hazard_data.get("found", False)
            },

            # Enriched contacts (Agents 3, 5, 6)
            "contacts": []
        }

        # Add each contact's enrichment data
        for contact in enriched_contacts:
            contact_data = {
                "name": contact.get("name"),
                "title": contact.get("title"),
                "company": contact.get("company"),
                "domain": contact.get("domain"),

                # Agent 3 (Contact Enricher)
                "agent3": {
                    "email": contact.get("email"),
                    "email_confidence": contact.get("email_confidence"),  # FIX: was email_confidence_score
                    "email_method": contact.get("email_method"),  # FIX: now mapped
                    "linkedin_url": contact.get("linkedin_url"),
                    "linkedin_method": contact.get("linkedin_method"),  # Added for completeness
                    "cost_usd": contact.get("_agent3_cost"),
                    "success": contact.get("email") is not None
                },

                # Agent 5 (Phone Finder)
                "agent5": {
                    "phone": contact.get("phone"),
                    "phone_source": contact.get("phone_source"),
                    "method": contact.get("method"),  # Added: perplexity_ai, not_found, etc.
                    "confidence": contact.get("confidence"),  # Added: confidence score
                    "cost_usd": contact.get("_agent5_cost"),
                    "success": contact.get("phone") is not None
                },

                # Agent 6.5 (Contact Background)
                "agent65": {
                    "tenure_years": contact.get("background", {}).get("tenure_years"),
                    "tenure_confidence": contact.get("background", {}).get("tenure_confidence"),
                    "previous_clubs": contact.get("background", {}).get("previous_clubs", []),
                    "industry_experience_years": contact.get("background", {}).get("industry_experience_years"),
                    "responsibilities": contact.get("background", {}).get("responsibilities", []),
                    "career_notes": contact.get("background", {}).get("career_notes"),
                    "cost_usd": contact.get("_agent65_cost"),
                    "turns": contact.get("_agent65_turns"),
                    "success": contact.get("background") is not None
                }
            }

            output_data["contacts"].append(contact_data)

        # ====================================================================
        # STEP 4: Calculate summary metrics
        # ====================================================================
        agent_costs = {
            "agent1": course_data.get("cost", 0) or 0,
            "agent2": course_data.get("cost", 0) or 0,
            "agent6": course_intel.get("cost", 0) or 0,  # Course-level (run once)
            "agent7": water_hazard_data.get("cost", 0) or 0,
            "agent3": sum(c.get("_agent3_cost", 0) or 0 for c in enriched_contacts),
            "agent5": sum(c.get("_agent5_cost", 0) or 0 for c in enriched_contacts),
            "agent65": sum(c.get("_agent65_cost", 0) or 0 for c in enriched_contacts),  # Contact-level
            "agent8": 0  # JSON writing is free
        }

        output_data["summary"] = {
            "total_cost_usd": round(sum(agent_costs.values()), 4),
            "contacts_enriched": len(enriched_contacts),
            "success": True,
            "agent_costs": agent_costs
        }

        # ====================================================================
        # STEP 5: Write to file
        # ====================================================================
        filename = f"enrichment_{safe_name}_{timestamp}.json"
        file_path = output_dir / filename

        with open(file_path, "w") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"   ✅ JSON written: {file_path}")

        return {
            "success": True,
            "file_path": str(file_path),
            "records_written": 1 + len(enriched_contacts),  # 1 course + N contacts
            "error": None
        }

    except Exception as e:
        print(f"   ❌ Error writing JSON: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "file_path": None,
            "records_written": 0,
            "error": str(e)
        }


async def main():
    """Demo: Write test data to JSON"""
    print("💾 Agent 8: JSON Writer")
    print("="*70)

    # Test data (would come from orchestrator in production)
    test_course_data = {
        "url": "https://vsga.org/courselisting/11950",
        "data": {
            "course_name": "Richmond Country Club",
            "website": "https://www.richmondcountryclubva.com/",
            "phone": "804-359-9141",
            "staff": [
                {"name": "Stacy Foster", "title": "General Manager"},
                {"name": "John Doe", "title": "Golf Course Superintendent"}
            ]
        },
        "cost": 0.013,
        "turns": 2
    }

    test_course_intel = {
        "segmentation": {
            "primary_target": "high-end",
            "confidence": 8,
            "signals": ["Private club", "Premium positioning"]
        },
        "range_intel": {
            "has_range": True,
            "volume_signals": ["Large facility"]
        },
        "opportunities": {
            "range_ball_buy": 8,
            "range_ball_sell": 2,
            "range_ball_lease": 9
        },
        "cost": 0.010,
        "turns": 2
    }

    test_water_hazard_data = {
        "water_hazard_count": 5,
        "confidence": "high",
        "details": ["Found via Perplexity search"],
        "query_approach": "direct",
        "cost": 0.003,
        "found": True
    }

    test_enriched_contacts = [
        {
            "name": "Stacy Foster",
            "title": "General Manager",
            "company": "Richmond Country Club",
            "domain": "richmondcountryclubva.com",
            "email": "sfoster@richmondcountryclubva.com",
            "email_confidence_score": 95,
            "linkedin_url": "https://www.linkedin.com/in/stacy-foster-test",
            "phone": "804-592-5861",
            "phone_source": "perplexity_search",
            "_agent3_cost": 0.014,
            "_agent5_cost": 0.010,
            "_agent65_cost": 0.004,
            "_agent65_turns": 2,
            "background": {
                "tenure_years": 5,
                "tenure_confidence": "medium",
                "previous_clubs": ["Oak Hill Country Club"],
                "industry_experience_years": 12,
                "responsibilities": ["Overall club operations", "Staff management", "Member relations"],
                "career_notes": "Promoted from assistant GM after 3 years"
            }
        }
    ]

    print(f"Course: {test_course_data['data']['course_name']}")
    print(f"Segment: {test_course_intel['segmentation']['primary_target']}")
    print(f"Water Hazards: {test_water_hazard_data['water_hazard_count']}")
    print(f"Contacts: {len(test_enriched_contacts)}\n")

    result = await write_to_json(
        test_course_data,
        test_course_intel,
        test_water_hazard_data,
        test_enriched_contacts
    )

    print(f"\n📊 Results:")
    print(f"   Success: {result['success']}")
    if result['success']:
        print(f"   File: {result['file_path']}")
        print(f"   Records: {result['records_written']}")
    else:
        print(f"   Error: {result['error']}")

    print(f"\n{'✅' if result['success'] else '❌'} Complete!")


if __name__ == "__main__":
    anyio.run(main)
