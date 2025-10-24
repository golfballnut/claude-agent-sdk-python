// Edge Function: notify-course-error
// Purpose: Create ClickUp task when course enrichment fails
// Triggered by: Database trigger on enrichment_status → 'error'
// Auth: Configured via Supabase dashboard to allow anonymous calls

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

const CLICKUP_API_KEY = Deno.env.get('CLICKUP_API_KEY')
const PERSONAL_LIST_ID = '901409749476' // User's personal task list

interface ErrorPayload {
  course_id: number
  course_name: string
  error_message: string
  timestamp: string
}

serve(async (req) => {
  try {
    const payload: ErrorPayload = await req.json()

    console.log(`🚨 Course error notification triggered for: ${payload.course_name} (ID: ${payload.course_id})`)

    // Create ClickUp task
    const taskData = {
      name: `🚨 Course Enrichment Error: ${payload.course_name}`,
      description: `# Enrichment Error

**Course:** ${payload.course_name}
**Course ID:** ${payload.course_id}
**Timestamp:** ${payload.timestamp}

## Error Message
\`\`\`
${payload.error_message}
\`\`\`

## Investigation Steps

1. **Check Render logs:**
   https://dashboard.render.com/web/srv-csa82fj6l47c738vhsrg/logs

2. **View course in Supabase:**
   \`\`\`sql
   SELECT * FROM golf_courses WHERE id = ${payload.course_id};
   \`\`\`

3. **Check course in ClickUp:**
   Search for: ${payload.course_name}

4. **Retry enrichment:**
   \`\`\`sql
   UPDATE golf_courses
   SET enrichment_status = 'pending',
       enrichment_requested_at = NOW()
   WHERE id = ${payload.course_id};
   \`\`\`

## Common Error Patterns

- **Timeout errors:** Retry usually works
- **Database errors:** Check trigger functions
- **ClickUp sync errors:** Check field mappings
- **LinkedIn scraping:** API rate limits

---

*Auto-generated error notification*`,
      markdown_description: `# Enrichment Error

**Course:** ${payload.course_name}
**Course ID:** ${payload.course_id}
**Timestamp:** ${payload.timestamp}

## Error Message
\`\`\`
${payload.error_message}
\`\`\`

## Investigation Steps

1. **Check Render logs:**
   https://dashboard.render.com/web/srv-csa82fj6l47c738vhsrg/logs

2. **View course in Supabase:**
   \`\`\`sql
   SELECT * FROM golf_courses WHERE id = ${payload.course_id};
   \`\`\`

3. **Check course in ClickUp:**
   Search for: ${payload.course_name}

4. **Retry enrichment:**
   \`\`\`sql
   UPDATE golf_courses
   SET enrichment_status = 'pending',
       enrichment_requested_at = NOW()
   WHERE id = ${payload.course_id};
   \`\`\`

## Common Error Patterns

- **Timeout errors:** Retry usually works
- **Database errors:** Check trigger functions
- **ClickUp sync errors:** Check field mappings
- **LinkedIn scraping:** API rate limits

---

*Auto-generated error notification*`,
      priority: 2, // High priority
      tags: ['error', 'needs-investigation', 'auto-created'],
      assignees: [90096078] // Steve McMillian
    }

    const clickupResponse = await fetch(`https://api.clickup.com/api/v2/list/${PERSONAL_LIST_ID}/task`, {
      method: 'POST',
      headers: {
        'Authorization': CLICKUP_API_KEY!,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(taskData)
    })

    if (!clickupResponse.ok) {
      const errorText = await clickupResponse.text()
      throw new Error(`ClickUp API error: ${clickupResponse.status} - ${errorText}`)
    }

    const clickupTask = await clickupResponse.json()
    console.log(`✅ Created error notification task: ${clickupTask.id}`)

    return new Response(
      JSON.stringify({
        success: true,
        task_id: clickupTask.id,
        task_url: clickupTask.url
      }),
      { headers: { 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('❌ Error creating notification:', error)
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    )
  }
})
