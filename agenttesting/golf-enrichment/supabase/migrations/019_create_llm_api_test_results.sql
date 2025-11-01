-- Migration 019: Create LLM API Test Results Table
-- Phase 2.5.1: Track API testing results for Perplexity, Claude, and OpenAI
-- Purpose: Store test data for comparison and decision-making

-- Create llm_api_test_results table
CREATE TABLE IF NOT EXISTS llm_api_test_results (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Test grouping (allows grouping 3 courses together for comparison)
  test_run_id UUID NOT NULL,

  -- Test metadata
  api_provider TEXT NOT NULL CHECK (api_provider IN ('perplexity', 'claude', 'openai')),
  course_name TEXT NOT NULL,
  state_code TEXT,
  city TEXT,

  -- Raw data
  v2_json JSONB,
  raw_response JSONB,  -- Full API response for debugging

  -- Quality metrics
  citations_provided BOOLEAN DEFAULT false,
  citation_count INTEGER DEFAULT 0,
  tier_classification TEXT,
  contact_count INTEGER DEFAULT 0,
  has_emails BOOLEAN DEFAULT false,
  has_linkedin BOOLEAN DEFAULT false,

  -- Performance metrics
  response_time_ms INTEGER,

  -- Cost tracking
  cost_usd NUMERIC(10,4),
  input_tokens INTEGER,
  output_tokens INTEGER,

  -- Manual quality assessment
  quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100),
  quality_notes TEXT,

  -- Validation status
  validation_status TEXT CHECK (validation_status IN ('pending', 'pass', 'fail')),
  validation_issues JSONB,  -- Array of issue descriptions

  -- Additional notes
  notes TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_llm_test_run_id ON llm_api_test_results(test_run_id);
CREATE INDEX idx_llm_api_provider ON llm_api_test_results(api_provider);
CREATE INDEX idx_llm_course_name ON llm_api_test_results(course_name);
CREATE INDEX idx_llm_created_at ON llm_api_test_results(created_at DESC);

-- Enable RLS (Row Level Security)
ALTER TABLE llm_api_test_results ENABLE ROW LEVEL SECURITY;

-- Policy: Allow service role full access
CREATE POLICY "Service role has full access to llm_api_test_results"
  ON llm_api_test_results
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Policy: Allow authenticated users to read test results
CREATE POLICY "Authenticated users can read llm_api_test_results"
  ON llm_api_test_results
  FOR SELECT
  TO authenticated
  USING (true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_llm_test_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER llm_test_update_timestamp
  BEFORE UPDATE ON llm_api_test_results
  FOR EACH ROW
  EXECUTE FUNCTION update_llm_test_updated_at();

-- Helpful views for analysis

-- View: Latest test results by provider
CREATE OR REPLACE VIEW v_llm_test_latest AS
SELECT DISTINCT ON (api_provider, course_name)
  id,
  test_run_id,
  api_provider,
  course_name,
  state_code,
  citation_count,
  contact_count,
  tier_classification,
  cost_usd,
  response_time_ms,
  quality_score,
  validation_status,
  created_at
FROM llm_api_test_results
ORDER BY api_provider, course_name, created_at DESC;

-- View: Test comparison summary
CREATE OR REPLACE VIEW v_llm_test_comparison AS
SELECT
  test_run_id,
  COUNT(*) as total_tests,
  COUNT(*) FILTER (WHERE api_provider = 'perplexity') as perplexity_tests,
  COUNT(*) FILTER (WHERE api_provider = 'claude') as claude_tests,
  COUNT(*) FILTER (WHERE api_provider = 'openai') as openai_tests,
  AVG(citation_count) as avg_citations,
  AVG(contact_count) as avg_contacts,
  AVG(cost_usd) as avg_cost,
  AVG(response_time_ms) as avg_response_time,
  AVG(quality_score) as avg_quality_score
FROM llm_api_test_results
GROUP BY test_run_id
ORDER BY MAX(created_at) DESC;

-- Comments for documentation
COMMENT ON TABLE llm_api_test_results IS 'Phase 2.5.1: Stores API test results for Perplexity, Claude, and OpenAI comparison';
COMMENT ON COLUMN llm_api_test_results.test_run_id IS 'Groups 3 courses together for cross-API comparison';
COMMENT ON COLUMN llm_api_test_results.quality_score IS 'Manual 0-100 quality assessment vs baseline';
COMMENT ON COLUMN llm_api_test_results.validation_issues IS 'JSON array of validation failure reasons';
