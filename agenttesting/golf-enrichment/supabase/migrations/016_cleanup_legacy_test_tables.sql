-- Migration 016: Cleanup Legacy Apollo Test Tables
-- Created: 2025-11-01
-- Purpose: Remove legacy test tables from archived Apollo workflow (pre-Oct 30, 2025)
--          These have been replaced by golf_courses_test and golf_course_contacts_test (Migration 015)

-- Context:
-- - test_golf_courses (5 rows): Legacy Apollo testing table with outdated schema (50 cols vs 68 in production)
-- - test_golf_course_contacts (23 rows): Legacy Apollo testing table (54 cols vs 53 in production)
-- - Only referenced in archived code (/archive/teams-2025-10-30/)
-- - Replaced by Migration 015 test tables which match current production schema

-- Risk Assessment: LOW
-- - Only test data (5 courses, 23 contacts)
-- - No production dependencies
-- - Apollo workflow archived on Oct 30, 2025
-- - New test infrastructure (Migration 015) already in use

-- Step 1: Drop legacy test contacts table
-- CASCADE handles any foreign key dependencies
DROP TABLE IF EXISTS test_golf_course_contacts CASCADE;

-- Step 2: Drop legacy test courses table
DROP TABLE IF EXISTS test_golf_courses CASCADE;

-- Verification:
-- After applying this migration, only the following test tables should exist:
-- - golf_courses_test (Migration 015)
-- - golf_course_contacts_test (Migration 015)
-- - llm_research_staging_test (Migration 015)

-- Expected Result:
-- Tables reduced from 22 → 20
-- Legacy Apollo test infrastructure removed
-- Current test infrastructure (Migration 015) remains intact
