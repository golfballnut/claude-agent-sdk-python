# Supabase Schema Design
**Date:** 2025-01-17
**Based On:** Real JSON outputs from 3 test courses
**Approach:** Flat schema (simple), can normalize later if needed

---

## 📊 Table Structure

### Table: `golf_courses`

**Course-Level Data (Agents 1, 2, 6, 7)**

```sql
CREATE TABLE golf_courses (
  -- Existing fields (your schema)
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_name VARCHAR(255) NOT NULL,
  state_code VARCHAR(2),
  website VARCHAR(500),
  phone VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),

  -- Agent 6: Business Intelligence (course-level - runs ONCE)
  segment VARCHAR(20),  -- 'high-end', 'budget', 'both', 'unknown'
  segment_confidence INT CHECK (segment_confidence BETWEEN 1 AND 10),
  segment_signals JSONB,  -- Array of classification signals
  range_intel JSONB,  -- {has_range, volume_signals, quality_complaints, ...}
  opportunity_scores JSONB,  -- {range_ball_buy: 8, range_ball_lease: 7, ...}
  agent6_enriched_at TIMESTAMP,

  -- Agent 7: Water Hazards (course-level - runs ONCE)
  water_hazard_count INT,
  water_hazard_confidence VARCHAR(20),  -- 'high', 'medium', 'low', 'none'
  water_hazard_details JSONB,  -- Array of details/sources
  agent7_enriched_at TIMESTAMP,

  -- Metadata
  enhancement_status VARCHAR(50),
  enrichment_completed_at TIMESTAMP
);
```

**Sample Data (Richmond Country Club):**
```json
{
  "course_name": "Richmond Country Club",
  "state_code": "VA",
  "website": "https://www.richmondcountryclubva.com/",
  "phone": "(804) 784-5663",

  "segment": "high-end",
  "segment_confidence": 9,
  "segment_signals": [
    "Private, member-owned club",
    "4.7-star rating",
    "Recent $$ renovation: range expanded 30%"
  ],

  "range_intel": {
    "has_range": true,
    "volume_signals": [
      "Grass range expanded 30% in 2022",
      "Capacity: 33-34 simultaneous users"
    ],
    "quality_complaints": [],
    "budget_signals": [],
    "sustainability_signals": []
  },

  "opportunity_scores": {
    "range_ball_buy": 8,
    "range_ball_sell": 2,
    "range_ball_lease": 7,
    "proshop_ecommerce": 5,
    "superintendent_partnership": 6,
    "ball_retrieval": 6
  },

  "water_hazard_count": 7,
  "water_hazard_confidence": "low"
}
```

---

### Table: `golf_course_contacts`

**Contact-Level Data (Agents 3, 5, 6.5)**

```sql
CREATE TABLE golf_course_contacts (
  -- Existing fields (your schema)
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  golf_course_id UUID REFERENCES golf_courses(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  title VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),

  -- Agent 3: Email + LinkedIn Enrichment
  email VARCHAR(255),
  email_confidence INT CHECK (email_confidence BETWEEN 0 AND 100),
  email_method VARCHAR(50),  -- 'hunter_io', 'web_search', 'focused_search', 'not_found'
  linkedin_url VARCHAR(500),
  linkedin_method VARCHAR(50),  -- 'hunter_io', 'web_search', 'not_found'
  agent3_enriched_at TIMESTAMP,

  -- Agent 5: Phone Enrichment
  phone VARCHAR(50),
  phone_method VARCHAR(50),  -- 'perplexity_ai', 'not_found'
  phone_confidence INT CHECK (phone_confidence BETWEEN 0 AND 100),
  phone_source VARCHAR(100),  -- 'aggregated' (Perplexity searches multiple sources)
  agent5_enriched_at TIMESTAMP,

  -- Agent 6.5: Contact Background
  tenure_years INT,
  tenure_confidence VARCHAR(20),  -- 'high', 'medium', 'low', 'unknown'
  previous_clubs JSONB,  -- Array of previous club names
  industry_experience_years INT,
  responsibilities JSONB,  -- Array of role responsibilities
  career_notes TEXT,  -- Career progression summary
  agent65_enriched_at TIMESTAMP,

  -- Metadata
  enrichment_status VARCHAR(50),
  enrichment_completed_at TIMESTAMP
);
```

**Sample Data (Stacy Foster):**
```json
{
  "golf_course_id": "uuid-of-richmond-cc",
  "name": "Stacy Foster",
  "title": "General Manager",

  "email": "sfoster@richmondcountryclubva.com",
  "email_confidence": 98,
  "email_method": "hunter_io",
  "linkedin_url": "https://www.linkedin.com/in/stacy-foster-20b79448",
  "linkedin_method": "hunter_io",

  "phone": "804-592-5861",
  "phone_method": "perplexity_ai",
  "phone_confidence": 90,
  "phone_source": "aggregated",

  "tenure_years": null,
  "tenure_confidence": "unknown",
  "previous_clubs": [],
  "industry_experience_years": null,
  "responsibilities": [
    "oversight of course operations",
    "staff management",
    "financial management",
    "member services"
  ],
  "career_notes": "General Manager at Richmond Country Club..."
}
```

---

## 📋 Field Mappings (JSON → SQL)

### Agent 6 (Course-Level)
| JSON Path | SQL Column | Type | Example |
|-----------|------------|------|---------|
| `agent6.segmentation.primary_target` | `segment` | VARCHAR(20) | 'high-end' |
| `agent6.segmentation.confidence` | `segment_confidence` | INT | 9 |
| `agent6.segmentation.signals` | `segment_signals` | JSONB | ["Private club", ...] |
| `agent6.range_intel` | `range_intel` | JSONB | {has_range: true, ...} |
| `agent6.opportunities` | `opportunity_scores` | JSONB | {range_ball_buy: 8, ...} |

### Agent 7 (Course-Level)
| JSON Path | SQL Column | Type | Example |
|-----------|------------|------|---------|
| `agent7.water_hazard_count` | `water_hazard_count` | INT | 7 |
| `agent7.confidence` | `water_hazard_confidence` | VARCHAR(20) | 'low' |
| `agent7.details` | `water_hazard_details` | JSONB | ["scorecard analysis..."] |

### Agent 3 (Contact-Level)
| JSON Path | SQL Column | Type | Example |
|-----------|------------|------|---------|
| `contacts[].agent3.email` | `email` | VARCHAR(255) | 'sfoster@...' |
| `contacts[].agent3.email_confidence` | `email_confidence` | INT | 98 |
| `contacts[].agent3.email_method` | `email_method` | VARCHAR(50) | 'hunter_io' |
| `contacts[].agent3.linkedin_url` | `linkedin_url` | VARCHAR(500) | 'https://...' |
| `contacts[].agent3.linkedin_method` | `linkedin_method` | VARCHAR(50) | 'hunter_io' |

### Agent 5 (Contact-Level)
| JSON Path | SQL Column | Type | Example |
|-----------|------------|------|---------|
| `contacts[].agent5.phone` | `phone` | VARCHAR(50) | '804-592-5861' |
| `contacts[].agent5.method` | `phone_method` | VARCHAR(50) | 'perplexity_ai' |
| `contacts[].agent5.confidence` | `phone_confidence` | INT | 90 |
| `contacts[].agent5.phone_source` | `phone_source` | VARCHAR(100) | 'aggregated' |

### Agent 6.5 (Contact-Level)
| JSON Path | SQL Column | Type | Example |
|-----------|------------|------|---------|
| `contacts[].agent65.tenure_years` | `tenure_years` | INT | null |
| `contacts[].agent65.tenure_confidence` | `tenure_confidence` | VARCHAR(20) | 'unknown' |
| `contacts[].agent65.previous_clubs` | `previous_clubs` | JSONB | ["Brickshire GC", ...] |
| `contacts[].agent65.industry_experience_years` | `industry_experience_years` | INT | null |
| `contacts[].agent65.responsibilities` | `responsibilities` | JSONB | ["golf instruction", ...] |
| `contacts[].agent65.career_notes` | `career_notes` | TEXT | 'PGA professional...' |

---

## 🔍 Data Type Decisions

### Why JSONB for Arrays?
**Fields:** segment_signals, range_intel, opportunity_scores, previous_clubs, responsibilities

**Pros:**
- Flexible (can add fields without migration)
- Queryable (can filter/index JSON keys)
- Matches JSON output structure exactly

**Cons:**
- Slightly harder to query than normalized tables

**Decision:** Use JSONB for now, can normalize later if query patterns demand it

### Why VARCHAR for Confidence Levels?
**Fields:** water_hazard_confidence, tenure_confidence

**Options:**
- ENUM (strict: 'high', 'medium', 'low')
- VARCHAR (flexible: can add 'very_high' later)

**Decision:** VARCHAR for flexibility (agents may return different confidence labels)

### Why TEXT for Career Notes?
**Field:** career_notes

**Reason:** Can be long (100-500 chars), variable length

---

## 🎯 Migration Strategy

### Option A: Run Both Migrations
```bash
# 1. Run original migration (Agent 6/7 course-level fields)
psql < migrations/001_add_agent_enrichment_fields.sql

# 2. Run refactor migration (Agent 3/5/6.5 enhancements)
psql < migrations/002_agent_refactor_update.sql
```

### Option B: Merge into Single Migration
- Combine 001 + 002
- Single atomic migration
- Cleaner history

**Recommendation:** Option A (keep history of design evolution)

---

## 📝 Nullable Fields Analysis

**Always Nullable (Expected):**
- `email`, `email_confidence`, `email_method` (50% success rate)
- `linkedin_url`, `linkedin_method` (25% success rate)
- `phone`, `phone_confidence`, `phone_method` (78% success rate)
- `tenure_years`, `industry_experience_years` (11% success rate)
- `previous_clubs` (22% find data, but always return [])

**Usually Populated:**
- `responsibilities` (100% - always finds some duties)
- `career_notes` (100% - even if "No data found")
- `segment`, `segment_confidence` (100%)
- `opportunity_scores` (100%)
- `water_hazard_count` (100% found so far!)

**Never Null:**
- `course_name`, `name`, `title` (Agent 2 always finds these)

---

## 🚀 Next Steps

1. **Review this schema** with stakeholder (you!)
2. **Apply migrations:**
   - 001 (if not already applied)
   - 002 (new fields)
3. **Update Agent 8** to write to Supabase using this schema
4. **Test on 1 course** to validate

---

**Schema is designed. Ready to integrate!**

---

**Last Updated:** 2025-01-17
**Status:** Complete - Ready for implementation
