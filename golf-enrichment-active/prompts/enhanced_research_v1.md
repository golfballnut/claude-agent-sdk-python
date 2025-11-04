# Golf Course Research Prompt - Enhanced v1

You are researching **{COURSE_NAME}** in **{CITY}, {STATE}** to gather comprehensive intelligence for a range ball and golf supply business.

**CRITICAL INSTRUCTIONS:**
1. Provide SOURCE URL for EVERY factual claim
2. Focus on CURRENT information (2024-2025 only)
3. Return response as valid JSON matching the schema below
4. Use `null` or `"not_found"` when data is unavailable
5. Be thorough - this is comprehensive research, not a quick lookup

---

## SECTION 1: RANGE BALL OPPORTUNITY CLASSIFICATION ⚠️ CRITICAL

**Objective:** Determine if this course represents a BUY, SELL, or BOTH opportunity for range ball services.

### BUY OPPORTUNITY (We purchase their waste balls)
Look for signals that the course has waste/used range balls they need to dispose of:
- "Throwing away old balls" / "discarding worn practice balls"
- "Storage full" / "too many old balls"
- "Recycling program" / "selling used balls"
- Large practice range (50+ stations) at a busy course
- Premium/resort course (high ball turnover)

**If found, gather:**
- Specific quotes mentioning ball disposal
- Estimated range size (# of stations)
- Course tier (affects ball volume/quality)
- Any mentions of current ball recycling/sales

### SELL OPPORTUNITY (They need to purchase from a supplier)
Look for pain points indicating they need a better range ball supplier:
- "Practice ball costs too high" / "budget concerns"
- "Range balls poor quality" / "worn out"
- "Member complaints about practice balls"
- "Looking for ball supplier"
- "Current supplier unreliable"

**If found, gather:**
- Specific pain points (cost vs quality vs reliability)
- Current supplier name (if mentioned)
- Budget/procurement timing mentions
- Quotes from reviews, newsletters, or announcements

### CLASSIFICATION RULES
- **BOTH**: Shows BOTH waste disposal needs AND purchasing pain points (HIGHEST VALUE)
- **BUY**: Only disposal/excess ball signals found
- **SELL**: Only purchasing pain/need signals found
- **INSUFFICIENT_DATA**: Cannot determine from available information

**Output for this section:**
```json
{
  "classification": "BOTH | BUY | SELL | INSUFFICIENT_DATA",
  "confidence": "high | medium | low",
  "buy_signals": [
    {
      "signal": "Quote or fact",
      "source": "https://..."
    }
  ],
  "sell_signals": [
    {
      "signal": "Quote or fact",
      "source": "https://..."
    }
  ],
  "recommended_strategy": "buy_first | sell_first | approach_both | insufficient_data",
  "reasoning": "1-2 sentences explaining the classification"
}
```

---

## SECTION 2: WATER HAZARDS (EXPANSION OPPORTUNITY)

**Objective:** Assess potential for ball retrieval services (secondary offering).

Look for:
- Total count of ponds, lakes, water hazards on the course
- Mentions of specific hazards (e.g., "island green on hole 7")
- High-traffic holes with water (signature holes, par 3s over water)
- Ball retrieval service mentions (current provider or need)
- Drainage/water management projects

**Output for this section:**
```json
{
  "water_hazards": {
    "total_count": 0,
    "details": [
      {
        "location": "Hole 7, island green",
        "type": "pond | lake | stream",
        "notes": "High-traffic par 3",
        "source": "https://..."
      }
    ],
    "ball_accumulation_estimate": "high | medium | low | unknown",
    "current_retrieval_service": "Company name or null",
    "source": "https://... (for retrieval service info)"
  }
}
```

---

## SECTION 3: PRACTICE FACILITIES (CRITICAL FOR VOLUME ESTIMATES)

**Objective:** Understand the size and quality of practice facilities.

Look for:
- Number of hitting stations / range size
- Range type: grass tees, mat tees, or both
- Practice area amenities (putting green, short game area, bunkers)
- Current practice ball supplier (if mentioned)
- Ball quality mentions ("poor condition", "need replacement")
- Recent range renovations or improvements

**Output for this section:**
```json
{
  "practice_facilities": {
    "range": {
      "stations": 0,
      "type": "grass | mat | both | unknown",
      "size_description": "Brief description",
      "source": "https://..."
    },
    "current_supplier": {
      "name": "Supplier name or null",
      "source": "https://..."
    },
    "quality_mentions": [
      {
        "mention": "Quote about ball quality",
        "sentiment": "positive | negative | neutral",
        "source": "https://..."
      }
    ],
    "recent_renovations": [
      {
        "project": "Range expansion completed 2024",
        "date": "2024",
        "source": "https://..."
      }
    ]
  }
}
```

---

## SECTION 4: DECISION MAKERS (CRITICAL - REQUIRED FOR OUTREACH)

**Objective:** Find verified contact information for key decision makers.

**Priority order:**
1. General Manager / Owner (HIGHEST PRIORITY)
2. Golf Course Superintendent / Director of Agronomy
3. Director of Golf / Head Golf Professional
4. Assistant Golf Professionals (if relevant)

**For each contact, find:**
- Full name
- Exact current title
- **Work email** (search: club newsletters, staff pages, CMAA directory, Form 990s, vendor sites)
- Phone number (direct line preferred)
- LinkedIn profile URL
- Employment verification (must be CURRENT 2024-2025)

**Sources to check:**
- Club website staff directory
- Club newsletters/announcements (PDFs, member updates)
- CMAA (Club Managers Association) member directory
- GCSAA (Golf Course Superintendents Association)
- PGA member directory
- LinkedIn profiles (verify current employment)
- Local news articles about staff changes
- Form 990 filings (for non-profit courses)

**Output for this section:**
```json
{
  "decision_makers": [
    {
      "name": "John Smith",
      "title": "General Manager",
      "priority": 1,
      "email": "jsmith@example.com or null",
      "email_source": "https://...",
      "phone": "+1-555-123-4567 or null",
      "phone_source": "https://...",
      "linkedin": "https://linkedin.com/in/... or null",
      "employment_verified": true,
      "verification_source": "https://...",
      "notes": "Any relevant context about this person"
    }
  ]
}
```

---

## SECTION 5: COURSE TIER CLASSIFICATION (AFFECTS BALL VOLUME/QUALITY)

**Objective:** Classify the course to estimate ball volume and quality needs.

Look for:
- **Pricing:** Daily green fees OR membership/initiation fees (if private)
- **Course type:** Private, semi-private, public, municipal, resort
- **Volume indicators:** Estimated annual rounds, tee time availability
- **Quality indicators:** Rankings (Golf Digest, Golf Magazine), awards, tournament hosting
- **Amenities:** Clubhouse quality, additional facilities

**Classification guidelines:**
- **Premium:** $75+ green fees, ranked courses, high-end private clubs, resorts
- **Medium:** $40-75 green fees, quality public or semi-private
- **Budget:** <$40 green fees, municipal courses, daily-fee value courses

**Output for this section:**
```json
{
  "course_tier": {
    "classification": "premium | medium | budget",
    "confidence": "high | medium | low",
    "pricing": {
      "green_fee_range": "$40-60 or null",
      "membership_fee": "$50,000 initiation or null",
      "source": "https://..."
    },
    "course_type": "private | semi-private | public | municipal | resort",
    "volume_indicators": {
      "estimated_annual_rounds": "50,000 or unknown",
      "source": "https://..."
    },
    "quality_indicators": [
      {
        "indicator": "Ranked #47 in state by Golf Digest",
        "source": "https://..."
      }
    ]
  }
}
```

---

## SECTION 6: BUYING SIGNALS (IDENTIFIES HOT OPPORTUNITIES)

**Objective:** Detect time-sensitive signals that indicate active buying intent or pain.

Look for:

### Cost Pain Signals
- "Practice ball budget increased X%"
- "Looking to reduce costs"
- "Seeking cost-effective supplier"

### Quality Pain Signals
- "Range balls in poor condition"
- "Member complaints about ball quality"
- "Need better practice balls"

### Operational Pain Signals
- "Too many vendors, need consolidation"
- "Current supplier unreliable"
- "Ball inventory management challenges"

### Change/Growth Signals
- "New General Manager" / "New Superintendent" (opportunity window)
- "Range renovation project"
- "Facility expansion"
- "Budget cycle / fiscal year mentions"

### Active Search Signals
- "Accepting bids" / "RFP for supplies"
- "Looking for ball supplier"
- "Evaluating vendors"

**Output for this section:**
```json
{
  "buying_signals": [
    {
      "signal": "New superintendent hired in Q1 2025",
      "category": "change_opportunity",
      "urgency": "high | medium | low",
      "source": "https://..."
    }
  ],
  "overall_urgency": "immediate | near_term | long_term | none",
  "reasoning": "Brief explanation of timing"
}
```

---

## SECTION 7: COURSE INTELLIGENCE (PERSONALIZATION DATA)

**Objective:** Gather contextual information for personalized outreach.

Look for:

### Ownership & Structure
- Owner names (if independent)
- Management company (if applicable)
- Member-owned vs investor-owned
- Years in operation
- Recent ownership changes

### Recent Projects (Last 2 Years)
- Course renovations (greens, bunkers, irrigation)
- Technology upgrades (GPS systems, booking software)
- Facility improvements (clubhouse, pro shop)
- Environmental projects (water conservation, sustainability)

### Current Vendors (If Mentioned)
- Turf/seed suppliers
- Irrigation equipment
- Maintenance equipment (mowers, etc.)
- Technology providers
- Other golf supplies

### Recognition & Awards
- Golf magazine rankings
- Tournament hosting (PGA, USGA events)
- Environmental certifications (Audubon, etc.)
- Local "best of" awards

### Challenges (If Mentioned)
- Water restrictions / drought concerns
- Budget constraints
- Competitive market pressures
- Regulatory/environmental challenges

**Output for this section:**
```json
{
  "course_intelligence": {
    "ownership": {
      "structure": "independent | management_company | member_owned | municipal",
      "details": "Additional context",
      "source": "https://..."
    },
    "recent_projects": [
      {
        "project": "Greens renovation",
        "year": 2024,
        "description": "Brief details",
        "source": "https://..."
      }
    ],
    "vendors": [
      {
        "category": "turf_supplies",
        "vendor_name": "Company Name",
        "source": "https://..."
      }
    ],
    "awards": [
      {
        "award": "Top 10 Public Course in State",
        "year": 2024,
        "source": "https://..."
      }
    ],
    "challenges": [
      {
        "challenge": "Water restrictions due to drought",
        "impact": "Brief description",
        "source": "https://..."
      }
    ]
  }
}
```

---

## SECTION 8: EVENT PROGRAM (NICE TO HAVE)

**Objective:** Understand corporate/event business for potential bulk ball needs.

Look for:
- Corporate outing packages
- Tournament hosting (charity, member-guest, league play)
- Event coordinator contact information
- Typical package inclusions
- Annual event count estimates

**Output for this section:**
```json
{
  "event_program": {
    "has_program": true,
    "details": [
      {
        "type": "corporate_outings",
        "frequency": "50+ per year or unknown",
        "typical_package": "Brief description",
        "source": "https://..."
      }
    ],
    "event_coordinator": {
      "name": "Jane Doe or null",
      "email": "events@example.com or null",
      "phone": "+1-555-555-5555 or null",
      "source": "https://..."
    }
  }
}
```

---

## FINAL JSON RESPONSE STRUCTURE

Combine all sections into a single JSON response:

```json
{
  "course_name": "{COURSE_NAME}",
  "city": "{CITY}",
  "state": "{STATE}",
  "research_date": "2025-10-31",
  "section_1_classification": { ... },
  "section_2_water_hazards": { ... },
  "section_3_practice_facilities": { ... },
  "section_4_decision_makers": [ ... ],
  "section_5_course_tier": { ... },
  "section_6_buying_signals": [ ... ],
  "section_7_course_intelligence": { ... },
  "section_8_event_program": { ... },
  "research_notes": "Any challenges encountered, data quality notes, or recommendations"
}
```

---

## RESEARCH GUIDELINES

1. **Source Quality:** Prioritize official sources (course website, professional associations, verified news) over social media or unverified sites
2. **Current Data:** Verify employment dates, project timelines, and pricing are current (2024-2025)
3. **Citation Format:** Always provide full URL, not just domain name
4. **Handling Missing Data:** Use `null` for missing single values, empty arrays `[]` for missing lists, and `"not_found"` or `"unknown"` for classification fields
5. **Thoroughness:** This is deep research - check multiple sources, cross-reference information, be comprehensive

**Search Strategy Suggestions:**
- Start with course's official website
- Check golf association directories (CMAA, GCSAA, PGA)
- Search for recent news/announcements
- Look for newsletters, board meeting minutes (often in PDFs)
- Check review sites (Google, Yelp) for operational insights
- Search Form 990s for non-profit courses (contact info often listed)
- Use LinkedIn to verify current employment and find additional contacts

**Now, begin comprehensive research on {COURSE_NAME} in {CITY}, {STATE}.**
