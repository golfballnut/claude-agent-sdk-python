# Data Collection Priorities

**Purpose:** Define WHAT data to collect and WHY it matters for Links Choice
**Audience:** LLM prompt engineers, enrichment workflow builders

---

## Priority 1: Critical Data (Deal Breakers)

### Range Ball Opportunity Classification ⭐ **HIGHEST PRIORITY**

**Why Critical:**
- BUY and SELL opportunities require completely different outreach
- BOTH opportunities = highest value (full circle relationship)
- Wrong classification = wrong message = lost opportunity
- Determines entry strategy and campaign routing

**What to Classify:**
- **BUY OPPORTUNITY:** They have waste balls to sell us
- **SELL OPPORTUNITY:** They need to purchase balls from us
- **BOTH:** Full circle opportunity (waste + need = maximum value)
- **UNKNOWN:** Insufficient data to classify

**Buy Signals (They have waste to sell us):**
```json
{
  "buy_signals": [
    "Throwing away old/worn range balls",
    "Storage full of old balls",
    "Just renovated range (old inventory to clear)",
    "Disposing of practice balls",
    "Worn out ball inventory",
    "Getting rid of balls",
    "No market for our used balls"
  ],
  "buy_characteristics": {
    "large_range": "50+ stations (high volume waste)",
    "premium_club": "Tier 1-2 (quality waste materials)",
    "established": "10+ years (accumulation)",
    "recent_renovation": "Old inventory exists"
  }
}
```

**Sell Signals (They need to purchase from us):**
```json
{
  "sell_signals": [
    "Practice ball budget too high",
    "Looking for ball supplier",
    "Range balls in poor condition",
    "Members complaining about ball quality",
    "Current supplier too expensive",
    "Need to buy/order range balls",
    "Budget constraints on range operations"
  ],
  "sell_characteristics": {
    "budget_pain": "Cost complaints, seeking savings",
    "quality_pain": "Member complaints, quality issues",
    "switching_trigger": "Vendor change, price increase",
    "new_operation": "Range expansion, new course"
  }
}
```

**BOTH Signals (Full Circle - HIGHEST VALUE):**
```json
{
  "both_indicators": [
    "BUY: Disposal mentions + SELL: Budget/quality pain",
    "Large range + Quality complaints + Discarding old balls",
    "'Just renovated' + 'Need new supplier'",
    "Premium club + Budget pressure + Waste inventory"
  ]
}
```

**LLM Prompt Addition:**
```
CRITICAL: Classify this course as BUY, SELL, or BOTH opportunity.

BUY OPPORTUNITY (They have balls we can purchase):
Look for: "Throwing away", "disposing of", "storage full", "old balls", "worn out inventory"
Estimate: Waste volume (based on range size) and quality level (based on course tier)

SELL OPPORTUNITY (They need to purchase from us):
Look for: "Budget too high", "looking for supplier", "poor quality", "member complaints", "need to buy"
Identify: Pain type (budget vs quality), current supplier, switching triggers

BOTH (HIGHEST PRIORITY - Full Circle):
Course shows BOTH waste disposal needs AND active purchasing needs
Example: Large range + quality complaints + mentions discarding balls

Classify as: BUY_OPPORTUNITY | SELL_OPPORTUNITY | BOTH_OPPORTUNITY | INSUFFICIENT_DATA
```

**Data to Collect:**
```json
{
  "range_ball_classification": {
    "opportunity_type": "buy" | "sell" | "both" | "unknown",

    "buy_opportunity": {
      "has_waste_balls": true,
      "disposal_mentions": ["throwing away old balls"],
      "volume_estimate": "high" | "medium" | "low",
      "quality_estimate": "premium" | "standard" | "practice",
      "buy_signals": ["..."]
    },

    "sell_opportunity": {
      "needs_supplier": true,
      "pain_type": "budget" | "quality" | "both",
      "current_supplier": "Titleist",
      "switching_triggers": ["price increase"],
      "sell_signals": ["..."]
    },

    "recommended_entry_strategy": "buy_first" | "sell_first" | "buy_then_sell"
  }
}
```

**Scoring Impact:**
- BOTH opportunity: 20 points (highest value, full circle potential)
- High-pain SELL: 15 points (fast close, ready to buy)
- Premium BUY: 12 points (easy entry, quality materials, upsell potential)
- Standard SELL: 10 points (moderate opportunity)
- BUY only (budget club): 7 points (lower priority)
- UNKNOWN: Requires discovery before scoring

---

### Practice Range Size

**Why Critical:**
- Range ball sales = primary revenue stream (SELL opportunities)
- Range ball purchase = primary entry point (BUY opportunities)
- Determines opportunity volume (stations × balls)
- Differentiates high-value vs low-value courses

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
- 50+ stations: 10 points (subscription fit, high volume BUY/SELL)
- 30-49 stations: 7 points (sales opportunity)
- 15-29 stations: 4 points (small opportunity)
- No range: 0 points (pro shop only, different offering)

---

### Water Hazards (EXPANSION SERVICE - Not Primary Entry)

**Why Important (But Not Entry Point):**
- Retrieval service = expansion opportunity after relationship established
- Raw materials for processing
- Quantifies future expansion opportunity size
- Differentiates potential for full service relationship

**Strategic Note:**
⚠️ Water hazard retrieval should NOT be used as primary entry point due to:
- High competition ("many companies calling daily")
- Low perceived value ("not much money for big clubs")
- Slow sales cycle (4-8 weeks, complex approval)
- Better used as expansion service after trust established via range balls

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
Find the number of ponds, lakes, or water hazards on the course.
Specifically identify:
- Total count of water hazards
- Which holes have island greens or lakeside hazards
- Any mentions of ball accumulation or retrieval needs
```

**Scoring Impact (for expansion potential, not entry):**
- 7+ hazards: 10 points (excellent expansion opportunity)
- 4-6 hazards: 7 points (good expansion potential)
- 1-3 hazards: 3 points (limited expansion)
- 0 hazards: 0 points (no retrieval opportunity)

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
