-- Migration 008: Complete Test Tables Schema Alignment
-- Purpose: Add ALL missing columns that Agent 8 writes
-- Date: October 20, 2025
--
-- Background: Test tables were created early and are missing many columns
-- This adds all columns that Agent 8 expects to write

-- ============================================================================
-- test_golf_course_contacts - Add missing columns
-- ============================================================================

ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS contact_source TEXT;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS tenure_start_date TEXT;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS linkedin_confidence TEXT;

COMMENT ON COLUMN test_golf_course_contacts.contact_source IS 'Where contact data came from (agent vs manual)';
COMMENT ON COLUMN test_golf_course_contacts.tenure_start_date IS 'When contact started current position (from Agent 4)';
COMMENT ON COLUMN test_golf_course_contacts.linkedin_confidence IS 'Confidence level for LinkedIn data';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE 'Migration 008 complete: All test table columns aligned with Agent 8 expectations';
END $$;
