-- Migration 003: Create Test Tables for Agent Testing
-- Date: 2025-10-18
-- Purpose: Create test_golf_courses and test_golf_course_contacts with FULL schema
--          Mirrors production tables for safe agent testing

-- ============================================================================
-- DROP existing test tables if they have incomplete schema
-- ============================================================================
DROP TABLE IF EXISTS test_golf_course_contacts CASCADE;
DROP TABLE IF EXISTS test_golf_courses CASCADE;

-- ============================================================================
-- CREATE test_golf_courses (matches production golf_courses)
-- ============================================================================
CREATE TABLE test_golf_courses (
  -- Primary Key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Basic Course Info (Agent 2)
  course_name VARCHAR(255) NOT NULL,
  state_code VARCHAR(2),
  website VARCHAR(500),
  phone VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),

  -- Agent 6: Business Intelligence (course-level)
  segment VARCHAR(20),  -- 'high-end', 'budget', 'both', 'unknown'
  segment_confidence INT CHECK (segment_confidence BETWEEN 1 AND 10),
  segment_signals JSONB,  -- Array of classification signals
  range_intel JSONB,  -- {has_range, volume_signals, quality_complaints, budget_signals, sustainability_signals}
  opportunity_scores JSONB,  -- {range_ball_buy, range_ball_sell, range_ball_lease, proshop_ecommerce, superintendent_partnership, ball_retrieval}
  agent6_enriched_at TIMESTAMP,

  -- Agent 7: Water Hazards (course-level)
  water_hazard_count INT,
  water_hazard_confidence VARCHAR(20),  -- 'high', 'medium', 'low', 'none'
  water_hazard_details JSONB,  -- Array of details/sources
  agent7_enriched_at TIMESTAMP
);

-- ============================================================================
-- CREATE test_golf_course_contacts (matches production golf_course_contacts)
-- ============================================================================
CREATE TABLE test_golf_course_contacts (
  -- Primary Key (uses contact_id for test tables, id for production)
  contact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign Key
  golf_course_id UUID REFERENCES test_golf_courses(id) ON DELETE CASCADE,

  -- Basic Contact Info (Agent 2)
  contact_name VARCHAR(255) NOT NULL,
  contact_title VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),

  -- Agent 3: Email + LinkedIn Enrichment
  contact_email VARCHAR(255),
  email_confidence INT CHECK (email_confidence BETWEEN 0 AND 100),
  email_method VARCHAR(50),  -- 'hunter_io', 'web_search', 'focused_search', 'not_found'
  linkedin_url VARCHAR(500),
  linkedin_method VARCHAR(50),  -- 'hunter_io', 'web_search', 'not_found'

  -- Agent 5: Phone Enrichment
  contact_phone VARCHAR(50),
  phone_method VARCHAR(50),  -- 'perplexity_ai', 'not_found'
  phone_confidence INT CHECK (phone_confidence BETWEEN 0 AND 100),

  -- Agent 6.5: Contact Background
  tenure_years INT,
  tenure_confidence VARCHAR(20),  -- 'high', 'medium', 'low', 'unknown'
  previous_clubs JSONB,  -- Array of previous club names
  industry_experience_years INT,
  responsibilities JSONB,  -- Array of role responsibilities
  career_notes TEXT,  -- Career progression summary
  agent65_enriched_at TIMESTAMP
);

-- ============================================================================
-- Enable Row Level Security (RLS)
-- ============================================================================
ALTER TABLE test_golf_courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_golf_course_contacts ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies: Allow service_role full access
-- ============================================================================

-- Test golf courses: Full access for service role
CREATE POLICY "Service role has full access to test courses"
  ON test_golf_courses
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Test contacts: Full access for service role
CREATE POLICY "Service role has full access to test contacts"
  ON test_golf_course_contacts
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Course lookups by name (for upsert logic)
CREATE INDEX idx_test_courses_name ON test_golf_courses(course_name);

-- Contact lookups by course + name (for upsert logic)
CREATE INDEX idx_test_contacts_course_name ON test_golf_course_contacts(golf_course_id, contact_name);

-- ============================================================================
-- Add Table Comments
-- ============================================================================

COMMENT ON TABLE test_golf_courses IS 'Test table for agent validation - mirrors production golf_courses schema';
COMMENT ON TABLE test_golf_course_contacts IS 'Test table for agent validation - mirrors production golf_course_contacts schema';

-- ============================================================================
-- Verification Query (run this to confirm success)
-- ============================================================================

/*
-- Verify test_golf_courses columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'test_golf_courses'
ORDER BY ordinal_position;

-- Verify test_golf_course_contacts columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'test_golf_course_contacts'
ORDER BY ordinal_position;

-- Check RLS policies
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE tablename LIKE 'test_golf%';
*/
