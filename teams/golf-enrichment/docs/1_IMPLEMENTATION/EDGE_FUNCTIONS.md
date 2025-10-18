# Supabase Edge Functions - Agent Integration

**Project:** golf-course-outreach
**Purpose:** Bridge between Supabase database and claude-agent-sdk-python Render API
**Status:** Design complete, ready to implement

---

## Overview

**3 Edge Functions Required:**

1. **trigger-agent-enrichment** - Calls Render API when enrichment requested
2. **receive-agent-enrichment** - Receives webhook from agents, writes to DB
3. **create-clickup-tasks** - Creates CRM tasks from enriched contacts

---

## Edge Function 1: trigger-agent-enrichment

**Location:** `golf-course-outreach/supabase/functions/trigger-agent-enrichment/index.ts`

**Triggered By:** Database trigger when `golf_courses.enrichment_status` = 'pending'

**Purpose:** Call Render API to start agent enrichment workflow

### Code:

```typescript
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface Course {
  id: string
  course_name: string
  state: string
  website?: string
  phone?: string
}

Deno.serve(async (req) => {
  try {
    const { course_id } = await req.json()

    // Initialize Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Get course data
    const { data: course, error: fetchError } = await supabase
      .from('golf_courses')
      .select('*')
      .eq('id', course_id)
      .single<Course>()

    if (fetchError || !course) {
      throw new Error(`Course not found: ${course_id}`)
    }

    console.log(`🚀 Triggering enrichment for: ${course.course_name}`)

    // Update status to processing
    const { error: updateError } = await supabase
      .from('golf_courses')
      .update({
        enrichment_status: 'processing',
        enrichment_requested_at: new Date().toISOString()
      })
      .eq('id', course_id)

    if (updateError) {
      throw new Error(`Failed to update status: ${updateError.message}`)
    }

    // Call Render API (Agent Workflow)
    const renderUrl = Deno.env.get('RENDER_API_URL') ||
                      'https://agent7-water-hazards.onrender.com'

    const response = await fetch(`${renderUrl}/enrich-course`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        course_name: course.course_name,
        state_code: course.state,
        course_id: course.id,
        use_test_tables: false // PRODUCTION MODE
      }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error(`❌ Render API error: ${errorText}`)

      // Mark as error in database
      await supabase
        .from('golf_courses')
        .update({
          enrichment_status: 'error',
          enrichment_error: `Render API returned ${response.status}: ${errorText}`
        })
        .eq('id', course_id)

      return new Response(
        JSON.stringify({ success: false, error: errorText }),
        { status: 500 }
      )
    }

    console.log(`✅ Agent workflow initiated for: ${course.course_name}`)

    return new Response(
      JSON.stringify({
        success: true,
        course_id,
        message: 'Agent enrichment started',
        expected_completion: '4-7 minutes'
      }),
      { headers: { 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Edge function error:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500 }
    )
  }
})
```

### Database Trigger Setup:

```sql
-- Function that calls the edge function
CREATE OR REPLACE FUNCTION call_trigger_agent_enrichment()
RETURNS TRIGGER AS $$
BEGIN
  -- Call edge function via HTTP (async)
  PERFORM net.http_post(
    url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/trigger-agent-enrichment',
    headers := '{"Content-Type": "application/json", "Authorization": "Bearer ' || current_setting('app.supabase_service_role_key') || '"}'::jsonb,
    body := json_build_object('course_id', NEW.id)::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on status change to 'pending'
CREATE TRIGGER on_enrichment_requested
AFTER UPDATE OF enrichment_status ON golf_courses
FOR EACH ROW
WHEN (NEW.enrichment_status = 'pending' AND
      (OLD.enrichment_status IS NULL OR OLD.enrichment_status != 'pending'))
EXECUTE FUNCTION call_trigger_agent_enrichment();
```

---

## Edge Function 2: receive-agent-enrichment

**Location:** `golf-course-outreach/supabase/functions/receive-agent-enrichment/index.ts`

**Triggered By:** Webhook from Render after agents complete

**Purpose:** Write agent results to Supabase (courses + contacts)

### Code:

```typescript
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface AgentResults {
  course_id: string
  success: boolean
  course_name: string
  state_code: string
  summary: {
    total_cost_usd: number
    total_duration_seconds: number
    contacts_enriched: number
  }
  agent_results: {
    agent6: {
      segmentation: {
        primary_target: string
        confidence: number
        signals: string[]
      }
      range_intel: any
      opportunities: any
    }
    agent7: {
      water_hazard_count: number
      confidence: string
    }
  }
  contacts: Array<{
    name: string
    title: string
    email?: string
    phone?: string
    linkedin?: string
    segment?: string
    tenure_years?: number
    previous_clubs?: any[]
    opportunities?: any
    conversation_starters?: any[]
  }>
}

Deno.serve(async (req) => {
  try {
    const payload: AgentResults = await req.json()

    console.log(`📥 Receiving enrichment for: ${payload.course_name}`)

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // 1. Update course with agent results
    const { error: courseError } = await supabase
      .from('golf_courses')
      .update({
        enrichment_status: payload.success ? 'complete' : 'error',
        enrichment_completed_at: new Date().toISOString(),
        enrichment_error: payload.success ? null : 'Agent workflow failed',

        // Agent 6 results
        segment: payload.agent_results?.agent6?.segmentation?.primary_target,
        segment_confidence: payload.agent_results?.agent6?.segmentation?.confidence,
        opportunities: payload.agent_results?.agent6?.opportunities,
        range_intel: payload.agent_results?.agent6?.range_intel,

        // Agent 7 results
        water_hazards: payload.agent_results?.agent7?.water_hazard_count,

        // Cost tracking
        agent_cost_usd: payload.summary?.total_cost_usd
      })
      .eq('id', payload.course_id)

    if (courseError) {
      throw new Error(`Failed to update course: ${courseError.message}`)
    }

    console.log(`✅ Course updated: ${payload.course_name}`)

    // 2. Insert contacts (triggers Step 5!)
    if (payload.contacts && payload.contacts.length > 0) {
      const contactsToInsert = payload.contacts.map(contact => ({
        golf_course_id: payload.course_id,
        name: contact.name,
        title: contact.title,
        email: contact.email,
        email_confidence: contact.email ? 95 : null,
        linkedin_url: contact.linkedin,
        phone: contact.phone,
        phone_confidence: contact.phone ? 90 : null,
        tenure_years: contact.tenure_years,
        previous_clubs: contact.previous_clubs,
        segment: contact.segment || payload.agent_results?.agent6?.segmentation?.primary_target,
        opportunities: contact.opportunities,
        conversation_starters: contact.conversation_starters,
        enriched_at: new Date().toISOString()
      }))

      const { error: contactsError } = await supabase
        .from('golf_course_contacts')
        .insert(contactsToInsert)

      if (contactsError) {
        console.error(`⚠️ Some contacts failed to insert: ${contactsError.message}`)
        // Don't throw - partial success is OK
      } else {
        console.log(`✅ Inserted ${payload.contacts.length} contacts`)
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        course_id: payload.course_id,
        contacts_inserted: payload.contacts?.length || 0
      }),
      { headers: { 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Webhook processing error:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500 }
    )
  }
})
```

### Render API Update (Send Webhook):

**File:** `production/golf-enrichment/api.py`

**Add after orchestrator completes:**

```python
# In enrich_course endpoint, after orchestrator returns result:

async def send_enrichment_webhook(course_id: str, result: Dict):
    """Send enrichment results back to Supabase"""
    import httpx

    webhook_url = "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/receive-agent-enrichment"

    # Format contacts for Supabase
    contacts = []
    for contact in result.get('enriched_contacts', []):
        contacts.append({
            'name': contact['name'],
            'title': contact['title'],
            'email': contact.get('email'),
            'phone': contact.get('phone'),
            'linkedin': contact.get('linkedin_url'),
            'segment': contact.get('segment'),
            'tenure_years': contact.get('tenure_years'),
            'previous_clubs': contact.get('previous_clubs'),
            'opportunities': contact.get('opportunities'),
            'conversation_starters': contact.get('conversation_starters')
        })

    payload = {
        'course_id': course_id,
        'success': result.get('success', False),
        'course_name': result.get('course_name'),
        'state_code': result.get('state_code'),
        'summary': result.get('summary'),
        'agent_results': result.get('agent_results'),
        'contacts': contacts
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            await client.post(webhook_url, json=payload)
            logger.info(f"✅ Webhook sent for course_id: {course_id}")
        except Exception as e:
            logger.error(f"⚠️ Webhook failed: {e}")
            # Don't fail the whole workflow if webhook fails
```

---

## Edge Function 3: create-clickup-tasks

**Location:** `golf-course-outreach/supabase/functions/create-clickup-tasks/index.ts`

**Triggered By:** Database trigger ON INSERT `golf_course_contacts`

**Purpose:** Create ClickUp task for each enriched contact

### Code:

```typescript
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface Contact {
  id: string
  golf_course_id: string
  name: string
  title: string
  email?: string
  phone?: string
  linkedin_url?: string
  segment?: string
  opportunities?: any
  conversation_starters?: any[]
}

interface Course {
  course_name: string
  website?: string
  phone?: string
  segment?: string
}

Deno.serve(async (req) => {
  try {
    const { record } = await req.json() // Postgres trigger passes 'record'
    const contact: Contact = record

    console.log(`📋 Creating ClickUp task for: ${contact.name}`)

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Get course data for context
    const { data: course } = await supabase
      .from('golf_courses')
      .select('*')
      .eq('id', contact.golf_course_id)
      .single<Course>()

    // Determine ClickUp folder/list based on segment
    const segment = contact.segment || course?.segment || 'both'

    const folderMap: Record<string, string> = {
      'high-end': Deno.env.get('CLICKUP_LIST_HIGH_END')!,
      'budget': Deno.env.get('CLICKUP_LIST_BUDGET')!,
      'both': Deno.env.get('CLICKUP_LIST_BOTH')!
    }

    const listId = folderMap[segment]

    // Format conversation starters
    const startersText = contact.conversation_starters
      ?.map((s: any, i: number) => `${i+1}. [${s.relevance}/10] ${s.text}`)
      .join('\n') || 'No conversation starters available'

    // Format opportunities
    const opportunitiesText = contact.opportunities
      ? Object.entries(contact.opportunities)
          .sort(([,a]: any, [,b]: any) => b - a) // Sort by score descending
          .map(([key, score]) => `- ${key}: ${score}/10`)
          .join('\n')
      : 'No opportunities scored'

    // Get top 2 opportunities
    const topOpportunities = contact.opportunities
      ? Object.entries(contact.opportunities)
          .sort(([,a]: any, [,b]: any) => b - a)
          .slice(0, 2)
      : []

    // Create ClickUp task
    const clickupResponse = await fetch('https://api.clickup.com/api/v2/list/' + listId + '/task', {
      method: 'POST',
      headers: {
        'Authorization': Deno.env.get('CLICKUP_API_KEY')!,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: `${contact.name} - ${contact.title} | ${course?.course_name}`,
        description: `## Contact Info
- **Email:** ${contact.email || 'Not found'}
- **Phone:** ${contact.phone || 'Not found'}
- **LinkedIn:** ${contact.linkedin_url || 'Not found'}
- **Company:** ${course?.course_name}
- **Website:** ${course?.website || 'N/A'}

## Business Intelligence
- **Segment:** ${segment.toUpperCase()} (${course?.segment_confidence || 'N/A'}/10 confidence)
- **Signals:** ${course?.segment ? 'See course record' : 'N/A'}

## Top Opportunities
${opportunitiesText}

## Pre-Written Conversation Starters
${startersText}

## Range Intel
${course?.range_intel ? JSON.stringify(course.range_intel, null, 2) : 'N/A'}
`,
        status: 'to do',
        priority: topOpportunities[0]?.[1] >= 8 ? 2 : 3, // High priority if top opp >= 8
        custom_fields: [
          { id: 'segment_field_id', value: segment },
          { id: 'email_field_id', value: contact.email },
          { id: 'phone_field_id', value: contact.phone },
          { id: 'linkedin_field_id', value: contact.linkedin_url },
          { id: 'top_opp_1_field_id', value: topOpportunities[0]?.[0] },
          { id: 'top_opp_1_score_field_id', value: topOpportunities[0]?.[1] },
          { id: 'top_opp_2_field_id', value: topOpportunities[1]?.[0] },
          { id: 'top_opp_2_score_field_id', value: topOpportunities[1]?.[1] }
        ]
      })
    })

    if (!clickupResponse.ok) {
      const errorText = await clickupResponse.text()
      console.error(`⚠️ ClickUp API error: ${errorText}`)
      // Don't throw - log and continue
      return new Response(
        JSON.stringify({ success: false, error: 'ClickUp API failed', details: errorText }),
        { status: 500 }
      )
    }

    const clickupTask = await clickupResponse.json()
    console.log(`✅ ClickUp task created: ${clickupTask.id}`)

    // Update contact with ClickUp task ID
    await supabase
      .from('golf_course_contacts')
      .update({ clickup_task_id: clickupTask.id })
      .eq('id', contact.id)

    return new Response(
      JSON.stringify({
        success: true,
        contact_id: contact.id,
        clickup_task_id: clickupTask.id,
        clickup_url: clickupTask.url
      }),
      { headers: { 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('ClickUp task creation error:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500 }
    )
  }
})
```

### Database Trigger Setup:

```sql
-- Function that calls the edge function
CREATE OR REPLACE FUNCTION call_create_clickup_task()
RETURNS TRIGGER AS $$
BEGIN
  -- Call edge function to create ClickUp task
  PERFORM net.http_post(
    url := 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/create-clickup-tasks',
    headers := '{"Content-Type": "application/json", "Authorization": "Bearer ' || current_setting('app.supabase_service_role_key') || '"}'::jsonb,
    body := json_build_object('record', row_to_json(NEW))::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on new contact insert
CREATE TRIGGER on_contact_inserted
AFTER INSERT ON golf_course_contacts
FOR EACH ROW
EXECUTE FUNCTION call_create_clickup_task();
```

---

## Environment Variables

### Supabase Edge Functions (Set via `supabase secrets set`)

```bash
# Render API endpoint
RENDER_API_URL=https://agent7-water-hazards.onrender.com

# ClickUp API
CLICKUP_API_KEY=pk_your_key_here
CLICKUP_LIST_HIGH_END=list_id_for_high_end_folder
CLICKUP_LIST_BUDGET=list_id_for_budget_folder
CLICKUP_LIST_BOTH=list_id_for_both_folder

# ClickUp Custom Field IDs (get from ClickUp API)
CLICKUP_FIELD_SEGMENT=field_id_here
CLICKUP_FIELD_EMAIL=field_id_here
CLICKUP_FIELD_PHONE=field_id_here
CLICKUP_FIELD_LINKEDIN=field_id_here
CLICKUP_FIELD_TOP_OPP_1=field_id_here
CLICKUP_FIELD_TOP_OPP_1_SCORE=field_id_here
CLICKUP_FIELD_TOP_OPP_2=field_id_here
CLICKUP_FIELD_TOP_OPP_2_SCORE=field_id_here
```

---

## Deployment Instructions

### Deploy to Supabase:

```bash
# From golf-course-outreach repo

# 1. Create function directories
mkdir -p supabase/functions/trigger-agent-enrichment
mkdir -p supabase/functions/receive-agent-enrichment
mkdir -p supabase/functions/create-clickup-tasks

# 2. Copy code to index.ts files
# ... (use code above)

# 3. Deploy functions
supabase functions deploy trigger-agent-enrichment
supabase functions deploy receive-agent-enrichment
supabase functions deploy create-clickup-tasks

# 4. Set environment variables
supabase secrets set RENDER_API_URL=https://agent7-water-hazards.onrender.com
supabase secrets set CLICKUP_API_KEY=pk_...
# ... (set all vars)

# 5. Apply database triggers
psql -h db.oadmysogtfopkbmrulmq.supabase.co -U postgres -d postgres < triggers.sql
```

---

## Testing Each Function

### Test Function 1 (Trigger):

```bash
# Call edge function directly
curl -X POST 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/trigger-agent-enrichment' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"course_id": "test-course-uuid"}'

# Expected: Render API called, status updated to 'processing'
```

### Test Function 2 (Receive):

```bash
# Send mock webhook
curl -X POST 'https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/receive-agent-enrichment' \
  -H 'Content-Type: application/json' \
  -d '{
    "course_id": "test-uuid",
    "success": true,
    "contacts": [{
      "name": "Test Contact",
      "title": "GM",
      "email": "test@example.com"
    }],
    "agent_results": {...}
  }'

# Expected: Course updated, contacts inserted
```

### Test Function 3 (ClickUp):

```bash
# Insert test contact manually
INSERT INTO golf_course_contacts (golf_course_id, name, title, segment)
VALUES ('test-uuid', 'Test Person', 'General Manager', 'high-end');

# Expected: ClickUp task created in HIGH-END CLUBS folder
```

---

## Error Scenarios & Debugging

### Scenario 1: Trigger doesn't fire

**Symptom:** `enrichment_status` stuck on 'pending'

**Debug:**
```sql
-- Check trigger exists
SELECT * FROM pg_trigger WHERE tgname = 'on_enrichment_requested';

-- Check if http extension enabled
SELECT * FROM pg_extension WHERE extname = 'http';

-- Enable if needed
CREATE EXTENSION IF NOT EXISTS http WITH SCHEMA extensions;
```

**Fix:** Recreate trigger, verify http extension enabled

---

### Scenario 2: Render API timeout

**Symptom:** `enrichment_status = 'processing'` for > 15 minutes

**Debug:**
```sql
SELECT id, course_name, enrichment_status,
       EXTRACT(EPOCH FROM (NOW() - enrichment_requested_at)) as seconds_elapsed
FROM golf_courses
WHERE enrichment_status = 'processing'
  AND enrichment_requested_at < NOW() - INTERVAL '15 minutes';
```

**Fix:**
```sql
-- Mark as error for manual retry
UPDATE golf_courses
SET enrichment_status = 'error',
    enrichment_error = 'Timeout: agents took > 15 minutes'
WHERE id = 'stuck-course-uuid';

-- Then retry
UPDATE golf_courses
SET enrichment_status = 'pending'
WHERE id = 'stuck-course-uuid';
```

---

### Scenario 3: Webhook never received

**Symptom:** Agents complete but `enrichment_status` still 'processing'

**Debug:**
- Check Render logs for webhook send
- Check Supabase edge function logs
- Verify webhook URL correct

**Fix:**
- Re-run agents and monitor webhook
- OR manually insert data from Render response

---

### Scenario 4: ClickUp task not created

**Symptom:** Contact inserted but `clickup_task_id` is NULL

**Debug:**
```sql
SELECT * FROM golf_course_contacts
WHERE enriched_at > NOW() - INTERVAL '1 hour'
  AND clickup_task_id IS NULL;
```

**Fix:**
- Check ClickUp API key valid
- Check list IDs correct
- Manual retry: DELETE contact, re-INSERT (triggers again)

---

## Monitoring Queries

### Health Dashboard:

```sql
-- Overall enrichment health (last 7 days)
SELECT
  enrichment_status,
  COUNT(*) as count,
  ROUND(AVG(agent_cost_usd), 4) as avg_cost,
  ROUND(AVG(EXTRACT(EPOCH FROM (enrichment_completed_at - enrichment_requested_at)))) as avg_duration_seconds
FROM golf_courses
WHERE enrichment_requested_at > NOW() - INTERVAL '7 days'
GROUP BY enrichment_status;

-- Expected output:
-- complete | 45 | 0.1950 | 385
-- error    |  2 | null   | null
-- processing | 1 | null | null
```

### Cost Tracking:

```sql
-- Daily cost
SELECT
  DATE(enrichment_requested_at) as date,
  COUNT(*) as courses_enriched,
  SUM(agent_cost_usd) as total_cost,
  ROUND(AVG(agent_cost_usd), 4) as avg_cost_per_course
FROM golf_courses
WHERE enrichment_status = 'complete'
  AND enrichment_requested_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(enrichment_requested_at)
ORDER BY date DESC;
```

### Success Rate:

```sql
-- Enrichment success rate
SELECT
  ROUND(
    COUNT(*) FILTER (WHERE enrichment_status = 'complete') * 100.0 / COUNT(*),
    2
  ) as success_rate_percent
FROM golf_courses
WHERE enrichment_requested_at IS NOT NULL;
```

---

## Next Steps

1. **Create these 3 edge functions in `golf-course-outreach` repo**
2. **Deploy to Supabase**
3. **Update Render API to send webhooks**
4. **Test end-to-end with manual trigger**

See also:
- `RELIABILITY_PLAYBOOK.md` - Operations guide
- `COST_OPTIMIZATION.md` - Cost analysis
- `../migrations/004_agent_integration_fields.sql` - Schema migration
