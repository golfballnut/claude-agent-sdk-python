#!/usr/bin/env python3
"""
Orchestrator: Golf Course Enrichment Pipeline
Coordinates Agents 1-8 to fully enrich a golf course with all contact data

Sequential Flow:
  Agent 1: Find course URL (Virginia directory)
  Agent 2: Extract course data + staff
  Agent 7: Count water hazards (once per course)
  FOR EACH CONTACT:
    Agent 3: Find email + LinkedIn
    Agent 5: Find phone number
    Agent 6: Generate business intelligence (uses water hazard count)
  Agent 8: Write to JSON file

Error Handling: All-or-nothing (if any agent fails, stop + return error)
Progress Tracking: Uses print statements for real-time updates (no TodoWrite here - orchestrator caller tracks)
Output: Structured dict with all agent results + JSON file path
"""

import anyio
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys
import time

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent))

# Import all agents
from agent1_url_finder import find_url
from agent2_data_extractor import extract_contact_data
from agent6_course_intelligence import enrich_course as enrich_course_intel
from agent7_water_hazard_counter import count_water_hazards
from agent3_contact_enricher import enrich_contact
from agent5_phone_finder import find_phone
from agent65_contact_enrichment import enrich_contact_background
from agent8_supabase_writer import write_to_supabase


async def enrich_course(
    course_name: str,
    state_code: str = "VA",
    use_test_tables: bool = True  # Default to test tables for safety
) -> Dict[str, Any]:
    """
    Fully enrich a golf course with all agents

    Args:
        course_name: Name of golf course (e.g., "Richmond Country Club")
        state_code: State code (default: "VA" for Virginia)

    Returns:
        Dict with:
        - success: bool
        - course_name: str
        - json_file: str (path to output JSON)
        - summary: dict (costs, durations, counts)
        - error: str (if failed)
        - agent_results: dict (raw outputs from each agent)
    """

    start_time = time.time()

    print(f"\n{'='*70}")
    print(f"🏌️ ENRICHING: {course_name}")
    print(f"{'='*70}\n")

    result = {
        "success": False,
        "course_name": course_name,
        "state_code": state_code,
        "json_file": None,
        "summary": {},
        "error": None,
        "agent_results": {}
    }

    try:
        # ====================================================================
        # AGENT 1: Find Course URL
        # ====================================================================
        print("🔍 [1/8] Agent 1: Finding course URL...")
        agent1_start = time.time()

        url_result = await find_url(course_name, state_code)

        agent1_duration = time.time() - agent1_start

        if not url_result or not url_result.get("url"):
            raise Exception(f"Agent 1 failed: Course URL not found for '{course_name}'")

        print(f"   ✅ Found: {url_result['url']}")
        print(f"   💰 Cost: ${url_result.get('cost', 0):.4f} | ⏱️  {agent1_duration:.1f}s\n")

        result["agent_results"]["agent1"] = url_result

        # ====================================================================
        # AGENT 2: Extract Course Data
        # ====================================================================
        print("📄 [2/8] Agent 2: Extracting course data...")
        agent2_start = time.time()

        course_data = await extract_contact_data(url_result["url"])

        agent2_duration = time.time() - agent2_start

        if not course_data or not course_data.get("data"):
            raise Exception("Agent 2 failed: Could not extract course data")

        staff = course_data["data"].get("staff", [])
        print(f"   ✅ Course: {course_data['data'].get('course_name')}")
        print(f"   📞 Phone: {course_data['data'].get('phone', 'Not found')}")
        print(f"   👥 Staff: {len(staff)} contacts found")
        print(f"   💰 Cost: ${course_data.get('cost', 0):.4f} | ⏱️  {agent2_duration:.1f}s\n")

        result["agent_results"]["agent2"] = course_data

        if not staff or len(staff) == 0:
            raise Exception("Agent 2: No staff contacts found")

        # ====================================================================
        # AGENT 6: Course-Level Business Intelligence (ONCE per course)
        # ====================================================================
        print("🎯 [3/8] Agent 6: Gathering course-level business intel...")
        agent6_start = time.time()

        website = course_data["data"].get("website")

        # Need water hazards first for Agent 6's ball_retrieval scoring
        # Quick inline water hazard count
        print("   🌊 Getting water hazard count for opportunity scoring...")
        water_data = await count_water_hazards(course_name, state_code, website)
        water_count = water_data.get("water_hazard_count", 0)

        course_intel = await enrich_course_intel(
            course_name,
            website or "",
            water_count
        )

        agent6_duration = time.time() - agent6_start

        seg = course_intel.get("segmentation", {})
        segment = seg.get("primary_target", "unknown")
        confidence = seg.get("confidence", 0)

        print(f"   ✅ Segment: {segment.upper()} ({confidence}/10 confidence)")
        print(f"   💰 Cost: ${course_intel.get('cost', 0):.4f} | ⏱️  {agent6_duration:.1f}s\n")

        result["agent_results"]["agent6"] = course_intel

        # ====================================================================
        # AGENT 7: Water Hazards (already counted above)
        # ====================================================================
        print(f"🌊 [4/8] Agent 7: Water hazard count")

        count = water_data.get("water_hazard_count")
        confidence = water_data.get("confidence", "unknown")

        if count:
            print(f"   ✅ Found: {count} water hazards ({confidence} confidence)")
        else:
            print(f"   ⚠️  Not found ({confidence})")

        print(f"   💰 Cost: ${water_data.get('cost', 0):.4f} (included in Agent 6)\n")

        result["agent_results"]["agent7"] = water_data

        # ====================================================================
        # AGENTS 3, 5, 6.5: Enrich Each Contact
        # ====================================================================
        print(f"👥 [5/8] Enriching {len(staff)} contacts (Agents 3, 5, 6.5)...\n")

        enriched_contacts = []
        total_agent3_cost = 0
        total_agent5_cost = 0
        total_agent65_cost = 0

        for i, staff_member in enumerate(staff, 1):
            name = staff_member.get("name", "Unknown")
            title = staff_member.get("title", "Unknown")

            print(f"   Contact {i}/{len(staff)}: {name} ({title})")

            # Prepare contact dict
            contact = {
                "name": name,
                "title": title,
                "company": course_data["data"].get("course_name"),
                "domain": course_data["data"].get("website", "").replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0] if course_data["data"].get("website") else None,
                "state": state_code
            }

            # ----------------------------------------------------------------
            # AGENT 3: Email + LinkedIn
            # ----------------------------------------------------------------
            print(f"      📧 Agent 3: Finding email + LinkedIn...")
            agent3_start = time.time()

            try:
                enriched = await enrich_contact(contact)

                agent3_duration = time.time() - agent3_start
                agent3_cost = enriched.get("_agent3_cost", 0)
                total_agent3_cost += agent3_cost

                # Merge enriched data
                contact.update(enriched)

                email = enriched.get("email")
                linkedin = enriched.get("linkedin_url")

                if email:
                    print(f"         ✅ Email: {email}")
                else:
                    print(f"         ⚠️  Email: Not found")

                if linkedin:
                    print(f"         ✅ LinkedIn: Found")
                else:
                    print(f"         ⚠️  LinkedIn: Not found")

                print(f"         💰 ${agent3_cost:.4f} | ⏱️  {agent3_duration:.1f}s")

            except Exception as e:
                print(f"         ❌ Error: {e}")
                contact["_agent3_error"] = str(e)

            # ----------------------------------------------------------------
            # AGENT 5: Phone Number
            # ----------------------------------------------------------------
            print(f"      📱 Agent 5: Finding phone...")
            agent5_start = time.time()

            try:
                phone_result = await find_phone(contact)

                agent5_duration = time.time() - agent5_start
                agent5_cost = phone_result.get("_agent5_cost", 0)
                total_agent5_cost += agent5_cost

                # Merge phone data
                contact.update(phone_result)

                phone = phone_result.get("phone")
                if phone:
                    print(f"         ✅ Phone: {phone}")
                else:
                    print(f"         ⚠️  Phone: Not found")

                print(f"         💰 ${agent5_cost:.4f} | ⏱️  {agent5_duration:.1f}s")

            except Exception as e:
                print(f"         ❌ Error: {e}")
                contact["_agent5_error"] = str(e)

            # ----------------------------------------------------------------
            # AGENT 6.5: Contact Background (tenure, previous clubs)
            # ----------------------------------------------------------------
            print(f"      📋 Agent 6.5: Enriching contact background...")
            agent65_start = time.time()

            try:
                bg_result = await enrich_contact_background(contact)

                agent65_duration = time.time() - agent65_start
                agent65_cost = bg_result.get("_agent65_cost", 0)
                total_agent65_cost += agent65_cost

                # Merge background data
                contact.update(bg_result)

                tenure = bg_result.get("_agent65_tenure")
                prev_clubs = bg_result.get("_agent65_previous_clubs", 0)

                if tenure:
                    print(f"         ✅ Tenure: {tenure} years")
                else:
                    print(f"         ⚠️  Tenure: Unknown")

                if prev_clubs > 0:
                    print(f"         ✅ Previous Clubs: {prev_clubs} found")
                else:
                    print(f"         ⚠️  Previous Clubs: None found")

                print(f"         💰 ${agent65_cost:.4f} | ⏱️  {agent65_duration:.1f}s")

            except Exception as e:
                print(f"         ❌ Error: {e}")
                contact["_agent65_error"] = str(e)

            enriched_contacts.append(contact)
            print()  # Blank line between contacts

        # ====================================================================
        # AGENT 8: Write to Supabase
        # ====================================================================
        print("💾 [6/8] Agent 8: Writing to Supabase...")
        agent8_start = time.time()

        supabase_result = await write_to_supabase(
            course_data,
            course_intel,
            water_data,
            enriched_contacts,
            state_code=state_code,
            use_test_tables=use_test_tables
        )

        agent8_duration = time.time() - agent8_start

        if not supabase_result.get("success"):
            raise Exception(f"Agent 8 failed: {supabase_result.get('error')}")

        print(f"   💰 Cost: $0.0000 | ⏱️  {agent8_duration:.1f}s\n")

        # Store Agent 8 result in agent_results
        result["agent_results"]["agent8"] = supabase_result

        # Also extract key fields to top level for convenience
        result["course_id"] = supabase_result["course_id"]
        result["contacts_written"] = supabase_result["contacts_written"]

        # ====================================================================
        # SUMMARY
        # ====================================================================
        total_duration = time.time() - start_time

        result["summary"] = {
            "total_cost_usd": round(
                course_data.get("cost", 0) +
                course_intel.get("cost", 0) +
                water_data.get("cost", 0) +
                total_agent3_cost +
                total_agent5_cost +
                total_agent65_cost,
                4
            ),
            "total_duration_seconds": round(total_duration, 1),
            "contacts_enriched": len(enriched_contacts),
            "agent_costs": {
                "agent1": course_data.get("cost", 0),
                "agent2": course_data.get("cost", 0),
                "agent6": round(course_intel.get("cost", 0), 4),
                "agent7": water_data.get("cost", 0),
                "agent3": round(total_agent3_cost, 4),
                "agent5": round(total_agent5_cost, 4),
                "agent65": round(total_agent65_cost, 4),
                "agent8": 0
            }
        }

        result["success"] = True

        print(f"{'='*70}")
        print(f"✅ SUCCESS: {course_name}")
        print(f"{'='*70}")
        print(f"💰 Total Cost: ${result['summary']['total_cost_usd']:.4f}")
        print(f"⏱️  Total Time: {result['summary']['total_duration_seconds']:.1f}s")
        print(f"👥 Contacts: {result['summary']['contacts_enriched']}")
        print(f"💾 Course ID: {result.get('course_id', 'N/A')[:8]}...")
        print(f"💾 Contacts Written: {result.get('contacts_written', 0)}")
        print(f"{'='*70}\n")

        return result

    except Exception as e:
        total_duration = time.time() - start_time

        print(f"\n{'='*70}")
        print(f"❌ FAILED: {course_name}")
        print(f"{'='*70}")
        print(f"Error: {e}")
        print(f"⏱️  Duration: {total_duration:.1f}s")
        print(f"{'='*70}\n")

        result["error"] = str(e)
        result["summary"]["total_duration_seconds"] = round(total_duration, 1)

        return result


async def main():
    """Demo: Enrich single course"""
    print("🎬 Golf Course Enrichment Orchestrator")
    print("="*70)
    print("⚠️  Using TEST tables by default")
    print("    Set use_test_tables=False for production\n")

    test_course = "Richmond Country Club"
    test_state = "VA"

    result = await enrich_course(test_course, test_state, use_test_tables=True)

    print(f"\n📊 Final Result:")
    print(f"   Success: {result['success']}")
    if result["success"]:
        print(f"   Course ID: {result.get('course_id', 'N/A')}")
        print(f"   Contacts Written: {result.get('contacts_written', 0)}")
        print(f"   Total Cost: ${result['summary']['total_cost_usd']:.4f}")
        print(f"   Total Time: {result['summary']['total_duration_seconds']:.1f}s")
    else:
        print(f"   Error: {result['error']}")

    print(f"\n✅ Demo Complete!")


if __name__ == "__main__":
    anyio.run(main)
