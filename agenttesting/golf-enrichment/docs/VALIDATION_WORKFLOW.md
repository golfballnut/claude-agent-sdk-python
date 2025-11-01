# V2 Validation Workflow - Manual Testing Guide

**Purpose:** Step-by-step guide for testing 5 NC courses through the V2 validation pipeline

**Goal:** Paste LLM JSON → Validate → Write to Test Tables → Verify → Switch to Production → ClickUp Tasks

---

## Pre-populated Courses (Ready for JSON)

| # | Staging ID | Course ID | Course Name | City |
|---|-----------|-----------|-------------|------|
| 1 | `76dbe9aa-53d0-46f0-b21d-d4b336e9dc08` | 1448 | The Tradition Golf Club | Charlotte |
| 2 | `48acb6b0-96fc-4342-93c4-21f2af00a643` | 1384 | Capital Golf Center | Wake Forest |
| 3 | `7887ceff-170a-45e4-8600-faa87956cef5` | 1376 | Keith Hills Golf Club | Buies Creek |
| 4 | `c2b94886-1230-44dd-938f-6b719ef3b0f0` | 1331 | Vineyard Golf At White Lake | Elizabethtown |
| 5 | `e3c023aa-b9f0-42b5-87e8-06abad78abac` | 1498 | Sound of Freedom Golf Course | Cherry Point |
| 6 | `8cd4cf7e-aeb0-44ed-97e9-849f70e97a21` | 1432 | Forest Creek Golf Club | Pinehurst |
| 7 | `2ad56643-289a-4667-af4d-41ecd7fec649` | 1346 | Warrenton Golf Club | Warrenton |
| 8 | `bf5ffed5-df98-44c2-8587-d59b29420cc8` | 1192 | Hemlock Golf Course | Walnut Cove |
| 9 | `4cfe1a1b-4230-4dbf-b407-7aabfa80b755` | 1396 | Asheboro Country Club | Asheboro |
| 10 | `a5d83846-fe61-4493-97bc-cd7176deea7f` | 1097 | Dan Valley Golf Course | Stoneville |

---

## Workflow for Each Course

### STEP 1: Run LLM Research (You)

1. Use your V2 research prompt with the course name and state
2. Copy the complete JSON output

### STEP 2: Paste JSON into Staging Table (You)

Replace `{STAGING_ID}` and `{YOUR_JSON}` below:

```sql
UPDATE llm_research_staging
SET v2_json = '{YOUR_JSON}'::jsonb
WHERE id = '{STAGING_ID}';
```

**Example for Course #1 (The Tradition Golf Club):**
```sql
UPDATE llm_research_staging
SET v2_json = '{
  "section1": {"tier": "Premium", "tier_confidence": 0.85, ...},
  "section2": {"has_water_hazards": true, ...},
  "section3": {"annual_rounds_estimate": 25000, ...},
  "section4": {"contacts": [...]},
  "section5": {"ownership": "Private", ...}
}'::jsonb
WHERE id = '76dbe9aa-53d0-46f0-b21d-d4b336e9dc08';
```

### STEP 3: Tell Claude to Validate (You → Claude)

**Simply say:** "Validate course #1" (or whichever course number)

Claude will:
1. Fetch the staging record
2. Call Render validator endpoint
3. Show validation results
4. Verify database writes

### STEP 4: Review Results (Claude)

Claude will show you:
- ✅ Success/failure status
- ✅ Course ID created
- ✅ Number of contacts created
- ✅ Any validation flags
- ✅ Database verification queries

---

## V2 JSON Structure Requirements

**CRITICAL:** Your JSON must use these exact keys:

```json
{
  "section1": {
    "tier": "Premium|Mid|Budget",
    "tier_confidence": 0.0-1.0,  // NUMERIC not string!
    "tier_reasoning": "...",
    "tier_citations": ["url1", "url2"]
  },
  "section2": {
    "has_water_hazards": true/false,
    "hazards_count": 12,  // numeric
    "hazards_description": "...",
    "expansion_opportunity": "high|medium|low",
    "hazards_citations": ["url"]
  },
  "section3": {
    "annual_rounds_estimate": 30000,  // numeric
    "range_ball_usage_estimate": 250000,  // numeric
    "volume_confidence": "high|medium|low",
    "volume_reasoning": "...",
    "volume_citations": ["url"]
  },
  "section4": {
    "contacts": [
      {
        "name": "Full Name",
        "title": "Job Title",
        "email": "email@example.com",
        "phone": "555-123-4567",
        "confidence": "high|medium|low",
        "source_url": "url"
      }
    ]
  },
  "section5": {
    "ownership": "Private|Public|Municipal|Resort",
    "management_company": "Company Name or Self-Managed",
    "course_architect": "Architect Name",
    "intelligence_citations": ["url"]
  }
}
```

**Common Mistakes to Avoid:**
- ❌ `"tier_confidence": "high"` → ✅ `"tier_confidence": 0.9`
- ❌ `"section1_tier_classification"` → ✅ `"section1"`
- ❌ Missing any of the 5 sections → Will fail validation

---

## Validation Results Tracking

| Course # | Name | Status | Course ID | Contacts | Flags | Notes |
|----------|------|--------|-----------|----------|-------|-------|
| 1 | The Tradition Golf Club | ⏳ Pending | - | - | - | - |
| 2 | Capital Golf Center | ⏳ Pending | - | - | - | - |
| 3 | Keith Hills Golf Club | ⏳ Pending | - | - | - | - |
| 4 | Vineyard Golf At White Lake | ⏳ Pending | - | - | - | - |
| 5 | Sound of Freedom Golf Course | ⏳ Pending | - | - | - | - |

**Success Criteria for Production Switch:**
- ✅ 5/5 courses return `success: true`
- ✅ All courses have course_id in response
- ✅ All courses have at least 1 contact created
- ✅ No critical validation errors
- ✅ Test table data verified for all 5

---

## After 5 Successful Validations

Claude will:
1. Update Render environment: `USE_TEST_TABLES=false`
2. Re-test with 1 course using production tables
3. Verify ClickUp task creation (automatic via trigger)
4. Document complete workflow in PROGRESS.md

---

## Quick Commands

**View staging records:**
```sql
SELECT id, course_id, course_name, status,
       CASE WHEN v2_json = '{}'::jsonb THEN 'Empty' ELSE 'Has JSON' END as json_status
FROM llm_research_staging
WHERE state_code = 'NC'
ORDER BY course_name;
```

**Check course #1 result:**
```sql
SELECT * FROM golf_courses_test WHERE id = 2056;  -- Adjust ID based on response
SELECT * FROM golf_course_contacts_test WHERE golf_course_id = 2056;
```

**Reset a staging record (if needed):**
```sql
UPDATE llm_research_staging
SET v2_json = '{}'::jsonb, status = 'pending', validation_error = NULL
WHERE id = '{STAGING_ID}';
```

---

**Ready to start!** Begin with course #1 when you have the LLM JSON ready.
