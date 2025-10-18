-- Migration: Add Agent 6 and Agent 7 enrichment fields
-- Date: 2025-01-17
-- Purpose: Support business intelligence and water hazard detection

-- ============================================================================
-- GOLF_COURSES Table: Add Agent 6 and Agent 7 fields
-- ============================================================================

-- Agent 6: Business Intelligence (course-level)
ALTER TABLE golf_courses
  ADD COLUMN IF NOT EXISTS segment VARCHAR(20),  -- 'high-end', 'budget', 'both', 'unknown'
  ADD COLUMN IF NOT EXISTS segment_confidence INT CHECK (segment_confidence BETWEEN 1 AND 10),
  ADD COLUMN IF NOT EXISTS segment_signals JSONB,  -- Array of classification reasons
  ADD COLUMN IF NOT EXISTS opportunity_scores JSONB,  -- {range_ball_buy: 8, range_ball_sell: 2, ...}
  ADD COLUMN IF NOT EXISTS range_intel JSONB,  -- {has_range: true, volume_signals: [...], ...}
  ADD COLUMN IF NOT EXISTS agent6_enriched_at TIMESTAMP;

-- Agent 7: Water Hazard Detection (course-level)
ALTER TABLE golf_courses
  ADD COLUMN IF NOT EXISTS water_hazard_count INT,
  ADD COLUMN IF NOT EXISTS water_hazard_confidence VARCHAR(20),  -- 'high', 'medium', 'low', 'none'
  ADD COLUMN IF NOT EXISTS water_hazard_details JSONB,  -- Details from search
  ADD COLUMN IF NOT EXISTS agent7_enriched_at TIMESTAMP;

-- Add comments
COMMENT ON COLUMN golf_courses.segment IS 'Business segmentation: high-end (buy target), budget (sell target), both, unknown';
COMMENT ON COLUMN golf_courses.segment_confidence IS 'Confidence in segmentation (1-10 scale)';
COMMENT ON COLUMN golf_courses.segment_signals IS 'Array of indicators that led to this classification';
COMMENT ON COLUMN golf_courses.opportunity_scores IS 'Scores for 6 opportunity types: range_ball_buy, range_ball_sell, range_ball_lease, proshop_ecommerce, superintendent_partnership, ball_retrieval';
COMMENT ON COLUMN golf_courses.range_intel IS 'Practice range intelligence: has_range, volume_signals, quality_complaints, budget_signals, sustainability_signals';
COMMENT ON COLUMN golf_courses.water_hazard_count IS 'Number of water hazards on course (for ball retrieval opportunity scoring)';
COMMENT ON COLUMN golf_courses.water_hazard_confidence IS 'Confidence in water hazard count: high (verified), medium (estimated), low (uncertain), none (not found)';

-- ============================================================================
-- GOLF_COURSE_CONTACTS Table: Add Agent 6 conversation starters
-- ============================================================================

-- Agent 6: Conversation Starters (contact-level, role-specific)
ALTER TABLE golf_course_contacts
  ADD COLUMN IF NOT EXISTS conversation_starters JSONB,  -- Array of {text, value_prop, relevance}
  ADD COLUMN IF NOT EXISTS top_opportunity_1 VARCHAR(50),  -- Primary opportunity for this contact
  ADD COLUMN IF NOT EXISTS top_opportunity_2 VARCHAR(50),  -- Secondary opportunity
  ADD COLUMN IF NOT EXISTS agent6_enriched_at TIMESTAMP;

-- Add comments
COMMENT ON COLUMN golf_course_contacts.conversation_starters IS 'Array of value-prop specific conversation starters: [{text, value_prop, relevance}, ...]';
COMMENT ON COLUMN golf_course_contacts.top_opportunity_1 IS 'Primary opportunity for this contact (from Agent 6 scoring)';
COMMENT ON COLUMN golf_course_contacts.top_opportunity_2 IS 'Secondary opportunity for this contact';

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Query patterns: Filter by segment, order by confidence/opportunity scores
CREATE INDEX IF NOT EXISTS idx_golf_courses_segment ON golf_courses(segment);
CREATE INDEX IF NOT EXISTS idx_golf_courses_segment_confidence ON golf_courses(segment_confidence DESC);
CREATE INDEX IF NOT EXISTS idx_golf_courses_water_hazards ON golf_courses(water_hazard_count DESC);

-- Query pattern: Find contacts needing enrichment
CREATE INDEX IF NOT EXISTS idx_contacts_agent6_enrichment ON golf_course_contacts(agent6_enriched_at)
  WHERE agent6_enriched_at IS NULL;

-- ============================================================================
-- Update enhancement_status enum (if needed)
-- ============================================================================

-- Add new statuses for Agent 6/7
-- Note: Check existing constraint before running
ALTER TABLE golf_courses DROP CONSTRAINT IF EXISTS golf_courses_enhancement_status_check;

ALTER TABLE golf_courses
  ADD CONSTRAINT golf_courses_enhancement_status_check
  CHECK (enhancement_status IN (
    'pending',
    'in_progress',
    'complete',
    'failed',
    'enhanced',
    'mismatch',
    'error',
    'contacts_complete',
    'social_media_enhanced',
    'classification_complete',
    'contacts_generated',
    'contacts_unavailable_closed',
    'social_media_no_website',
    'agent_enrichment_complete',  -- NEW: All agents (1-7) completed
    'agent6_complete',  -- NEW: Business intel complete
    'agent7_complete'   -- NEW: Water hazards complete
  ));

-- ============================================================================
-- Sample Data Update (Test Courses)
-- ============================================================================

-- Example: Update Richmond Country Club with Agent 6/7 data
-- (This would come from orchestrator in production)
/*
UPDATE golf_courses
SET
  segment = 'high-end',
  segment_confidence = 8,
  segment_signals = '[
    "Private club positioning",
    "4.5+ rating with quality expectations",
    "Recent facility investments"
  ]'::jsonb,
  opportunity_scores = '{
    "range_ball_buy": 8,
    "range_ball_sell": 2,
    "range_ball_lease": 9,
    "proshop_ecommerce": 5,
    "superintendent_partnership": 6,
    "ball_retrieval": 7
  }'::jsonb,
  water_hazard_count = 5,
  water_hazard_confidence = 'high',
  agent6_enriched_at = NOW(),
  agent7_enriched_at = NOW(),
  enhancement_status = 'agent_enrichment_complete'
WHERE course_name = 'Richmond Country Club' AND state_code = 'VA';
*/
