"""
Supabase Writer - Mirrors Agent 8 Database Write Pattern

Purpose: Write validated V2 data to golf_courses and golf_course_contacts tables
Architecture: Agent writes to database (NOT webhook) - matches existing pattern

Key Behavior:
- UPSERT golf_courses record (create or update)
- INSERT golf_course_contacts records (one per contact)
- Contact insert triggers ClickUp sync automatically
- Store full V2 JSON for audit trail

Created: 2025-10-31
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseWriter:
    """
    Database writer for V2 validated data

    Mirrors Agent 8 pattern:
    1. Write to golf_courses (UPSERT)
    2. Write to golf_course_contacts (INSERT per contact)
    3. Contact insert triggers ClickUp sync (automatic)
    """

    def __init__(self, supabase_url: str, supabase_key: str, use_test_tables: bool = False):
        """
        Initialize Supabase client

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            use_test_tables: If True, write to *_test tables (for Docker testing)
        """
        self.client: Client = create_client(supabase_url, supabase_key)
        self.use_test_tables = use_test_tables

        # Table names (production or test)
        self.table_courses = "golf_courses_test" if use_test_tables else "golf_courses"
        self.table_contacts = "golf_course_contacts_test" if use_test_tables else "golf_course_contacts"
        self.table_staging = "llm_research_staging_test" if use_test_tables else "llm_research_staging"

        logger.info(f"SupabaseWriter initialized: {'TEST MODE' if use_test_tables else 'PRODUCTION MODE'}")

    async def write_to_supabase(
        self,
        course_id: Optional[str],
        course_name: str,
        state_code: str,
        tier_data: Dict[str, Any],
        hazard_data: Dict[str, Any],
        volume_data: Dict[str, Any],
        contacts_data: List[Dict[str, Any]],
        intel_data: Dict[str, Any],
        v2_json_full: Dict[str, Any],
        validation_flags: List[str]
    ) -> Dict[str, Any]:
        """
        Write validated V2 data to Supabase tables

        Args:
            course_id: Existing course UUID (None if new course)
            course_name: Golf course name
            state_code: State code (e.g., NC)
            tier_data: Parsed Section 1 data
            hazard_data: Parsed Section 2 data
            volume_data: Parsed Section 3 data
            contacts_data: Parsed Section 4 data (list of contacts)
            intel_data: Parsed Section 5 data
            v2_json_full: Full V2 JSON object (for audit)
            validation_flags: List of quality warning flags

        Returns:
            {
                "course_id": str,
                "contacts_count": int
            }

        Raises:
            Exception: If database write fails
        """
        logger.info(f"💾 Writing to Supabase: {course_name} ({state_code})")

        # ====================================================================
        # STEP 1: Build golf_courses record
        # ====================================================================
        course_record = self._build_course_record(
            course_name=course_name,
            state_code=state_code,
            tier_data=tier_data,
            hazard_data=hazard_data,
            volume_data=volume_data,
            intel_data=intel_data,
            v2_json_full=v2_json_full,
            validation_flags=validation_flags
        )

        # ====================================================================
        # STEP 2: UPSERT golf_courses (create or update)
        # ====================================================================
        if course_id:
            # Update existing course
            logger.info(f"   Updating existing course: {course_id}")
            response = self.client.table(self.table_courses).update(course_record).eq("id", course_id).execute()

            if not response.data:
                raise Exception(f"Failed to update course {course_id}")

            actual_course_id = course_id

        else:
            # Insert new course
            logger.info(f"   Creating new course")
            response = self.client.table(self.table_courses).insert(course_record).execute()

            if not response.data or len(response.data) == 0:
                raise Exception("Failed to create new course")

            actual_course_id = response.data[0]["id"]

        logger.info(f"✅ Course record written: {actual_course_id}")

        # ====================================================================
        # STEP 3: INSERT contacts (one per contact)
        # ====================================================================
        contacts_written = 0

        for contact in contacts_data:
            contact_record = self._build_contact_record(
                golf_course_id=actual_course_id,
                contact=contact
            )

            try:
                response = self.client.table(self.table_contacts).insert(contact_record).execute()

                if response.data:
                    contacts_written += 1
                    logger.info(f"✅ Contact written: {contact['name']} ({contact['title']})")
                else:
                    logger.warning(f"⚠️  Failed to write contact: {contact['name']}")

            except Exception as e:
                logger.error(f"❌ Error writing contact {contact['name']}: {e}")
                # Continue with other contacts

        logger.info(f"✅ Total contacts written: {contacts_written}")

        # ====================================================================
        # STEP 4: Return summary
        # ====================================================================
        return {
            "course_id": actual_course_id,
            "contacts_count": contacts_written
        }

    def _build_course_record(
        self,
        course_name: str,
        state_code: str,
        tier_data: Dict[str, Any],
        hazard_data: Dict[str, Any],
        volume_data: Dict[str, Any],
        intel_data: Dict[str, Any],
        v2_json_full: Dict[str, Any],
        validation_flags: List[str]
    ) -> Dict[str, Any]:
        """
        Build golf_courses record from parsed data

        Returns:
            Dictionary ready for Supabase insert/update
        """
        now = datetime.utcnow().isoformat()

        return {
            # Basic info
            "course_name": course_name,
            "state_code": state_code,

            # V2 metadata
            "v2_research_json": v2_json_full,
            "v2_parsed_at": now,
            "v2_validation_flags": validation_flags,

            # Section 1: Course Tier
            "course_tier": tier_data["tier"],
            "course_tier_confidence": tier_data["confidence"],
            "course_tier_evidence": tier_data["evidence"],

            # Section 2: Water Hazards
            "water_hazards": hazard_data["count"],
            "has_water_hazards": hazard_data["count"] > 0,
            "water_hazards_count": f"{hazard_data['count']} holes" if hazard_data["count"] > 0 else "0 holes",
            "water_hazard_rating": hazard_data["rating"],
            "water_hazard_source": hazard_data["source"],
            "water_hazard_confidence": hazard_data["confidence"],

            # Section 3: Volume Indicator
            "annual_rounds_estimate": volume_data["estimate"],
            "annual_rounds_range": volume_data["range"],
            "annual_rounds_confidence": volume_data["confidence"],

            # Section 5: Intelligence (stored as JSONB)
            "v2_intelligence": intel_data,

            # Status tracking (matches Agent 8 pattern)
            "enrichment_status": "completed",  # V2 validation complete, ready for Phase 2.2 enrichment
            "enrichment_completed_at": now
        }

    def _build_contact_record(
        self,
        golf_course_id: str,
        contact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build golf_course_contacts record from parsed contact

        Args:
            golf_course_id: UUID of golf_courses record
            contact: Parsed contact dictionary

        Returns:
            Dictionary ready for Supabase insert

        Note:
            enriched_at triggers ClickUp sync automatically
        """
        now = datetime.utcnow().isoformat()

        return {
            # Foreign key
            "golf_course_id": golf_course_id,

            # Basic info (match actual column names)
            "contact_name": contact["name"],
            "contact_title": contact["title"],
            "contact_source": "manual",  # V2 LLM research = manual discovery

            # Contact methods (may be None)
            "contact_email": contact.get("email"),
            "linkedin_url": contact.get("linkedin_url"),
            "contact_phone": contact.get("phone"),

            # V2 metadata
            "contact_sources": contact.get("sources", []),
            "employment_verified": contact.get("employment_verified", False),

            # Enrichment flags
            "needs_enrichment": True,  # Will trigger Phase 2.2 Apollo/Hunter enrichment
            "enriched_at": now  # CRITICAL: Triggers ClickUp sync via database trigger
        }

    async def update_staging_status(
        self,
        staging_id: str,
        status: str,
        error: Optional[str]
    ):
        """
        Update llm_research_staging record status after processing

        Args:
            staging_id: UUID of staging record
            status: 'validated' or 'validation_failed'
            error: Error message if status is 'validation_failed'
        """
        update_data = {
            "status": status,
            "processed_at": datetime.utcnow().isoformat()
        }

        if error:
            update_data["validation_error"] = error

        self.client.table(self.table_staging).update(update_data).eq("id", staging_id).execute()
