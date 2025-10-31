# Golf Enrichment v2 - System Architecture

**Purpose:** Technical design specification for enhanced enrichment workflow
**Status:** 🟡 Living document - updates as system evolves
**Last Updated:** October 31, 2025

---

## 🎯 System Overview

**Goal:** Automated golf course enrichment with BUY/SELL opportunity classification

**Input:** Course name, city, state
**Output:** Qualified leads in ClickUp with recommended entry strategy

**Success Criteria:**
- 70%+ email discovery rate
- 100% classification accuracy on test courses
- All courses processed (tagged for review if incomplete)
- Deterministic scoring (same inputs = same score)

---

## 🏗️ Architecture Design

### 4-Phase Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: Course Name, City, State                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: LLM Research Agent                                │
│  - Deep web research (8 sections)                           │
│  - Classify: BUY / SELL / BOTH / UNKNOWN                    │
│  - Extract contacts (names, titles, citations)              │
│  - Gather course intelligence                               │
│  Output: Structured data (markdown or JSON - TBD)           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Contact Enrichment (Apollo → Hunter Waterfall)   │
│  - Apollo: Name + company → email + LinkedIn               │
│  - Hunter: Fallback if Apollo fails                         │
│  - Verify email deliverability                              │
│  Output: Enriched contacts with verified emails             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: Organizer Agent                                   │
│  - Merge LLM data + enriched contacts                       │
│  - Calculate qualification score (deterministic)            │
│  - Apply data quality tags                                  │
│  - Write to Supabase enrichment_queue                       │
│  Output: Course record ready for ClickUp                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: ClickUp Sync Agent                                │
│  - Query: WHERE clickup_task_id IS NULL                     │
│  - Route by score + tags                                    │
│  - Create task with custom fields                           │
│  - Update clickup_task_id in Supabase                       │
│  Output: Task in appropriate ClickUp list                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Phase 1: LLM Research Agent

### Purpose
Single LLM call returns ALL course intelligence with citations

### Input Schema
```python
{
  "course_name": "Pinehurst No. 2",
  "city": "Pinehurst",
  "state": "NC"
}
```

### LLM Prompt Structure (8 Sections)

**Priority:** Section 1 is CRITICAL, rest are high-value

```
Research {course_name} in {city}, {state}.
IMPORTANT: Provide SOURCE URL for every claim.

═══════════════════════════════════════════════════════
SECTION 1: RANGE BALL OPPORTUNITY CLASSIFICATION (CRITICAL)
═══════════════════════════════════════════════════════

Classify as: BUY_OPPORTUNITY | SELL_OPPORTUNITY | BOTH_OPPORTUNITY | INSUFFICIENT_DATA

BUY OPPORTUNITY (They have waste balls we can purchase):
- Signals: "Throwing away old balls", "storage full", "worn out inventory"
- Estimate: Volume (based on range size), quality (based on course tier)
- Cite sources

SELL OPPORTUNITY (They need to purchase from us):
- Signals: "Budget too high", "looking for supplier", "poor quality", "member complaints"
- Identify: Pain type (budget vs quality), current supplier, switching triggers
- Cite sources

BOTH (HIGHEST PRIORITY - Full Circle):
- Shows BOTH waste disposal AND active purchasing needs
- Example: Large range + quality complaints + discarding old balls

═══════════════════════════════════════════════════════
SECTION 2: WATER HAZARDS (EXPANSION - NOT PRIMARY ENTRY)
═══════════════════════════════════════════════════════

Find:
- Total count of ponds, lakes, water hazards
- High-traffic hazards (island greens, lakeside par 3s)
- Ball accumulation level: high | medium | low
- Current retrieval service status
- Cite sources

═══════════════════════════════════════════════════════
SECTION 3: PRACTICE FACILITIES (CRITICAL)
═══════════════════════════════════════════════════════

Find:
- Number of hitting stations
- Range type: grass | mat | both
- Current practice ball supplier (if mentioned)
- Quality mentions ("poor condition", "need replacement")
- Recent range renovations
- Cite sources

═══════════════════════════════════════════════════════
SECTION 4: DECISION MAKERS (CRITICAL - EMAILS REQUIRED)
═══════════════════════════════════════════════════════

Find contacts for (IN PRIORITY ORDER):

1. General Manager / Owner (HIGHEST PRIORITY)
   - Full name, exact title
   - WORK EMAIL (search: newsletters, staff pages, CMAA, 990s)
   - LinkedIn profile URL
   - Phone number
   - SOURCE URL for verification

2. Superintendent / Director of Agronomy
   - Full name, exact title
   - WORK EMAIL (search: vendor sites, GCSAA, club blogs)
   - LinkedIn, phone
   - SOURCE URL

3. Director of Golf / Head Golf Professional
   - Full name, exact title
   - WORK EMAIL (search: PGA.org, newsletters, club website)
   - LinkedIn, phone
   - SOURCE URL

Verify:
- Employment is CURRENT (2024-2025)
- Email is WORK email (not personal gmail/yahoo)
- Source is legitimate

═══════════════════════════════════════════════════════
SECTION 5: COURSE POSITIONING (CRITICAL)
═══════════════════════════════════════════════════════

Classify course tier:

1. Green Fees or Membership
   - Daily green fee pricing
   - OR membership fees/initiation (if private)

2. Course Type
   - Private, semi-private, public, municipal, resort

3. Volume Indicators
   - Estimated annual rounds

4. Quality Indicators
   - Rankings, awards, championships
   - Recent renovations

Classification:
- Premium: $75+ green fees, ranked, private
- Medium: $40-75, semi-private or quality public
- Budget: <$40, municipal or budget daily-fee

═══════════════════════════════════════════════════════
SECTION 6: BUYING SIGNALS (HIGH VALUE)
═══════════════════════════════════════════════════════

Look for:

Cost Pain:
- "Practice ball budget too high"
- "Looking to reduce costs"

Quality Pain:
- "Range balls in poor condition"
- "Members complaining"

Operational Pain:
- "Throwing away old balls"
- "Multiple vendors too complicated"

Growth Signals:
- "Range renovation"
- "New superintendent" or "new GM"
- "Looking for ball supplier"

Budget Timing:
- Fiscal year end
- Procurement cycle mentions

═══════════════════════════════════════════════════════
SECTION 7: COURSE INTELLIGENCE (PERSONALIZATION)
═══════════════════════════════════════════════════════

Gather:

Ownership & History:
- Owner names, member-owned vs management
- Years in operation, recent ownership changes

Recent Projects (Last 2 Years):
- Renovations, technology upgrades, facility expansions

Current Vendors:
- Turf suppliers, irrigation, equipment, software

Awards & Recognition:
- Golf Magazine rankings, local awards, tournament hosting

Challenges:
- Water management, turf issues, budget pressures

═══════════════════════════════════════════════════════
SECTION 8: EVENT PROGRAM (NICE TO HAVE)
═══════════════════════════════════════════════════════

If available:
- Corporate outing count per year
- Charity tournaments
- Event coordinator contact
- Typical package needs

═══════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════

Structure response with clear sections.
Include source URLs for all factual claims.
Specify "Not found" if information unavailable.
Focus on CURRENT information (2024-2025).
```

### Output Format (TBD - Testing Phase)

**Option A: Structured Markdown**
```markdown
## SECTION 1: Range Ball Opportunity Classification

**Classification:** BOTH_OPPORTUNITY

**Buy Signals:**
- "Throwing away old practice balls each season" (Source: club newsletter March 2024)
- Large range with 60 stations (Source: club website)

**Sell Signals:**
- "Practice ball budget increased 40% this year" (Source: board meeting minutes)
- "Members complaining about ball quality" (Source: Yelp review Jan 2025)

**Recommended Strategy:** buy_first

[... remaining sections ...]
```

**Option B: Structured JSON**
```json
{
  "section_1_classification": {
    "type": "both",
    "buy_signals": [
      {
        "signal": "Throwing away old practice balls each season",
        "source": "https://clubnewsletter.com/march2024"
      }
    ],
    "sell_signals": [
      {
        "signal": "Practice ball budget increased 40%",
        "source": "https://boardminutes.com/2024"
      }
    ],
    "recommended_strategy": "buy_first"
  }
}
```

**Decision:** Test both on 1 course, pick winner based on:
- LLM output quality (does it follow structure?)
- Parsing reliability (can we extract data easily?)
- Citation preservation (are source URLs maintained?)

---

## 🔧 Phase 2: Contact Enrichment

### Phase 2a: Apollo Agent

**Input:**
```python
{
  "name": "John Smith",
  "title": "General Manager",
  "company": "Pinehurst Country Club",
  "source_citation": "https://cmaa.org/members/john-smith"
}
```

**Process:**
1. Query Apollo API with name + company
2. Extract email + LinkedIn
3. Verify email deliverability
4. Return enriched contact

**Output:**
```python
{
  "name": "John Smith",
  "title": "General Manager",
  "email": "jsmith@pinehurst.com",
  "email_verified": True,
  "linkedin": "linkedin.com/in/johnsmith",
  "source_citation": "https://cmaa.org/members/john-smith",
  "enrichment_source": "apollo"
}
```

**Failure Handling:** If Apollo fails, pass to Hunter Agent

---

### Phase 2b: Hunter Agent (Waterfall)

**Trigger:** Apollo returned no email

**Input:** Same as Apollo

**Process:**
1. Query Hunter API with name + domain (extracted from company)
2. Verify email with Hunter verification
3. LinkedIn discovery (if not found by Apollo)

**Output:** Same format as Apollo, with `enrichment_source: "hunter"`

**Failure Handling:** If both fail:
```python
{
  "name": "John Smith",
  "title": "General Manager",
  "email": None,
  "email_verified": False,
  "linkedin": None,
  "source_citation": "https://cmaa.org/members/john-smith",
  "enrichment_source": "none",
  "enrichment_status": "failed"
}
```

---

## ⚙️ Phase 3: Organizer Agent

### Purpose
Merge LLM data + enriched contacts, calculate score, write to database

### Input
```python
{
  "llm_data": {
    "opportunity_type": "both",
    "buy_signals": [...],
    "sell_signals": [...],
    "contacts": [  # Names from LLM
      {"name": "John Smith", "title": "GM", "citation": "..."}
    ],
    "water_hazards": {...},
    "range_details": {...},
    "course_tier": "premium",
    "buying_signals": {...}
  },
  "enriched_contacts": [  # Emails from Apollo/Hunter
    {
      "name": "John Smith",
      "email": "jsmith@club.com",
      "email_verified": True,
      "linkedin": "..."
    }
  ]
}
```

### Processing Steps

**1. Merge Contacts**
```python
def merge_contacts(llm_contacts, enriched_contacts):
    """Match by name, merge email + LinkedIn"""
    merged = []
    for llm_contact in llm_contacts:
        enriched = find_match(llm_contact['name'], enriched_contacts)
        merged.append({
            **llm_contact,
            'email': enriched.get('email'),
            'linkedin': enriched.get('linkedin'),
            'email_verified': enriched.get('email_verified', False)
        })
    return merged
```

**2. Calculate Qualification Score**

**Algorithm (Deterministic):**
```python
def calculate_qualification_score(data):
    """
    Weighted scoring: 0-10 scale

    Opportunity Type (25%):
    - BOTH: 10 points
    - High-pain SELL: 7.5 points
    - Premium BUY: 6 points
    - Standard SELL: 5 points
    - BUY (budget club): 3.5 points

    Contact Quality (30%):
    - 3+ emails verified: 10 points
    - 2 emails verified: 7 points
    - 1 email verified: 4 points
    - 0 emails: 1 point

    Facility Size (20%):
    - Water hazards (7+ = 5pts, 4-6 = 3pts, 1-3 = 1pt)
    - Range stations (50+ = 5pts, 30-49 = 3pts, 15-29 = 1pt)

    Course Tier (10%):
    - Premium: 4 points
    - Medium: 3 points
    - Budget: 2 points

    Buying Signals (15%):
    - 3+ signals: 6 points
    - 2 signals: 4 points
    - 1 signal: 2 points
    """

    score = 0

    # Opportunity type (0-2.5 scaled to 0-10 = 25%)
    opp_score = {
        'both': 2.5,
        'sell_high_pain': 1.875,
        'buy_premium': 1.5,
        'sell': 1.25,
        'buy': 0.875
    }.get(data['opportunity_type'], 0)
    score += opp_score

    # Contact quality (0-3.0 = 30%)
    verified_count = sum(1 for c in data['contacts'] if c.get('email_verified'))
    contact_score = {
        3: 3.0,
        2: 2.1,
        1: 1.2,
        0: 0.3
    }.get(min(verified_count, 3), 0.3)
    score += contact_score

    # Facility size (0-2.0 = 20%)
    water_score = min(data.get('water_hazards', {}).get('count', 0) / 7 * 0.5, 0.5) * 10
    range_score = min(data.get('range_details', {}).get('stations', 0) / 50 * 0.5, 0.5) * 10
    score += (water_score + range_score)

    # Course tier (0-1.0 = 10%)
    tier_score = {
        'premium': 0.4,
        'medium': 0.3,
        'budget': 0.2
    }.get(data.get('course_tier'), 0.2)
    score += tier_score * 10

    # Buying signals (0-1.5 = 15%)
    signal_count = len(data.get('buying_signals', []))
    signal_score = min(signal_count / 3 * 1.5, 1.5)
    score += signal_score * 10

    return round(score, 1)
```

**3. Apply Data Quality Tags**
```python
def apply_quality_tags(data):
    tags = []

    # No contacts found
    if not data.get('contacts'):
        tags.append('needs_human_review')
        tags.append('no_contacts_found')

    # No verified emails
    verified = sum(1 for c in data['contacts'] if c.get('email_verified'))
    if verified == 0:
        tags.append('needs_human_review')
        tags.append('no_emails_verified')

    # Classification uncertain
    if data.get('opportunity_type') == 'unknown':
        tags.append('needs_human_review')
        tags.append('classification_uncertain')

    # High priority BOTH opportunity
    if data.get('opportunity_type') == 'both':
        tags.append('high_priority_both_opportunity')

    return tags
```

**4. Write to Supabase**
```python
def write_to_supabase(merged_data):
    """Write course record to enrichment_queue"""

    record = {
        'course_name': merged_data['course_name'],
        'city': merged_data['city'],
        'state': merged_data['state'],

        # Opportunity classification
        'opportunity_type': merged_data['opportunity_type'],
        'buy_signals': json.dumps(merged_data['buy_signals']),
        'sell_signals': json.dumps(merged_data['sell_signals']),
        'recommended_strategy': merged_data['recommended_strategy'],

        # Qualification
        'qualification_score': merged_data['qualification_score'],
        'course_tier': merged_data['course_tier'],
        'data_quality_tags': merged_data['tags'],

        # Contacts (store in separate table or JSONB)
        'contacts': json.dumps(merged_data['contacts']),

        # Facilities
        'water_hazards': json.dumps(merged_data['water_hazards']),
        'range_details': json.dumps(merged_data['range_details']),

        # Intelligence
        'buying_signals': json.dumps(merged_data['buying_signals']),
        'course_intelligence': json.dumps(merged_data['course_intelligence']),

        # Metadata
        'enriched_at': datetime.utcnow(),
        'clickup_task_id': None  # Will be set by Phase 4
    }

    supabase.table('enrichment_queue').insert(record).execute()
```

---

## 📋 Phase 4: ClickUp Sync Agent

### Purpose
Create ClickUp tasks with routing by score + tags

### Query
```sql
SELECT * FROM enrichment_queue
WHERE clickup_task_id IS NULL
ORDER BY qualification_score DESC
```

### Routing Logic
```python
def determine_list(course):
    """Route to ClickUp list based on score + tags"""

    # Priority 1: Needs human review
    if 'needs_human_review' in course['data_quality_tags']:
        return 'Human Review Queue'

    # Priority 2: Score-based routing
    score = course['qualification_score']

    if score >= 8.0:
        return 'Hot Leads'
    elif score >= 6.0:
        return 'Qualified Leads'
    else:
        return 'Nurture / Low Priority'
```

### Task Description Template
```markdown
## {Course Name} - {Qualification Tier}-Tier Lead

**Qualification Score:** {score}/10
**Opportunity Type:** {BUY | SELL | BOTH}
**Course Tier:** {premium | medium | budget}
**Recommended Strategy:** {buy_first | sell_first | buy_then_sell}

---

## 🎯 Opportunity Classification

**Type:** {opportunity_type}

{if BUY}
**Buy Signals:**
- {signal 1 with citation}
- {signal 2 with citation}

**Estimated Volume:** {volume_estimate}
**Estimated Quality:** {quality_estimate}
{endif}

{if SELL}
**Sell Signals:**
- {signal 1 with citation}
- {signal 2 with citation}

**Pain Type:** {budget | quality | both}
**Current Supplier:** {supplier if known}
{endif}

---

## 📊 Facilities

**Water Hazards:** {count}
- High-traffic: {hole list if available}
- Accumulation: {high | medium | low}

**Practice Range:** {stations} stations
- Type: {grass | mat | both}
- Quality: {quality_mentions}

---

## 👥 Decision Makers ({count} found)

### {Name 1} - {Title 1} ⭐ PRIMARY
**Email:** {email or 'Not found'}
**LinkedIn:** {url or 'Not found'}
**Source:** {citation}

### {Name 2} - {Title 2}
...

---

## 💡 Buying Signals ({count} detected)

- {Signal 1 with citation}
- {Signal 2 with citation}

---

## 🏌️ Course Intelligence

**Recent Projects:**
- {project with year}

**Current Vendors:**
- {vendor category}: {vendor name}

**Awards:**
- {award, year}

---

## 📝 Recommended Outreach Strategy

**First Contact:** {primary_decision_maker}
**Entry Service:** {recommended_service}
**Messaging Angle:** {personalization_hook}
**Campaign:** {campaign_name}
```

### Custom Fields
```python
custom_fields = {
    'opportunity_type': course['opportunity_type'],
    'qualification_score': course['qualification_score'],
    'course_tier': course['course_tier'],
    'contacts_found': len(course['contacts']),
    'emails_verified': sum(1 for c in course['contacts'] if c.get('email_verified')),
    'data_quality': 'complete' if not course['data_quality_tags'] else 'needs_review'
}
```

### Tags
```python
tags = course['data_quality_tags']  # From Organizer
```

### Update Supabase
```python
supabase.table('enrichment_queue').update({
    'clickup_task_id': task.id,
    'synced_to_clickup_at': datetime.utcnow()
}).eq('id', course['id']).execute()
```

---

## 🗄️ Database Schema

### Supabase: `enrichment_queue` Table

```sql
CREATE TABLE enrichment_queue (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Course identification
    course_name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,

    -- Opportunity classification (NEW)
    opportunity_type VARCHAR(20),  -- 'buy', 'sell', 'both', 'unknown'
    buy_signals JSONB,
    sell_signals JSONB,
    recommended_strategy VARCHAR(50),  -- 'buy_first', 'sell_first', 'buy_then_sell'

    -- Qualification (NEW)
    qualification_score NUMERIC(3,1),  -- 0.0-10.0
    course_tier VARCHAR(20),  -- 'premium', 'medium', 'budget'
    data_quality_tags TEXT[],

    -- Contacts (store as JSONB or foreign key to contacts table)
    contacts JSONB,

    -- Facilities
    water_hazards JSONB,  -- {count, high_traffic, accumulation_level}
    range_details JSONB,  -- {stations, type, quality_mentions, supplier}

    -- Intelligence
    buying_signals JSONB,
    course_intelligence JSONB,
    event_program JSONB,

    -- ClickUp integration
    clickup_task_id VARCHAR(50),
    synced_to_clickup_at TIMESTAMPTZ,

    -- Metadata
    enriched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_clickup_sync ON enrichment_queue(clickup_task_id) WHERE clickup_task_id IS NULL;
CREATE INDEX idx_qualification_score ON enrichment_queue(qualification_score DESC);
CREATE INDEX idx_opportunity_type ON enrichment_queue(opportunity_type);
```

---

## 🧪 Testing Strategy

### Unit Tests

**1. LLM Classification Test** (`tests/test_llm_classification.py`)
```python
def test_buy_opportunity_detection():
    """Verify LLM correctly identifies BUY opportunity"""
    # Mock LLM response with buy signals
    # Parse classification
    # Assert: opportunity_type == 'buy'

def test_sell_opportunity_detection():
    # Similar for SELL

def test_both_opportunity_detection():
    # Similar for BOTH
```

**2. Scoring Algorithm Test** (`tests/test_scoring.py`)
```python
def test_scoring_deterministic():
    """Same input = same output"""
    data = {...}
    score1 = calculate_qualification_score(data)
    score2 = calculate_qualification_score(data)
    assert score1 == score2

def test_both_scores_highest():
    """BOTH opportunity scores higher than BUY or SELL alone"""
    both_data = {'opportunity_type': 'both', ...}
    buy_data = {'opportunity_type': 'buy', ...}
    assert calculate_qualification_score(both_data) > calculate_qualification_score(buy_data)
```

**3. Contact Enrichment Test** (`tests/test_contact_enrichment.py`)
```python
def test_apollo_waterfall_to_hunter():
    """If Apollo fails, Hunter runs"""
    # Mock Apollo failure
    # Run enrichment
    # Assert: Hunter was called
```

### Integration Tests

**End-to-End Test** (`tests/test_end_to_end.py`)
```python
def test_full_workflow():
    """Run all 4 phases on test course"""
    # Phase 1: LLM research
    # Phase 2: Contact enrichment
    # Phase 3: Organization + scoring
    # Phase 4: ClickUp sync
    # Assert: Task exists in ClickUp with correct fields
```

### Test Data

**Test Courses** (`tests/fixtures/test_courses.json`)
```json
{
  "buy_only": {
    "name": "Pine Valley Golf Club",
    "city": "Clementon",
    "state": "NJ",
    "expected_classification": "buy",
    "expected_score_range": [6.0, 8.0]
  },
  "sell_only": {
    "name": "Bethpage State Park (Black)",
    "city": "Farmingdale",
    "state": "NY",
    "expected_classification": "sell",
    "expected_score_range": [7.0, 9.0]
  },
  "both": {
    "name": "Pinehurst No. 2",
    "city": "Pinehurst",
    "state": "NC",
    "expected_classification": "both",
    "expected_score_range": [8.0, 10.0]
  }
}
```

---

## 📊 Design Decisions

### Why LLM Does Heavy Lifting?
- **Pro:** LLM excels at research, reasoning, extraction
- **Pro:** Fewer parsing steps, simpler architecture
- **Pro:** Can adapt to different website structures
- **Con:** Need to ensure structured output (hence testing markdown vs JSON)

### Why Scoring in Organizer (Not LLM)?
- **Pro:** Deterministic (same inputs = same score)
- **Pro:** Easy to adjust weights based on results
- **Pro:** No LLM variability or hallucination
- **Con:** Need to maintain separate scoring logic

### Why Process Incomplete Data?
- **Pro:** Don't lose leads (tag for human review instead)
- **Pro:** Graceful degradation (partial data still useful)
- **Pro:** Learn from failures (what data is hardest to find?)
- **Con:** Need human review queue management

### Why Citations Required?
- **Pro:** Validate LLM didn't hallucinate contacts
- **Pro:** Trust in automated data
- **Pro:** Human reviewers can verify sources
- **Con:** LLM might struggle to always provide URLs

---

## 🚀 Deployment Notes

### Local Development
```bash
# Run orchestrator
python teams/golf-enrichment/orchestrator.py

# Run specific phase
python teams/golf-enrichment/agents/llm_researcher.py --course "Pinehurst No. 2" --city "Pinehurst" --state "NC"
```

### Production (Future)
- Docker containerization
- Cron/scheduled runs
- Error monitoring (Sentry)
- Cost tracking (LLM API usage)

---

## 📚 References

**Business Context:**
- Entry Point Strategy: `../../../business-context/service-offerings/entry-point-strategy.md`
- Data Priorities: `../../../business-context/enrichment-requirements/data-priorities.md`
- Workflow Mapping: `../../../business-context/enrichment-requirements/workflow-mapping.md`

**Implementation:**
- Progress Log: `../PROGRESS.md`
- Code Map: `../IMPLEMENTATION_MAP.md`

**External:**
- Apollo API: https://apolloio.github.io/apollo-api-docs/
- Hunter API: https://hunter.io/api-documentation/v2
- ClickUp API: https://clickup.com/api

---

**Last Updated:** October 31, 2025
**Next Review:** After Phase 1 completion
