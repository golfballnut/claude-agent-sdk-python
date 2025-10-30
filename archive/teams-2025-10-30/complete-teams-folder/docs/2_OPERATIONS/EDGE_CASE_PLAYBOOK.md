# Edge Case Playbook - Outreach System

**Purpose:** Comprehensive handling for 10 critical edge cases in outreach workflow
**Audience:** Dev/ops + sales team
**Last Updated:** October 18, 2024

---

## 🎯 **Core Principle**

**Every edge case has:**
1. **Detection** - How we know it happened
2. **Supabase Action** - What gets logged/updated in database
3. **ClickUp Action** - What sales team sees/does
4. **Recovery** - How to handle it gracefully

---

## Edge Case #1: Multi-Channel Pivot (Email Fails → LinkedIn Works)

### **Scenario:**
```
Email #1 → No response (3 days)
Email #2 → No response (3 days)
LinkedIn Message → RESPONSE! ✅
```

### **Detection:**
- Email sends logged but `replied = false`
- LinkedIn send logged
- LinkedIn response received (webhook)

### **Supabase Actions:**
```sql
-- Log all attempts
INSERT INTO outreach_communications (channel='email', direction='outbound', replied=false);  -- Email #1
INSERT INTO outreach_communications (channel='email', direction='outbound', replied=false);  -- Email #2
INSERT INTO outreach_communications (channel='linkedin', direction='outbound');  -- LinkedIn
INSERT INTO outreach_communications (channel='linkedin', direction='inbound', response_text='...');  -- Response!

-- Update activity
UPDATE outreach_activities
SET responded = true,
    response_channel = 'linkedin',  -- They preferred LinkedIn!
    status = 'replied'
WHERE id = 'activity-uuid';

-- Analytics: Track channel preference
-- Later: Prioritize LinkedIn for this contact in future campaigns
```

### **ClickUp Actions:**
- Subtask "Email #1" → Status: "No Response"
- Subtask "Email #2" → Status: "No Response"
- Subtask "LinkedIn Message" → Status: "Response Received" ✅
- Comment: "💬 Responded via LinkedIn: '{preview of response}'"
- Custom field "Response Channel" → "LinkedIn"
- Main task status → "Replied - Action Needed"
- Notify sales rep

### **Sales Team Next Steps:**
- Continue conversation on LinkedIn (they're active there)
- Note preference for future outreach
- Ask if email works or prefer LinkedIn going forward

### **Learning:**
```sql
-- Query: Do certain roles prefer LinkedIn?
SELECT
  c.title_category,
  oc.channel,
  COUNT(*) as responses
FROM outreach_communications oc
JOIN outreach_activities oa ON oc.outreach_activity_id = oa.id
JOIN golf_course_contacts c ON oa.primary_contact_id = c.id
WHERE oc.direction = 'inbound'
GROUP BY c.title_category, oc.channel;

-- If GMs respond better to LinkedIn → adjust sequence!
```

---

## Edge Case #2: Wrong Contact Responds

### **Scenario:**
```
Email to: Phil Kiester (GM)
Response from: Warren West (Director of Golf)
Message: "Phil forwarded this to me. I handle range operations. Let's talk."
```

### **Detection:**
- Response email address ≠ sent-to email
- Or: Response mentions forwarding

### **Supabase Actions:**
```sql
-- Log original send
INSERT INTO outreach_communications (
  contact_id = 'phil-uuid',
  direction = 'outbound'
);

-- Log response from different person
INSERT INTO outreach_communications (
  contact_id = 'phil-uuid',  -- Original recipient
  responder_contact_id = 'warren-uuid',  -- Actual responder!
  responder_name = 'Warren West',
  responder_email = 'warren.west@theccv.org',
  direction = 'inbound',
  response_text = 'Phil forwarded...'
);

-- Check if Warren already in contacts
IF warren NOT IN golf_course_contacts:
  -- Add Warren as new contact
  INSERT INTO golf_course_contacts (
    name='Warren West',
    title='Director of Golf',
    email='warren.west@theccv.org',
    discovered_via='forwarded_from_phil',
    is_active=true
  );
END IF;

-- Update activity: Warren is now primary!
UPDATE outreach_activities
SET responded = true,
    responded_by_contact_id = 'warren-uuid',  -- Different person
    primary_contact_id = 'warren-uuid',  -- Switch primary!
    status = 'replied'
WHERE id = 'activity-uuid';
```

### **ClickUp Actions:**
- Comment: "⚡ ATTENTION: Warren West (Director of Golf) responded on behalf of Phil"
- Comment: "Phil forwarded internally - good sign! Warren handles range operations."
- Update custom field "Primary Contact" → Warren West
- Check if Warren exists in Contacts list:
  - If YES: Link to existing
  - If NO: Create new contact task
- Main task status → "Replied - Continue with Warren"
- Keep Phil linked as "Referrer"

### **Sales Team Next Steps:**
- Thank Warren for responding
- Reference Phil's forward (shows internal interest)
- Continue conversation with Warren
- Optional: CC Phil on future emails (keep him looped)

### **Why This is GOOD News:**
- Internal forward = they're taking it seriously
- Found the right operational owner
- Warren may have more authority on range decisions than GM
- Two champions better than one!

---

## Edge Case #3: Contact Left Company

### **Scenario:**
```
Email sent → Auto-reply: "Phil Kiester is no longer with Country Club of Virginia"
OR
LinkedIn: Profile updated "Past: CCV" (was "Current")
```

### **Detection:**
- Email auto-reply contains "no longer", "left", "not with"
- Email hard bounce (address disabled)
- LinkedIn title changed to "Past: CCV"
- Agent 8 monthly check detects job change

### **Supabase Actions:**
```sql
-- Mark contact inactive
SELECT mark_contact_left_company(
  'phil-uuid',
  'email_auto_reply',
  'Auto-reply: Phil no longer with company as of Oct 2024'
);

-- This function:
-- 1. Sets is_active=false, left_date=NOW()
-- 2. Logs to contact_changes table
-- 3. Stops all active sequences
-- 4. Updates outreach_activities status='contact_left'

-- Queue for replacement discovery
INSERT INTO contact_replacement_queue (
  course_id = 'ccv-uuid',
  position_needed = 'General Manager',
  priority = 'high',  -- Was in active outreach
  notes = 'Phil Kiester left Oct 2024'
);

-- Future: Agent 9 (Contact Replacement Finder)
-- Automatically searches for new GM at CCV
-- Creates new contact when found
-- Creates new outreach task
```

### **ClickUp Actions:**
- Comment: "🚨 ALERT: Contact left company (auto-detected from email bounce)"
- Tag: `contact-left`
- Contact task (Phil) → Status: "Inactive"
- Outreach task → Status: "Contact Left - Find Replacement"
- Create NEW task: "Find new GM at Country Club of Virginia"
  - Description: "Phil Kiester left Oct 2024. Need replacement contact."
  - Link to original outreach (preserve context)
  - Assignee: Research team or Agent 9 automation

### **Sales Team Next Steps:**
- Put campaign on hold
- Research new GM (LinkedIn, website, call course)
- When found: Create new contact + new outreach task
- Reference: "Following up on conversation with former GM Phil Kiester..."

### **Prevention:**
- Run Agent 8 monthly on all active contacts
- Proactive LinkedIn monitoring
- Catch changes BEFORE outreach fails

---

## Edge Case #4: Multiple Responders (CC'd)

### **Scenario:**
```
Email to: Phil (GM)
CC: Warren (Director of Golf), Christian (Superintendent)
Responses from: ALL THREE with different perspectives
```

### **Detection:**
- 3 inbound emails from same thread_id
- Different from_addresses

### **Supabase Actions:**
```sql
-- Log each response separately
INSERT INTO outreach_communications (
  contact_id='phil-uuid',
  responder_contact_id='phil-uuid',
  response_text='Phil: I like this idea for our flagship course...'
);

INSERT INTO outreach_communications (
  contact_id='warren-uuid',
  responder_contact_id='warren-uuid',
  response_text='Warren: What about our other two courses?...'
);

INSERT INTO outreach_communications (
  contact_id='christian-uuid',
  responder_contact_id='christian-uuid',
  response_text='Christian: Also interested in ball retrieval...'
);

-- Update activity
UPDATE outreach_activities
SET status = 'multiple_responses',  -- Special status!
    total_touches = total_touches + 2  -- Count additional engagement
WHERE id = 'activity-uuid';
```

### **ClickUp Actions:**
- Comment #1: "💬 Phil Kiester responded: '{preview}'"
- Comment #2: "💬 Warren West responded: '{preview}'"
- Comment #3: "💬 Christian Sain responded: '{preview}'"
- Status → "Multiple Responses - VERY HOT LEAD 🔥"
- Create 3 checklists:
  - [ ] Follow up with Phil on flagship course interest
  - [ ] Follow up with Warren on other courses (expansion!)
  - [ ] Follow up with Christian on retrieval opportunity (cross-sell!)

### **Sales Team Next Steps:**
- Respond to thread (include all three)
- Acknowledge each person's specific interest
- Propose: "Given interest from all three, should we schedule a group call?"
- Opportunity: Pitch multiple programs (buy + retrieval)
- Escalate: This is a HOT lead with multiple champions!

### **Why This is BEST Case Scenario:**
- Internal consensus (all three interested!)
- Different perspectives = comprehensive buy-in
- Upsell opportunities (retrieval + buy)
- Higher close probability

---

## Edge Case #5: Late Response (After Sequence Ended)

### **Scenario:**
```
Sequence: Jan 1-15 (5 touches) → Marked complete, no response
Reply: April 10 (85 days later) → "Sorry for delay, still interested"
```

### **Detection:**
- outreach_sequences.status = 'completed'
- But new inbound communication received
- received_at > completed_at + 30 days

### **Supabase Actions:**
```sql
-- Log the late response
INSERT INTO outreach_communications (
  outreach_activity_id='activity-uuid',
  direction='inbound',
  received_at=NOW(),
  response_text='Sorry for delay, been busy. Still interested in range ball program.',
  response_sentiment='positive_late'
);

-- Reactivate activity
UPDATE outreach_activities
SET status = 'replied',
    response_received_at = NOW(),
    responded = true,
    outcome_notes = 'Late response (85 days after last contact)'
WHERE id = 'activity-uuid';

-- Reactivate sequence (for follow-up)
UPDATE outreach_sequences
SET status = 'reactivated',
    current_step = total_steps + 1,  -- Continue from where we left off
    next_scheduled_at = NULL  -- Manual response needed (not automated)
WHERE outreach_activity_id = 'activity-uuid';
```

### **ClickUp Actions:**
- Comment: "🎯 LATE RESPONSE RECEIVED (85 days after last contact)"
- Comment: "Original context: '{summary of original pitch}'"
- Status → "Reactivated - Action Needed"
- Subtask: "Respond to late reply - refresh context"
- Alert: Notify sales rep (may need to review original conversation)

### **Sales Team Next Steps:**
- Review original conversation (description has full context!)
- Acknowledge the delay (no judgment)
- Refresh the opportunity (may have changed in 3 months)
- Ask: "What made you think of us again?" (understand trigger)
- Proceed as if fresh lead (circumstances may have changed)

### **Follow-Up Email Template:**
```
"Warren, thanks for circling back! I know it's been a few months since we originally connected about CCV's range ball program.

Quick refresher: [Brief re-pitch with updated numbers if available]

Has anything changed on your end that makes now a better time to explore this? Happy to send over more details or hop on a quick call.
```

---

## Edge Case #6: Opt-Out / Unsubscribe Request

### **Scenario:**
```
Response: "Remove me from your mailing list"
OR
Clicks unsubscribe link
OR
Replies: "Not interested, don't contact again"
```

### **Detection:**
- Response text contains: "unsubscribe", "remove", "don't contact", "do not email"
- Unsubscribe link clicked (webhook)
- Aggressive negative sentiment in reply

### **Supabase Actions (IMMEDIATE - Compliance!):**
```sql
-- CRITICAL: Handle within seconds
SELECT handle_opt_out(
  'contact-uuid',
  'Remove from mailing list - not interested',
  'email_reply'
);

-- This function:
-- 1. Sets opted_out=true, do_not_contact=true
-- 2. Logs to IMMUTABLE opt_out_log table
-- 3. Stops ALL active sequences
-- 4. Updates ALL outreach activities to 'opted_out'
-- 5. Honors request immediately

-- Block future outreach
UPDATE golf_course_contacts
SET do_not_contact = true,
    opted_out = true,
    opted_out_at = NOW()
WHERE id = 'contact-uuid';

-- Option: Blacklist entire course (your policy decision)
UPDATE golf_courses
SET do_not_contact = true,
    blacklist_reason = 'contact_opt_out_phil_kiester'
WHERE id = 'course-uuid';
```

### **ClickUp Actions (IMMEDIATE):**
- Tag ALL contacts from this course: `do-not-contact`
- Outreach task → Status: "Opted Out 🚫"
- Comment: "🚫 OPT-OUT REQUEST RECEIVED - Do not contact per request"
- Lock task (prevent accidental re-opening)
- Remove from all views except "Opted Out" view

### **Sales Team Next Steps:**
- STOP all contact immediately
- Do NOT send any more emails
- Do NOT call
- Do NOT message on LinkedIn
- Document: Why they opted out (helpful for others)

### **Compliance:**
- Must honor within 10 business days (legally)
- We honor immediately (good practice)
- Cannot re-contact unless they initiate
- Keep in database (need record for compliance)

### **Edge Sub-Case: They Say "Not Now, Try Again in 6 Months"**

**This is NOT opt-out!** This is nurture:
```sql
-- Different handling
UPDATE outreach_activities
SET status = 'nurture',
    outcome = 'timing_not_right',
    outcome_notes = 'Requested follow-up in 6 months (April 2025)'
WHERE id = 'activity-uuid';

-- Schedule future reactivation
INSERT INTO outreach_sequences (
  outreach_activity_id = 'activity-uuid',
  sequence_type = 'reactivation_6_month',
  next_scheduled_at = NOW() + INTERVAL '6 months',
  status = 'paused'
);
```

**ClickUp:**
- Status → "Nurture (6 Months)"
- Due date → April 2025
- Comment: "Not now, but open to future. Set reminder for April."

---

## Edge Case #7: Wrong Opportunity Pivot

### **Scenario:**
```
Pitched: Range Ball Buy Program
Response: "Not interested in selling balls, but tell me about ball retrieval"
```

### **Detection:**
- Response mentions different opportunity keyword
- Sentiment: positive but not for original pitch

### **Supabase Actions:**
```sql
-- Log original pitch attempt
INSERT INTO outreach_communications (
  outreach_type_pitched = 'range_ball_buy',
  response_sentiment = 'interested_different_opportunity'
);

-- Note interest in different opportunity
UPDATE outreach_activities
SET outcome = 'pivoted_to_different_opportunity',
    outcome_notes = 'Interested in ball retrieval instead of range ball buy'
WHERE id = 'activity-uuid';

-- Get retrieval score for this course
SELECT opportunities->>'ball_retrieval' as retrieval_score
FROM golf_courses
WHERE id = 'course-uuid';
-- If score is good (7+), create new campaign
```

### **ClickUp Actions:**
- Comment: "🔄 PIVOT: Not interested in range ball buy, but asked about ball retrieval"
- Create NEW outreach task:
  - Name: "Country Club of Virginia - Ball Retrieval | Phil Kiester"
  - Type: Ball Retrieval Contract
  - Score: {from Agent 6} (if we have it)
  - Description: Use retrieval conversation starters
  - Reference: "Pivot from range ball buy campaign"
  - Link to original task
- Original task → Status: "Pivoted - See New Task"
- Link both tasks

### **Sales Team Next Steps:**
- Don't lose momentum! Respond immediately
- "Great! Let me tell you about our retrieval services..."
- Use retrieval-specific pitch (we have 7 water hazards intel!)
- Send retrieval info packet
- Schedule call focused on retrieval

### **Why This Happens:**
- They need something, just not what we pitched first
- Our multi-opportunity scoring helps us pivot quickly
- We have the intel for ALL opportunities (Agent 6!)
- Don't give up - just different path to revenue

---

## Edge Case #8: Forward to Procurement/New Contact

### **Scenario:**
```
Response from Phil: "I'm forwarding this to Sarah Johnson, our Procurement Director. She handles vendor relationships."
Email from Sarah: "Phil forwarded your email. Tell me more."
```

### **Detection:**
- Forward mentioned in response
- New email address responds (not in our database)
- Name mentioned we don't have

### **Supabase Actions:**
```sql
-- Log Phil's forward
INSERT INTO outreach_communications (
  contact_id = 'phil-uuid',
  response_text = 'Forwarding to Sarah Johnson (Procurement)...',
  forwarded_to_name = 'Sarah Johnson',
  forwarded_to_email = 'sarah.johnson@theccv.org'
);

-- Create NEW contact (Sarah)
INSERT INTO golf_course_contacts (
  golf_course_id = 'ccv-uuid',
  name = 'Sarah Johnson',
  title = 'Procurement Director',  -- From Phil's message
  email = 'sarah.johnson@theccv.org',
  discovered_via = 'forwarded_from_phil_kiester',
  discovered_date = NOW(),
  is_active = true,
  enriched_by_agents = false  -- Manually discovered
);

-- Log Sarah's response
INSERT INTO outreach_communications (
  contact_id = 'sarah-uuid',
  direction = 'inbound',
  response_text = 'Phil forwarded. Tell me more.'
);

-- Create NEW outreach activity for Sarah
INSERT INTO outreach_activities (
  course_id = 'ccv-uuid',
  primary_contact_id = 'sarah-uuid',
  outreach_type = 'range_ball_buy',  -- Same opportunity
  target_segment = 'high-end',  -- Same segment
  opportunity_score = 9,  -- Same score
  referred_by_contact_id = 'phil-uuid',  -- Note the referral!
  status = 'replied',  -- She already engaged!
  created_by = 'referral_automation'
);
```

### **ClickUp Actions:**
- Original task (Phil):
  - Comment: "✅ Phil forwarded to Sarah Johnson (Procurement Director)"
  - Status → "Forwarded - Success"
  - Link to new task

- NEW Contact task (Sarah):
  - List: 📇 Contacts
  - Name: "👤 Sarah Johnson - Procurement Director"
  - Email: sarah.johnson@theccv.org
  - Course: Country Club of Virginia (relationship)
  - Tag: `discovered-via-referral`, `warm-lead`
  - Description: "Referred by Phil Kiester (GM). Already engaged - responded to forwarded email."

- NEW Outreach task (Sarah):
  - List: 📞 Outreach Activities
  - Name: "Country Club of Virginia - Range Ball Buy | Sarah Johnson"
  - Description: SAME rich context (all contacts, same intel)
  - Add section: "**Referred By:** Phil Kiester (GM) - Internal champion!"
  - Status: "Active - Referred Lead 🔥"
  - Priority: HIGH (referral = warm!)

### **Sales Team Next Steps:**
- Thank Sarah for responding
- Thank Phil in separate email (acknowledge the forward)
- Continue with Sarah (she's the decision-maker)
- Ask Sarah: "What questions can I answer about the program?"
- Keep Phil CC'd (he's your champion!)

### **Why This is GREAT:**
- Phil is a champion (forwarded vs ignoring)
- Found real decision-maker (Sarah handles vendors)
- Sarah already warm (Phil vouched for us)
- Two contacts engaged = higher close rate

---

## Edge Case #9: Hard Email Bounce

### **Scenario:**
```
Email sent → Bounce notification: "Address doesn't exist" or "User unknown"
```

### **Detection:**
- Email provider webhook: bounce_type = 'hard'
- 550 error code (permanent failure)

### **Supabase Actions:**
```sql
-- Log bounce
INSERT INTO outreach_communications (
  contact_id = 'contact-uuid',
  channel = 'email',
  direction = 'outbound',
  bounce_type = 'hard',
  response_sentiment = 'bounce_hard',
  response_text = 'Email bounced: User unknown'
);

-- Invalidate email
UPDATE golf_course_contacts
SET email = NULL,  -- Remove bad email!
    email_valid = false,
    email_bounce_date = NOW(),
    email_bounce_type = 'hard'
WHERE id = 'contact-uuid';

-- Log the change
INSERT INTO contact_changes (
  contact_id = 'contact-uuid',
  change_type = 'email_invalid',
  old_value = 'old.email@example.com',
  new_value = NULL,
  detected_by = 'email_bounce',
  confidence = 10
);

-- Trigger Agent 3 re-run (find correct email)
-- OR pivot to different channel immediately
```

### **ClickUp Actions:**
- Comment: "⚠️ EMAIL BOUNCED (hard bounce - address invalid)"
- Tag: `needs-re-enrichment`
- Subtask "Email #1" → Status: "Failed - Bad Email"
- Subtask "LinkedIn Message" → Status: "To Do" (auto-promoted)
- Custom field "Email" → Clear (remove invalid email)
- Status → "Bad Contact Info - Retry LinkedIn"

### **Sales Team Next Steps:**
- Try LinkedIn immediately (we have the URL!)
- OR call phone number (we have it!)
- OR research correct email (company website, LinkedIn)
- Note in task: "Old email invalid, used {new method}"

### **Soft Bounce (Temporary) Handling:**
```sql
-- If bounce_type = 'soft' (mailbox full, server down):
-- Retry in 24 hours (don't invalidate email)
-- If 3 soft bounces → treat as hard bounce
```

---

## Edge Case #10: Full Success Progression (Track Attribution)

### **Scenario:**
```
Email #1 → Opened → Replied interested
Call scheduled → Call held → Proposal sent
Proposal accepted → Closed Won! 💰
```

### **Detection:**
- Status progressions tracked
- Each step logged

### **Supabase Actions (Complete Audit Trail):**
```sql
-- Communication #1: Initial email
INSERT INTO outreach_communications (
  channel='email', direction='outbound',
  subject='CCV + Range Ball Opportunity',
  conversation_starter_num=1,
  sequence_step=1,
  sent_at='2024-01-15 10:00:00'
);

-- Communication #2: Opened
UPDATE outreach_communications
SET opened=true, opened_at='2024-01-15 14:30:00'
WHERE id='email-1-id';

-- Communication #3: Positive reply
INSERT INTO outreach_communications (
  channel='email', direction='inbound',
  response_text='Sounds interesting! Can we schedule a call?',
  response_sentiment='positive_interested',
  received_at='2024-01-16 09:15:00'
);

-- Communication #4: Meeting scheduled
INSERT INTO outreach_communications (
  channel='email', direction='outbound',
  subject='CCV Call - Jan 20 at 2pm',
  sent_at='2024-01-16 10:00:00'
);

-- Communication #5: Call held
INSERT INTO outreach_communications (
  channel='phone', direction='outbound',
  body='Discovery call notes: Interested in buy program for all 3 courses...',
  sent_at='2024-01-20 14:00:00'
);

-- Communication #6: Proposal sent
INSERT INTO outreach_communications (
  channel='email', direction='outbound',
  subject='CCV Range Ball Buy Program - Proposal',
  body='Attached: Full proposal...',
  sent_at='2024-01-22 11:00:00'
);

-- Communication #7: Deal accepted!
INSERT INTO outreach_communications (
  channel='email', direction='inbound',
  response_text='Proposal looks great. Lets move forward.',
  response_sentiment='closed_won',
  received_at='2024-01-25 15:30:00'
);

-- Final update
UPDATE outreach_activities
SET status = 'closed_won',
    closed_at = NOW(),
    deal_value_usd = 15000.00,
    outcome = 'annual_contract_signed',
    total_touches = 7
WHERE id = 'activity-uuid';
```

### **ClickUp Actions (Track Everything):**
- Subtask #1 (Email 1): ✅ Complete - Opened Jan 15
- Subtask #2 (Response): ✅ Complete - Replied Jan 16
- Subtask #3 (Call): ✅ Complete - Call held Jan 20
- Subtask #4 (Proposal): ✅ Complete - Sent Jan 22
- Subtask #5 (Close): ✅ Complete - Won Jan 25
- Status → "Closed Won 🎉"
- Custom field "Deal Value" → $15,000
- Custom field "Outcome" → "Annual Contract Signed"
- Comment timeline shows full progression

### **Attribution Analysis (Critical for Optimization):**
```sql
-- What worked? Query the data:
SELECT
  conversation_starter_num as starter_used,
  target_segment,
  outreach_type,
  total_touches,
  EXTRACT(DAY FROM (closed_at - created_at)) as days_to_close,
  deal_value_usd
FROM outreach_activities
WHERE status = 'closed_won';

-- Results for this win:
-- Starter #1 (9/10 relevance)
-- Segment: High-End
-- Opportunity: Range Ball Buy
-- Touches: 7
-- Days: 10
-- Value: $15,000

-- Learning: Starter #1 works for high-end buy programs!
-- Future: Use Starter #1 more aggressively for similar profiles
```

### **ROI Calculation:**
```
Enrichment Cost: $0.2767 (7 contacts)
Outreach Cost: $0.15 (7 emails via SendGrid)
Total CAC: $0.43

Deal Value: $15,000/year
CAC: $0.43
ROI: 34,883% 🚀

Payback Period: Instant (first ball pickup covers CAC 35,000x over)
```

---

## 🚨 **Summary: Edge Case Response Matrix**

| Scenario | Detection | Supabase | ClickUp | Sales Action |
|----------|-----------|----------|---------|--------------|
| **Multi-channel pivot** | LinkedIn response after email fails | Log both channels, note preferred | Update subtasks, mark LinkedIn success | Continue on LinkedIn |
| **Wrong contact responds** | responder_email ≠ sent_to_email | Log both contacts, switch primary | Comment alert, create new contact | Thank referrer, continue with responder |
| **Contact left** | Auto-reply "no longer here" | Mark inactive, trigger replacement | Tag contact-left, create find-replacement task | Find new contact |
| **Multiple responders** | 3+ inbound from same thread | Log each separately | Multiple comments, create checklist | Respond to all, propose group call |
| **Late response** | Reply 30+ days after sequence ended | Reactivate sequence | Comment late response, re-engage status | Review context, respond fresh |
| **Opt-out** | "unsubscribe" keyword | IMMEDIATE blacklist, stop all | Tag do-not-contact, lock task | STOP all contact immediately |
| **Opportunity pivot** | Interested in different program | Note preferred opportunity | Create new task for new opp | Pivot pitch, maintain momentum |
| **Forward to new contact** | "forwarding to [name]" | Create new contact, new activity | Create new contact + outreach tasks | Thank referrer, engage new person |
| **Email bounce** | Hard bounce from provider | Invalidate email, clear field | Tag needs-re-enrichment, try LinkedIn | Use alternate channel |
| **Closed won** | Deal accepted | Complete audit trail, calculate ROI | Mark complete, track metrics | Celebrate! Analyze what worked |

---

## 📊 **Monitoring Queries (Daily Checks)**

### **Check for Opt-Outs (Daily):**
```sql
-- Any new opt-outs in last 24 hours?
SELECT * FROM opt_out_log
WHERE opted_out_at > NOW() - INTERVAL '24 hours';

-- Verify honored immediately
SELECT * FROM outreach_activities
WHERE primary_contact_id IN (SELECT contact_id FROM opt_out_log)
  AND status != 'opted_out';
-- Should return 0 rows!
```

### **Check for Contact Changes (Weekly):**
```sql
-- Who left companies recently?
SELECT * FROM contact_changes
WHERE change_type = 'left_company'
  AND detected_at > NOW() - INTERVAL '7 days';

-- Are replacements being found?
SELECT
  course_id,
  position_needed,
  created_at,
  CASE WHEN found_at IS NULL THEN 'PENDING' ELSE 'FOUND' END as status
FROM contact_replacement_queue
WHERE priority = 'high'
ORDER BY created_at DESC;
```

### **Check for Stuck Sequences:**
```sql
-- Sequences that should have executed but didn't
SELECT * FROM v_active_sequences
WHERE urgency = 'OVERDUE';

-- Investigate why (automation failure? Holiday? Manual pause?)
```

---

## 🎯 **Edge Case Prevention Strategies**

### **1. Email Validation (Before Sending):**
```sql
-- Don't send if email looks invalid
SELECT * FROM golf_course_contacts
WHERE email IS NOT NULL
  AND email_valid = false;  -- Skip these in outreach

-- Or: Verify with Hunter.io before first send
```

### **2. Contact Freshness (Monthly Check):**
```sql
-- Run Agent 8 on all active outreach contacts
SELECT id, name, linkedin_url
FROM golf_course_contacts
WHERE id IN (
  SELECT DISTINCT primary_contact_id
  FROM outreach_activities
  WHERE status IN ('active', 'scheduled', 'replied')
)
AND (last_validated_at IS NULL OR last_validated_at < NOW() - INTERVAL '30 days');

-- Agent 8 checks LinkedIn for job changes
-- Prevents "contact left" bounces
```

### **3. Duplicate Detection (Before Creating):**
```sql
-- Before creating outreach activity, check for duplicates
SELECT * FROM outreach_activities
WHERE course_id = 'ccv-uuid'
  AND outreach_type = 'range_ball_buy'
  AND status IN ('active', 'scheduled', 'replied');

-- If exists: Update existing instead of create new
```

### **4. Rate Limiting (Prevent Spam):**
```sql
-- Don't send to same contact more than once per 7 days
SELECT last_contact_at
FROM outreach_activities
WHERE primary_contact_id = 'contact-uuid'
ORDER BY last_contact_at DESC
LIMIT 1;

-- If last_contact_at < 7 days ago → SKIP
```

---

## 📚 **Related Documentation**

- **CLICKUP_ARCHITECTURE.md** - Field specifications
- **OUTREACH_TASK_TEMPLATE.md** - Rich description format
- **RELIABILITY_PLAYBOOK.md** - System operations
- **Migration 005** - Outreach tables schema

---

**Last Updated:** October 18, 2024
**Maintained By:** Engineering + Sales Ops
**Review Frequency:** Monthly (update as new edge cases discovered)
