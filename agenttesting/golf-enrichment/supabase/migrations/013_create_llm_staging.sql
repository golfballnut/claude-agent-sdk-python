-- Migration 013: Create llm_research_staging table for V2 JSON inputs
-- Purpose: Staging table for manual V2 JSON paste → validation → database write workflow
-- Created: 2025-10-31

-- ============================================================================
-- STAGING TABLE: llm_research_staging
-- ============================================================================
-- Stores raw V2 JSON from LLM research prompt
-- Permanent storage for audit trail and re-processing capability

CREATE TABLE IF NOT EXISTS llm_research_staging (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id UUID REFERENCES golf_courses(id) ON DELETE CASCADE,
  course_name TEXT NOT NULL,
  state_code TEXT,
  v2_json JSONB NOT NULL,

  -- Processing tracking
  status TEXT CHECK (status IN ('pending', 'processing', 'validated', 'validation_failed')) DEFAULT 'pending',
  validation_error TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ,

  -- Ensure v2_json is a valid JSON object
  CONSTRAINT valid_json CHECK (jsonb_typeof(v2_json) = 'object')
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_staging_status ON llm_research_staging(status);
CREATE INDEX idx_staging_course_id ON llm_research_staging(course_id);
CREATE INDEX idx_staging_created_at ON llm_research_staging(created_at DESC);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE llm_research_staging IS 'Staging table for V2 LLM research JSON before validation and database write';
COMMENT ON COLUMN llm_research_staging.v2_json IS 'Raw JSON output from V2 research prompt (5 sections: tier, hazards, volume, contacts, intel)';
COMMENT ON COLUMN llm_research_staging.status IS 'Processing status: pending → processing → validated/validation_failed';
COMMENT ON COLUMN llm_research_staging.validation_error IS 'Error message if validation fails (structure issues, missing required fields)';

-- ============================================================================
-- TRIGGER FUNCTION: Call validate-v2-research edge function
-- ============================================================================

CREATE OR REPLACE FUNCTION call_validate_v2_research()
RETURNS TRIGGER AS $$
BEGIN
  -- Call edge function asynchronously via HTTP POST
  -- Edge function will fetch v2_json, call Render validator, update status
  PERFORM net.http_post(
    url := current_setting('app.supabase_url') || '/functions/v1/validate-v2-research',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.supabase_service_key')
    ),
    body := json_build_object(
      'staging_id', NEW.id,
      'course_id', NEW.course_id,
      'course_name', NEW.course_name,
      'state_code', NEW.state_code
    )::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION call_validate_v2_research IS 'HTTP POST to validate-v2-research edge function when v2_json is inserted';

-- ============================================================================
-- TRIGGER: Fire validation on JSON insert
-- ============================================================================

CREATE TRIGGER on_v2_json_inserted
AFTER INSERT ON llm_research_staging
FOR EACH ROW
WHEN (NEW.v2_json IS NOT NULL AND NEW.status = 'pending')
EXECUTE FUNCTION call_validate_v2_research();

COMMENT ON TRIGGER on_v2_json_inserted ON llm_research_staging IS 'Triggers validation edge function when V2 JSON is pasted into staging table';
