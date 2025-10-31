# Product Requirements Document: Outreach Automation Agent System

**Project:** Golf Course Outreach Funnel Automation
**Version:** 3.0 (Landing Pages + Form Self-Qualification)
**Date:** October 24, 2025
**Status:** ✅ Ready for Agent Implementation
**Owner:** Golf Enrichment Team
**Target:** Scale from 10 outreaches/day → 50+ outreaches/day with full automation

**Major Features:**
- 8 Agents (9, 10A, 10B, 10.5, 11, 12, 13, 14)
- Personalized landing pages with embedded forms
- AI-powered lead qualification and routing
- 15X conversion improvement (0.4% → 4.2%)

---

## Executive Summary

Build an intelligent, automated outreach funnel that takes enriched golf course data from Supabase and executes personalized email campaigns at scale with minimal human intervention. The system will handle email drafting, sending, follow-up scheduling, reply detection, and lead qualification automatically.

**Current State:**
- 185 enriched courses ready for outreach
- 170 ClickUp tasks created (all in "scheduled" status)
- Manual process: 10 courses/day, 2-3 hours/day
- Bottlenecks: Email drafting, decision paralysis (170 tasks), follow-up tracking

**Target State:**
- 50 automated outreaches/day
- 30-40 automated follow-ups/day
- Human time: 30-45 min/day (replies only)
- 99% cost reduction vs manual process

---

## Business Objectives

### Primary Goals
1. **Scale outreach volume 5x** (10/day → 50/day) without increasing headcount
2. **Reduce time per outreach 90%** (15-20 min → 2-3 min)
3. **Increase follow-up completion rate** (30% → 90%+)
4. **Automatic lead qualification** (AI categorizes all replies)
5. **Data-driven optimization** (A/B test subject lines, conversation starters, timing)

### Success Metrics (After 30 Days)
- **Volume:** 1,000 new outreaches sent (50/day × 20 working days)
- **Time savings:** 25 hours/week saved on email drafting
- **Reply rate:** > 10% (vs 2-5% industry average)
- **Follow-up completion:** > 90% (vs 30% manual)
- **Cost per outreach:** < $0.22 (enrichment + email automation)
- **Human intervention:** < 1 hour/day (only for interested replies)

### Out of Scope (Phase 2)
- LinkedIn automation (focus on email only)
- Phone call automation
- CRM integration beyond ClickUp
- Contract negotiation workflow
- Payment processing

---

## System Architecture

### Visual Flow: How Email Drafting Works

```
AGENT 10A: EMAIL DRAFTER (Always Runs First)
═══════════════════════════════════════════════════════════
Runs: 8:00 AM daily (pg_cron)
Input: 50 courses from send_queue

┌─────────────────────────────────────────────────────────┐
│ FOR EACH of 50 courses:                                 │
│                                                          │
│ 1. Query Supabase:                                      │
│    - golf_courses (course data)                         │
│    - golf_course_contacts (primary contact)             │
│    - business_intelligence (conversation starters)      │
│                                                          │
│ 2. Call Claude API:                                     │
│    Prompt: "Generate personalized email using           │
│            conversation starter #1 for {contact_name}   │
│            at {course_name}..."                         │
│    Output: {subject, body}                              │
│                                                          │
│ 3. Quality Check:                                       │
│    - Name matches? ✓                                    │
│    - Course name present? ✓                             │
│    - Word count 150-250? ✓                              │
│    - No spam words? ✓                                   │
│    - Has CTA? ✓                                         │
│    → Quality Score: 0.92 (out of 1.0)                   │
│                                                          │
│ 4. Store Draft:                                         │
│    INSERT INTO email_drafts (                           │
│      subject, body, quality_score, status='draft'       │
│    )                                                     │
│                                                          │
│ 5. Update ClickUp:                                      │
│    Status → "Ready to Send"                             │
│    Add draft to task description                        │
│                                                          │
└─────────────────────────────────────────────────────────┘

Output: 50 drafts stored, ready for Agent 10B
Cost: ~$0.05 (50 Claude API calls @ $0.001 each)
Time: 5-10 minutes
```

```
AGENT 10B: EMAIL SENDER (Mode-Dependent Behavior)
═══════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│ MODE 1: TESTING (Week 1-2)                              │
│ Trigger: ClickUp webhook (human clicks "Approve")      │
│                                                          │
│ Human Workflow:                                         │
│ 8:30 AM - Review 50 drafts in ClickUp                  │
│ 8:35 AM - Spot-check 10 emails (20% sample)            │
│ 8:45 AM - Click "Approve All" button                   │
│           ↓                                              │
│ ClickUp webhook fires → Agent 10B                       │
│           ↓                                              │
│ Agent 10B sends all 50 emails via SendGrid              │
│                                                          │
│ Time: 15-20 min/day                                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ MODE 2: HYBRID (Week 3-4)                               │
│ Trigger: pg_cron at 8:15 AM (15 min after drafts)      │
│                                                          │
│ Agent 10B Logic:                                        │
│ 1. Query all drafts (50 total)                         │
│                                                          │
│ 2. Route by quality score:                             │
│    ├─ 40 drafts with score >= 0.9                      │
│    │  → AUTO-SEND immediately                           │
│    │                                                     │
│    └─ 10 drafts with score < 0.9                       │
│       → Flag "Review Needed" in ClickUp                 │
│       → Slack notification to sales team                │
│       → Wait for human approval                         │
│                                                          │
│ Human Workflow:                                         │
│ 8:30 AM - Review 10 flagged emails (10-15 min)         │
│ 8:45 AM - Approve reviewed emails                      │
│           ↓                                              │
│ Agent 10B sends approved batch                          │
│                                                          │
│ Total sent: 50 emails (40 auto + 10 after review)      │
│ Time: 10-15 min/day                                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ MODE 3: PRODUCTION (Week 5+, Optional)                  │
│ Trigger: pg_cron at 8:15 AM                             │
│                                                          │
│ Agent 10B Logic:                                        │
│ 1. Query all drafts (50 total)                         │
│                                                          │
│ 2. AUTO-SEND all 50 emails                             │
│                                                          │
│ 3. Random 5% sample (2-3 emails):                       │
│    → Flag for post-send audit                           │
│    → Human reviews for quality monitoring               │
│                                                          │
│ Human Workflow:                                         │
│ End of day - Review 2-3 emails (5 min)                 │
│                                                          │
│ Total sent: 50 emails (100% automated)                  │
│ Time: 5 min/day (audit only)                           │
└─────────────────────────────────────────────────────────┘
```

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ NIGHTLY BATCH (12 AM): Agent 9 - Queue Prioritization          │
│   - Score 170 courses in Supabase (opportunity + segment)      │
│   - Select top 50 for tomorrow                                 │
│   - INSERT into send_queue table                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ MORNING BATCH (8 AM): Agent 10 - Email Generation & Sending    │
│   - For each of 50 courses in send_queue                       │
│   - Generate personalized email from conversation starters     │
│   - Send via SendGrid API                                      │
│   - Log to outreach_communications table                       │
│   - Update ClickUp status → "Sent (Waiting)"                   │
│   - Trigger Agent 11 to create follow-up tasks                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ REAL-TIME: Agent 12 - Reply Analysis                           │
│   - Webhook from SendGrid on email reply                       │
│   - Claude analyzes sentiment & intent                         │
│   - Categorize: Interested | Not Now | No | Wrong Contact      │
│   - Update Supabase + ClickUp                                  │
│   - Notify human if INTERESTED (Slack/ClickUp)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ SCHEDULED: Agent 11 - Automatic Follow-Ups (Day 3, 7, 14)      │
│   - Query: follow_up_date = TODAY                              │
│   - Generate follow-up email (different conversation starter)  │
│   - Send automatically via SendGrid                            │
│   - Log to DB, update ClickUp                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Supabase Tables (Source of Truth)
├── golf_courses (185 enriched)
├── golf_course_contacts (363 contacts)
├── outreach_activities (170 campaigns)
├── outreach_communications (all emails sent/received)
├── outreach_sequences (follow-up state machine)
└── send_queue (daily batch queue)
        ↓
Edge Functions (Business Logic)
├── prioritize-send-queue (Agent 9)
├── generate-and-send-email (Agent 10)
├── create-followup-sequence (Agent 11)
└── analyze-reply-sentiment (Agent 12)
        ↓
External Services
├── SendGrid (email delivery + webhooks)
├── ClickUp (task management for humans)
└── Slack (notifications for hot leads)
```

---

## Component Specifications

## Agent 9: Queue Prioritization Engine

### Purpose
Intelligently select the top 50 courses from 170-course backlog each night based on opportunity score, segment, region, and age.

### Technical Specs

**Edge Function:** `prioritize-send-queue`

**Trigger:** pg_cron daily at 12:00 AM

**Input:** None (queries Supabase directly)

**Processing Logic:**
```python
def prioritize_send_queue():
    # Query all scheduled outreach activities
    activities = supabase.from_('outreach_activities') \
        .select('*, golf_courses(*), golf_course_contacts(*)') \
        .eq('status', 'scheduled') \
        .execute()

    # Score each activity
    scored = []
    for activity in activities:
        score = calculate_priority_score(activity)
        scored.append((activity, score))

    # Select top 50
    top_50 = sorted(scored, key=lambda x: x[1], reverse=True)[:50]

    # Insert into send_queue
    for activity, score in top_50:
        supabase.from_('send_queue').insert({
            'outreach_activity_id': activity.id,
            'course_id': activity.golf_course_id,
            'priority_score': score,
            'scheduled_send_at': datetime.now() + timedelta(hours=8),  # 8 AM tomorrow
            'status': 'queued'
        }).execute()

    return {'queued_count': 50, 'total_scored': len(activities)}

def calculate_priority_score(activity):
    """
    Scoring algorithm:
    - Opportunity Score: 40% (from Agent 6)
    - Segment Value: 30% (high-end=1.0, budget=0.7, both=0.85)
    - Region Balance: 20% (underserved regions get boost)
    - Age in Queue: 10% (FIFO tiebreaker)
    """
    course = activity.golf_courses

    # Component 1: Opportunity score (1-10 scale)
    opp_score = activity.opportunity_score / 10 * 0.4

    # Component 2: Segment value
    segment_values = {'high-end': 1.0, 'both': 0.85, 'budget': 0.7}
    segment_score = segment_values.get(activity.target_segment, 0.7) * 0.3

    # Component 3: Region balance (query outreach by region, boost underserved)
    region_count = get_region_outreach_count(course.state_code)
    region_score = (1 - min(region_count / 50, 1)) * 0.2  # Diminishing returns

    # Component 4: Age (days in queue / 30) capped at 1.0
    age_days = (datetime.now() - activity.created_at).days
    age_score = min(age_days / 30, 1.0) * 0.1

    return opp_score + segment_score + region_score + age_score
```

**Output:**
- Inserts 50 records into `send_queue` table
- Returns summary: `{queued_count: 50, total_scored: 170}`

**Error Handling:**
- If < 50 courses available, queue all available
- If scoring fails for a course, assign default score of 0.5
- Log all errors to `agent_execution_logs` table

**Testing Requirements:**
- Unit test: Scoring algorithm with known inputs
- Integration test: End-to-end queue population
- Edge case: Handle empty queue, single course, 1000+ courses

---

## Agent 10: Email Automation (Split into 10A + 10B)

### Why Split Agent 10?

**Rationale:** Separating drafting from sending enables progressive automation with quality gates.

**Benefits:**
- ✅ Safety during testing (human can catch bad AI outputs)
- ✅ Clear path to full automation (change mode, not code)
- ✅ Quality metrics to validate AI performance
- ✅ Easy rollback if quality drops

**Progressive Modes:**
```
Week 1-2: TESTING MODE
  Agent 10A drafts → Human reviews 100% → Human approves → Agent 10B sends

Week 3-4: HYBRID MODE
  Agent 10A drafts → Quality score >= 0.9?
    ├─ YES (80%) → Agent 10B auto-sends
    └─ NO (20%) → Human reviews → Agent 10B sends after approval

Week 5+: PRODUCTION MODE (Optional)
  Agent 10A drafts → Agent 10B auto-sends all → 5% random audit
```

---

## Agent 10A: Email Draft Generator

### Purpose
Generate personalized email drafts from conversation starters and course intelligence. Store drafts for approval (testing phase) or quality scoring (production phase).

### Technical Specs

**Edge Function:** `generate-email-drafts`

**Trigger:** pg_cron daily at 8:00 AM (batch processing)

**Input:** Records from `send_queue` where `status = 'queued'` and `scheduled_send_at <= NOW()`

**Processing Logic:**
```python
async def generate_email_drafts():
    # Get today's batch
    queue_items = supabase.from_('send_queue') \
        .select('*, outreach_activities(*, golf_courses(*), golf_course_contacts(*))') \
        .eq('status', 'queued') \
        .lte('scheduled_send_at', datetime.now()) \
        .execute()

    results = {'drafts_created': 0, 'failed': 0, 'errors': []}

    for item in queue_items:
        try:
            # Generate email draft
            email = await generate_email(item)

            # Calculate quality score
            quality_score = await calculate_quality_score(email, item)

            # Store draft (don't send yet)
            draft = await supabase.from_('email_drafts').insert({
                'course_id': item.course_id,
                'contact_id': item.contact_id,
                'outreach_activity_id': item.outreach_activity_id,
                'subject': email['subject'],
                'body': email['body'],
                'conversation_starter_num': 1,
                'quality_score': quality_score.score,
                'quality_flags': quality_score.flags,
                'status': 'draft',
                'created_at': datetime.now()
            }).execute()

            # Update ClickUp with draft preview
            await update_clickup_with_draft(item.outreach_activity_id, email, quality_score)

            results['drafts_created'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append(str(e))

    return results

async def calculate_quality_score(email, queue_item):
    """
    Calculate quality score (0.0-1.0) for auto-send routing
    """
    activity = queue_item.outreach_activities
    contact = activity.golf_course_contacts
    course = activity.golf_courses

    score = 1.0
    flags = []

    # Check 1: Contact name present and correct
    if contact.name.lower() not in email['body'].lower():
        score -= 0.3
        flags.append('missing_contact_name')

    # Check 2: Course name present
    if course.name.lower() not in email['body'].lower():
        score -= 0.3
        flags.append('missing_course_name')

    # Check 3: Word count (150-250 ideal)
    word_count = len(email['body'].split())
    if word_count < 100:
        score -= 0.2
        flags.append('too_short')
    elif word_count > 300:
        score -= 0.1
        flags.append('too_long')

    # Check 4: Spam trigger words
    spam_words = ['buy now', 'limited time', 'act fast', 'guaranteed', 'free money']
    if any(word in email['body'].lower() for word in spam_words):
        score -= 0.2
        flags.append('spam_words')

    # Check 5: Has call-to-action
    cta_phrases = ['call', 'meeting', 'conversation', 'discuss', 'explore']
    if not any(phrase in email['body'].lower() for phrase in cta_phrases):
        score -= 0.1
        flags.append('missing_cta')

    # Check 6: Conversation starter used correctly
    intel = await get_business_intelligence(contact.id)
    starter_text = intel.conversation_starters[0]['text'][:50]  # First 50 chars
    if starter_text.lower() not in email['body'].lower():
        score -= 0.15
        flags.append('starter_not_used')

    return {'score': max(0.0, score), 'flags': flags}

async def generate_email(queue_item):
    """
    Use Claude to generate personalized email
    """
    activity = queue_item.outreach_activities
    course = activity.golf_courses
    contact = activity.golf_course_contacts  # Primary contact

    # Get conversation starters from business_intelligence table
    intel = supabase.from_('business_intelligence') \
        .select('conversation_starters') \
        .eq('contact_id', contact.id) \
        .single() \
        .execute()

    starters = intel.data['conversation_starters']
    top_starter = starters[0]  # Use highest-ranked starter

    # Get email template for this segment
    template = get_email_template(
        segment=activity.target_segment,
        outreach_type=activity.outreach_type
    )

    # Generate email using Claude
    prompt = f"""
    Generate a personalized outreach email for this golf course contact.

    **Contact:**
    - Name: {contact.name}
    - Title: {contact.title}
    - Course: {course.name}

    **Business Context:**
    - Segment: {activity.target_segment}
    - Opportunity: {activity.outreach_type} ({activity.opportunity_score}/10 score)
    - Top conversation starter: {top_starter['text']}

    **Template:**
    {template.body_template}

    **Requirements:**
    1. Use the conversation starter as the opening
    2. Keep email under 200 words
    3. Include specific numbers/data from course intelligence
    4. End with clear call-to-action (15-min call)
    5. Professional but conversational tone
    6. Include P.S. with secondary opportunity if relevant

    Return:
    - subject_line (max 60 chars)
    - email_body (plain text, < 200 words)
    """

    response = await claude_sdk.query(prompt)

    return {
        'to_email': contact.email,
        'to_name': contact.name,
        'subject': response.subject_line,
        'body': response.email_body,
        'from_email': 'steve@rangeballreconditioning.com',  # Config
        'from_name': 'Steve McMillion',  # Config
        'reply_to': 'steve@rangeballreconditioning.com',
        'conversation_starter_num': 1,
        'template_id': template.id
    }

async def send_via_sendgrid(email):
    """
    Send email via SendGrid API
    """
    sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

    message = Mail(
        from_email=Email(email['from_email'], email['from_name']),
        to_emails=To(email['to_email'], email['to_name']),
        subject=email['subject'],
        plain_text_content=email['body']
    )

    # Add unsubscribe footer (CAN-SPAM compliance)
    message.add_content(Content('text/plain', '\n\n---\n' + get_unsubscribe_footer()))

    # Enable tracking
    message.tracking_settings = TrackingSettings(
        click_tracking=ClickTracking(enable=True),
        open_tracking=OpenTracking(enable=True)
    )

    try:
        response = sendgrid_client.send(message)
        return {'success': True, 'message_id': response.headers['X-Message-Id']}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

**Output:**
- Creates 50 draft records in `email_drafts` table
- Each draft includes quality score (0.0-1.0)
- Updates ClickUp tasks with draft preview
- Returns: `{drafts_created: 50, avg_quality_score: 0.92}`

**Quality Score Routing:**
- **Score >= 0.95:** Auto-send approved (production phase)
- **Score 0.80-0.94:** Human review recommended
- **Score < 0.80:** Must review (likely has errors)

---

## Agent 10B: Email Sender (Progressive Modes)

### Purpose
Send emails via SendGrid with progressive automation: manual approval (testing) → hybrid auto-send (scale) → full automation (production).

### Technical Specs

**Edge Function:** `send-approved-emails`

**Triggers (Mode-Dependent):**
- **Testing Mode (Week 1-2):** ClickUp webhook when status → "Approved"
- **Hybrid Mode (Week 3-4):** pg_cron at 8:15 AM (auto-send quality_score >= 0.9)
- **Production Mode (Week 5+):** pg_cron at 8:15 AM (auto-send all)

**Input:**
- Testing: Single `draft_id` from ClickUp webhook
- Hybrid/Production: Query `email_drafts` where `status = 'draft'`

**Processing Logic:**
```python
async def send_approved_emails(mode='testing'):
    """
    Send emails based on current automation mode
    """
    if mode == 'testing':
        # TESTING MODE: Only send manually approved drafts
        drafts = await get_approved_drafts()  # Human clicked "Approve"

    elif mode == 'hybrid':
        # HYBRID MODE: Auto-send high-quality, route low-quality to review
        all_drafts = await get_pending_drafts()

        high_quality = [d for d in all_drafts if d.quality_score >= 0.9]
        needs_review = [d for d in all_drafts if d.quality_score < 0.9]

        # Auto-send high-quality
        drafts = high_quality

        # Flag low-quality for human review
        for draft in needs_review:
            await flag_for_human_review(draft)

    elif mode == 'production':
        # PRODUCTION MODE: Auto-send all, 5% random sample for audit
        all_drafts = await get_pending_drafts()
        drafts = all_drafts

        # Random 5% sample for quality monitoring
        sample = random.sample(all_drafts, max(1, int(len(all_drafts) * 0.05)))
        for draft in sample:
            await flag_for_audit(draft)

    # Send emails via SendGrid
    results = {'sent': 0, 'failed': 0}

    for draft in drafts:
        try:
            send_result = await send_via_sendgrid(draft)

            if send_result.success:
                # Log communication
                await log_outreach_communication(draft, send_result)

                # Create follow-up sequence
                await trigger_agent_11(draft.outreach_activity_id)

                # Update ClickUp status
                await update_clickup_status(draft.outreach_activity_id, 'Sent (Waiting)')

                # Mark draft as sent
                await mark_draft_sent(draft.id)

                results['sent'] += 1
            else:
                results['failed'] += 1

        except Exception as e:
            results['failed'] += 1
            await log_error(draft.id, str(e))

    return results

async def flag_for_human_review(draft):
    """Flag low-quality draft for human review"""
    await supabase.from_('email_drafts').update({
        'status': 'needs_review',
        'flagged_at': datetime.now()
    }).eq('id', draft.id).execute()

    await clickup.update_task(draft.clickup_task_id, {
        'status': 'Review Needed',
        'priority': 'high'
    })

    # Optional: Slack notification
    await slack.notify(f"⚠️ Email needs review: {draft.course_name} (quality: {draft.quality_score})")
```

**Output:**
- Sends X emails via SendGrid (X depends on mode)
- Logs each email to `outreach_communications` table
- Updates `send_queue` status to 'sent'
- Triggers Agent 11 for follow-up creation
- Returns: `{sent: 48, failed: 2, needs_review: 5}`

**Email Template Structure:**
```
Subject: {Course Name} + {Value Prop} | Quick Question

Hi {FirstName},

{Conversation Starter - personalized with course-specific data}

{Problem/Opportunity identified by Agent 6 - 2-3 sentences}

{Our unique value proposition - 1-2 sentences}

{Call to action - 15-min call request}

Best regards,
{Your Name}
{Title}
{Phone}

P.S. {Secondary opportunity if relevant, e.g., ball retrieval}

---
[Unsubscribe link | Physical address | Privacy policy]
```

**Error Handling:**
- Retry failed sends 3 times with exponential backoff
- Mark failed items in send_queue with error message
- Alert admin if > 10% failure rate
- Continue batch even if some emails fail

**Testing Requirements:**
- Unit test: Email generation with various inputs
- Unit test: Template variable substitution
- Integration test: SendGrid API call (use test mode)
- A/B test: Subject line variants (track in DB)

---

## Agent 11: Follow-Up Sequence Creator

### Purpose
Automatically create follow-up tasks (Day 3, 7, 14) when initial email is sent.

### Technical Specs

**Edge Function:** `create-followup-sequence`

**Trigger:** Called by Agent 10 after successful email send

**Input:** `outreach_activity_id` (UUID)

**Processing Logic:**
```python
def create_followup_sequence(outreach_activity_id):
    """
    Create 3 automated follow-up tasks
    """
    activity = get_activity(outreach_activity_id)

    # Determine follow-up schedule based on segment
    if activity.target_segment == 'high-end':
        schedule = [3, 7, 14]  # More patient with premium
    else:
        schedule = [2, 5, 10]  # Faster cadence for budget

    # Create sequence record
    sequence = supabase.from_('outreach_sequences').insert({
        'outreach_activity_id': outreach_activity_id,
        'sequence_type': '3-touch-email',
        'total_steps': 3,
        'current_step': 1,
        'status': 'active',
        'started_at': datetime.now(),
        'next_scheduled_at': datetime.now() + timedelta(days=schedule[0])
    }).execute()

    # Create communication records (pre-scheduled)
    for step_num, days_offset in enumerate(schedule, start=2):
        supabase.from_('outreach_communications').insert({
            'outreach_activity_id': outreach_activity_id,
            'contact_id': activity.contact_id,
            'channel': 'email',
            'direction': 'outbound',
            'sequence_step': step_num,
            'scheduled_send_at': datetime.now() + timedelta(days=days_offset),
            'status': 'scheduled',
            'conversation_starter_num': step_num  # Use different starter
        }).execute()

    # Create ClickUp subtasks (visual for humans)
    clickup.create_subtask(
        parent_task_id=activity.clickup_task_id,
        name=f"📧 Follow-Up #{step_num}",
        due_date=datetime.now() + timedelta(days=days_offset),
        description=f"Auto-scheduled follow-up (Day {days_offset})"
    )

    return {'sequence_id': sequence.id, 'follow_ups_created': 3}
```

**Follow-Up Email Generation:**
```python
def generate_followup_email(comm_record):
    """
    Generate follow-up email with different angle
    """
    activity = comm_record.outreach_activity
    step = comm_record.sequence_step

    # Get conversation starter for this step
    intel = get_business_intelligence(activity.contact_id)
    starter = intel.conversation_starters[step - 1]  # 0-indexed

    prompt = f"""
    Generate a follow-up email for a prospect who hasn't replied.

    **Context:**
    - Initial email sent {step * 3} days ago
    - Original pitch: {activity.outreach_type}
    - This is follow-up #{step} of 3

    **Approach:**
    - Acknowledge they're busy (no guilt trip)
    - Use a DIFFERENT angle (conversation starter #{step})
    - Add new information or social proof
    - Keep it short (< 150 words)
    - Softer CTA (just asking if worth exploring)

    **Conversation starter:**
    {starter['text']}

    Return:
    - subject_line (reference original or new angle)
    - email_body (brief, value-focused)
    """

    response = claude_sdk.query(prompt)
    return response
```

**Output:**
- 1 sequence record in `outreach_sequences`
- 3 communication records in `outreach_communications` (scheduled)
- 3 ClickUp subtasks (for human visibility)

**Error Handling:**
- If sequence already exists, skip creation
- If ClickUp task doesn't exist, log warning but continue
- Validate email schedule doesn't conflict with existing sends

**Testing Requirements:**
- Unit test: Sequence creation logic
- Integration test: Full sequence → actual follow-ups sent
- Edge case: Handle stopped sequences (reply received)

---

## Agent 13: Landing Page Generator

### Purpose
Auto-generate personalized landing pages for each course with course-specific data, ROI calculators, and embedded form for self-qualification.

### Technical Specs

**Edge Function:** `generate-landing-page`

**Trigger:** Called by Agent 10A before drafting email

**Input:** `course_id`, `contact_id`, `outreach_activity_id`

**Processing Logic:**
```python
async def generate_landing_page(course_id, contact_id):
    """
    Generate personalized landing page with form
    """
    # 1. Get all course data
    course = await get_course_with_intel(course_id)
    contact = await get_contact(contact_id)
    intel = await get_business_intelligence(contact_id)

    # 2. Generate unique slug
    slug = slugify(f"{course.name}-{course.state_code}")
    # Example: "country-club-of-virginia-va"

    # 3. Generate HTML with Claude
    html_prompt = f"""
    Generate a modern, single-page HTML landing page for:

    **Course:** {course.name}
    **Contact:** {contact.name} ({contact.title})
    **Opportunity:** ${intel.estimated_revenue}/year from {intel.ball_volume} used balls
    **Target Segment:** {course.segment}

    **Requirements:**
    1. Hero section with course name and opportunity headline
    2. ROI snapshot (4 key metrics in grid)
    3. Interactive calculator (volume × price = revenue)
    4. 3-step process diagram
    5. Social proof (testimonials from similar clubs)
    6. TWO CTAs:
       - Primary: "See If This Fits" → Shows 6-question form
       - Secondary: "Learn More" → Links to linkschoice.com
    7. Form fields:
       - Volume (pre-selected based on intel)
       - Current practice
       - Interests (checkboxes)
       - Timeline
       - Additional stakeholders
       - Questions/concerns
    8. Tracking pixel for analytics
    9. Mobile-responsive
    10. Tailwind CSS styling

    **Tone:** Professional, data-driven, consultative

    Return complete HTML (ready to deploy).
    """

    html = await claude.generate(html_prompt)

    # 4. Enhance with dynamic charts
    roi_chart_url = await generate_roi_chart(course, intel)
    process_diagram_url = await generate_process_diagram()

    # Inject chart URLs into HTML
    html = html.replace('{{ROI_CHART}}', roi_chart_url)
    html = html.replace('{{PROCESS_DIAGRAM}}', process_diagram_url)

    # 5. Upload to Supabase Storage
    file_path = f"landing-pages/{slug}.html"
    await supabase.storage
        .from_('public')
        .upload(file_path, html, {'contentType': 'text/html'})

    # 6. Get public URL
    public_url = f"https://oadmysogtfopkbmrulmq.supabase.co/storage/v1/object/public/landing-pages/{slug}.html"

    # 7. Store landing page record
    await supabase.from_('landing_pages').insert({
        'course_id': course_id,
        'contact_id': contact_id,
        'slug': slug,
        'url': public_url,
        'html_content': html,
        'created_at': datetime.now()
    })

    return {
        'url': public_url,
        'slug': slug
    }

async def generate_roi_chart(course, intel):
    """Use QuickChart.io to generate ROI visualization"""
    chart_config = {
        'type': 'bar',
        'data': {
            'labels': ['Current (Waste)', 'With Our Program'],
            'datasets': [{
                'label': 'Annual Value',
                'data': [0, intel.estimated_revenue],
                'backgroundColor': ['#dc2626', '#16a34a']
            }]
        },
        'options': {
            'plugins': {
                'title': {
                    'display': True,
                    'text': f"{course.name} - Range Ball Opportunity"
                }
            }
        }
    }

    # QuickChart API (FREE)
    import urllib.parse
    config_json = json.dumps(chart_config)
    chart_url = f"https://quickchart.io/chart?c={urllib.parse.quote(config_json)}"

    return chart_url
```

**Output:**
- Unique landing page URL
- HTML stored in Supabase Storage
- Charts embedded
- Form ready to accept submissions
- Tracking configured

**Cost:** ~$0.01 per page (one-time, reusable)

---

## Agent 14: Form Analyzer & Task Router (THE GAME-CHANGER!)

### Purpose
Analyze form submissions with Claude, categorize lead quality, extract insights, and auto-route to appropriate human with talking points.

### Technical Specs

**Edge Function:** `analyze-form-submission`

**Trigger:** Form submit (POST from landing page)

**Input:** Form submission data (JSON)
```json
{
  "contact": {
    "name": "Phil Kiester",
    "email": "phil.kiester@theccv.org",
    "course_id": "uuid",
    "contact_id": "uuid"
  },
  "form_data": {
    "volume": "30000-50000",
    "current_practice": "discard",
    "interests": ["buy", "retrieval"],
    "timeline": "immediate",
    "additional_contacts": "Warren West",
    "questions": "What's your purchase price?"
  },
  "engagement": {
    "page_duration": 180,
    "calculator_used": true,
    "sections_viewed": ["roi", "process", "form"]
  }
}
```

**Processing Logic:**
```python
async def analyze_form_submission(submission):
    """
    AI-powered form analysis with automatic task routing
    """

    # 1. Analyze with Claude
    analysis_prompt = f"""
    You are an expert B2B sales qualification agent.

    Analyze this form submission from a golf course prospect:

    **Contact:** {submission.contact.name} ({submission.contact.title})
    **Course:** {submission.course_name}

    **Form Responses:**
    - Volume: {submission.form_data.volume}
    - Current Practice: {submission.form_data.current_practice}
    - Interests: {', '.join(submission.form_data.interests)}
    - Timeline: {submission.form_data.timeline}
    - Additional Stakeholders: {submission.form_data.additional_contacts}
    - Their Question: "{submission.form_data.questions}"

    **Engagement Data:**
    - Time on page: {submission.engagement.page_duration} seconds
    - Used calculator: {submission.engagement.calculator_used}

    **TASK: Provide sales intelligence**

    1. **Lead Categorization:**
       - HOT (90-100): Immediate timeline + buying signals + high value
       - WARM (70-89): Soon timeline + interested + needs education
       - NURTURE (50-69): Future timeline + researching
       - INFO (0-49): No timeline + vague responses

    2. **Route Decision:**
       - Steve (founder): Hot leads 90+ OR strategic accounts OR multi-opportunity
       - Sales Team: Warm leads 70-89
       - Marketing: Nurture 50-69 + info gathering

    3. **Qualification Insights:**
       - What makes this hot/warm/cold?
       - Key buying signals detected
       - Red flags or concerns
       - Missing information needed

    4. **Recommended Actions:**
       - What should human do first? (call, email, wait)
       - When? (immediate, 3 days, 1 week)
       - Talking points for conversation
       - Questions to ask on call

    5. **Deal Intelligence:**
       - Estimated deal value (annual)
       - Probability of close (0-100%)
       - Sales cycle timeline estimate
       - Cross-sell opportunities

    Return JSON with this structure:
    {{
      "lead_category": "HOT|WARM|NURTURE|INFO",
      "lead_score": 0-100,
      "urgency": "immediate|high|medium|low",
      "route_to": "steve|sales|marketing",
      "route_reasoning": "why this person/team",

      "qualification": {{
        "buying_signals": ["signal 1", "signal 2"],
        "concerns": ["concern 1"],
        "missing_info": ["what we still need to know"]
      }},

      "recommended_action": {{
        "action": "call|email|nurture|archive",
        "timing": "within 24h|within 3 days|next week|6 months",
        "priority": 1-4,
        "talking_points": ["point 1", "point 2", "point 3"],
        "questions_to_ask": ["question 1", "question 2"],
        "conversation_opener": "suggested opening line"
      }},

      "deal_intelligence": {{
        "estimated_value": 15000,
        "probability": 0.75,
        "sales_cycle_days": 45,
        "cross_sell_opportunities": ["retrieval", "lease"],
        "objection_prevention": ["how to handle price question"]
      }}
    }}
    """

    analysis = await claude.messages.create({
        model: 'claude-sonnet-4-5',
        messages: [{'role': 'user', 'content': analysis_prompt}]
    })

    result = json.loads(analysis.content[0].text)

    # 2. Store submission
    submission_record = await supabase.from_('form_submissions').insert({
        'course_id': submission.course_id,
        'contact_id': submission.contact_id,
        'form_data': submission.form_data,
        'lead_category': result.lead_category,
        'lead_score': result.lead_score,
        'urgency': result.urgency,
        'route_to': result.route_to,
        'agent_insights': result,
        'page_view_duration': submission.engagement.page_duration,
        'calculator_used': submission.engagement.calculator_used,
        'submitted_at': datetime.now()
    }).execute()

    # 3. Create routed ClickUp task
    task = await create_routed_task(submission, result)

    # 4. Notify assigned human (if HOT or WARM)
    if result.lead_category in ['HOT', 'WARM']:
        await notify_assignee(result.route_to, submission, result)

    # 5. Send confirmation email to prospect
    await send_confirmation_email(submission, result)

    return result

async def create_routed_task(submission, analysis):
    """
    Create ClickUp task in appropriate list with AI-generated context
    """

    # Route to list based on category
    routing = {
        'HOT': {
            'list_id': '901409749476',  # Steve's High-Priority
            'assignee': 'steve@example.com',
            'priority': 1,  # Urgent
            'due_date': datetime.now() + timedelta(hours=24)
        },
        'WARM': {
            'list_id': '901413111587',  # General Sales Queue
            'assignee': 'sales-team@example.com',
            'priority': 2,  # High
            'due_date': datetime.now() + timedelta(days=3)
        },
        'NURTURE': {
            'list_id': '901413111588',  # Nurture Campaign
            'assignee': 'marketing@example.com',
            'priority': 3,  # Normal
            'due_date': datetime.now() + timedelta(months=6)
        },
        'INFO': {
            'list_id': '901413111589',  # Info Requests
            'assignee': 'marketing@example.com',
            'priority': 4,  # Low
            'due_date': None
        }
    }

    config = routing[analysis.lead_category]

    # Generate rich task description
    description = f"""
# 🔥 FORM FILL LEAD: {analysis.lead_category} ({analysis.lead_score}/100)

**Agent Analysis:** {analysis.route_reasoning}

═══════════════════════════════════════════════════════════

## 👤 CONTACT INFORMATION

**Name:** {submission.contact.name}
**Title:** {submission.contact.title}
**Email:** {submission.contact.email}
**Phone:** {submission.contact.phone}
**Course:** {submission.course_name}

**Additional Stakeholders Mentioned:**
{submission.form_data.additional_contacts or 'None'}

═══════════════════════════════════════════════════════════

## 📋 FORM RESPONSES

**Range Ball Volume:** {submission.form_data.volume}
**Current Practice:** {submission.form_data.current_practice}

**Programs of Interest:**
{format_interests(submission.form_data.interests)}

**Timeline:** {submission.form_data.timeline}

**Their Question:**
> "{submission.form_data.questions}"

═══════════════════════════════════════════════════════════

## 🎯 AGENT QUALIFICATION INSIGHTS

**Buying Signals Detected:**
{format_list(analysis.qualification.buying_signals)}

**Potential Concerns:**
{format_list(analysis.qualification.concerns)}

**Missing Information:**
{format_list(analysis.qualification.missing_info)}

═══════════════════════════════════════════════════════════

## 💼 DEAL INTELLIGENCE

**Estimated Annual Value:** ${analysis.deal_intelligence.estimated_value:,}
**Probability to Close:** {analysis.deal_intelligence.probability * 100}%
**Expected Sales Cycle:** {analysis.deal_intelligence.sales_cycle_days} days

**Cross-Sell Opportunities:**
{format_list(analysis.deal_intelligence.cross_sell_opportunities)}

═══════════════════════════════════════════════════════════

## 🗣️ RECOMMENDED NEXT STEPS (Agent Suggested)

**Action:** {analysis.recommended_action.action.upper()}
**Timing:** {analysis.recommended_action.timing}
**Priority:** {analysis.recommended_action.priority}/4

**Conversation Opener:**
"{analysis.recommended_action.conversation_opener}"

**Talking Points:**
{format_numbered_list(analysis.recommended_action.talking_points)}

**Questions to Ask:**
{format_numbered_list(analysis.recommended_action.questions_to_ask)}

**Objection Prevention:**
{format_list(analysis.deal_intelligence.objection_prevention)}

═══════════════════════════════════════════════════════════

## 📊 ENGAGEMENT DATA

**Page Visit Duration:** {submission.engagement.page_duration} seconds
**Calculator Used:** {'Yes ✓' if submission.engagement.calculator_used else 'No'}
**Sections Viewed:** {', '.join(submission.engagement.sections_viewed)}
**Form Fill Time:** {submission.engagement.form_fill_time} seconds

**Engagement Score:** {calculate_engagement_score(submission.engagement)}/10
  → {get_engagement_interpretation(submission.engagement)}

═══════════════════════════════════════════════════════════

## 📎 LINKS

- Landing Page: {submission.landing_page_url}
- Links Choice Profile: https://linkschoice.com
- Form Submission Details: [View in Supabase]

═══════════════════════════════════════════════════════════

**Source:** Landing Page Form Fill
**Submitted:** {submission.submitted_at}
**Agent Analysis Confidence:** {analysis.confidence * 100}%

🤖 Auto-generated by Agent 14 (Form Analyzer & Router)
    """

    # Create task
    task = await clickup.create_task(
        list_id=config['list_id'],
        name=f"🔥 {submission.course_name} - Form Fill ({analysis.lead_category})",
        description=description,
        assignees=[config['assignee']],
        priority=config['priority'],
        due_date=config['due_date'],
        tags=[
            'form-fill',
            analysis.lead_category.lower(),
            submission.form_data.timeline,
            *submission.form_data.interests
        ],
        custom_fields=[
            {'id': 'lead_score', 'value': analysis.lead_score},
            {'id': 'estimated_value', 'value': analysis.deal_intelligence.estimated_value},
            {'id': 'source', 'value': 'Landing Page Form'}
        ]
    )

    return task

def calculate_engagement_score(engagement):
    """
    Score 0-10 based on page engagement
    """
    score = 0

    # Time on page (max 4 points)
    if engagement.page_duration >= 180:  # 3+ min
        score += 4
    elif engagement.page_duration >= 120:  # 2-3 min
        score += 3
    elif engagement.page_duration >= 60:  # 1-2 min
        score += 2
    else:
        score += 1

    # Calculator use (3 points)
    if engagement.calculator_used:
        score += 3

    # Sections viewed (max 3 points)
    score += min(len(engagement.sections_viewed), 3)

    return score
```

**Output:**
- Landing page HTML generated & deployed
- Public URL returned to Agent 10A
- Charts embedded (QuickChart)
- Form configured with course-specific data
- Tracking pixel installed

**Cost:** ~$0.01 per page generation

---

## Agent 14: Form Analyzer & Task Router

### Purpose
Automatically analyze form submissions, categorize lead quality, extract insights, and route to appropriate human with AI-generated talking points.

### Technical Specs

**Edge Function:** `analyze-form-submission`

**Trigger:** Form submit (webhook from landing page)

**Input:** See processing logic above

**Output:**
- Lead categorized (HOT/WARM/NURTURE/INFO)
- ClickUp task created in routed list
- Assigned to appropriate person
- Slack notification (if HOT/WARM)
- Confirmation email sent to prospect

**Lead Scoring Algorithm:**
```python
def calculate_lead_score(form_data, engagement):
    """
    Combine form responses + engagement for final score
    """
    score = 0

    # Timeline (max 30 points)
    timeline_scores = {
        'immediate': 30,
        'soon': 20,
        'future': 10,
        'learning': 5
    }
    score += timeline_scores.get(form_data.timeline, 0)

    # Volume (max 25 points)
    volume_scores = {
        '50000+': 25,
        '30000-50000': 20,
        '10000-30000': 15,
        '<10000': 10,
        'unknown': 5
    }
    score += volume_scores.get(form_data.volume, 0)

    # Current practice (max 15 points)
    if form_data.current_practice == 'discard':
        score += 15  # Perfect fit!
    elif form_data.current_practice == 'donate':
        score += 10  # Good fit
    elif form_data.current_practice == 'vendor':
        score += 5  # Has vendor but might switch

    # Interests (max 10 points)
    interest_value = {
        'buy': 10,  # Highest value program
        'lease': 8,
        'retrieval': 7,
        'sell': 5
    }
    score += max([interest_value.get(i, 0) for i in form_data.interests])

    # Additional contacts (max 5 points)
    if form_data.additional_contacts:
        score += 5  # Multiple stakeholders = serious

    # Question quality (max 10 points)
    if 'price' in form_data.questions.lower() or 'cost' in form_data.questions.lower():
        score += 10  # Asking price = buying signal
    elif len(form_data.questions) > 20:
        score += 7  # Thoughtful question
    elif form_data.questions:
        score += 5  # Has question

    # Engagement score (max 10 points)
    engagement_score = calculate_engagement_score(engagement)
    score += engagement_score

    return min(score, 100)
```

**Routing Matrix:**
```python
def determine_routing(lead_score, form_data, course_data):
    """
    Route to appropriate human based on multiple factors
    """

    # Override 1: Strategic accounts → Steve (regardless of score)
    if course_data.segment == 'high-end' and course_data.opportunity_score >= 9:
        return 'steve', 'Strategic account (high-end + high opportunity)'

    # Override 2: Multi-opportunity → Steve
    if len(form_data.interests) >= 3:
        return 'steve', 'Multi-opportunity deal (3+ programs interested)'

    # Standard routing by score
    if lead_score >= 90:
        return 'steve', f'Hot lead ({lead_score}/100)'
    elif lead_score >= 70:
        return 'sales', f'Warm lead ({lead_score}/100)'
    elif lead_score >= 50:
        return 'marketing', f'Nurture lead ({lead_score}/100)'
    else:
        return 'marketing', f'Info gathering ({lead_score}/100)'
```

**Testing Requirements:**
- Unit test: Lead scoring with 20+ test cases
- Unit test: Routing logic (verify correct assignments)
- Integration test: Form submit → Task created
- Edge case: Invalid form data, duplicate submissions

---

## Agent 12: Reply Sentiment Analyzer

### Purpose
Automatically detect, analyze, and categorize email replies to qualify leads.

### Technical Specs

**Edge Function:** `analyze-reply-sentiment`

**Trigger:** SendGrid inbound webhook (POST on email reply)

**Input:** SendGrid webhook payload
```json
{
  "from": "phil.kiester@theccv.org",
  "to": "steve@rangeballreconditioning.com",
  "subject": "Re: CCV + Range Ball Revenue Opportunity",
  "text": "Thanks for reaching out. We'd be interested in learning more...",
  "html": "<html>...",
  "headers": {
    "In-Reply-To": "<original-message-id>",
    "References": "<original-message-id>"
  },
  "timestamp": 1698765432
}
```

**Processing Logic:**
```python
async def analyze_reply_sentiment(webhook_payload):
    """
    Analyze email reply and categorize intent
    """
    # 1. Match to original outreach
    original_message_id = webhook_payload['headers']['In-Reply-To']
    communication = supabase.from_('outreach_communications') \
        .select('*, outreach_activities(*)') \
        .eq('email_message_id', original_message_id) \
        .single() \
        .execute()

    if not communication:
        # Can't match reply to outreach, log and exit
        log_orphan_reply(webhook_payload)
        return {'status': 'orphan', 'action': 'manual_review'}

    # 2. Analyze sentiment with Claude
    reply_text = webhook_payload['text']
    analysis = await claude_sdk.query(f"""
    Analyze this email reply to a sales outreach.

    **Reply:**
    {reply_text}

    **Categorize as ONE of:**
    1. INTERESTED - Wants to learn more, asks questions, open to call
       Examples: "Tell me more", "Sounds interesting", "Let's talk"

    2. NOT_NOW - Interested but bad timing, asks to follow up later
       Examples: "Check back in Q2", "Busy right now", "Revisit in 6 months"

    3. NOT_INTERESTED - Clear no, has supplier, doesn't fit
       Examples: "Not interested", "We're all set", "Don't need this"

    4. WRONG_CONTACT - Forwarded to someone else, contact left company
       Examples: "Talk to John instead", "I don't handle this", "No longer here"

    5. AUTO_REPLY - Out of office, vacation, automated response
       Examples: "Out of office", "On vacation", "Automatic reply"

    6. QUESTION - Asking for clarification, pricing, details
       Examples: "How much?", "Where are you located?", "What's your process?"

    **Return JSON:**
    {{
      "category": "INTERESTED|NOT_NOW|NOT_INTERESTED|WRONG_CONTACT|AUTO_REPLY|QUESTION",
      "confidence": 0.0-1.0,
      "sentiment": "positive|neutral|negative",
      "key_phrases": ["quote from reply"],
      "suggested_action": "call|email|wait|archive|forward",
      "urgency": "high|medium|low",
      "next_step_recommendation": "specific action to take"
    }}
    """)

    # 3. Update database
    supabase.from_('outreach_communications').update({
        'direction': 'inbound',
        'received_at': datetime.now(),
        'response_text': reply_text,
        'response_sentiment': analysis.category,
        'response_summary': analysis.key_phrases[0] if analysis.key_phrases else None,
        'next_action': analysis.suggested_action
    }).eq('id', communication.id).execute()

    # 4. Update outreach activity
    activity = communication.outreach_activities
    supabase.from_('outreach_activities').update({
        'status': get_new_status(analysis.category),
        'response_received': True
    }).eq('activity_id', activity.activity_id).execute()

    # 5. Stop follow-up sequence if reply received
    if analysis.category != 'AUTO_REPLY':
        stop_sequence(activity.activity_id)

    # 6. Update ClickUp
    await update_clickup_on_reply(activity, analysis)

    # 7. Notify human if INTERESTED or QUESTION
    if analysis.category in ['INTERESTED', 'QUESTION'] and analysis.urgency == 'high':
        await notify_sales_team(activity, analysis, reply_text)

    return analysis

def get_new_status(category):
    """Map analysis category to activity status"""
    status_map = {
        'INTERESTED': 'Replied (Action!)',
        'QUESTION': 'Replied (Action!)',
        'NOT_NOW': 'Nurture (6mo)',
        'NOT_INTERESTED': 'Closed',
        'WRONG_CONTACT': 'Needs Review',
        'AUTO_REPLY': 'Sent (Waiting)'  # Keep waiting
    }
    return status_map.get(category, 'Replied')

def stop_sequence(activity_id):
    """Stop all future follow-ups for this activity"""
    supabase.from_('outreach_sequences').update({
        'status': 'stopped',
        'response_received': True,
        'paused_at': datetime.now(),
        'paused_reason': 'Reply received'
    }).eq('outreach_activity_id', activity_id).execute()

    # Delete scheduled (unsent) follow-ups
    supabase.from_('outreach_communications').delete() \
        .eq('outreach_activity_id', activity_id) \
        .eq('status', 'scheduled') \
        .execute()

async def notify_sales_team(activity, analysis, reply_text):
    """Send Slack notification for hot leads"""
    slack_message = {
        'channel': '#sales-hot-leads',
        'text': f"🔥 HOT LEAD: {activity.golf_courses.name}",
        'blocks': [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f"*{activity.golf_courses.name}* replied to outreach!\n\n*Sentiment:* {analysis.sentiment}\n*Suggested action:* {analysis.next_step_recommendation}"
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f"*Reply:*\n>{reply_text[:200]}..."
                }
            },
            {
                'type': 'actions',
                'elements': [
                    {
                        'type': 'button',
                        'text': {'type': 'plain_text', 'text': 'View in ClickUp'},
                        'url': f"https://app.clickup.com/t/{activity.clickup_task_id}"
                    }
                ]
            }
        ]
    }

    await slack_client.post_message(slack_message)
```

**Output:**
- Updates `outreach_communications` with reply data
- Updates `outreach_activities` status
- Stops follow-up sequence if appropriate
- Updates ClickUp task status
- Sends Slack notification if hot lead

**Error Handling:**
- If sentiment analysis fails, default to 'QUESTION' (safe fallback)
- If can't match reply to original, log to manual review queue
- Retry Claude API calls 3 times
- All errors logged to monitoring table

**Testing Requirements:**
- Unit test: Sentiment categorization (20+ test cases)
- Integration test: End-to-end webhook → DB update
- Edge case: Multiple replies, auto-replies, forwarded emails

---

## Database Schema

### New Tables

#### `landing_pages` (New table for Agent 13)
```sql
CREATE TABLE landing_pages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id INTEGER REFERENCES golf_courses(id),
  contact_id UUID REFERENCES golf_course_contacts(id),
  outreach_activity_id UUID REFERENCES outreach_activities(activity_id),

  slug TEXT UNIQUE NOT NULL,  -- URL slug (country-club-of-virginia-va)
  url TEXT NOT NULL,  -- Full public URL
  html_content TEXT NOT NULL,  -- Complete HTML

  -- Metadata
  variant TEXT,  -- A/B test variant
  template_version INTEGER DEFAULT 1,

  -- Performance tracking
  total_views INTEGER DEFAULT 0,
  unique_visitors INTEGER DEFAULT 0,
  avg_time_on_page INTEGER,  -- Seconds
  form_conversion_rate NUMERIC(5,4),  -- Form fills / visits

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_landing_pages_course ON landing_pages(course_id);
CREATE INDEX idx_landing_pages_slug ON landing_pages(slug);
```

#### `landing_page_analytics` (Tracks visitor behavior)
```sql
CREATE TABLE landing_page_analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  landing_page_id UUID REFERENCES landing_pages(id),
  course_id INTEGER REFERENCES golf_courses(id),
  contact_id UUID REFERENCES golf_course_contacts(id),

  -- Visit tracking
  visited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  duration_seconds INTEGER,
  referrer TEXT,  -- Where they came from (email link)

  -- Interaction tracking
  calculator_used BOOLEAN DEFAULT FALSE,
  calculator_interactions INTEGER DEFAULT 0,
  sections_scrolled TEXT[],  -- Which sections they viewed

  -- Conversion tracking
  form_started BOOLEAN DEFAULT FALSE,
  form_completed BOOLEAN DEFAULT FALSE,
  form_submission_id UUID REFERENCES form_submissions(id),

  -- Device/Browser
  user_agent TEXT,
  device_type TEXT,  -- desktop, mobile, tablet
  ip_address INET,

  -- UTM parameters (track email campaign)
  utm_source TEXT DEFAULT 'email',
  utm_medium TEXT DEFAULT 'outreach',
  utm_campaign TEXT,  -- Links to outreach_activity_id

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_landing_analytics_page ON landing_page_analytics(landing_page_id);
CREATE INDEX idx_landing_analytics_visited ON landing_page_analytics(visited_at);
```

#### `form_submissions` (Agent 14 input)
```sql
CREATE TABLE form_submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  landing_page_id UUID REFERENCES landing_pages(id),
  course_id INTEGER REFERENCES golf_courses(id),
  contact_id UUID REFERENCES golf_course_contacts(id),

  -- Form data (structured)
  form_data JSONB NOT NULL,

  -- Agent 14 analysis
  lead_category TEXT CHECK (lead_category IN ('HOT', 'WARM', 'NURTURE', 'INFO')),
  lead_score INTEGER CHECK (lead_score >= 0 AND lead_score <= 100),
  urgency TEXT,
  route_to TEXT,  -- steve, sales, marketing
  agent_insights JSONB,  -- Full Claude analysis

  -- Engagement tracking
  page_view_duration INTEGER,  -- Seconds on page before submitting
  calculator_used BOOLEAN,
  form_fill_time INTEGER,  -- Seconds to complete form

  -- ClickUp routing
  clickup_task_id TEXT,
  clickup_list_id TEXT,
  clickup_assignee TEXT,
  clickup_created_at TIMESTAMP WITH TIME ZONE,

  -- Confirmation sent
  confirmation_email_sent BOOLEAN DEFAULT FALSE,
  confirmation_sent_at TIMESTAMP WITH TIME ZONE,

  submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_form_submissions_category ON form_submissions(lead_category);
CREATE INDEX idx_form_submissions_score ON form_submissions(lead_score);
CREATE INDEX idx_form_submissions_submitted ON form_submissions(submitted_at);
CREATE INDEX idx_form_submissions_route ON form_submissions(route_to);
```

#### `email_drafts` (CRITICAL - New table for draft storage)
```sql
CREATE TABLE email_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id INTEGER REFERENCES golf_courses(id),
  contact_id UUID REFERENCES golf_course_contacts(id),
  outreach_activity_id UUID REFERENCES outreach_activities(activity_id),

  -- Email content
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  conversation_starter_num INTEGER,

  -- Quality scoring
  quality_score NUMERIC(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
  quality_flags JSONB, -- Detailed check results: ['missing_name', 'too_short']

  -- Approval workflow
  status TEXT CHECK (status IN ('draft', 'approved', 'sent', 'rejected', 'needs_review')),
  approved_by TEXT,
  approved_at TIMESTAMP WITH TIME ZONE,
  flagged_at TIMESTAMP WITH TIME ZONE,
  reviewed_at TIMESTAMP WITH TIME ZONE,

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  sent_at TIMESTAMP WITH TIME ZONE,
  clickup_task_id TEXT
);

CREATE INDEX idx_email_drafts_status ON email_drafts(status);
CREATE INDEX idx_email_drafts_quality ON email_drafts(quality_score);
CREATE INDEX idx_email_drafts_created ON email_drafts(created_at);
```

#### `send_queue`
```sql
CREATE TABLE send_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  outreach_activity_id UUID REFERENCES outreach_activities(activity_id),
  course_id INTEGER REFERENCES golf_courses(id),
  contact_id UUID REFERENCES golf_course_contacts(id),
  priority_score NUMERIC(4,3),
  scheduled_send_at TIMESTAMP WITH TIME ZONE,
  status TEXT CHECK (status IN ('queued', 'sent', 'failed', 'cancelled')),
  sent_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_send_queue_status ON send_queue(status);
CREATE INDEX idx_send_queue_scheduled ON send_queue(scheduled_send_at);
```

#### `email_templates`
```sql
CREATE TABLE email_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_name TEXT NOT NULL,
  segment TEXT CHECK (segment IN ('high-end', 'budget', 'both')),
  outreach_type TEXT,
  subject_line_template TEXT NOT NULL,
  body_template TEXT NOT NULL,
  variables JSONB,  -- Variables used in template
  version INTEGER DEFAULT 1,
  is_active BOOLEAN DEFAULT TRUE,

  -- A/B testing
  variant TEXT,  -- 'A', 'B', 'control', etc.
  test_group TEXT,

  -- Performance tracking
  times_used INTEGER DEFAULT 0,
  total_opens INTEGER DEFAULT 0,
  total_replies INTEGER DEFAULT 0,
  avg_reply_rate NUMERIC(5,4),

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `agent_execution_logs`
```sql
CREATE TABLE agent_execution_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name TEXT NOT NULL,  -- 'Agent 9', 'Agent 10', etc.
  execution_type TEXT,  -- 'batch', 'webhook', 'manual'
  status TEXT CHECK (status IN ('started', 'completed', 'failed')),

  -- Input/Output
  input_params JSONB,
  output_result JSONB,
  error_message TEXT,

  -- Performance
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  duration_seconds NUMERIC(10,3),

  -- Cost tracking
  anthropic_input_tokens INTEGER,
  anthropic_output_tokens INTEGER,
  anthropic_cost_usd NUMERIC(10,6),
  sendgrid_emails_sent INTEGER,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agent_logs_name ON agent_execution_logs(agent_name);
CREATE INDEX idx_agent_logs_status ON agent_execution_logs(status);
CREATE INDEX idx_agent_logs_created ON agent_execution_logs(created_at);
```

### Modified Tables

#### `outreach_communications` (Add columns)
```sql
ALTER TABLE outreach_communications ADD COLUMN IF NOT EXISTS
  -- Email tracking
  email_message_id TEXT,  -- SendGrid message ID
  email_thread_id TEXT,   -- Thread for replies
  scheduled_send_at TIMESTAMP WITH TIME ZONE,
  status TEXT,  -- 'scheduled', 'sent', 'delivered', 'opened', 'replied'

  -- Template tracking
  template_id UUID REFERENCES email_templates(id),
  variant TEXT,  -- A/B test variant

  -- Performance
  delivered_at TIMESTAMP WITH TIME ZONE,
  bounced_at TIMESTAMP WITH TIME ZONE,
  bounce_reason TEXT;
```

#### `outreach_sequences` (Add columns)
```sql
ALTER TABLE outreach_sequences ADD COLUMN IF NOT EXISTS
  -- Auto-follow-up control
  auto_send_enabled BOOLEAN DEFAULT TRUE,
  last_auto_send_at TIMESTAMP WITH TIME ZONE,

  -- Performance
  total_opens INTEGER DEFAULT 0,
  total_clicks INTEGER DEFAULT 0,
  conversion_step INTEGER;  -- Which step converted
```

---

## External Service Configuration

### SendGrid Setup

**Account Requirements:**
- SendGrid account (free tier: 100 emails/day, paid: $19.95/mo for 40K emails)
- Domain verification (rangeballreconditioning.com)
- SPF/DKIM records configured

**API Configuration:**
```bash
# Environment variables
SENDGRID_API_KEY=SG.xxxxx
SENDGRID_FROM_EMAIL=steve@rangeballreconditioning.com
SENDGRID_FROM_NAME=Steve McMillion
SENDGRID_REPLY_TO=steve@rangeballreconditioning.com
```

**Webhook Configuration:**
```
Inbound Parse Webhook:
  URL: https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/analyze-reply-sentiment
  Domain: mail.rangeballreconditioning.com

Event Webhook:
  URL: https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/sendgrid-events
  Events: delivered, opened, clicked, bounced, unsubscribed
```

**Email Footer (CAN-SPAM Compliance):**
```
---
Range Ball Reconditioning
[Physical Address]
[Unsubscribe link]
[Privacy Policy link]

You received this email because you manage a golf course with range ball needs.
```

### Slack Integration (Optional)

**Webhook URL:**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL_HOT_LEADS=#sales-hot-leads
```

**Notification Triggers:**
- INTERESTED replies (instant)
- QUESTION replies (instant)
- Daily summary (8 AM: emails sent, replies received)
- Weekly report (Monday 9 AM: conversion rates, top performers)

---

## ClickUp Configuration

### Status Workflow

**Add 6 Custom Statuses to List 901413111587:**

1. **📥 Intake Queue** (Gray)
   - All agent-created tasks start here
   - Auto-sorted by priority_score (custom field)

2. **📧 Ready to Send** (Blue)
   - Limit: 50 tasks maximum
   - Agent 9 moves tasks here daily

3. **⏳ Sent (Waiting)** (Yellow)
   - Automatic after email sent
   - Subtasks for follow-ups appear here

4. **💬 Replied (Action!)** (Green)
   - Agent 12 moves here on INTERESTED/QUESTION
   - **Priority: Urgent** auto-set
   - **Assigned to:** Sales manager

5. **✅ Qualified (Meeting)** (Purple)
   - Human moves here when meeting booked

6. **📁 Closed** (Red/Gray)
   - Auto-archive after 30 days
   - Subdivided by outcome (Won, Lost, Not Interested, Nurture)

### Custom Fields (Add to List)

```json
{
  "priority_score": {
    "type": "number",
    "range": "0-10",
    "decimals": 2,
    "purpose": "Agent 9 scoring for queue prioritization"
  },
  "email_sent_date": {
    "type": "date",
    "purpose": "Track when initial email sent"
  },
  "reply_sentiment": {
    "type": "dropdown",
    "options": ["Interested", "Question", "Not Now", "Not Interested", "Wrong Contact"],
    "purpose": "Agent 12 categorization"
  },
  "conversation_starter_used": {
    "type": "dropdown",
    "options": ["#1", "#2", "#3", "#4", "#5", "#6", "#7"],
    "purpose": "A/B testing which starters work"
  },
  "template_variant": {
    "type": "dropdown",
    "options": ["A", "B", "Control"],
    "purpose": "A/B testing templates"
  },
  "auto_generated": {
    "type": "checkbox",
    "purpose": "Flag agent-created vs manual tasks"
  }
}
```

### Automation Rules (ClickUp Native)

**Rule 1: Limit Ready to Send Queue**
- Trigger: Task moved to "Ready to Send"
- Condition: Status = "Ready to Send" has >= 50 tasks
- Action: Block move, show warning: "Clear today's queue first (50 max)"

**Rule 2: Auto-Assign Replied Tasks**
- Trigger: Status changed to "Replied (Action!)"
- Action: Set priority = Urgent
- Action: Assign to = Steve McMillion
- Action: Add comment: "🔥 Hot lead - respond within 24 hours"

**Rule 3: Auto-Archive Closed Tasks**
- Trigger: Status = "Closed" for 30 days
- Action: Archive task
- Action: Add tag: "archived-{month}"

**Rule 4: Prevent Duplicate Work**
- Trigger: Task moved from "Intake Queue"
- Condition: Same course already in "Sent" or "Replied"
- Action: Block move, add comment: "Duplicate - this course already contacted"

---

## Testing Plan

### Phase 1: Unit Testing (Week 1)

**Agent 9 Tests:**
- [ ] Scoring algorithm with known inputs
- [ ] Handle empty queue
- [ ] Handle queue with < 50 items
- [ ] Region balancing logic
- [ ] FIFO tiebreaker

**Agent 10 Tests:**
- [ ] Email generation with various segments
- [ ] Template variable substitution
- [ ] SendGrid API call (sandbox mode)
- [ ] Error handling (API timeout, invalid email)
- [ ] Conversation starter selection

**Agent 11 Tests:**
- [ ] Follow-up schedule creation
- [ ] Sequence for different segments
- [ ] Prevent duplicate sequences
- [ ] Stop sequence on reply

**Agent 12 Tests:**
- [ ] Sentiment categorization (20 test cases)
- [ ] Webhook payload parsing
- [ ] Match reply to original email
- [ ] Handle forwarded emails
- [ ] Auto-reply detection

### Phase 2: Integration Testing (Week 1-2)

**End-to-End Scenarios:**
- [ ] Agent 9 → 10 → 11 full flow (5 test courses)
- [ ] Reply webhook → Agent 12 → DB update
- [ ] Follow-up auto-send at Day 3
- [ ] A/B test variant assignment
- [ ] ClickUp status sync

**Performance Tests:**
- [ ] 50 emails generated in < 5 min
- [ ] 50 emails sent in < 10 min
- [ ] Reply analysis in < 2 seconds
- [ ] Database queries < 100ms

### Phase 3: Controlled Production Test (Week 2)

**100-Course Test:**
- [ ] Day 1: Queue 100 courses
- [ ] Day 1-5: Send 20/day, spot-check 20%
- [ ] Day 3-19: Monitor follow-ups
- [ ] Day 7-21: Track replies
- [ ] Week 3: Analyze results

**Metrics to Track:**
- Email delivery rate (target: > 98%)
- Open rate (target: > 20%)
- Reply rate (target: > 10%)
- Sentiment accuracy (human review 50 replies)
- Time saved vs manual (target: > 90%)

---

## Rollout Plan

### Week 1: Build & Test (TESTING MODE)
- **Day 1-2:** ClickUp restructure, SendGrid setup, create 4 new tables
- **Day 3:** Build Agent 9 (Queue Prioritization)
- **Day 4:** Build Agent 10A (Email Drafter)
- **Day 5:** Build Agent 10B (Email Sender - manual approval mode)
- **Day 6:** Build Agent 11 (Follow-Up Scheduler)
- **Day 7:** Build Agent 12 (Reply Analyzer)

**Agent 10B Mode:** TESTING
- Human approves every email in ClickUp
- ClickUp webhook triggers Agent 10B to send
- 100% human review (spot-check 20%)

### Week 2: Controlled Test (100 Courses) - TESTING MODE
- **Day 1:** Queue 100 courses
- **Day 1-5:** Agent 10A drafts 20/day, human approves & Agent 10B sends
- **Day 3-19:** Monitor automated follow-ups (Agent 11)
- **Throughout:** Track reply categorization accuracy (Agent 12)
- **Week end:** Analyze results (quality score distribution, reply rate)

**Success Gate:** If avg quality_score >= 0.85 and < 10% human edits needed → Proceed to Week 3

### Week 3: Scale to 30/Day (HYBRID MODE)
- **Day 1:** Enable hybrid mode in Agent 10B
  ```python
  # Config change
  AGENT_10B_MODE = 'hybrid'
  AUTO_SEND_THRESHOLD = 0.9
  ```
- **Day 1-7:**
  - Agent 10A drafts 30 emails/day
  - Agent 10B auto-sends ~24/day (quality >= 0.9)
  - Agent 10B flags ~6/day for review (quality < 0.9)
  - Human reviews edge cases (15 min/day)
- **Day 7:** A/B test subject lines (variant A vs B)

**Success Gate:** If > 80% auto-sent and reply rate >= 10% → Proceed to Week 4

### Week 4: Scale to 50/Day (HYBRID MODE)
- **Day 1-7:**
  - Agent 10A drafts 50 emails/day
  - Agent 10B auto-sends ~40/day (quality >= 0.9)
  - Agent 10B flags ~10/day for review
  - Human reviews edge cases (20 min/day)
- **Week end:** Validate sustainability (can team handle 50/day + replies?)

**Success Gate:** If quality maintained and team satisfied → Proceed to Production

### Week 5+: Sustain at 50/Day (PRODUCTION MODE - Optional)
- **Enable full automation** (if quality validated):
  ```python
  AGENT_10B_MODE = 'production'
  AUTO_SEND_ALL = True
  SAMPLE_RATE = 0.05  # 5% random audit
  ```
- **Agent 10B auto-sends all 50 emails**
- **Human only handles:**
  - Replies from interested leads (Agent 12 notifications)
  - 5% random sample audit (2-3 emails/day)
  - Edge cases (wrong contact, opt-outs)
- **Time:** 5-15 min/day

**Note:** You may choose to stay in Hybrid Mode permanently (human comfort + quality assurance)

---

## Success Criteria

### Technical Success (Week 2)
- [ ] 100 emails sent with 0% manual drafting
- [ ] > 95% delivery rate
- [ ] All follow-ups auto-created
- [ ] All replies auto-categorized
- [ ] < 10% false positive rate (sentiment)

### Business Success (Week 4)
- [ ] 50 outreaches/day sustained
- [ ] > 90% follow-up completion rate
- [ ] > 10% reply rate
- [ ] < 1 hour/day human time (replies only)
- [ ] < $0.25 total cost per outreach

### Quality Gates
- [ ] No spam complaints
- [ ] < 2% bounce rate
- [ ] > 4.0/5.0 email quality rating (human review)
- [ ] Zero CAN-SPAM violations
- [ ] > 80% sales team satisfaction

---

## Risk Mitigation

### Technical Risks

**Risk: SendGrid account suspended**
- Mitigation: Warm up account (start 10/day, scale slowly)
- Mitigation: Monitor spam reports, bounces
- Contingency: Backup with Mailgun

**Risk: Claude API rate limits**
- Mitigation: Implement retry logic with backoff
- Mitigation: Cache email templates for reuse
- Contingency: Reduce batch size to 25/day

**Risk: Database performance degradation**
- Mitigation: Add indexes on hot queries
- Mitigation: Archive old communications (> 6 months)
- Monitoring: Query performance dashboard

### Business Risks

**Risk: Low reply rate (<5%)**
- Mitigation: A/B test conversation starters
- Mitigation: Human review 20% of emails (quality)
- Adjustment: Slow send rate, improve copy

**Risk: High unsubscribe rate (>5%)**
- Mitigation: Improve targeting (only high-fit courses)
- Mitigation: Softer CTA language
- Adjustment: Review segmentation accuracy

**Risk: Sentiment analysis inaccuracy**
- Mitigation: Human review 50 replies/week
- Mitigation: Refine prompts based on errors
- Adjustment: Default to "QUESTION" when uncertain

---

## Maintenance & Operations

### Daily Operations (Automated)
- 12:00 AM: Agent 9 prioritizes queue → 50 courses
- 8:00 AM: Agent 10 sends 50 emails
- 9:00 AM, 12:00 PM, 3:00 PM: Agent 11 sends follow-ups
- Real-time: Agent 12 analyzes replies

### Human Operations (15-45 min/day)
- Morning (10 min): Review "Replied (Action!)" column
- Midday (10 min): Respond to interested leads
- Afternoon (10 min): Quality spot-check (5 random emails)
- Weekly (1 hour): Review metrics, optimize A/B tests

### Weekly Review (Monday 9 AM)
- **Metrics dashboard:**
  - Emails sent last week
  - Open rate, reply rate, conversion rate
  - Top-performing conversation starters
  - Segment performance comparison
  - Cost per lead

- **Optimization tasks:**
  - Promote winning A/B test variant
  - Refine low-performing templates
  - Adjust queue prioritization weights
  - Review and resolve edge cases

### Monthly Audit
- [ ] Review 100 random emails for quality
- [ ] Check CAN-SPAM compliance
- [ ] Validate sentiment accuracy (50 replies)
- [ ] Cost analysis (vs budget)
- [ ] Database cleanup (archive old records)

---

## Cost Breakdown

### Infrastructure (Monthly)
| Service | Cost | Volume |
|---------|------|--------|
| Supabase Pro | $25 | Database + edge functions |
| SendGrid | $19.95 | 40K emails (1,600 used) |
| Anthropic API | ~$15 | Reply analysis (~2K replies) |
| Render | $7 | Existing agent service |
| **Total** | **$66.95** | |

### Per-Course Cost
- Enrichment (Agents 1-8): $0.15
- Email automation: $0.07
- **Total: $0.22/course**

### ROI Analysis
**Manual process:**
- 15 min/email × $20/hr = $5/email
- 1,600 emails/month = $8,000

**Automated process:**
- Infrastructure: $66.95/month
- Time: 10 hours/month × $20/hr = $200
- **Total: $266.95/month**

**Savings: $7,733/month (97% cost reduction)**

---

## Appendix

### A. Conversation Starter Examples

**High-End Segment (Range Ball Buy):**
1. "Phil, I noticed CCV's commitment to quality with your recent golf performance center investment. Are you currently disposing of used range balls once they show wear, or have you explored recycling programs that could turn that waste into revenue?"

2. "With 800,000 range balls dispensed annually and a 6-month replacement cycle, CCV generates significant volume of used balls. We're the only company worldwide that can recondition these to like-new quality—interested in learning how this creates revenue while reducing waste?"

**Budget Segment (Range Ball Sell):**
1. "Quick question: What do you currently pay per range ball? Most courses are paying $0.80-1.20 for new balls. We can supply reconditioned balls (like-new quality) at 40-60% less. Worth a 15-min call to explore?"

### B. Email Template Variables

```python
{
  'contact_name': 'Phil Kiester',
  'contact_first_name': 'Phil',
  'contact_title': 'General Manager',
  'course_name': 'Country Club of Virginia',
  'course_short_name': 'CCV',
  'segment': 'high-end',
  'opportunity_score': 9,
  'conversation_starter': 'Full text from Agent 6',
  'specific_data_point': '800,000 range balls dispensed annually',
  'value_proposition': '$15,000+ annual revenue from waste',
  'water_hazards': 7,
  'secondary_opportunity': 'ball retrieval'
}
```

### C. Sentiment Analysis Test Cases

```python
test_cases = [
    {
        'reply': "Thanks for reaching out! This sounds interesting. Let's schedule a call next week.",
        'expected': 'INTERESTED',
        'confidence': 0.95
    },
    {
        'reply': "Not interested, we already have a supplier.",
        'expected': 'NOT_INTERESTED',
        'confidence': 1.0
    },
    {
        'reply': "I'm out of office until next month. Please resend then.",
        'expected': 'AUTO_REPLY',
        'confidence': 0.9
    },
    # ... 17 more test cases
]
```

---

## Implementation Checklist

### Pre-Implementation
- [ ] SendGrid account created & domain verified
- [ ] Slack workspace configured (optional)
- [ ] ClickUp statuses & fields added
- [ ] Supabase tables created (3 new tables)

### Week 1: Build
- [ ] Database: Create 4 new tables (email_drafts, send_queue, email_templates, agent_execution_logs)
- [ ] Agent 9: Queue prioritization
- [ ] Agent 10A: Email draft generator (with quality scoring)
- [ ] Agent 10B: Email sender (testing mode - manual approval)
- [ ] Agent 11: Follow-up scheduler
- [ ] Agent 12: Reply analyzer
- [ ] Unit tests (all 5 agent functions)
- [ ] Integration tests

### Week 2: Test
- [ ] 100-course controlled test
- [ ] Spot-check 20% of emails
- [ ] Monitor metrics daily
- [ ] Analyze results

### Week 3-4: Scale
- [ ] Scale to 30/day
- [ ] Scale to 50/day
- [ ] A/B testing setup
- [ ] Weekly optimization

---

---

## Quick Reference: Agent 10 Split Explained

### Do We Need a Separate Draft Agent?

**YES - Agent 10 is split into TWO agents for progressive automation:**

**Agent 10A (Drafter):**
- Always runs first
- Generates ALL email drafts
- Calculates quality scores
- Stores in database
- Updates ClickUp

**Agent 10B (Sender):**
- Runs AFTER Agent 10A
- Behavior changes by mode:
  - **Testing:** Waits for human approval (ClickUp webhook)
  - **Hybrid:** Auto-sends high-quality (>=0.9), flags low-quality for review
  - **Production:** Auto-sends all, 5% random sample

**Why separate?**
- Quality gate between drafting and sending
- Progressive trust-building (test → hybrid → production)
- Easy mode switching (config change, not code change)
- Safety net (can always revert to manual approval)

---

### Complete Flow Summary

**Every Day at Midnight:**
```
Agent 9 runs → Selects top 50 from 170 backlog → Inserts into send_queue
```

**Every Day at 8:00 AM:**
```
Agent 10A runs → Generates 50 drafts → Stores with quality scores → Updates ClickUp
```

**Every Day at 8:15 AM (or when approved):**
```
Agent 10B runs → Sends emails (based on mode) → Triggers Agent 11 → Creates follow-ups
```

**Throughout the Day:**
```
Agent 12 listens → Reply received → Analyzes sentiment → Updates DB/ClickUp → Notifies human if interested
```

**Day 3, 7, 14:**
```
Agent 11 runs → Sends scheduled follow-ups → Logs to database
```

---

## Implementation Handoff

**This PRD is ready for:**
- Development team to build agents
- Database team to create tables
- DevOps to configure SendGrid + webhooks
- Sales team to review workflow

**Estimated implementation time:** 4 weeks to 50/day sustained volume

---

---

## SYSTEM ENHANCEMENTS (Added Oct 24 - PM Session)

### Enhancement 1: Landing Page + Form Self-Qualification

**THE GAME-CHANGER:** Instead of waiting for email replies, drive prospects to personalized landing pages with embedded forms.

**New Agents:**
- **Agent 10.5:** Subject Line Optimizer (generates 5 variants, picks best)
- **Agent 13:** Landing Page Generator (personalized HTML per course)
- **Agent 14:** Form Analyzer & Router (AI qualification + automatic routing)

**Impact:**
- Traditional: 0.4% conversion (4 qualified leads from 1,000 emails)
- **With landing pages:** 4.2% conversion (42 qualified leads from 1,000 emails)
- **15X improvement!**

**Why it works:**
1. Email becomes ultra-short teaser (50 words vs 200)
2. Landing page educates at scale (no human time)
3. Form self-qualifies (structured data vs email parsing)
4. Agent 14 routes intelligently (HOT → Steve, WARM → Sales)
5. Engagement tracking (know who's interested before they submit)

### Enhancement 2: Progressive Email Shortening

**Old email strategy:** 150-200 words explaining everything

**New email strategy:** 50-word teaser driving to landing page

**Example:**
```
Subject: CCV - Custom Range Ball Analysis Ready

Hi Phil,

Based on CCV's 30,000 range balls/year, we built a custom
revenue analysis for you:

→ rangeballrecon.com/ccv-custom-analysis

Shows your $15K opportunity, process, and options.

Takes 2 min to review, 30 sec to request info if interested.

Steve
```

**Benefits:**
- Higher read completion (50 words vs 200)
- Curiosity-driven (what's in the analysis?)
- Trackable (landing page analytics)
- Professional (custom analysis = credibility)

### Enhancement 3: Two-Path Funnel

**Path A: High Intent (Form Fill)**
- Email → Landing page → Form → Agent 14 analyzes → ClickUp task routed
- Conversion: 60% of page visitors fill form
- Outcome: Structured data, automatic qualification, talking points generated

**Path B: Medium Intent (Links Choice)**
- Email → Landing page → "Learn More" link → linkschoice.com
- Conversion: 25% choose this path
- Outcome: Retargeting opportunity via Agent 15

**Benefits:**
- Multiple conversion paths (not just email reply)
- Lower friction (form vs composing email)
- Better qualification (form + engagement vs email text)

---

## Revised Timeline (With Enhancements)

### Week 1-2: Core + Subject Lines
- Build Agents 9, 10A, 10B, 11, 12
- Add Agent 10.5 (subject optimizer)
- Test with 100 plain-text emails + optimized subjects

### Week 3: Add Landing Pages
- Build Agent 13 (page generator)
- Build Agent 14 (form analyzer)
- Create professional landing page template
- Test with 100 emails (now include landing page links)
- **Expected:** 40 page visits, 24 form fills, 15 qualified leads

### Week 4: Optimize & Scale
- Refine landing page based on analytics
- A/B test page variants
- Scale to 50/day
- **Expected:** 20 form fills/day, 12 qualified leads/day

### Week 5+: Premium Features
- Add video personalization (strategic accounts)
- Add live visitor tracking
- Add multi-channel retargeting
- Build Agent 15 (performance optimizer)

---

## Tech Stack (Final)

**Required:**
- ✅ Supabase (database, edge functions, storage)
- ✅ Anthropic Claude API (all AI generation)
- ⚠️ SendGrid (email delivery + webhooks)
- ⚠️ QuickChart.io (chart generation - free API)
- ⚠️ Mermaid.ink (diagram generation - free API)

**Optional (Premium):**
- Calendly (meeting booking - free tier)
- Google Analytics (page tracking - free)
- Slack (notifications - free)
- Synthesia (video generation - $30/mo)

**Total monthly cost:** $76.95 (with enhancements)

---

## Success Metrics (Revised with Landing Pages)

### After Week 3 (100 Emails with Landing Pages):
- [ ] Landing page click rate: > 40% (40 visits from 100 emails)
- [ ] Form completion rate: > 60% (24 forms from 40 visits)
- [ ] HOT lead rate: > 30% (7-8 HOT from 24 forms)
- [ ] Agent 14 routing accuracy: > 90% (validated by human)
- [ ] Time per qualified lead: < 5 min (vs 30 min manual)

### After Week 4 (50/Day Sustained):
- [ ] Daily form fills: 3-5 per day (from 50 emails)
- [ ] HOT leads to Steve: 1-2 per day
- [ ] WARM leads to sales: 2-3 per day
- [ ] Human qualification time: 0 minutes (Agent 14 does it)
- [ ] Sales call success rate: > 75% (pre-qualified leads)

---

**Document Version:** 3.0 (Added Agents 10.5, 13, 14 + Landing Pages)
**Last Updated:** October 24, 2025 (PM - Major Enhancements)
**Next Review:** After Week 3 landing page test
**Questions/Feedback:** Contact Steve McMillion

---

**Related Documents:**
- `ULTIMATE_OUTREACH_FLOW_REVIEW.md` - Complete system analysis
- `OUTREACH_QUICK_START.md` - Implementation guide
- `10_24_25_outreach_proposed_flow.md` - Design context
