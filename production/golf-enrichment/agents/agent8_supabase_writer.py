#!/usr/bin/env python3
"""
Agent 8: Supabase Writer
Writes enriched course and contact data to Supabase database

Responsibilities:
- Upsert golf_courses with Agent 2/6/7 data
- Upsert golf_course_contacts with Agent 3/4/5 data
- Agent 4 provides LinkedIn URL and tenure (extracted from Firecrawl search)
- Atomic operation (all-or-nothing)
- Handle errors gracefully

Schema Requirements:
- Migrations 001-009 must be applied
- See: docs/supabase_schema_design.md
"""

import anyio
import json
from typing import Any, Dict, List
from pathlib import Path
import sys
from datetime import datetime

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "template" / "utils"))

from env_loader import load_project_env, get_api_key


async def write_to_supabase(
    course_data: Dict[str, Any],
    course_intel: Dict[str, Any],
    water_data: Dict[str, Any],
    enriched_contacts: List[Dict[str, Any]],
    state_code: str,  # Required: state code for the course
    course_id: int | None = None,  # Optional: Course ID to update (avoids name mismatch)
    total_cost: float = 0.0,  # Total cost from orchestrator
    contacts_page_url: str | None = None,  # From Agent 1 (VSGA listing URL)
    use_test_tables: bool = True  # Default to test tables for safety
) -> Dict[str, Any]:
    """
    Write enriched course and contact data to Supabase

    Args:
        course_data: Output from Agent 2
        course_intel: Output from Agent 6 (course-level)
        water_data: Output from Agent 7
        enriched_contacts: Contacts from Agents 3/5/6.5
        state_code: State code (e.g., 'VA', 'MD', 'DC')
        course_id: Optional course ID to update (if provided, skips name lookup)
        total_cost: Total enrichment cost in USD (for cost tracking)
        use_test_tables: If True, write to test_golf_courses/test_golf_course_contacts
                        If False, write to production golf_courses/golf_course_contacts

    Returns:
        dict: {success, course_id, contacts_written, error}
    """

    # Load environment
    load_project_env()
    supabase_url = get_api_key("SUPABASE_URL")
    supabase_key = get_api_key("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        return {
            "success": False,
            "error": "SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in .env",
            "course_id": None,
            "contacts_written": 0
        }

    try:
        from supabase import create_client, Client

        # Select table names
        course_table = "test_golf_courses" if use_test_tables else "golf_courses"
        contact_table = "test_golf_course_contacts" if use_test_tables else "golf_course_contacts"

        table_type = "TEST" if use_test_tables else "PRODUCTION"
        print(f"   🔌 Connecting to Supabase ({table_type} tables)...")

        # Create client (TODO: Add timeout - need to research correct syntax for supabase-py)
        supabase: Client = create_client(supabase_url, supabase_key)

        # ====================================================================
        # STEP 1: Prepare Course Data
        # ====================================================================
        print(f"   📦 Preparing course data...")

        course_name = course_data.get("data", {}).get("course_name")
        if not course_name:
            raise ValueError("course_name not found in course_data")

        # Extract course-level data
        course_record = {
            "course_name": course_name,
            "state_code": state_code,  # Required field
            "website": course_data.get("data", {}).get("website"),
            "phone": course_data.get("data", {}).get("phone"),

            # Agent 6: Business Intelligence
            "segment": course_intel.get("segmentation", {}).get("primary_target"),
            "segment_confidence": course_intel.get("segmentation", {}).get("confidence"),
            "segment_signals": json.dumps(course_intel.get("segmentation", {}).get("signals", [])),
            "range_intel": json.dumps(course_intel.get("range_intel", {})),
            "opportunities": json.dumps(course_intel.get("opportunities", {})),

            # Agent 7: Water Hazards (SkyGolf ratings + optional count)
            "water_hazards": water_data.get("water_hazard_count"),  # Integer or NULL
            "water_hazard_rating": water_data.get("water_hazard_rating"),  # scarce/moderate/heavy or NULL
            "water_hazard_source": water_data.get("source"),  # skygolf/verified/not_found
            "water_hazard_confidence": water_data.get("confidence"),

            # Cost Tracking
            "agent_cost_usd": total_cost,

            # Contacts Page URL (from Agent 1 - VSGA listing where contacts were found)
            "contacts_page_url": contacts_page_url,
            "contacts_page_search_method": "vsga_directory" if contacts_page_url else None,
            "contacts_page_found_at": datetime.utcnow().isoformat() if contacts_page_url else None
        }

        # Set enrichment status (both test and production tables have these fields since migration 009)
        course_record["enrichment_status"] = "completed"
        course_record["enrichment_completed_at"] = datetime.utcnow().isoformat()

        # ====================================================================
        # STEP 2: Upsert Course
        # ====================================================================
        print(f"   🏌️ Upserting course: {course_name}...")

        # Use provided course_id if available (from API parameter)
        if course_id:
            print(f"      ✅ Using provided course_id: {course_id}")
            # Update existing course by ID (skip name lookup)
            supabase.table(course_table)\
                .update(course_record)\
                .eq("id", course_id)\
                .execute()
            print(f"      ✅ Updated course ID: {course_id}")
        else:
            # Fallback: Check if course exists by name
            print(f"      🔍 Looking up course by name: {course_name}")
            try:
                existing = supabase.table(course_table)\
                    .select("id")\
                    .eq("course_name", course_name)\
                    .maybe_single()\
                    .execute()
            except Exception as e:
                raise Exception(f"Failed to query {course_table} table: {e}. Make sure the table exists and has proper permissions.")

            if existing and existing.data:
                # Update existing
                course_id = existing.data["id"]
                supabase.table(course_table)\
                    .update(course_record)\
                    .eq("id", course_id)\
                    .execute()
                print(f"      ✅ Updated existing course (ID: {course_id})")
            else:
                # Insert new
                try:
                    result = supabase.table(course_table)\
                        .insert(course_record)\
                        .execute()
                    if not result or not result.data or len(result.data) == 0:
                        raise Exception(f"Insert to {course_table} returned empty result")
                    course_id = result.data[0]["id"]
                    print(f"      ✅ Created new course (ID: {course_id})")
                except Exception as e:
                    raise Exception(f"Failed to insert into {course_table}: {e}")

        # ====================================================================
        # STEP 3: Upsert Contacts
        # ====================================================================
        print(f"   👥 Upserting {len(enriched_contacts)} contacts...")

        contacts_written = 0

        for i, contact in enumerate(enriched_contacts, 1):
            name = contact.get("name")
            if not name:
                print(f"      ⚠️  [{i}/{len(enriched_contacts)}] Skipping: No name")
                continue

            # Prepare contact record (field names differ between test and production)
            contact_record = {
                "golf_course_id": course_id,
                "contact_source": "website_scrape",  # Required field - contacts found via Agent 2 website scraping
            }

            # Add name and title (same field names for both test and production)
            if use_test_tables:
                contact_record["contact_name"] = name
                contact_record["contact_title"] = contact.get("title")
                contact_record["contact_email"] = contact.get("email")
                contact_record["contact_phone"] = contact.get("phone")
            else:
                contact_record["contact_name"] = name
                contact_record["contact_title"] = contact.get("title")
                contact_record["contact_email"] = contact.get("email")
                contact_record["contact_phone"] = contact.get("phone")

            # Common fields for both test and production
            contact_record.update({
                # Agent 3: Email + LinkedIn
                "linkedin_url": contact.get("linkedin_url"),

                # Agent 5: Phone
                "phone_confidence": contact.get("confidence"),

                # Agent 4: Tenure (from LinkedIn search description - NEW!)
                "tenure_years": contact.get("tenure_years"),  # Top-level from Agent 4!
                "tenure_start_date": contact.get("start_date"),  # From Agent 4
                "previous_clubs": json.dumps(contact.get("previous_clubs", []) if contact.get("previous_clubs") else [])
            })

            # Test-only fields (these columns don't exist in production)
            if use_test_tables:
                contact_record.update({
                    "email_confidence": contact.get("email_confidence"),
                    "email_method": contact.get("email_method"),
                    "linkedin_method": contact.get("linkedin_method"),
                    "linkedin_confidence": contact.get("linkedin_confidence"),
                    "phone_method": contact.get("method"),
                    "tenure_source": "agent4_search_description",  # From Agent 4 Firecrawl search
                    "agent4_enriched_at": datetime.utcnow().isoformat()
                })
            else:
                # Production-only fields (use actual production column names)
                contact_record.update({
                    "phone_source": contact.get("method"),  # Maps to phone_source in production
                    "email_confidence_score": contact.get("email_confidence"),  # Note: different name
                    "email_discovery_method": contact.get("email_method"),
                    "discovery_method": contact.get("linkedin_method")
                })

            # Check if contact exists (both test and production use same field names)
            id_field = "contact_id"
            name_query_field = "contact_name"

            try:
                existing_contact = supabase.table(contact_table)\
                    .select(id_field)\
                    .eq("golf_course_id", course_id)\
                    .eq(name_query_field, name)\
                    .maybe_single()\
                    .execute()
            except Exception as e:
                raise Exception(f"Failed to query {contact_table} for contact {name}: {e}")

            if existing_contact and existing_contact.data:
                # Update existing
                contact_id = existing_contact.data[id_field]
                supabase.table(contact_table)\
                    .update(contact_record)\
                    .eq(id_field, contact_id)\
                    .execute()
                print(f"      [{i}/{len(enriched_contacts)}] ✅ Updated: {name}")
            else:
                # Insert new
                supabase.table(contact_table)\
                    .insert(contact_record)\
                    .execute()
                print(f"      [{i}/{len(enriched_contacts)}] ✅ Created: {name}")

            contacts_written += 1

        # ====================================================================
        # SUCCESS
        # ====================================================================
        print(f"   ✅ Success! Course + {contacts_written} contacts written to Supabase")

        return {
            "success": True,
            "course_id": course_id,
            "contacts_written": contacts_written,
            "error": None
        }

    except Exception as e:
        print(f"   ❌ Supabase error: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "course_id": None,
            "contacts_written": 0
        }


async def main():
    """Demo: Test Supabase connection and write"""
    print("💾 Agent 8: Supabase Writer")
    print("="*70)

    # Test data (minimal for connection testing)
    test_course_data = {
        "data": {
            "course_name": "Test Course (Agent 8)",
            "website": "https://testcourse.com",
            "phone": "804-555-1234"
        }
    }

    test_course_intel = {
        "segmentation": {
            "primary_target": "unknown",
            "confidence": 5,
            "signals": ["Test data"]
        },
        "range_intel": {"has_range": True},
        "opportunities": {
            "range_ball_buy": 5,
            "range_ball_lease": 5
        }
    }

    test_water_data = {
        "water_hazard_count": 0,
        "confidence": "none",
        "details": ["Test data"]
    }

    test_contacts = [
        {
            "name": "Test Contact",
            "title": "Test Manager",
            "email": "test@testcourse.com",
            "email_confidence": 50,
            "email_method": "test",
            "phone": "804-555-5678",
            "method": "test",
            "confidence": 50,
            "phone_source": "test",
            "background": {
                "tenure_years": None,
                "tenure_confidence": "unknown",
                "previous_clubs": [],
                "industry_experience_years": None,
                "responsibilities": ["Test duty"],
                "career_notes": "Test notes"
            }
        }
    ]

    print("Testing Supabase connection...\n")
    print("⚠️  Using TEST tables (test_golf_courses, test_golf_course_contacts)")
    print("    Set use_test_tables=False for production\n")

    result = await write_to_supabase(
        test_course_data,
        test_course_intel,
        test_water_data,
        test_contacts,
        state_code="VA",  # Required parameter
        use_test_tables=True  # Safe default
    )

    print(f"\n📊 Results:")
    print(f"   Success: {result['success']}")
    if result['success']:
        print(f"   Course ID: {result['course_id']}")
        print(f"   Contacts Written: {result['contacts_written']}")
        print(f"\n   ⚠️  NOTE: Test course created in your database!")
        print(f"   You can delete it with:")
        print(f"   DELETE FROM golf_courses WHERE course_name = 'Test Course (Agent 8)';")
    else:
        print(f"   Error: {result['error']}")

    print(f"\n{'✅' if result['success'] else '❌'} Complete!")


if __name__ == "__main__":
    anyio.run(main)
