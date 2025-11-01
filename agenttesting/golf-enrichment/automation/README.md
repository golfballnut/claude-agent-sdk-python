# Automation Workspace - LLM Research Pipeline

**START HERE** for Phase 2.5 (LLM API Testing) and Phase 2.6 (Full Automation)

---

## 🎯 Current Phase: 2.5 - LLM API Automation Testing

**Goal:** Test Perplexity/Claude/OpenAI APIs for automated 15,000 course enrichment

**Status:** Ready to build test infrastructure

---

## 📂 Directory Structure

```
automation/
├── README.md                    # This file - START HERE
├── CURRENT_PHASE.md             # Single source: "We're in Phase 2.5"
├── api_testing/
│   ├── perplexity/              # Perplexity test results
│   ├── claude/                  # Claude test results
│   ├── openai/                  # OpenAI test results
│   └── comparison_report.md     # Final API selection
├── edge_functions/
│   ├── test-perplexity-research/    # Phase 2.5 test functions
│   ├── test-claude-research/
│   ├── test-openai-research/
│   └── batch-llm-research/          # Phase 2.6 production function
├── test_courses/
│   ├── tradition_golf_club.json     # 3 test courses for validation
│   ├── forest_creek.json
│   └── hemlock_golf.json
├── prompts/
│   └── v2_research_prompt.md        # Active V2 prompt
└── docs/
    ├── phase_2.5_plan.md            # Complete testing plan
    ├── api_references/              # API documentation
    │   ├── perplexity_sonar_pro.md
    │   ├── claude_sonnet_4.5.md
    │   ├── openai_gpt4o.md
    │   ├── supabase_edge_functions.md
    │   └── cost_comparison.md
    └── monitoring_queries.sql       # Database monitoring
```

---

## 🚀 Quick Start for Agents

### Step 1: Read These Files (In Order)
1. `CURRENT_PHASE.md` - What phase we're in
2. `docs/phase_2.5_plan.md` - Complete testing plan
3. `docs/api_references/perplexity_sonar_pro.md` - Primary API docs
4. `../prompts/v2_research_prompt.md` - The actual prompt to use

### Step 2: Execute Phase 2.5.1
- Build 3 test edge functions (Perplexity, Claude, OpenAI)
- Deploy to Supabase
- Configure API keys

### Step 3: Execute Phase 2.5.2
- Test Perplexity on 3 courses
- Validate citation quality (CRITICAL)
- Make GO/NO-GO decision

### Step 4: Fallback Testing (If Needed)
- Test Claude if Perplexity fails
- Test OpenAI if both fail
- Generate comparison report

### Step 5: User Decision
- Present API selection recommendation
- Get budget approval
- Proceed to Phase 2.6 (full automation)

---

## 📍 Context: What We Have Complete

### Infrastructure (100% Built)
- ✅ Render validator service: `https://agent7-water-hazards.onrender.com/validate-and-write`
- ✅ Supabase edge function: `validate-v2-research` (deployed)
- ✅ Database tables: `llm_research_staging`, `golf_courses`, `golf_course_contacts`
- ✅ Test tables: `*_test` for production-safe validation
- ✅ ClickUp integration: Automatic task creation
- ✅ Docker validation: 100% passing

### Proven Quality
- ✅ Manual V2 prompt testing: 100% tier accuracy, 3-4 contacts per course
- ✅ Citation coverage: 100% sourced
- ✅ Validation tested: Course ID 2055 created successfully

---

## 🎯 Success Criteria for Phase 2.5

### Primary Test (Perplexity)
- ✅ **Citations provided** for all claims (URLs, sources) - CRITICAL
- ✅ **Tier accuracy** ≥90% vs manual baseline - CRITICAL
- ✅ **Contact count** ≥3 per course - HIGH
- ✅ **Email/LinkedIn** for GM or Superintendent - HIGH
- ✅ **Cost** ≤$0.01 per course ($75 for 15k) - HIGH

### Fallback Tests (Claude, OpenAI)
- Only run if Perplexity fails CRITICAL checks
- Same success criteria
- Higher cost thresholds ($900, $675 respectively)

---

## 🔗 External References

**Parent Project:** `../../` (claude-agent-sdk-python root)
**Production Code:** `../../../../production/golf-enrichment/`
**Legacy V1:** `../../archive/v1_agents/` (reference only)
**Main Docs:** `../../docs/PROGRESS.md` (session history)

---

## ⚠️ What NOT to Do

- ❌ Don't modify V1 agent files (archived, not used)
- ❌ Don't change database schema (already validated)
- ❌ Don't edit production validator code (working, tested)
- ❌ Don't skip Perplexity test (cheapest option, test first)
- ❌ Don't deploy to production before 3-course pilot

---

**Next Action:** Read `CURRENT_PHASE.md` to confirm current status, then proceed to `docs/phase_2.5_plan.md` for detailed instructions.
