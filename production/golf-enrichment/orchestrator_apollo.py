#!/usr/bin/env python3
"""
Orchestrator: Golf Course Enrichment Pipeline (Apollo Version)

STREAMLINED 5-AGENT FLOW:
  Agent 1: Find course URL (Virginia directory) - OPTIONAL (can use DB URL)
  Agent 2-Apollo: Contact discovery + enrichment (ALL-IN-ONE)
  Agent 6: Course segmentation (uses SkyGolf fees)
  Agent 7: Water hazards + SkyGolf data
  Agent 8: Write to Supabase

REPLACES:
- Agent 2: Contact discovery (web scraping)
- Agent 3: Email enrichment (Hunter.io)
- Agent 4: LinkedIn & tenure extraction

NEW BENEFITS:
- Current employees (job change detection)
- Verified emails (90%+ confidence, 57% coverage)
- LinkedIn included (100% coverage)
- Employment history (tenure, previous clubs, education)
- Simpler architecture (5 agents vs 8)

Cost: ~$0.18/course (vs $0.111 current)
Data Quality: 95%+ accuracy (vs 50% outdated)
"""

import anyio
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys
import time

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import agents
from agents.agent1_url_finder import find_url
from agents.agent2_apollo_discovery import discover_contacts
from agents.agent6_course_intelligence import enrich_course as enrich_course_intel
from agents.agent7_water_hazard_counter import count_water_hazards
from agents.agent8_supabase_writer import write_to_supabase


async def update_enrichment_status(
    status: str,
    course_name: str,
    state_code: str = "VA",
    course_id: int | None = None,
    error_message: str | None = None,
    use_test_tables: bool = True
) -> None:
    """Update enrichment_status in database"""
    try:
        from template.utils.env_loader import load_project_env, get_api_key
        from supabase import create_client

        load_project_env()
        supabase_url = get_api_key("SUPABASE_URL")
        supabase_key = get_api_key("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            return

        supabase = create_client(supabase_url, supabase_key)
        course_table = "test_golf_courses" if use_test_tables else "golf_courses"

        update_record = {"enrichment_status": status}

        if status == "error" and error_message:
            update_record["enrichment_error"] = error_message

        if course_id:
            supabase.table(course_table).update(update_record).eq("id", course_id).execute()
        else:
            existing = supabase.table(course_table).select("id").eq("course_name", course_name).maybe_single().execute()
            if existing and existing.data:
                supabase.table(course_table).update(update_record).eq("id", existing.data["id"]).execute()

    except Exception as e:
        print(f"   ⚠️  Failed to update status: {e}")


async def enrich_course(
    course_name: str,
    state_code: str = "VA",
    course_id: int | None = None,
    use_test_tables: bool = True,
    domain: str = ""  # For NC courses, pass domain directly
) -> Dict[str, Any]:
    """
    Fully enrich a golf course using Apollo.io workflow

    Args:
        course_name: Name of golf course
        state_code: State code (default: "VA")
        course_id: Optional course ID
        use_test_tables: Use test tables for safety
        domain: Optional domain (for NC courses to bypass Agent 1)

    Returns:
        Dict with success, agent results, summary
    """

    start_time = time.time()

    print(f"\n{'='*70}")
    print(f"🏌️ ENRICHING: {course_name} (Apollo Workflow)")
    print(f"{'='*70}\n")

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
        "workflow": "apollo",
        "json_file": None,
        "summary": {},
        "error": None,
        "agent_results": {}
    }

    try:
        # ====================================================================
        # AGENT 1: Find Course URL (SKIP for NC - use database domain)
        # ====================================================================
        # Use provided domain if available (for testing or NC courses)
        if not domain:
            domain_lookup = ""
        else:
            domain_lookup = domain

        if state_code == "VA" and not domain:
            print("🔍 [1/5] Agent 1: Finding course URL...")
            agent1_start = time.time()

            url_result = await find_url(course_name, state_code)
            agent1_duration = time.time() - agent1_start

            if url_result and url_result.get("url"):
                url = url_result['url']
                domain_lookup = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
                print(f"   ✅ Found: {url}")
                print(f"   💰 Cost: ${url_result.get('cost', 0):.4f} | ⏱️  {agent1_duration:.1f}s\n")
            else:
                print(f"   ⚠️  URL not found")

            result["agent_results"]["agent1"] = url_result
        elif not domain:  # NC without domain provided
            print(f"🔍 [1/5] Agent 1: SKIPPED (NC course - using provided domain)")
            result["agent_results"]["agent1"] = {"url": None, "cost": 0, "skipped": True}
        else:  # Domain was provided
            print(f"🔍 [1/5] Agent 1: SKIPPED (domain provided: {domain_lookup})\n")
            result["agent_results"]["agent1"] = {"url": None, "cost": 0, "skipped": True}

        # ====================================================================
        # AGENT 2-APOLLO: Contact Discovery & Enrichment (ALL-IN-ONE!)
        # ====================================================================
        print("🔍 [2/5] Agent 2-Apollo: Finding current staff + emails...")
        print(f"   Course: {course_name}")
        print(f"   Domain: {domain_lookup or 'Not provided'}")
        print()
        agent2_start = time.time()

        apollo_result = await discover_contacts(course_name, domain_lookup)

        agent2_duration = time.time() - agent2_start

        contacts = apollo_result.get("contacts", [])
        credits_used = apollo_result.get("credits_used", 0)
        apollo_cost = apollo_result.get("apollo_cost_usd", 0)
        total_cost = apollo_result.get("total_cost_usd", 0)

        if not contacts:
            raise Exception(f"Agent 2-Apollo: No contacts found for '{course_name}'")

        emails_found = len([c for c in contacts if c.get('email')])

        print(f"   ✅ Found {len(contacts)} current employees")
        print(f"   📧 Emails: {emails_found}/{len(contacts)} (all verified 90%+)")
        print(f"   🔗 LinkedIn: {len([c for c in contacts if c.get('linkedin_url')])}/{len(contacts)}")
        print(f"   ⏱️  Tenure data: {len([c for c in contacts if c.get('tenure_years')])}/{len(contacts)}")
        print(f"   💰 Cost: ${total_cost:.4f} | Credits: {credits_used} | ⏱️  {agent2_duration:.1f}s\n")

        for i, contact in enumerate(contacts, 1):
            print(f"      {i}. {contact['name']} ({contact['title']})")
            if contact.get('email'):
                print(f"         Email: {contact['email']} ✅")
            if contact.get('tenure_years'):
                print(f"         Tenure: {contact['tenure_years']} years")

        print()

        result["agent_results"]["agent2_apollo"] = apollo_result

        # ====================================================================
        # AGENT 7: Water Hazards (SkyGolf)
        # ====================================================================
        print("🌊 [3/5] Agent 7: Finding water hazard rating...")
        agent7_start = time.time()

        # Get website from Agent 2-Apollo domain or construct from domain
        website = f"https://{domain}" if domain else None

        water_data = await count_water_hazards(course_name, state_code, website)

        agent7_duration = time.time() - agent7_start

        rating = water_data.get("water_hazard_rating")
        skygolf_content = water_data.get("skygolf_content")

        if rating:
            print(f"   ✅ Rating: {rating.upper()}")
        else:
            print(f"   ⚠️  Not found in SkyGolf database")

        print(f"   💰 Cost: $0.00 (FREE) | ⏱️  {agent7_duration:.1f}s\n")

        result["agent_results"]["agent7"] = water_data

        # ====================================================================
        # AGENT 6: Course Intelligence (Segment + Opportunities)
        # ====================================================================
        print("🎯 [4/5] Agent 6: Analyzing course segment...")
        agent6_start = time.time()

        course_intel = await enrich_course_intel(
            course_name,
            website or "",
            water_hazard_rating=rating,
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
        # AGENT 8: Write to Supabase
        # ====================================================================
        print("💾 [5/5] Agent 8: Writing to database...")
        agent8_start = time.time()

        # Prepare data for Agent 8 (matches expected signature)
        course_data_for_db = {
            "course_name": course_name,
            "website": f"https://{domain_lookup}" if domain_lookup else None,
            "phone": None,  # Course phone from contacts if available
            "data": {
                "course_name": course_name,
                "website": f"https://{domain_lookup}" if domain_lookup else None
            }
        }

        write_result = await write_to_supabase(
            course_data=course_data_for_db,
            course_intel=course_intel,
            water_data=water_data,
            enriched_contacts=contacts,  # Apollo-enriched contacts
            state_code=state_code,
            course_id=course_id,
            total_cost=apollo_cost + url_result.get('cost', 0) if 'url_result' in locals() else apollo_cost,
            contacts_page_url=None,  # Not applicable for Apollo flow
            use_test_tables=use_test_tables
        )

        agent8_duration = time.time() - agent8_start

        if write_result.get("success"):
            print(f"   ✅ Course data written")
            print(f"   ✅ {len(contacts)} contacts written")
            print(f"   💰 Cost: $0.00 | ⏱️  {agent8_duration:.1f}s\n")

            result["agent_results"]["agent8"] = write_result

            # Extract course_id from Agent 8's result for webhook triggering
            if write_result.get("course_id"):
                result["course_id"] = write_result["course_id"]

            result["success"] = True
        else:
            raise Exception(f"Agent 8 write failed: {write_result.get('error')}")

        # ====================================================================
        # SUMMARY
        # ====================================================================
        total_duration = time.time() - start_time

        # Calculate total cost
        agent1_cost = result["agent_results"].get("agent1", {}).get("cost", 0)
        total_agent_cost = (
            agent1_cost +
            total_cost +  # Apollo (includes SDK cost)
            course_intel.get('cost', 0)
        )

        result["summary"] = {
            "total_cost_usd": round(total_agent_cost, 4),
            "total_duration_seconds": round(total_duration, 1),
            "contacts_found": len(contacts),
            "emails_found": emails_found,
            "linkedin_found": len([c for c in contacts if c.get('linkedin_url')]),
            "tenure_found": len([c for c in contacts if c.get('tenure_years')]),
            "apollo_credits_used": credits_used,
            "workflow": "apollo",
            "agents_used": ["agent1", "agent2_apollo", "agent6", "agent7", "agent8"]
        }

        print("="*70)
        print("✅ ENRICHMENT COMPLETE!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"   Contacts: {len(contacts)}")
        print(f"   Emails: {emails_found}/{len(contacts)} (all verified 90%+)")
        print(f"   LinkedIn: {result['summary']['linkedin_found']}/{len(contacts)}")
        print(f"   Tenure: {result['summary']['tenure_found']}/{len(contacts)}")
        print(f"   Apollo credits: {credits_used}")
        print(f"   Total cost: ${total_agent_cost:.4f}")
        print(f"   Duration: {total_duration:.1f}s")
        print()

        # Update status to completed
        await update_enrichment_status(
            status="completed",
            course_name=course_name,
            state_code=state_code,
            course_id=course_id,
            use_test_tables=use_test_tables
        )

        return result

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ENRICHMENT FAILED: {error_msg}\n")

        result["error"] = error_msg

        # Update status to error
        await update_enrichment_status(
            status="error",
            course_name=course_name,
            state_code=state_code,
            course_id=course_id,
            error_message=error_msg,
            use_test_tables=use_test_tables
        )

        return result


async def main():
    """Demo: Test Apollo workflow on sample course"""
    print("\n🚀 Golf Course Enrichment - Apollo Workflow")
    print("="*70)

    # Test course (no course_id to avoid UUID issue in test)
    course = {
        "name": "Ballantyne Country Club",
        "state": "NC",
        "domain": "ballantyneclub.com"  # Hard-code for testing
    }

    result = await enrich_course(
        course_name=course["name"],
        state_code=course["state"],
        course_id=None,  # Skip DB lookups for now
        use_test_tables=True,
        domain=course["domain"]  # Pass domain for NC testing
    )

    if result["success"]:
        print("\n✅ Test successful!")
        print(f"   Cost: ${result['summary']['total_cost_usd']}")
        print(f"   Emails: {result['summary']['emails_found']}")
        print(f"   Credits: {result['summary']['apollo_credits_used']}")
    else:
        print(f"\n❌ Test failed: {result['error']}")


if __name__ == "__main__":
    anyio.run(main)
