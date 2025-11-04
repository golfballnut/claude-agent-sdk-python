# Current Phase Status

**Last Updated:** November 1, 2025

---

## 📍 We Are Currently In:

# **PHASE 2.5: LLM API AUTOMATION TESTING**

---

## What This Means

We're testing **automated LLM research** to replace **manual copy/paste workflow**.

**Manual (Current):** User pastes course into ChatGPT-5 → waits 10 min → copies JSON → pastes to database
- **Problem:** 15,000 courses = 2,500 hours = 15 MONTHS of work
- **Risk:** Human error, burnout

**Automated (Goal):** Edge function calls LLM API → parses JSON → writes to database (unattended)
- **Benefit:** 52 days running 24/7, zero human time
- **Cost:** $75-675 depending on API choice

---

## 🎯 Current Objective

**Test 3 LLM APIs** to find which one delivers quality data with citations:

1. **Perplexity Sonar Pro** (PRIMARY - cheapest at $75 total)
2. **Claude Sonnet 4.5** (FALLBACK #1 - $900 total)
3. **OpenAI GPT-4o** (FALLBACK #2 - $675 total)

**Critical Success Factor:** **Citations must be provided with verifiable URLs**

---

## 📋 What Needs to Happen Next

### Phase 2.5.1: Build Test Infrastructure
- [ ] Create 3 test edge functions (one per API)
- [ ] Deploy to Supabase
- [ ] Configure API keys
- [ ] Create results tracking table

### Phase 2.5.2: Test Perplexity (PRIMARY)
- [ ] Test on 3 NC courses (The Tradition, Forest Creek, Hemlock)
- [ ] Validate citation quality
- [ ] Compare vs manual ChatGPT-5 baseline
- [ ] **DECISION:** Pass → Phase 2.6 | Fail → Test Claude

### Phase 2.5.3: Test Claude (ONLY IF PERPLEXITY FAILS)
- [ ] Same 3 courses
- [ ] Same quality checks
- [ ] **DECISION:** Pass → Phase 2.6 | Fail → Test OpenAI

### Phase 2.5.4: Test OpenAI (ONLY IF BOTH FAIL)
- [ ] Same 3 courses (should match manual - same model)

### Phase 2.5.5: API Selection
- [ ] Generate comparison report
- [ ] User approves selected API and budget
- [ ] Proceed to Phase 2.6

---

## ✅ What We Already Have Complete

- ✅ Render validator service (live at agent7-water-hazards.onrender.com)
- ✅ Supabase edge function (validate-v2-research deployed)
- ✅ V2 research prompt (tested, 100% tier accuracy)
- ✅ Database schema (migrations 013-018 applied)
- ✅ Test tables for production-safe testing
- ✅ Docker validation (100% passing)
- ✅ ClickUp integration (automatic)

**Translation:** Once we select the best API, we're 90% done. Just need the batch edge function.

---

## 🚫 What NOT to Do

- ❌ Don't skip Perplexity test (cheapest option, test first)
- ❌ Don't deploy to production before 3-course pilot
- ❌ Don't modify validator code (already working)
- ❌ Don't change database schema (already validated)

---

## 📚 Key Files for This Phase

**Read First:**
1. `/automation/docs/phase_2.5_plan.md` - Complete testing plan
2. `/automation/docs/api_references/perplexity_sonar_pro.md` - API specs
3. `/../prompts/v2_research_prompt.md` - The prompt to use

**Reference:**
- `/../docs/PROGRESS.md` - Historical session log
- `/automation/docs/api_references/cost_comparison.md` - Budget analysis

---

## 🎯 Success = Moving to Phase 2.6

**Phase 2.6 = Full Automation:**
- Build production batch-llm-research edge function
- Schedule it to run every 5 minutes
- Process 15,000 courses unattended over 52 days
- Cost: $75-675 (vs $125k manual opportunity cost)

---

**Next Action for Agent:** Read `/automation/docs/phase_2.5_plan.md` and begin Phase 2.5.1 (build test infrastructure)
