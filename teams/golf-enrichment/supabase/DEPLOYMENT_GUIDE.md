# Supabase Edge Functions - Deployment Guide

**Project:** golf-course-outreach (oadmysogtfopkbmrulmq)
**Status:** ✅ Functions Deployed - Needs Environment Variables
**Date:** October 18, 2024

---

## ✅ What's Deployed

### Edge Functions (3):
1. **trigger-agent-enrichment** - Calls Render API when enrichment requested
2. **receive-agent-enrichment** - Receives webhook from agents, writes to DB
3. **create-clickup-tasks** - Creates ClickUp outreach task with rich description

### Database:
- ✅ Migration 004 applied (agent integration fields)
- ✅ Migration 005 applied (outreach tables)
- ✅ Triggers active (auto-call edge functions)
- ✅ Views created (monitoring queries)

---

## 🔧 Required Environment Variables

Set these in Supabase dashboard or via Supabase CLI:

```bash
# Method 1: Supabase Dashboard
# Go to: https://supabase.com/dashboard/project/oadmysogtfopkbmrulmq/settings/functions
# Add each secret in Edge Functions > Manage secrets

# Method 2: Supabase CLI
supabase secrets set RENDER_API_URL=https://agent7-water-hazards.onrender.com
supabase secrets set CLICKUP_API_KEY=your_api_key_here
```

### Required Secrets:

1. **RENDER_API_URL**
   - Value: `https://agent7-water-hazards.onrender.com`
   - Used by: trigger-agent-enrichment
   - Purpose: Endpoint for agent workflow API

2. **CLICKUP_API_KEY**
   - Value: `pk_...` (your personal API key)
   - Used by: create-clickup-tasks
   - Purpose: Create tasks in ClickUp
   - Get from: https://app.clickup.com/settings/apps

---

## 📋 ClickUp Field IDs (Already Hardcoded)

These are already set in the edge function code:

### Outreach Activities List (901413111587):
- Target Segment: `c52d0d6d-5f3e-4c5e-aa1f-256c27a1a212`
- Top Opportunity #1: `31bb96ce-439c-47b2-8bd6-8cdffd523fc7`
- Top Opportunity #1 Score: `1c6f30b2-930d-45d0-a14f-e28cc5c738b1`
- Top Opportunity #2: `2bfb13d6-be8b-4f80-84d8-4e07a44153b4`
- Top Opportunity #2 Score: `9c1a8615-5953-4826-9492-a77f74e9aa37`

---

## 🔄 Data Flow

```
1. User/System: UPDATE golf_courses SET enrichment_status = 'pending'
   ↓
2. DB Trigger → Edge Function: trigger-agent-enrichment
   ↓
3. Edge Function → Render API: POST /enrich-course
   ↓
4. Agents run (4-7 minutes)
   ↓
5. Agents complete → Webhook → Edge Function: receive-agent-enrichment
   ↓
6. Edge Function writes: golf_courses + golf_course_contacts (4-7 rows)
   ↓
7. DB Trigger ON INSERT contacts → Edge Function: create-clickup-tasks
   ↓
8. Edge Function creates: ClickUp task in Outreach Activities (901413111587)
   - Description: ALL contacts + intel + conversation starters
   - Fields: Target Segment + Top 2 Opportunities with scores
```

---

## 🧪 Testing Guide

### Test 1: Trigger Enrichment

```sql
-- Pick a test course
SELECT id, course_name, enrichment_status
FROM golf_courses
WHERE enrichment_status IS NULL
LIMIT 1;

-- Trigger enrichment
UPDATE golf_courses
SET enrichment_status = 'pending'
WHERE id = YOUR_COURSE_ID;

-- Monitor status (should change to 'processing' immediately)
SELECT enrichment_status, enrichment_requested_at
FROM golf_courses
WHERE id = YOUR_COURSE_ID;
```

### Test 2: Check Logs

```bash
# View edge function logs in Supabase dashboard:
# https://supabase.com/dashboard/project/oadmysogtfopkbmrulmq/logs/edge-functions

# Look for:
# - "🚀 Triggering enrichment for: [course name]"
# - "✅ Agent workflow initiated"
```

### Test 3: Wait for Completion (4-7 min)

```sql
-- Check if enrichment completed
SELECT
  enrichment_status,
  enrichment_completed_at,
  agent_cost_usd,
  segment,
  water_hazards
FROM golf_courses
WHERE id = YOUR_COURSE_ID;

-- Check contacts inserted
SELECT contact_name, contact_email, contact_phone, linkedin_url
FROM golf_course_contacts
WHERE golf_course_id = YOUR_COURSE_ID;
```

### Test 4: Verify ClickUp Task Created

```sql
-- Get ClickUp task IDs
SELECT contact_name, clickup_task_id
FROM golf_course_contacts
WHERE golf_course_id = YOUR_COURSE_ID;
```

Then check in ClickUp: https://app.clickup.com/9014129779/v/l/901413111587

---

## 🚨 Troubleshooting

### Issue: Trigger doesn't fire

**Check:**
```sql
SELECT * FROM pg_trigger WHERE tgname = 'on_enrichment_requested';
SELECT * FROM pg_extension WHERE extname = 'http';
```

**Fix:**
```sql
CREATE EXTENSION IF NOT EXISTS http WITH SCHEMA extensions;
```

### Issue: Edge function fails

**Check logs:**
- Supabase Dashboard → Edge Functions → Logs
- Look for error messages

**Common issues:**
- Missing environment variables
- ClickUp API key invalid
- Render API not responding

### Issue: ClickUp task not created

**Check:**
```sql
SELECT * FROM golf_course_contacts
WHERE enriched_at IS NOT NULL AND clickup_task_id IS NULL;
```

**Debug:**
- Check create-clickup-tasks edge function logs
- Verify CLICKUP_API_KEY is set
- Verify field IDs are correct

---

## 📊 Monitoring Queries

```sql
-- Overall health
SELECT * FROM v_enrichment_health;

-- Recent errors
SELECT * FROM v_enrichment_errors;

-- Contacts waiting for ClickUp sync
SELECT contact_name, enriched_at
FROM golf_course_contacts
WHERE enriched_at IS NOT NULL
  AND clickup_task_id IS NULL
  AND enriched_at > NOW() - INTERVAL '1 hour';
```

---

## 🎯 Success Criteria

**System is working when:**
- ✅ enrichment_status changes: pending → processing → complete
- ✅ Course updated with segment, water_hazards, opportunities
- ✅ 4-7 contacts inserted with email, phone, LinkedIn
- ✅ ClickUp task auto-created in Outreach Activities list
- ✅ Task description shows ALL contacts + conversation starters
- ✅ Target Segment field populated for filtering

---

## 🚀 Next Steps After Testing

1. Update Render API to send webhook to receive-agent-enrichment
2. Test with 5-10 courses
3. Monitor costs and performance
4. Create ClickUp custom views for sales team
5. Document any edge cases discovered

---

**Last Updated:** October 18, 2024
**Deployed By:** Claude Code Agent SDK
