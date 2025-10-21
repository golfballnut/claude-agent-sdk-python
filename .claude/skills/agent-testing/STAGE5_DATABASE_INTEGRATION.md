# Stage 5: Database Integration Testing

**Purpose:** Validate agents write data correctly to database using test tables that mirror production.

**Critical Insight:** Test tables must be EXACT mirrors of production to enable complete workflow testing without risking production data.

---

## Why Stage 5 Matters

**Problem:** Production database has 40+ columns that evolved over time. Test tables created early have minimal schema. This causes:
- Schema errors during testing
- Can't validate data writes
- Must test in production (risky!)
- No way to compare results

**Solution:** Mirror production schema in test tables

---

## The Test Table Mirroring Strategy

### **Pattern:**
```
Production Tables:          Test Tables:
- golf_courses         →   - test_golf_courses (exact mirror!)
- golf_course_contacts →   - test_golf_course_contacts (exact mirror!)
```

### **Benefits:**
✅ Safe testing (isolated from production data)
✅ Complete workflow validation (all columns exist)
✅ Edge function compatibility (schema matches)
✅ Fast iteration (break things safely)
✅ True production simulation

---

## The Database Integration Process

### **Step 1: Audit Schema Alignment (5-10 min)**

Use Supabase MCP to list tables and compare schemas:

```python
# List all tables
mcp__supabase__list_tables(project_id="xxx")

# Returns schema for each table including columns
```

**Compare:**
```
Production golf_courses: 43 columns
Test golf_courses: 17 columns
MISSING: 26 columns! ❌
```

### **Step 2: Create Alignment Migration (10-15 min)**

Create comprehensive migration that adds ALL missing columns:

```sql
-- Migration: Align test tables with production

-- Add missing columns to test_golf_courses
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS city VARCHAR;
ALTER TABLE test_golf_courses ADD COLUMN IF NOT EXISTS street_address VARCHAR;
-- ... (add all 26 missing columns)

-- Add missing columns to test_golf_course_contacts
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS contact_source VARCHAR;
ALTER TABLE test_golf_course_contacts ADD COLUMN IF NOT EXISTS source_url TEXT;
-- ... (add all missing columns)

-- Force schema cache reload
NOTIFY pgrst, 'reload schema';
```

**Pro tip:** Use `IF NOT EXISTS` - safe to run multiple times!

### **Step 3: Apply Migration via MCP (2 min)**

```python
# Apply migration
mcp__supabase__execute_sql(
  project_id="xxx",
  query="<full migration SQL>"
)

# Verify schema alignment
mcp__supabase__list_tables(project_id="xxx")

# Check column counts match
```

**Validation:**
```
Test tables: 50 columns
Production: 43 columns
✅ Test has MORE (superset is OK!)
```

### **Step 4: Create Test Versions of Files (10-15 min)**

**Pattern:** Never modify production files until Docker validates!

```bash
# Create test orchestrator
cp orchestrator.py test_orchestrator.py

# Modify test version (remove Agent 6.5, use Agent 4 tenure)
# Add ⚠️ TEST warning in header

# Create test Agent 8
cp agents/agent8_supabase_writer.py agents/test_agent8_supabase_writer.py

# Modify to read Agent 4's tenure format
# - OLD: contact.get("background", {}).get("tenure_years")
# - NEW: contact.get("tenure_years")
```

**File naming convention:**
- `test_orchestrator.py` - Test workflow coordinator
- `test_agent8_supabase_writer.py` - Test database writer
- `test_quick.py` - Quick test script

### **Step 5: Run Integration Test (5 min)**

```bash
python test_quick.py
```

**Expected output:**
```
✅ SUCCESS: Course enriched
💰 Total Cost: $0.XX
👥 Contacts: X written to database
💾 Course ID: uuid-xxx
```

### **Step 6: Validate Data in Database (5 min)**

Query test tables to verify data written correctly:

```sql
-- Check course data
SELECT id, course_name, segment, water_hazard_rating, agent_cost_usd
FROM test_golf_courses
WHERE course_name = 'Test Course';

-- Check contact tenure (THE KEY VALIDATION!)
SELECT
  contact_name,
  linkedin_url,
  tenure_years,      -- Should be 6.8 (not NULL!)
  tenure_start_date  -- Should be "Jan 2019"
FROM test_golf_course_contacts
WHERE golf_course_id = '<test-course-uuid>'
ORDER BY contact_name;
```

**Expected for Dustin Betthauser:**
```json
{
  "contact_name": "Dustin Betthauser",
  "linkedin_url": "https://linkedin.com/in/dustin-betthauser",
  "tenure_years": 6.8,           ← VALIDATES Agent 4 extraction!
  "tenure_start_date": "Jan 2019"
}
```

**Expected for contact without LinkedIn:**
```json
{
  "contact_name": "Bryan McFerren",
  "linkedin_url": null,
  "tenure_years": null,          ← Correct NULL handling!
  "tenure_start_date": null
}
```

---

## Common Issues & Solutions

### **Issue 1: Schema Cache Not Refreshing**

**Error:** `Could not find the 'column_name' column in the schema cache`

**Solution:**
```sql
NOTIFY pgrst, 'reload schema';
```

Or restart Supabase connection.

### **Issue 2: Data Type Mismatch**

**Error:** `invalid input syntax for type integer: "6.8"`

**Cause:** Agent returns decimal (6.8 years), column is INTEGER

**Solution:**
```sql
ALTER TABLE test_golf_course_contacts
  ALTER COLUMN tenure_years TYPE NUMERIC(4,1)
  USING tenure_years::numeric;
```

**Pro tip:** NUMERIC(4,1) = 4 total digits, 1 decimal place (0.0 to 999.9)

### **Issue 3: UUID vs Integer ID Mismatch**

**Error:** `invalid input syntax for type uuid: "108"`

**Cause:** Test tables use UUID, production uses INTEGER

**Solution:** Don't pass course_id to test tables - let them create/lookup by name:
```python
result = await enrich_course(
    course_name='Test Course',
    state_code='VA',
    course_id=None,  # Let test table generate UUID
    use_test_tables=True
)
```

### **Issue 4: Nested vs Top-Level Data**

**Error:** Tenure not written to database

**Cause:** Agent 8 reads from old format:
```python
contact.get("background", {}).get("tenure_years")  # Agent 6.5 format
```

But Agent 4 now provides:
```python
contact.get("tenure_years")  # Top-level
```

**Solution:** Update test_agent8.py to read from new location.

---

## Testing Checklist

**Before declaring database integration complete:**

- [ ] Test tables have ≥ production column count
- [ ] All missing columns added via migration
- [ ] Migration applied successfully via MCP
- [ ] Schema alignment verified (list_tables)
- [ ] Test orchestrator runs without schema errors
- [ ] Test Agent 8 reads from correct data locations
- [ ] Data written to test database successfully
- [ ] SQL query validates expected values exist
- [ ] NULL handling verified
- [ ] Data types correct (tenure as decimal, etc.)
- [ ] No production files modified

---

## Success Criteria

✅ All agents complete without schema errors
✅ Data written to test tables successfully
✅ SQL query shows tenure: 6.8 years (Agent 4 extraction!)
✅ NULL handling works (contacts without LinkedIn)
✅ Cost under budget
✅ Production files untouched

---

## Time Estimate

- Schema audit: 5-10 min
- Create migration: 10-15 min
- Apply migration: 2 min
- Create test files: 10-15 min
- Run integration test: 5 min
- Validate in database: 5 min
**Total: 40-50 minutes**

---

## Real Example from Golf Enrichment (Oct 20, 2025)

**Starting state:**
- test_golf_courses: 17 columns
- test_golf_course_contacts: 20 columns

**Ending state:**
- test_golf_courses: 50 columns (added 33!)
- test_golf_course_contacts: 51 columns (added 31!)

**Migrations applied:**
- 007: agent_cost_usd column
- 008: contact tracking columns
- 009: Complete alignment (58 ALTER statements)

**Result:**
- ✅ Agent 4 tenure extracted: 6.8 years
- ✅ Written to database successfully
- ✅ Validated via SQL query
- ✅ Ready for Docker testing

**Key lesson:** Align test tables COMPLETELY, not just minimal columns. Worth the upfront investment!

---

**Next:** Stage 6 (Docker Testing) - Use these test tables in Docker container!
