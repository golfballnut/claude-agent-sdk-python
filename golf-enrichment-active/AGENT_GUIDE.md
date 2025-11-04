# Agent Execution Guide - Golf Enrichment V2

**Purpose:** Master guide for agents working on automated LLM research pipeline

---

## 🎯 CURRENT STATUS

**Phase:** 2.5 - LLM API Automation Testing
**Goal:** Test Perplexity/Claude/OpenAI APIs for 15,000 course automation
**Location:** `/automation/` directory ← **START HERE**

---

## 📂 CRITICAL FILES (Read These First)

### Phase 2.5 Execution
1. **`/automation/README.md`** - Automation workspace overview
2. **`/automation/CURRENT_PHASE.md`** - What we're doing NOW
3. **`/automation/docs/phase_2.5_plan.md`** - Complete test plan
4. **`/automation/docs/api_references/perplexity_sonar_pro.md`** - API specs

### V2 Prompt & Schema
5. **`/prompts/v2_research_prompt.md`** - Active V2 prompt (use this!)
6. **`/schemas/llm_response_v1.json`** - V2 JSON structure

### Infrastructure Reference
7. **`/docs/PROGRESS.md`** - Session history and context
8. **`/supabase/migrations/`** - Database schema (013-018)

---

## 🚫 IGNORE THESE (Legacy V1 Code)

### Deprecated Files
- `/agents/agent1_url_finder.py` through `/agents/agent8_supabase_writer.py`
  - **Why:** V1 agent-based enrichment, replaced by V2 LLM research
  - **Where:** Will be archived to `/archive/v1_agents/`

- `/docs/ARCHITECTURE.md` lines 1-929
  - **Why:** V1 architecture documentation (superseded by V2)
  - **Where:** Extract and archive

- `/results/docker/batch_test/` and `/results/docker/*_oct30.md`
  - **Why:** October testing results (complete, historical)
  - **Where:** Will be archived to `/archive/october_testing/`

### Files to Skip
- `/data/apollo_duplicate_contacts.json` - October debugging, not relevant
- `/supabase/.temp/` - Temporary Supabase CLI files
- `/render/validator/` (outdated) - Production code is in `/production/golf-enrichment/`

---

## 🔑 API CREDENTIALS

**Location:** Supabase Secrets (configured via CLI)

```bash
# View secrets
supabase secrets list --project-ref oadmysogtfopkbmrulmq

# Set secrets
supabase secrets set PERPLEXITY_API_KEY=<your-key>
supabase secrets set ANTHROPIC_API_KEY=<your-key>
supabase secrets set OPENAI_API_KEY=<your-key>
```

**Environment Variables:**
- `PERPLEXITY_API_KEY` - For test-perplexity-research edge function
- `ANTHROPIC_API_KEY` - For test-claude-research edge function
- `OPENAI_API_KEY` - For test-openai-research edge function
- `SUPABASE_URL` - Auto-available in edge functions
- `SUPABASE_SERVICE_ROLE_KEY` - Auto-available in edge functions

---

## 📚 EXTERNAL DOCUMENTATION REQUIRED

**Agents will need official API docs for:**

1. **Perplexity Sonar Pro** (PRIMARY)
   - See: `/automation/docs/api_references/perplexity_sonar_pro.md`
   - **CRITICAL:** `return_citations` parameter for citation extraction
   - Endpoint, model ID, pricing, rate limits

2. **Claude Sonnet 4.5** (FALLBACK)
   - See: `/automation/docs/api_references/claude_sonnet_4.5.md`
   - System prompt structure, message format, pricing

3. **OpenAI GPT-4o** (FALLBACK)
   - See: `/automation/docs/api_references/openai_gpt4o.md`
   - ChatCompletion API, temperature, max_tokens

4. **Supabase Edge Functions**
   - See: `/automation/docs/api_references/supabase_edge_functions.md`
   - Deployment, secrets, cron scheduling

---

## ✅ PHASE 2.5 EXECUTION CHECKLIST

**Phase 2.5.1: Build Test Infrastructure** (DO THIS FIRST)
- [ ] Create 3 test edge functions (Perplexity, Claude, OpenAI)
- [ ] Deploy all 3 to Supabase
- [ ] Configure API keys in Supabase secrets
- [ ] Create `llm_api_test_results` tracking table
- [ ] Document infrastructure in session log

**Phase 2.5.2: Perplexity Test** (PRIMARY)
- [ ] Test course 1: The Tradition Golf Club
- [ ] Test course 2: Forest Creek Golf Club
- [ ] Test course 3: Hemlock Golf Course
- [ ] **CRITICAL:** Validate citations provided with URLs
- [ ] Compare quality vs manual ChatGPT-5 baseline
- [ ] Make GO/NO-GO decision
- [ ] Save results to `/automation/api_testing/perplexity/`

**Phase 2.5.3: Claude Test** (ONLY IF PERPLEXITY FAILS)
- [ ] Test same 3 courses with Claude API
- [ ] Validate citations and accuracy
- [ ] Make GO/NO-GO decision
- [ ] Save results to `/automation/api_testing/claude/`

**Phase 2.5.4: OpenAI Test** (ONLY IF BOTH FAIL)
- [ ] Test same 3 courses with OpenAI
- [ ] Should match manual quality (same GPT-4o model)
- [ ] Save results to `/automation/api_testing/openai/`

**Phase 2.5.5: API Selection**
- [ ] Generate comparison report
- [ ] Present to user with cost-benefit analysis
- [ ] Get user approval for selected API and budget
- [ ] Update PROGRESS.md with decision

---

## 🎯 CRITICAL SUCCESS CRITERIA

### Perplexity Must Provide:
1. ✅ **Citations with URLs** (not just "source: website")
2. ✅ **Tier classification** matching manual results
3. ✅ **3+ contacts** per course with email OR LinkedIn
4. ✅ **JSON in V2 format** (5 sections)

**If ANY of these fail → Use Claude or OpenAI fallback**

---

## 📊 Cost Analysis Reference

| API | Cost/Course | Total (15k) | Timeline | Quality Expected |
|-----|-------------|-------------|----------|------------------|
| **Perplexity** | $0.005 | **$75** | 52 days | Unknown (testing now) |
| **Claude** | $0.06 | $900 | 52 days | High (reasoning strong) |
| **OpenAI** | $0.045 | $675 | 52 days | Identical to manual |

**Manual Baseline:** $125k opportunity cost (2,500 hours)

**ROI:** Any API pays for itself immediately

---

## 🔄 Workflow After API Selection

Once user approves selected API:

### Phase 2.6: Build Production Automation
1. Create `batch-llm-research` edge function with selected API
2. Deploy to Supabase with cron schedule (every 5 minutes)
3. Monitor first 100 courses (validation success rate ≥90%)
4. Switch to production tables (`USE_TEST_TABLES=false`)
5. Let it run 24/7 for 15,000 courses
6. Weekly quality spot-checks
7. Complete in ~52 days

---

## 🚨 DECISION GATES

### Gate 1: After Perplexity Test
**Question:** Does Perplexity provide citations and match quality?
- **YES** → Skip Claude/OpenAI, proceed to Phase 2.6 (save $600-825)
- **NO** → Test Claude

### Gate 2: After Claude Test
**Question:** Does Claude justify 12x cost vs Perplexity?
- **YES** → Skip OpenAI, proceed to Phase 2.6 ($900 budget)
- **NO** → Test OpenAI

### Gate 3: After API Selection
**Question:** User approves selected API and budget?
- **YES** → Build Phase 2.6 production automation
- **NO** → Revisit strategy

### Gate 4: After 100 Automated Courses
**Question:** Quality metrics meeting targets?
- **YES** → Continue for remaining 14,900 courses
- **NO** → Pause, debug, adjust

---

## 📁 File Organization

**Active Work:** `/automation/` (THIS directory)
**Production:** `/production/golf-enrichment/` (validator service)
**Database:** `/supabase/migrations/` (schema)
**Legacy:** `/archive/` (V1 agents, October tests)
**Documentation:** `/docs/` (PROGRESS.md, ARCHITECTURE_V2.md)

---

## 🎯 Next Immediate Action

**Agent should:**
1. Read `/automation/docs/phase_2.5_plan.md` (complete test plan)
2. Read `/automation/docs/api_references/perplexity_sonar_pro.md` (API specs)
3. Execute Phase 2.5.1: Build test-perplexity-research edge function
4. Deploy and test on first course
5. Validate citations are present
6. Proceed through testing protocol

---

**Status:** Infrastructure ready, docs complete, waiting for agent to build test functions
