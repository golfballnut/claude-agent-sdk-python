-- Migration 006: Add Water Hazard Rating Fields
-- Date: October 20, 2025
-- Purpose: Add qualitative water hazard ratings from SkyGolf database
--
-- Changes:
-- 1. Add water_hazard_rating column (scarce/moderate/heavy)
-- 2. Add water_hazard_source column (skygolf/verified/not_found)
-- 3. Keep water_hazards INTEGER for backward compatibility
-- 4. Update existing guessed values to NULL (will be re-enriched)
--
-- Rationale:
-- - SkyGolf provides accurate qualitative ratings (60% coverage)
-- - Eliminates hallucinated numbers from Perplexity
-- - Reduces cost to $0 (free scraping vs $0.006 per course)
-- - Golf-specific ratings (doesn't count creeks/streams)

-- ============================================================================
-- Add New Columns
-- ============================================================================

-- Add water_hazard_rating column (qualitative: scarce, moderate, heavy)
ALTER TABLE golf_courses
ADD COLUMN IF NOT EXISTS water_hazard_rating TEXT
CHECK (water_hazard_rating IN ('scarce', 'moderate', 'heavy'));

COMMENT ON COLUMN golf_courses.water_hazard_rating IS
'Qualitative water hazard rating from SkyGolf database: scarce (0-3 holes), moderate (4-9 holes), heavy (10+ holes). NULL if not found in SkyGolf.';

-- Add water_hazard_source column (tracking data provenance)
ALTER TABLE golf_courses
ADD COLUMN IF NOT EXISTS water_hazard_source TEXT;

COMMENT ON COLUMN golf_courses.water_hazard_source IS
'Source of water hazard data: skygolf (SkyGolf database), verified (manual verification), not_found (no data available)';

-- ============================================================================
-- Migrate Existing Data
-- ============================================================================

-- Convert existing numeric counts to qualitative ratings (best effort)
UPDATE golf_courses
SET water_hazard_rating =
  CASE
    WHEN water_hazards IS NOT NULL AND water_hazards <= 3 THEN 'scarce'
    WHEN water_hazards IS NOT NULL AND water_hazards BETWEEN 4 AND 9 THEN 'moderate'
    WHEN water_hazards IS NOT NULL AND water_hazards >= 10 THEN 'heavy'
    ELSE NULL
  END,
  water_hazard_source =
    CASE
      WHEN water_hazards IS NOT NULL AND water_hazard_confidence = 'high' THEN 'verified'
      WHEN water_hazards IS NOT NULL THEN 'legacy_perplexity'
      ELSE NULL
    END
WHERE water_hazards IS NOT NULL;

-- ============================================================================
-- Clean Up Hallucinated Data
-- ============================================================================

-- Set water_hazards to NULL for low-confidence guesses
-- These should be re-enriched with accurate SkyGolf data
UPDATE golf_courses
SET
  water_hazards = NULL,
  water_hazard_rating = NULL,
  water_hazard_source = 'needs_re_enrichment',
  water_hazard_confidence = 'none'
WHERE water_hazard_confidence = 'low'
  AND water_hazard_source = 'legacy_perplexity';

-- ============================================================================
-- Add Index for Filtering by Rating
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_golf_courses_water_rating
ON golf_courses(water_hazard_rating)
WHERE water_hazard_rating IS NOT NULL;

COMMENT ON INDEX idx_golf_courses_water_rating IS
'Index for filtering courses by water hazard rating (for opportunity scoring and retrieval targeting)';

-- ============================================================================
-- Validation Query (Run After Migration)
-- ============================================================================

-- Show distribution of water hazard ratings
-- SELECT
--   water_hazard_rating,
--   COUNT(*) as course_count,
--   AVG(water_hazards) as avg_numeric_count
-- FROM golf_courses
-- WHERE water_hazard_rating IS NOT NULL
-- GROUP BY water_hazard_rating
-- ORDER BY
--   CASE water_hazard_rating
--     WHEN 'heavy' THEN 1
--     WHEN 'moderate' THEN 2
--     WHEN 'scarce' THEN 3
--   END;
