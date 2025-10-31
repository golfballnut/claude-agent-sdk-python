# Golf Enrichment v2 - Progress Tracking

**Project:** Enhanced enrichment workflow with BUY/SELL opportunity classification
**Started:** October 31, 2025
**Status:** 🟡 In Progress - Phase 1 (LLM Research Agent)

---

## 📍 Current Phase

**Phase 1: LLM Research Agent**
- Goal: Single LLM call returns ALL course intelligence with citations
- Status: Planning → Implementation

---

## 🎯 Session Log

### Session 1 - October 31, 2025 (Morning)

**Completed:**
- ✅ Ideated buy/sell opportunity classification strategy
- ✅ Defined 4-phase architecture (LLM → Enrichment → Organization → ClickUp)
- ✅ Created tracking documentation structure

**Decisions Made:**
1. **LLM does heavy lifting** - Research, classification, extraction (not just prompt engineering)
2. **Agents stay focused** - Email finding (Apollo/Hunter), data merging, syncing
3. **Test both output formats** - Markdown vs JSON, pick winner based on parsing quality
4. **Scoring in Organizer** - Deterministic math, not LLM (easier to adjust weights)
5. **Process incomplete data** - Tag 'needs_human_review', don't lose leads

**Blockers/Questions:**
- None currently

**Next Session Goals:**
1. Build LLM Research Agent with enhanced 8-section prompt
2. Test markdown vs JSON output format on 1 test course
3. Validate classification accuracy on 3 test courses (BUY, SELL, BOTH)

---

### Session 2 - October 31, 2025 (Afternoon)

**Completed:**
- ✅ Created comprehensive 8-section LLM research prompt (`prompts/enhanced_research_v1.md`)
- ✅ Designed optimized JSON response schema with inline citations (`schemas/llm_response_v1.json`)
- ✅ Built test course definitions with 3 test courses: The Neuse Golf Club, Pinehurst No. 2, Bethpage Black (`test_courses.json`)
- ✅ Created automated test runner script with validation (`test_prompt.py`)
- ✅ Created results tracking template (`results/TEMPLATE.md`)
- ✅ Created testing directory guide (`CLAUDE.md`)

**Decisions Made:**
1. **All 8 sections in one prompt** - Test comprehensive approach (vs incremental)
2. **Optimize JSON schema for LLM output quality** - Not strict architecture field names yet
3. **Inline citations with each data point** - Each signal/contact has its own source field
4. **Explicit null handling** - LLM instructed to use null for missing single values
5. **JSON output format** - Structured output with code block detection for parsing

**Test Infrastructure Created:**
```
agenttesting/golf-enrichment/
├── CLAUDE.md                          # Testing guide
├── prompts/enhanced_research_v1.md    # 8-section comprehensive prompt
├── schemas/llm_response_v1.json       # JSON validation schema
├── test_courses.json                  # 3 test courses with expected outcomes
├── test_prompt.py                     # Automated test runner with validation
└── results/
    └── TEMPLATE.md                    # Results documentation template
```

**Prompt Enhancement Details:**
- **Section 1 (CRITICAL):** Range ball BUY/SELL/BOTH classification with confidence, reasoning, and inline citations
- **Section 2:** Water hazards for retrieval expansion opportunities
- **Section 3:** Practice facilities with range size, supplier info, quality mentions
- **Section 4 (CRITICAL):** Decision makers with work emails, LinkedIn, phone, employment verification, sources
- **Section 5:** Course tier classification (premium/medium/budget) with pricing data
- **Section 6:** Buying signals by 5 categories (cost/quality/operational/change/active search)
- **Section 7:** Course intelligence (ownership, projects, vendors, awards, challenges)
- **Section 8:** Event program for bulk ball opportunities

**Test Course Selection:**
- **Phase 1:** The Neuse Golf Club (baseline test, medium tier expected)
- **Phase 2:** Pinehurst No. 2 (premium resort, BOTH opportunity expected), Bethpage Black (municipal/public, SELL opportunity expected)

**Blockers/Questions:**
- None currently

**Next Actions:**
1. Run Phase 1 test: `cd agenttesting/golf-enrichment && python test_prompt.py 1`
2. Review JSON response from The Neuse Golf Club
3. Validate classification accuracy, citation quality, data completeness
4. Document findings using results/TEMPLATE.md
5. Iterate on prompt if issues found
6. Run Phase 2 tests on Pinehurst and Bethpage

---

## 📊 Test Results

### Classification Accuracy Tests
**Status:** Not started

| Course Type | Expected | Actual | Pass/Fail | Notes |
|-------------|----------|--------|-----------|-------|
| BUY Only | buy | - | - | Not tested |
| SELL Only | sell | - | - | Not tested |
| BOTH | both | - | - | Not tested |

### Output Format Test
**Status:** Not started

| Format | Parsing Success | LLM Quality | Pick? |
|--------|----------------|-------------|-------|
| Markdown | - | - | - |
| JSON | - | - | - |

---

## 🗺️ Roadmap

### ✅ Phase 0: Planning (Complete)
- [x] Define business requirements
- [x] Design architecture
- [x] Create tracking docs

### 🟡 Phase 1: LLM Research Agent (In Progress)
- [x] Build enhanced LLM prompt with 8 sections
- [x] Create JSON output schema with inline citations
- [x] Build automated test runner with validation
- [ ] Run Phase 1 test (The Neuse Golf Club)
- [ ] Validate classification accuracy on test course
- [ ] Run Phase 2 tests (Pinehurst No. 2, Bethpage Black)
- [ ] Document results and iterate on prompt

### ⚪ Phase 2: Contact Enrichment
- [ ] Build Apollo agent
- [ ] Build Hunter waterfall
- [ ] Test email discovery rate (target: ≥70%)

### ⚪ Phase 3: Organization & Scoring
- [ ] Build Organizer agent
- [ ] Implement scoring algorithm
- [ ] Add data quality tagging

### ⚪ Phase 4: ClickUp Integration
- [ ] Build ClickUp sync with routing
- [ ] Add custom fields + tags
- [ ] Test end-to-end on 5 courses

---

## 📚 Reference Links

**Business Context:**
- Strategy: `../../business-context/service-offerings/entry-point-strategy.md`
- Data Priorities: `../../business-context/enrichment-requirements/data-priorities.md`
- Workflow Mapping: `../../business-context/enrichment-requirements/workflow-mapping.md`

**Implementation:**
- Architecture: `./docs/ARCHITECTURE.md`
- Code Map: `./IMPLEMENTATION_MAP.md`

---

## 🎯 Success Metrics (Running Tally)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Classification Accuracy | 100% (3 test courses) | - | 🟡 Not tested |
| Email Discovery Rate | ≥70% | - | 🟡 Not tested |
| End-to-End Success | 5/5 courses complete | 0/5 | 🟡 Not started |
| LLM Citations Present | 100% | - | 🟡 Not tested |

---

## 💡 Lessons Learned

**Session 1:**
- Incremental approach (Option A) reduces risk
- LLM should do research, agents should do operations
- Citations critical for validating contact data
- Process incomplete data (tag for review) > discard

---

**Last Updated:** October 31, 2025
