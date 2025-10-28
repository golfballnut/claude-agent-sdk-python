-- Migration 010: Add PGA Membership Type Field
-- Purpose: Track PGA membership status for contact prioritization
-- Date: October 28, 2025
--
-- Context: PGA directory shows membership badges (PGA MEMBER vs ASSOCIATE)
-- This helps identify senior staff (PGA MEMBER = decision-makers) vs junior staff

-- ============================================================================
-- PART 1: Add pga_membership_type to Production Tables
-- ============================================================================

ALTER TABLE golf_course_contacts
ADD COLUMN IF NOT EXISTS pga_membership_type VARCHAR(50);

COMMENT ON COLUMN golf_course_contacts.pga_membership_type IS
'PGA membership status from directory.pga.org: PGA MEMBER (full professional, typically senior staff/decision-makers) or ASSOCIATE (assistant/junior professional). NULL for non-PGA contacts or when data unavailable.';

-- ============================================================================
-- PART 2: Add pga_membership_type to Test Tables
-- ============================================================================

ALTER TABLE test_golf_course_contacts
ADD COLUMN IF NOT EXISTS pga_membership_type VARCHAR(50);

COMMENT ON COLUMN test_golf_course_contacts.pga_membership_type IS
'PGA membership status from directory.pga.org: PGA MEMBER (full professional, typically senior staff/decision-makers) or ASSOCIATE (assistant/junior professional). NULL for non-PGA contacts or when data unavailable.';

-- ============================================================================
-- PART 3: Verification
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Migration 010: PGA Membership Type';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Added pga_membership_type to:';
  RAISE NOTICE '  - golf_course_contacts';
  RAISE NOTICE '  - test_golf_course_contacts';
  RAISE NOTICE '';
  RAISE NOTICE 'Business Value:';
  RAISE NOTICE '  - Identify decision-makers (PGA MEMBER)';
  RAISE NOTICE '  - Prioritize outreach targets';
  RAISE NOTICE '  - Validate title accuracy';
  RAISE NOTICE '========================================';
END $$;
