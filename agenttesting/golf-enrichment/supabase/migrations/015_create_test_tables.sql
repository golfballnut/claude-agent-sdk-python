-- Migration 015: Create test tables for safe Docker validation
-- Purpose: Isolated test tables to prevent pollution of production data during testing
-- Created: 2025-10-31

-- ============================================================================
-- TEST TABLE: golf_courses_test (clone of golf_courses)
-- ============================================================================

CREATE TABLE IF NOT EXISTS golf_courses_test (LIKE golf_courses INCLUDING ALL);

-- ============================================================================
-- TEST TABLE: golf_course_contacts_test (clone of golf_course_contacts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS golf_course_contacts_test (LIKE golf_course_contacts INCLUDING ALL);

-- ============================================================================
-- TEST TABLE: llm_research_staging_test (clone of llm_research_staging)
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_research_staging_test (LIKE llm_research_staging INCLUDING ALL);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE golf_courses_test IS 'Test table for Docker validation - safe to truncate';
COMMENT ON TABLE golf_course_contacts_test IS 'Test table for Docker validation - safe to truncate';
COMMENT ON TABLE llm_research_staging_test IS 'Test staging table for Docker validation - safe to truncate';

-- ============================================================================
-- HELPER FUNCTION: Clean test tables
-- ============================================================================

CREATE OR REPLACE FUNCTION clean_test_tables()
RETURNS void AS $$
BEGIN
  DELETE FROM golf_course_contacts_test;
  DELETE FROM golf_courses_test;
  DELETE FROM llm_research_staging_test;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION clean_test_tables IS 'Purge all test table data - call after Docker tests complete';
