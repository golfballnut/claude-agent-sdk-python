# Audit Queries for Golf Enrichment Testing

Pre-configured Supabase SQL queries for validating enrichment results.

**Use with:** `mcp__supabase__execute_sql` tool
**Project ID:** oadmysogtfopkbmrulmq

---

## 🔍 Pre-Test Queries

### Query 1: Find Test Course Candidates

```sql
SELECT
  id,
  course_name,
  state_code,
  enhancement_status,
  enrichment_completed_at,
  (SELECT COUNT(*) FROM golf_course_contacts WHERE golf_course_id = golf_courses.id) as existing_contacts
FROM golf_courses
WHERE
  enhancement_status = 'pending'
  AND state_code = 'VA'
ORDER BY id
LIMIT 10;
```

**Purpose:** Find courses ready for testing
**Look For:** Courses with status 'pending' and 0 contacts

---

### Query 2: Check Specific Course Details

```sql
SELECT
  id,
  course_name,
  state_code,
  enhancement_status,
  enrichment_completed_at,
  segment,
  water_hazards
FROM golf_courses
WHERE id IN (93, 98, 103, 108);
```

**Purpose:** Get current state before testing
**Document:** Status and existing enrichment data

---

## ✅ Post-Test Validation Queries

### Query 3: Full Course Record Audit

```sql
SELECT
  id,
  course_name,
  state_code,
  website,
  phone,
  -- Business Intelligence
  segment,
  segment_confidence,
  segment_signals,
  range_intel,
  opportunities,
  -- Water Hazards
  water_hazards,
  water_hazard_confidence,
  -- Status
  enhancement_status,
  enrichment_completed_at,
  -- CRITICAL FIELDS
  agent_cost_usd,
  contacts_page_url,
  contacts_page_search_method,
  contacts_page_found_at,
  -- Timestamps
  created_at
FROM golf_courses
WHERE id = [TEST_COURSE_ID];
```

**Purpose:** Validate ALL course fields after enrichment
**Critical Checks:**
- ✅ `agent_cost_usd` is NOT NULL
- ✅ `contacts_page_url` is NOT empty string
- ✅ `enhancement_status` = 'complete'
- ✅ `enrichment_completed_at` = recent timestamp
- ✅ `segment` is NOT NULL
- ✅ `segment_confidence` between 1-10

---

### Query 4: Contact Records Validation

```sql
SELECT
  contact_id,
  golf_course_id,
  contact_name,
  contact_title,
  contact_email,
  contact_phone,
  -- CRITICAL
  contact_source,
  -- Email enrichment
  email_confidence_score,
  email_discovery_method,
  -- Phone enrichment
  phone_confidence,
  phone_source,
  -- LinkedIn & Background
  linkedin_url,
  tenure_years,
  previous_clubs,
  -- Timestamps
  created_at
FROM golf_course_contacts
WHERE golf_course_id = [TEST_COURSE_ID]
ORDER BY contact_name;
```

**Purpose:** Validate all contact records
**Critical Checks:**
- ✅ `golf_course_id` = [TEST_COURSE_ID]
- ✅ `contact_source` = 'website_scrape' (REQUIRED - constraint)
- ✅ At least 1 contact has `contact_email`
- ✅ At least 1 contact has `contact_phone`
- ✅ `email_confidence_score` present if email found
- ✅ `phone_confidence` present if phone found

---

### Query 5: Quick Validation (Pass/Fail)

```sql
SELECT
  id,
  course_name,
  -- Critical fields with pass/fail indicators
  CASE
    WHEN agent_cost_usd IS NULL THEN '❌ FAIL: agent_cost_usd NULL'
    WHEN agent_cost_usd = 0 THEN '⚠️  WARN: agent_cost_usd ZERO'
    ELSE '✅ PASS: $' || agent_cost_usd::text
  END as cost_check,
  CASE
    WHEN contacts_page_url IS NULL THEN '❌ FAIL: contacts_page_url NULL'
    WHEN contacts_page_url = '' THEN '❌ FAIL: contacts_page_url EMPTY'
    ELSE '✅ PASS: URL present'
  END as contacts_page_check,
  CASE
    WHEN segment IS NULL THEN '❌ FAIL: segment NULL'
    WHEN segment NOT IN ('high-end', 'budget', 'both') THEN '❌ FAIL: Invalid segment'
    ELSE '✅ PASS: ' || segment
  END as segment_check,
  CASE
    WHEN enhancement_status != 'complete' THEN '❌ FAIL: Not complete'
    ELSE '✅ PASS: complete'
  END as status_check,
  CASE
    WHEN enrichment_completed_at IS NULL THEN '❌ FAIL: No timestamp'
    ELSE '✅ PASS: ' || enrichment_completed_at::text
  END as timestamp_check,
  (SELECT COUNT(*) FROM golf_course_contacts WHERE golf_course_id = golf_courses.id) as contact_count
FROM golf_courses
WHERE id = [TEST_COURSE_ID];
```

**Purpose:** One-query validation with visual pass/fail
**Expected:** All ✅ PASS
**If ANY ❌ FAIL:** Stop and fix before continuing

---

## 🔎 Diagnostic Queries

### Query 6: Check for Duplicate Courses

```sql
SELECT
  id,
  course_name,
  enhancement_status,
  enrichment_completed_at
FROM golf_courses
WHERE course_name ILIKE '%[COURSE_NAME_FRAGMENT]%'
ORDER BY created_at DESC;
```

**Purpose:** Detect if duplicate courses created
**Expected:** Only 1 row per unique course
**If Multiple:** course_id parameter not used correctly

---

### Query 7: Compare Agent 2 Name vs Database Name

```sql
-- Run AFTER enrichment to check name mismatch
SELECT
  id as db_id,
  course_name as db_name,
  '[AGENT2_EXTRACTED_NAME]' as agent2_name,
  CASE
    WHEN course_name = '[AGENT2_EXTRACTED_NAME]' THEN '✅ MATCH'
    ELSE '⚠️  MISMATCH - course_id parameter critical!'
  END as name_comparison
FROM golf_courses
WHERE id = [TEST_COURSE_ID];
```

**Purpose:** Identify name mismatch issues
**Example:**
- Database: "Brambleton Regional Park Golf Course"
- Agent 2: "Brambleton Golf Course"
- Result: ⚠️ MISMATCH

**Why This Matters:** Without course_id parameter, wrong course gets updated

---

### Query 8: Contact Source Validation

```sql
SELECT
  golf_course_id,
  contact_name,
  contact_source,
  CASE
    WHEN contact_source IS NULL THEN '❌ FAIL: NULL (constraint violation)'
    WHEN contact_source NOT IN ('website_scrape', 'linkedin_search', 'dual_verified', 'email_generated', 'manual')
      THEN '❌ FAIL: Invalid value'
    ELSE '✅ PASS'
  END as validation
FROM golf_course_contacts
WHERE golf_course_id = [TEST_COURSE_ID];
```

**Purpose:** Verify contact_source field (database constraint)
**Expected:** All ✅ PASS with 'website_scrape'
**If FAIL:** Database will reject insert

---

## 📊 Aggregate Metrics Queries

### Query 9: Multi-Course Testing Summary

```sql
SELECT
  id,
  course_name,
  enhancement_status,
  agent_cost_usd,
  CASE WHEN contacts_page_url IS NOT NULL AND contacts_page_url != '' THEN '✅' ELSE '❌' END as has_contacts_page,
  (SELECT COUNT(*) FROM golf_course_contacts WHERE golf_course_id = golf_courses.id) as contact_count,
  enrichment_completed_at
FROM golf_courses
WHERE id IN (93, 98, 103, 108)
ORDER BY id;
```

**Purpose:** Compare results across multiple test courses
**Look For:** Consistency in fields populated

---

### Query 10: Cost Analysis

```sql
SELECT
  id,
  course_name,
  agent_cost_usd,
  (SELECT COUNT(*) FROM golf_course_contacts WHERE golf_course_id = golf_courses.id) as contacts,
  ROUND(agent_cost_usd / NULLIF((SELECT COUNT(*) FROM golf_course_contacts WHERE golf_course_id = golf_courses.id), 0), 4) as cost_per_contact
FROM golf_courses
WHERE id IN ([TEST_COURSE_IDS])
AND agent_cost_usd IS NOT NULL
ORDER BY id;
```

**Purpose:** Analyze cost efficiency
**Thresholds:**
- Average cost < $0.15 per course
- Cost per contact < $0.08

---

## 🚨 Error Detection Queries

### Query 11: Find Null Critical Fields

```sql
SELECT
  id,
  course_name,
  CASE WHEN agent_cost_usd IS NULL THEN 'agent_cost_usd' END as null_cost,
  CASE WHEN contacts_page_url IS NULL OR contacts_page_url = '' THEN 'contacts_page_url' END as null_page,
  CASE WHEN segment IS NULL THEN 'segment' END as null_segment,
  CASE WHEN enhancement_status IS NULL THEN 'enhancement_status' END as null_status
FROM golf_courses
WHERE id IN ([TEST_COURSE_IDS])
AND (
  agent_cost_usd IS NULL
  OR contacts_page_url IS NULL
  OR contacts_page_url = ''
  OR segment IS NULL
  OR enhancement_status IS NULL
);
```

**Purpose:** Find courses with missing critical fields
**Expected:** No rows returned
**If Rows:** Fix agents before deploying

---

### Query 12: Check Contacts Missing Required Fields

```sql
SELECT
  contact_id,
  golf_course_id,
  contact_name,
  CASE WHEN contact_source IS NULL THEN '❌ contact_source NULL' END as source_issue,
  CASE WHEN contact_email IS NULL AND contact_phone IS NULL THEN '⚠️  No email or phone' END as contact_info_issue
FROM golf_course_contacts
WHERE golf_course_id IN ([TEST_COURSE_IDS])
AND (
  contact_source IS NULL
  OR (contact_email IS NULL AND contact_phone IS NULL)
);
```

**Purpose:** Find contacts with data quality issues
**Expected:** No rows (all contacts have source and at least email or phone)

---

## 🔄 Comparison Queries

### Query 13: Before vs After Enrichment

**Run BEFORE Test:**
```sql
SELECT
  id,
  course_name,
  enhancement_status as status_before,
  segment as segment_before,
  water_hazards as water_before,
  (SELECT COUNT(*) FROM golf_course_contacts WHERE golf_course_id = golf_courses.id) as contacts_before
FROM golf_courses
WHERE id = [TEST_COURSE_ID];
```

**Run AFTER Test:**
```sql
SELECT
  id,
  course_name,
  enhancement_status as status_after,
  segment as segment_after,
  water_hazards as water_after,
  (SELECT COUNT(*) FROM golf_course_contacts WHERE golf_course_id = golf_courses.id) as contacts_after
FROM golf_courses
WHERE id = [TEST_COURSE_ID];
```

**Compare:** All fields should change from null → populated

---

## 📋 Usage Instructions

### How to Use These Queries:

**1. Copy query from this file**

**2. Use Supabase MCP tool:**
```
mcp__supabase__execute_sql
project_id: oadmysogtfopkbmrulmq
query: [paste query, replace [TEST_COURSE_ID] with actual ID]
```

**3. Analyze results:**
- Check for ✅ PASS indicators
- Investigate any ❌ FAIL
- Document findings

**4. Iterate:**
- If failures found → fix code
- Rebuild Docker
- Retest
- Re-audit

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Related:** SKILL.md, FIELD_VALIDATION.md, TROUBLESHOOTING.md
