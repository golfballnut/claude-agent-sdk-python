# Business Context → Enrichment Workflow Mapping

**Purpose:** Connect business requirements to technical implementation
**Audience:** Engineers building/enhancing the enrichment workflow

---

## How Business Context Changes the Workflow

### Current Workflow (v1)

**Strengths:**
- ✅ 71% contact discovery success
- ✅ Apollo → Hunter waterfall
- ✅ Course intelligence collection

**Gaps:**
- ❌ No water hazard emphasis (missed retrieval opportunity sizing)
- ❌ No range size data (missed subscription fit assessment)
- ❌ No buying signal detection (missed urgency indicators)
- ❌ No course tier classification (wrong service offering match)
- ❌ Flat contact list (no decision authority mapping)

---

### Enhanced Workflow (v2) - What We Need

**Add:**
1. **Opportunity Qualification Data** (water hazards, range size)
2. **Buying Signal Detection** (pain points, timing, budget)
3. **Course Tier Classification** (green fees, rounds, membership)
4. **Decision Maker Ranking** (authority level by service type)
5. **Service-Fit Matching** (which offerings match this course?)

---

## Enhanced LLM Discovery Prompt

### V2 Prompt Template

```
Find all current decision makers and intelligence about {course_name} in {city}, {state}.

═══════════════════════════════════════════════════════
SECTION 1: WATER HAZARDS (CRITICAL - HIGHEST PRIORITY)
═══════════════════════════════════════════════════════

Find detailed information about water hazards on the course:

1. Total number of ponds, lakes, or water hazards
2. Which specific holes have water hazards (e.g., "Hole 3 - Island green")
3. Identify high-traffic hazards where balls accumulate heavily
   - Island greens
   - Lakeside par 3s
   - Forced carry water holes
4. Any mentions of:
   - Ball retrieval services (current or needed)
   - Balls accumulating in ponds
   - Water hazard maintenance
   - Environmental/aesthetic concerns about ponds

Estimate ball accumulation level: high | medium | low

═══════════════════════════════════════════════════════
SECTION 2: PRACTICE FACILITIES (CRITICAL)
═══════════════════════════════════════════════════════

Find information about the practice range:

1. Number of hitting stations or range size
2. Range type: grass tees, mats, or both
3. Current practice ball supplier (if mentioned)
4. Ball quality mentions:
   - "Old balls" or "poor condition"
   - "Need replacement" or "upgrading"
   - Member complaints about ball quality
5. Recent range improvements or renovations
6. Range ball procurement process or timing

═══════════════════════════════════════════════════════
SECTION 3: DECISION MAKERS (CRITICAL - EMAILS REQUIRED)
═══════════════════════════════════════════════════════

Find contacts for these roles (IN PRIORITY ORDER):

**1. General Manager or Owner (HIGHEST PRIORITY)**
   - Full name
   - Exact title
   - **WORK EMAIL** (search newsletters, staff pages, CMAA directory, ProPublica 990s)
   - LinkedIn profile URL
   - Phone number
   - Tenure at course (if mentioned)
   - SOURCE URL for verification

**2. Superintendent / Director of Agronomy**
   - Full name
   - Exact title
   - **WORK EMAIL** (search vendor websites like Mach 1 Greens, GCSAA, state GCSA chapters, club blogs)
   - LinkedIn profile URL
   - Phone number
   - Professional credentials (CGCS, if mentioned)
   - SOURCE URL

**3. Director of Golf / Head Golf Professional**
   - Full name
   - Exact title (Director of Golf vs Head Pro)
   - **WORK EMAIL** (search PGA.org, club newsletters on AnyFlip, club website /golf page)
   - LinkedIn profile URL
   - Phone number
   - PGA credentials
   - SOURCE URL

**4. Event Coordinator (if course hosts events)**
   - Full name, email, phone

For EACH contact, verify:
- Employment is CURRENT (2024-2025)
- Email is WORK email (not personal gmail/yahoo)
- Source is legitimate (not aggregator sites like ContactOut unless verified elsewhere)

═══════════════════════════════════════════════════════
SECTION 4: COURSE POSITIONING (CRITICAL)
═══════════════════════════════════════════════════════

Classify the course tier:

1. **Green Fees or Membership:**
   - Daily green fee pricing
   - OR membership fees/initiation fees (if private)

2. **Course Type:**
   - Private country club
   - Semi-private
   - Public daily-fee
   - Municipal
   - Resort

3. **Volume Indicators:**
   - Estimated annual rounds (if mentioned)
   - Busy season or capacity mentions

4. **Quality Indicators:**
   - Course rankings or awards (2024-2025)
   - Recent renovations or improvements
   - Championship status or tournament hosting

Based on this, classify as:
- **Elite/Premium (Tier 1):** Green fees $150+, ranked nationally, exclusive private
- **Premium Private (Tier 2):** Green fees $75-150, established private clubs
- **Mid-Market (Tier 3):** Green fees $40-75, semi-private or better public
- **Budget (Tier 4):** Green fees $20-40, municipal or budget daily-fee

═══════════════════════════════════════════════════════
SECTION 5: BUYING SIGNALS (HIGH VALUE)
═══════════════════════════════════════════════════════

Look for indicators of readiness to buy:

**Cost Pain Signals:**
- "Practice ball budget too high"
- "Looking to reduce costs"
- "Budget constraints" mentioned

**Quality Pain Signals:**
- "Range balls in poor condition"
- "Members complaining about ball quality"
- "Need to upgrade practice balls"

**Operational Pain Signals:**
- "Throwing away old balls" or "waste"
- "Multiple vendors too complicated"
- "Ponds need cleaning" or "ball accumulation"

**Growth/Change Signals:**
- "Range renovation" or expansion
- "New superintendent" or "new GM" hired
- "Looking for ball supplier" or vendor search

**Budget Timing Signals:**
- Fiscal year end dates
- Procurement cycle mentions
- Annual contract renewals

═══════════════════════════════════════════════════════
SECTION 6: COURSE INTELLIGENCE (PERSONALIZATION)
═══════════════════════════════════════════════════════

Gather details for outreach personalization:

**Ownership & History:**
- Owner names (if independent)
- Member-owned vs management company
- Years in operation
- Recent ownership changes

**Recent Projects (Last 2 Years):**
- Renovations (greens, fairways, clubhouse)
- Technology upgrades (irrigation, GPS)
- Facility expansions
- Major purchases

**Current Vendors & Technology:**
- Turf suppliers (Mach 1 Greens, seed companies)
- Irrigation systems (Rain Bird, Toro)
- Golf equipment (John Deere, Toro mowers)
- Software/tech (Tagmarshal, ForeUp, GolfNow)

**Awards & Recognition:**
- Golf Magazine rankings
- Local "Best Of" awards
- Tournament hosting (USGA, state championships)
- GCSAA environmental awards

**Challenges Mentioned:**
- Water management issues
- Turf disease or maintenance challenges
- Member satisfaction concerns
- Budget pressures
- Competitive pressures

═══════════════════════════════════════════════════════
SECTION 7: EVENT PROGRAM (NICE TO HAVE)
═══════════════════════════════════════════════════════

If information is available:

- Number of corporate outings per year
- Charity tournaments hosted
- Member-guest events
- Event coordinator contact info
- Typical package needs (branded items, custom balls)

═══════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════

Structure your response with clear sections for each category above.
Include source URLs for all factual claims.
Specify "Not found" if information is not available.
Focus on CURRENT information (2024-2025).
```

---

## Enhanced Enrichment Queue Schema

### New Fields for `enrichment_queue` Table

```sql
ALTER TABLE enrichment_queue ADD COLUMN IF NOT EXISTS

  -- Opportunity Sizing
  water_hazard_count INTEGER,
  water_hazard_details JSONB,  -- {high_traffic: [...], total: X}
  range_station_count INTEGER,
  range_quality_mentions TEXT,

  -- Course Classification
  course_tier VARCHAR(20),  -- 'tier_1', 'tier_2', 'tier_3', 'tier_4'
  green_fee_range VARCHAR(50),
  estimated_annual_rounds INTEGER,

  -- Buying Signals
  buying_signals JSONB,  -- {cost_pain: [...], quality_pain: [...], ...}
  buying_signal_count INTEGER,
  urgency_level VARCHAR(20),  -- 'high', 'medium', 'low'

  -- Decision Maker Authority
  decision_maker_authority VARCHAR(50),  -- 'contract', 'budget', 'operational'
  recommended_entry_service VARCHAR(50),  -- 'retrieval', 'range_balls', 'subscription'

  -- Qualification Scoring
  qualification_score NUMERIC(3,1),  -- 0.0-10.0
  qualification_tier VARCHAR(1);  -- 'A', 'B', 'C', 'D'
```

---

## Enhanced Parsing Agent Logic

### After LLM Discovery

```python
async def parse_llm_response_v2(raw_response):
    """
    Enhanced parsing to extract business-critical data
    """

    parsed = {
        "contacts": [],
        "opportunity_data": {},
        "qualification_data": {},
        "course_intelligence": {}
    }

    # SECTION 1: Parse Water Hazards
    water_data = extract_water_hazards(raw_response)
    parsed["opportunity_data"]["water_hazards"] = {
        "total_count": water_data["total"],
        "high_traffic": water_data["high_traffic_holes"],
        "accumulation_level": water_data["estimate"],  # high/medium/low
        "current_retrieval": water_data.get("current_service")
    }

    # Calculate retrieval opportunity score
    hazard_score = calculate_hazard_score(water_data["total"])


    # SECTION 2: Parse Range Details
    range_data = extract_range_info(raw_response)
    parsed["opportunity_data"]["range"] = {
        "station_count": range_data["stations"],
        "range_type": range_data["type"],  # grass/mat/both
        "quality_mentions": range_data["quality_mentions"],
        "current_supplier": range_data.get("supplier")
    }

    # Calculate range opportunity score
    range_score = calculate_range_score(range_data["stations"])


    # SECTION 3: Parse Decision Makers with Authority
    contacts = extract_contacts_with_authority(raw_response)

    for contact in contacts:
        # Determine decision authority
        contact["decision_authority"] = map_authority(contact["title"])

        # Determine relevant services
        contact["relevant_services"] = map_services_to_role(contact["title"])

        # Priority ranking (1=highest)
        contact["priority_rank"] = rank_decision_maker(contact["title"])

        parsed["contacts"].append(contact)

    # Calculate contact quality score
    contact_score = calculate_contact_score(contacts)


    # SECTION 4: Classify Course Tier
    tier_data = extract_course_positioning(raw_response)
    parsed["qualification_data"]["course_tier"] = classify_tier(
        green_fees=tier_data["green_fees"],
        course_type=tier_data["type"],
        indicators=tier_data["quality_indicators"]
    )

    # Calculate tier score
    tier_score = calculate_tier_score(parsed["qualification_data"]["course_tier"])


    # SECTION 5: Extract Buying Signals
    signals = extract_buying_signals(raw_response)
    parsed["qualification_data"]["buying_signals"] = {
        "cost_pain": signals["cost"],
        "quality_pain": signals["quality"],
        "operational_pain": signals["operational"],
        "growth_signals": signals["growth"],
        "budget_timing": signals["timing"]
    }

    # Calculate urgency score
    signal_score = calculate_signal_score(signals)


    # SECTION 6: Course Intelligence
    parsed["course_intelligence"] = extract_course_intelligence(raw_response)


    # CALCULATE OVERALL QUALIFICATION SCORE
    qualification_score = (
        hazard_score * 0.15 +      # Water hazards (15%)
        range_score * 0.15 +       # Range size (15%)
        tier_score * 0.10 +        # Course tier (10%)
        contact_score * 0.30 +     # Decision makers (30%)
        signal_score * 0.30        # Buying signals (30%)
    )

    parsed["qualification_data"]["score"] = round(qualification_score, 1)
    parsed["qualification_data"]["tier"] = assign_tier(qualification_score)


    # DETERMINE RECOMMENDED ENTRY SERVICE
    parsed["qualification_data"]["recommended_service"] = determine_entry_service(
        water_hazards=water_data,
        range_data=range_data,
        course_tier=parsed["qualification_data"]["course_tier"],
        buying_signals=signals
    )

    return parsed
```

---

## Service Recommendation Logic

```python
def determine_entry_service(water_hazards, range_data, course_tier, buying_signals):
    """
    Map course characteristics → recommended first service
    """

    # High water hazards = retrieval entry
    if water_hazards["total"] >= 5:
        return "retrieval_service"

    # Large range + quality complaints = range balls
    if range_data["stations"] >= 30 and buying_signals["quality"]:
        return "range_balls"

    # Tier 1-2 + large range = subscription
    if course_tier in ["tier_1", "tier_2"] and range_data["stations"] >= 50:
        return "subscription_program"

    # Cost pain + any range = range balls (cost savings pitch)
    if buying_signals["cost"] and range_data["stations"] > 0:
        return "range_balls"

    # Event mentions = outing packages
    if buying_signals.get("event_program"):
        return "outing_packages"

    # Default: range balls (most universal)
    return "range_balls"
```

---

## ClickUp Task Creation (Enhanced)

### Task Description Template

```markdown
## {Course Name} - {Qualification Tier}-Tier Lead

**Qualification Score:** {score}/10
**Recommended Entry Service:** {service}

---

## Opportunity Summary

**Water Hazards:** {count} ({estimate} ball accumulation)
- High-traffic hazards: {hole_list}
- **Retrieval Opportunity:** {size_estimate}

**Practice Range:** {stations} stations
- Quality mentions: {quality_notes}
- Current supplier: {supplier}
- **Range Ball Opportunity:** {size_estimate}

**Course Tier:** {tier_name}
- Green fees: {fees}
- Type: {course_type}
- **Service Fit:** {recommended_offerings}

---

## Decision Makers ({count} found)

### {Name 1} - {Title 1} ⭐ PRIMARY
**Authority:** {authority_type}
**Email:** {email}
**LinkedIn:** {linkedin}
**Phone:** {phone}
**Relevant Services:** {services_list}
**Outreach Priority:** {priority}

### {Name 2} - {Title 2}
...

---

## Buying Signals ({count} detected)

**Urgency Level:** {high/medium/low}

- {Signal 1}
- {Signal 2}
- {Signal 3}

---

## Course Intelligence (Personalization)

**Recent Projects:**
- {Project description with year}

**Current Vendors:**
- {Vendor type}: {Vendor name}

**Awards:**
- {Award name, year}

**Challenges:**
- {Challenge 1}

---

## Recommended Outreach Strategy

**First Contact:** {primary_decision_maker}
**Entry Service:** {recommended_service}
**Messaging Angle:** {personalization_hook}
**Timing:** {urgency_based_timing}
```

### Custom Fields (Enhanced)

```javascript
{
  // Opportunity Sizing
  "water_hazard_count": 8,
  "range_station_count": 50,
  "qualification_score": 8.5,
  "qualification_tier": "A",

  // Classification
  "course_tier": "Premium Private (Tier 2)",
  "green_fee_range": "$75-150",

  // Entry Strategy
  "recommended_service": "Retrieval Service",
  "primary_contact": "John Smith, GM",
  "primary_contact_email": "jsmith@course.com",

  // Urgency
  "buying_signal_count": 3,
  "urgency_level": "High",

  // Personalization
  "recent_project": "Range renovation 2024",
  "key_vendor": "Mach 1 Greens (turf)"
}
```

---

## Workflow Decision Tree

```
LLM Discovery Complete
    ↓
Parse Response (extract structured data)
    ↓
Calculate Qualification Score
    ↓
    ├─→ Score ≥8.0: A-Tier
    │       ↓
    │   Create ClickUp Task in "Hot Leads" List
    │   Recommended: Immediate outreach (same day)
    │
    ├─→ Score 6.0-7.9: B-Tier
    │       ↓
    │   Create ClickUp Task in "Qualified Leads" List
    │   Recommended: Sequence outreach (within 3 days)
    │
    ├─→ Score 4.0-5.9: C-Tier
    │       ↓
    │   Create ClickUp Task in "Nurture Leads" List
    │   Recommended: Educational drip campaign
    │
    └─→ Score <4.0: D-Tier
            ↓
        Archive in Supabase (don't create ClickUp task)
        Revisit in 6-12 months
```

---

## Testing Validation

### Test Cases to Validate Enhanced Workflow

**Test 1: High Water Hazard Course**
- Input: Course with 8 water hazards, 30-station range, GM + Super found
- Expected Output:
  - Water hazard score: 10/10
  - Range score: 7/10
  - Recommended service: Retrieval
  - Qualification tier: A or B
  - ClickUp task created with retrieval emphasis

**Test 2: Large Range, Few Hazards**
- Input: Course with 2 ponds, 60-station range, Dir of Golf found
- Expected Output:
  - Water hazard score: 3/10
  - Range score: 10/10
  - Recommended service: Range balls or Subscription
  - Qualification tier: B
  - ClickUp task created with range ball emphasis

**Test 3: Municipal Course (Easy Contacts, Budget Focus)**
- Input: Municipal, 5 hazards, 40 stations, GM + Super + Dir Golf all found (public directory)
- Expected Output:
  - High contact score (3 contacts)
  - Budget tier classification (Tier 4)
  - Recommended service: Range balls (cost savings message)
  - Qualification tier: B
  - ClickUp task emphasizes taxpayer value

---

## Related Documents

- **Data Priorities:** `data-priorities.md` (what data to collect)
- **Qualification Criteria:** `../customer-segmentation/qualification-criteria.md`
- **Decision Hierarchy:** `../buyer-personas/decision-hierarchy.md`
- **Service Offerings:** `../service-offerings/` (offering → course fit)
