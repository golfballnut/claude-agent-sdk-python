# ClickUp Architecture - Golf Course Outreach System

**Last Updated:** October 18, 2024
**Purpose:** Complete specification for 3-list ClickUp structure
**Design Principle:** "Outreach Task = Command Center" - Sales team never leaves the outreach task

---

## 🏗️ **System Overview**

### **Three Lists (Existing Structure):**

```
Links Choice Space (90140666423)
└── Golf Course Outreach (90147098214)
    ├── 📊 Reference Data (90147173715)
    │   ├── 🏌️ Golf Courses (901413061864)      ← FACILITY intelligence
    │   └── 📇 Contacts (901413061863)            ← PERSON information
    └── 🎯 Active Outreach (90147173733)
        └── 📞 Outreach Activities (901413111587)  ← WORKING tasks ⭐
```

### **Design Philosophy:**

**🏌️ Golf Courses** = Reference (rarely opened)
- Course-level business intelligence
- Facility data (range, hazards, etc.)
- Opportunity scores
- Linked from outreach tasks

**📇 Contacts** = Reference (rarely opened)
- Individual contact information
- Personal data (email, phone, LinkedIn)
- Employment history
- Linked from outreach tasks

**📞 Outreach Activities** = Command Center (sales lives here)
- Complete context in description (ALL contacts + intel)
- Relationship fields pull from other lists
- Subtasks = multi-touch sequence
- Comments = responses
- **Sales team NEVER needs to leave this task**

---

## 🏌️ **Golf Courses List (901413061864)**

### **Purpose:**
Reference database for COURSE-LEVEL business intelligence

### **Existing Fields (Keep As-Is):**
- Course name (title)
- Website (probably exists)
- Phone (probably exists)
- Address (probably exists)

### **New Custom Fields to Add:**

#### **Group 1: Segmentation (Agent 6 Output)**

**Field 1: Segment**
- Type: Dropdown
- Options:
  - High-End (color: red)
  - Budget (color: green)
  - Both (color: yellow)
- Default: null
- Purpose: Business segment classification from Agent 6

**Field 2: Segment Confidence**
- Type: Number
- Range: 1-10
- Purpose: How confident Agent 6 is in segment classification

**Field 3: Segment Signals**
- Type: Long Text (or store in description)
- Purpose: Why this segment? (for verification)

#### **Group 2: Facility Data (Agent 6 + 7)**

**Field 4: Water Hazards**
- Type: Number
- Range: 0-18
- Purpose: Count from Agent 7 (affects retrieval opportunity)

**Field 5: Has Practice Range**
- Type: Checkbox
- Purpose: Range presence from Agent 6

**Field 6: Range Volume Indicator**
- Type: Dropdown: Low, Medium, High, Very High
- Purpose: How many balls they use (from Agent 6 intel)

#### **Group 3: Opportunity Scores (Agent 6 - Course Level)**

**Field 7: Range Ball Buy Score**
- Type: Number
- Range: 1-10
- Purpose: How good a fit for buy program

**Field 8: Range Ball Sell Score**
- Type: Number
- Range: 1-10
- Purpose: How good a fit for sell program

**Field 9: Range Ball Lease Score**
- Type: Number
- Range: 1-10
- Purpose: How good a fit for lease program

**Field 10: Ball Retrieval Score**
- Type: Number
- Range: 1-10
- Purpose: How good a fit for retrieval contract (based on water hazards)

#### **Group 4: Workflow Control**

**Field 11: Enrichment Status**
- Type: Dropdown
- Options: Not Started, Pending, Processing, Complete, Error
- Purpose: Track agent workflow progress

**Field 12: Enriched Date**
- Type: Date
- Purpose: When agents completed enrichment

**Field 13: Agent Cost**
- Type: Number (Currency)
- Purpose: Track enrichment cost per course

---

### **Task Name Format:**
`🏌️ {Course Name} | {City}, {State}`

Example: `🏌️ Country Club of Virginia | Richmond, VA`

### **Task Description Format:**
```markdown
## Course Intelligence
- **Segment:** High-End (9/10 confidence)
- **Water Hazards:** 7
- **Practice Range:** Yes (3 ranges, 800K balls/year)

## Top Opportunities
1. Range Ball Buy: 9/10
2. Ball Retrieval: 8/10
3. Range Ball Lease: 8/10

## Enrichment
- Enriched: Oct 18, 2024
- Contacts Found: 7
- Cost: $0.28
```

---

## 📇 **Contacts List (901413061863)**

### **Purpose:**
Reference database for INDIVIDUAL contact information

### **Existing Fields (✅ Keep & Use):**

1. **Email** (592c3d27-07af-42ce-a6c0-beb158305f9d)
   - Type: Email
   - ✅ Already exists

2. **LinkedIn URL** (f94bff39-d2de-4b6f-a010-cdafce7f2621)
   - Type: URL
   - ✅ Already exists

3. **Position** (99bb1ae8-edf5-4d79-b791-e2f38f67e2b0)
   - Type: Dropdown
   - Options: General Manager, Superintendent, Golf Professional, Director of Golf, etc.
   - ✅ Already exists - USE THIS

4. **State** (81bc2505-28a7-4290-a557-50e49e410732)
   - Type: Dropdown
   - ✅ Already exists

5. **Course** (b31efd5f-cae0-4920-aeb9-17542badffe3)
   - Type: Relationship → Golf Courses list
   - ✅ Already exists - CRITICAL for linking

6. **Last Contact Date** (bffd113f-65c7-4deb-8ddf-59187cfad7c0)
   - Type: Date
   - ✅ Already exists - use for tracking

7. **📞 Outreach Activities** (caa160a9-487d-406d-aacd-ea2dcb421ef0)
   - Type: Relationship → Outreach Activities list
   - ✅ Already exists - shows which campaigns this contact is in

### **New Custom Fields to Add:**

**Field 1: Phone** ⭐ CRITICAL
- Type: Phone
- Purpose: From Agent 5

**Field 2: Tenure Years**
- Type: Number
- Range: 0-50
- Purpose: How long at this course (from Agent 6.5)

**Field 3: Previous Clubs**
- Type: Short Text (or Long Text for JSON)
- Purpose: Employment history from Agent 6.5

**Field 4: Enriched By Agents**
- Type: Checkbox
- Purpose: Distinguish agent-enriched vs manual entry

**Field 5: Is Active**
- Type: Checkbox
- Default: true
- Purpose: Track if contact still employed (Agent 8 validation)

### **Existing Tags (✅ Keep Using):**
- `needs-enrichment` - Queue for agents
- `enriched` - Completed by agents
- `email-verified`, `linkedin-verified` - Data quality
- `decision-maker` - Priority contacts
- Role tags: `general-manager`, `superintendent`, `head-professional`, etc.

### **Task Name Format (Keep Current):**
`👤 {Name} - {Title}`

Example: `👤 Phil Kiester - General Manager`

### **Task Description (Minimal):**
```markdown
Contact at **{Course Name}**

**Email:** {email}
**Phone:** {phone}
**LinkedIn:** {url}
**Tenure:** {years} years at {current course}
**Previous:** {previous clubs}

**Enriched By:** Agents (Oct 18, 2024)
**Status:** Ready for outreach
```

---

## 📞 **Outreach Activities List (901413111587)** ⭐

### **Purpose:**
PRIMARY WORKING AREA - Sales team lives here, has complete context

### **New Custom Fields to Add:**

#### **Group 1: References (Relationships)**

**Field 1: Golf Course** ⭐ CRITICAL
- Type: Relationship → Golf Courses list (901413061864)
- Purpose: Shows course name, segment, website in sidebar
- Visible fields: Name, Segment, Website, Water Hazards

**Field 2: Primary Contact** ⭐ CRITICAL
- Type: Relationship → Contacts list (901413061863)
- Purpose: Shows main contact info in sidebar
- Visible fields: Name, Position, Email, Phone, LinkedIn

**Note:** Description will show ALL contacts, but this field shows the PRIMARY one for quick reference

#### **Group 2: Campaign Configuration**

**Field 3: Outreach Type**
- Type: Dropdown
- Options:
  - Range Ball Buy Program
  - Range Ball Sell Program
  - Range Ball Lease Program
  - Ball Retrieval Contract
  - Pro Shop E-Commerce
  - Superintendent Partnership
  - Multi-Opportunity (testing multiple)
- Purpose: Which value prop we're pitching

**Field 4: Target Segment** (copied from course for filtering)
- Type: Dropdown
- Options: High-End, Budget, Both
- Purpose: Filter outreach activities by segment

**Field 5: Opportunity Score**
- Type: Number
- Range: 1-10
- Purpose: How strong this opportunity is (from Agent 6)

#### **Group 3: Sequence Tracking**

**Field 6: Sequence Type**
- Type: Dropdown
- Options: 3-Email, 5-Touch (Email+LinkedIn), 7-Touch (Full Court Press)
- Purpose: Which automation sequence

**Field 7: Current Step**
- Type: Number
- Purpose: Which step in sequence (1, 2, 3...)

**Field 8: Conversation Starter Used**
- Type: Dropdown
- Options: #1, #2, #3, #4, #5
- Purpose: Which AI-generated starter we led with

#### **Group 4: Email Tracking**

**Field 9: Email Subject**
- Type: Short Text
- Purpose: What subject line we used

**Field 10: Email Sent Date**
- Type: Date
- Purpose: When first email sent

**Field 11: Email Opened**
- Type: Checkbox (or Date for when)
- Purpose: Did they open it

**Field 12: Replied**
- Type: Checkbox
- Purpose: Did they respond

**Field 13: Reply Date**
- Type: Date
- Purpose: When they responded

**Field 14: Response Channel**
- Type: Dropdown
- Options: Email, LinkedIn, Phone, In-Person
- Purpose: How they responded (edge case tracking!)

#### **Group 5: Outcome Tracking**

**Field 15: Meeting Booked**
- Type: Checkbox
- Purpose: Did we get a meeting

**Field 16: Meeting Date**
- Type: Date
- Purpose: When meeting scheduled

**Field 17: Call Attempted**
- Type: Checkbox
- Purpose: Did we try phone

**Field 18: Outcome**
- Type: Dropdown
- Options:
  - ✅ Qualified - Interested
  - 🔄 Follow-Up Needed
  - 📅 Nurture (6 months)
  - ❌ Not Interested
  - 👤 Wrong Contact (forward)
  - 🏢 Wrong Fit
  - 🚫 Do Not Contact
  - 🎉 Closed Won
  - 💔 Closed Lost
- Purpose: Final disposition

**Field 19: Deal Value**
- Type: Currency
- Purpose: If won, track revenue (for ROI)

---

### **Task Name Format:**
`{Course Name} - {Outreach Type} | {Primary Contact Name}`

Example: `Country Club of Virginia - Range Ball Buy | Phil Kiester`

### **Task Status Options:**
- To Do (not started)
- Scheduled (queued for send)
- Active (sequence running)
- Replied (got response)
- Meeting Scheduled (qualified)
- Closed Won (customer!)
- Closed Lost (didn't convert)
- Opted Out (blacklist)

### **Subtask Structure (Multi-Touch Sequence):**

```
Main Task: Country Club of Virginia - Range Ball Buy | Phil Kiester
│
├── 📧 Email #1: Initial Outreach
│   Status: Complete
│   Assignee: Sales Rep
│   Custom Fields:
│     - Channel: Email
│     - Sent Date: Jan 15
│     - Opened: Yes
│     - Replied: No
│   Comments:
│     - "Sent using Starter #1"
│     - "Email opened Jan 15 at 10:30 AM"
│
├── 📧 Email #2: Follow-Up
│   Status: In Progress
│   Due Date: Jan 18 (3 days after #1)
│   Depends On: Email #1 (no response)
│   Custom Fields:
│     - Channel: Email
│     - Scheduled: Jan 18
│   Comments:
│     - "Using Starter #2 - different angle"
│
├── 💼 LinkedIn Message
│   Status: To Do
│   Due Date: Jan 21 (if emails fail)
│   Depends On: Email #2 (no response)
│   Custom Fields:
│     - Channel: LinkedIn
│   Comments:
│     - "Backup channel if email doesn't work"
│
├── 📞 Phone Call
│   Status: To Do
│   Due Date: Jan 25
│   Custom Fields:
│     - Channel: Phone
│   Comments:
│     - "Use: (804) 288-2891"
│     - "Script based on Starter #1"
│
└── 🔄 Pivot to Warren West
    Status: To Do
    Due Date: If Phil unresponsive
    Comments:
      - "Try Director of Golf instead"
      - "CC Phil for visibility"
```

---

### **Task Description (THE MAGIC - Complete Context):**

See `OUTREACH_TASK_TEMPLATE.md` for full template with:
- All decision-makers (email, phone, LinkedIn for each)
- Complete company intelligence
- All conversation starters ranked
- Sequence plan
- Edge case handling notes

---

## 📊 **Data Distribution Matrix**

| Data Element | Golf Courses | Contacts | Outreach Activities | Supabase |
|--------------|--------------|----------|---------------------|----------|
| **Course name** | ✅ Primary | | 🔗 Relationship | ✅ Truth |
| **Segment** | ✅ Primary | | 📋 Copied | ✅ Truth |
| **Water hazards** | ✅ Primary | | 📝 In description | ✅ Truth |
| **Opportunity scores** | ✅ All 6 scores | 🔗 View only | 📋 Top 1-2 only | ✅ Truth |
| **Contact name** | | ✅ Primary | 🔗 Relationship | ✅ Truth |
| **Email, Phone, LinkedIn** | | ✅ Primary | 📝 ALL in description | ✅ Truth |
| **Tenure, prev clubs** | | ✅ Primary | 📝 In description | ✅ Truth |
| **Conversation starters** | | | 📝 In description | ✅ Truth (JSONB) |
| **Outreach type** | | | ✅ Primary | ✅ Truth |
| **Email tracking** | | | ✅ Primary | ✅ Truth (detailed) |
| **Responses** | | | 💬 Comments | ✅ Truth (full log) |

**Key:**
- ✅ Primary = Field stores the data
- 🔗 Relationship = Linked field shows data from other list
- 📋 Copied = Duplicated for filtering/sorting
- 📝 In description = Formatted text in description
- 💬 Comments = Discussion/responses

---

## 🔄 **Data Flow (Supabase → ClickUp)**

### **When Agents Complete Enrichment:**

```
Agents Finish (Render API)
    ↓
Webhook to Supabase
    ↓
Supabase Edge Function: receive-agent-enrichment
    ├── Update golf_courses table
    ├── Insert golf_course_contacts (4-7 rows)
    └── Trigger: create-clickup-outreach-tasks
        ↓
Edge Function: create-clickup-outreach-tasks
    ├── Step 1: Update/Create Golf Course Task
    │   List: 🏌️ Golf Courses
    │   Update: Segment, Water Hazards, Opp Scores, Status=Complete
    │
    ├── Step 2: Update/Create Contact Tasks (4-7 tasks)
    │   List: 📇 Contacts
    │   Update: Email, Phone, LinkedIn, Tenure
    │   Tag: enriched, {segment}
    │
    └── Step 3: Create Outreach Task (1 task per course)
        List: 📞 Outreach Activities
        Name: {Course} - {Top Opp} | {Primary Contact}
        Description: ← ALL CONTACTS + INTEL + STARTERS (rich!)
        Custom Fields: Course rel, Contact rel, Opp Type, Score, etc.
        Subtasks: Email #1, #2, #3, LinkedIn, Phone
        Status: Scheduled
```

---

## 💬 **Response Handling (ClickUp → Supabase)**

### **Scenario: Email Response Received**

```
Email Provider (SendGrid) Webhook
    ↓
Supabase Edge Function: email-response-received
    ├── Parse: from_email, subject, body, sentiment
    ├── Match: to contact (phil@theccv.org → Phil Kiester)
    ├── Match: to outreach activity (active campaign for this contact)
    ├── INSERT: outreach_communications (inbound row)
    ├── UPDATE: outreach_sequences (response_received=true, stop sequence)
    └── Trigger: update-clickup-on-response
        ↓
Edge Function: update-clickup-on-response
    ├── Find outreach task by clickup_task_id
    ├── Update subtask "Email #1" → Status: "Response Received" ✅
    ├── Add comment: "💬 Phil responded: '{preview}'"
    ├── Update custom field: Replied=true, Reply Date=today
    ├── Update main task status → "Replied - Action Needed"
    └── Notify: Assign to sales rep, send notification
```

---

## 🚨 **Edge Case Handling (Documented for Each)**

### **Edge Case 1: Multi-Channel Pivot**

**Scenario:** Email fails → Pivot to LinkedIn

**Supabase:**
```sql
-- Email attempt
INSERT INTO outreach_communications (
  channel='email', direction='outbound', replied=false
);

-- LinkedIn attempt
INSERT INTO outreach_communications (
  channel='linkedin', direction='outbound', replied=true
);

-- Track channel effectiveness
SELECT channel,
       COUNT(*) FILTER (WHERE replied=true) * 100.0 / COUNT(*) as response_rate
FROM outreach_communications
WHERE direction='outbound'
GROUP BY channel;
```

**ClickUp:**
- Subtask "Email #1" → Status: "No Response"
- Subtask "LinkedIn Message" → Status: "Response Received" ✅
- Custom field "Response Channel" → "LinkedIn"
- Comment: "Pivoted to LinkedIn after email non-response - SUCCESS"

---

### **Edge Case 2: Wrong Contact Responds**

**Scenario:** Email Phil → Warren responds

**Supabase:**
```sql
INSERT INTO outreach_communications (
  contact_id = 'phil-uuid',
  responder_contact_id = 'warren-uuid', -- DIFFERENT!
  responder_name = 'Warren West',
  responder_email = 'warren.west@theccv.org',
  response_text = 'Warren replied...',
  direction = 'inbound'
);

-- Flag for sales attention
UPDATE outreach_activities
SET status = 'needs_review',
    status_reason = 'Different contact responded';
```

**ClickUp:**
- Comment: "⚡ ATTENTION: Warren West (Director of Golf) responded on behalf of Phil"
- Update: Response Channel = "Email (via colleague)"
- Action item: "Should we continue with Warren instead?"
- Option 1: Update Primary Contact field → Warren
- Option 2: Create new outreach task for Warren

---

### **Edge Case 3: Contact Left Company**

**Scenario:** Auto-reply "Phil no longer works here"

**Supabase:**
```sql
-- Mark contact inactive
UPDATE golf_course_contacts
SET is_active = false,
    left_date = now(),
    left_reason = 'email_auto_reply'
WHERE id = 'phil-uuid';

-- Log communication
INSERT INTO outreach_communications (
  contact_id = 'phil-uuid',
  direction = 'inbound',
  response_text = 'Out of office - no longer with company',
  response_sentiment = 'contact_left'
);

-- Trigger: Find replacement (future - Agent 8)
INSERT INTO contact_replacement_queue (
  course_id = 'ccv-uuid',
  position_needed = 'General Manager',
  priority = 'high'
);
```

**ClickUp:**
- Comment: "🚨 Contact left company (auto-detected from email bounce)"
- Tag: `contact-left`
- Status: "Contact Inactive"
- Create follow-up task: "Find new GM at Country Club of Virginia"
- Link to original outreach for context

---

### **Edge Case 4: Opt-Out / Unsubscribe**

**Scenario:** "Remove from list" response

**Supabase (IMMEDIATE - Compliance!):**
```sql
-- Blacklist contact
UPDATE golf_course_contacts
SET opted_out = true,
    opted_out_at = now(),
    opt_out_reason = 'user_requested',
    do_not_contact = true
WHERE id = 'contact-uuid';

-- Blacklist entire course (your choice)
UPDATE golf_courses
SET do_not_contact = true,
    blacklisted_at = now(),
    blacklist_reason = 'contact_opt_out'
WHERE id = 'course-uuid';

-- Stop ALL sequences
UPDATE outreach_sequences
SET status = 'unsubscribed',
    paused_at = now()
WHERE contact_id = 'contact-uuid';

-- Audit trail (IMMUTABLE)
INSERT INTO opt_out_log (contact_id, course_id, opted_out_at, ip_address, method);
```

**ClickUp (IMMEDIATE):**
- All tasks for this contact → Tag: `do-not-contact`
- All outreach tasks → Status: "Opted Out"
- Comment: "🚫 OPT-OUT REQUESTED - Do not contact"
- Block future task creation for this contact/course

---

## 📝 **Outreach Task Description Template (Complete)**

### **Structure:**

```
1. Campaign Summary (status, type, score)
2. Primary Contact (name, email, phone, LinkedIn, tenure)
3. All Other Contacts (same format for 3-6 more people)
4. Company Intelligence (segment, signals, facility data)
5. Why This Opportunity (buying signals, pain points)
6. Conversation Starters (3-5 ranked options)
7. Outreach Sequence Plan (which touches planned)
8. Success Criteria (what qualifies, what disqualifies)
9. Metrics (cost, touches, timeline)
```

**See:** `OUTREACH_TASK_TEMPLATE.md` for full formatted template

**Key Innovation:** ALL 4-7 contacts visible with complete info → Sales can pivot without leaving task!

---

## 🎯 **Custom Views for Sales Team**

### **In Outreach Activities List:**

**View 1: "🔥 High-End Pipeline"**
- Filter: Target Segment = "High-End"
- Group by: Outreach Type
- Sort: Opportunity Score (descending)
- Show: Course, Primary Contact, Email, Phone, Opportunity Score, Status

**View 2: "💰 Budget Pipeline"**
- Filter: Target Segment = "Budget"
- Group by: Outreach Type
- Sort: Opportunity Score (descending)

**View 3: "📧 Active Sequences"**
- Filter: Status IN ("Scheduled", "Active")
- Sort: Email Sent Date (oldest first)
- Purpose: What needs attention today

**View 4: "✅ Replied - Action Needed"**
- Filter: Replied = true AND Status = "Replied"
- Sort: Reply Date (newest first)
- Purpose: Hot leads to respond to

**View 5: "📅 Meetings This Week"**
- Filter: Meeting Booked = true AND Meeting Date = this week
- Sort: Meeting Date
- Purpose: Prep for upcoming meetings

**View 6: "🎉 Closed Won"**
- Filter: Outcome = "Closed Won"
- Group by: Outreach Type
- Purpose: Success tracking, attribution

**View 7: "By Conversation Starter"**
- Group by: Conversation Starter Used
- Filter: Replied = true
- Purpose: Which starters work best? (A/B testing)

---

## 🔔 **Automation Rules in ClickUp**

### **Rule 1: Auto-Create Follow-Up Subtasks**
- Trigger: When Email #1 subtask marked complete + Replied = false
- Wait: 3 days
- Action: Move "Email #2" subtask to "To Do" status

### **Rule 2: Auto-Update on Reply**
- Trigger: When comment added containing "responded" or webhook
- Action: Update Status → "Replied - Action Needed"
- Action: Update Replied field → true

### **Rule 3: Alert on Opt-Out**
- Trigger: When comment contains "unsubscribe" or "remove from list"
- Action: Add tag "do-not-contact"
- Action: Update Status → "Opted Out"
- Action: Notify admin immediately

### **Rule 4: Auto-Archive Closed**
- Trigger: When Status = "Closed Won" or "Closed Lost"
- Wait: 30 days
- Action: Archive task (keep for reporting)

---

## 📊 **Reporting & Analytics**

### **From ClickUp (Operational Metrics):**

**Sales Dashboard Views:**
- Active campaigns by segment
- Response rate by conversation starter
- Pipeline by opportunity type
- Meeting conversion rate
- Win rate by segment

### **From Supabase (Deep Analytics):**

```sql
-- Response rate by channel
SELECT channel,
       COUNT(*) FILTER (WHERE replied=true) * 100.0 / COUNT(*) as response_rate
FROM outreach_communications
WHERE direction='outbound'
GROUP BY channel;

-- Conversation starter effectiveness
SELECT conversation_starter_num,
       COUNT(*) FILTER (WHERE replied=true) * 100.0 / COUNT(*) as response_rate,
       AVG(EXTRACT(EPOCH FROM (replied_at - sent_at)) / 3600) as avg_hours_to_response
FROM outreach_communications
WHERE direction='outbound' AND conversation_starter_num IS NOT NULL
GROUP BY conversation_starter_num
ORDER BY response_rate DESC;

-- Segment conversion
SELECT
  target_segment,
  COUNT(*) as total_campaigns,
  COUNT(*) FILTER (WHERE status='closed_won') as won,
  ROUND(COUNT(*) FILTER (WHERE status='closed_won') * 100.0 / COUNT(*), 2) as win_rate,
  AVG(deal_value_usd) FILTER (WHERE status='closed_won') as avg_deal_value
FROM outreach_activities
GROUP BY target_segment;
```

---

## 🎯 **Implementation Checklist**

### **ClickUp Setup:**
- [ ] Add 9 custom fields to Golf Courses list
- [ ] Add 5 custom fields to Contacts list (Phone is critical!)
- [ ] Add 19 custom fields to Outreach Activities list
- [ ] Create 7 custom views
- [ ] Document all field IDs in config file
- [ ] Test task creation with full data

### **Supabase:**
- [ ] Apply migration 004 (courses + contacts fields)
- [ ] Apply migration 005 (outreach tables)
- [ ] Create communication logging triggers
- [ ] Test data writes

### **Edge Functions:**
- [ ] create-outreach-task (generates rich description)
- [ ] update-clickup-on-response (webhook handler)
- [ ] log-communication (audit trail)

### **Testing:**
- [ ] End-to-end: Enrich → ClickUp tasks created
- [ ] Test: All contacts in description
- [ ] Test: Subtasks created
- [ ] Test: Response logging
- [ ] Test: Edge cases (opt-out, wrong contact, etc.)

---

## 📚 **Related Documentation**

- **OUTREACH_TASK_TEMPLATE.md** - Complete description template
- **EDGE_CASE_PLAYBOOK.md** - 10 scenarios with handling
- **SUPABASE_SCHEMA_COMPLETE.sql** - 5 tables for full system
- **EDGE_FUNCTIONS.md** - 4 edge functions with code

---

**Last Updated:** October 18, 2024
**Status:** Architecture designed, ready to implement
**Next:** Create templates and schemas
