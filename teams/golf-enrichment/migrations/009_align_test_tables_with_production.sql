-- Migration 009: Complete Test Table Alignment with Production
-- Purpose: Make test tables exact mirrors of production for complete workflow testing
-- Date: October 20, 2025
--
-- Why: Test tables were created early with minimal schema. Production has evolved
-- with 40+ columns. This aligns test tables to enable complete testing without
-- touching production data.

-- ============================================================================
-- PART 1: test_golf_courses - Add ALL Missing Production Columns
-- ============================================================================

-- Location fields (from production)
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS city VARCHAR;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS street_address VARCHAR;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS zipcode VARCHAR;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS latitude NUMERIC;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS longitude NUMERIC;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS google_place_id VARCHAR;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS google_maps_link TEXT;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS region VARCHAR;

-- Course status fields
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS course_status VARCHAR CHECK (course_status IN ('active', 'inactive', 'closed', 'unknown', 'Active', 'Open', 'Closed'));
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS data_source VARCHAR;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;

-- Discovery tracking
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS discovery_difficulty TEXT CHECK (discovery_difficulty IN ('easy', 'medium', 'hard', 'impossible'));
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS discovery_notes TEXT;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS discovery_completed_at TIMESTAMP;

-- External directory tracking (VSGA, PGA, etc.)
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS external_directory_url TEXT;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS external_directory_source TEXT CHECK (external_directory_source IN ('vsga', 'pga', 'gcsaa', 'state_association', 'management_company', 'other'));

-- Enrichment workflow fields
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS enrichment_status TEXT CHECK (enrichment_status IN ('pending', 'processing', 'completed', 'error', 'manual_entry'));
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS enrichment_requested_at TIMESTAMPTZ;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS enrichment_completed_at TIMESTAMPTZ;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS enrichment_error TEXT;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS google_enriched BOOLEAN DEFAULT false;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS last_enhanced TIMESTAMP;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS enhancement_status VARCHAR DEFAULT 'pending';

-- Water hazards (Agent 7) - production column names
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS water_hazards INTEGER;  -- Match production!

-- ClickUp integration
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS clickup_task_id TEXT;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS clickup_synced_at TIMESTAMPTZ;

-- ALREADY EXISTS from previous migrations (verify):
-- segment, segment_confidence, segment_signals
-- range_intel, opportunity_scores, agent6_enriched_at
-- water_hazard_count, water_hazard_confidence, water_hazard_details, agent7_enriched_at
-- water_hazard_rating, water_hazard_source (from migration 007)
-- contacts_page_url, contacts_page_search_method, contacts_page_found_at (from migration 007)
-- opportunities (from migration 007)
-- agent_cost_usd (from migration 007)

-- ============================================================================
-- PART 2: test_golf_course_contacts - Add ALL Missing Production Columns
-- ============================================================================

-- Quality tracking
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS contact_source VARCHAR CHECK (contact_source IN ('website_scrape', 'linkedin_search', 'dual_verified', 'email_generated', 'manual'));
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS last_verified TIMESTAMP;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS is_primary_contact BOOLEAN DEFAULT false;

-- Email enrichment (detailed tracking)
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS email_verification_status VARCHAR;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS email_verification_date TIMESTAMP;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS email_confidence_score INTEGER;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS email_enrichment_provider VARCHAR;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS email_enrichment_date TIMESTAMP;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS email_deliverability_score INTEGER;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS email_catch_all BOOLEAN;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS email_discovery_method VARCHAR;

-- LinkedIn enrichment (employment verification)
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS employment_verified BOOLEAN DEFAULT false;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS employment_verified_date TIMESTAMP;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS current_company TEXT;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS current_position TEXT;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS tenure_at_course TEXT;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS job_change_detected BOOLEAN DEFAULT false;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS linkedin_enrichment_status TEXT CHECK (linkedin_enrichment_status IN ('verified_current', 'job_change_detected', 'left_industry', 'profile_inactive', 'enrichment_failed', 'url_invalid', 'pending'));
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS linkedin_last_enriched TIMESTAMP;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS failed_enrichment_attempts INTEGER DEFAULT 0;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS linkedin_url_invalid BOOLEAN DEFAULT false;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS tenure_start_date TEXT;  -- From Agent 4!
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS linkedin_confidence TEXT;

-- Contact lifecycle
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS inactive_reason TEXT CHECK (inactive_reason IN ('wrong_role', 'job_change', 'duplicate', 'unresponsive', 'other'));

-- ClickUp integration
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS clickup_task_id TEXT;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS clickup_synced_at TIMESTAMPTZ;

-- Denormalized fields
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS region VARCHAR;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS state_code VARCHAR;

-- Discovery tracking
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS discovery_method TEXT;

-- ALREADY EXISTS from base schema:
-- contact_id, golf_course_id, contact_name, contact_title, created_at
-- contact_email, email_confidence, email_method
-- linkedin_url, linkedin_method
-- contact_phone, phone_method, phone_confidence
-- tenure_years, tenure_confidence, previous_clubs
-- industry_experience_years, responsibilities, career_notes, agent65_enriched_at

-- ============================================================================
-- PART 3: Add Comments (Documentation)
-- ============================================================================

COMMENT ON TABLE test_golf_courses IS 'Test table - exact mirror of production golf_courses for safe workflow testing';
COMMENT ON TABLE test_golf_course_contacts IS 'Test table - exact mirror of production golf_course_contacts for safe workflow testing';

COMMENT ON COLUMN test_golf_courses.agent_cost_usd IS 'Total USD cost for agent enrichment (for budget tracking)';
COMMENT ON COLUMN test_golf_course_contacts.tenure_start_date IS 'Start date of current position (extracted by Agent 4 from Firecrawl search)';
COMMENT ON COLUMN test_golf_course_contacts.tenure_years IS 'Years at current position (extracted by Agent 4, no scraping needed!)';

-- ============================================================================
-- PART 4: Verification
-- ============================================================================

DO $$
DECLARE
  test_courses_count INTEGER;
  test_contacts_count INTEGER;
  prod_courses_count INTEGER;
  prod_contacts_count INTEGER;
BEGIN
  -- Count columns in each table
  SELECT COUNT(*) INTO test_courses_count
  FROM information_schema.columns
  WHERE table_name = 'test_golf_courses';

  SELECT COUNT(*) INTO test_contacts_count
  FROM information_schema.columns
  WHERE table_name = 'test_golf_course_contacts';

  SELECT COUNT(*) INTO prod_courses_count
  FROM information_schema.columns
  WHERE table_name = 'golf_courses';

  SELECT COUNT(*) INTO prod_contacts_count
  FROM information_schema.columns
  WHERE table_name = 'golf_course_contacts';

  RAISE NOTICE '========================================';
  RAISE NOTICE 'Test Table Alignment Complete!';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'test_golf_courses: % columns', test_courses_count;
  RAISE NOTICE 'golf_courses (prod): % columns', prod_courses_count;
  RAISE NOTICE 'Column parity: % columns added', (test_courses_count - 17);
  RAISE NOTICE '';
  RAISE NOTICE 'test_golf_course_contacts: % columns', test_contacts_count;
  RAISE NOTICE 'golf_course_contacts (prod): % columns', prod_contacts_count;
  RAISE NOTICE 'Column parity: % columns added', (test_contacts_count - 20);
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Ready for complete workflow testing!';
  RAISE NOTICE '========================================';
END $$;
