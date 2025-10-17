# Phase Validation Checklists
**Purpose:** Clear validation criteria for each phase before proceeding to next

---

## Phase 1: Data Collection Infrastructure ✅ 80% COMPLETE

### Agent 1: URL Finder ✅
- [x] Finds correct URL for course name
- [x] Cost < $0.02 per search
- [x] Speed < 5 seconds
- [x] 100% accuracy on test cases
- [x] Handles "not found" gracefully

### Agent 2: Data Extractor ✅
- [x] Extracts course name, website, phone
- [x] Extracts all staff (name + title)
- [x] Cost < $0.02 per extraction
- [x] Speed < 10 seconds
- [x] 100% accuracy on test cases

### Agent 3: Contact Enricher ✅
- [x] Finds emails (50%+ success rate)
- [x] Finds LinkedIn (25%+ bonus)
- [x] Cost < $0.02 per contact
- [x] 95%+ confidence when found
- [x] Returns clean nulls (no guessing)

### Agent 5: Phone Finder ⚠️
- [x] Built and functional
- [ ] Tested in full workflow
- [ ] Success rate measured
- [ ] Cost validated
- [ ] Integrated with orchestrator

### Agent 6: Business Intelligence ✅
- [x] Segments correctly (high-end vs budget)
- [x] Scores 6 opportunity types
- [x] Generates 5-7 conversation starters
- [x] Cost < $0.05 per contact
- [x] 100% success rate (direct API)

### Orchestrator ⚠️
- [ ] Coordinates Agent 1 → 2 → 3 → 5 → 6
- [ ] Handles errors gracefully
- [ ] Tracks total cost
- [ ] Tested on 20+ courses
- [ ] Success rate 80%+

**GATE TO PHASE 2:** All checkboxes above must be checked

---

## Phase 2: Data Storage (Supabase) 📋 PLANNED

### Schema Design
- [ ] courses table designed
- [ ] contacts table designed
- [ ] contact_enrichment table designed
- [ ] business_intelligence table designed
- [ ] outreach_history table designed (Phase 7)
- [ ] Relationships (foreign keys) defined
- [ ] Indexes for performance identified

### Implementation
- [ ] Supabase project created
- [ ] Migrations written
- [ ] Migrations applied
- [ ] Sample data inserted
- [ ] CRUD operations tested
- [ ] RLS policies configured

### Validation
- [ ] Can insert course data
- [ ] Can insert contacts (with FK to course)
- [ ] Can insert enrichment (with FK to contact)
- [ ] Can query full contact with all joins
- [ ] Performance acceptable (<100ms queries)
- [ ] Security: RLS prevents unauthorized access

**GATE TO PHASE 3:** All checkboxes above must be checked

---

## Phase 3: CRM Integration (ClickUp) 📋 PLANNED

### Workspace Setup
- [ ] Space created: "Golf Course Outreach"
- [ ] Folder created: "HIGH-END CLUBS"
- [ ] Folder created: "BUDGET CLUBS"
- [ ] Folder created: "BOTH"
- [ ] Lists created in each folder (New Leads, Contacted, etc.)
- [ ] Custom fields configured (Segment, Email, Phone, etc.)

### Integration Testing
- [ ] ClickUp MCP tools tested (create_task, update_task)
- [ ] Can create task with custom fields
- [ ] Can query tasks by folder
- [ ] Can update task status
- [ ] Can add comments/attachments

### Sync Logic
- [ ] Function to map segment → folder ID
- [ ] Function to create task from contact data
- [ ] Function to format conversation starters in description
- [ ] Batch sync tested (10+ contacts)
- [ ] Idempotency (don't create duplicates)

### Validation
- [ ] Manual test: Create 5 contacts → ClickUp tasks appear
- [ ] Correct folders (high-end in HIGH-END folder, etc.)
- [ ] Custom fields populated accurately
- [ ] Conversation starters formatted correctly
- [ ] Sales team can use tasks immediately

**GATE TO PHASE 5:** All checkboxes above must be checked (Phase 4 parallel)

---

## Phase 4: Orchestrator Agent 📋 IN PROGRESS

### Core Functionality
- [ ] Sequential execution (Agent 1 → 2 → 3 → 5 → 6)
- [ ] Error handling (fail fast vs continue partial)
- [ ] Cost tracking (aggregate from all agents)
- [ ] Time tracking (total workflow duration)
- [ ] Result aggregation (combine all agent outputs)

### Error Handling
- [ ] Agent 1 fails → Stop, return error
- [ ] Agent 2 fails → Stop, return error
- [ ] Agent 3 partial → Continue, flag missing email
- [ ] Agent 5 partial → Continue, flag missing phone
- [ ] Agent 6 partial → Continue, flag missing intel
- [ ] Network errors → Retry with backoff (3 attempts)

### Testing
- [ ] Test on 10 courses (various sizes)
- [ ] Test on 20 courses (measure performance)
- [ ] Test error scenarios (API down, bad data, etc.)
- [ ] Measure success rate (80%+ target)
- [ ] Measure average cost ($0.15 target)
- [ ] Measure average time (45s target)

### Validation
- [ ] Can process single course end-to-end
- [ ] Can process batch of 10 courses
- [ ] Handles all error types correctly
- [ ] Cost tracking accurate
- [ ] Logs useful for debugging

**GATE TO PHASE 5:** All checkboxes above must be checked

---

## Phase 5: Deployment (Sandbox Server) 📋 PLANNED

### Containerization
- [ ] Dockerfile created
- [ ] Dependencies listed (requirements.txt)
- [ ] Environment variables documented
- [ ] Build succeeds locally
- [ ] Container runs orchestrator correctly

### Platform Selection
- [ ] Railway OR Render chosen
- [ ] Account created
- [ ] Pricing confirmed
- [ ] Deploy region selected

### API Implementation
- [ ] FastAPI/Flask server created
- [ ] POST /api/enrich-course endpoint
- [ ] Authentication (API key) implemented
- [ ] Webhook callback implemented
- [ ] Health check endpoint (/health)
- [ ] Docs endpoint (/docs)

### Deployment
- [ ] Code deployed to sandbox
- [ ] Environment variables configured
- [ ] API accessible via HTTPS
- [ ] Test request succeeds
- [ ] Webhook callback works
- [ ] Logs visible in platform

### Validation
- [ ] Can call API from Postman/curl
- [ ] Returns correct response format
- [ ] Webhook sends to callback URL
- [ ] Handles concurrent requests (3-5 simultaneous)
- [ ] Monitoring/logs accessible

**GATE TO PHASE 6:** All checkboxes above must be checked

---

## Phase 6: Automation Pipeline 📋 PLANNED

### Supabase Triggers
- [ ] Database trigger created (ON INSERT courses)
- [ ] Trigger calls edge function correctly
- [ ] Edge function receives course data
- [ ] Manual insert → trigger fires

### Edge Function: send_to_agent
- [ ] Created and deployed
- [ ] Calls agent API with correct payload
- [ ] Includes callback URL
- [ ] Handles agent API errors
- [ ] Retry logic (if agent API down)

### Edge Function: receive_enrichment
- [ ] Created and deployed
- [ ] Receives webhook from agent
- [ ] Parses enriched data correctly
- [ ] Updates courses table
- [ ] Inserts into contacts table
- [ ] Inserts into contact_enrichment table
- [ ] Inserts into business_intelligence table
- [ ] Handles partial data (missing fields)

### Edge Function: sync_to_clickup
- [ ] Created and deployed
- [ ] Determines correct folder per segment
- [ ] Creates ClickUp tasks
- [ ] Sets all custom fields
- [ ] Formats description with conversation starters
- [ ] Handles ClickUp API errors

### End-to-End Testing
- [ ] Manual: Insert course → ClickUp task appears
- [ ] Automatic: 10 courses → 24 ClickUp tasks (avg 2.4 contacts)
- [ ] Error handling: Failed agent → course marked failed
- [ ] Error handling: Retry logic works
- [ ] Performance: < 60s from insert to ClickUp task

### Validation
- [ ] Sales team can see tasks in ClickUp
- [ ] All data accurate (email, phone, segment, etc.)
- [ ] Conversation starters usable immediately
- [ ] No duplicate tasks created
- [ ] System recovers from failures

**GATE TO PHASE 7:** All checkboxes above must be checked

---

## Phase 7: Outreach Funnel 📋 FUTURE

### Email Service Setup
- [ ] SendGrid/Mailgun account created
- [ ] API key configured
- [ ] Email templates created (9 templates)
- [ ] Tracking webhooks configured (opens, clicks, replies)
- [ ] Test emails send successfully

### ClickUp Automations
- [ ] Automation: New Lead → Send Email 1
- [ ] Automation: Email 1 + 3 days → Send Email 2
- [ ] Automation: Email 2 + 4 days → Send Email 3
- [ ] Automation: Reply received → Pause sequence
- [ ] Automation: Meeting booked → Move to Qualified

### Personalization Logic
- [ ] Templates pull custom fields (segment, opportunities)
- [ ] Conversation starters inserted dynamically
- [ ] Company-specific intel used
- [ ] Fallbacks for missing data

### Tracking & Reporting
- [ ] Open rate tracked per email
- [ ] Reply rate tracked per email
- [ ] Response time measured
- [ ] Dashboard shows funnel metrics
- [ ] Can see performance by segment

### Validation
- [ ] Test sequence on 10 contacts (don't send to real people)
- [ ] Emails personalized correctly
- [ ] Timing works (3 days, 7 days)
- [ ] Replies detected and sequence stops
- [ ] Sales team gets notifications

**GATE TO PRODUCTION:** All checkboxes above must be checked

---

## Production Readiness Checklist (All Phases)

### Technical
- [ ] All agents 95%+ success rate
- [ ] Average cost < $0.20 per course
- [ ] Average time < 60 seconds per course
- [ ] Can handle 100+ courses/day
- [ ] Error rate < 5%
- [ ] Monitoring and alerting configured

### Data Quality
- [ ] Email found rate 50%+
- [ ] Phone found rate 80%+
- [ ] Segmentation accuracy validated (manual review 50 cases)
- [ ] Opportunity scores make sense (manual review)
- [ ] Conversation starters are usable

### Business
- [ ] Sales team trained on ClickUp CRM
- [ ] Outreach sequences tested (10-20 real contacts)
- [ ] Reply rate > 8% (better than industry avg)
- [ ] First customer from system (validation)
- [ ] ROI positive (cost < manual research)

### Compliance
- [ ] GDPR/privacy considerations documented
- [ ] Email unsubscribe mechanism
- [ ] Data retention policy
- [ ] Security audit complete
- [ ] Legal review (if needed)

---

**Use these checklists to validate each phase before proceeding.**

**Don't skip steps - technical debt compounds fast.**

---

**Last Updated:** 2025-01-17
