-- Migration 007: Add agent_cost_usd to TEST tables
-- Purpose: Fix missing agent_cost_usd column in test_golf_courses
-- Date: October 20, 2025
--
-- Background: Test tables were created before migration 004 was applied
-- This adds the missing cost tracking column to test tables only

-- Add to test_golf_courses
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS
  agent_cost_usd DECIMAL(10,4);

COMMENT ON COLUMN test_golf_courses.agent_cost_usd IS 'Total cost in USD for agent enrichment workflow';

-- Verify column exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'test_golf_courses' AND column_name = 'agent_cost_usd'
  ) THEN
    RAISE EXCEPTION 'Migration failed: agent_cost_usd column not added to test_golf_courses';
  END IF;

  RAISE NOTICE 'Migration 007 complete: agent_cost_usd added to test_golf_courses';
END $$;
