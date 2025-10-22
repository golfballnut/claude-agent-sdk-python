---
name: Supabase-to-ClickUp Sync SOP
description: Complete methodology for syncing enriched data from Supabase to ClickUp with idempotent operations, field validation, and protection mechanisms. Covers audit procedures, single-source-of-truth architecture, incremental testing, and production deployment. Proven Oct 21, 2025 with Course 159 (5 contacts, tenure data, zero errors). Use when integrating database-to-CRM workflows, fixing sync issues, implementing automation safely, or preventing data corruption in active sales workflows.
allowed-tools: Read, Bash, Edit, Write, mcp__supabase__execute_sql, mcp__supabase__list_tables, mcp__clickup__get_task, mcp__clickup__get_workspace_tasks, mcp__clickup__create_task, mcp__clickup__update_task, mcp__clickup__get_workspace_hierarchy
---

# Supabase-to-ClickUp Sync SOP

**Proven:** Oct 21, 2025 - Course 159 test (5 contacts, 3 with LinkedIn + tenure, zero errors)
**Purpose:** Safely sync database enrichments to ClickUp without corrupting active sales workflows
**Team:** Golf Course Enrichment

---

## 🎯 **The Golden Rules**

### **Rule #1: AUDIT BEFORE ACTING**
> Never assume sync state. Always audit ClickUp + Supabase to identify safe vs protected data.

**Why:** We discovered 30 courses with active outreach that would've been corrupted without audit.

### **Rule #2: SINGLE SOURCE OF TRUTH**
> One system writes to database. Edge functions READ and sync to ClickUp.

**Why:** Double-writes cause conflicts. Agent 8 has proper UPSERT logic, edge functions should only read.

### **Rule #3: PROTECT ACTIVE WORKFLOWS**
> Check if ClickUp task exists with active workflow before modifying.

**Why:** Sales team has 30 active outreach campaigns - automation must not disrupt them.

### **Rule #4: DROPDOWN FIELDS = OPTION INDICES**
> ClickUp dropdowns require option index (0, 1, 2), not string values.

**Why:** "VA" fails validation. Must use STATE_OPTION_INDEX['VA'] = 0.

### **Rule #5: TEST INCREMENTALLY**
> Test 1 course, fix issues, then scale. Don't batch test with broken code.

**Why:** Course 159 test revealed 3 field validation errors. Fixed all before scaling.

---

## 📐 **The 5-Stage Process**

### **Stage 1: Pre-Deployment Audit** ⭐ CRITICAL

**Purpose:** Identify safe test candidates and protect active data

**Steps:**
1. **Audit ClickUp:** Find courses with active outreach (DON'T TOUCH)
   ```sql
   -- Get courses with active outreach
   SELECT DISTINCT c.id, c.course_name
   FROM golf_courses c
   JOIN outreach_activities o ON o.golf_course_id = c.id
   WHERE o.clickup_task_id IS NOT NULL
   ORDER BY c.course_name;
   ```

2. **Audit Supabase:** Find enriched courses WITHOUT outreach (SAFE)
   ```sql
   -- Get safe test candidates
   SELECT
     c.id, c.course_name, c.enrichment_status,
     COUNT(contacts.contact_id) as contact_count
   FROM golf_courses c
   LEFT JOIN golf_course_contacts contacts ON contacts.golf_course_id = c.id
   LEFT JOIN outreach_activities o ON o.golf_course_id = c.id
   WHERE c.enrichment_status = 'completed'
     AND o.activity_id IS NULL  -- NO outreach = SAFE
   GROUP BY c.id
   HAVING COUNT(contacts.contact_id) >= 2
   ORDER BY c.enrichment_completed_at DESC
   LIMIT 10;
   ```

3. **Cross-Reference:** Verify no conflicts

4. **Document:**
   - Safe candidates list (9+ courses)
   - Protected courses list (30 in our case)
   - Sync discrepancies found
   - Cleanup needed

**Deliverable:** List of 10+ safe test candidates + protected list

**Time:** 1 hour

---

### **Stage 2: Architecture Validation**

**Purpose:** Ensure single source of truth, no double-writes

**Check:**
1. **Who writes to database?**
   - ✅ Agent 8 (orchestrator) = PRIMARY writer
   - ❌ Edge function should NOT write (read only)

2. **Data flow:**
   ```
   Agent 8 → Writes DB (courses + contacts)
     ↓
   api.py → Sends webhook (minimal payload)
     ↓
   receive-agent-enrichment → Triggers ClickUp sync (NO DB writes!)
     ↓
   create-clickup-tasks → Reads DB + Creates ClickUp tasks
   ```

3. **Verify UPSERT logic:**
   - Agent 8: Has proper upsert (checks existing by course_id, name)
   - Edge function: Should NOT insert (causes duplicates)

**Red Flags:**
- ❌ Edge function has INSERT statements
- ❌ Two systems updating same tables
- ❌ No unique constraints to prevent duplicates

**Deliverable:** Confirmed single-source architecture

**Time:** 30 min

---

### **Stage 3: Field Validation & Mapping**

**Purpose:** Map database fields to ClickUp custom fields correctly

**ClickUp Field Rules:**

1. **Dropdown Fields → Option Index (not string)**
   ```typescript
   // WRONG:
   { id: 'state-field-id', value: 'VA' }  // ❌ Fails validation

   // CORRECT:
   const STATE_INDEX = { 'VA': 0, 'MD': 1, ... }
   { id: 'state-field-id', value: STATE_INDEX['VA'] }  // ✅ Works
   ```

2. **Phone Field → Description Only**
   - ClickUp has strict phone validation
   - Safer to put in description, not custom field

3. **Status → Omit (use list default)**
   - Each list has different status options
   - Let ClickUp set default status

4. **Relationships → Array of Task IDs**
   ```typescript
   // Link to course
   { id: 'course-relationship-id', value: [courseTaskId] }

   // Link to multiple contacts
   { id: 'contacts-relationship-id', value: [contact1Id, contact2Id, contact3Id] }
   ```

**Mappings to Create:**
```typescript
const STATE_OPTION_INDEX = {
  'VA': 0, 'MD': 1, 'NC': 2, 'PA': 3, 'DC': 4,
  'WV': 5, 'SC': 6, 'TN': 7, 'FL': 8, 'GA': 9,
  'NY': 10, 'NJ': 11, 'OH': 12
}

const SEGMENT_OPTION_INDEX = {
  'high-end': 0, 'budget': 1, 'both': 2, 'unknown': 3
}
```

**Deliverable:** Complete field mapping constants

**Time:** 1 hour (includes testing each field)

---

### **Stage 4: Protection Implementation**

**Purpose:** Safeguard active sales workflows from automation

**Protection Mechanism:**
```typescript
// Check if course has existing outreach with ClickUp task
const { data: outreachDb } = await supabase
  .from('outreach_activities')
  .select('activity_id, clickup_task_id, status')
  .eq('golf_course_id', payload.course_id)
  .maybeSingle()

if (outreachDb && outreachDb.clickup_task_id) {
  console.log(`⚠️  PROTECTION ACTIVATED!`)
  console.log(`    Course ${payload.course_id} has active outreach`)
  console.log(`    SKIPPING outreach task modification`)

  // Still update Course + Contact tasks, just skip Outreach
  results.outreach_task = {
    taskId: outreachDb.clickup_task_id,
    action: 'protected - not modified'
  }
} else {
  // Safe to create/update outreach task
}
```

**Test Protection:**
- Try syncing protected course (should skip outreach)
- Verify Course + Contact tasks still updated
- Verify outreach task not modified

**Deliverable:** Protection code + test validation

**Time:** 30 min

---

### **Stage 5: Incremental Testing**

**Purpose:** Test with 1 safe candidate, fix issues, then scale

**Test Strategy:**

**Test 1: First-Time Creation (Best Data)**
- Course: Pick candidate with most contacts + LinkedIn + tenure
- Example: Course 159 (5 contacts, 3 with tenure 9.7-20.8 years)
- Expected: Create 1 Course + 5 Contact + 1 Outreach task
- Validate: All 3 task types in ClickUp, relationships working

**Test 2: Update Flow (Re-enrichment)**
- Course: Same as Test 1
- Action: Re-run webhook
- Expected: UPDATE all tasks (no duplicates)
- Validate: Same ClickUp task IDs in database

**Test 3: Protection Test**
- Course: Pick protected course (has active outreach)
- Expected: Outreach NOT modified, Course + Contacts updated
- Validate: Outreach task unchanged in ClickUp

**Test 4-9: Batch Validation**
- Courses: 6 more safe candidates
- Expected: All succeed with zero errors
- Validate: Success rate 100%

**Validation Checklist:**
- [ ] All 3 task types created in ClickUp
- [ ] Descriptions have enriched data (tenure, LinkedIn, confidence)
- [ ] Relationships working (can click Course → see Contacts)
- [ ] Database synced (clickup_task_id populated)
- [ ] No duplicates created
- [ ] Protected courses untouched

**Deliverable:** 100% success rate on 9+ test candidates

**Time:** 2 hours

---

## 🚨 **Red Flags (Stop and Fix)**

**Stop if you see:**
- ❌ Duplicate ClickUp tasks created
- ❌ Active outreach tasks modified
- ❌ Field validation errors (400 responses)
- ❌ Contacts missing from Outreach description
- ❌ Relationships not working (can't click through)
- ❌ Database unique constraint violations

**Do this instead:**
1. Check logs for specific error
2. Verify field mappings (use option indices)
3. Test protection mechanism
4. Validate with single course first
5. Don't proceed to batch until zero errors

---

## 📋 **Quick Reference**

### **Audit Queries:**

```sql
-- Find safe test candidates
SELECT c.id, c.course_name, COUNT(contacts.contact_id) as contacts
FROM golf_courses c
LEFT JOIN golf_course_contacts contacts ON contacts.golf_course_id = c.id
LEFT JOIN outreach_activities o ON o.golf_course_id = c.id
WHERE c.enrichment_status = 'completed'
  AND o.activity_id IS NULL
GROUP BY c.id
HAVING COUNT(contacts.contact_id) >= 2
ORDER BY c.enrichment_completed_at DESC;

-- Find protected courses
SELECT c.id, c.course_name, o.clickup_task_id
FROM golf_courses c
JOIN outreach_activities o ON o.golf_course_id = c.id
WHERE o.clickup_task_id IS NOT NULL;

-- Check sync discrepancies
SELECT c.id, c.course_name,
       COUNT(contacts.contact_id) as total,
       COUNT(contacts.clickup_task_id) as synced
FROM golf_courses c
JOIN golf_course_contacts contacts ON contacts.golf_course_id = c.id
WHERE c.clickup_task_id IS NOT NULL
GROUP BY c.id
HAVING COUNT(contacts.contact_id) > COUNT(contacts.clickup_task_id);
```

### **Test Commands:**

```bash
# Test single course
curl -X POST 'https://[project].supabase.co/functions/v1/receive-agent-enrichment' \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"course_id": 159, "success": true, "course_name": "Dominion Valley CC", "state_code": "VA"}'

# Verify in database
SELECT clickup_task_id, clickup_synced_at
FROM golf_courses WHERE id = 159;

SELECT contact_name, clickup_task_id
FROM golf_course_contacts WHERE golf_course_id = 159;
```

---

## ✅ **Success Criteria**

**System is ready when:**
- ✅ Audit complete (safe + protected lists documented)
- ✅ Single source of truth confirmed (Agent 8 writes, edge functions read)
- ✅ Field mappings correct (dropdown indices, not strings)
- ✅ Protection mechanism active (tests confirm)
- ✅ Test 1 passes (1 course, all 3 task types, zero errors)
- ✅ Relationships verified (can click through in ClickUp UI)
- ✅ Batch test passes (9+ courses, 100% success)

**Production ready when:**
- ✅ Documentation complete (implementation doc + this Skill)
- ✅ Test results validated (ClickUp UI checked visually)
- ✅ Zero impact on protected courses confirmed
- ✅ Monitoring queries in place
- ✅ Rollback plan documented

---

## 📊 **Patterns Reference**

### **Pattern 1: Audit-First Deployment**

**When:** Before any sync automation
**What:** Identify safe vs protected data
**How:** SQL queries + ClickUp workspace tasks audit
**Why:** Prevents corrupting active workflows

### **Pattern 2: Single Source of Truth**

**When:** Multiple systems could write same data
**What:** Designate one system as writer, others as readers
**How:** Agent 8 writes DB, edge functions read + sync ClickUp
**Why:** Eliminates conflicts, simplifies logic

### **Pattern 3: Idempotent Upsert**

**When:** System may be called multiple times
**What:** Try UPDATE (if task_id exists) → fallback CREATE (if 404)
**How:** Check existing task ID, attempt update, handle 404, create if needed
**Why:** Safe re-enrichment, handles deleted tasks

### **Pattern 4: Dropdown Index Mapping**

**When:** ClickUp custom fields with dropdown type
**What:** Map string values to option indices (0, 1, 2...)
**How:** Create mapping constants, use indices in API calls
**Why:** ClickUp validates strictly, strings cause 400 errors

### **Pattern 5: Protection Mechanisms**

**When:** Automation could modify user-managed data
**What:** Check for active workflows, skip if protected
**How:** Query outreach_activities, check clickup_task_id, skip if exists
**Why:** Sales team actively working 30 campaigns - don't disrupt

### **Pattern 6: Rich Context Descriptions**

**When:** Creating outreach/sales tasks
**What:** Include ALL contacts with full enriched data in description
**How:** Template with loops, conditional formatting, context-aware rationale
**Why:** Sales team sees complete picture, never leaves task

### **Pattern 7: Incremental Testing**

**When:** Deploying new sync automation
**What:** Test 1 course → fix → test 3 more → fix → scale to all
**How:** Pick best test data first, validate thoroughly, iterate
**Why:** Catches issues early, cheaper to fix, higher confidence

---

## 🧪 **Case Study: Oct 21, 2025 Session**

### **Starting Point:**
- 358 golf courses in database
- 95 enriched with agent data
- Some have ClickUp tasks, inconsistent sync state
- Need to automate: Enrichment → ClickUp task creation

### **Audit Results:**
- ✅ 9 safe test candidates (enriched + NO outreach)
- ⚠️ 30 protected courses (active outreach - DON'T TOUCH!)
- ⚠️ 10 courses with sync discrepancies (missing contact tasks)
- ⚠️ 3 courses with duplicate outreach_activities rows

### **Issues Found:**

**Issue 1: Double-Write Architecture**
- Agent 8 writes to DB
- Edge function ALSO writes to DB (duplicate!)
- Fix: Edge function reads only

**Issue 2: ClickUp Field Validation**
- Dropdown fields sent as strings ('VA') → 400 error
- Phone field validation failing
- Status field using wrong values
- Fix: Use option indices, omit phone/status

**Issue 3: No Protection**
- Automation would modify 30 active outreach tasks
- Sales workflows would be disrupted
- Fix: Check existing outreach, skip if protected

### **Test Results (Course 159 - Dominion Valley CC):**

**Before Fixes:**
- ❌ 4 contact tasks failed (phone validation)
- ❌ 1 contact task failed (dropdown validation)
- ❌ Outreach task failed (invalid status)

**After Fixes:**
- ✅ 1 Course task updated (86b6xy9xt)
- ✅ 5 Contact tasks created (86b7679n0-8)
- ✅ 1 Outreach task created (86b7679n9)
- ✅ Zero errors!
- ✅ Rich description with ALL 5 contacts + tenure data
- ✅ Relationships set (can click through)

**Data Quality:**
- 3 contacts with LinkedIn URLs
- 3 contacts with tenure: 9.7, 1.8, 20.8 years
- Tenure highlighting: "⭐ LONG TENURE!" for 20.8 years
- Context-aware rationale for each contact

---

## 📝 **Implementation Checklist**

### **Phase 0: Audit & Preparation**
- [ ] Run ClickUp audit (find active outreach)
- [ ] Run Supabase audit (find safe candidates)
- [ ] Document 10+ safe test candidates
- [ ] Document protected courses list
- [ ] Clean up duplicates (if found)
- [ ] Export ClickUp backup (all lists to CSV)

### **Phase 1: Architecture**
- [ ] Verify Agent 8 is primary DB writer
- [ ] Verify edge function doesn't write to DB
- [ ] Implement: receive-agent-enrichment (webhook receiver, NO DB writes)
- [ ] Implement: create-clickup-tasks (reads DB, syncs ClickUp)

### **Phase 2: Field Mapping**
- [ ] Create dropdown option index mappings
- [ ] Remove phone from custom_fields
- [ ] Remove status from task creation
- [ ] Map all custom fields (Course, Contact, Outreach)

### **Phase 3: Protection**
- [ ] Add protection check before outreach creation
- [ ] Test with protected course
- [ ] Verify outreach not modified
- [ ] Verify Course + Contacts still updated

### **Phase 4: Testing**
- [ ] Test 1: Best data course (most contacts + LinkedIn + tenure)
- [ ] Fix any errors found
- [ ] Test 2: Re-run same course (verify UPDATE not CREATE)
- [ ] Test 3: Protected course (verify protection works)
- [ ] Test 4-9: Batch test 6 more safe candidates
- [ ] Validate: 100% success rate

### **Phase 5: Production**
- [ ] Enable automation
- [ ] Monitor first 3 enrichments
- [ ] Verify zero impact on protected courses
- [ ] Document success rate
- [ ] Update team documentation

---

## 🎯 **Common Mistakes to Avoid**

### **Mistake #1: Testing with Active Outreach**
❌ **DON'T:** Test with Course 142 (has active outreach)
✅ **DO:** Test with Course 159 (safe candidate)
**Result:** Protected 30 active sales workflows

### **Mistake #2: Using String Values for Dropdowns**
❌ **DON'T:** `{ id: 'state-field', value: 'VA' }`
✅ **DO:** `{ id: 'state-field', value: STATE_INDEX['VA'] }`
**Result:** Fixed 5 validation errors

### **Mistake #3: Double-Writing to Database**
❌ **DON'T:** Agent 8 writes + Edge function writes
✅ **DO:** Agent 8 writes, Edge function reads
**Result:** Eliminated duplicate write conflicts

### **Mistake #4: Batch Testing Broken Code**
❌ **DON'T:** Test all 9 courses with field errors
✅ **DO:** Test 1, fix errors, then scale
**Result:** Saved time, caught issues early

### **Mistake #5: Skipping Audit**
❌ **DON'T:** Assume all courses are safe to test
✅ **DO:** Audit first, identify safe vs protected
**Result:** Prevented corrupting 30 active outreach tasks

---

## 📚 **Related Documentation**

**In this Skill:**
- `PATTERNS.md` - 7 key patterns with code examples
- `EXAMPLES.md` - Real case studies from Oct 21 session
- `STAGE1_AUDIT.md` - Complete audit procedures
- `STAGE3_FIELD_VALIDATION.md` - ClickUp field mappings
- `STAGE4_PROTECTION.md` - Protection mechanism details

**In Project:**
- `teams/golf-enrichment/docs/1_IMPLEMENTATION/CLICKUP_SYNC_OCT21_IMPLEMENTATION.md` - Complete implementation doc
- `teams/golf-enrichment/docs/1_IMPLEMENTATION/CLICKUP_ARCHITECTURE.md` - Field specifications
- `teams/golf-enrichment/supabase/functions/create-clickup-tasks/index.ts` - Working implementation

---

## ⏱️ **Timeline**

**Total:** ~6 hours for complete implementation

- Phase 0: Audit (1 hour)
- Phase 1: Architecture (1 hour)
- Phase 2: Field Mapping (1 hour)
- Phase 3: Protection (30 min)
- Phase 4: Testing (2 hours)
- Phase 5: Production (30 min)

**Actual Oct 21:** 6 hours including:
- 3 major architecture fixes
- Field validation debugging
- Protection mechanism
- Successful test with Course 159

---

## 🎊 **Success Metrics**

**From Oct 21 Session:**
- ✅ 9 safe test candidates identified
- ✅ 30 protected courses safeguarded
- ✅ 3 duplicate outreach activities cleaned
- ✅ Single-source architecture implemented
- ✅ Field validation fixed (dropdown indices)
- ✅ Course 159 test: 0 errors, all 3 task types created
- ✅ Rich descriptions: ALL 5 contacts with tenure/LinkedIn/context
- ✅ Idempotent upsert working (course task UPDATED, contacts CREATED)

**Expected Production Results:**
- New enrichments auto-create ClickUp tasks
- Re-enrichments update existing tasks (no duplicates)
- Active outreach protected (30 courses untouched)
- Sales team has complete context in every task
- Database always in sync with ClickUp

---

## 🚀 **When to Use This Skill**

**Use for:**
- Database enrichment → CRM sync workflows
- Supabase → ClickUp automation
- Fixing sync state discrepancies
- Implementing idempotent operations
- Protecting active user workflows
- Re-enrichment scenarios (data improves over time)

**Don't use for:**
- One-time manual data entry
- Simple ClickUp task creation
- Systems without re-enrichment needs
- When user manages all ClickUp tasks manually

---

**Last Updated:** Oct 21, 2025
**Status:** Production-ready (validated with Course 159)
**Maintainer:** Golf Enrichment Team
