# Outreach Funnel Goals (Phase 7)
**Status:** FUTURE (Build after Phase 6 complete)
**Purpose:** Don't forget these goals - document now, build later

---

## Overview

**When:** After automation pipeline complete (Phase 6)

**What:** ClickUp-controlled email sequences that use business intelligence for personalized outreach

**Why:** Transform business intel into actual revenue (meetings → deals → customers)

---

## 3-Track Email Sequences

### Track 1: High-End Clubs (Buy + Lease Programs)

**Segment:** `primary_target = "high-end"`

**Top Opportunities:** range_ball_buy (8-9/10), range_ball_lease (7-9/10)

**Email Sequence:**

**Email 1 (Day 0): Lease Program Introduction**
- Subject: `{Company} + Range Ball Management | Quick Question`
- Focus: Fresh balls, eliminate disposal, predictable cost
- CTA: 15-minute call
- Uses conversation starter #1 (highest relevance)

**Email 2 (Day 3): Buy Program Pivot**
- Subject: `Re: {Company} | Alternative Approach`
- Focus: Turn waste into revenue, unique technology
- CTA: Sample ball demonstration
- Uses conversation starter #2

**Email 3 (Day 7): Sustainability Angle**
- Subject: `{Company}'s Environmental Impact Opportunity`
- Focus: ESG compliance, waste reduction goals
- CTA: Case study from peer club
- Uses sustainability signals from business intel

---

### Track 2: Budget Clubs (Sell + Lease Programs)

**Segment:** `primary_target = "budget"`

**Top Opportunities:** range_ball_sell (7-9/10), range_ball_lease (6-8/10)

**Email Sequence:**

**Email 1 (Day 0): Sell Program Introduction**
- Subject: `Cut Range Ball Costs 40-60% at {Company}`
- Focus: Cost savings, quality maintained, proof
- CTA: Annual cost comparison
- Uses conversation starter #1

**Email 2 (Day 3): Cost Breakdown**
- Subject: `Re: {Company} | Here's How Much You'd Save`
- Focus: Calculate savings based on practice range size
- CTA: Free sample balls
- Personalized math using range intel

**Email 3 (Day 7): Lease Alternative**
- Subject: `{Company} | No-Upfront-Cost Option`
- Focus: Lease program (if they can't afford bulk purchase)
- CTA: Flexible terms discussion
- Uses conversation starter focused on capital constraints

---

### Track 3: Both/Mixed Signals (Test Multiple)

**Segment:** `primary_target = "both"` OR low confidence scores

**Strategy:** Test all value props, see what resonates

**Email Sequence:**

**Email 1 (Day 0): General Value Prop**
- Subject: `{Company} | 3 Ways We Help Golf Courses`
- Focus: Mention all programs (buy, sell, lease)
- CTA: Which interests you most?
- Discovery-focused

**Email 2 (Day 3): Top Opportunity Focus**
- Subject: `Re: {Company} | Following Up on {Top Opportunity}`
- Focus: Whichever program scored highest
- CTA: Specific to that program
- Uses top-scored conversation starter

**Email 3 (Day 7): Alternative Approach**
- Subject: `{Company} | Different Angle`
- Focus: Second-highest opportunity
- CTA: Open-ended discovery call
- Flexible based on response signals

---

## Email Personalization (Using Business Intel)

### Dynamic Fields (Pulled from Agent 6 Output)

**All Emails:**
- `{Company}` - Course name
- `{Name}` - Contact first name
- `{Title}` - Contact title

**From Business Intel:**
- `{Recent_Upgrade}` - e.g., "your recent irrigation system upgrade"
- `{Quality_Signal}` - e.g., "your 4.8-star rating"
- `{Sustainability_Signal}` - e.g., "River Creek's commitment to sustainability"
- `{Competitor_Name}` - e.g., "Hermitage Country Club"
- `{Practice_Range_Size}` - e.g., "12-tee practice facility"

**From Opportunity Scores:**
- Primary value prop to lead with
- Secondary value prop for follow-up
- Specific pain point to address

---

## Response Tracking

### Metrics to Measure

**Per Segment:**
- Open rate (% who open emails)
- Reply rate (% who respond)
- Meeting booked rate (% who schedule call)
- Conversion rate (% who become customers)

**Per Opportunity:**
- Which opportunities drive most engagement?
- Does Buy, Sell, or Lease resonate more?
- Should we reorder the pitch?

**Per Conversation Starter:**
- Which starters get the most replies?
- What relevance score correlates with response?
- Refine Agent 6 based on real-world data

---

## A/B Testing Framework

### Test Variables

**Subject Lines:**
- Question format vs statement
- With company name vs without
- Specific benefit vs curiosity

**Opening Lines:**
- Use conversation starter #1 vs #2
- Generic intro vs hyper-specific
- Flattery vs pain point

**Call-to-Action:**
- 15-min call vs sample demonstration
- Specific date/time vs open-ended
- Link vs reply

### Test Process

1. Segment leads into A/B groups (random split)
2. Send variant A to 50%, variant B to 50%
3. Measure response rates
4. Winner becomes new control
5. Iterate continuously

---

## ClickUp Automation Triggers

### Trigger 1: New Lead → Send Email 1

**When:** Task created in "New Leads" list
**Wait:** 0 days
**Action:** Send Email 1 (track-specific)
**Update:** Move to "Contacted" list

### Trigger 2: Email 1 → Send Email 2

**When:** 3 days after Email 1 sent, no reply
**Action:** Send Email 2 (follow-up)
**Update:** Add tag "Follow-up 1"

### Trigger 3: Email 2 → Send Email 3

**When:** 4 days after Email 2 sent (7 days total), no reply
**Action:** Send Email 3 (final touch)
**Update:** Add tag "Follow-up 2"

### Trigger 4: Reply Received → Pause Sequence

**When:** Contact replies to any email
**Action:** Stop automated sequence
**Update:** Move to "Qualified" list, assign to sales rep

### Trigger 5: Meeting Booked → Convert

**When:** Meeting scheduled
**Action:** Stop sequence
**Update:** Move to "Negotiating" list

---

## Integration Requirements

**Email Service:**
- SendGrid or Mailgun (transactional email)
- Track opens, clicks, replies
- Webhook for reply detection

**ClickUp Automations:**
- Native automations OR
- Zapier/Make.com for complex logic

**Supabase Edge Functions:**
- `send_email` - Formats and sends via email service
- `track_response` - Records opens/replies in outreach_history
- `update_clickup_on_reply` - Moves tasks when replies detected

---

## Templates (To Be Created in Phase 7)

1. `templates/email_high_end_1.md` - High-end Email 1
2. `templates/email_high_end_2.md` - High-end Email 2
3. `templates/email_high_end_3.md` - High-end Email 3
4. `templates/email_budget_1.md` - Budget Email 1
5. `templates/email_budget_2.md` - Budget Email 2
6. `templates/email_budget_3.md` - Budget Email 3
7. `templates/email_both_1.md` - Both Email 1
8. `templates/email_both_2.md` - Both Email 2
9. `templates/email_both_3.md` - Both Email 3

---

## Success Metrics (When Live)

### Target Performance

| Metric | Target | Industry Avg |
|--------|--------|--------------|
| Open Rate | 40%+ | 20-25% |
| Reply Rate | 10%+ | 2-5% |
| Meeting Booked | 5%+ | 1-2% |
| Conversion to Customer | 2%+ | 0.5-1% |

**Why Higher Than Industry:**
- Personalized with real intel
- Value-prop matched to segment
- Conversation starters tested
- Not generic cold outreach

---

## Current Status

**Phase:** NOT STARTED (Phase 7 - Future)

**Blockers:**
- Need automation pipeline (Phase 6)
- Need ClickUp integration (Phase 3)
- Need Supabase storage (Phase 2)

**Estimated Start:** Week 5+ (after infrastructure complete)

**Estimated Completion:** Week 6-7

---

**REMEMBER:** This is the end goal. Don't build until Phases 1-6 are rock solid.

Save this file. Reference it. Come back to it when ready.

---

**Last Updated:** 2025-01-17
