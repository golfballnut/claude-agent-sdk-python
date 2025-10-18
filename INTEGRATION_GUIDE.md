# Golf Course Outreach System - Integration Guide

**Last Updated:** October 18, 2024
**Status:** Documentation for two-project integration
**Projects:** `golf-course-outreach` + `claude-agent-sdk-python`

---

## 🏗️ **Architecture Overview**

### **Two-Project System:**

```
┌────────────────────────────────────────────────────────────────┐
│ Project 1: golf-course-outreach                                │
│ ├── Slash commands (/map-regions, /validate-courses)          │
│ ├── Supabase edge functions (batch-import, triggers)          │
│ └── Production database (golf_courses, golf_course_contacts)  │
└────────────────────────────────────────────────────────────────┘
                              ↓ calls
┌────────────────────────────────────────────────────────────────┐
│ Project 2: claude-agent-sdk-python (THIS REPO)                 │
│ ├── 8 intelligent agents (enrichment workflow)                 │
│ ├── Orchestrator (coordinates agents)                          │
│ ├── FastAPI wrapper (api.py)                                   │
│ └── Deployed to Render                                         │
│     URL: https://agent7-water-hazards.onrender.com            │
└────────────────────────────────────────────────────────────────┘
                              ↓ writes back to
┌────────────────────────────────────────────────────────────────┐
│ Supabase Production Database                                   │
│ ├── golf_courses (updated with segment, intel)                │
│ └── golf_course_contacts (enriched data)                      │
└────────────────────────────────────────────────────────────────┘
                              ↓ syncs to
┌────────────────────────────────────────────────────────────────┐
│ ClickUp CRM                                                    │
│ ├── Folder: HIGH-END CLUBS                                     │
│ ├── Folder: BUDGET CLUBS                                       │
│ └── Tasks: Enriched contacts ready for outreach               │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔄 **Complete 5-Step Workflow**

### **Step 1: Map Regions** ✅ MANUAL

**Project:** `golf-course-outreach`
**Trigger:** Slash command `/map-regions`
**Location:** `.claude/commands/map-regions.md`

**What it does:**
- Creates state/region entries in Supabase
- Organizes multi-state expansion
- One-time setup per new state

**Output:** `regions` table populated

---

### **Step 2: Find Courses in State** ✅ MANUAL

**Project:** `golf-course-outreach`
**Trigger:** Slash command `/validate-courses`
**Location:** `.claude/commands/validate-courses.md`

**What it does:**
- Searches for golf courses in a state (VSGA or other directory)
- Populates `golf_courses` table with:
  - `course_name`
  - `state`
  - `enrichment_status` = NULL
  - `google_enriched` = false

**Output:** Course rows created (minimal data)

**Cost:** ~$0.01-0.02 per course (directory fetch)

---

### **Step 3: Google Places Enrichment** ✅ MANUAL

**Project:** `golf-course-outreach`
**Trigger:** Edge function `batch-import-courses`
**URL:** `https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/batch-import-courses`

**What it does:**
- Reads courses where `google_enriched = false`
- Calls Google Places API for each course
- Updates `golf_courses` table:
  - `website` (from Google)
  - `google_maps_link`
  - `address`
  - `phone` (Google's data)
  - `google_enriched` = true

**Output:** Course rows enriched with Google data

**Cost:** $0.017 per lookup (Google Places API pricing)

---

### **Step 4: Agent Workflow Enrichment** 🔄 NEW - DESIGN TRIGGER

**Projects:** Both (trigger in `golf-course-outreach`, agents in `claude-agent-sdk-python`)

#### **Manual Trigger (Current - To Implement):**

```sql
-- Admin manually requests enrichment
UPDATE golf_courses
SET enrichment_status = 'pending',
    enrichment_requested_at = NOW()
WHERE id = 'course-uuid-here';
```

#### **Flow:**

```
1. UPDATE enrichment_status = 'pending'
   ↓
2. Database Trigger fires
   CREATE TRIGGER on_enrichment_status_pending
   AFTER UPDATE OF enrichment_status ON golf_courses
   ↓
3. Calls Edge Function: trigger-agent-enrichment
   ↓
4. Edge Function:
   a. Updates enrichment_status = 'processing'
   b. Calls Render API:
      POST https://agent7-water-hazards.onrender.com/enrich-course
      Body: {
        course_name: "Country Club of Virginia",
        state_code: "VA",
        course_id: "uuid",
        use_test_tables: false
      }
   ↓
5. Render API (Agents 1-8 run for 4-7 minutes)
   ↓
6. Render sends webhook back to Supabase:
   POST /functions/v1/receive-agent-enrichment
   Body: {
     course_id: "uuid",
     contacts: [...],
     agent_results: {...},
     total_cost: 0.19
   }
   ↓
7. Edge Function: receive-agent-enrichment
   a. Updates golf_courses:
      - enrichment_status = 'complete'
      - segment, water_hazards, opportunities, etc.
   b. Inserts into golf_course_contacts (triggers Step 5!)
```

**Output:** Enriched course + contacts in Supabase

**Cost:** $0.18-0.28 per course (agent workflow)

---

### **Step 5: ClickUp Outreach Tasks** 📋 TO BUILD

**Project:** `golf-course-outreach`
**Trigger:** Database trigger ON INSERT `golf_course_contacts`
**Edge Function:** `create-clickup-tasks`

**What it does:**
1. New contact inserted → trigger fires
2. Edge function reads contact enrichment data
3. Determines ClickUp folder:
   - `segment = 'high-end'` → Folder: "HIGH-END CLUBS"
   - `segment = 'budget'` → Folder: "BUDGET CLUBS"
   - `segment = 'both'` → Folder: "BOTH"
4. Creates ClickUp task in "New Leads" list:
   - Task name: `{Name} - {Title} | {Company}`
   - Custom fields: Email, Phone, LinkedIn, Segment, Opportunities
   - Description: Conversation starters + business intel
5. Updates 3 ClickUp lists:
   - Golf Courses list (course-level task)
   - Contacts list (contact-level task)
   - Outreach Activities list (campaign task)

**Output:** Sales team sees qualified lead in ClickUp CRM

**Cost:** $0 (ClickUp API free)

---

## 🗄️ **Database Schema (Integration Fields)**

### **golf_courses table** (Additions needed)

```sql
-- Workflow control fields
enrichment_status TEXT,              -- 'pending', 'processing', 'complete', 'error'
enrichment_requested_at TIMESTAMPTZ, -- When Step 4 triggered
enrichment_completed_at TIMESTAMPTZ, -- When agents finished
enrichment_error TEXT,               -- Error message if failed
google_enriched BOOLEAN,             -- Step 3 complete flag

-- Agent output fields
segment TEXT,                        -- 'high-end', 'budget', 'both'
segment_confidence INT,              -- 1-10
water_hazards INT,                   -- From Agent 7
opportunities JSONB,                 -- 6 opportunity scores from Agent 6
range_intel JSONB,                   -- Range data from Agent 6
agent_cost_usd DECIMAL(10,4),       -- Total agent workflow cost

-- See migration: teams/golf-enrichment/migrations/004_agent_integration_fields.sql
```

### **golf_course_contacts table** (Additions needed)

```sql
-- Contact enrichment (from agents)
email TEXT,
email_confidence INT,
linkedin_url TEXT,
phone TEXT,
phone_confidence INT,

-- Background data (Agent 6.5)
tenure_years INT,
previous_clubs JSONB,

-- Business intelligence (Agent 6)
segment TEXT,                        -- Inherited from course or contact-specific
opportunities JSONB,                 -- Opportunity scores
conversation_starters JSONB,         -- Pre-written openers

-- Metadata
enriched_at TIMESTAMPTZ,
clickup_task_id TEXT                 -- Link back to CRM
```

---

## 🔌 **Edge Functions (3 Required)**

### **Function 1: trigger-agent-enrichment**

**Location:** `golf-course-outreach/supabase/functions/trigger-agent-enrichment/index.ts`

**Triggered by:** Database trigger when `enrichment_status` changes to 'pending'

**Responsibility:**
1. Read course data from golf_courses
2. Update status to 'processing'
3. Call Render API (claude-agent-sdk-python)
4. Handle errors (mark as 'error' if API unreachable)

**See:** `teams/golf-enrichment/docs/EDGE_FUNCTIONS.md` for full code

---

### **Function 2: receive-agent-enrichment**

**Location:** `golf-course-outreach/supabase/functions/receive-agent-enrichment/index.ts`

**Triggered by:** Webhook from Render (after agents complete)

**Responsibility:**
1. Receive enriched data from agents
2. Update golf_courses (segment, opportunities, status='complete')
3. Insert golf_course_contacts (triggers Step 5!)
4. Error handling (log failures)

**See:** `teams/golf-enrichment/docs/EDGE_FUNCTIONS.md` for full code

---

### **Function 3: create-clickup-tasks**

**Location:** `golf-course-outreach/supabase/functions/create-clickup-tasks/index.ts`

**Triggered by:** Database trigger ON INSERT `golf_course_contacts`

**Responsibility:**
1. Read contact + enrichment data
2. Determine folder by segment
3. Create ClickUp task with:
   - Custom fields populated
   - Conversation starters in description
   - Opportunity scores visible
4. Update contact with clickup_task_id
5. Update 3 ClickUp lists

**See:** `teams/golf-enrichment/docs/EDGE_FUNCTIONS.md` for full code

---

## 🎯 **Manual Trigger Process (Step 4)**

### **Current Implementation (What You'll Do Now):**

**Step-by-Step:**

1. **Check courses ready for enrichment:**
   ```sql
   SELECT id, course_name, state, website, google_enriched, enrichment_status
   FROM golf_courses
   WHERE google_enriched = true
     AND enrichment_status IS NULL
   LIMIT 10;
   ```

2. **Select a course to enrich:**
   ```sql
   -- Copy the course_id (UUID)
   ```

3. **Trigger enrichment manually:**
   ```sql
   UPDATE golf_courses
   SET enrichment_status = 'pending',
       enrichment_requested_at = NOW()
   WHERE id = '1531adbd-0f79-496b-a459-c66e9b2a0d4d';
   ```

4. **Database trigger fires automatically:**
   - Calls edge function `trigger-agent-enrichment`
   - Edge function calls Render API
   - Agents run (4-7 min)

5. **Monitor progress:**
   ```sql
   SELECT enrichment_status, enrichment_requested_at, enrichment_completed_at
   FROM golf_courses
   WHERE id = 'your-uuid';

   -- Status progression:
   -- pending → processing → complete (or error)
   ```

6. **Verify results:**
   ```sql
   -- Check enriched data
   SELECT * FROM golf_courses WHERE id = 'your-uuid';

   -- Check contacts created
   SELECT * FROM golf_course_contacts WHERE golf_course_id = 'your-uuid';
   ```

---

## ⚡ **Future Automation Options**

### **Option A: Auto-Enrich After Google** (Immediate)
```sql
-- Automatically request enrichment when Google enrichment completes
CREATE TRIGGER auto_request_enrichment
AFTER UPDATE OF google_enriched ON golf_courses
FOR EACH ROW
WHEN (NEW.google_enriched = true AND NEW.enrichment_status IS NULL)
EXECUTE FUNCTION set_enrichment_pending();
```

**Pros:** Fully automated
**Cons:** No manual control, costs can spiral

### **Option B: Batch Processing** (Hourly/Daily)
```typescript
// Supabase cron edge function
// Runs every hour, processes 10 courses

const coursesToEnrich = await supabase
  .from('golf_courses')
  .select('*')
  .eq('google_enriched', true)
  .is('enrichment_status', null)
  .order('created_at', { ascending: true })
  .limit(10);

for (const course of coursesToEnrich) {
  await supabase
    .from('golf_courses')
    .update({ enrichment_status: 'pending' })
    .eq('id', course.id);
  // Triggers agent workflow
}
```

**Pros:** Rate limiting, predictable costs
**Cons:** Not real-time

### **Option C: Manual Queue Approval** (Most Control)
```
1. Admin reviews courses in Supabase dashboard
2. Selects courses to enrich (checkbox UI)
3. Bulk UPDATE enrichment_status = 'pending'
4. Agents process selected courses
```

**Pros:** Full control, cost predictability
**Cons:** Manual step required

**Recommendation:** Start with Option C (manual), move to Option B (batch) once validated

---

## 🔐 **Environment Variables (Required)**

### **Render Service** (`claude-agent-sdk-python`)
```env
# Already configured in Render dashboard
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
HUNTER_API_KEY=...
SUPABASE_URL=https://oadmysogtfopkbmrulmq.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
FIRECRAWL_API_KEY=...
JINA_API_KEY=...
BRIGHTDATA_API_TOKEN=...
```

### **Supabase Edge Functions** (`golf-course-outreach`)
```env
# Set in Supabase edge function secrets
RENDER_API_URL=https://agent7-water-hazards.onrender.com
CLICKUP_API_KEY=pk_...
CLICKUP_WORKSPACE_ID=...
CLICKUP_LIST_IDS={"high-end": "...", "budget": "...", "both": "..."}
```

---

## 📊 **Data Flow Diagram**

```
Admin (Manual)
  │
  │ Step 1: /map-regions
  ├────────────────────────────────────┐
  │                                    │
  ↓                                    ↓
regions table                    Admin reviews
  │
  │ Step 2: /validate-courses
  ├────────────────────────────────────┐
  │                                    │
  ↓                                    ↓
golf_courses                      Admin reviews
(name, state only)
  │
  │ Step 3: batch-import-courses (Edge Function)
  ├────────────────────────────────────┐
  │                                    │
  ↓                                    ↓
Google Places API ──────────────> golf_courses
(website, maps, phone)           (google_enriched=true)
  │
  │ Step 4: Manual UPDATE enrichment_status='pending'
  ├────────────────────────────────────────┐
  │                                        │
  ↓                                        ↓
DB Trigger ──> trigger-agent-enrichment   Admin monitors
               (Edge Function)
  │
  ├────────────────────────────────────────┐
  │                                        │
  ↓                                        ↓
Render API                           enrichment_status
(Agent Workflow)                     = 'processing'
  │
  │ 4-7 minutes (Agents 1-8)
  ├────────────────────────────────────────┐
  │                                        │
  ↓                                        ↓
Webhook: receive-agent-enrichment    enrichment_status
  │                                  = 'complete'
  ├────────────────────────────────────────┐
  │                                        │
  ↓                                        ↓
golf_courses updated                golf_course_contacts
(segment, intel, hazards)           inserted (NEW ROWS)
  │
  │ Step 5: DB Trigger ON INSERT contacts
  ├────────────────────────────────────────┐
  │                                        │
  ↓                                        ↓
create-clickup-tasks                 ClickUp Tasks
(Edge Function)                      (Segmented folders)
  │
  ├────────────────────────────────────────┐
  │                                        │
  ↓                                        ↓
ClickUp MCP                          Sales Team
(3 lists updated)                    (Ready for outreach!)
```

---

## 🛠️ **Implementation Checklist**

### **Phase 1: Database Schema** (30 min)
- [ ] Create migration: `004_agent_integration_fields.sql`
- [ ] Apply to production Supabase
- [ ] Verify columns added
- [ ] Test indexes

### **Phase 2: Edge Function 1** (1-2 hours)
- [ ] Create `trigger-agent-enrichment/index.ts`
- [ ] Deploy to Supabase
- [ ] Test: Call manually with test course_id
- [ ] Verify: Render API receives request

### **Phase 3: Render API Webhook** (1 hour)
- [ ] Update `production/golf-enrichment/api.py`
- [ ] Add webhook callback after enrichment
- [ ] Pass `course_id` through workflow
- [ ] Deploy to Render
- [ ] Test: Verify webhook sent

### **Phase 4: Edge Function 2** (1 hour)
- [ ] Create `receive-agent-enrichment/index.ts`
- [ ] Deploy to Supabase
- [ ] Test: Send mock webhook payload
- [ ] Verify: Data written to tables

### **Phase 5: Edge Function 3** (1-2 hours)
- [ ] Create `create-clickup-tasks/index.ts`
- [ ] Deploy to Supabase
- [ ] Test: Insert test contact
- [ ] Verify: ClickUp task created

### **Phase 6: Integration Test** (1 hour)
- [ ] End-to-end test:
   1. UPDATE enrichment_status = 'pending'
   2. Wait 7 minutes
   3. Verify course updated
   4. Verify contacts inserted
   5. Verify ClickUp tasks created

---

## 🚨 **Error Handling Strategy**

### **Failure Points & Recovery:**

| Step | Failure Scenario | Detection | Recovery |
|------|------------------|-----------|----------|
| 1-2 | Slash command fails | Manual | Re-run slash command |
| 3 | Google API error | google_enriched=false | Re-run edge function |
| 4a | Trigger doesn't fire | Status stuck on 'pending' | Check DB trigger |
| 4b | Render API timeout | Status='processing' >15min | Set to 'error', manual retry |
| 4c | Agents fail mid-workflow | enrichment_error set | Review logs, fix, retry |
| 4d | Webhook fails | Status='processing' forever | Manual data entry OR retry |
| 5 | ClickUp API error | clickup_task_id NULL | Queue for retry |

### **Monitoring Queries:**

```sql
-- Stuck in processing (> 15 minutes)
SELECT * FROM golf_courses
WHERE enrichment_status = 'processing'
  AND enrichment_requested_at < NOW() - INTERVAL '15 minutes';

-- Recent errors
SELECT * FROM golf_courses
WHERE enrichment_status = 'error'
  AND enrichment_requested_at > NOW() - INTERVAL '24 hours'
ORDER BY enrichment_requested_at DESC;

-- Success rate (last 100)
SELECT
  enrichment_status,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '7 days'
GROUP BY enrichment_status;
```

---

## 💰 **Cost Tracking & Optimization**

### **Per-Course Cost Breakdown:**

```
Step 1: Map Regions          $0.00  (one-time)
Step 2: Find Courses         $0.02  (directory fetch)
Step 3: Google Places        $0.017 (Google API)
Step 4: Agent Enrichment     $0.19  (4 contacts, optimized)
Step 5: ClickUp Sync         $0.00  (free API)
────────────────────────────────────
TOTAL:                       $0.23  per course
```

### **Monthly Projection (500 courses):**

```
Step 2: 500 × $0.02 = $10
Step 3: 500 × $0.017 = $8.50
Step 4: 500 × $0.19 = $95
Infrastructure: $32 (Supabase + Render)
────────────────────────────────────
TOTAL: ~$145/month

vs Manual: $5,000/month
SAVINGS: $4,855/month (97% reduction!)
```

### **Optimization Targets:**

**Target: < $0.25/course**

**Quick Wins:**
1. ✅ Limit to 4 contacts (Save $0.10) → **$0.19/course**
2. ⏳ Optimize Agent 6 queries (Save $0.02) → **$0.17/course**
3. ⏳ Batch Google calls (Save $0.005) → **$0.165/course**

---

## 🧪 **Testing Strategy**

### **Manual Testing (Current):**

1. **Test Step 3 → Step 4 transition:**
   ```sql
   -- Pick a course that Google enriched
   SELECT * FROM golf_courses
   WHERE google_enriched = true
     AND enrichment_status IS NULL
   LIMIT 1;

   -- Trigger enrichment
   UPDATE golf_courses SET enrichment_status = 'pending' WHERE id = '...';

   -- Monitor
   SELECT enrichment_status FROM golf_courses WHERE id = '...';
   -- Should go: pending → processing → complete
   ```

2. **Test Step 4 → Step 5 transition:**
   ```sql
   -- After Step 4 completes, check contacts
   SELECT * FROM golf_course_contacts WHERE golf_course_id = '...';

   -- Check ClickUp
   -- Verify task created in correct folder
   ```

3. **Test error scenarios:**
   ```sql
   -- Trigger on invalid course
   UPDATE golf_courses
   SET enrichment_status = 'pending'
   WHERE course_name = 'Invalid Name Test';

   -- Should result in enrichment_status = 'error'
   ```

---

## 📚 **Documentation Files (This Plan Creates)**

1. **INTEGRATION_GUIDE.md** (This file) - Master integration doc
2. **teams/golf-enrichment/docs/EDGE_FUNCTIONS.md** - Function specs with code
3. **teams/golf-enrichment/docs/RELIABILITY_PLAYBOOK.md** - Operations guide
4. **teams/golf-enrichment/docs/COST_OPTIMIZATION.md** - Cost analysis

---

## 🚀 **Next Steps**

### **Immediate (Today):**
1. ✅ Create all 4 documentation files
2. ✅ Create migration file for schema additions
3. ✅ Update PROGRESS.md with integration plan

### **Near-Term (Next Session):**
1. Apply database migration
2. Build 3 edge functions
3. Update Render API for webhooks
4. Test manual Step 4 trigger
5. Verify Step 5 ClickUp integration

### **Future:**
1. Optimize agent costs (< $0.20/course)
2. Add batch processing option
3. Build monitoring dashboard
4. Scale to 500 courses/month

---

**Status:** Ready to create documentation! 📝