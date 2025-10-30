-- Migration 004: Agent Integration Fields
-- Purpose: Add fields to support agent workflow integration
-- Project: golf-course-outreach (apply to production Supabase)
-- Date: October 18, 2024
--
-- This migration adds:
-- 1. Workflow control fields (enrichment_status, timestamps)
-- 2. Agent output fields (segment, opportunities, intel)
-- 3. Cost tracking fields
-- 4. Indexes for performance
-- 5. Database triggers for automation

-- ============================================================================
-- PART 1: golf_courses table additions
-- ============================================================================

-- Workflow control fields
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  enrichment_status TEXT CHECK (enrichment_status IN ('pending', 'processing', 'complete', 'error', 'manual_entry'));

ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  enrichment_requested_at TIMESTAMPTZ;

ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  enrichment_completed_at TIMESTAMPTZ;

ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  enrichment_error TEXT;

ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  retry_count INT DEFAULT 0;

-- Step 3 flag (Google Places enrichment complete)
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  google_enriched BOOLEAN DEFAULT false;

-- Agent 6 output (Course Intelligence)
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  segment TEXT CHECK (segment IN ('high-end', 'budget', 'both'));

ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  segment_confidence INT CHECK (segment_confidence BETWEEN 1 AND 10);

ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  segment_signals JSONB;

-- Agent 7 output (Water Hazards)
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  water_hazards INT;

ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  water_hazard_confidence TEXT;

-- Agent 6 business intelligence
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  opportunities JSONB;  -- 6 opportunity types scored 1-10

ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  range_intel JSONB;  -- Practice range data

-- Cost tracking
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  agent_cost_usd DECIMAL(10,4);

-- Comments for documentation
COMMENT ON COLUMN golf_courses.enrichment_status IS 'Agent workflow status: pending (requested), processing (running), complete (done), error (failed)';
COMMENT ON COLUMN golf_courses.segment IS 'Business segment from Agent 6: high-end (buy target), budget (sell target), both (mixed)';
COMMENT ON COLUMN golf_courses.opportunities IS 'JSON object with 6 opportunity scores (1-10): range_ball_buy, range_ball_sell, range_ball_lease, proshop_ecommerce, superintendent_partnership, ball_retrieval';
COMMENT ON COLUMN golf_courses.range_intel IS 'JSON object with practice range data: has_range, volume_signals, quality_complaints, budget_signals';

-- ============================================================================
-- PART 2: golf_course_contacts table additions
-- ============================================================================

-- Contact enrichment (from agents)
ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  email TEXT;

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  email_confidence INT CHECK (email_confidence BETWEEN 0 AND 100);

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  email_source TEXT;  -- 'hunter.io', 'manual', etc.

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  linkedin_url TEXT;

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  phone TEXT;

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  phone_confidence INT CHECK (phone_confidence BETWEEN 0 AND 100);

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  phone_source TEXT;  -- 'perplexity', 'google', 'manual', etc.

-- Agent 6.5 output (Contact Background)
ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  tenure_years INT;

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  previous_clubs JSONB;  -- Array of previous clubs

-- Agent 6 output (Contact-level intelligence)
ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  segment TEXT;  -- Can override course-level segment

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  opportunities JSONB;  -- Contact-specific opportunity scores

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  conversation_starters JSONB;  -- Array of pre-written starters with relevance scores

-- Metadata
ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  enriched_at TIMESTAMPTZ;

-- ClickUp integration
ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  clickup_task_id TEXT;

ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  clickup_synced_at TIMESTAMPTZ;

-- Comments for documentation
COMMENT ON COLUMN golf_course_contacts.conversation_starters IS 'JSON array of objects: [{text: "...", value_prop: "range_ball_buy", relevance: 9}]';
COMMENT ON COLUMN golf_course_contacts.clickup_task_id IS 'ClickUp task ID for CRM tracking';

-- ============================================================================
-- PART 3: Indexes for performance
-- ============================================================================

-- Index for finding courses ready to enrich
CREATE INDEX IF NOT EXISTS idx_google_enriched_not_agent_enriched
  ON golf_courses(google_enriched, enrichment_status)
  WHERE google_enriched = true AND enrichment_status IS NULL;

-- Index for finding pending enrichments (trigger lookup)
CREATE INDEX IF NOT EXISTS idx_enrichment_pending
  ON golf_courses(enrichment_status, enrichment_requested_at)
  WHERE enrichment_status = 'pending';

-- Index for finding stuck processing
CREATE INDEX IF NOT EXISTS idx_enrichment_processing
  ON golf_courses(enrichment_status, enrichment_requested_at)
  WHERE enrichment_status = 'processing';

-- Index for finding errors
CREATE INDEX IF NOT EXISTS idx_enrichment_errors
  ON golf_courses(enrichment_status, enrichment_requested_at)
  WHERE enrichment_status = 'error';

-- Index for cost analysis
CREATE INDEX IF NOT EXISTS idx_enrichment_completed_cost
  ON golf_courses(enrichment_completed_at, agent_cost_usd)
  WHERE enrichment_status = 'complete';

-- Index for contact lookups
CREATE INDEX IF NOT EXISTS idx_contacts_by_course
  ON golf_course_contacts(golf_course_id, enriched_at);

-- Index for ClickUp sync monitoring
CREATE INDEX IF NOT EXISTS idx_contacts_clickup_sync
  ON golf_course_contacts(clickup_task_id, enriched_at)
  WHERE clickup_task_id IS NULL;

-- ============================================================================
-- PART 4: Database triggers (Automation - Step 4 & 5)
-- ============================================================================

-- Enable http extension for calling edge functions
CREATE EXTENSION IF NOT EXISTS http WITH SCHEMA extensions;

-- Trigger Function 1: Call agent enrichment edge function
-- Fires when enrichment_status changes to 'pending'
CREATE OR REPLACE FUNCTION call_trigger_agent_enrichment()
RETURNS TRIGGER AS $$
BEGIN
  -- Async HTTP call to edge function
  PERFORM net.http_post(
    url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/trigger-agent-enrichment',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.supabase_anon_key', true)
    ),
    body := json_build_object('course_id', NEW.id)::text
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger: On enrichment_status change to 'pending'
DROP TRIGGER IF EXISTS on_enrichment_requested ON golf_courses;
CREATE TRIGGER on_enrichment_requested
AFTER UPDATE OF enrichment_status ON golf_courses
FOR EACH ROW
WHEN (NEW.enrichment_status = 'pending' AND
      (OLD.enrichment_status IS NULL OR OLD.enrichment_status IS DISTINCT FROM 'pending'))
EXECUTE FUNCTION call_trigger_agent_enrichment();

COMMENT ON TRIGGER on_enrichment_requested ON golf_courses IS 'Step 4: Triggers agent enrichment workflow when enrichment_status set to pending';

-- Trigger Function 2: Call ClickUp sync edge function
-- Fires when new contact inserted
CREATE OR REPLACE FUNCTION call_create_clickup_task()
RETURNS TRIGGER AS $$
BEGIN
  -- Async HTTP call to edge function
  PERFORM net.http_post(
    url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/create-clickup-tasks',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.supabase_anon_key', true)
    ),
    body := row_to_json(NEW)::text
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger: On new contact insert
DROP TRIGGER IF EXISTS on_contact_inserted ON golf_course_contacts;
CREATE TRIGGER on_contact_inserted
AFTER INSERT ON golf_course_contacts
FOR EACH ROW
WHEN (NEW.enriched_at IS NOT NULL)  -- Only trigger if enriched by agents
EXECUTE FUNCTION call_create_clickup_task();

COMMENT ON TRIGGER on_contact_inserted ON golf_course_contacts IS 'Step 5: Creates ClickUp task when enriched contact inserted';

-- ============================================================================
-- PART 5: Helper functions for monitoring
-- ============================================================================

-- Function: Get enrichment health metrics
CREATE OR REPLACE FUNCTION get_enrichment_health(days_back INT DEFAULT 7)
RETURNS TABLE (
  pending_count BIGINT,
  processing_count BIGINT,
  complete_count BIGINT,
  error_count BIGINT,
  success_rate_percent NUMERIC,
  avg_cost_usd NUMERIC,
  avg_duration_seconds NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*) FILTER (WHERE enrichment_status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE enrichment_status = 'processing') as processing_count,
    COUNT(*) FILTER (WHERE enrichment_status = 'complete') as complete_count,
    COUNT(*) FILTER (WHERE enrichment_status = 'error') as error_count,
    ROUND(
      COUNT(*) FILTER (WHERE enrichment_status = 'complete') * 100.0 /
      NULLIF(COUNT(*) FILTER (WHERE enrichment_status IN ('complete', 'error')), 0),
      2
    ) as success_rate_percent,
    ROUND(AVG(agent_cost_usd) FILTER (WHERE enrichment_status = 'complete'), 4) as avg_cost_usd,
    ROUND(
      AVG(EXTRACT(EPOCH FROM (enrichment_completed_at - enrichment_requested_at)))
      FILTER (WHERE enrichment_status = 'complete'),
      1
    ) as avg_duration_seconds
  FROM golf_courses
  WHERE enrichment_requested_at > NOW() - (days_back || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_enrichment_health IS 'Quick health check: SELECT * FROM get_enrichment_health(7);';

-- Function: Reset stuck processing
CREATE OR REPLACE FUNCTION reset_stuck_processing(max_minutes INT DEFAULT 15)
RETURNS INT AS $$
DECLARE
  updated_count INT;
BEGIN
  UPDATE golf_courses
  SET enrichment_status = 'error',
      enrichment_error = 'Timeout: Processing exceeded ' || max_minutes || ' minutes'
  WHERE enrichment_status = 'processing'
    AND enrichment_requested_at < NOW() - (max_minutes || ' minutes')::INTERVAL;

  GET DIAGNOSTICS updated_count = ROW_COUNT;
  RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION reset_stuck_processing IS 'Reset courses stuck in processing: SELECT reset_stuck_processing(15);';

-- ============================================================================
-- PART 6: Monitoring views
-- ============================================================================

-- View: System health dashboard
CREATE OR REPLACE VIEW v_enrichment_health AS
SELECT
  COUNT(*) FILTER (WHERE enrichment_status = 'pending') as pending,
  COUNT(*) FILTER (WHERE enrichment_status = 'processing') as processing,
  COUNT(*) FILTER (WHERE enrichment_status = 'complete') as completed,
  COUNT(*) FILTER (WHERE enrichment_status = 'error') as errors,
  ROUND(
    COUNT(*) FILTER (WHERE enrichment_status = 'complete') * 100.0 /
    NULLIF(COUNT(*) FILTER (WHERE enrichment_status IN ('complete', 'error')), 0),
    2
  ) as success_rate_percent,
  ROUND(AVG(agent_cost_usd) FILTER (WHERE enrichment_status = 'complete'), 4) as avg_cost,
  ROUND(
    AVG(EXTRACT(EPOCH FROM (enrichment_completed_at - enrichment_requested_at)))
    FILTER (WHERE enrichment_status = 'complete'),
    1
  ) as avg_duration_seconds
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '7 days';

-- View: Recent errors
CREATE OR REPLACE VIEW v_enrichment_errors AS
SELECT
  id,
  course_name,
  state,
  enrichment_error,
  enrichment_requested_at,
  retry_count,
  ROUND(EXTRACT(EPOCH FROM (NOW() - enrichment_requested_at)) / 60, 1) as minutes_ago
FROM golf_courses
WHERE enrichment_status = 'error'
  AND enrichment_requested_at > NOW() - INTERVAL '24 hours'
ORDER BY enrichment_requested_at DESC;

-- View: Cost analysis by day
CREATE OR REPLACE VIEW v_daily_costs AS
SELECT
  DATE(enrichment_requested_at) as date,
  COUNT(*) as courses_enriched,
  SUM(agent_cost_usd) as total_cost,
  ROUND(AVG(agent_cost_usd), 4) as avg_cost_per_course,
  ROUND(MIN(agent_cost_usd), 4) as min_cost,
  ROUND(MAX(agent_cost_usd), 4) as max_cost
FROM golf_courses
WHERE enrichment_status = 'complete'
  AND enrichment_requested_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(enrichment_requested_at)
ORDER BY date DESC;

-- View: ClickUp sync status
CREATE OR REPLACE VIEW v_clickup_sync_status AS
SELECT
  COUNT(*) FILTER (WHERE clickup_task_id IS NOT NULL) as synced,
  COUNT(*) FILTER (WHERE clickup_task_id IS NULL) as not_synced,
  ROUND(
    COUNT(*) FILTER (WHERE clickup_task_id IS NOT NULL) * 100.0 / COUNT(*),
    2
  ) as sync_rate_percent
FROM golf_course_contacts
WHERE enriched_at > NOW() - INTERVAL '7 days';

-- ============================================================================
-- PART 7: Data integrity constraints
-- ============================================================================

-- Prevent duplicate contacts per course
-- (Use unique index instead of constraint for flexibility)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_contact_per_course
  ON golf_course_contacts(golf_course_id, name)
  WHERE enriched_at IS NOT NULL;

-- Ensure contacts link to valid courses
-- (Foreign key should already exist, but verify)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'golf_course_contacts_golf_course_id_fkey'
      AND table_name = 'golf_course_contacts'
  ) THEN
    ALTER TABLE golf_course_contacts
    ADD CONSTRAINT golf_course_contacts_golf_course_id_fkey
    FOREIGN KEY (golf_course_id)
    REFERENCES golf_courses(id)
    ON DELETE CASCADE;
  END IF;
END $$;

-- ============================================================================
-- PART 8: Testing & Validation
-- ============================================================================

-- Test 1: Verify columns added
DO $$
DECLARE
  required_columns TEXT[] := ARRAY[
    'enrichment_status',
    'enrichment_requested_at',
    'enrichment_completed_at',
    'segment',
    'water_hazards',
    'opportunities',
    'agent_cost_usd'
  ];
  col TEXT;
BEGIN
  FOREACH col IN ARRAY required_columns
  LOOP
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'golf_courses' AND column_name = col
    ) THEN
      RAISE EXCEPTION 'Migration failed: Column % missing from golf_courses', col;
    END IF;
  END LOOP;

  RAISE NOTICE 'Migration validation passed: All required columns exist';
END $$;

-- Test 2: Verify indexes created
SELECT
  schemaname,
  tablename,
  indexname
FROM pg_indexes
WHERE tablename IN ('golf_courses', 'golf_course_contacts')
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- Test 3: Verify triggers created
SELECT
  trigger_name,
  event_manipulation,
  event_object_table,
  action_statement
FROM information_schema.triggers
WHERE trigger_name IN ('on_enrichment_requested', 'on_contact_inserted')
ORDER BY event_object_table, trigger_name;

-- ============================================================================
-- PART 9: Quick access queries for admins
-- ============================================================================

-- Check system health
-- SELECT * FROM v_enrichment_health;

-- See recent errors
-- SELECT * FROM v_enrichment_errors;

-- Check daily costs
-- SELECT * FROM v_daily_costs;

-- Check ClickUp sync
-- SELECT * FROM v_clickup_sync_status;

-- Get health metrics
-- SELECT * FROM get_enrichment_health(7);  -- Last 7 days

-- Reset stuck courses
-- SELECT reset_stuck_processing(15);  -- Reset courses processing > 15 min

-- ============================================================================
-- PART 10: Migration completion
-- ============================================================================

-- Log migration
INSERT INTO _migrations (name, applied_at)
VALUES ('004_agent_integration_fields', NOW())
ON CONFLICT (name) DO UPDATE SET applied_at = NOW();

-- Summary
DO $$
BEGIN
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Migration 004 Complete!';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Added to golf_courses:';
  RAISE NOTICE '  - enrichment_status (workflow control)';
  RAISE NOTICE '  - segment (high-end/budget/both)';
  RAISE NOTICE '  - opportunities (6 types scored)';
  RAISE NOTICE '  - water_hazards (retrieval scoring)';
  RAISE NOTICE '  - agent_cost_usd (cost tracking)';
  RAISE NOTICE '';
  RAISE NOTICE 'Added to golf_course_contacts:';
  RAISE NOTICE '  - email, phone, linkedin_url';
  RAISE NOTICE '  - tenure_years, previous_clubs';
  RAISE NOTICE '  - conversation_starters';
  RAISE NOTICE '  - clickup_task_id';
  RAISE NOTICE '';
  RAISE NOTICE 'Created 7 indexes for performance';
  RAISE NOTICE 'Created 2 triggers for automation';
  RAISE NOTICE 'Created 4 monitoring views';
  RAISE NOTICE 'Created 2 helper functions';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Next Steps:';
  RAISE NOTICE '  1. Deploy edge functions';
  RAISE NOTICE '  2. Test manual trigger:';
  RAISE NOTICE '     UPDATE golf_courses SET enrichment_status = ''pending'' WHERE id = ''test-uuid'';';
  RAISE NOTICE '  3. Monitor: SELECT * FROM v_enrichment_health;';
  RAISE NOTICE '========================================';
END $$;
