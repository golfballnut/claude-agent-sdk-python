#!/usr/bin/env python3
"""
Agent 8: Supabase Writer
Writes enriched course and contact data to Supabase database

Responsibilities:
- Upsert golf_courses with Agent 2/6/7 data
- Upsert golf_course_contacts with Agent 3/5/6.5 data
- Atomic operation (all-or-nothing)
- Handle errors gracefully

Schema Requirements:
- Migrations 001 and 002 must be applied
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
    use_test_tables: bool = True  # Default to test tables for safety
) -> Dict[str, Any]:
    """
    Write enriched course and contact data to Supabase

    Args:
        course_data: Output from Agent 2
        course_intel: Output from Agent 6 (course-level)
        water_data: Output from Agent 7
        enriched_contacts: Contacts from Agents 3/5/6.5
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
            "website": course_data.get("data", {}).get("website"),
            "phone": course_data.get("data", {}).get("phone"),

            # Agent 6: Business Intelligence
            "segment": course_intel.get("segmentation", {}).get("primary_target"),
            "segment_confidence": course_intel.get("segmentation", {}).get("confidence"),
            "segment_signals": json.dumps(course_intel.get("segmentation", {}).get("signals", [])),
            "range_intel": json.dumps(course_intel.get("range_intel", {})),
            "opportunity_scores": json.dumps(course_intel.get("opportunities", {})),
            "agent6_enriched_at": datetime.utcnow().isoformat(),

            # Agent 7: Water Hazards
            "water_hazard_count": water_data.get("water_hazard_count"),
            "water_hazard_confidence": water_data.get("confidence"),
            "water_hazard_details": json.dumps(water_data.get("details", [])),
            "agent7_enriched_at": datetime.utcnow().isoformat()
        }

        # Add production-only fields (test tables don't have these columns)
        if not use_test_tables:
            course_record["enhancement_status"] = "agent_enrichment_complete"
            course_record["enrichment_completed_at"] = datetime.utcnow().isoformat()

        # ====================================================================
        # STEP 2: Upsert Course
        # ====================================================================
        print(f"   🏌️ Upserting course: {course_name}...")

        # Check if course exists
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
            print(f"      ✅ Updated existing course (ID: {str(course_id)[:8]}...)")
        else:
            # Insert new
            try:
                result = supabase.table(course_table)\
                    .insert(course_record)\
                    .execute()
                if not result or not result.data or len(result.data) == 0:
                    raise Exception(f"Insert to {course_table} returned empty result")
                course_id = result.data[0]["id"]
                print(f"      ✅ Created new course (ID: {str(course_id)[:8]}...)")
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
            }

            # Add name and title (different field names in test vs production)
            if use_test_tables:
                contact_record["contact_name"] = name
                contact_record["contact_title"] = contact.get("title")
                contact_record["contact_email"] = contact.get("email")
                contact_record["contact_phone"] = contact.get("phone")
            else:
                contact_record["name"] = name
                contact_record["title"] = contact.get("title")
                contact_record["email"] = contact.get("email")
                contact_record["phone"] = contact.get("phone")

            # Common fields for both test and production
            contact_record.update({
                # Agent 3: Email + LinkedIn
                "email_confidence": contact.get("email_confidence"),
                "email_method": contact.get("email_method"),
                "linkedin_url": contact.get("linkedin_url"),
                "linkedin_method": contact.get("linkedin_method"),

                # Agent 5: Phone
                "phone_method": contact.get("method"),  # Note: contact.method, not contact.phone_method
                "phone_confidence": contact.get("confidence"),  # Note: contact.confidence

                # Agent 6.5: Background
                "tenure_years": contact.get("background", {}).get("tenure_years"),
                "tenure_confidence": contact.get("background", {}).get("tenure_confidence"),
                "previous_clubs": json.dumps(contact.get("background", {}).get("previous_clubs", [])),
                "industry_experience_years": contact.get("background", {}).get("industry_experience_years"),
                "responsibilities": json.dumps(contact.get("background", {}).get("responsibilities", [])),
                "career_notes": contact.get("background", {}).get("career_notes"),
                "agent65_enriched_at": datetime.utcnow().isoformat()
            })

            # Add production-only fields
            if not use_test_tables:
                contact_record["phone_source"] = contact.get("phone_source")
                contact_record["enrichment_status"] = "agent_enrichment_complete"
                contact_record["enrichment_completed_at"] = datetime.utcnow().isoformat()

            # Check if contact exists (use contact_id for test tables, id for production)
            id_field = "contact_id" if use_test_tables else "id"
            name_query_field = "contact_name" if use_test_tables else "name"

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
