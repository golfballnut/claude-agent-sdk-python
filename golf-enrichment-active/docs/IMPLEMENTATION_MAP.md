# Golf Enrichment v2 - Implementation Map

**Purpose:** Quick reference - "Where is X implemented?"
**Last Updated:** October 31, 2025

---

## 🗺️ Business Context → Code Mapping

### Entry Point Strategy (BUY/SELL/BOTH Classification)

**Business Requirement:** `../../business-context/service-offerings/entry-point-strategy.md`

| What | Where Implemented | File |
|------|------------------|------|
| **LLM classifies BUY/SELL/BOTH** | LLM Research Agent prompt | `agents/llm_researcher.py` |
| **Parse classification from LLM** | Organizer Agent | `agents/organizer.py` |
| **Store opportunity_type** | Supabase enrichment_queue | Schema in `docs/ARCHITECTURE.md` |
| **Route by opportunity type** | ClickUp Sync Agent | `agents/clickup_syncer.py` |

---

### Data Collection Priorities

**Business Requirement:** `../../business-context/enrichment-requirements/data-priorities.md`

| Priority Data | Collected By | Processed By |
|---------------|-------------|--------------|
| **Range ball classification** | LLM Research Agent | Organizer (validation) |
| **Water hazards (count + details)** | LLM Research Agent | Organizer (scoring) |
| **Practice range size** | LLM Research Agent | Organizer (scoring) |
| **Decision maker contacts** | LLM finds names → Apollo/Hunter find emails | Contact Enrichment Agents |
| **Course tier (premium/medium/budget)** | LLM Research Agent | Organizer (validation) |
| **Buying signals** | LLM Research Agent | Organizer (scoring boost) |
| **Course intelligence** | LLM Research Agent | ClickUp (task description) |

---

### Enhanced Workflow Mapping

**Business Requirement:** `../../business-context/enrichment-requirements/workflow-mapping.md`

| Workflow Section | Implementation |
|-----------------|----------------|
| **Section 1: Range Ball Classification** | LLM prompt section 1 → `agents/llm_researcher.py:45-120` |
| **Section 2: Water Hazards** | LLM prompt section 2 → `agents/llm_researcher.py:122-160` |
| **Section 3: Practice Facilities** | LLM prompt section 3 → `agents/llm_researcher.py:162-200` |
| **Section 4: Decision Makers** | LLM prompt section 4 → `agents/llm_researcher.py:202-280` |
| **Section 5: Course Positioning** | LLM prompt section 5 → `agents/llm_researcher.py:282-330` |
| **Section 6: Buying Signals** | LLM prompt section 6 → `agents/llm_researcher.py:332-380` |
| **Section 7: Course Intelligence** | LLM prompt section 7 → `agents/llm_researcher.py:382-430` |
| **Section 8: Event Program** | LLM prompt section 8 → `agents/llm_researcher.py:432-460` |

**Note:** Line numbers are estimates, will update after implementation

---

## 🤖 Agent Responsibilities

### Phase 1: LLM Research Agent
**File:** `agents/llm_researcher.py`

**Input:**
```python
{
  "course_name": "Pinehurst No. 2",
  "city": "Pinehurst",
  "state": "NC"
}
```

**Output:** (Markdown or JSON - TBD after testing)
```
- opportunity_classification (buy/sell/both/unknown)
- buy_signals, sell_signals
- contacts (names, titles, citations)
- water_hazards, range_details
- course_tier, buying_signals
- course_intelligence
```

**Responsibilities:**
- Deep web research (8 sections)
- Classify opportunity type
- Extract contacts with citations
- Provide all source URLs

---

### Phase 2a: Apollo Enrichment Agent
**File:** `agents/apollo_enricher.py`

**Input:**
```python
{
  "name": "John Smith",
  "title": "General Manager",
  "company": "Pinehurst Country Club"
}
```

**Output:**
```python
{
  "email": "jsmith@pinehurst.com",
  "linkedin": "linkedin.com/in/johnsmith",
  "verified": true
}
```

**Responsibilities:**
- Name + company → email lookup
- LinkedIn URL discovery
- First attempt in waterfall

---

### Phase 2b: Hunter Enrichment Agent
**File:** `agents/hunter_enricher.py`

**Input:** Same as Apollo (runs if Apollo fails)

**Output:** Same as Apollo

**Responsibilities:**
- Fallback email discovery
- Domain-based search
- Email verification

---

### Phase 3: Organizer Agent
**File:** `agents/organizer.py`

**Input:**
```python
{
  "llm_data": {...},  # From LLM Research Agent
  "enriched_contacts": [...]  # From Apollo/Hunter
}
```

**Output:**
```python
{
  "course_id": "uuid",
  "opportunity_type": "both",
  "qualification_score": 8.5,
  "course_tier": "premium",
  "tags": ["high_priority_both_opportunity"],
  "contacts": [...],  # Merged with emails
  "ready_for_clickup": true
}
```

**Responsibilities:**
- Merge LLM data + enriched contacts
- Calculate qualification score (deterministic algorithm)
- Apply data quality tags
- Validate completeness
- Write to Supabase `enrichment_queue`

---

### Phase 4: ClickUp Sync Agent
**File:** `agents/clickup_syncer.py`

**Input:** Query Supabase `enrichment_queue WHERE clickup_task_id IS NULL`

**Output:** ClickUp task created, `clickup_task_id` updated in Supabase

**Responsibilities:**
- Route by score (8+ = Hot, 6-8 = Qualified, <6 = Nurture, needs_review = Human Review)
- Format task description (BUY/SELL sections)
- Set custom fields (`opportunity_type`, `qualification_score`, `course_tier`)
- Apply tags (`needs_human_review`, `high_priority_both_opportunity`)

---

## 📦 Database Schema

### Supabase: `enrichment_queue` Table

**New Columns (Phase 1):**
```sql
-- Range Ball Opportunity
opportunity_type VARCHAR(20),           -- 'buy', 'sell', 'both', 'unknown'
buy_signals JSONB,                      -- {has_waste: bool, signals: [...]}
sell_signals JSONB,                     -- {needs_supplier: bool, pain_level: 'high'}
recommended_strategy VARCHAR(50),       -- 'buy_first', 'sell_first', 'buy_then_sell'

-- Qualification
qualification_score NUMERIC(3,1),       -- 0.0-10.0
course_tier VARCHAR(20),                -- 'premium', 'medium', 'budget'

-- Metadata
data_quality_tags TEXT[],               -- ['needs_human_review', 'no_contacts_found']
```

**Full schema:** See `docs/ARCHITECTURE.md`

---

## 🎯 ClickUp Integration

### Custom Fields
**Where configured:** ClickUp workspace settings (manual setup)

| Field Name | Type | Values | Used For |
|-----------|------|--------|----------|
| `opportunity_type` | Dropdown | buy, sell, both, unknown | Campaign routing |
| `qualification_score` | Number | 0-10 | Prioritization |
| `course_tier` | Dropdown | premium, medium, budget | Service offering match |
| `contacts_found` | Number | 0+ | Data quality indicator |
| `emails_verified` | Number | 0+ | Outreach readiness |
| `data_quality` | Dropdown | complete, partial, needs_review | Human review flag |

### Tags
**Where applied:** `agents/clickup_syncer.py`

- `needs_human_review` - Incomplete data
- `no_contacts_found` - Zero contacts discovered
- `classification_uncertain` - LLM returned "UNKNOWN"
- `high_priority_both_opportunity` - Full circle opportunity

### Lists (Routing)
**Where routed:** `agents/clickup_syncer.py:routing_logic()`

| Score | Tag | List Name |
|-------|-----|-----------|
| Any | `needs_human_review` | "Human Review Queue" |
| 8.0+ | None | "Hot Leads" |
| 6.0-7.9 | None | "Qualified Leads" |
| 4.0-5.9 | None | "Nurture / Low Priority" |
| <4.0 | None | "Nurture / Low Priority" |

---

## 📂 Key Files Reference

### Core Implementation
```
teams/golf-enrichment/
├── orchestrator.py              # Main workflow coordinator
├── agents/
│   ├── llm_researcher.py       # Phase 1: LLM research + classification
│   ├── apollo_enricher.py      # Phase 2a: Apollo email discovery
│   ├── hunter_enricher.py      # Phase 2b: Hunter waterfall
│   ├── organizer.py            # Phase 3: Merge + score + write
│   └── clickup_syncer.py       # Phase 4: ClickUp task creation
├── tests/
│   ├── test_llm_classification.py   # Test BUY/SELL/BOTH accuracy
│   ├── test_contact_enrichment.py   # Test email discovery
│   ├── test_scoring.py              # Test qualification algorithm
│   └── test_end_to_end.py           # Full workflow validation
└── docs/
    └── ARCHITECTURE.md          # System design, schemas, contracts
```

### Business Context (Read-Only)
```
business-context/
├── service-offerings/
│   └── entry-point-strategy.md      # BUY/SELL/BOTH strategy
├── enrichment-requirements/
│   ├── data-priorities.md           # What data to collect
│   └── workflow-mapping.md          # Enhanced LLM prompt structure
└── v1_current_state.md              # Baseline snapshot
```

### Tracking & Progress
```
teams/golf-enrichment/
├── PROGRESS.md                  # Session log, decisions, test results
└── IMPLEMENTATION_MAP.md        # This file (quick reference)
```

---

## 🔍 Quick Lookup

### "Where is...?"

| Question | Answer |
|----------|--------|
| **BUY/SELL classification logic?** | LLM prompt in `agents/llm_researcher.py` section 1 |
| **Scoring algorithm?** | `agents/organizer.py:calculate_qualification_score()` |
| **Email discovery?** | `agents/apollo_enricher.py` → `agents/hunter_enricher.py` |
| **ClickUp routing?** | `agents/clickup_syncer.py:route_by_score()` |
| **Database writes?** | `agents/organizer.py:write_to_supabase()` |
| **Data quality tags?** | `agents/organizer.py:apply_quality_tags()` |
| **Test courses?** | `tests/fixtures/test_courses.json` |
| **Business requirements?** | `../../business-context/` |

---

## 🎯 Decision Log

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2025-10-31 | LLM does heavy lifting (research + classification) | LLM best at research, agents best at operations | Simplified architecture, fewer agents |
| 2025-10-31 | Test markdown vs JSON output | Don't prematurely optimize, validate both | Pick winner based on parsing quality |
| 2025-10-31 | Scoring in Organizer (not LLM) | Deterministic, easy to adjust weights | Consistent scores, no LLM variability |
| 2025-10-31 | Process incomplete data + tag | Don't lose leads | Human review queue, graceful degradation |
| 2025-10-31 | Citations required for contacts | Validate LLM didn't hallucinate | Data quality, trust in automation |

---

**Last Updated:** October 31, 2025
**Next Review:** After Phase 1 completion
