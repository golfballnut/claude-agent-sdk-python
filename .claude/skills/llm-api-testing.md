# LLM API Testing for Golf Course Automation

Systematic methodology for testing Perplexity/Claude/OpenAI APIs to automate 15,000 course enrichment pipeline. Validates citation quality, data accuracy, and cost-effectiveness before full automation deployment.

## When to Use This Skill

Use when:
- Starting Phase 2.5 (LLM API automation testing)
- User asks to "test Perplexity API" or "compare LLM APIs"
- Building automation infrastructure for golf course enrichment
- Evaluating citation quality from automated LLM research

DO NOT use when:
- Manual testing with ChatGPT (that's complete)
- Working on validator service (already deployed)
- Database schema changes (migrations complete)
- ClickUp integration (already working)

## Prerequisites Check

Before starting, verify infrastructure is complete:

```sql
-- Verify staging table exists
SELECT COUNT(*) FROM llm_research_staging;

-- Verify Render validator is live
-- Check: https://agent7-water-hazards.onrender.com/health

-- Verify edge function deployed
SELECT * FROM supabase.functions WHERE name = 'validate-v2-research';
```

**Required:**
- ✅ llm_research_staging table exists
- ✅ Render validator responding at /validate-and-write
- ✅ validate-v2-research edge function deployed
- ✅ V2 prompt at `/prompts/v2_research_prompt.md`
- ✅ API keys available (user will provide)

## Execution Protocol

### STEP 1: Fetch Latest API Documentation

**Use Context7 for official specs:**

```typescript
// Fetch Perplexity docs
mcp__context7__resolve-library-id({ libraryName: "perplexity api" })
// Select: /ppl-ai/api-cookbook (Trust Score: 9)

mcp__context7__get-library-docs({
  context7CompatibleLibraryID: "/ppl-ai/api-cookbook",
  topic: "sonar-pro model, return_citations, chat completions",
  tokens: 3000
})

// Fetch Claude docs
mcp__context7__resolve-library-id({ libraryName: "anthropic claude api" })
// Select: /docs.anthropic.com-7a01857/llmstxt (56,960 snippets)

mcp__context7__get-library-docs({
  context7CompatibleLibraryID: "/docs.anthropic.com-7a01857/llmstxt",
  topic: "claude-sonnet-4.5, messages API, system prompts",
  tokens: 3000
})

// Fetch OpenAI docs
mcp__context7__resolve-library-id({ libraryName: "openai api" })
// Select: /websites/platform_openai (Trust Score: 9.5, 382k snippets)

mcp__context7__get-library-docs({
  context7CompatibleLibraryID: "/websites/platform_openai",
  topic: "gpt-4o, chat completions, JSON mode, response_format",
  tokens: 3000
})
```

**Update API reference files with official docs**

### STEP 2: Build Test Infrastructure (Phase 2.5.1)

**Create 3 test edge functions:**

1. **test-perplexity-research**
   - Location: `/automation/edge_functions/test-perplexity-research/index.ts`
   - API: Perplexity Sonar Pro
   - **CRITICAL:** Set `return_citations: true`

2. **test-claude-research**
   - Location: `/automation/edge_functions/test-claude-research/index.ts`
   - API: Claude Sonnet 4.5
   - **CRITICAL:** Use `system` parameter for V2 prompt

3. **test-openai-research**
   - Location: `/automation/edge_functions/test-openai-research/index.ts`
   - API: OpenAI GPT-4o
   - **CRITICAL:** Use `response_format: { type: "json_object" }`

**Deploy all 3:**
```bash
cd /automation/edge_functions
supabase functions deploy test-perplexity-research
supabase functions deploy test-claude-research
supabase functions deploy test-openai-research
```

**Configure secrets:**
```bash
supabase secrets set PERPLEXITY_API_KEY=<key>
supabase secrets set ANTHROPIC_API_KEY=<key>
supabase secrets set OPENAI_API_KEY=<key>
```

**Create tracking table:**
```sql
CREATE TABLE llm_api_test_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_run_id UUID NOT NULL,
  api_provider TEXT NOT NULL,
  course_name TEXT NOT NULL,
  v2_json JSONB,
  citations_provided BOOLEAN,
  citation_count INTEGER,
  tier_classification TEXT,
  contact_count INTEGER,
  has_emails BOOLEAN,
  response_time_ms INTEGER,
  cost_usd NUMERIC(10,4),
  quality_score INTEGER,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### STEP 3: Test Perplexity API (PRIMARY)

**Test 3 diverse NC courses:**
1. The Tradition Golf Club (Charlotte - well-documented)
2. Forest Creek Golf Club (Pinehurst - moderate docs)
3. Hemlock Golf Course (Walnut Cove - limited docs)

**For each course:**

1. **Call API:**
   ```bash
   curl -X POST "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/test-perplexity-research" \
     -H "Authorization: Bearer <anon-key>" \
     -H "Content-Type: application/json" \
     -d '{"course_name": "<COURSE>", "state_code": "NC"}'
   ```

2. **Save response:**
   - File: `/automation/api_testing/perplexity/<course_name>.json`

3. **Validate citations (CRITICAL):**
   ```typescript
   const citations = response.citations || []
   const citations_valid = citations.length >= 3 &&
                          citations.every(c => c.startsWith('http'))
   ```

4. **Test with validator:**
   ```bash
   curl -X POST "https://agent7-water-hazards.onrender.com/validate-and-write" \
     -H "Content-Type: application/json" \
     -d '{
       "staging_id": "<uuid>",
       "course_name": "<name>",
       "state_code": "NC",
       "v2_json": <perplexity_response>
     }'
   ```

5. **Score quality (0-100):**
   - Citations present with URLs: +40 points (CRITICAL)
   - Tier matches manual baseline: +20 points
   - Contact count ≥3: +20 points
   - Email/LinkedIn for GM: +10 points
   - Volume estimate reasonable: +10 points

**Pass threshold: ≥80 points**

### STEP 4: Decision Gate #1

```
IF all 3 courses score ≥80 AND citations valid:
  ✅ Perplexity APPROVED
  ✅ SKIP Claude and OpenAI tests (save time + money)
  ✅ PROCEED to Phase 2.6 (full automation)
  ✅ Budget: $75 for 15,000 courses

ELSE IF citations missing OR tier accuracy <90%:
  ❌ Perplexity REJECTED
  ⏭️  PROCEED to STEP 5 (Claude test)
```

### STEP 5: Test Claude API (FALLBACK #1)

**ONLY IF PERPLEXITY FAILS**

- Repeat STEP 3 with Claude API
- Same 3 courses, same quality checks
- Budget: $900 for 15,000 courses

**Decision Gate #2:**
```
IF Claude scores ≥80 AND citations valid:
  ✅ Claude APPROVED
  ✅ SKIP OpenAI test
  ✅ PROCEED to Phase 2.6

ELSE:
  ⏭️  PROCEED to STEP 6 (OpenAI test)
```

### STEP 6: Test OpenAI API (FALLBACK #2)

**ONLY IF BOTH PERPLEXITY AND CLAUDE FAIL**

- Repeat STEP 3 with OpenAI GPT-4o
- Should match manual quality (same model as ChatGPT-5 Pro)
- Budget: $675 for 15,000 courses

**Expected:** 100% match to manual baseline

### STEP 7: Generate Comparison Report

**Create:** `/automation/api_testing/comparison_report.md`

**Include:**
| API | Citations | Tier Accuracy | Avg Contacts | Quality Score | Cost/15k | Recommendation |
|-----|-----------|---------------|--------------|---------------|----------|----------------|
| Perplexity | ✅/❌ | X/3 | X.X | XX/100 | $75 | Use/Skip |
| Claude | ✅/❌ | X/3 | X.X | XX/100 | $900 | Use/Skip |
| OpenAI | ✅/❌ | X/3 | X.X | XX/100 | $675 | Use/Skip |

**Recommendation:**
- Selected API: <name>
- Rationale: <citation quality + cost-benefit>
- Budget request: $<amount>
- Timeline: 52 days unattended

### STEP 8: User Approval Required

Present comparison report to user and ask:
- ✅ Approve selected API?
- ✅ Approve budget ($75-900)?
- ✅ Approve 52-day timeline?
- ✅ Proceed to Phase 2.6?

**If approved → STEP 9 (build production automation)**

### STEP 9: Build Production Automation (Phase 2.6)

**Create:** `/automation/edge_functions/batch-llm-research/index.ts`

**Features:**
- Fetches 10 courses from queue per batch
- Calls selected API with V2 prompt
- Writes to llm_research_staging
- Triggers existing validator pipeline automatically
- Rate limits to 12 requests/hour (safe)
- Handles errors gracefully

**Deploy:**
```bash
supabase functions deploy batch-llm-research

# Schedule via Supabase dashboard cron:
# */5 * * * * (every 5 minutes)
```

**Monitor first 100 courses:**
```sql
SELECT
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE status='validated') as successful,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status='validated') / COUNT(*), 1) as success_rate
FROM llm_research_staging
WHERE created_at > NOW() - INTERVAL '24 hours';
```

**Success criteria:** ≥90% validation success rate

### STEP 10: Switch to Production Tables

**After 100 successful automated courses:**

```bash
# Via Render MCP or dashboard
USE_TEST_TABLES=false
```

**Verify ClickUp integration:**
- Course record written → Contact inserted → ClickUp tasks created (automatic)

### STEP 11: Full Production Run

**Let automation run unattended:**
- 15,000 courses ÷ 12/hour = 1,250 hours = 52 days
- Weekly quality spot-checks (10 random courses)
- Monitor costs vs budget
- Handle validation failures (retry up to 3x)

## Success Criteria

**Phase 2.5 Complete:**
- ✅ All 3 APIs tested on same 3 courses
- ✅ Citations validated (URLs present and verifiable)
- ✅ Best API selected based on quality + cost
- ✅ User approved budget and timeline
- ✅ Comparison report documented

**Phase 2.6 Complete:**
- ✅ Batch automation deployed and scheduled
- ✅ First 100 courses ≥90% validation success
- ✅ Production tables enabled
- ✅ ClickUp tasks created automatically
- ✅ 15,000 courses enriched in 52 days
- ✅ Total cost within budget ($75-900)

## Critical Validations

**Citations Check (MOST IMPORTANT):**
```typescript
function validateCitations(response: any): boolean {
  // Perplexity
  if (response.citations) {
    return response.citations.length >= 3 &&
           response.citations.every(c => c.startsWith('http'))
  }

  // Claude/OpenAI
  const v2_json = JSON.parse(response.choices[0].message.content)
  const has_tier_citations = v2_json.section1?.tier_citations?.length >= 1
  const has_hazard_citations = v2_json.section2?.hazards_citations?.length >= 1
  const has_intel_citations = v2_json.section5?.intelligence_citations?.length >= 1

  return has_tier_citations && has_hazard_citations && has_intel_citations
}
```

**If citations fail → REJECT that API immediately**

## Troubleshooting

### Problem: Perplexity doesn't return citations
**Check:** `return_citations: true` in request body
**Fix:** Verify parameter is set, check API response format

### Problem: Claude/OpenAI citations generic
**Check:** V2 prompt instructs to include URLs in *_citations arrays
**Fix:** Enhance prompt with explicit citation URL instructions

### Problem: Rate limit exceeded
**Check:** Free tier limits (50/day Perplexity, varies OpenAI/Claude)
**Fix:** Upgrade to Pro tier OR add delays between requests

### Problem: Validation success rate <90%
**Check:** V2 JSON structure matches validator expectations
**Fix:** Debug parser errors, adjust API prompt formatting

### Problem: Costs exceed budget
**Check:** Token usage vs estimates
**Fix:** Reduce prompt size, optimize max_tokens, switch to cheaper API

## Files This Skill Works With

**Read:**
- `/automation/CURRENT_PHASE.md` - Confirms Phase 2.5 active
- `/automation/docs/phase_2.5_plan.md` - Complete test plan
- `/automation/docs/api_references/<api>.md` - Official API specs
- `/prompts/v2_research_prompt.md` - Active prompt

**Create:**
- `/automation/edge_functions/test-*-research/` - Test functions
- `/automation/api_testing/<api>/<course>.json` - Test results
- `/automation/api_testing/comparison_report.md` - Final report

**Update:**
- `/docs/PROGRESS.md` - Add Session 10 results

## Expected Timeline

- **Phase 2.5.1:** Build infrastructure - 1-2 hours
- **Phase 2.5.2:** Test Perplexity - 30 minutes
- **Phase 2.5.3:** Test Claude (if needed) - 30 minutes
- **Phase 2.5.4:** Test OpenAI (if needed) - 30 minutes
- **Phase 2.5.5:** Generate report - 15 minutes
- **User decision:** 1-24 hours
- **Phase 2.6:** Build production - 2 hours
- **Total:** 5-6 hours of agent work + user approval time

## Cost Analysis Reference

| Scenario | API Selected | Cost | Time Saved | ROI |
|----------|--------------|------|------------|-----|
| Best case | Perplexity | $75 | 2,500 hours | $124,925 |
| Good case | OpenAI | $675 | 2,500 hours | $124,325 |
| Acceptable case | Claude | $900 | 2,500 hours | $124,100 |
| Worst case | Manual | $125k opportunity cost | 0 | -$125,000 |

**Any automation option has 1,000x+ ROI**

## Quality Benchmarks (From Manual Testing)

Agents should compare API results against these proven baselines:

| Metric | Manual ChatGPT-5 Pro Result |
|--------|----------------------------|
| Tier Classification Accuracy | 100% (3/3 courses) |
| Contact Count Average | 3-4 per course |
| Citation Coverage | 100% (every claim sourced) |
| Email Discovery | Varies by course (realistic) |
| Water Hazard Detail | Hole-by-hole with evidence |
| Volume Estimates | 22k-55k with reasoning |

**API must achieve ≥80% of manual quality to be approved**

## Final Deliverable

**Comparison Report Must Include:**
1. Test results table (all 3 APIs, 3 courses each)
2. Citation quality assessment with examples
3. Cost-benefit analysis
4. Recommended API with rationale
5. Budget request for user approval
6. Next steps (Phase 2.6 if approved)

---

**Status:** Ready for Phase 2.5.1 execution
**Next Action:** Use Context7 to fetch API docs, then build test edge functions
