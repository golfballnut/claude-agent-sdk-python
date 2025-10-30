# Outreach Automation - Quick Start Guide

**For:** Implementation team starting Agent 9-12 build
**Time to First Email:** 1 week
**Status:** Ready to build

---

## TL;DR - What We're Building

**Transform this:**
- 170 tasks in flat ClickUp list
- 10 manual emails/day (2-3 hours)
- 30% follow-up completion
- No reply tracking

**Into this:**
- 50 automated emails/day (15 min human time)
- 90%+ follow-up completion
- Automatic reply categorization
- Data-driven optimization

**How:** Build 4 agents (9, 10A, 10B, 11, 12) that draft, send, follow-up, and analyze

---

## Day 1: Setup (2 hours)

### 1. ClickUp Restructure (30 min)

**Add 6 statuses to list 901413111587:**

Go to: https://app.clickup.com/9014129779/v/li/901413111587/settings

```
1. 📥 Intake Queue (gray) - Default for new tasks
2. 📧 Ready to Send (blue) - Agent 10A places drafts here
3. ⏳ Sent (Waiting) (yellow) - Agent 10B marks after send
4. 💬 Replied (Action!) (green) - Agent 12 marks on INTERESTED reply
5. ✅ Qualified (Meeting) (purple) - Human marks when meeting booked
6. 📁 Closed (red) - Archive completed outreach
```

**Convert to Kanban board:**
- List view → Board view
- Group by: Status
- Sort "Intake Queue" by custom field: priority_score (descending)

**Bulk move existing tasks:**
- Move all 170 tasks → "Intake Queue" status
- This clears the clutter immediately

---

### 2. SendGrid Account (45 min)

**Create account:**
- Go to: https://sendgrid.com
- Start with free tier (100 emails/day)
- Plan to upgrade: $19.95/mo (after testing validates)

**Domain verification:**
1. Add domain: rangeballreconditioning.com
2. Add DNS records (SPF, DKIM, CNAME)
3. Verify (may take 24-48 hours)

**Create API key:**
- Settings → API Keys → Create
- Permissions: Full Access (Mail Send)
- Copy key → Save to password manager

**Configure webhooks:**
```
Inbound Parse:
  MX Record: mx.sendgrid.net
  URL: https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/analyze-reply-sentiment
  Spam Check: Disabled
  Send Raw: Enabled

Event Webhook:
  URL: https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/sendgrid-events
  Events: ✓ Delivered, ✓ Opened, ✓ Clicked, ✓ Bounced, ✓ Unsubscribed
```

---

### 3. Supabase Environment Variables (15 min)

Go to: https://supabase.com/dashboard/project/oadmysogtfopkbmrulmq/settings/functions

**Add secrets:**
```bash
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=steve@rangeballreconditioning.com
SENDGRID_FROM_NAME=Steve McMillion
SENDGRID_REPLY_TO=steve@rangeballreconditioning.com

# Optional: Slack integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL_HOT_LEADS=#sales-hot-leads
```

---

### 4. Database Setup (30 min)

**Create 4 new tables:**

Run this SQL in Supabase SQL Editor:

```sql
-- Table 1: Email drafts (Agent 10A output)
CREATE TABLE email_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id INTEGER REFERENCES golf_courses(id),
  contact_id UUID REFERENCES golf_course_contacts(id),
  outreach_activity_id UUID REFERENCES outreach_activities(activity_id),

  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  conversation_starter_num INTEGER,

  quality_score NUMERIC(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
  quality_flags JSONB,

  status TEXT CHECK (status IN ('draft', 'approved', 'sent', 'rejected', 'needs_review')),
  approved_by TEXT,
  approved_at TIMESTAMP WITH TIME ZONE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  sent_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_email_drafts_status ON email_drafts(status);
CREATE INDEX idx_email_drafts_quality ON email_drafts(quality_score);

-- Table 2: Send queue (Agent 9 output)
CREATE TABLE send_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  outreach_activity_id UUID REFERENCES outreach_activities(activity_id),
  course_id INTEGER REFERENCES golf_courses(id),
  priority_score NUMERIC(4,3),
  scheduled_send_at TIMESTAMP WITH TIME ZONE,
  status TEXT CHECK (status IN ('queued', 'sent', 'failed')),
  sent_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_send_queue_status ON send_queue(status);
CREATE INDEX idx_send_queue_scheduled ON send_queue(scheduled_send_at);

-- Table 3: Email templates (Agent 10A uses)
CREATE TABLE email_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_name TEXT NOT NULL,
  segment TEXT CHECK (segment IN ('high-end', 'budget', 'both')),
  subject_line_template TEXT NOT NULL,
  body_template TEXT NOT NULL,
  variables JSONB,
  variant TEXT,
  times_used INTEGER DEFAULT 0,
  total_opens INTEGER DEFAULT 0,
  total_replies INTEGER DEFAULT 0,
  avg_reply_rate NUMERIC(5,4),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 4: Agent execution logs (monitoring all agents)
CREATE TABLE agent_execution_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name TEXT NOT NULL,
  execution_type TEXT,
  status TEXT CHECK (status IN ('started', 'completed', 'failed')),
  input_params JSONB,
  output_result JSONB,
  error_message TEXT,
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  duration_seconds NUMERIC(10,3),
  anthropic_cost_usd NUMERIC(10,6),
  sendgrid_emails_sent INTEGER
);

CREATE INDEX idx_agent_logs_name ON agent_execution_logs(agent_name);
```

---

## Day 2-7: Build Agents (1 agent per day)

### Day 2: Agent 9 - Queue Prioritization

**Create:** `teams/golf-enrichment/supabase/functions/prioritize-send-queue/index.ts`

**Test locally:**
```bash
cd teams/golf-enrichment/supabase
supabase functions serve prioritize-send-queue
```

**Deploy:**
```bash
supabase functions deploy prioritize-send-queue
```

**Schedule with pg_cron:**
```sql
SELECT cron.schedule(
  'nightly-queue-prioritization',
  '0 0 * * *',  -- Midnight daily
  $$ SELECT net.http_post(
    url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/prioritize-send-queue',
    headers := '{"Content-Type": "application/json"}'::JSONB,
    body := '{}'::JSONB
  ); $$
);
```

**Validate:**
```sql
-- Check queue populated
SELECT COUNT(*) FROM send_queue WHERE status = 'queued';
-- Should be 50
```

---

### Day 3: Agent 10A - Email Drafter

**Create:** `teams/golf-enrichment/supabase/functions/generate-email-drafts/index.ts`

**Test:**
```bash
supabase functions serve generate-email-drafts

# Test with 1 course
curl -X POST http://localhost:54321/functions/v1/generate-email-drafts \
  -H "Content-Type: application/json" \
  -d '{"test_mode": true, "limit": 1}'
```

**Deploy:**
```bash
supabase functions deploy generate-email-drafts
```

**Schedule:**
```sql
SELECT cron.schedule(
  'morning-email-drafting',
  '0 8 * * *',  -- 8 AM daily
  $$ SELECT net.http_post(
    url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/generate-email-drafts',
    headers := '{"Content-Type": "application/json"}'::JSONB,
    body := '{}'::JSONB
  ); $$
);
```

**Validate:**
```sql
-- Check drafts created
SELECT
  COUNT(*) as total_drafts,
  AVG(quality_score) as avg_quality,
  COUNT(*) FILTER (WHERE quality_score >= 0.9) as high_quality
FROM email_drafts
WHERE created_at > NOW() - INTERVAL '1 day';
```

---

### Day 4: Agent 10B - Email Sender (Testing Mode)

**Create:** `teams/golf-enrichment/supabase/functions/send-approved-emails/index.ts`

**Configuration:**
```typescript
// Mode config (change this to switch modes)
const AGENT_10B_MODE = 'testing';  // 'testing' | 'hybrid' | 'production'
const AUTO_SEND_THRESHOLD = 0.9;
```

**ClickUp Webhook Setup:**
1. Go to: List Settings → Automations
2. Create automation:
   - Trigger: Status changes to "Approved"
   - Action: Webhook POST to:
     ```
     https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/send-approved-emails
     ```

**Deploy:**
```bash
supabase functions deploy send-approved-emails
```

**Test (manual trigger):**
```bash
# Approve a draft in ClickUp
# → Webhook fires → Email sends

# Or test directly:
curl -X POST https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/send-approved-emails \
  -H "Authorization: Bearer <anon_key>" \
  -d '{"draft_id": "your-draft-uuid"}'
```

**Validate:**
```sql
-- Check emails sent
SELECT * FROM outreach_communications
WHERE sent_at > NOW() - INTERVAL '1 hour'
ORDER BY sent_at DESC;

-- Check SendGrid message IDs present
SELECT
  COUNT(*) as total_sent,
  COUNT(*) FILTER (WHERE email_message_id IS NOT NULL) as has_sendgrid_id
FROM outreach_communications
WHERE sent_at > NOW() - INTERVAL '1 day';
```

---

### Day 5: Agent 11 - Follow-Up Scheduler

**Create:** `teams/golf-enrichment/supabase/functions/create-followup-sequence/index.ts`

**Called by Agent 10B** (not scheduled independently)

**Deploy:**
```bash
supabase functions deploy create-followup-sequence
```

**Test:**
```sql
-- After Agent 10B sends an email, check follow-ups created
SELECT
  oa.activity_id,
  os.total_steps,
  os.next_scheduled_at,
  COUNT(oc.id) as scheduled_followups
FROM outreach_sequences os
JOIN outreach_activities oa ON oa.activity_id = os.outreach_activity_id
LEFT JOIN outreach_communications oc ON oc.outreach_activity_id = os.outreach_activity_id
  AND oc.status = 'scheduled'
WHERE os.created_at > NOW() - INTERVAL '1 day'
GROUP BY oa.activity_id, os.total_steps, os.next_scheduled_at;

-- Should show 3 scheduled follow-ups per course
```

**Schedule auto-sender:**
```sql
-- Check for due follow-ups every 3 hours
SELECT cron.schedule(
  'auto-followup-sender',
  '0 9,12,15,18 * * *',  -- 9 AM, 12 PM, 3 PM, 6 PM
  $$ SELECT net.http_post(
    url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/send-scheduled-followups',
    headers := '{"Content-Type": "application/json"}'::JSONB,
    body := '{}'::JSONB
  ); $$
);
```

---

### Day 6: Agent 12 - Reply Analyzer

**Create:** `teams/golf-enrichment/supabase/functions/analyze-reply-sentiment/index.ts`

**Deploy:**
```bash
supabase functions deploy analyze-reply-sentiment --no-verify-jwt
# Note: --no-verify-jwt required for external webhooks
```

**SendGrid webhook already configured on Day 1** ✓

**Test (simulate reply):**
```bash
# Send test email to yourself
# Reply to it
# Check if Agent 12 categorizes correctly

# Or test directly:
curl -X POST https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/analyze-reply-sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "from": "phil.kiester@theccv.org",
    "to": "steve@rangeballreconditioning.com",
    "subject": "Re: CCV + Range Ball Revenue Opportunity",
    "text": "Thanks for reaching out! This sounds interesting. Lets schedule a call next week.",
    "headers": {
      "In-Reply-To": "<test-message-id@sendgrid.net>"
    }
  }'
```

**Validate:**
```sql
-- Check replies categorized
SELECT
  response_sentiment,
  COUNT(*) as count
FROM outreach_communications
WHERE direction = 'inbound'
  AND received_at > NOW() - INTERVAL '1 day'
GROUP BY response_sentiment;

-- Should show: INTERESTED, NOT_NOW, etc.
```

---

## Day 7: End-to-End Testing

### Test Scenario 1: Complete Flow (Single Course)

**1. Queue one course manually:**
```sql
INSERT INTO send_queue (
  outreach_activity_id,
  course_id,
  priority_score,
  scheduled_send_at,
  status
) VALUES (
  (SELECT activity_id FROM outreach_activities LIMIT 1),
  (SELECT id FROM golf_courses WHERE enrichment_status = 'completed' LIMIT 1),
  0.95,
  NOW() + INTERVAL '1 minute',  -- Send in 1 minute (for testing)
  'queued'
);
```

**2. Trigger Agent 10A manually:**
```bash
curl -X POST https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/generate-email-drafts \
  -H "Authorization: Bearer <anon_key>"
```

**3. Check draft created:**
```sql
SELECT subject, body, quality_score, status FROM email_drafts ORDER BY created_at DESC LIMIT 1;
```

**4. Approve draft in ClickUp:**
- Go to task
- Review draft
- Change status to "Approved"

**5. Wait for Agent 10B (webhook trigger):**
- Email should send automatically
- Check SendGrid dashboard

**6. Verify follow-ups created:**
```sql
SELECT * FROM outreach_sequences WHERE created_at > NOW() - INTERVAL '5 minutes';
-- Should have 1 sequence with 3 scheduled communications
```

**7. Test reply (send yourself):**
- Reply to the email you received
- Check Agent 12 categorizes it

---

## Week 2: 100-Course Test

### Monday - Queue 100 Courses

```sql
-- Let Agent 9 do this, or manually:
INSERT INTO send_queue (outreach_activity_id, course_id, priority_score, scheduled_send_at, status)
SELECT
  oa.activity_id,
  oa.golf_course_id,
  0.8 + (RANDOM() * 0.2), -- Random score 0.8-1.0
  CURRENT_DATE + INTERVAL '1 day' + INTERVAL '8 hours', -- Tomorrow 8 AM
  'queued'
FROM outreach_activities oa
WHERE oa.status = 'scheduled'
ORDER BY RANDOM()
LIMIT 100;
```

---

### Tuesday-Friday - Send 20/Day

**Agent 10A runs automatically at 8 AM** (drafts 20 emails)

**Your workflow (8:30 AM):**
1. Open ClickUp "Ready to Send" column (20 tasks)
2. Spot-check 4 emails (20% sample, 2 min each = 8 min)
3. Click "Approve All" (bulk action)
4. Agent 10B sends emails automatically (webhook trigger)

**Time: 10-15 min/day**

---

### Monitor Metrics

**Daily (5 min):**
```sql
-- Check today's sends
SELECT
  DATE(sent_at) as date,
  COUNT(*) as emails_sent,
  COUNT(*) FILTER (WHERE delivered_at IS NOT NULL) as delivered,
  COUNT(*) FILTER (WHERE opened_at IS NOT NULL) as opened,
  COUNT(*) FILTER (WHERE direction = 'inbound') as replies
FROM outreach_communications
WHERE sent_at > CURRENT_DATE
GROUP BY DATE(sent_at);
```

**Weekly (30 min):**
```sql
-- Quality score distribution
SELECT
  CASE
    WHEN quality_score >= 0.95 THEN 'Excellent (0.95+)'
    WHEN quality_score >= 0.9 THEN 'Good (0.9-0.94)'
    WHEN quality_score >= 0.8 THEN 'Fair (0.8-0.89)'
    ELSE 'Poor (<0.8)'
  END as quality_tier,
  COUNT(*) as count,
  ROUND(AVG(quality_score), 3) as avg_score
FROM email_drafts
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY quality_tier
ORDER BY avg_score DESC;

-- Reply rate analysis
SELECT
  COUNT(*) as emails_sent,
  COUNT(*) FILTER (WHERE opened_at IS NOT NULL) as opened,
  COUNT(*) FILTER (WHERE direction = 'inbound') as replied,
  ROUND(COUNT(*) FILTER (WHERE opened_at IS NOT NULL) * 100.0 / COUNT(*), 2) as open_rate,
  ROUND(COUNT(*) FILTER (WHERE direction = 'inbound') * 100.0 / COUNT(*), 2) as reply_rate
FROM outreach_communications
WHERE sent_at > NOW() - INTERVAL '7 days'
  AND direction = 'outbound';
```

---

## Week 3: Enable Hybrid Mode

**If Week 2 results show:**
- ✅ Average quality_score >= 0.85
- ✅ < 10% of emails needed human edits
- ✅ Reply rate >= 8%

**Then enable hybrid mode:**

```typescript
// Update in send-approved-emails/index.ts
const AGENT_10B_MODE = 'hybrid';  // Changed from 'testing'
const AUTO_SEND_THRESHOLD = 0.9;
```

**Redeploy Agent 10B:**
```bash
supabase functions deploy send-approved-emails
```

**Also schedule pg_cron (instead of webhook):**
```sql
SELECT cron.schedule(
  'hybrid-email-sender',
  '15 8 * * *',  -- 8:15 AM daily (15 min after drafts)
  $$ SELECT net.http_post(
    url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/send-approved-emails',
    headers := '{"Content-Type": "application/json"}'::JSONB,
    body := '{"mode": "hybrid"}'::JSONB
  ); $$
);
```

**New workflow:**
- 8:00 AM: Agent 10A drafts 30 emails
- 8:15 AM: Agent 10B auto-sends ~24 (quality >= 0.9)
- 8:16 AM: Slack notifies you of 6 that need review
- 8:20 AM: You review 6 emails, approve (10 min)
- 8:30 AM: All 30 sent

**Time: 10-15 min/day**

---

## Troubleshooting

### Agent 10A: No drafts created

**Check:**
```sql
SELECT * FROM send_queue WHERE status = 'queued' LIMIT 5;
-- If empty, Agent 9 didn't run
```

**Solution:**
```sql
-- Check pg_cron
SELECT * FROM cron.job WHERE jobname = 'nightly-queue-prioritization';

-- Manually trigger Agent 9
SELECT net.http_post(
  url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/prioritize-send-queue'
);
```

---

### Agent 10B: Emails not sending

**Check mode:**
```typescript
// In send-approved-emails/index.ts
console.log('AGENT_10B_MODE:', AGENT_10B_MODE);
// If 'testing', you must approve in ClickUp first
```

**Check logs:**
```bash
supabase functions logs send-approved-emails --tail
```

**Common issues:**
- SendGrid API key not set → Add to Supabase secrets
- Domain not verified → Wait 24-48 hours for DNS
- Draft status not 'approved' → Check ClickUp workflow

---

### Agent 12: Replies not categorized

**Check webhook:**
```bash
# SendGrid → Settings → Mail Settings → Inbound Parse
# Verify URL is correct

# Test webhook manually
curl -X POST https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/analyze-reply-sentiment \
  -H "Content-Type: application/json" \
  -d @test_reply_payload.json
```

**Check logs:**
```sql
SELECT * FROM agent_execution_logs
WHERE agent_name = 'Agent 12'
ORDER BY started_at DESC
LIMIT 10;
```

---

## Quick Commands

### Manual Trigger Agent 9
```bash
curl -X POST https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/prioritize-send-queue
```

### Manual Trigger Agent 10A
```bash
curl -X POST https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/generate-email-drafts
```

### Check Today's Queue
```sql
SELECT COUNT(*) FROM send_queue
WHERE scheduled_send_at::DATE = CURRENT_DATE
AND status = 'queued';
```

### Check Draft Quality
```sql
SELECT
  ROUND(AVG(quality_score), 3) as avg_quality,
  MIN(quality_score) as min_quality,
  MAX(quality_score) as max_quality
FROM email_drafts
WHERE created_at > NOW() - INTERVAL '1 day';
```

### Check Emails Sent Today
```sql
SELECT COUNT(*) FROM outreach_communications
WHERE sent_at::DATE = CURRENT_DATE;
```

### Pause Automation
```sql
-- Disable all cron jobs
UPDATE cron.job SET active = FALSE;
```

### Resume Automation
```sql
-- Enable all cron jobs
UPDATE cron.job SET active = TRUE;
```

---

## Success Checklist

**After Week 1 (Build Complete):**
- [ ] All 5 edge functions deployed
- [ ] All 4 tables created
- [ ] pg_cron jobs scheduled
- [ ] SendGrid webhooks configured
- [ ] ClickUp statuses added
- [ ] End-to-end test passes (1 course)

**After Week 2 (100 Courses Tested):**
- [ ] 100 emails sent with <10% manual edits
- [ ] Average quality score >= 0.85
- [ ] Reply rate >= 8%
- [ ] Zero spam complaints
- [ ] Follow-ups auto-created (90%+ completion)
- [ ] Ready to scale to hybrid mode

**After Week 4 (50/Day Sustained):**
- [ ] 50 emails/day for 5 consecutive days
- [ ] Human time < 30 min/day
- [ ] Reply rate maintained >= 10%
- [ ] Quality score stable >= 0.9
- [ ] Team satisfaction >= 4/5

---

## File Structure (After Build)

```
teams/golf-enrichment/
├── supabase/
│   └── functions/
│       ├── prioritize-send-queue/          (Agent 9)
│       │   └── index.ts
│       ├── generate-email-drafts/          (Agent 10A)
│       │   └── index.ts
│       ├── send-approved-emails/           (Agent 10B)
│       │   └── index.ts
│       ├── create-followup-sequence/       (Agent 11)
│       │   └── index.ts
│       ├── send-scheduled-followups/       (Agent 11 - sender mode)
│       │   └── index.ts
│       └── analyze-reply-sentiment/        (Agent 12)
│           └── index.ts
├── tests/
│   └── outreach/
│       ├── test_agent9_prioritization.py
│       ├── test_agent10a_drafting.py
│       ├── test_agent10b_sending.py
│       ├── test_agent11_followups.py
│       └── test_agent12_sentiment.py
└── docs/
    └── 1_IMPLEMENTATION/
        ├── OUTREACH_AUTOMATION_PRD.md (Full spec)
        ├── OUTREACH_QUICK_START.md (This file)
        └── 10_24_25_outreach_proposed_flow.md (Context)
```

---

**Ready to build? Start with Day 1 setup, then one agent per day!**

**Questions:** See full PRD in `OUTREACH_AUTOMATION_PRD.md`
