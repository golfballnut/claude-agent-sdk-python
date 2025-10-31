# Golf Enrichment Prompt Testing

**Location:** `/agenttesting/golf-enrichment/`
**Purpose:** Test and validate LLM research prompts for golf course enrichment

## Structure

```
agenttesting/golf-enrichment/
├── CLAUDE.md                          # This file - working directory guide
├── prompts/
│   └── enhanced_research_v1.md        # 8-section comprehensive prompt
├── schemas/
│   └── llm_response_v1.json          # JSON schema for validation
├── test_courses.json                  # Test course definitions
├── test_prompt.py                     # Test runner script
├── results/
│   ├── TEMPLATE.md                    # Results documentation template
│   └── [course_id]_response.json      # Individual test results
└── docs/
    ├── PROGRESS.md                    # Session log & tracking
    ├── ARCHITECTURE.md                # Technical design
    └── IMPLEMENTATION_MAP.md          # Business → code mapping
```

## Quick Start

### Run Phase 1 Test (The Neuse Golf Club only)
```bash
cd agenttesting/golf-enrichment
python test_prompt.py 1
```

### Run Phase 2 Test (All courses)
```bash
python test_prompt.py 2
```

## What Gets Tested

The enhanced prompt tests **8 critical sections**:
1. **Range Ball BUY/SELL/BOTH Classification** (CRITICAL)
2. Water Hazards (expansion opportunity)
3. Practice Facilities (volume estimates)
4. Decision Makers (contacts with emails)
5. Course Tier Classification (premium/medium/budget)
6. Buying Signals (hot opportunities)
7. Course Intelligence (personalization data)
8. Event Program (bulk ball needs)

## Success Criteria

- ✅ Valid JSON response
- ✅ Classification is not "INSUFFICIENT_DATA" (unless truly no data)
- ✅ At least 1 decision maker found
- ✅ Citations present for 80%+ of claims
- ✅ Tier classification matches reality

## Documentation

**Progress tracking:** `/agenttesting/golf-enrichment/docs/PROGRESS.md`
**Architecture:** `/agenttesting/golf-enrichment/docs/ARCHITECTURE.md`
**Implementation map:** `/agenttesting/golf-enrichment/docs/IMPLEMENTATION_MAP.md`

## Test Workflow

1. **Create/modify prompt** → `prompts/enhanced_research_v1.md`
2. **Run test** → `python test_prompt.py 1`
3. **Review results** → `results/[course_id]_response.json`
4. **Document findings** → Use `results/TEMPLATE.md` structure
5. **Update progress** → `/agenttesting/golf-enrichment/docs/PROGRESS.md`
6. **Iterate** → Modify prompt based on findings

## Key Files

- **Prompt:** Full instructions for LLM research
- **Schema:** JSON structure for response validation
- **Test courses:** Defined courses with expected outcomes
- **Test runner:** Automated testing with validation
- **Results template:** Structured documentation format
