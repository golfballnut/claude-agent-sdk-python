-- Migration: Agent 6/6.5 Refactoring + Field Enhancements
-- Date: 2025-01-17
-- Purpose: Update schema for Agent 6/6.5 split + add missing Agent 3/5 fields

-- ============================================================================
-- GOLF_COURSE_CONTACTS: Add Agent 3/5/6.5 Enhanced Fields
-- ============================================================================

-- Agent 3: Email enrichment enhancements
ALTER TABLE golf_course_contacts
  ADD COLUMN IF NOT EXISTS email_confidence INT CHECK (email_confidence BETWEEN 0 AND 100),
  ADD COLUMN IF NOT EXISTS email_method VARCHAR(50),  -- 'hunter_io', 'web_search', 'focused_search', 'not_found'
  ADD COLUMN IF NOT EXISTS linkedin_method VARCHAR(50);  -- 'hunter_io', 'web_search', 'not_found'

-- Agent 5: Phone enrichment enhancements
ALTER TABLE golf_course_contacts
  ADD COLUMN IF NOT EXISTS phone_method VARCHAR(50),  -- 'perplexity_ai', 'not_found'
  ADD COLUMN IF NOT EXISTS phone_confidence INT CHECK (phone_confidence BETWEEN 0 AND 100);

-- Agent 6.5: Contact background (NEW)
ALTER TABLE golf_course_contacts
  ADD COLUMN IF NOT EXISTS tenure_years INT,
  ADD COLUMN IF NOT EXISTS tenure_confidence VARCHAR(20),  -- 'high', 'medium', 'low', 'unknown'
  ADD COLUMN IF NOT EXISTS previous_clubs JSONB,  -- Array of previous club names
  ADD COLUMN IF NOT EXISTS industry_experience_years INT,
  ADD COLUMN IF NOT EXISTS responsibilities JSONB,  -- Array of role responsibilities
  ADD COLUMN IF NOT EXISTS career_notes TEXT,  -- Career progression summary
  ADD COLUMN IF NOT EXISTS agent65_enriched_at TIMESTAMP;

-- Remove deprecated fields (Agent 6 no longer generates these)
ALTER TABLE golf_course_contacts
  DROP COLUMN IF EXISTS conversation_starters,
  DROP COLUMN IF EXISTS top_opportunity_1,
  DROP COLUMN IF EXISTS top_opportunity_2,
  DROP COLUMN IF EXISTS agent6_enriched_at;

-- ============================================================================
-- Add Comments
-- ============================================================================

-- Agent 3 fields
COMMENT ON COLUMN golf_course_contacts.email_confidence IS 'Email confidence score (0-100) from Hunter.io or web search';
COMMENT ON COLUMN golf_course_contacts.email_method IS 'How email was found: hunter_io (highest confidence), web_search, focused_search, not_found';
COMMENT ON COLUMN golf_course_contacts.linkedin_method IS 'How LinkedIn was found: hunter_io (bonus from email search), web_search, not_found';

-- Agent 5 fields
COMMENT ON COLUMN golf_course_contacts.phone_method IS 'How phone was found: perplexity_ai (aggregated sources), not_found';
COMMENT ON COLUMN golf_course_contacts.phone_confidence IS 'Phone confidence score (0-100) - 90 if found via Perplexity';

-- Agent 6.5 fields
COMMENT ON COLUMN golf_course_contacts.tenure_years IS 'Years at current course (from Agent 6.5 background search)';
COMMENT ON COLUMN golf_course_contacts.tenure_confidence IS 'Confidence in tenure data: high (verified), medium (estimated), low (uncertain), unknown (not found)';
COMMENT ON COLUMN golf_course_contacts.previous_clubs IS 'Array of previous golf courses/clubs worked at';
COMMENT ON COLUMN golf_course_contacts.industry_experience_years IS 'Total years in golf course industry';
COMMENT ON COLUMN golf_course_contacts.responsibilities IS 'Array of role-specific responsibilities and duties';
COMMENT ON COLUMN golf_course_contacts.career_notes IS 'Career progression summary and background notes';

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Query pattern: Find high-confidence emails for outreach
CREATE INDEX IF NOT EXISTS idx_contacts_email_confidence ON golf_course_contacts(email_confidence DESC)
  WHERE email IS NOT NULL;

-- Query pattern: Find contacts with tenure data (experienced professionals)
CREATE INDEX IF NOT EXISTS idx_contacts_tenure ON golf_course_contacts(tenure_years DESC)
  WHERE tenure_years IS NOT NULL;

-- Query pattern: Find contacts needing Agent 6.5 enrichment
CREATE INDEX IF NOT EXISTS idx_contacts_agent65_enrichment ON golf_course_contacts(agent65_enriched_at)
  WHERE agent65_enriched_at IS NULL;

-- ============================================================================
-- Sample Data Update (Test)
-- ============================================================================

-- Example: Update Stacy Foster with Agent 3/5/6.5 data
/*
UPDATE golf_course_contacts
SET
  email_confidence = 98,
  email_method = 'hunter_io',
  linkedin_method = 'hunter_io',
  phone_method = 'perplexity_ai',
  phone_confidence = 90,
  tenure_years = NULL,
  tenure_confidence = 'unknown',
  previous_clubs = '[]'::jsonb,
  industry_experience_years = NULL,
  responsibilities = '[
    "oversight of course operations",
    "staff management",
    "financial management",
    "member services"
  ]'::jsonb,
  career_notes = 'General Manager at Richmond Country Club',
  agent65_enriched_at = NOW()
WHERE name = 'Stacy Foster'
  AND golf_course_id = (SELECT id FROM golf_courses WHERE course_name = 'Richmond Country Club' AND state_code = 'VA');
*/
