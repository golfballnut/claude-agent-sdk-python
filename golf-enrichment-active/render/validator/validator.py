"""
V2 Validator Orchestrator

Purpose: Coordinates V2 JSON validation, parsing, and database writes
Architecture: Validates → Parses 5 sections → Writes to Supabase

Validation Strategy:
- CRITICAL validations (hard failures): Missing sections, invalid tier, confidence <0.5
- QUALITY validations (soft warnings): Low confidence, missing contacts, no contact methods

Created: 2025-10-31
"""

import logging
from typing import Dict, Any, List, Optional

# Parsers (will import after creating them)
from parsers import section1_tier, section2_hazards, section3_volume, section4_contacts, section5_intel
from writers.supabase_writer import SupabaseWriter

logger = logging.getLogger(__name__)

class V2Validator:
    """
    Main validator orchestrator for V2 LLM research JSON

    Workflow:
    1. Validate structure (all 5 sections present)
    2. Validate tier data (CRITICAL)
    3. Parse each section
    4. Collect quality warnings
    5. Write to Supabase (golf_courses + golf_course_contacts)
    """

    def __init__(self, supabase_url: str, supabase_key: str, use_test_tables: bool = False):
        """
        Initialize validator with Supabase credentials

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            use_test_tables: If True, write to *_test tables (for Docker testing)
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.use_test_tables = use_test_tables
        self.writer = SupabaseWriter(supabase_url, supabase_key, use_test_tables)

    async def process(
        self,
        staging_id: str,
        course_id: Optional[str],
        course_name: str,
        state_code: str,
        v2_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main processing workflow

        Args:
            staging_id: UUID of staging record
            course_id: UUID of existing course (None if new)
            course_name: Name of golf course
            state_code: State code (e.g., NC)
            v2_json: Full V2 JSON object

        Returns:
            {
                "success": bool,
                "course_id": str,
                "contacts_created": int,
                "validation_flags": List[str],
                "error": Optional[str]
            }
        """
        logger.info(f"🔍 Validating V2 JSON for: {course_name}")

        # ====================================================================
        # STEP 1: CRITICAL Validations (hard failures)
        # ====================================================================
        validation_result = self._validate_structure(v2_json)
        if not validation_result["valid"]:
            logger.error(f"❌ Structure validation failed: {validation_result['error']}")
            return {
                "success": False,
                "error": validation_result["error"]
            }

        logger.info("✅ Structure validation passed")

        # ====================================================================
        # STEP 2: Parse each section
        # ====================================================================
        try:
            logger.info("📋 Parsing Section 1: Course Tier")
            tier_data = section1_tier.parse(v2_json.get("section1", {}))

            logger.info("📋 Parsing Section 2: Water Hazards")
            hazard_data = section2_hazards.parse(v2_json.get("section2", {}))

            logger.info("📋 Parsing Section 3: Volume Indicator")
            volume_data = section3_volume.parse(v2_json.get("section3", {}))

            logger.info("📋 Parsing Section 4: Contacts")
            contacts_data = section4_contacts.parse(v2_json.get("section4", {}))

            logger.info("📋 Parsing Section 5: Intelligence")
            intel_data = section5_intel.parse(v2_json.get("section5", {}))

        except Exception as e:
            logger.exception(f"❌ Parsing error: {e}")
            return {
                "success": False,
                "error": f"Parsing failed: {str(e)}"
            }

        logger.info(f"✅ All sections parsed successfully")
        logger.info(f"   Tier: {tier_data.get('tier')} ({tier_data.get('confidence')} confidence)")
        logger.info(f"   Water hazards: {hazard_data.get('count')} holes")
        logger.info(f"   Volume estimate: {volume_data.get('estimate')} rounds/year")
        logger.info(f"   Contacts found: {len(contacts_data)}")

        # ====================================================================
        # STEP 3: QUALITY Validations (soft warnings)
        # ====================================================================
        validation_flags = self._collect_quality_warnings(
            tier_data, contacts_data, volume_data
        )

        if validation_flags:
            logger.warning(f"⚠️  Quality warnings: {', '.join(validation_flags)}")
        else:
            logger.info("✅ No quality warnings")

        # ====================================================================
        # STEP 4: Write to Supabase (mirrors Agent 8 behavior)
        # ====================================================================
        try:
            logger.info("💾 Writing to Supabase...")
            write_result = await self.writer.write_to_supabase(
                course_id=course_id,
                course_name=course_name,
                state_code=state_code,
                tier_data=tier_data,
                hazard_data=hazard_data,
                volume_data=volume_data,
                contacts_data=contacts_data,
                intel_data=intel_data,
                v2_json_full=v2_json,
                validation_flags=validation_flags
            )

            logger.info(f"✅ Database write successful")
            logger.info(f"   Course ID: {write_result['course_id']}")
            logger.info(f"   Contacts written: {write_result['contacts_count']}")

            # Update staging record status
            logger.info("📝 Updating staging record status...")
            await self.writer.update_staging_status(staging_id, "validated", None)

        except Exception as e:
            logger.exception(f"❌ Database write error: {e}")
            # Update staging with error
            await self.writer.update_staging_status(staging_id, "validation_failed", str(e))
            return {
                "success": False,
                "error": f"Database write failed: {str(e)}"
            }

        # ====================================================================
        # STEP 5: Return success response
        # ====================================================================
        return {
            "success": True,
            "course_id": write_result["course_id"],
            "contacts_created": write_result["contacts_count"],
            "validation_flags": validation_flags
        }

    def _validate_structure(self, v2_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate V2 JSON structure (CRITICAL validations)

        Required:
        - All 5 sections present
        - Tier exists and is valid
        - Tier confidence ≥ 0.5

        Returns:
            {"valid": bool, "error": Optional[str]}
        """
        # Check all 5 sections present
        required_sections = ["section1", "section2", "section3", "section4", "section5"]
        missing_sections = [s for s in required_sections if s not in v2_json]

        if missing_sections:
            return {
                "valid": False,
                "error": f"Missing required sections: {', '.join(missing_sections)}"
            }

        # Validate Section 1: Tier
        section1 = v2_json["section1"]

        if "tier" not in section1:
            return {
                "valid": False,
                "error": "Section 1 missing 'tier' field"
            }

        tier = section1["tier"]
        if tier not in ["Premium", "Mid", "Budget"]:
            return {
                "valid": False,
                "error": f"Invalid tier value: {tier}. Must be Premium, Mid, or Budget"
            }

        # Validate tier confidence
        confidence = section1.get("tier_confidence", 0.0)
        if isinstance(confidence, (int, float)) and confidence < 0.5:
            return {
                "valid": False,
                "error": f"Tier confidence too low: {confidence} (minimum 0.5 required)"
            }

        return {"valid": True}

    def _collect_quality_warnings(
        self,
        tier_data: Dict[str, Any],
        contacts_data: List[Dict[str, Any]],
        volume_data: Dict[str, Any]
    ) -> List[str]:
        """
        Collect quality warnings (soft failures that need manual review)

        Warnings:
        - LOW_TIER_CONFIDENCE: confidence < 0.7
        - NO_CONTACTS_FOUND: zero contacts discovered
        - NO_CONTACT_METHODS: contacts exist but no emails or LinkedIn URLs
        - NO_VOLUME_DATA: volume estimate is None

        Returns:
            List of warning flag strings
        """
        flags = []

        # Check tier confidence
        if tier_data.get("confidence", 1.0) < 0.7:
            flags.append("LOW_TIER_CONFIDENCE")

        # Check contacts
        if len(contacts_data) == 0:
            flags.append("NO_CONTACTS_FOUND")
        else:
            # Check if ANY contact has email or LinkedIn
            emails_found = sum(1 for c in contacts_data if c.get("email"))
            linkedin_found = sum(1 for c in contacts_data if c.get("linkedin_url"))

            if emails_found == 0 and linkedin_found == 0:
                flags.append("NO_CONTACT_METHODS")

        # Check volume data
        if volume_data.get("estimate") is None:
            flags.append("NO_VOLUME_DATA")

        return flags
