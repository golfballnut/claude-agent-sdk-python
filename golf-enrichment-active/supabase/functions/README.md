# LLM API Test Edge Functions - Deployment Guide

**Phase:** 2.5.1 - LLM API Automation Testing
**Created:** November 1, 2025
**Purpose:** Test Perplexity, Claude, and OpenAI APIs for automated golf course research

---

## Overview

This directory contains 3 Supabase Edge Functions that test different LLM APIs for automating golf course enrichment at scale:

1. **test-perplexity-research** - PRIMARY ($75 for 15k courses)
2. **test-claude-research** - FALLBACK #1 ($900 for 15k courses)
3. **test-openai-research** - FALLBACK #2 ($675 for 15k courses)

Each function:
- Takes course name and state code as input
- Calls the respective LLM API with the V2 research prompt
- Returns structured test results with quality metrics
- Tracks citations, contacts, tier classification, cost, and response time

---

## Prerequisites

### 1. Supabase CLI

```bash
# Install Supabase CLI if needed
npm install -g supabase

# Login to Supabase
supabase login

# Link to project
supabase link --project-ref oadmysogtfopkbmrulmq
```

### 2. API Keys

You'll need API keys for the LLM providers you want to test:

- **Perplexity API Key**: Get from https://www.perplexity.ai/settings/api
- **Anthropic API Key**: Get from https://console.anthropic.com/
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys

### 3. Database Migration

Apply the tracking table migration:

```bash
cd /Users/stevemcmillian/llama-3-agents/Apps/projects/claude-agent-sdk-python/agenttesting/golf-enrichment

# Apply migration 019 (creates llm_api_test_results table)
supabase db push
```

---

## Deployment Steps

### Step 1: Deploy Edge Functions

From the automation directory:

```bash
cd /Users/stevemcmillian/llama-3-agents/Apps/projects/claude-agent-sdk-python/agenttesting/golf-enrichment/automation/edge_functions

# Deploy all 3 functions
supabase functions deploy test-perplexity-research --project-ref oadmysogtfopkbmrulmq
supabase functions deploy test-claude-research --project-ref oadmysogtfopkbmrulmq
supabase functions deploy test-openai-research --project-ref oadmysogtfopkbmrulmq
```

### Step 2: Configure API Keys

Set the API keys as Supabase secrets:

```bash
# Perplexity (PRIMARY - test this first)
supabase secrets set PERPLEXITY_API_KEY="pplx-xxx" --project-ref oadmysogtfopkbmrulmq

# Anthropic (FALLBACK #1 - only if Perplexity fails)
supabase secrets set ANTHROPIC_API_KEY="sk-ant-xxx" --project-ref oadmysogtfopkbmrulmq

# OpenAI (FALLBACK #2 - only if both fail)
supabase secrets set OPENAI_API_KEY="sk-xxx" --project-ref oadmysogtfopkbmrulmq
```

### Step 3: Verify Deployment

```bash
# List deployed functions
supabase functions list --project-ref oadmysogtfopkbmrulmq

# Should show:
# - test-perplexity-research
# - test-claude-research
# - test-openai-research
```

---

## Testing the Functions

### Get Supabase Anon Key

```bash
# From Supabase Dashboard → Settings → API
# Or use: supabase status
```

### Test Perplexity (PRIMARY)

```bash
curl -X POST \
  "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/test-perplexity-research" \
  -H "Authorization: Bearer YOUR_SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "The Tradition Golf Club",
    "state_code": "NC",
    "city": "Charlotte"
  }'
```

**Expected Response:**

```json
{
  "success": true,
  "metadata": {
    "course_name": "The Tradition Golf Club",
    "state_code": "NC",
    "api_provider": "perplexity",
    "response_time_ms": 5234
  },
  "quality_metrics": {
    "citations_provided": true,
    "citation_count": 15,
    "citations_have_urls": true,
    "json_parsed_successfully": true,
    "has_tier_classification": true,
    "contact_count": 3
  },
  "cost_metrics": {
    "estimated_cost_usd": 0.005
  },
  "parsed_json": { ... },
  "validation": {
    "ready_for_staging": true,
    "issues": []
  }
}
```

### Test Claude (FALLBACK #1)

```bash
curl -X POST \
  "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/test-claude-research" \
  -H "Authorization: Bearer YOUR_SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "Forest Creek Golf Club",
    "state_code": "NC",
    "city": "Pinehurst"
  }'
```

### Test OpenAI (FALLBACK #2)

```bash
curl -X POST \
  "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/test-openai-research" \
  -H "Authorization: Bearer YOUR_SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "Hemlock Golf Course",
    "state_code": "NC",
    "city": "Walnut Cove"
  }'
```

---

## Phase 2.5.2: Running the 3-Course Pilot

### Test Courses

Per HANDOFF.md, test these 3 NC courses:

1. **The Tradition Golf Club** (Charlotte) - Premium tier, well-documented
2. **Forest Creek Golf Club** (Pinehurst) - Mid tier, golf resort area
3. **Hemlock Golf Course** (Walnut Cove) - Budget tier, limited data (stress test)

### Testing Workflow

**Step 1: Generate Test Run ID**

```bash
# In psql or Supabase SQL Editor
SELECT gen_random_uuid();
# Save this as TEST_RUN_ID for grouping
```

**Step 2: Test Perplexity on All 3 Courses**

For each course, call the Perplexity function and save the response to a file:

```bash
# Course 1: The Tradition
curl -X POST "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/test-perplexity-research" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"course_name": "The Tradition Golf Club", "state_code": "NC", "city": "Charlotte"}' \
  > results/perplexity_the_tradition.json

# Course 2: Forest Creek
curl -X POST "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/test-perplexity-research" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Forest Creek Golf Club", "state_code": "NC", "city": "Pinehurst"}' \
  > results/perplexity_forest_creek.json

# Course 3: Hemlock
curl -X POST "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/test-perplexity-research" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Hemlock Golf Course", "state_code": "NC", "city": "Walnut Cove"}' \
  > results/perplexity_hemlock.json
```

**Step 3: Insert Results into Tracking Table**

```sql
-- For each test result, insert into tracking table
INSERT INTO llm_api_test_results (
  test_run_id,
  api_provider,
  course_name,
  state_code,
  city,
  v2_json,
  raw_response,
  citations_provided,
  citation_count,
  tier_classification,
  contact_count,
  has_emails,
  response_time_ms,
  cost_usd,
  validation_status,
  validation_issues
) VALUES (
  'YOUR_TEST_RUN_ID',
  'perplexity',
  'The Tradition Golf Club',
  'NC',
  'Charlotte',
  '<parsed_json from response>',
  '<full raw_response>',
  true,  -- From quality_metrics.citations_provided
  15,    -- From quality_metrics.citation_count
  'premium',  -- From parsed_json.section5_course_tier.classification
  3,     -- From quality_metrics.contact_count
  true,  -- Check if any contacts have emails
  5234,  -- From metadata.response_time_ms
  0.005, -- From cost_metrics.estimated_cost_usd
  'pending',  -- Will update after manual review
  '[]'::jsonb  -- From validation.issues
);
```

**Step 4: Quality Assessment**

For each course, compare Perplexity result against manual ChatGPT-5 Pro baseline:

| Quality Metric | Weight | Pass Threshold |
|----------------|--------|----------------|
| **Citation Coverage** | CRITICAL | 100% of claims cited |
| **Citation Format** | CRITICAL | URLs provided, verifiable |
| **Tier Classification** | HIGH | Matches manual result |
| **Contact Count** | HIGH | ≥3 contacts |
| **Contact Quality** | HIGH | Email or LinkedIn for GM/Super |

Update quality scores:

```sql
UPDATE llm_api_test_results
SET
  quality_score = 85,  -- 0-100 manual assessment
  quality_notes = 'Tier matches baseline, 3 contacts found with emails, citations all verifiable',
  validation_status = 'pass'
WHERE id = '<result_id>';
```

**Step 5: Make GO/NO-GO Decision**

```sql
-- View test summary
SELECT
  course_name,
  citation_count,
  tier_classification,
  contact_count,
  has_emails,
  cost_usd,
  quality_score,
  validation_status
FROM llm_api_test_results
WHERE test_run_id = 'YOUR_TEST_RUN_ID'
  AND api_provider = 'perplexity'
ORDER BY course_name;
```

**Decision Matrix:**

```
IF all 3 courses pass CRITICAL checks (citations + tier accuracy):
  → Perplexity APPROVED ✅
  → SKIP Claude/OpenAI tests
  → PROCEED to Phase 2.6 (Full Automation)
  → Budget: $75 for 15,000 courses

ELSE IF any course fails citations OR tier:
  → Perplexity REJECTED ❌
  → PROCEED to test Claude on same 3 courses
  → Document failure reasons in quality_notes
```

---

## Troubleshooting

### Function Deployment Errors

```bash
# View function logs
supabase functions logs test-perplexity-research --project-ref oadmysogtfopkbmrulmq

# Common issues:
# - API key not set → Set via supabase secrets set
# - Permission errors → Check RLS policies on llm_api_test_results table
# - Timeout → Increase max_tokens or adjust prompt
```

### API Rate Limits

- **Perplexity**: 50 requests/day (free tier) or upgrade to Pro
- **Claude**: No hard rate limits with paid API access
- **OpenAI**: 500 requests/day (tier 1), easily sufficient for testing

### Citation Quality Issues

If Perplexity doesn't return citations:

1. Check `return_citations: true` is set in API call (already done in code)
2. Try adding `search_recency_filter: "month"` (already included)
3. Review raw API response in `raw_response` field
4. If still failing → Document and move to Claude test

---

## Cost Tracking

### Query Cost Summary

```sql
-- Total cost by API provider
SELECT
  api_provider,
  COUNT(*) as test_count,
  SUM(cost_usd) as total_cost,
  AVG(cost_usd) as avg_cost,
  SUM(cost_usd) * 15000 as estimated_full_cost
FROM llm_api_test_results
GROUP BY api_provider
ORDER BY total_cost ASC;
```

### Expected Costs (15,000 courses)

| API | Per Course | Total (15k) | Quality Expected |
|-----|-----------|-------------|------------------|
| Perplexity Sonar Pro | $0.005 | **$75** | Good (if citations work) |
| Claude Sonnet 4.5 | $0.060 | **$900** | Excellent |
| OpenAI GPT-4o | $0.045 | **$675** | Matches manual baseline |

---

## Next Steps After Testing

### If Perplexity Passes

1. Generate comparison report (even with just Perplexity data)
2. Present to user for approval
3. Get budget approval ($75)
4. Proceed to Phase 2.6: Build production batch automation

### If Need to Test Claude/OpenAI

1. Repeat testing workflow for fallback APIs
2. Generate full comparison report across all tested APIs
3. Present recommendation with cost-benefit analysis
4. Get user approval on selected API and budget
5. Proceed to Phase 2.6

---

## File Structure

```
automation/edge_functions/
├── README.md (this file)
├── test-perplexity-research/
│   └── index.ts
├── test-claude-research/
│   └── index.ts
└── test-openai-research/
    └── index.ts

automation/api_testing/
├── perplexity_<course>.json  # Raw test results
├── claude_<course>.json
├── openai_<course>.json
└── comparison_report.md      # Final recommendation

supabase/migrations/
└── 019_create_llm_api_test_results.sql
```

---

## References

- **HANDOFF.md**: `/automation/HANDOFF.md` - Current session status
- **PROGRESS.md**: `/docs/PROGRESS.md` - Complete Phase 2.5 plan
- **V2 Prompt**: `/prompts/enhanced_research_v1.md` - Research template
- **API Docs**: `/automation/docs/api_references/` - API specifications

---

**Status:** Phase 2.5.1 Complete - Edge functions ready for deployment
**Next:** Deploy functions, set API keys, run 3-course pilot test
