# Field Validation Reference

Complete reference for all fields that must be validated after enrichment.

---

## 🏌️ golf_courses Table - Required Fields

### Core Identity Fields

| Field | Type | Required | Validation | Notes |
|-------|------|----------|------------|-------|
| id | integer | ✅ Yes | Auto-generated or provided | Primary key |
| course_name | varchar | ✅ Yes | Non-empty string | From Agent 2 |
| state_code | varchar | ✅ Yes | 2-letter state code | From API request |

### Contact Information

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| website | text | ⚠️ Recommended | Valid URL | Agent 2 |
| phone | varchar | ⚠️ Recommended | Phone format | Agent 2 |

### Business Intelligence (Agent 6)

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| segment | text | ✅ Critical | 'high-end' OR 'budget' OR 'both' | Agent 6 |
| segment_confidence | integer | ✅ Critical | 1-10 | Agent 6 |
| segment_signals | jsonb | ✅ Critical | JSON array of strings | Agent 6 |
| range_intel | jsonb | ⚠️ Recommended | JSON object | Agent 6 |
| opportunities | jsonb | ✅ Critical | JSON with opportunity scores | Agent 6 |

### Water Hazards (Agent 7)

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| water_hazards | integer | ✅ Critical | Integer or null | Agent 7 |
| water_hazard_confidence | text | ⚠️ Recommended | 'high', 'medium', 'low', 'none' | Agent 7 |

### Status & Tracking

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| enhancement_status | varchar | ✅ Critical | 'complete', 'pending', etc | Agent 8 |
| enrichment_completed_at | timestamp | ✅ Critical | Recent timestamp | Agent 8 |
| **agent_cost_usd** | **numeric** | **✅ CRITICAL** | **> 0, typically 0.10-0.20** | **Orchestrator → Agent 8** |

### Contacts Page (Future Employment Verification)

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| **contacts_page_url** | **text** | **✅ CRITICAL** | **Valid URL or null** | **Agent 2 → Agent 8** |
| **contacts_page_search_method** | text | ⚠️ Recommended | 'agent2_extraction' or null | Agent 8 |
| **contacts_page_found_at** | timestamptz | ⚠️ If URL found | Timestamp or null | Agent 8 |

---

## 👥 golf_course_contacts Table - Required Fields

### Core Identity

| Field | Type | Required | Validation | Notes |
|-------|------|----------|------------|-------|
| contact_id | uuid | ✅ Yes | Auto-generated UUID | Primary key |
| golf_course_id | integer | ✅ Yes | FK to golf_courses.id | Must match test course |
| contact_name | varchar | ✅ Yes | Non-empty string | From Agent 2 |
| **contact_source** | **varchar** | **✅ CRITICAL** | **'website_scrape'** | **Constraint violation if missing** |

### Contact Details

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| contact_title | varchar | ⚠️ Recommended | Job title | Agent 2 |
| contact_email | varchar | ✅ Critical | Valid email format | Agent 3 |
| contact_phone | varchar | ✅ Critical | Phone format | Agent 5 |

### Email Enrichment (Agent 3)

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| email_confidence_score | integer | ⚠️ If email found | 0-100 | Agent 3 |
| email_discovery_method | varchar | ⚠️ If email found | 'hunter_io', etc | Agent 3 |

### Phone Enrichment (Agent 5)

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| phone_confidence | integer | ⚠️ If phone found | 0-100 | Agent 5 |
| phone_source | varchar | ⚠️ If phone found | 'perplexity_ai', etc | Agent 5 |

### LinkedIn & Background (Agents 3 & 6.5)

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| linkedin_url | text | Optional | Valid URL or null | Agent 3 |
| tenure_years | integer | Optional | Integer or null | Agent 6.5 |
| previous_clubs | jsonb | Optional | JSON array | Agent 6.5 |

**Note:** These fields often null (agents may not find data) - acceptable

---

## 🚨 Critical Field Validation

### Must Never Be Null (BLOCKERS):

1. **golf_courses.agent_cost_usd**
   - Why: Cost tracking for budget monitoring
   - If null: Fix orchestrator → Agent 8 cost passing

2. **golf_courses.contacts_page_url**
   - Why: Future employment verification agent needs this
   - If empty: Fix Agent 2 extraction → Agent 8 writing

3. **golf_course_contacts.contact_source**
   - Why: Database constraint - insert will FAIL
   - If missing: Agent 8 must set to 'website_scrape'

4. **golf_courses.enhancement_status**
   - Why: Tracking field - prevents re-enrichment
   - Must be: 'complete' after successful enrichment

5. **golf_courses.enrichment_completed_at**
   - Why: Timestamp tracking
   - Must be: Recent timestamp

---

## ⚠️ Should Investigate if Null:

1. **segment** - Agent 6 should classify every course
2. **water_hazards** - Agent 7 should find count (may be 0)
3. **contact_email** - Agent 3 should find for most contacts
4. **contact_phone** - Agent 5 should find for most contacts
5. **email_confidence_score** - Should exist if email found
6. **phone_confidence** - Should exist if phone found

---

## ✅ Validation SQL Template

```sql
-- Quick validation query
SELECT
  id,
  course_name,
  CASE WHEN agent_cost_usd IS NULL THEN '❌ NULL' ELSE '✅ ' || agent_cost_usd::text END as agent_cost,
  CASE WHEN contacts_page_url = '' THEN '❌ EMPTY' WHEN contacts_page_url IS NULL THEN '❌ NULL' ELSE '✅ Present' END as contacts_page,
  CASE WHEN segment IS NULL THEN '❌ NULL' ELSE '✅ ' || segment END as segment_check,
  CASE WHEN water_hazards IS NULL THEN '⚠️  NULL' ELSE '✅ ' || water_hazards::text END as water_check,
  enhancement_status
FROM golf_courses
WHERE id = [TEST_COURSE_ID];
```

**Expected Output:**
```
agent_cost: ✅ 0.1119
contacts_page: ✅ Present
segment_check: ✅ budget
water_check: ✅ 8
enhancement_status: complete
```

**If ANY ❌ appears → FIX REQUIRED**

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
