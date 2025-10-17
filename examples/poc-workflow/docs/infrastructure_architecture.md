# Infrastructure Architecture
**System:** Golf Course Outreach Automation
**Date:** 2025-01-17

---

## Full System Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│  USER INPUT                                                          │
│  Sales rep adds course to Supabase manually or via CSV import       │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│  SUPABASE (Phase 2)                                                  │
│                                                                      │
│  Table: courses                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ course_name: "Richmond Country Club"                       │   │
│  │ state: "Virginia"                                          │   │
│  │ status: "pending_enrichment"                               │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Database Trigger: ON INSERT → Call edge function                   │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│  SUPABASE EDGE FUNCTION: send_to_agent                               │
│                                                                      │
│  POST https://agent-api.railway.app/api/enrich-course               │
│  {                                                                   │
│    "course_name": "Richmond Country Club",                           │
│    "state": "Virginia",                                              │
│    "callback_url": "https://[...].supabase.co/.../receive"           │
│  }                                                                   │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│  DEPLOYED AGENT API (Phase 5)                                        │
│  Railway/Render server running orchestrator                          │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ ORCHESTRATOR (Phase 4)                                     │   │
│  │                                                            │   │
│  │  Agent 1: URL Finder                                       │   │
│  │    └→ https://vsga.org/courselisting/11950                 │   │
│  │                                                            │   │
│  │  Agent 2: Data Extractor                                   │   │
│  │    └→ {course: ..., staff: [3 contacts]}                   │   │
│  │                                                            │   │
│  │                                                            │   │
│  │  Agent 7: Water Hazard Counter (once per course)          │   │
│  │    └→ {water_hazard_count: 10, confidence: 'high'}        │   │
│  │                                                            │   │
│  │  For each contact:                                         │   │
│  │    Agent 3: Email + LinkedIn enrichment                    │   │
│  │    Agent 5: Phone number discovery                         │   │
│  │    Agent 6: Business intelligence (uses water count)       │   │
│  │                                                            │   │
│  │  Returns: Fully enriched contacts + course intel          │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Processing: ONE course at a time (triggered individually)           │
│  Time: ~50 seconds per course                                        │
│  Cost: ~$0.16 per course (includes Agent 7)                          │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│  WEBHOOK CALLBACK (Phase 6)                                          │
│                                                                      │
│  POST https://[...].supabase.co/functions/v1/receive-enrichment      │
│  {                                                                   │
│    "course": {course data},                                          │
│    "contacts": [                                                     │
│      {                                                               │
│        "name": "Stacy Foster",                                       │
│        "email": "sfoster@richmondcountryclubva.com",                 │
│        "phone": "804-592-5861",                                      │
│        "linkedin": "https://linkedin.com/in/stacy-foster-...",       │
│        "segment": "high-end",                                        │
│        "segment_confidence": 8,                                      │
│        "opportunities": {                                            │
│          "range_ball_buy": 8,                                        │
│          "range_ball_lease": 9,                                      │
│          ...                                                         │
│        },                                                            │
│        "conversation_starters": [...]                                │
│      }                                                               │
│    ]                                                                 │
│  }                                                                   │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│  SUPABASE EDGE FUNCTION: receive_enrichment                          │
│                                                                      │
│  1. UPDATE courses SET status = 'enriched', website = ...            │
│  2. INSERT INTO contacts (course_id, name, title, ...)               │
│  3. INSERT INTO contact_enrichment (contact_id, email, phone, ...)   │
│  4. INSERT INTO business_intelligence (contact_id, segment, ...)     │
│                                                                      │
│  Data now persisted in Supabase                                      │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│  SUPABASE EDGE FUNCTION: sync_to_clickup                             │
│                                                                      │
│  For each contact:                                                   │
│    1. Determine folder: High-End, Budget, or Both                    │
│    2. Create task in "New Leads" list                                │
│    3. Set custom fields:                                             │
│       - Segment, Confidence, Email, Phone, LinkedIn                  │
│       - Top 2 opportunities with scores                              │
│    4. Add conversation starters to description                       │
│    5. Assign to appropriate sales rep (if routing rules exist)       │
│                                                                      │
│  Uses: ClickUp MCP tools (mcp__clickup__create_task)                │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│  CLICKUP CRM (Phase 3)                                               │
│                                                                      │
│  Task: Stacy Foster - General Manager | Richmond Country Club       │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Folder: HIGH-END CLUBS                                     │   │
│  │ List: New Leads                                            │   │
│  │                                                            │   │
│  │ Custom Fields:                                             │   │
│  │   Segment: High-End (8/10)                                 │   │
│  │   Email: sfoster@richmondcountryclubva.com                 │   │
│  │   Phone: 804-592-5861                                      │   │
│  │   LinkedIn: https://...                                    │   │
│  │   Top Opp 1: range_ball_lease (9/10)                       │   │
│  │   Top Opp 2: range_ball_buy (8/10)                         │   │
│  │                                                            │   │
│  │ Description:                                               │   │
│  │   ## Pre-Written Conversation Starters                     │   │
│  │   1. [9/10] "I noticed Richmond Country Club..."           │   │
│  │   2. [8/10] "Many premium clubs are exploring..."          │   │
│  │   ...                                                      │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Sales rep now has full context ready for outreach                   │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│  OUTREACH FUNNEL (Phase 7 - FUTURE)                                 │
│                                                                      │
│  ClickUp Automation: Task moved to "Contacted" → Trigger Email 1     │
│                                                                      │
│  Email sent using:                                                   │
│  - Segment-specific template (High-End Track)                        │
│  - Personalized with conversation starters                           │
│  - Contact info from custom fields                                   │
│                                                                      │
│  3-email sequence runs automatically                                 │
│  Response tracking updates ClickUp task                              │
│  Sales rep notified when reply received                              │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│  AGENT 8: CONTACT FRESHNESS (Monthly - Future)                       │
│                                                                      │
│  Supabase Cron Job (1st of every month):                             │
│    SELECT contacts WHERE last_verified > 30 days                     │
│                                                                      │
│  For each contact:                                                   │
│    1. Check LinkedIn (did they change jobs?)                         │
│    2. Verify email (still deliverable?)                              │
│    3. If job change → Mark inactive, find replacement                │
│    4. Update Supabase (source of truth)                              │
│    5. Sync to ClickUp (archive old, create new if replacement)       │
│                                                                      │
│  Keeps database fresh automatically!                                 │
└──────────────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────────────────────────────────────────────────────────────┐
│  BI-DIRECTIONAL SYNC (Supabase ↔ ClickUp)                          │
│                                                                      │
│  Supabase → ClickUp (Automated):                                    │
│    Agents enrich → Supabase → Edge function → ClickUp tasks        │
│                                                                      │
│  ClickUp → Supabase (Manual Corrections):                           │
│    Sales rep updates ClickUp → Webhook → Supabase updated          │
│                                                                      │
│  Supabase = Source of Truth                                         │
│  ClickUp = Working Interface for Sales Team                         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Detail

### Step-by-Step

**1. Course Added to Supabase**
```sql
INSERT INTO courses (course_name, state, status)
VALUES ('Richmond Country Club', 'Virginia', 'pending_enrichment');
```

**2. Database Trigger Fires**
```sql
-- Trigger executes immediately on INSERT
CALL edge_function('send_to_agent', {
  course_id: NEW.id,
  course_name: NEW.course_name,
  state: NEW.state
});
```

**3. Edge Function Calls Agent API**
```javascript
// send_to_agent edge function
const response = await fetch('https://agent-api.railway.app/api/enrich-course', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-API-Key': process.env.AGENT_API_KEY },
  body: JSON.stringify({
    course_name: courseData.course_name,
    state: courseData.state,
    callback_url: `https://${SUPABASE_URL}/functions/v1/receive-enrichment`,
    course_id: courseData.id
  })
});
// Returns: { job_id: "uuid", status: "processing" }
```

**4. Agent Orchestrator Runs (ONE Course at a Time)**
```python
# Orchestrator executes all agents for THIS course
# Holds ALL data in memory, writes atomically at end

# Course-level enrichment
url_result = await agent1_find_url(course_name, state_code)
course_data = await agent2_extract(url_result.url)
water_data = await agent7_count_hazards(course_name, state_code)  # Once per course

# Contact-level enrichment
contacts = []
for staff in course_data.staff:
    enriched = await agent3_enrich(staff, course_data.website)
    enriched = await agent5_phone(enriched, state_code)
    enriched = await agent6_intel(enriched, course_data, water_data)  # Uses water count
    contacts.append(enriched)

# Atomic result (all or nothing)
result = {
  "course_id": request.course_id,
  "course": {**course_data, **water_data, "segment": contacts[0].segment},
  "contacts": contacts,
  "total_cost": sum_all_agent_costs(),
  "total_time": calculate_duration()
}

# Send webhook with complete data
requests.post(callback_url, json=result)
```

**5. Webhook Receiver Updates Supabase**
```javascript
// receive_enrichment edge function
const { course, contacts } = await request.json();

// Update course
await supabase.from('courses')
  .update({ status: 'enriched', website: course.website, ... })
  .eq('id', course.id);

// Insert contacts
for (const contact of contacts) {
  const { data: contactRow } = await supabase.from('contacts')
    .insert({ course_id: course.id, name: contact.name, title: contact.title })
    .select()
    .single();

  // Insert enrichment
  await supabase.from('contact_enrichment')
    .insert({
      contact_id: contactRow.id,
      email: contact.email,
      phone: contact.phone,
      linkedin_url: contact.linkedin_url,
      ...
    });

  // Insert business intel
  await supabase.from('business_intelligence')
    .insert({
      contact_id: contactRow.id,
      segment: contact.business_intel.segmentation.primary_target,
      ...
    });
}

// Trigger ClickUp sync
await callEdgeFunction('sync_to_clickup', { course_id: course.id });
```

**6. ClickUp Sync Creates Tasks**
```javascript
// sync_to_clickup edge function
const contacts = await supabase
  .from('contacts')
  .select('*, contact_enrichment(*), business_intelligence(*)')
  .eq('course_id', courseId);

for (const contact of contacts) {
  // Determine folder based on segment
  const folderId = contact.business_intelligence.segment === 'high-end'
    ? HIGH_END_FOLDER_ID
    : contact.business_intelligence.segment === 'budget'
    ? BUDGET_FOLDER_ID
    : BOTH_FOLDER_ID;

  // Create ClickUp task
  await clickup.createTask({
    folderId,
    listName: 'New Leads',
    name: `${contact.name} - ${contact.title} | ${contact.course.name}`,
    customFields: {
      segment: contact.business_intelligence.segment,
      confidence: contact.business_intelligence.segment_confidence,
      email: contact.contact_enrichment.email,
      ...
    },
    description: formatTaskDescription(contact)
  });
}
```

**7. Sales Rep Access in ClickUp**
- Opens "New Leads" list
- Sees task with full context
- Reviews conversation starters
- Clicks "Send Email" (future: triggers sequence)

---

## Technology Stack

### Data Collection Layer (Phase 1)
- **Language:** Python 3.11+
- **Framework:** Claude Agent SDK
- **Model:** Haiku 4.5 (most agents), Sonnet 4.5 (Agent 6)
- **APIs:** Hunter.io, Perplexity, Jina AI
- **Cost:** ~$0.15 per course

### Data Storage Layer (Phase 2)
- **Database:** Supabase (PostgreSQL)
- **ORM:** Supabase client (JavaScript/Python)
- **Migrations:** Supabase CLI
- **Cost:** $25/month (Pro plan)

### CRM Layer (Phase 3)
- **Platform:** ClickUp
- **Integration:** MCP tools (mcp__clickup__*)
- **Structure:** Spaces → Folders → Lists → Tasks
- **Cost:** $12/month per seat (Business plan)

### Orchestration Layer (Phase 4)
- **Runtime:** Python asyncio
- **Pattern:** Sequential with error handling
- **Logging:** Structured JSON logs
- **Monitoring:** TBD (Sentry, LogTail, or similar)

### Deployment Layer (Phase 5)
- **Platform:** Railway or Render
- **Container:** Docker
- **API Framework:** FastAPI or Flask
- **Authentication:** API key-based
- **Cost:** $5-10/month (sandbox)

### Automation Layer (Phase 6)
- **Triggers:** Supabase database triggers
- **Edge Functions:** Deno (Supabase runtime)
- **Webhooks:** HTTPS callbacks
- **Reliability:** Retry logic, dead letter queues

### Outreach Layer (Phase 7)
- **Email Service:** SendGrid or Mailgun
- **Sequences:** ClickUp automations or Zapier
- **Tracking:** Opens, clicks, replies
- **Cost:** $0.01-0.02 per email sent

---

## Security Architecture

### API Keys (Environment Variables)
- HUNTER_API_KEY (Agent 3)
- PERPLEXITY_API_KEY (Agent 5, 6)
- JINA_API_KEY (Agent 2, optional)
- SUPABASE_URL + SUPABASE_ANON_KEY
- CLICKUP_API_KEY
- AGENT_API_KEY (for Supabase → Agent auth)

**Storage:**
- Local: `.env` file (git-ignored)
- Production: Supabase secrets, Railway/Render env vars

### Data Security
- **Supabase RLS:** Row-level security on all tables
- **ClickUp:** Team-level access control
- **Agent API:** API key authentication
- **HTTPS:** All communication encrypted

---

## Scalability Considerations

### Current Scale (POC)
- **Throughput:** 10-50 courses/day
- **Concurrency:** 1-2 concurrent workflows
- **Cost:** $7.50-37.50/day

### Production Scale (Target)
- **Throughput:** 500 courses/day
- **Concurrency:** 10-20 concurrent workflows
- **Cost:** $75/day = $2,250/month (agents only)

### Bottlenecks

**Agent Processing Time:**
- Current: 45s per course (sequential)
- Optimization: Parallelize Agent 3/5/6 (per contact)
- Future: 20-25s per course

**API Rate Limits:**
- Hunter.io: 100 req/month free, 10K req/month paid
- Perplexity: 50 req/day free, unlimited paid
- ClickUp: 100 req/min (sufficient)

**Database:**
- Supabase: 500MB free, unlimited on Pro
- Writes/sec: Unlimited (PostgreSQL)

---

## Monitoring & Observability

### Metrics to Track

**Agent Performance:**
- Success rate per agent
- Average cost per agent
- Average time per agent
- Error rate and types

**Workflow Performance:**
- End-to-end success rate
- Total cost per course
- Total time per course
- Bottleneck identification

**Data Quality:**
- Email found rate (Agent 3)
- Phone found rate (Agent 5)
- Segmentation confidence distribution (Agent 6)
- Opportunity score distributions

**Business Metrics:**
- Leads generated per day
- Segmentation breakdown (high-end vs budget)
- Cost per qualified lead
- ClickUp task creation rate

### Logging Strategy

**Structured Logs (JSON):**
```json
{
  "timestamp": "2025-01-17T16:30:00Z",
  "level": "INFO",
  "agent": "agent6",
  "course_name": "Richmond Country Club",
  "contact_name": "Stacy Foster",
  "action": "segmentation_complete",
  "segment": "high-end",
  "confidence": 8,
  "cost": 0.033,
  "duration_ms": 18500
}
```

**Tools:**
- Local: Python logging module
- Production: Sentry (errors), LogTail (logs), or Datadog

---

## Error Handling Strategy

### Error Types

**1. Agent Failures (Retryable)**
- Network timeouts
- API rate limits
- Temporary service outages

**Action:** Retry with exponential backoff (3 attempts)

**2. Data Not Found (Expected)**
- Agent 1: Course URL not found
- Agent 3: Email not found (50% expected)
- Agent 5: Phone not found

**Action:** Log, continue with null values

**3. Critical Failures (Stop Workflow)**
- Agent 1 fails (can't proceed without URL)
- Agent 2 fails (can't get contacts)
- Invalid input data

**Action:** Return error, mark course as "failed", alert admin

**4. Infrastructure Failures (Escalate)**
- Supabase down
- ClickUp down
- Deployment server down

**Action:** Alert admin, queue for retry when service restored

---

## Deployment Architecture

### Development Environment
```
Local machine
└── Python virtual environment
    └── Claude Agent SDK
        └── Agents 1-6 (direct execution)
```

### Staging/Sandbox Environment
```
Railway/Render
└── Docker container
    └── FastAPI server
        └── Orchestrator API
            └── Agents 1-6 (subprocess execution)
```

### Production Environment (Future)
```
Cloud Run (serverless)
├── Auto-scaling (0-100 instances)
├── Regional deployment
└── Load balancing
    └── Orchestrator API
        └── Agents 1-6
```

---

## Dependencies

### Python Packages
- claude-agent-sdk
- httpx (async HTTP)
- anyio (async runtime)
- python-dotenv (env variables)
- supabase-py (database client)
- fastapi (API framework)

### External Services
- Supabase (database + edge functions)
- ClickUp (CRM)
- Hunter.io (email finding)
- Perplexity (research/phone)
- Railway/Render (hosting)
- SendGrid/Mailgun (email, Phase 7)

---

## Next Phase Gates

**Phase 1 → Phase 2:**
- ✅ All agents production ready
- ✅ Orchestrator complete
- ✅ End-to-end test passed (20+ courses)

**Phase 2 → Phase 3:**
- ✅ Schema designed and tested
- ✅ CRUD operations work
- ✅ Sample data loaded

**Phase 3 → Phase 4:**
- (Phase 4 is parallel to 2-3, not sequential)

**Phase 4 → Phase 5:**
- ✅ Orchestrator handles 50+ courses
- ✅ Error handling validated
- ✅ Performance acceptable

**Phase 5 → Phase 6:**
- ✅ API deployed and accessible
- ✅ Handles concurrent requests
- ✅ Monitoring configured

**Phase 6 → Phase 7:**
- ✅ Full automation works (trigger → ClickUp)
- ✅ 100+ courses processed successfully
- ✅ Sales team using ClickUp CRM
- ✅ Data quality validated

---

**Last Updated:** 2025-01-17
**Current Focus:** Phase 4 (Orchestrator)
