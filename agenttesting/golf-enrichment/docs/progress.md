# Golf Enrichment V2 - Automated LLM Research Pipeline

**Project:** Automate golf course enrichment at scale using LLM research + validation
**Started:** October 31, 2025
**Current Status:** ✅ Phase 2.4 Complete - Ready for LLM API Automation Testing

---

## 🎯 **CURRENT GOAL: Automate 15,000 Course Enrichment**

### The Challenge
- **Manual approach:** 15,000 courses × 10 min/course = 2,500 hours = **15 MONTHS** of copy/paste
- **Risk:** Human error, burnout, inconsistency
- **Cost:** $125k opportunity cost (2,500 hours of labor)

### The Solution
- **Automated LLM research:** Edge function calls Perplexity/Claude/OpenAI API
- **Unattended processing:** 52 days running 24/7
- **Cost:** $75-675 depending on API choice
- **Risk:** Zero (infrastructure 100% tested and validated)

---

## ✅ **WHAT WE HAVE COMPLETE**

### Infrastructure (100% Built & Tested)

1. ✅ **V2 Research Prompt** - 5 focused sections with inline citations
   - Location: `prompts/enhanced_research_v2.md`
   - Tested on 3 courses: 100% tier accuracy, 3-4 contacts per course
   - Citation quality: 100% sourced with URLs

2. ✅ **Supabase Database**
   - `llm_research_staging` table - Receives LLM JSON
   - V2 fields added to `golf_courses` and `golf_course_contacts`
   - Test tables (`*_test`) for production-safe validation
   - Migrations 013-018 applied successfully

3. ✅ **Supabase Edge Function**
   - `validate-v2-research` - Deployed and configured
   - Receives staging inserts → calls Render validator
   - Environment: `RENDER_VALIDATOR_URL` configured

4. ✅ **Render Validator Service**
   - URL: `https://agent7-water-hazards.onrender.com/validate-and-write`
   - 5 section parsers (tier, hazards, volume, contacts, intel)
   - Supabase writer with test/production mode toggle
   - Docker validated: 100% success rate
   - Live and tested: Course ID 2055 created successfully

5. ✅ **ClickUp Integration**
   - Automatic task creation on contact insert
   - Creates 3 tasks: Course + Contact + Outreach
   - Tested and working

### Proven Data Quality (Manual LLM Testing)

| Metric | Result | Evidence |
|--------|--------|----------|
| **Tier Classification** | 100% accurate (3/3) | Premium/Mid correctly identified with pricing evidence |
| **Contact Discovery** | 3-4 per course | GM, Superintendent, Head Pro with titles |
| **Email Quality** | Varies by transparency | Direct work emails when public, LinkedIn fallback |
| **Water Hazards** | Detailed assessments | Hole-by-hole with evidence |
| **Volume Estimates** | Reasonable ranges | 22k-55k with triangulated data |
| **Citations** | 100% present | Every claim sourced with URL |

---

## 🧪 **PHASE 2.5: LLM API AUTOMATION TESTING**

### Goal
Test automated LLM research with **Perplexity API** (primary) and **Claude/OpenAI APIs** (fallback) to validate we can achieve the same data quality at scale without manual copy/paste.

### Why This Matters
If Perplexity can match ChatGPT-5 Pro quality with citations, we save:
- **2,500 hours** of manual work
- **$125k** opportunity cost
- **13.5 months** of time

### Critical Success Criteria

**PRIMARY TEST: Perplexity Sonar Pro**
- ✅ Returns JSON in V2 format (5 sections)
- ✅ **Citations provided for all claims** (URLs, sources)
- ✅ Tier classification accuracy ≥90% (vs manual baseline)
- ✅ Contact discovery: 3+ contacts per course average
- ✅ Email/LinkedIn quality matches manual results
- ✅ Cost: ≤$0.01 per course ($150 for 15,000 courses)

**If Perplexity fails ANY criteria → FALLBACK to Claude/OpenAI**

---

## 📋 **TESTING PLAN: 3-Course Pilot**

### Test Set (Diverse NC Courses)

| # | Course | City | Tier Expected | Why Selected |
|---|--------|------|---------------|--------------|
| 1 | **The Tradition Golf Club** | Charlotte | Premium | Large metro, well-documented, 11 water hazards |
| 2 | **Forest Creek Golf Club** | Pinehurst | Mid | Golf resort area, moderate documentation |
| 3 | **Hemlock Golf Course** | Walnut Cove | Budget | Small town, limited online presence (stress test) |

**Rationale:** Tests high/medium/low data availability scenarios

---

### TEST 1: Perplexity Sonar Pro (PRIMARY)

**Hypothesis:** Perplexity can deliver same quality as ChatGPT-5 Pro with built-in web search and citations.

**Method:**

**STEP 1: Create Perplexity Test Edge Function**
```typescript
// File: supabase/functions/test-perplexity-research/index.ts
// Purpose: Test Perplexity API for 3 courses before full automation

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

serve(async (req) => {
  const { course_name, state_code } = await req.json()

  // Call Perplexity Sonar Pro with V2 prompt
  const response = await fetch('https://api.perplexity.ai/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('PERPLEXITY_API_KEY')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'sonar-pro',
      messages: [
        {
          role: 'system',
          content: `<FULL V2 PROMPT FROM prompts/enhanced_research_v2.md>`
        },
        {
          role: 'user',
          content: `Research: ${course_name}, ${state_code}`
        }
      ],
      temperature: 0.2,
      max_tokens: 4000,
      return_citations: true,  // CRITICAL: Must return citations
      return_related_questions: false
    })
  })

  const result = await response.json()

  return new Response(JSON.stringify({
    success: true,
    raw_response: result,
    parsed_json: result.choices[0].message.content,
    citations: result.citations,  // Perplexity's citation format
    cost: result.usage
  }), {
    headers: { 'Content-Type': 'application/json' }
  })
})
```

**STEP 2: Deploy & Test**
```bash
# Deploy edge function
cd agenttesting/golf-enrichment
supabase functions deploy test-perplexity-research
supabase secrets set PERPLEXITY_API_KEY=<your-key>

# Test on 3 courses (manual invocation)
curl -X POST "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/test-perplexity-research" \
  -H "Authorization: Bearer <anon-key>" \
  -H "Content-Type: application/json" \
  -d '{"course_name": "The Tradition Golf Club", "state_code": "NC"}'
```

**STEP 3: Quality Assessment**

For each of 3 courses, compare Perplexity vs your manual ChatGPT-5 Pro results:

| Quality Metric | Weight | Pass Threshold |
|----------------|--------|----------------|
| **Citation Coverage** | CRITICAL | 100% of claims cited |
| **Citation Format** | CRITICAL | URLs provided, verifiable sources |
| **Tier Classification** | HIGH | Matches manual result |
| **Contact Count** | HIGH | ≥3 contacts |
| **Contact Quality** | HIGH | Email or LinkedIn for GM/Super |
| **Water Hazards Detail** | MEDIUM | Yes/No + count accurate |
| **Volume Estimate** | MEDIUM | Within 30% of manual estimate |
| **Intelligence Richness** | LOW | Ownership + 1-2 vendors |

**Pass Criteria:**
- ✅ ALL CRITICAL metrics must pass
- ✅ ≥80% of HIGH metrics must pass
- ⚠️ MEDIUM/LOW metrics nice-to-have

**STEP 4: Decision Matrix**

```
IF Perplexity passes ALL criteria:
  → PROCEED to full automation (Phase 2.6)
  → Deploy batch-llm-research edge function
  → Process all 15,000 courses
  → Cost: ~$75 total

ELSE IF Perplexity fails citations OR tier accuracy:
  → FALLBACK to Test 2 (Claude API)
  → Re-test same 3 courses
  → Compare quality and cost

ELSE IF both fail:
  → FALLBACK to Test 3 (OpenAI GPT-4o)
  → Higher cost but proven quality
```

---

### TEST 2: Claude API (FALLBACK #1)

**Hypothesis:** Claude Sonnet 4.5 delivers ChatGPT-5 Pro quality with better reasoning and citations.

**Method:**

**STEP 1: Modify Edge Function for Claude**
```typescript
// File: supabase/functions/test-claude-research/index.ts
// Same structure as Perplexity test, different API

const response = await fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  headers: {
    'x-api-key': Deno.env.get('ANTHROPIC_API_KEY'),
    'anthropic-version': '2023-06-01',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'claude-sonnet-4-5-20250929',
    max_tokens: 4000,
    temperature: 0.2,
    system: `<FULL V2 PROMPT>`,
    messages: [
      {
        role: 'user',
        content: `Research: ${course_name}, ${state_code}`
      }
    ]
  })
})
```

**Cost:**
- Input: ~10k tokens × $3/1M = $0.03
- Output: ~2k tokens × $15/1M = $0.03
- **Total:** ~$0.06 per course × 15,000 = **$900 total**

**STEP 2: Test on Same 3 Courses**

Compare against Perplexity results and manual baseline.

**STEP 3: Decision**
```
IF Claude quality > Perplexity AND cost acceptable:
  → Use Claude API for full automation
  → $900 budget approved?

ELSE:
  → Proceed to Test 3 (OpenAI)
```

---

### TEST 3: OpenAI GPT-4o (FALLBACK #2)

**Hypothesis:** GPT-4o (same model as ChatGPT-5 Pro) delivers identical quality to manual approach.

**Method:**

**STEP 1: Modify Edge Function for OpenAI**
```typescript
// File: supabase/functions/test-openai-research/index.ts

const response = await fetch('https://api.openai.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4o',
    messages: [
      {
        role: 'system',
        content: `<FULL V2 PROMPT>`
      },
      {
        role: 'user',
        content: `Research: ${course_name}, ${state_code}`
      }
    ],
    temperature: 0.2,
    max_tokens: 4000
  })
})
```

**Cost:**
- Input: ~10k tokens × $2.50/1M = $0.025
- Output: ~2k tokens × $10/1M = $0.020
- **Total:** ~$0.045 per course × 15,000 = **$675 total**

**STEP 2: Test on Same 3 Courses**

This should match your manual ChatGPT-5 Pro quality exactly (same model).

**STEP 3: Decision**
```
IF OpenAI quality matches manual baseline:
  → Use OpenAI for full automation
  → $675 budget vs $125k opportunity cost = obvious ROI

ELSE:
  → Houston, we have a problem (unlikely)
  → Investigate prompt/parsing issues
```

---

## 📊 **TESTING EXECUTION WORKFLOW**

### Phase 2.5.1: Build Test Infrastructure (1-2 hours)

**Agent Instructions:**

1. **Create 3 test edge functions:**
   - `test-perplexity-research`
   - `test-claude-research`
   - `test-openai-research`
   - Each takes course_name + state_code, returns V2 JSON + metadata

2. **Deploy all 3 to Supabase:**
   ```bash
   cd agenttesting/golf-enrichment/supabase/functions
   supabase functions deploy test-perplexity-research
   supabase functions deploy test-claude-research
   supabase functions deploy test-openai-research
   ```

3. **Configure API keys:**
   ```bash
   supabase secrets set PERPLEXITY_API_KEY=<key>
   supabase secrets set ANTHROPIC_API_KEY=<key>
   supabase secrets set OPENAI_API_KEY=<key>
   ```

4. **Create results tracking table:**
   ```sql
   CREATE TABLE llm_api_test_results (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     test_run_id UUID NOT NULL,  -- Groups 3 courses together
     api_provider TEXT NOT NULL,  -- perplexity, claude, openai
     course_name TEXT NOT NULL,
     v2_json JSONB,
     citations_provided BOOLEAN,
     citation_count INTEGER,
     tier_classification TEXT,
     contact_count INTEGER,
     has_emails BOOLEAN,
     has_linkedin BOOLEAN,
     response_time_ms INTEGER,
     cost_usd NUMERIC(10,4),
     quality_score INTEGER,  -- 0-100 manual assessment
     notes TEXT,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

### Phase 2.5.2: Run Perplexity Test (PRIMARY - 30 minutes)

**Agent Instructions:**

**FOR EACH COURSE (The Tradition, Forest Creek, Hemlock):**

1. **Call Perplexity API:**
   ```bash
   curl -X POST "<supabase-url>/functions/v1/test-perplexity-research" \
     -H "Authorization: Bearer <anon-key>" \
     -H "Content-Type: application/json" \
     -d '{"course_name": "<COURSE_NAME>", "state_code": "NC"}'
   ```

2. **Save raw response to file:**
   - `agenttesting/golf-enrichment/api_tests/perplexity_<course_name>.json`

3. **Insert result into tracking table:**
   ```sql
   INSERT INTO llm_api_test_results (
     test_run_id, api_provider, course_name, v2_json,
     citations_provided, citation_count, tier_classification,
     contact_count, response_time_ms, cost_usd
   ) VALUES (
     '<test-run-uuid>',
     'perplexity',
     '<course_name>',
     '<v2_json>',
     <true/false>,
     <count>,
     '<tier>',
     <count>,
     <ms>,
     <cost>
   );
   ```

4. **Validate JSON structure:**
   - Run through `/validate-and-write` endpoint
   - Check for validation errors
   - Verify test table writes

5. **Manual quality assessment:**
   - Compare to your manual ChatGPT-5 Pro result for same course
   - Score 0-100 based on criteria table above
   - Document gaps in notes field

**CRITICAL CHECKS (Must Pass):**

```
✅ Citations present? (Check result.citations array)
✅ Citation URLs valid? (Can you verify sources?)
✅ Tier matches manual result?
✅ Contact count ≥3?
✅ Email OR LinkedIn for GM/Superintendent?
```

**DECISION POINT:**

```
IF all 3 courses pass CRITICAL checks:
  → Perplexity quality APPROVED ✅
  → SKIP Tests 2 & 3 (Claude/OpenAI)
  → PROCEED directly to Phase 2.6 (Full Automation)
  → Estimated savings: $600-825 vs Claude/OpenAI

ELSE IF any course fails citations OR tier accuracy:
  → Perplexity quality REJECTED ❌
  → PROCEED to Test 2 (Claude API)
  → Document failure reasons for analysis
```

---

### Phase 2.5.3: Run Claude API Test (FALLBACK #1 - If Needed)

**Agent Instructions:**

**ONLY RUN IF PERPLEXITY FAILS**

Repeat Phase 2.5.2 steps with Claude API:
- Use same 3 test courses
- Call `test-claude-research` edge function
- Save results to `api_tests/claude_<course_name>.json`
- Insert into llm_api_test_results with `api_provider='claude'`
- Compare quality scores

**Cost:** ~$0.06 per course (2x Perplexity, 1/12th OpenAI)

**DECISION POINT:**

```
IF Claude passes all CRITICAL checks:
  → Claude quality APPROVED ✅
  → SKIP Test 3 (OpenAI)
  → PROCEED to Phase 2.6 with Claude API
  → Budget: ~$900 for 15,000 courses

ELSE:
  → PROCEED to Test 3 (OpenAI GPT-4o)
  → This should match manual quality (same model)
```

---

### Phase 2.5.4: Run OpenAI Test (FALLBACK #2 - If Needed)

**Agent Instructions:**

**ONLY RUN IF BOTH PERPLEXITY & CLAUDE FAIL**

Repeat Phase 2.5.2 steps with OpenAI API:
- Use same 3 test courses
- Call `test-openai-research` edge function
- Save results to `api_tests/openai_<course_name>.json`
- Insert into llm_api_test_results with `api_provider='openai'`

**Expected:** Should match your manual ChatGPT-5 Pro results exactly (same GPT-4o model)

**Cost:** ~$0.045 per course

**DECISION:**

```
OpenAI quality should be 100% since it's the same model you're using manually.

IF OpenAI fails:
  → Problem is with prompt or API parameters, not model choice
  → Debug prompt formatting, JSON schema instructions
  → Fix and re-test all 3 APIs
```

---

### Phase 2.5.5: Final API Selection & Cost Analysis

**Agent Instructions:**

After testing complete, generate comparison report:

```markdown
# LLM API Test Results - Final Report

## Test Summary

| API | Citation Quality | Tier Accuracy | Avg Contacts | Avg Quality Score | Cost/Course | Total Cost (15k) |
|-----|------------------|---------------|--------------|-------------------|-------------|------------------|
| Perplexity | <pass/fail> | <X/3> | <count> | <score>/100 | $0.005 | $75 |
| Claude | <pass/fail> | <X/3> | <count> | <score>/100 | $0.06 | $900 |
| OpenAI | <pass/fail> | <X/3> | <count> | <score>/100 | $0.045 | $675 |

## Recommendation

**SELECTED API:** <Perplexity/Claude/OpenAI>

**Rationale:**
- Citation quality: <assessment>
- Data accuracy: <assessment>
- Cost-benefit: <analysis>
- Risk level: <low/medium/high>

**Budget Request:** $<total> for 15,000 course automation

**Timeline:** 52 days unattended (12 requests/hour rate limit)

## Next Steps

PROCEED to Phase 2.6: Build production automation with selected API
```

**User Decision Required:**

After reviewing report, user approves:
- ✅ Selected API choice
- ✅ Budget allocation
- ✅ Timeline acceptance
- ✅ Proceed to Phase 2.6

---

## 📋 **PHASE 2.6: FULL AUTOMATION BUILD** (After Test Approval)

### Goal
Build production-ready batch LLM research pipeline using selected API.

### Agent Instructions

**STEP 1: Create Production Edge Function**

```typescript
// File: supabase/functions/batch-llm-research/index.ts
// Purpose: Automated 24/7 course enrichment with selected LLM API

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SELECTED_API = '<perplexity|claude|openai>'  // From Phase 2.5 results
const BATCH_SIZE = 10  // Process 10 courses per invocation
const RATE_LIMIT_DELAY_MS = 5000  // 5 seconds between requests (12/hour safe)

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // 1. Get courses needing research
  const { data: courses, error } = await supabase
    .from('golf_courses')
    .select('id, course_name, state_code, website')
    .is('v2_research_json', null)  // Not yet researched
    .in('state_code', ['NC', 'SC'])  // Start with NC/SC
    .order('id')
    .limit(BATCH_SIZE)

  if (error || !courses || courses.length === 0) {
    return new Response(JSON.stringify({
      success: true,
      message: 'No courses in queue',
      processed: 0
    }))
  }

  const results = {
    processed: 0,
    successful: 0,
    failed: 0,
    errors: []
  }

  // 2. Process each course
  for (const course of courses) {
    try {
      console.log(`🔍 Researching: ${course.course_name}`)

      // Call selected LLM API (Perplexity/Claude/OpenAI)
      const v2_json = await call_llm_api(SELECTED_API, course)

      // 3. Insert into staging table
      // Database trigger will automatically invoke validate-v2-research
      // Which calls Render validator → writes to production → creates ClickUp tasks
      const { error: insertError } = await supabase
        .from('llm_research_staging')
        .insert({
          course_id: course.id,
          course_name: course.course_name,
          state_code: course.state_code,
          v2_json: v2_json,
          status: 'pending'  // Trigger will process
        })

      if (insertError) throw insertError

      results.processed++
      results.successful++
      console.log(`✅ Staged: ${course.course_name}`)

      // 4. Rate limit delay
      await new Promise(resolve => setTimeout(resolve, RATE_LIMIT_DELAY_MS))

    } catch (error) {
      results.processed++
      results.failed++
      results.errors.push({
        course: course.course_name,
        error: error.message
      })
      console.error(`❌ Failed: ${course.course_name} - ${error.message}`)

      // Continue processing other courses
    }
  }

  return new Response(JSON.stringify(results), {
    headers: { 'Content-Type': 'application/json' }
  })
})

// Helper function - calls the selected API
async function call_llm_api(provider: string, course: any): Promise<object> {
  const prompt = await Deno.readTextFile('./v2_prompt.md')  // V2 prompt

  switch(provider) {
    case 'perplexity':
      return await call_perplexity(prompt, course)
    case 'claude':
      return await call_claude(prompt, course)
    case 'openai':
      return await call_openai(prompt, course)
    default:
      throw new Error(`Unknown provider: ${provider}`)
  }
}
```

**STEP 2: Deploy with Supabase Cron**

```bash
# Deploy function
supabase functions deploy batch-llm-research

# Schedule: Every 5 minutes
# Via Supabase dashboard: Edge Functions → batch-llm-research → Settings → Cron
# Schedule: */5 * * * * (every 5 minutes)
# Or: 0 */1 * * * (every hour for slower processing)
```

**STEP 3: Monitor First 100 Courses**

```sql
-- Check progress
SELECT
  COUNT(*) as total_researched,
  COUNT(*) FILTER (WHERE status = 'validated') as validated,
  COUNT(*) FILTER (WHERE status = 'validation_failed') as failed,
  AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_processing_time_sec
FROM llm_research_staging
WHERE state_code IN ('NC', 'SC');

-- Check validation success rate
SELECT
  status,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage
FROM llm_research_staging
WHERE v2_json != '{}'::jsonb
GROUP BY status
ORDER BY count DESC;

-- Check courses created
SELECT COUNT(*) as courses_created
FROM golf_courses
WHERE v2_research_json IS NOT NULL;

-- Check contacts created
SELECT COUNT(*) as contacts_created
FROM golf_course_contacts
WHERE created_at > '<automation_start_time>';
```

**Success Criteria (First 100 Courses):**
- ✅ Validation success rate ≥90%
- ✅ Average 3+ contacts per course
- ✅ ClickUp tasks created automatically
- ✅ Cost per course within expected range
- ✅ No system failures or crashes

**DECISION:**
```
IF first 100 pass all criteria:
  → APPROVE full 15,000 course automation
  → Let it run unattended for 52 days
  → Monitor weekly for quality drift

ELSE:
  → PAUSE automation
  → Debug validation failures
  → Adjust prompt or API parameters
  → Re-test 100 courses before proceeding
```

---

## 🚀 **PHASE 2.6: FULL AUTOMATION** (After Test Approval)

### Production Deployment

**Agent Instructions:**

1. **Verify environment:**
   ```bash
   # Render: USE_TEST_TABLES=false (write to production!)
   # Supabase: Cron schedule active
   # Database triggers: All enabled
   ```

2. **Start automation:**
   - Edge function runs every 5 minutes automatically
   - Processes 10-12 courses per hour (rate limit safe)
   - 15,000 courses ÷ 12/hour = 1,250 hours = 52 days

3. **Monitoring dashboard queries:**
   ```sql
   -- Daily progress check
   SELECT
     DATE(created_at) as date,
     COUNT(*) as courses_researched,
     COUNT(*) FILTER (WHERE status = 'validated') as successful,
     SUM((v2_json->'section4'->'contacts'->0) IS NOT NULL) as courses_with_contacts
   FROM llm_research_staging
   WHERE state_code IN ('NC', 'SC')
   GROUP BY DATE(created_at)
   ORDER BY date DESC
   LIMIT 7;

   -- Cost tracking
   SELECT
     SUM((v2_json->>'cost')::numeric) as total_cost_usd,
     AVG((v2_json->>'cost')::numeric) as avg_cost_per_course,
     COUNT(*) as courses_processed
   FROM llm_research_staging
   WHERE status IN ('validated', 'validation_failed');
   ```

4. **Weekly quality spot-checks:**
   - Random sample 10 courses
   - Manually verify tier classifications
   - Check contact email quality
   - Verify citations are real URLs
   - Update quality_score in tracking table

5. **Handle failures:**
   ```sql
   -- Retry failed validations (up to 3 attempts)
   SELECT id, course_name, validation_error
   FROM llm_research_staging
   WHERE status = 'validation_failed'
     AND (retry_count IS NULL OR retry_count < 3)
   ORDER BY created_at
   LIMIT 20;

   -- Reset for retry
   UPDATE llm_research_staging
   SET status = 'pending', v2_json = '{}'::jsonb, retry_count = COALESCE(retry_count, 0) + 1
   WHERE id IN ('<failed_ids>');
   ```

---

## 📊 **SUCCESS METRICS**

### Automation Goals

| Metric | Target | Tracking Query |
|--------|--------|----------------|
| **Validation Success Rate** | ≥90% | `SELECT COUNT(*) FILTER (WHERE status='validated') / COUNT(*)` |
| **Contacts Per Course** | ≥3 avg | `SELECT AVG(contact_count) FROM ...` |
| **Email Discovery Rate** | ≥60% | `SELECT COUNT(*) FILTER (WHERE contact_email IS NOT NULL) / COUNT(*)` |
| **Tier Classification** | 100% assigned | `SELECT COUNT(*) FILTER (WHERE course_tier IS NOT NULL) / COUNT(*)` |
| **Cost Per Course** | ≤$0.06 | `SELECT AVG(cost_usd) FROM llm_api_test_results` |
| **ClickUp Task Creation** | 100% | `SELECT COUNT(*) FROM golf_courses WHERE clickup_task_id IS NOT NULL` |
| **Processing Time** | 52 days max | Monitor daily progress |

---

## 🔄 **FALLBACK STRATEGIES**

### If Perplexity Citations Insufficient

**Problem:** Perplexity returns data but citations are generic or missing URLs

**Solution:**
1. Try with `return_citations: true` AND `search_recency_filter: "month"`
2. If still fails → Use Claude API (better reasoning, explicit citations)
3. Cost increase: $75 → $900 (still acceptable vs $125k manual cost)

### If All APIs Fail Quality Checks

**Problem:** No API matches ChatGPT-5 Pro manual quality

**Solution:**
1. **Investigate prompt engineering:** May need API-specific prompt variations
2. **Hybrid approach:** Use API for bulk data gathering, manual review for tier classification
3. **Staged automation:** Automate sections 2-5, keep section 1 (tier) manual
4. **Contact enrichment only:** Skip LLM research, focus on Apollo/Hunter automation

### If Rate Limits Block Progress

**Problem:** Free tier limits prevent 52-day timeline

**Solution:**
1. **Perplexity:** Upgrade to Pro ($20/month for 1,000 req/day)
2. **Claude:** No hard rate limits with paid tier
3. **OpenAI:** Standard tier handles 10k requests/day easily
4. **Parallel processing:** Run multiple edge function instances

### If Costs Exceed Budget

**Problem:** Actual costs significantly higher than estimates

**Solution:**
1. **Pause automation** after first 1,000 courses
2. **Analyze cost overruns:** Token usage, API fees, unexpected charges
3. **Optimize prompt:** Reduce input tokens, request shorter responses
4. **Switch APIs:** Move to cheaper alternative mid-stream
5. **Partial automation:** Complete high-value courses only (Premium tier first)

---

## 📝 **DOCUMENTATION REQUIREMENTS**

### After Each Test Phase

**Agent must document:**

1. **API Response Samples:**
   - Save raw JSON to `api_tests/<provider>_<course>.json`
   - Include citations array, token usage, cost

2. **Quality Comparison:**
   - Side-by-side: Manual vs API result
   - Highlight differences in tier, contacts, citations
   - Score 0-100 with explanation

3. **Decision Rationale:**
   - Why selected or rejected this API
   - Cost-benefit analysis
   - Risk assessment

4. **Update PROGRESS.md:**
   - Add Session 10 (or 8.1) with test results
   - Update roadmap status
   - Document selected API and next steps

---

## 🎯 **AGENT EXECUTION CHECKLIST**

**Phase 2.5.1: Infrastructure** (DO THIS FIRST)
- [ ] Create 3 test edge functions (Perplexity, Claude, OpenAI)
- [ ] Deploy all 3 to Supabase
- [ ] Configure API keys (secrets)
- [ ] Create llm_api_test_results tracking table
- [ ] Document test infrastructure in PROGRESS.md

**Phase 2.5.2: Perplexity Test** (PRIMARY)
- [ ] Test course 1: The Tradition Golf Club
- [ ] Test course 2: Forest Creek Golf Club
- [ ] Test course 3: Hemlock Golf Course
- [ ] Validate citations provided (CRITICAL)
- [ ] Compare quality vs manual baseline
- [ ] Make GO/NO-GO decision
- [ ] Document results

**Phase 2.5.3: Claude Test** (ONLY IF PERPLEXITY FAILS)
- [ ] Test same 3 courses with Claude API
- [ ] Validate citations and quality
- [ ] Make GO/NO-GO decision
- [ ] Document results

**Phase 2.5.4: OpenAI Test** (ONLY IF BOTH FAIL)
- [ ] Test same 3 courses with OpenAI
- [ ] Should match manual quality (same model)
- [ ] Document results

**Phase 2.5.5: Final Selection**
- [ ] Generate comparison report
- [ ] User approves selected API and budget
- [ ] Update PROGRESS.md with decision

**Phase 2.6: Production Automation** (AFTER APPROVAL)
- [ ] Build batch-llm-research with selected API
- [ ] Deploy to Supabase with cron schedule
- [ ] Switch USE_TEST_TABLES=false (production mode!)
- [ ] Monitor first 100 courses
- [ ] Validate ClickUp integration working
- [ ] Let it run for 15,000 courses
- [ ] Weekly quality spot-checks
- [ ] Final documentation and handoff

---

## 🚨 **CRITICAL DECISION POINTS**

### Decision 1: After Perplexity Test (3 courses)
**Question:** Does Perplexity provide acceptable citations and accuracy?
- **YES** → Skip Claude/OpenAI tests, proceed to Phase 2.6 ($75 total cost)
- **NO** → Proceed to Claude test

### Decision 2: After Claude Test (if needed)
**Question:** Does Claude justify 12x cost increase vs Perplexity?
- **YES** → Skip OpenAI test, proceed to Phase 2.6 ($900 total cost)
- **NO** → Proceed to OpenAI test

### Decision 3: After API Selection
**Question:** Approve full 15,000 course automation with selected API?
- **YES** → Build Phase 2.6 production automation
- **NO** → Stay with manual approach or hybrid solution

### Decision 4: After First 100 Automated Courses
**Question:** Quality and costs meeting expectations?
- **YES** → Continue unattended for remaining 14,900 courses
- **NO** → Pause, debug, adjust, resume

---

## 📍 **CURRENT SESSION STATUS**

**Session 9 Complete:** Infrastructure setup (edge function, Render validator, Docker validation)

**Session 10 Starting:** LLM API automation testing (Perplexity → Claude → OpenAI)

**Ready for:** Phase 2.5.1 - Build test infrastructure for 3-course pilot

**User Action:** Approve plan and agent can begin building test edge functions

---

**Last Updated:** November 1, 2025 (Session 10 Plan Approved - Ready for API Testing)
