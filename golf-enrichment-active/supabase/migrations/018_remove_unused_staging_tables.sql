-- Migration 018: Remove Unused Staging Tables
-- Created: 2025-11-01
-- Purpose: Remove unused staging tables that served an unclear/abandoned manual validation workflow

-- Context:
-- - golf_courses_staging (978 rows): Staging table with unique validation columns, no code references
-- - golf_course_contacts_staging (0 rows): Empty staging table, no code references
-- - These are DIFFERENT from llm_research_staging (which IS actively used for V2 workflow)
-- - Contains unique columns: validation_status, validation_notes, validated_at, validated_by, pga_facility_url
-- - No references found in active codebase (grep search returned 0 matches)
-- - User confirmed: "Data in step 1 is not needed"

-- Risk Assessment: MEDIUM
-- - 978 courses in staging table (but confirmed not needed by user)
-- - No active code references (thoroughly verified)
-- - Different purpose than llm_research_staging (which remains untouched)
-- - No foreign key dependencies from other tables

-- Important Note:
-- This does NOT affect llm_research_staging which is actively used for V2 JSON processing
-- (created in Migration 013, used by validate-v2-research edge function)

-- Step 1: Drop unused staging contacts table (empty)
DROP TABLE IF EXISTS golf_course_contacts_staging CASCADE;

-- Step 2: Drop unused staging courses table (978 rows)
-- User confirmed this data is not needed (2025-11-01)
DROP TABLE IF EXISTS golf_courses_staging CASCADE;

-- Verification:
-- After applying this migration:
-- - golf_courses_staging removed ✓
-- - golf_course_contacts_staging removed ✓
-- - llm_research_staging REMAINS (active V2 workflow) ✓

-- Expected Result:
-- Tables reduced from 19 → 17
-- Removed abandoned manual validation workflow tables
-- Active llm_research_staging table untouched
-- Clear separation of purposes: staging (removed) vs llm_research_staging (active)
