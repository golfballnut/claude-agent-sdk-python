#!/usr/bin/env python3
"""
Local Baseline Runner for Golf Enrichment Agents

Runs all 8 agents locally using Claude Code MCP to establish expected baseline.
This is the GROUND TRUTH for what Docker should produce.

Usage:
    python tests/local/run_baseline.py 93 "Westlake Golf and Country Club" VA
    python tests/local/run_baseline.py 98 "Course Name" VA

Output:
    - Saves baseline to tests/baselines/course_{id}_baseline.json
    - Displays expected results
    - Provides Docker test command for comparison
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import anyio

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all agents
from agents.agent1_url_finder import find_url
from agents.agent2_data_extractor import extract_contact_data
from agents.agent3_contact_enricher import enrich_contact
from agents.agent4_linkedin_finder import find_linkedin
from agents.agent5_phone_finder import find_phone
from agents.agent6_course_intelligence import enrich_course as enrich_course_intel
from agents.agent7_water_hazard_counter import count_water_hazards


async def run_local_baseline(course_id: int, course_name: str, state_code: str = "VA"):
    """
    Run ALL agents locally to establish expected baseline

    This is what Docker SHOULD produce.

    Args:
        course_id: Database course ID
        course_name: Exact course name from database
        state_code: State code (default: VA)

    Returns:
        Baseline results dict
    """

    start_time = time.time()

    baseline = {
        "test_type": "local_baseline",
        "course_id": course_id,
        "course_name": course_name,
        "state_code": state_code,
        "timestamp": datetime.utcnow().isoformat(),
        "agent_results": {},
        "enriched_contacts": [],
        "summary": {}
    }

    print("\n" + "="*70)
    print(f"🧪 LOCAL BASELINE TEST - Course {course_id}")
    print("="*70)
    print(f"Course: {course_name}")
    print(f"State: {state_code}")
    print("Purpose: Establish expected results for Docker comparison")
    print("="*70 + "\n")

    try:
        # ================================================================
        # AGENT 1: URL Finder
        # ================================================================
        print("🔍 [1/8] Agent 1 (Local): Finding course URL...")
        agent1_start = time.time()

        agent1_result = await find_url(course_name, state_code)
        agent1_duration = time.time() - agent1_start

        if not agent1_result or not agent1_result.get("url"):
            raise Exception("Agent 1 failed: Course URL not found")

        baseline["agent_results"]["agent1"] = agent1_result

        print(f"   ✅ URL: {agent1_result.get('url')}")
        print(f"   💰 Cost: ${agent1_result.get('cost', 0):.4f} | ⏱️  {agent1_duration:.1f}s\n")

        # ================================================================
        # AGENT 2: Data Extractor
        # ================================================================
        print("📄 [2/8] Agent 2 (Local): Extracting course data...")
        agent2_start = time.time()

        agent2_result = await extract_contact_data(agent1_result["url"])
        agent2_duration = time.time() - agent2_start

        baseline["agent_results"]["agent2"] = agent2_result

        staff = agent2_result.get("data", {}).get("staff", [])
        print(f"   ✅ Course: {agent2_result['data'].get('course_name')}")
        print(f"   📞 Phone: {agent2_result['data'].get('phone', 'Not found')}")
        print(f"   👥 Staff: {len(staff)} contacts found")
        print(f"   💰 Cost: ${agent2_result.get('cost', 0):.4f} | ⏱️  {agent2_duration:.1f}s\n")

        if not staff:
            raise Exception("Agent 2: No staff contacts found")

        # ================================================================
        # AGENT 7: Water Hazards (SkyGolf Database) - RUN FIRST!
        # ================================================================
        print("💧 [3/8] Agent 7 (Local): Finding water hazard rating...")
        agent7_start = time.time()

        website = agent2_result["data"].get("website")
        agent7_result = await count_water_hazards(
            course_name,
            state_code,
            website
        )
        agent7_duration = time.time() - agent7_start

        baseline["agent_results"]["agent7"] = agent7_result

        rating = agent7_result.get('water_hazard_rating')
        count = agent7_result.get('water_hazard_count')

        if rating:
            print(f"   ✅ Rating: {rating.upper()}")
            if count:
                print(f"   ✅ Specific count: {count} holes")
        else:
            print("   ⚠️  Not found in SkyGolf")

        print(f"   💰 Cost: ${agent7_result.get('cost', 0):.4f} | ⏱️  {agent7_duration:.1f}s\n")

        # ================================================================
        # AGENT 6: Course Intelligence (Uses SkyGolf data from Agent 7)
        # ================================================================
        print("🎯 [4/8] Agent 6 (Local): Fee-based course segmentation...")
        agent6_start = time.time()

        # Pass SkyGolf content from Agent 7 to Agent 6 (reuse data!)
        agent6_result = await enrich_course_intel(
            course_name,
            website or "",
            water_hazard_rating=rating,
            skygolf_content=agent7_result.get('skygolf_content')
        )
        agent6_duration = time.time() - agent6_start

        baseline["agent_results"]["agent6"] = agent6_result

        segment = agent6_result.get("segmentation", {}).get("primary_target")
        confidence = agent6_result.get("segmentation", {}).get("confidence")
        weekend_fee = agent6_result.get("segmentation", {}).get("weekend_fee")

        print(f"   ✅ Segment: {segment.upper()} (confidence: {confidence}/10)")
        if weekend_fee:
            print(f"   💵 Weekend fee: ${weekend_fee}")
        print(f"   💰 Cost: ${agent6_result.get('cost', 0):.4f} | ⏱️  {agent6_duration:.1f}s\n")

        # ================================================================
        # CONTACT ENRICHMENT: Agents 3, 4, 5
        # ================================================================
        print(f"👥 [5/8] Enriching {len(staff)} contacts (Agents 3, 4, 5)...\n")

        total_agent3_cost = 0
        total_agent4_cost = 0
        total_agent5_cost = 0

        for idx, contact in enumerate(staff[:4], 1):  # Limit to 4 contacts
            print(f"   Contact {idx}/{min(len(staff), 4)}: {contact.get('name')} ({contact.get('title')})")

            # Agent 3: Email + LinkedIn (via Hunter.io)
            print("      📧 Agent 3 (Local): Finding email...")
            try:
                agent3_result = await enrich_contact(contact, website)
                contact.update(agent3_result)
                total_agent3_cost += agent3_result.get("_agent3_cost", 0)
                print(f"         ✅ Email: {contact.get('email', 'Not found')}")
                if contact.get('linkedin_url'):
                    print("         ✅ LinkedIn: Found (via Hunter.io)")
            except Exception as e:
                print(f"         ❌ Error: {e}")

            # Agent 4: LinkedIn (if not found by Agent 3)
            if not contact.get('linkedin_url'):
                print("      🔗 Agent 4 (Local): Finding LinkedIn...")
                try:
                    agent4_result = await find_linkedin(contact, course_name, state_code)
                    contact.update(agent4_result)
                    total_agent4_cost += agent4_result.get("_agent4_cost", 0)

                    if contact.get('linkedin_url'):
                        print(f"         ✅ LinkedIn: {contact.get('linkedin_url')}")
                        if contact.get('tenure_years'):
                            print(f"         ✅ Tenure: {contact.get('tenure_years')} years (since {contact.get('start_date', 'unknown')})")
                        else:
                            print("         ⚠️  Tenure: Not in search description")
                        print(f"         Method: {agent4_result.get('linkedin_method')}")
                    else:
                        print("         ⚠️  LinkedIn: Not found")
                except Exception as e:
                    print(f"         ❌ Error: {e}")

            # Agent 5: Phone
            print("      📱 Agent 5 (Local): Finding phone...")
            try:
                agent5_result = await find_phone(contact, course_name, state_code)
                contact.update(agent5_result)
                total_agent5_cost += agent5_result.get("_agent5_cost", 0)
                print(f"         ✅ Phone: {contact.get('phone', 'Not found')}")
            except Exception as e:
                print(f"         ❌ Error: {e}")

            # Agent 6.5 REMOVED - Tenure now from Agent 4!
            # Agent 4 extracts tenure from Firecrawl search descriptions

            baseline["enriched_contacts"].append(contact)
            print()

        # ================================================================
        # SUMMARY
        # ================================================================
        total_duration = time.time() - start_time

        total_cost = round(
            agent1_result.get("cost", 0) +
            agent2_result.get("cost", 0) +
            agent6_result.get("cost", 0) +
            agent7_result.get("cost", 0) +
            total_agent3_cost +
            total_agent4_cost +
            total_agent5_cost,
            4
        )

        baseline["summary"] = {
            "total_cost_usd": total_cost,
            "total_duration_seconds": round(total_duration, 1),
            "contacts_enriched": len(baseline["enriched_contacts"]),
            "agent_costs": {
                "agent1": agent1_result.get("cost", 0),
                "agent2": agent2_result.get("cost", 0),
                "agent6": agent6_result.get("cost", 0),
                "agent7": agent7_result.get("cost", 0),
                "agent3": round(total_agent3_cost, 4),
                "agent4": round(total_agent4_cost, 4),
                "agent5": round(total_agent5_cost, 4)
            }
        }

        # Save baseline
        baseline_dir = Path(__file__).parent.parent / "baselines"
        baseline_dir.mkdir(exist_ok=True)

        baseline_file = baseline_dir / f"course_{course_id}_baseline.json"
        with open(baseline_file, "w") as f:
            json.dump(baseline, f, indent=2)

        print("="*70)
        print("✅ LOCAL BASELINE COMPLETE")
        print("="*70)
        print(f"💰 Expected Cost: ${total_cost}")
        print(f"⏱️  Total Time: {total_duration:.1f}s")
        print(f"👥 Expected Contacts: {len(baseline['enriched_contacts'])}")
        print(f"🔗 VSGA URL: {agent1_result.get('url')}")
        print(f"📁 Saved: {baseline_file}")
        print("="*70)

        print("\n🐳 DOCKER TEST COMMAND:")
        print("curl -X POST http://localhost:8000/enrich-course \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{")
        print(f"    \"course_name\": \"{course_name}\",")
        print(f"    \"state_code\": \"{state_code}\",")
        print(f"    \"course_id\": {course_id},")
        print("    \"use_test_tables\": false")
        print("  }' \\")
        print(f"  -o /tmp/course{course_id}-docker.json\n")

        print("📊 COMPARISON COMMAND:")
        print(f"python tests/local/compare_to_docker.py {course_id}\n")

        return baseline

    except Exception as e:
        print(f"\n{'='*70}")
        print("❌ LOCAL BASELINE FAILED")
        print(f"{'='*70}")
        print(f"Error: {e}")
        print(f"⏱️  Duration: {time.time() - start_time:.1f}s")
        print(f"{'='*70}\n")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tests/local/run_baseline.py <course_id> <course_name> [state_code]")
        print('Example: python tests/local/run_baseline.py 93 "Westlake Golf and Country Club" VA')
        sys.exit(1)

    course_id = int(sys.argv[1])
    course_name = sys.argv[2]
    state_code = sys.argv[3] if len(sys.argv) > 3 else "VA"

    anyio.run(run_local_baseline, course_id, course_name, state_code)
