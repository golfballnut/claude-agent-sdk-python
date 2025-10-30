-- Migration 012: Contact Source Tracking
-- Purpose: Track which data source provided golf course contacts (PGA, LinkedIn, Perplexity)
-- Date: October 28, 2025
-- Related: Agent 2.1 (LinkedIn), Agent 2.2 (Perplexity) fallback implementation

-- Add contact_source field to track where contacts came from
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  contact_source TEXT CHECK (contact_source IN (
    'vsga_directory',      -- Virginia State Golf Association directory
    'pga_directory',       -- PGA.org facility directory
    'linkedin_company',    -- LinkedIn company page (Agent 2.1)
    'perplexity_research', -- Perplexity AI research (Agent 2.2)
    'manual_research',     -- Manually researched
    'none_found'           -- No contacts found from any source
  ));

-- Add JSONB field to track which fallback sources were attempted
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  fallback_sources_attempted JSONB;

-- Add index for querying by contact source
CREATE INDEX IF NOT EXISTS idx_golf_courses_contact_source
  ON golf_courses(contact_source);

-- Add same fields to test tables
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS
  contact_source TEXT CHECK (contact_source IN (
    'vsga_directory',
    'pga_directory',
    'linkedin_company',
    'perplexity_research',
    'manual_research',
    'none_found'
  ));

ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS
  fallback_sources_attempted JSONB;

CREATE INDEX IF NOT EXISTS idx_test_golf_courses_contact_source
  ON test_golf_courses(contact_source);

-- Example usage queries:

-- Query 1: Check fallback effectiveness
-- SELECT
--   contact_source,
--   COUNT(*) as courses,
--   AVG(JSONB_ARRAY_LENGTH(COALESCE(fallback_sources_attempted, '[]'::jsonb))) as avg_fallbacks_tried
-- FROM golf_courses
-- WHERE enrichment_status = 'complete'
-- GROUP BY contact_source;

-- Query 2: Find courses that needed multiple fallbacks
-- SELECT
--   course_name,
--   contact_source,
--   fallback_sources_attempted
-- FROM golf_courses
-- WHERE fallback_sources_attempted IS NOT NULL
-- ORDER BY enrichment_completed_at DESC
-- LIMIT 20;

-- Query 3: Success rate by source
-- SELECT
--   contact_source,
--   COUNT(*) as total,
--   SUM(CASE WHEN enrichment_status = 'complete' THEN 1 ELSE 0 END) as successful,
--   ROUND(100.0 * SUM(CASE WHEN enrichment_status = 'complete' THEN 1 ELSE 0 END) / COUNT(*), 1) as success_rate_pct
-- FROM golf_courses
-- GROUP BY contact_source;
