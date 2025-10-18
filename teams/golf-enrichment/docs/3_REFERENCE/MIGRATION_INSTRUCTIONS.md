# Supabase Migration Instructions
**Apply these migrations before running the orchestrator with Supabase integration**

---

## 🎯 Goal
Add Agent 6, 6.5, and 7 enrichment fields to your Supabase database.

---

## 📋 Step-by-Step Instructions

### Step 1: Open Supabase SQL Editor

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" in left sidebar
4. Click "New Query"

---

### Step 2: Run Migration 001 (Agent 6/7 Course Fields)

**File:** `migrations/001_add_agent_enrichment_fields.sql`

**What it does:**
- Adds Agent 6 fields to `golf_courses` table:
  - segment, segment_confidence, segment_signals
  - range_intel, opportunity_scores
  - agent6_enriched_at

- Adds Agent 7 fields to `golf_courses` table:
  - water_hazard_count, water_hazard_confidence
  - water_hazard_details
  - agent7_enriched_at

**Instructions:**
1. Copy entire contents of `001_add_agent_enrichment_fields.sql`
2. Paste into Supabase SQL Editor
3. Click "Run" (bottom right)
4. Check for "Success" message (no errors)

**Expected Result:**
```
Success. No rows returned
```

---

### Step 3: Run Migration 002 (Agent 3/5/6.5 Contact Fields)

**File:** `migrations/002_agent_refactor_update.sql`

**What it does:**
- Adds Agent 3 enhanced fields to `golf_course_contacts`:
  - email_confidence, email_method
  - linkedin_method

- Adds Agent 5 enhanced fields to `golf_course_contacts`:
  - phone_method, phone_confidence

- Adds Agent 6.5 fields to `golf_course_contacts`:
  - tenure_years, tenure_confidence
  - previous_clubs, industry_experience_years
  - responsibilities, career_notes
  - agent65_enriched_at

- Removes deprecated fields:
  - conversation_starters, top_opportunity_1/2, agent6_enriched_at

**Instructions:**
1. Copy entire contents of `002_agent_refactor_update.sql`
2. Paste into Supabase SQL Editor
3. Click "Run"
4. Check for "Success" message

**Expected Result:**
```
Success. No rows returned
```

---

### Step 4: Verify Migrations

**Run this verification query:**

```sql
-- Check golf_courses columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'golf_courses'
  AND column_name IN (
    'segment',
    'segment_confidence',
    'water_hazard_count',
    'opportunity_scores',
    'range_intel'
  )
ORDER BY column_name;

-- Check golf_course_contacts columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'golf_course_contacts'
  AND column_name IN (
    'email_confidence',
    'email_method',
    'phone_method',
    'tenure_years',
    'previous_clubs',
    'responsibilities'
  )
ORDER BY column_name;
```

**Expected Result:**
You should see all the columns listed with their data types.

If any columns are missing, check the migration for errors.

---

### Step 5: Test with Sample Data (Optional)

**Run this test insert:**

```sql
-- Test insert into golf_courses
INSERT INTO golf_courses (
  course_name,
  state_code,
  segment,
  segment_confidence,
  water_hazard_count
) VALUES (
  'Test Migration Course',
  'VA',
  'high-end',
  8,
  5
) RETURNING id, course_name, segment;

-- If successful, delete test data
DELETE FROM golf_courses
WHERE course_name = 'Test Migration Course';
```

**Expected Result:**
Should insert and return the row, then delete it successfully.

---

## ✅ Verification Checklist

Before running the orchestrator, verify:

- ✅ Migration 001 ran successfully (no errors)
- ✅ Migration 002 ran successfully (no errors)
- ✅ Verification query shows all new columns
- ✅ Test insert/delete worked (optional)
- ✅ `.env` file has SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY set

---

## 🚨 Troubleshooting

### Error: "column already exists"
**Solution:** Migration already applied (safe to ignore)

### Error: "table does not exist"
**Solution:** Verify table names match your schema
- Expected: `golf_courses`, `golf_course_contacts`
- If different: Update migration file with your table names

### Error: "permission denied"
**Solution:** You need admin/owner access to run migrations
- Use Supabase dashboard (not API)
- Or contact project owner

### Error: "constraint violation"
**Solution:** Existing data conflicts with new constraints
- Check if you have enhancement_status values not in the enum
- May need to adjust constraint or update existing data first

---

## 📞 After Migration

**You're ready to test!**

Run:
```bash
python3 agents/orchestrator.py
```

This will enrich Richmond Country Club and write to your Supabase.

**Then verify data:**
```sql
SELECT * FROM golf_courses
WHERE course_name = 'Richmond Country Club';

SELECT * FROM golf_course_contacts
WHERE golf_course_id = (
  SELECT id FROM golf_courses
  WHERE course_name = 'Richmond Country Club'
);
```

---

**Questions? Issues? Let me know and I'll help debug!**
