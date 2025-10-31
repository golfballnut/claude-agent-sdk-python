# Data Collection Priorities

**Purpose:** Define WHAT data to collect and WHY it matters for Links Choice
**Audience:** LLM prompt engineers, enrichment workflow builders

---

## Priority 1: Critical Data (Deal Breakers)

### Water Hazards ⭐ **HIGHEST PRIORITY**

**Why Critical:**
- Retrieval service = entry point + raw materials
- Quantifies opportunity size ($X per hazard)
- Differentiates high-value vs low-value courses

**What to Collect:**
```json
{
  "water_hazards": {
    "total_count": 8,
    "high_traffic_hazards": [
      "Hole 3 - Island green",
      "Hole 17 - Lakeside par 3"
    ],
    "ball_accumulation_estimate": "high" | "medium" | "low",
    "hazard_types": ["ponds", "lakes", "creeks"],
    "current_retrieval": "in-house" | "vendor" | "none"
  }
}
```

**LLM Prompt Addition:**
```
CRITICAL: Find the number of ponds, lakes, or water hazards on the course.
Specifically identify:
- Total count of water hazards
- Which holes have island greens or lakeside hazards
- Any mentions of ball accumulation or retrieval needs
```

**Scoring Impact:**
- 7+ hazards: 10 points (A-tier opportunity)
- 4-6 hazards: 7 points
- 1-3 hazards: 3 points
- 0 hazards: DISQUALIFY (wrong fit)

---

### Practice Range Size

**Why Critical:**
- Range ball sales = primary revenue stream
- Subscription program fit (50+ stations = ideal)
- Determines annual volume/revenue potential

**What to Collect:**
```json
{
  "practice_facilities": {
    "has_driving_range": true,
    "range_stations": 50,
    "range_type": "grass" | "mat" | "both",
    "current_ball_supplier": "Titleist practice balls",
    "ball_quality_mentions": ["old balls", "need replacement"],
    "recent_range_renovation": "2024-01 renovation"
  }
}
```

**LLM Prompt Addition:**
```
Find information about the practice range:
- Number of hitting stations
- Grass or mat tees
- Current practice ball supplier
- Any mentions of ball quality or replacement needs
- Recent range improvements or renovations
```

**Scoring Impact:**
- 50+ stations: 10 points (subscription fit)
- 30-49 stations: 7 points (sales opportunity)
- 15-29 stations: 4 points (small opportunity)
- No range: 0 points (pro shop only, different offering)

---

### Decision Maker Contacts ⭐ **HIGHEST PRIORITY**

**Why Critical:**
- Can't sell if can't reach them
- Quality of contact = close rate
- Multiple contacts = multiple entry points

**What to Collect (Priority Order):**

**1. General Manager / Owner:**
```json
{
  "name": "John Smith",
  "title": "General Manager / COO",
  "email": "jsmith@course.com",  // WORK email critical
  "phone": "(555) 123-4567",
  "linkedin_url": "linkedin.com/in/johnsmith",
  "source_url": "https://cmaa.org/...",
  "source_type": "cmaa_directory",
  "verified_current": true,
  "verification_sources": ["CMAA 2025", "Club website"]
}
```

**2. Superintendent:**
```json
{
  "name": "Mike Jones",
  "title": "Superintendent / Director of Agronomy",
  "email": "mjones@course.com",
  "source_type": "vendor_website" | "gcsaa" | "club_blog"
}
```

**3. Director of Golf:**
```json
{
  "name": "Sarah Williams",
  "title": "Director of Golf / Head Golf Professional",
  "email": "swilliams@course.com",
  "source_type": "pga_directory" | "club_newsletter"
}
```

**LLM Prompt Addition:**
```
CRITICAL: Find work email addresses (not personal) for:
1. General Manager or Owner (highest priority)
2. Superintendent / Director of Agronomy
3. Director of Golf / Head Golf Professional

For EACH person include:
- Full name and exact title
- Work email (REQUIRED - search newsletters, staff pages, vendor sites)
- LinkedIn profile URL
- Phone number (direct or department)
- SOURCE LINKS for verification
```

**Scoring Impact:**
- 4+ contacts with emails: 15 points
- 3 contacts with emails: 12 points
- 2 contacts with emails: 8 points
- 1 contact with email: 5 points
- No emails: 2 points or DISQUALIFY

---

### Course Tier Classification

**Why Critical:**
- Determines service offering fit
- Pricing strategy varies by tier
- Messaging different per tier

**What to Collect:**
```json
{
  "course_positioning": {
    "tier": "premium_private" | "mid_market" | "budget",
    "green_fees": "$75-150",
    "membership_type": "private" | "semi-private" | "public",
    "membership_fees": "$10,000/year initiation",
    "estimated_annual_rounds": 35000,
    "course_condition": "championship" | "excellent" | "good" | "basic"
  }
}
```

**LLM Prompt Addition:**
```
Find course financial positioning:
- Green fee pricing (or membership fees if private)
- Course type (private, semi-private, public, municipal)
- Estimated annual rounds played
- Course condition/quality indicators
- Recent rankings or awards
```

**Scoring Impact:**
- Tier 1 (Elite): 5 points (hard to close, save for later)
- Tier 2 (Premium Private): 10 points (SWEET SPOT)
- Tier 3 (Mid-Market): 8 points (volume play)
- Tier 4 (Budget): 5 points (low margin)

---

## Priority 2: High-Value Data (Qualification)

### Buying Signals

**Why Valuable:**
- Urgency = faster close
- Active pain = higher priority
- Budget timing = close rate

**What to Collect:**
```json
{
  "buying_signals": {
    "cost_complaints": ["practice ball budget too high"],
    "quality_complaints": ["range balls in poor condition", "members complaining"],
    "waste_mentions": ["throwing away old balls"],
    "vendor_search": ["looking for new supplier"],
    "upcoming_projects": ["range renovation Q2 2025"],
    "budget_cycle": ["fiscal year ends March"],
    "procurement_mentions": ["RFP for ball supplier"]
  }
}
```

**LLM Prompt Addition:**
```
Look for buying signals and pain points:
- Cost complaints (budget pressure, too expensive)
- Quality issues (poor condition, member complaints)
- Waste mentions (throwing away balls)
- Vendor changes (looking for supplier, RFP)
- Upcoming projects (renovations, improvements)
- Budget timing (fiscal year, procurement cycle)
```

**Scoring Impact:**
- 3+ buying signals: 15 points
- 2 signals: 10 points
- 1 signal: 5 points
- No signals: 0 points

---

### Course Intelligence (Outreach Personalization)

**Why Valuable:**
- Personalized outreach = higher response rate
- Shows we did research = credibility
- Find entry angle = conversation starter

**What to Collect:**
```json
{
  "course_intelligence": {
    "ownership": {
      "type": "member_owned" | "independent" | "resort" | "municipal",
      "details": "Jack & Shirley McDougall since 2021"
    },
    "recent_projects": [
      {
        "type": "renovation",
        "description": "Range expansion, 20 new stations",
        "year": 2024,
        "source": "club website announcement"
      }
    ],
    "vendors": [
      {
        "category": "turf",
        "vendor": "Mach 1 Greens",
        "product": "Ultradwarf bermudagrass",
        "source": "vendor case study"
      }
    ],
    "awards": [
      {
        "award": "#13 Best US Public Course",
        "organization": "Golf Magazine",
        "year": 2024
      }
    ],
    "challenges": [
      "Water management in summer heat",
      "Member complaints about pace of play"
    ]
  }
}
```

**LLM Prompt Addition:**
```
Gather course intelligence for personalization:
- Ownership structure and history
- Recent projects (last 2 years): renovations, expansions, improvements
- Current vendors: turf suppliers, irrigation, equipment, technology
- Awards or rankings (2024-2025)
- Challenges or pain points mentioned publicly
- Unique characteristics or achievements
```

**Usage:**
- Personalize email subject lines
- Reference in outreach ("I saw you just renovated...")
- Show we understand their needs
- Build credibility and rapport

---

## Priority 3: Nice-to-Have Data (Enhancement)

### Event Program Details

**Why Useful:**
- Outing packages = additional revenue
- Events = less price-sensitive (client pays)
- Cross-sell opportunity

**What to Collect:**
```json
{
  "event_program": {
    "annual_outing_count": 15,
    "event_types": ["corporate", "charity", "member_guest"],
    "event_coordinator": {
      "name": "Jane Doe",
      "email": "events@course.com"
    },
    "typical_package_needs": ["144 player outing", "branded tees"]
  }
}
```

**LLM Prompt (Optional):**
```
If found, capture event/outing information:
- Number of events hosted annually
- Event types (corporate, charity, tournaments)
- Event coordinator contact
- Typical package needs or customization requirements
```

---

### Competitive Intelligence

**Why Useful:**
- Displacement opportunity
- Pricing benchmark
- Switching cost understanding

**What to Collect:**
```json
{
  "competitive_intel": {
    "current_suppliers": {
      "practice_balls": "Titleist",
      "range_equipment": "Toro",
      "irrigation": "Rain Bird"
    },
    "contract_timing": "Annual contract renews January",
    "pain_points_with_current": "Quality inconsistent, price increases"
  }
}
```

**LLM Prompt (Optional):**
```
If mentioned, capture competitive intelligence:
- Current ball suppliers
- Contract timing or renewal dates
- Complaints about current vendors
- Switching triggers or pain points
```

---

## Data Collection Hierarchy

### Minimum Viable Discovery

**Must Have (or disqualify):**
- ✅ 1+ water hazards OR practice range
- ✅ 1+ decision maker contact (email preferred)
- ✅ Course tier indicators (green fees or type)
- ✅ Location (state, city)

**If missing any:** Consider disqualifying or marking as "insufficient data"

---

### Standard Discovery

**Should Have (quality lead):**
- ✅ Water hazard count
- ✅ Range size
- ✅ 2+ decision maker contacts with emails
- ✅ Course tier classification
- ✅ Basic buying signals (1+)

**Leads with this data:** B-tier or better

---

### Comprehensive Discovery

**Ideal (A-tier lead):**
- ✅ Detailed water hazard intel (high-traffic holes)
- ✅ Range details + quality mentions
- ✅ 3+ decision makers with emails + LinkedIn
- ✅ Course tier + financials
- ✅ Multiple buying signals (2-3)
- ✅ Course intelligence (projects, vendors, awards)
- ✅ Event program details

**Leads with this data:** A-tier, immediate outreach

---

## LLM Prompt Enhancement Roadmap

### Current Prompt (v1)

Focuses on:
- Contact discovery (names, emails, LinkedIn)
- Basic course intel (ownership, projects)

**Gap:**
- Missing water hazard emphasis
- Missing range size data
- Missing buying signals
- Missing course tier indicators

---

### Enhanced Prompt (v2) - RECOMMENDED

Add sections:
1. **Water Hazard Deep Dive** (detailed questions)
2. **Practice Facilities Assessment** (range size, quality)
3. **Buying Signal Detection** (complaints, searches, budget timing)
4. **Course Positioning** (green fees, rounds, tier classification)
5. **Decision Maker Prioritization** (GM > Super > Dir of Golf)

**See:** `workflow-mapping.md` for full prompt template

---

## Data Quality Standards

### Email Verification

**Before Enrichment:**
- Format check (has @, valid TLD)
- Domain matches course website (preferred)

**After Enrichment:**
- Hunter.io verification (deliverable status)
- Confidence score ≥70%

**Reject:**
- Generic emails (info@, contact@)
- Personal emails (gmail.com, unless owner)
- Undeliverable (Hunter rejects)

---

### Source Attribution

**Always Require:**
- Source URL for each contact
- Source type (pga_directory, cmaa, vendor_site, newsletter)
- Verification date (2024-2025 recency)

**Why:**
- Credibility check (is source legitimate?)
- Recency validation (is info current?)
- Quality control (pattern analysis)

---

## Related Documents

- **Workflow Mapping:** `workflow-mapping.md` (data priorities → LLM prompts)
- **Qualification Criteria:** `../customer-segmentation/qualification-criteria.md`
- **Decision Hierarchy:** `../buyer-personas/decision-hierarchy.md`
- **Changelog:** `changelog.md` (track data requirement changes)
