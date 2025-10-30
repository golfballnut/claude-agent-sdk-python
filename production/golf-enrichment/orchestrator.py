#!/usr/bin/env python3
"""
Orchestrator: Golf Course Enrichment Pipeline
Coordinates Agents 1-8 to fully enrich a golf course with all contact data

Sequential Flow:
  Agent 1: Find course URL (Virginia directory)
  Agent 2: Extract course data + staff
  Agent 7: Count water hazards + get SkyGolf data
  Agent 6: Course segmentation (uses SkyGolf fees)
  FOR EACH CONTACT:
    Agent 3: Find email
    Agent 4: Find LinkedIn + Tenure (from Firecrawl search descriptions)
    Agent 5: Find phone number
  Agent 8: Write to Supabase

Architecture Notes:
- Agent 4 extracts tenure from Firecrawl search descriptions (no separate scraping)
- Agent 4 ALWAYS runs (LinkedIn specialist, not conditional)
- Total agents: 8 (Agent 6.5 eliminated - tenure consolidated into Agent 4)

Error Handling: All-or-nothing (if any agent fails, stop + return error)
Progress Tracking: Uses print statements for real-time updates
Output: Structured dict with all agent results + database write confirmation
"""

import anyio
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys
import time

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all agents
from agents.agent1_url_finder import find_url
from agents.agent2_data_extractor import extract_contact_data
from agents.agent6_course_intelligence import enrich_course as enrich_course_intel
from agents.agent7_water_hazard_counter import count_water_hazards
from agents.agent3_contact_enricher import enrich_contact
from agents.agent4_linkedin_finder import find_linkedin
from agents.agent5_phone_finder import find_phone
from agents.agent8_supabase_writer import write_to_supabase


async def update_enrichment_status(
    status: str,
    course_name: str,
    state_code: str = "VA",
    course_id: int | None = None,
    error_message: str | None = None,
    use_test_tables: bool = True
) -> None:
    """
    Update enrichment_status in database (for tracking workflow progress)

    Args:
        status: New status ('processing', 'completed', 'error')
        course_name: Name of the course
        state_code: State code
        course_id: Optional course ID (if known)
        error_message: Error message (only for 'error' status)
        use_test_tables: Whether to use test tables
    """
    try:
        # Import here to avoid circular dependency
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "template" / "utils"))
        from env_loader import load_project_env, get_api_key

        load_project_env()
        supabase_url = get_api_key("SUPABASE_URL")
        supabase_key = get_api_key("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            print(f"   ⚠️  Cannot update status: Supabase credentials not found")
            return

        from supabase import create_client
        from datetime import datetime

        supabase = create_client(supabase_url, supabase_key)
        course_table = "test_golf_courses" if use_test_tables else "golf_courses"

        # Prepare update record
        update_record = {
            "enrichment_status": status
        }

        if status == "error" and error_message:
            update_record["enrichment_error"] = error_message

        # Find course by ID or name
        if course_id:
            supabase.table(course_table)\
                .update(update_record)\
                .eq("id", course_id)\
                .execute()
        else:
            # Lookup by name
            existing = supabase.table(course_table)\
                .select("id")\
                .eq("course_name", course_name)\
                .maybe_single()\
                .execute()

            if existing and existing.data:
                supabase.table(course_table)\
                    .update(update_record)\
                    .eq("id", existing.data["id"])\
                    .execute()

    except Exception as e:
        print(f"   ⚠️  Failed to update status: {e}")


async def get_contacts_page_url_from_db(
    course_id: int | None,
    use_test_tables: bool
) -> str | None:
    """
    Get contacts_page_url from database if available

    For NC/SC and future states, this URL is pre-populated with PGA facility URLs.
    If found, Agent 1 can be bypassed entirely.

    Args:
        course_id: Course ID to lookup
        use_test_tables: Whether to use test tables

    Returns:
        contacts_page_url from database, or None if not found
    """
    if not course_id:
        return None

    try:
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "template" / "utils"))
        from env_loader import load_project_env, get_api_key
        from supabase import create_client

        load_project_env()
        supabase = create_client(
            get_api_key("SUPABASE_URL"),
            get_api_key("SUPABASE_SERVICE_ROLE_KEY")
        )

        table = "test_golf_courses" if use_test_tables else "golf_courses"
        result = supabase.table(table).select("contacts_page_url").eq("id", course_id).single().execute()

        return result.data.get("contacts_page_url") if result.data else None
    except Exception as e:
        print(f"   ⚠️  Could not fetch contacts_page_url from database: {e}")
        return None


async def enrich_course(
    course_name: str,
    state_code: str = "VA",
    course_id: int | None = None,
    use_test_tables: bool = True  # Default to test tables for safety
) -> Dict[str, Any]:
    """
    Fully enrich a golf course with all agents

    Args:
        course_name: Name of golf course (e.g., "Richmond Country Club")
        state_code: State code (default: "VA" for Virginia)
        course_id: Optional course ID to update (ensures correct course, avoids name mismatch)

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

    # Set status to "processing" at start
    await update_enrichment_status(
        status="processing",
        course_name=course_name,
        state_code=state_code,
        course_id=course_id,
        use_test_tables=use_test_tables
    )

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
        # AGENT 1: Find Course URL (or use pre-populated URL from database)
        # ====================================================================
        print("🔍 [1/8] Agent 1: Finding course URL...")
        agent1_start = time.time()

        # Check if URL already in database (for NC/SC and future states)
        db_url = await get_contacts_page_url_from_db(course_id, use_test_tables)

        if db_url:
            print(f"   ✅ Using URL from database (Agent 1 bypassed)")
            print(f"   📋 URL: {db_url}")
            url_result = {
                "url": db_url,
                "cost": 0.0,
                "turns": 0,
                "source": "database"
            }
        else:
            print(f"   🔍 No URL in database, searching with Agent 1...")
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

        # NEW: Wrap Agent 2 in try/except to allow waterfall fallback on errors
        try:
            course_data = await extract_contact_data(url_result["url"])
            agent2_duration = time.time() - agent2_start

            if not course_data or not course_data.get("data"):
                print(f"   ⚠️  Agent 2: No data returned, triggering fallbacks...")
                # Create minimal course_data to allow waterfall
                course_data = {
                    "data": {
                        "course_name": course_name,
                        "staff": [],
                        "phone": None,
                        "source": "pga_directory_error"
                    },
                    "cost": 0.0
                }
                staff = []
            else:
                staff = course_data["data"].get("staff", [])
                print(f"   ✅ Course: {course_data['data'].get('course_name')}")
                print(f"   📞 Phone: {course_data['data'].get('phone', 'Not found')}")
                print(f"   👥 Staff: {len(staff)} contacts found")
                print(f"   💰 Cost: ${course_data.get('cost', 0):.4f} | ⏱️  {agent2_duration:.1f}s\n")

        except Exception as agent2_error:
            # Agent 2 threw error (API 529/500, parse error, etc.)
            # Create minimal course_data to allow waterfall fallback
            print(f"   ⚠️  Agent 2 error: {agent2_error}")
            print(f"   🔁 Continuing to fallback agents...\n")
            agent2_duration = time.time() - agent2_start

            course_data = {
                "data": {
                    "course_name": course_name,
                    "staff": [],
                    "phone": None,
                    "source": "pga_directory_error"
                },
                "cost": 0.0,
                "error": str(agent2_error)
            }
            staff = []

        result["agent_results"]["agent2"] = course_data

        # ====================================================================
        # CONTACT FALLBACK CASCADE: Ensure we have 2+ contacts
        # ====================================================================
        contact_source = course_data["data"].get("source", "pga_directory")  # Default source

        if staff and len(staff) >= 2:
            print(f"   ✅ Agent 2 met threshold: {len(staff)} contacts found")
            course_data["data"]["contact_source"] = contact_source
        else:
            print(f"   ⚠️  Agent 2 below threshold: {len(staff)} contact(s), triggering fallbacks...")
            fallback_attempts = []

            # FALLBACK 1: LinkedIn Company Page
            print("   🔗 [Fallback 1/2] Agent 2.1: LinkedIn Company Search...")
            fallback_attempts.append("linkedin_company")

            try:
                from agents.agent2_1_linkedin_company import find_linkedin_company_staff

                linkedin_staff = await find_linkedin_company_staff(
                    course_data["data"].get("course_name"),
                    state_code
                )

                if linkedin_staff and len(linkedin_staff) >= 2:
                    print(f"   ✅ Agent 2.1 SUCCESS: {len(linkedin_staff)} contacts from LinkedIn")
                    staff = linkedin_staff
                    course_data["data"]["staff"] = staff
                    course_data["data"]["contact_source"] = "linkedin_company"
                    course_data["data"]["fallback_sources_attempted"] = fallback_attempts
                else:
                    print(f"   ⚠️  Agent 2.1 below threshold: {len(linkedin_staff)} contacts")

                    # FALLBACK 2: Perplexity AI Research
                    print("   🤖 [Fallback 2/2] Agent 2.2: Perplexity AI Research...")
                    fallback_attempts.append("perplexity_research")

                    from agents.agent2_2_perplexity_research import research_course_contacts

                    # Get city (may need to parse from location or other field)
                    city = course_data["data"].get("city", course_name.split()[0])  # Fallback to first word

                    perplexity_staff = await research_course_contacts(
                        course_data["data"].get("course_name"),
                        city,
                        state_code
                    )

                    if perplexity_staff and len(perplexity_staff) >= 1:
                        print(f"   ✅ Agent 2.2 SUCCESS: {len(perplexity_staff)} contacts from Perplexity")
                        staff = perplexity_staff
                        course_data["data"]["staff"] = staff
                        course_data["data"]["contact_source"] = "perplexity_research"
                        course_data["data"]["fallback_sources_attempted"] = fallback_attempts
                    else:
                        # All sources exhausted
                        print("   ❌ All sources exhausted (Agent 2, 2.1, 2.2) - NO CONTACTS FOUND")
                        course_data["data"]["fallback_sources_attempted"] = fallback_attempts
                        raise Exception("No contacts available from any source (PGA, LinkedIn, Perplexity)")

            except ImportError as e:
                print(f"   ⚠️  Fallback agents not available: {e}")
                raise Exception("Agent 2: No staff contacts found and fallbacks unavailable")

        # At this point, we have staff from SOME source (Agent 2, 2.1, or 2.2)
        print(f"   ▶️  Proceeding with {len(staff)} contacts from source: {course_data['data'].get('contact_source')}\n")

        # ====================================================================
        # AGENT 6: Course-Level Business Intelligence (ONCE per course)
        # ====================================================================
        print("🎯 [3/8] Agent 6: Gathering course-level business intel...")
        agent6_start = time.time()

        website = course_data["data"].get("website")

        # Need water hazards first for Agent 6's opportunity scoring
        # Get SkyGolf data (water rating + fees for segmentation)
        print("   🌊 Getting SkyGolf data (water + fees)...")
        water_data = await count_water_hazards(course_name, state_code, website)
        water_rating = water_data.get("water_hazard_rating")  # scarce/moderate/heavy
        skygolf_content = water_data.get("skygolf_content")  # Full page content

        # Agent 6 uses water rating + SkyGolf content for fee-based segmentation
        course_intel = await enrich_course_intel(
            course_name,
            website or "",
            water_hazard_rating=water_rating,
            skygolf_content=skygolf_content
        )

        agent6_duration = time.time() - agent6_start

        seg = course_intel.get("segmentation", {})
        segment = seg.get("primary_target", "unknown")
        confidence = seg.get("confidence", 0)

        print(f"   ✅ Segment: {segment.upper()} ({confidence}/10 confidence)")
        print(f"   💰 Cost: ${course_intel.get('cost', 0):.4f} | ⏱️  {agent6_duration:.1f}s\n")

        result["agent_results"]["agent6"] = course_intel

        # ====================================================================
        # AGENT 7: Water Hazards (already retrieved above via SkyGolf)
        # ====================================================================
        print(f"🌊 [4/8] Agent 7: Water hazard rating (SkyGolf)")

        rating = water_data.get("water_hazard_rating")
        count = water_data.get("water_hazard_count")
        source = water_data.get("source", "unknown")

        if rating:
            print(f"   ✅ Rating: {rating.upper()}")
            if count:
                print(f"   ✅ Specific count: {count} holes")
            print(f"   Source: SkyGolf database")
        else:
            print(f"   ⚠️  Not found in SkyGolf (40% of courses don't have this data)")

        print(f"   💰 Cost: $0.00 (FREE - SkyGolf scraping)\n")

        result["agent_results"]["agent7"] = water_data

        # ====================================================================
        # AGENTS 3, 4, 5: Enrich Each Contact (Agent 4 now includes tenure!)
        # ====================================================================
        print(f"👥 [5/8] Enriching {len(staff)} contacts (Agents 3, 4, 5)...\n")

        enriched_contacts = []
        total_agent3_cost = 0
        total_agent4_cost = 0
        total_agent5_cost = 0
        # Agent 6.5 removed - tenure now from Agent 4!

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
            # AGENT 4: LinkedIn + Tenure (ALWAYS RUNS!)
            # ----------------------------------------------------------------
            # Agent 4 is the LinkedIn specialist - always run for best coverage
            # Agent 3 is good for email, but Hunter.io LinkedIn is unreliable
            print(f"      🔗 Agent 4: Finding LinkedIn + Tenure (specialist)...")
            agent4_start = time.time()

            try:
                linkedin_result = await find_linkedin(
                    contact,
                    course_data["data"].get("course_name"),
                    state_code
                )

                agent4_duration = time.time() - agent4_start
                agent4_cost = linkedin_result.get("_agent4_cost", 0)
                total_agent4_cost += agent4_cost

                # Merge LinkedIn + Tenure data (overwrites Agent 3's LinkedIn if both found)
                contact.update(linkedin_result)

                linkedin = linkedin_result.get("linkedin_url")
                tenure = linkedin_result.get("tenure_years")
                start_date = linkedin_result.get("start_date")

                if linkedin:
                    print(f"         ✅ LinkedIn: {linkedin}")
                    if tenure:
                        print(f"         ✅ Tenure: {tenure} years (since {start_date})")
                    else:
                        print(f"         ⚠️  Tenure: Not in search description")
                    print(f"         Method: {linkedin_result.get('linkedin_method')}")
                else:
                    print(f"         ⚠️  LinkedIn: Not found (tried all methods)")

                print(f"         💰 ${agent4_cost:.4f} | ⏱️  {agent4_duration:.1f}s")

            except Exception as e:
                print(f"         ❌ Error: {e}")
                contact["_agent4_error"] = str(e)

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
            # AGENT 6.5 REMOVED
            # ----------------------------------------------------------------
            # Tenure is now extracted by Agent 4 from Firecrawl search descriptions!
            # No separate scraping needed - faster, cheaper, more reliable

            enriched_contacts.append(contact)
            print()  # Blank line between contacts

        # ====================================================================
        # Calculate Total Cost (BEFORE Agent 8 so we can write it to DB)
        # ====================================================================
        total_cost_usd = round(
            course_data.get("cost", 0) +
            course_intel.get("cost", 0) +
            water_data.get("cost", 0) +
            total_agent3_cost +
            total_agent4_cost +
            total_agent5_cost,
            # Agent 6.5 removed - tenure now in Agent 4!
            4
        )

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
            course_id=course_id,
            total_cost=total_cost_usd,
            contacts_page_url=url_result.get("url"),  # From Agent 1 (VSGA listing)
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
            "total_cost_usd": total_cost_usd,
            "total_duration_seconds": round(total_duration, 1),
            "contacts_enriched": len(enriched_contacts),
            "agent_costs": {
                "agent1": course_data.get("cost", 0),
                "agent2": course_data.get("cost", 0),
                "agent6": round(course_intel.get("cost", 0), 4),
                "agent7": water_data.get("cost", 0),
                "agent3": round(total_agent3_cost, 4),
                "agent4": round(total_agent4_cost, 4),  # Now includes tenure!
                "agent5": round(total_agent5_cost, 4),
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
        # Handle both int and string course_id
        course_id_display = result.get('course_id', 'N/A')
        if isinstance(course_id_display, int):
            print(f"💾 Course ID: {course_id_display}")
        elif isinstance(course_id_display, str):
            print(f"💾 Course ID: {course_id_display[:8]}...")
        else:
            print(f"💾 Course ID: {course_id_display}")
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

        # Set status to "error" with error message
        await update_enrichment_status(
            status="error",
            course_name=course_name,
            state_code=state_code,
            course_id=course_id,
            error_message=str(e),
            use_test_tables=use_test_tables
        )

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
