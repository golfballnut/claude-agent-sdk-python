-- Migration 014: Add V2 fields to golf_courses and golf_course_contacts
-- Purpose: Extend existing tables to store validated V2 research data
-- Created: 2025-10-31

-- ============================================================================
-- GOLF_COURSES TABLE: Add V2 enrichment fields
-- ============================================================================

-- Raw V2 JSON storage (permanent, for audit trail and re-processing)
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS v2_research_json JSONB;
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS v2_parsed_at TIMESTAMPTZ;
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS v2_validation_flags JSONB; -- Array of warning flags: ["LOW_TIER_CONFIDENCE", "NO_CONTACTS_FOUND"]

-- Section 1: Course Tier (Premium/Mid/Budget classification)
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS course_tier TEXT CHECK (course_tier IN ('Premium', 'Mid', 'Budget'));
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS course_tier_confidence NUMERIC CHECK (course_tier_confidence BETWEEN 0 AND 1);
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS course_tier_evidence JSONB; -- Array of {claim, source} objects

-- Section 3: Volume Indicator (estimated annual rounds)
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS annual_rounds_estimate INTEGER CHECK (annual_rounds_estimate > 0);
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS annual_rounds_range TEXT; -- "20k-30k"
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS annual_rounds_confidence NUMERIC CHECK (annual_rounds_confidence BETWEEN 0 AND 1);

-- Section 5: Basic Intelligence (stored as JSONB for flexibility)
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS v2_intelligence JSONB;
-- Structure: {ownership: {type, entity_name, source}, recent_changes: [...], current_vendors: [...], selling_points: [...]}

-- ============================================================================
-- GOLF_COURSE_CONTACTS TABLE: Add V2 contact fields
-- ============================================================================

-- V2-specific contact metadata
ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS contact_sources JSONB; -- Array of source URLs where contact was found
ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS employment_verified BOOLEAN DEFAULT FALSE; -- LLM verified current employment
ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS needs_enrichment BOOLEAN DEFAULT TRUE; -- Flag for Phase 2.2 email enrichment

-- ============================================================================
-- INDEXES
-- ============================================================================

-- V2 query optimization
CREATE INDEX IF NOT EXISTS idx_course_tier ON golf_courses(course_tier);
CREATE INDEX IF NOT EXISTS idx_annual_rounds ON golf_courses(annual_rounds_estimate) WHERE annual_rounds_estimate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_v2_parsed ON golf_courses(v2_parsed_at DESC) WHERE v2_parsed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_validation_flags ON golf_courses USING GIN(v2_validation_flags) WHERE v2_validation_flags IS NOT NULL;

-- Contact enrichment optimization
CREATE INDEX IF NOT EXISTS idx_needs_enrichment ON golf_course_contacts(needs_enrichment) WHERE needs_enrichment = TRUE;

-- ============================================================================
-- COMMENTS
-- ============================================================================

-- golf_courses V2 fields
COMMENT ON COLUMN golf_courses.v2_research_json IS 'Full V2 LLM research output (5 sections) - permanent audit trail';
COMMENT ON COLUMN golf_courses.v2_parsed_at IS 'Timestamp when V2 JSON was successfully parsed and validated';
COMMENT ON COLUMN golf_courses.v2_validation_flags IS 'Array of quality warnings: LOW_TIER_CONFIDENCE, NO_CONTACTS_FOUND, NO_CONTACT_METHODS';
COMMENT ON COLUMN golf_courses.course_tier IS 'V2 Section 1: Premium (high-end/resort) | Mid (semi-private) | Budget (public/municipal)';
COMMENT ON COLUMN golf_courses.course_tier_confidence IS 'V2 Section 1: LLM confidence score 0.0-1.0 (≥0.7 recommended)';
COMMENT ON COLUMN golf_courses.course_tier_evidence IS 'V2 Section 1: Pricing evidence array [{claim, source}]';
COMMENT ON COLUMN golf_courses.annual_rounds_estimate IS 'V2 Section 3: Estimated annual rounds per year (midpoint of range)';
COMMENT ON COLUMN golf_courses.annual_rounds_range IS 'V2 Section 3: Volume range text (e.g., "20k-30k")';
COMMENT ON COLUMN golf_courses.annual_rounds_confidence IS 'V2 Section 3: Confidence in volume estimate 0.0-1.0';
COMMENT ON COLUMN golf_courses.v2_intelligence IS 'V2 Section 5: JSONB {ownership, recent_changes, current_vendors, selling_points}';

-- golf_course_contacts V2 fields
COMMENT ON COLUMN golf_course_contacts.contact_sources IS 'V2 Section 4: Array of URLs where contact information was discovered';
COMMENT ON COLUMN golf_course_contacts.employment_verified IS 'V2 Section 4: LLM verified person currently employed at this course';
COMMENT ON COLUMN golf_course_contacts.needs_enrichment IS 'Flag for Phase 2.2: TRUE = needs Apollo/Hunter enrichment for email/LinkedIn';

-- ============================================================================
-- DATA QUALITY VIEWS
-- ============================================================================

-- View: V2 courses needing manual review
CREATE OR REPLACE VIEW v2_courses_needing_review AS
SELECT
  id,
  course_name,
  state_code,
  course_tier,
  course_tier_confidence,
  v2_validation_flags,
  annual_rounds_estimate,
  v2_parsed_at
FROM golf_courses
WHERE v2_parsed_at IS NOT NULL
  AND (
    course_tier_confidence < 0.7
    OR v2_validation_flags ? 'NO_CONTACTS_FOUND'
    OR v2_validation_flags ? 'NO_CONTACT_METHODS'
    OR v2_validation_flags ? 'LOW_TIER_CONFIDENCE'
  )
ORDER BY v2_parsed_at DESC;

COMMENT ON VIEW v2_courses_needing_review IS 'V2 courses with quality warnings that may need manual review';

-- View: Contacts needing enrichment
CREATE OR REPLACE VIEW contacts_needing_enrichment AS
SELECT
  c.id,
  c.name,
  c.title,
  c.email,
  c.linkedin_url,
  c.phone,
  c.employment_verified,
  gc.course_name,
  gc.state_code
FROM golf_course_contacts c
JOIN golf_courses gc ON c.golf_course_id = gc.id
WHERE c.needs_enrichment = TRUE
  AND (c.email IS NULL OR c.linkedin_url IS NULL) -- Missing contact method
ORDER BY c.enriched_at DESC;

COMMENT ON VIEW contacts_needing_enrichment IS 'Contacts that need Apollo/Hunter enrichment for email or LinkedIn discovery';
