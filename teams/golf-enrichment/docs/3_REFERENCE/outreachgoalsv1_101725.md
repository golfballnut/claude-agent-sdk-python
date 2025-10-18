# Master Roadmap: Golf Course Outreach Automation System
**Version:** 1.0
**Date:** October 17, 2025
**Status:** Phase 1 (80% Complete)

---

## Mission

Build a fully automated golf course business intelligence and outreach system that:
1. Discovers golf courses
2. Extracts contact data
3. Enriches with email/phone/LinkedIn
4. Gathers business intelligence (segmentation + opportunities)
5. Stores in Supabase database
6. Syncs to ClickUp CRM
7. Triggers personalized outreach sequences
8. Tracks engagement and conversions

**End Result:** Sales team receives qualified, segmented leads with pre-written conversation starters in ClickUp CRM, ready for personalized outreach.

---

## Business Context

### The Business: Range Ball Reconditioning & Golf Ball Retrieval

**Core Service:** Golf ball retrieval (pond/water hazard recovery)

**Innovation:** Used range ball reconditioning
- **Unique Value:** ONLY company worldwide that can clean + add protective coating to used range balls
- **Technology:** Clean balls <50% worn + apply protective coating
- **Market Gap:** High-end clubs discard used balls, budget clubs need affordable alternatives

**Revenue Streams:**
1. **Buy Program (High-End):** Purchase used range balls from premium clubs
2. **Sell Program (Budget):** Sell reconditioned balls at 40-60% discount
3. **Lease Program (All):** 6-month swap cycle (always fresh inventory)
4. **Core Service:** Golf ball retrieval contracts

**Future Opportunities:**
5. Pro shop e-commerce platform
6. Superintendent found ball buyback
7. Tournament ball programs
8. Youth program support (CSR)
9. Sustainability partnerships
10. Equipment leasing

---

## System Architecture (7 Phases)

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: DATA COLLECTION (Agents 1-6)                          │
│   Input: Course name → Output: Enriched contacts + intel       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: DATA STORAGE (Supabase)                               │
│   Schema: courses, contacts, enrichment, business_intel        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: CRM INTEGRATION (ClickUp)                             │
│   Sync: Supabase → ClickUp tasks (segmented folders)           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 4: ORCHESTRATOR (Workflow Coordination)                  │
│   Flow: Agent 1 → 2 → 3 → 5 → 6 (seamless handoffs)           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 5: DEPLOYMENT (Sandbox Server)                           │
│   API: POST /enrich-course → Returns enriched data             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 6: AUTOMATION PIPELINE (End-to-End)                      │
│   Trigger → Agent → Webhook → Supabase → ClickUp              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 7: OUTREACH FUNNEL (ClickUp-Controlled Sequences)        │
│   3 Tracks: High-End, Budget, Both (personalized emails)       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Data Collection Infrastructure ✅ 80% COMPLETE

**Goal:** Build intelligent agents that gather complete contact + business data

### Agents Built

#### Agent 1: URL Finder ✅ PRODUCTION READY
- **Input:** Course name
- **Output:** https://vsga.org/courselisting/[ID]
- **Performance:** 100% success, $0.015/course, 3.4s
- **File:** `agents/agent1_url_finder.py`

#### Agent 2: Data Extractor ✅ PRODUCTION READY
- **Input:** URL from Agent 1
- **Output:** Course data (name, phone, website, staff list)
- **Performance:** 100% success, $0.012/course, 8.5s
- **File:** `agents/agent2_data_extractor.py`

#### Agent 3: Contact Enricher ✅ PRODUCTION READY
- **Input:** Contacts from Agent 2
- **Output:** Email (50% success) + LinkedIn (25% bonus)
- **Performance:** $0.012/contact, 95-98% confidence when found
- **File:** `agents/agent3_contact_enricher.py`
- **Discovery:** Hunter.io returns LinkedIn URLs (Agent 4 cancelled!)

#### Agent 5: Phone Finder ⚠️ BUILT, NOT TESTED IN WORKFLOW
- **Input:** Contacts from Agent 3
- **Output:** Phone numbers via Perplexity AI
- **Expected:** 100% API success, $0.003-0.005/contact
- **File:** `agents/agent5_phone_finder.py`
- **Status:** Needs integration testing in full workflow

#### Agent 6: Business Intelligence ✅ PRODUCTION READY
- **Input:** Contacts + course context
- **Output:** Segment (high-end/budget/both) + 6 opportunity scores + 7 conversation starters
- **Performance:** 100% success, $0.033/contact, 20s
- **File:** `agents/agent6_context_enrichment.py`
- **Breakthrough:** Direct Perplexity API = 100% reliability

#### Agent 7: Water Hazard Counter ✅ VALIDATED (60% Text Success)
- **Input:** Course name + state
- **Output:** Water hazard count + confidence + details
- **Performance:** 60% text success, hybrid approach planned (text + visual fallback = ~90%)
- **File:** `tests/test_water_hazard_detection.py` (test complete)
- **Next:** Build agent7_water_hazard_counter.py
- **Business Value:** Enhances ball_retrieval opportunity scoring (Riverfront: 15 hazards = premium opportunity!)

#### Agent 8: Contact Freshness Validator 📋 DESIGNED (Phase 8 - Future)
- **Purpose:** Monthly validation - detect job changes, verify emails, find replacements
- **Trigger:** Supabase cron job (monthly)
- **Process:** LinkedIn check → Email verify → Mark inactive → Find replacement
- **File:** `docs/data_freshness_strategy.md` (design complete)
- **Status:** Build after Phases 1-7 complete

### Phase 1 Remaining Work

**🔄 Build Orchestrator**
- Coordinate Agent 1 → 2 → 3 → 5 → 6 flow
- Error handling (fail fast vs continue with partial data)
- Result aggregation
- Cost tracking

**📊 End-to-End Testing**
- Test full workflow on 20-50 courses
- Validate data quality at each step
- Measure total cost per course
- Identify bottlenecks

**Estimated Time:** 1-2 days

---

## Phase 2: Data Storage (Supabase) 📋 PLANNED

**Goal:** Persist all gathered data for CRM sync and analysis

### Database Schema

#### Table: `courses`
```sql
id              UUID PRIMARY KEY
course_name     TEXT NOT NULL
url             TEXT
website         TEXT
phone           TEXT
created_at      TIMESTAMP
updated_at      TIMESTAMP
_agent1_cost    DECIMAL
_agent2_cost    DECIMAL
```

#### Table: `contacts`
```sql
id              UUID PRIMARY KEY
course_id       UUID REFERENCES courses(id)
name            TEXT NOT NULL
title           TEXT
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

#### Table: `contact_enrichment`
```sql
id                  UUID PRIMARY KEY
contact_id          UUID REFERENCES contacts(id)
email               TEXT
email_confidence    INT
email_method        TEXT
linkedin_url        TEXT
linkedin_method     TEXT
phone               TEXT
phone_confidence    INT
phone_method        TEXT
_agent3_cost        DECIMAL
_agent5_cost        DECIMAL
created_at          TIMESTAMP
```

#### Table: `business_intelligence`
```sql
id                      UUID PRIMARY KEY
contact_id              UUID REFERENCES contacts(id)
segment                 TEXT (high-end|budget|both)
segment_confidence      INT
segment_signals         JSONB
has_range               BOOLEAN
range_intel             JSONB
opportunity_scores      JSONB
conversation_starters   JSONB
_agent6_cost            DECIMAL
created_at              TIMESTAMP
```

#### Table: `outreach_history` (Phase 7)
```sql
id              UUID PRIMARY KEY
contact_id      UUID REFERENCES contacts(id)
email_sent_at   TIMESTAMP
email_subject   TEXT
email_body      TEXT
opened_at       TIMESTAMP
replied_at      TIMESTAMP
status          TEXT
track_type      TEXT (high-end|budget|both)
```

### Phase 2 Tasks

1. Create Supabase project (or use existing)
2. Design schema (above tables)
3. Create migrations
4. Test CRUD operations
5. Set up RLS policies (security)
6. Create indexes for performance

**Estimated Time:** 1-2 days

---

## Phase 3: CRM Integration (ClickUp) 📋 PLANNED

**Goal:** Sync enriched contacts to ClickUp for sales team management

### ClickUp Workspace Structure

```
Space: Golf Course Outreach
├── Folder: HIGH-END CLUBS (Buy + Lease targets)
│   ├── List: New Leads
│   ├── List: Contacted
│   ├── List: Qualified
│   ├── List: Negotiating
│   └── List: Closed Won
├── Folder: BUDGET CLUBS (Sell + Lease targets)
│   ├── List: New Leads
│   ├── List: Contacted
│   ├── List: Qualified
│   ├── List: Negotiating
│   └── List: Closed Won
└── Folder: BOTH (Mixed signals)
    ├── List: New Leads
    ├── List: Contacted
    ├── List: Qualified
    ├── List: Negotiating
    └── List: Closed Won
```

### Task Structure (Per Contact)

**Task Name:** `{Name} - {Title} | {Company}`

**Custom Fields:**
- **Segment:** Dropdown (High-End, Budget, Both)
- **Confidence:** Number (1-10)
- **Email:** Text
- **Phone:** Text
- **LinkedIn:** URL
- **Top Opportunity 1:** Dropdown (6 opportunity types)
- **Opp 1 Score:** Number (1-10)
- **Top Opportunity 2:** Dropdown
- **Opp 2 Score:** Number (1-10)
- **Conversation Starters:** Long Text (formatted list)
- **Company Website:** URL
- **Course Phone:** Text

**Task Description:**
```markdown
## Contact Info
- Email: {email}
- Phone: {phone}
- LinkedIn: {linkedin_url}
- Company: {company} ({website})

## Business Intelligence
- **Segment:** {segment} ({confidence}/10 confidence)
- **Signals:** {signals}

## Top Opportunities
1. {opportunity_1}: {score}/10
2. {opportunity_2}: {score}/10

## Pre-Written Conversation Starters
1. [9/10] {starter_1}
2. [8/10] {starter_2}
3. [8/10] {starter_3}
...

## Range Intel
- Has Range: {yes/no}
- Volume Signals: {signals}
- Quality Complaints: {complaints}
- Budget Signals: {budget_signals}
```

### Phase 3 Tasks

1. Test ClickUp MCP tools (create_task, update_task, etc.)
2. Create ClickUp workspace structure
3. Configure custom fields
4. Build task creation function (Supabase → ClickUp)
5. Test sync with sample data

**Estimated Time:** 1 day

---

## Phase 4: Orchestrator Agent 🔄 IN PROGRESS

**Goal:** Coordinate all sub-agents into seamless workflow

### Orchestrator Design

**Input:**
```json
{
  "course_name": "Richmond Country Club",
  "state": "Virginia"  // optional
}
```

**Workflow:**
```python
async def orchestrate(course_name, state="Virginia"):
    # Step 1: Find URL (state-aware)
    url_result = await agent1_find_url(course_name, state)
    if not url_result.get("url"):
        return {"error": "Course not found"}

    # Step 2: Extract data
    course_data = await agent2_extract_data(url_result["url"])
    if not course_data.get("staff"):
        return {"error": "No contacts found"}

    # Step 3: Water hazard count (ONCE per course)
    water_data = await agent7_count_hazards(course_name, state)

    # Step 4-7: Enrich each contact
    enriched_contacts = []
    for contact in course_data["staff"]:
        # Agent 3: Email + LinkedIn
        contact = await agent3_enrich(contact, course_data["website"])

        # Agent 5: Phone
        contact = await agent5_find_phone(contact, state)

        # Agent 6: Business Intel (uses water_data for retrieval scoring!)
        contact = await agent6_business_intel(contact, course_data, water_data)

        enriched_contacts.append(contact)

    # Atomic return (all data held in memory, written once)
    return {
        "course": {**course_data, **water_data, "segment": enriched_contacts[0].segment},
        "contacts": enriched_contacts,
        "total_cost": calculate_total_cost(),
        "total_time": calculate_total_time()
    }
```

**Error Handling:**
- **Critical failures** (Agent 1-2): Stop workflow, return error
- **Partial failures** (Agent 3-6): Continue, flag missing data
- **Cost tracking:** Aggregate costs from all agents
- **Logging:** Track each step for debugging

### Phase 4 Tasks

1. Create `agents/orchestrator.py`
2. Implement sequential workflow
3. Add error handling
4. Add cost tracking
5. Test on 10-20 courses end-to-end
6. Measure performance (time, cost, success rate)

**Estimated Time:** 1 day

---

## Phase 5: Deployment (Sandbox Server) 📋 PLANNED

**Goal:** Deploy orchestrator as REST API for external triggers

### Platform Options

**Recommended:** Railway or Render
- Pros: Simple deploy, databases included, reasonable pricing
- Cons: None for POC scale

**Alternatives:**
- Cloud Run (serverless, scales to zero)
- Fly.io (edge deployment)

### API Design

**Endpoint:** `POST /api/enrich-course`

**Request:**
```json
{
  "course_name": "Richmond Country Club",
  "state": "Virginia",
  "callback_url": "https://your-supabase-project.supabase.co/functions/v1/webhook-receiver"
}
```

**Response (Async):**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "estimated_time_seconds": 45
}
```

**Webhook Callback (When Complete):**
```json
{
  "job_id": "uuid",
  "status": "complete",
  "course": {...},
  "contacts": [
    {
      "name": "Stacy Foster",
      "email": "sfoster@...",
      "segment": "high-end",
      "opportunities": {...},
      "conversation_starters": [...]
    }
  ],
  "total_cost": 0.15,
  "total_time_seconds": 42
}
```

### Phase 5 Tasks

1. Containerize orchestrator (Docker)
2. Choose deployment platform
3. Deploy to sandbox
4. Test API endpoint
5. Configure environment variables (API keys)
6. Set up monitoring/logging

**Estimated Time:** 0.5 days

---

## Phase 6: Automation Pipeline 📋 PLANNED

**Goal:** Full automation from Supabase trigger to ClickUp task creation

### End-to-End Flow

**Trigger:** New course added to `courses` table in Supabase

**Flow:**
```
1. Sales rep adds course to Supabase (manual or CSV import)
   INSERT INTO courses (course_name, state) VALUES ('Richmond CC', 'VA')
   ↓
2. Supabase database trigger fires
   ON INSERT INTO courses → Call edge function
   ↓
3. Edge Function: send_to_agent
   POST https://agent-api.railway.app/api/enrich-course
   {
     "course_name": "Richmond CC",
     "state": "VA",
     "callback_url": "https://[project].supabase.co/functions/v1/receive-enrichment"
   }
   ↓
4. Agent API processes (Agents 1 → 2 → 3 → 5 → 6)
   45 seconds later...
   ↓
5. Agent sends webhook callback
   POST https://[project].supabase.co/functions/v1/receive-enrichment
   { ... enriched contacts data ... }
   ↓
6. Edge Function: receive_enrichment
   a. Parse webhook data
   b. Update courses table
   c. Insert into contacts table
   d. Insert into contact_enrichment table
   e. Insert into business_intelligence table
   ↓
7. Edge Function: sync_to_clickup
   For each contact:
   a. Determine folder (High-End/Budget/Both)
   b. Create task in "New Leads" list
   c. Set custom fields
   d. Add conversation starters to description
   ↓
8. ClickUp CRM now has qualified leads ready for outreach
```

### Supabase Components

**Database Triggers:**
```sql
CREATE TRIGGER on_course_insert
AFTER INSERT ON courses
FOR EACH ROW
EXECUTE FUNCTION trigger_enrichment();
```

**Edge Functions:**
1. `send_to_agent` - Calls deployed agent API
2. `receive_enrichment` - Receives webhook, updates DB
3. `sync_to_clickup` - Creates ClickUp tasks from DB records

### Phase 6 Tasks

1. Create Supabase edge functions (3 functions)
2. Set up database triggers
3. Test trigger → agent → webhook → DB flow
4. Test DB → ClickUp sync
5. End-to-end test (manual course insert → ClickUp task appears)
6. Error handling and retry logic

**Estimated Time:** 2 days

---

## Phase 7: Outreach Funnel (ClickUp-Controlled) 📋 FUTURE

**Goal:** Automated, personalized outreach sequences triggered by ClickUp

**See:** `outreach_funnel_goals.md` for full details

**High-Level:**
- 3 tracks based on segment (High-End, Budget, Both)
- 3-email sequences per track
- Value-prop specific messaging
- Response tracking
- A/B testing framework

**Trigger:** ClickUp task status change (New Leads → Contacted)
**Action:** Send Email 1 (personalized with conversation starters)

**Status:** Build after Phase 6 complete

**Estimated Time:** 1-2 days

---

## Current Progress Summary

| Phase | Status | Progress | Blocking Issues |
|-------|--------|----------|----------------|
| 1. Data Collection | ✅ 85% | Agents 1-3,6,7 done, Agent 5 built | Need orchestrator |
| 2. Supabase | ✅ 20% | Existing tables + migration ready | Need to apply migration |
| 3. ClickUp | ✅ 30% | Existing structure mapped | Need custom fields added |
| 4. Orchestrator | 🔄 In Progress | 10% | Design complete, build next |
| 5. Deployment | 📋 Planned | 0% | Need orchestrator first |
| 6. Automation | 📋 Planned | 0% | Need deployment first |
| 7. Outreach | 📋 Future | 0% | Need automation first |
| 8. Data Freshness | 📋 Designed | 5% | Agent 8 design complete |

**Overall Progress:** ~20% complete (was 15%)

---

## Cost Projections

### Per Course (with avg 2.4 contacts)

| Component | Cost | Notes |
|-----------|------|-------|
| Agent 1 | $0.015 | URL finding (multi-state planned) |
| Agent 2 | $0.012 | Data extraction |
| Agent 7 | $0.006 | Water hazards (once per course) |
| Agent 3 | $0.029 | Email/LinkedIn (2.4 contacts @ $0.012 each) |
| Agent 5 | $0.012 | Phone (2.4 contacts @ $0.005 each) |
| Agent 6 | $0.079 | Business intel (2.4 contacts @ $0.033 each) |
| **Total** | **$0.153** | **Per course, fully enriched** |

### Monthly Scale (500 courses)

| Item | Cost |
|------|------|
| 500 courses @ $0.153 | $76.50/month |
| Agent 8 (monthly freshness, 400 contacts) | $18/month |
| Supabase (Pro plan) | $25/month |
| Railway/Render | $5-10/month |
| ClickUp (Business) | $12/month per seat |
| **Total** | **~$136-151/month** |

**ROI:**
- Manual research: 30 min/course × $20/hr = $10/course
- 500 courses/month manual = $5,000/month
- Automated: $136-151/month
- **Savings: $4,849-4,864/month (97% cost reduction)**

**Plus Data Freshness:**
- Manual contact validation: 15 min/contact × $20/hr = $5/contact
- 400 contacts/month = $2,000/month
- Agent 8: $18/month
- **Additional Savings: $1,982/month**

---

## Success Criteria (Per Phase)

### Phase 1 (Data Collection)
- ✅ All agents 100% functional
- ✅ Cost < $0.20 per course
- ✅ Orchestrator coordinates smoothly
- ✅ End-to-end test: 80%+ success rate

### Phase 2 (Supabase)
- ✅ Schema supports all data types
- ✅ CRUD operations work
- ✅ RLS policies secure data
- ✅ Indexes for performance

### Phase 3 (ClickUp)
- ✅ Tasks created in correct folders
- ✅ Custom fields populated
- ✅ Sales team can use immediately
- ✅ Sync < 5s per contact

### Phase 4 (Orchestrator)
- ✅ Handles 20-50 courses successfully
- ✅ Error handling works
- ✅ Cost tracking accurate
- ✅ Logs useful for debugging

### Phase 5 (Deployment)
- ✅ API responds < 60s
- ✅ Handles 10+ concurrent requests
- ✅ Monitoring/alerting configured
- ✅ Environment variables secure

### Phase 6 (Automation)
- ✅ Trigger → webhook flow works
- ✅ DB updates correctly
- ✅ ClickUp sync automatic
- ✅ Error recovery/retry working

### Phase 7 (Outreach)
- ✅ Emails send automatically
- ✅ Response rate > 10% (vs 2-5% industry avg)
- ✅ Conversation starters drive replies
- ✅ A/B testing framework functional

---

## Risk Mitigation

### Technical Risks

**Risk:** Agent reliability drops under load
- **Mitigation:** Test at 2x expected scale, implement retry logic

**Risk:** API keys rate limited
- **Mitigation:** Implement request queuing, monitor rate limits

**Risk:** ClickUp/Supabase integration breaks
- **Mitigation:** Extensive error handling, fallback to manual sync

**Risk:** Costs exceed projections
- **Mitigation:** Per-phase cost validation, kill switches

### Business Risks

**Risk:** Segmentation accuracy poor in production
- **Mitigation:** Human review of first 50 cases, refine logic

**Risk:** Conversation starters don't drive responses
- **Mitigation:** A/B test different approaches, iterate

**Risk:** Data quality degrades over time
- **Mitigation:** Weekly quality audits, agent performance monitoring

---

## Timeline (Realistic)

| Week | Focus | Deliverables |
|------|-------|--------------|
| Week 1 (Current) | Phase 1 + 4 | Orchestrator, end-to-end tests |
| Week 2 | Phase 2 + 3 | Supabase schema, ClickUp integration |
| Week 3 | Phase 5 + 6 | Deployment, automation pipeline |
| Week 4 | Phase 6 (cont) | Testing, debugging, refinement |
| Week 5+ | Phase 7 | Outreach funnel (if ready) |

**To Production:** 4-5 weeks

---

## Immediate Next Steps (This Session)

1. ✅ Create master planning documents (this file + 5 others)
2. ✅ Document Agent 6 success (100% segmentation!)
3. 📋 Decide: Keep Agent 6 monolithic or split to micro-agents?
4. 📋 Build orchestrator (Phase 4)
5. 📋 Test end-to-end workflow

---

## References

- **Phase Details:** See individual phase sections above
- **Outreach Funnel:** See `outreach_funnel_goals.md`
- **Agent Skills:** See `docs/agent_skills_research.md`
- **Architecture:** See `docs/infrastructure_architecture.md`
- **Checklists:** See `docs/phase_checklists.md`

---

**Last Updated:** 2025-01-17
**Current Phase:** Phase 1 (80%) + Phase 4 (0%)
**Next Milestone:** Orchestrator complete + end-to-end test