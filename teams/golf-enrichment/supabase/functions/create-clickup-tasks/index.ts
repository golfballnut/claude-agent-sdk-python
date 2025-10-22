import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// ============================================================================
// INTERFACES
// ============================================================================

interface WebhookPayload {
  course_id: number
  course_name: string
  state_code: string
}

interface ClickUpTaskData {
  name: string
  description: string
  status?: string
  priority?: number
  custom_fields?: Array<{ id: string; value: any }>
  tags?: string[]
}

interface UpsertResult {
  taskId: string
  action: 'created' | 'updated' | 'protected'
}

// ============================================================================
// CLICKUP FIELD MAPPINGS
// ============================================================================

// State dropdown option indices (Golf Courses & Contacts & Outreach lists)
const STATE_OPTION_INDEX: { [key: string]: number } = {
  'VA': 0,
  'MD': 1,
  'NC': 2,
  'PA': 3,
  'DC': 4,
  'WV': 5,
  'SC': 6,
  'TN': 7,
  'FL': 8,
  'GA': 9,
  'NY': 10,
  'NJ': 11,
  'OH': 12
}

// Segment dropdown option indices (Golf Courses list - field: 27bbd669-557d-428a-bdfd-24ae7b366127)
const SEGMENT_OPTION_INDEX: { [key: string]: number } = {
  'high-end': 0,
  'budget': 1,
  'both': 2,
  'unknown': 3
}

// Target Segment dropdown option indices (Outreach Activities list - field: c52d0d6d-5f3e-4c5e-aa1f-256c27a1a212)
const TARGET_SEGMENT_OPTION_INDEX: { [key: string]: number } = {
  'high-end': 0,
  'budget': 1,
  'both': 2
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Idempotent task upsert - tries update, falls back to create
 */
async function upsertClickUpTask(
  taskData: ClickUpTaskData,
  existingTaskId: string | null,
  listId: string,
  apiKey: string
): Promise<UpsertResult> {

  // CASE 1: No existing task → CREATE
  if (!existingTaskId) {
    console.log(`📋 No existing task, creating new in list ${listId}`)
    const task = await createClickUpTask(listId, taskData, apiKey)
    return { taskId: task.id, action: 'created' }
  }

  // CASE 2: Has existing task → TRY UPDATE
  try {
    console.log(`🔄 Attempting to update existing task ${existingTaskId}`)

    const updateResponse = await fetch(
      `https://api.clickup.com/api/v2/task/${existingTaskId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
      }
    )

    // CASE 2A: Task deleted in ClickUp (404)
    if (updateResponse.status === 404) {
      console.log(`⚠️ Task ${existingTaskId} not found (deleted), creating new`)
      const task = await createClickUpTask(listId, taskData, apiKey)
      return { taskId: task.id, action: 'created' }
    }

    // CASE 2B: Update failed (other error)
    if (!updateResponse.ok) {
      const errorText = await updateResponse.text()
      throw new Error(`ClickUp API error ${updateResponse.status}: ${errorText}`)
    }

    // CASE 2C: Update succeeded
    console.log(`✅ Successfully updated task ${existingTaskId}`)
    return { taskId: existingTaskId, action: 'updated' }

  } catch (error) {
    // CASE 2D: Network/API failure → Fallback to CREATE
    console.error(`❌ Update failed: ${error.message}`)
    console.log(`🔄 Fallback: Creating new task`)

    try {
      const task = await createClickUpTask(listId, taskData, apiKey)
      return { taskId: task.id, action: 'created' }
    } catch (createError) {
      throw new Error(`Both update and create failed: ${createError.message}`)
    }
  }
}

/**
 * Create new ClickUp task
 */
async function createClickUpTask(
  listId: string,
  taskData: ClickUpTaskData,
  apiKey: string
): Promise<any> {
  const response = await fetch(
    `https://api.clickup.com/api/v2/list/${listId}/task`,
    {
      method: 'POST',
      headers: {
        'Authorization': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(taskData)
    }
  )

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`ClickUp create failed ${response.status}: ${errorText}`)
  }

  return await response.json()
}

/**
 * Format opportunity name for display
 */
function formatOpportunityName(key: string): string {
  const formatted = key.replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
  return formatted
}

/**
 * Get contact rationale based on title
 */
function getContactRationale(title: string, isPrimary: boolean): string {
  const lowerTitle = title.toLowerCase()

  if (isPrimary) {
    if (lowerTitle.includes('general manager') || lowerTitle.includes('gm')) {
      return 'General Manager = budget authority + purchasing decisions'
    }
    if (lowerTitle.includes('director of golf')) {
      return 'Director of Golf = oversees golf operations including ranges'
    }
    if (lowerTitle.includes('head professional') || lowerTitle.includes('head golf')) {
      return 'Head Professional = manages golf operations, likely decision-maker'
    }
  }

  if (lowerTitle.includes('superintendent')) {
    return 'Manages course maintenance. Good for retrieval cross-sell opportunity'
  }
  if (lowerTitle.includes('director of instruction') || lowerTitle.includes('teaching')) {
    return 'Heavy range user, can influence range ball decisions'
  }
  if (lowerTitle.includes('assistant')) {
    return 'Can provide operational context, may escalate to decision-maker'
  }

  return 'Secondary contact - may have input or can forward to decision-maker'
}

// ============================================================================
// MAIN HANDLER
// ============================================================================

Deno.serve(async (req) => {
  try {
    const payload: WebhookPayload = await req.json()

    console.log(`📥 ClickUp sync requested for: ${payload.course_name}`)
    console.log(`   Course ID: ${payload.course_id}`)

    // Initialize Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Initialize ClickUp API key
    const clickupApiKey = Deno.env.get('CLICKUP_API_KEY')
    if (!clickupApiKey) {
      throw new Error('CLICKUP_API_KEY not set in environment')
    }

    // ========================================================================
    // READ DATA FROM DATABASE (Agent 8 already wrote it)
    // ========================================================================

    console.log(`\n📖 Reading data from database...`)

    // Get course data (written by Agent 8)
    const { data: courseData, error: courseError } = await supabase
      .from('golf_courses')
      .select('*')
      .eq('id', payload.course_id)
      .single()

    if (courseError || !courseData) {
      throw new Error(`Course ${payload.course_id} not found in database: ${courseError?.message}`)
    }

    console.log(`✅ Course data loaded: ${courseData.course_name}`)

    // Get contacts (written by Agent 8)
    const { data: contactsData, error: contactsError } = await supabase
      .from('golf_course_contacts')
      .select('*')
      .eq('golf_course_id', payload.course_id)

    if (contactsError) {
      throw new Error(`Failed to load contacts: ${contactsError.message}`)
    }

    if (!contactsData || contactsData.length === 0) {
      throw new Error(`No contacts found for course ${payload.course_id}`)
    }

    console.log(`✅ Contacts loaded: ${contactsData.length}`)

    const results = {
      course_task: null as any,
      contact_tasks: [] as any[],
      outreach_task: null as any,
      errors: [] as string[]
    }

    // ========================================================================
    // STEP 1: Create/Update Golf Course Task
    // ========================================================================

    try {
      console.log(`\n🏌️ [1/3] Processing Golf Course task...`)

      const courseTaskData: ClickUpTaskData = {
        name: `🏌️ ${courseData.course_name}`,
        description: `${courseData.city || ''}, ${payload.state_code}`,
        // Don't set status - let ClickUp use list default
        custom_fields: [
          // Segment - use option index
          { id: '27bbd669-557d-428a-bdfd-24ae7b366127', value: SEGMENT_OPTION_INDEX[courseData.segment?.toLowerCase() || 'unknown'] },
          // Segment Confidence
          { id: 'dc651567-580d-4e4c-9559-f8d865eb834a', value: courseData.segment_confidence || 0 },
          // Water Hazards
          { id: '56308d92-19fd-453d-8ea0-cda5d008f951', value: courseData.water_hazards },
          // Agent Cost (convert to cents)
          { id: '3e1b1cf8-057a-47c6-baa1-9f41bc46e199', value: courseData.agent_cost_usd ? courseData.agent_cost_usd * 100 : 0 },
          // Website
          { id: '2e52887f-d13c-44d1-bcc4-e6586e818ab3', value: courseData.website },
          // State - use option index
          { id: '81bc2505-28a7-4290-a557-50e49e410732', value: STATE_OPTION_INDEX[payload.state_code] }
        ],
        tags: ['golf course', payload.state_code.toLowerCase()]
      }

      const courseResult = await upsertClickUpTask(
        courseTaskData,
        courseData.clickup_task_id,
        '901413061864', // Golf Courses list
        clickupApiKey
      )

      // Update database with task ID
      await supabase
        .from('golf_courses')
        .update({
          clickup_task_id: courseResult.taskId,
          clickup_synced_at: new Date().toISOString()
        })
        .eq('id', payload.course_id)

      results.course_task = courseResult
      console.log(`✅ Course task ${courseResult.action}: ${courseResult.taskId}`)

    } catch (error) {
      const errorMsg = `Golf Course task failed: ${error.message}`
      console.error(`❌ ${errorMsg}`)
      results.errors.push(errorMsg)
    }

    // ========================================================================
    // STEP 2: Create/Update Contact Tasks
    // ========================================================================

    console.log(`\n👥 [2/3] Processing ${contactsData.length} Contact tasks...`)

    const contactTaskIds: string[] = []

    for (let i = 0; i < contactsData.length; i++) {
      const contact = contactsData[i]

      try {
        console.log(`   Processing contact ${i + 1}/${contactsData.length}: ${contact.contact_name}`)

        const contactTaskData: ClickUpTaskData = {
          name: `👤 ${contact.contact_name} - ${contact.contact_title}`,
          description: `Email: ${contact.contact_email || 'Not found'}${contact.email_confidence_score ? ` (${contact.email_confidence_score}% confidence, verified)` : ''}
Phone: ${contact.contact_phone || 'Not found'}
LinkedIn: ${contact.linkedin_url || 'Not found'}

${contact.tenure_years ? `Tenure: ${contact.tenure_years} years` : 'Tenure: Unknown'}${contact.tenure_start_date ? ` (Since ${contact.tenure_start_date})` : ''}
${contact.previous_clubs && contact.previous_clubs.length > 0 ? `Previous Clubs: ${JSON.stringify(contact.previous_clubs)}` : ''}

Enrichment Status:
${contact.email_discovery_method ? `Email verified via ${contact.email_discovery_method}` : ''}
${contact.email_confidence_score ? `Confidence Score: ${contact.email_confidence_score}%` : ''}
Enriched: ${contact.enriched_at ? new Date(contact.enriched_at).toISOString().split('T')[0] : new Date().toISOString().split('T')[0]}`,
          // Don't set status - let ClickUp use list default
          custom_fields: [
            // Email
            { id: '592c3d27-07af-42ce-a6c0-beb158305f9d', value: contact.contact_email },
            // Phone - REMOVED (causes validation error, keep in description only)
            // LinkedIn URL
            { id: 'f94bff39-d2de-4b6f-a010-cdafce7f2621', value: contact.linkedin_url },
            // Tenure Years
            { id: '2bf67cf7-d7b1-4bbd-a353-5d3de9d032d1', value: contact.tenure_years ? parseFloat(String(contact.tenure_years)) : null },
            // Previous Clubs
            { id: 'f41625fc-e195-4044-a30b-86d5ea36a523', value: contact.previous_clubs ? JSON.stringify(contact.previous_clubs) : null },
            // Course relationship
            { id: 'b31efd5f-cae0-4920-aeb9-17542badffe3', value: results.course_task?.taskId ? [results.course_task.taskId] : [] },
            // Enriched By Agents
            { id: '5a5521a2-7502-481f-b7c4-f6d54b5e4f67', value: true },
            // Is Active
            { id: '7dd9fe34-f8a4-44a2-818f-4ac28cb32364', value: true },
            // State - use option index
            { id: '81bc2505-28a7-4290-a557-50e49e410732', value: STATE_OPTION_INDEX[payload.state_code] }
          ],
          tags: ['contact', payload.state_code.toLowerCase(), 'enriched']
        }

        const contactResult = await upsertClickUpTask(
          contactTaskData,
          contact.clickup_task_id,
          '901413061863', // Contacts list
          clickupApiKey
        )

        contactTaskIds.push(contactResult.taskId)

        // Update database with task ID
        await supabase
          .from('golf_course_contacts')
          .update({
            clickup_task_id: contactResult.taskId,
            clickup_synced_at: new Date().toISOString()
          })
          .eq('contact_id', contact.contact_id)

        results.contact_tasks.push(contactResult)
        console.log(`   ✅ Contact task ${contactResult.action}: ${contact.contact_name} (${contactResult.taskId})`)

      } catch (error) {
        const errorMsg = `Contact ${contact.contact_name} task failed: ${error.message}`
        console.error(`   ❌ ${errorMsg}`)
        results.errors.push(errorMsg)
      }
    }

    // ========================================================================
    // STEP 3: Create/Update Outreach Activity Task
    // ========================================================================

    console.log(`\n📞 [3/3] Processing Outreach Activity task...`)

    try {
      // PROTECTION: Check if course has existing outreach with ClickUp task
      const { data: outreachDb } = await supabase
        .from('outreach_activities')
        .select('activity_id, clickup_task_id, status')
        .eq('golf_course_id', payload.course_id)
        .maybeSingle()

      if (outreachDb && outreachDb.clickup_task_id) {
        console.log(`⚠️  PROTECTION ACTIVATED!`)
        console.log(`    Course ${payload.course_id} (${payload.course_name})`)
        console.log(`    Has existing outreach task: ${outreachDb.clickup_task_id}`)
        console.log(`    Status: ${outreachDb.status}`)
        console.log(`    SKIPPING outreach creation to protect active sales workflow`)

        results.outreach_task = {
          taskId: outreachDb.clickup_task_id,
          action: 'protected'
        }

        console.log(`✅ Course + Contact tasks processed, Outreach protected`)

      } else {
        console.log(`✅ No existing outreach - safe to create/update`)

        // Build rich description with ALL contacts
        const contactsSection = contactsData.map((contact, index) => {
          const isPrimary = index === 0
          return `### 👤 ${contact.contact_name} - ${contact.contact_title}${isPrimary ? ' ⭐ PRIMARY' : ''}

📧 Email: ${contact.contact_email || 'Not found'}${contact.email_confidence_score ? ` (${contact.email_confidence_score}% confidence, verified via ${contact.email_discovery_method})` : ''}
📱 Phone: ${contact.contact_phone || 'Not found'}${contact.phone_source ? ` (verified via ${contact.phone_source})` : ''}
💼 LinkedIn: ${contact.linkedin_url || 'Not found'}
⏱️ Tenure: ${contact.tenure_years ? contact.tenure_years + ' years' : 'Unknown'}${contact.tenure_start_date ? ` (since ${contact.tenure_start_date})` : ''}${contact.tenure_years && parseFloat(String(contact.tenure_years)) > 15 ? ' ⭐ LONG TENURE!' : ''}

**Why Contact:** ${getContactRationale(contact.contact_title, isPrimary)}`
        }).join('\n\n---\n\n')

        // Parse opportunities from database
        const opportunities = courseData.opportunities ? (typeof courseData.opportunities === 'string' ? JSON.parse(courseData.opportunities) : courseData.opportunities) : {}
        const oppEntries = Object.entries(opportunities)
          .filter(([key]) => !key.includes('primary'))
          .sort(([,a], [,b]) => (b as number) - (a as number))

        const oppText = oppEntries.length > 0
          ? oppEntries.map(([key, score], idx) => `${idx + 1}. ${formatOpportunityName(key)}: ${score}/10`).join('\n')
          : 'No specific opportunities scored'

        const description = `# 👥 DECISION-MAKERS (${contactsData.length} contacts)

${contactsSection}

═══════════════════════════════════════════════════════════

## 🏌️ COURSE INTELLIGENCE

**${courseData.course_name}**
🌐 Website: ${courseData.website || 'N/A'}
📞 Main: ${courseData.phone || 'N/A'}
📍 ${courseData.city || courseData.course_name}, ${payload.state_code}

**Segment:** ${courseData.segment?.toUpperCase() || 'UNKNOWN'} (${courseData.segment_confidence || 0}/10 confidence)
${courseData.segment_signals ? '- Signals: ' + JSON.stringify(courseData.segment_signals) : ''}

**Water Features:**
- Rating: ${courseData.water_hazard_rating?.toUpperCase() || 'Unknown'}
${courseData.water_hazards ? `- Count: ${courseData.water_hazards}` : ''}
- Retrieval Opportunity: ${opportunities.ball_retrieval || 'N/A'}/10

**Top Opportunities:**
${oppText}

**Primary Pitch:** ${opportunities.primary_pitch || 'Custom ball program consultation'}

═══════════════════════════════════════════════════════════

## 💡 NEXT ACTIONS

1. ${courseData.segment_confidence < 7 ? '⚠️ LOW CONFIDENCE SEGMENT - Manual research needed' : 'Review segment classification'}
2. Start outreach with ${contactsData[0]?.contact_name} (${contactsData[0]?.contact_title})
3. ${contactsData[0]?.linkedin_url ? '✅ LinkedIn available for multi-channel approach' : '📧 Email/phone only'}
4. ${opportunities.ball_retrieval >= 7 ? '🎯 CROSS-SELL: High ball retrieval opportunity!' : ''}
5. ${contactsData.filter(c => c.tenure_years && parseFloat(String(c.tenure_years)) > 15).length > 0 ? '⭐ Long-tenured contacts = strong relationships, personalize accordingly' : ''}
`

        // Get top 2 opportunities
        const topOpps = oppEntries.slice(0, 2)

        const outreachTaskData: ClickUpTaskData = {
          name: `${courseData.course_name} - ${opportunities.primary_pitch || 'Outreach'}`,
          description: description,
          // Don't set status - let ClickUp use list default
          priority: topOpps[0]?.[1] >= 8 ? 2 : 3,
          custom_fields: [
            // Related Course
            { id: '62ec1220-a35b-4023-8bdd-8af74ad3bb1d', value: results.course_task?.taskId ? [results.course_task.taskId] : [] },
            // Related Contacts
            { id: 'caa160a9-487d-406d-aacd-ea2dcb421ef0', value: contactTaskIds },
            // Target Segment - use option index (note: different options than Golf Courses)
            { id: 'c52d0d6d-5f3e-4c5e-aa1f-256c27a1a212', value: TARGET_SEGMENT_OPTION_INDEX[courseData.segment?.toLowerCase() || 'unknown'] || null },
            // Top Opportunity #1
            { id: '31bb96ce-439c-47b2-8bd6-8cdffd523fc7', value: topOpps[0]?.[0] || null },
            // Top Opportunity #1 Score
            { id: '1c6f30b2-930d-45d0-a14f-e28cc5c738b1', value: topOpps[0]?.[1] || null },
            // Top Opportunity #2
            { id: '2bfb13d6-be8b-4f80-84d8-4e07a44153b4', value: topOpps[1]?.[0] || null },
            // Top Opportunity #2 Score
            { id: '9c1a8615-5953-4826-9492-a77f74e9aa37', value: topOpps[1]?.[1] || null },
            // State - use option index
            { id: '81bc2505-28a7-4290-a557-50e49e410732', value: STATE_OPTION_INDEX[payload.state_code] }
          ],
          tags: ['agent-enriched', payload.state_code.toLowerCase()]
        }

        const outreachResult = await upsertClickUpTask(
          outreachTaskData,
          outreachDb?.clickup_task_id || null,
          '901413111587', // Outreach Activities list
          clickupApiKey
        )

        // Update/insert outreach_activities table
        const outreachRecord = {
          golf_course_id: payload.course_id,
          clickup_task_id: outreachResult.taskId,
          clickup_synced_at: new Date().toISOString(),
          clickup_sync_status: 'synced',
          clickup_sync_error: null,
          outreach_type: topOpps[0]?.[0] || 'general',
          status: 'scheduled',
          region: courseData.region,
          state_code: payload.state_code
        }

        if (outreachDb?.activity_id) {
          await supabase
            .from('outreach_activities')
            .update(outreachRecord)
            .eq('activity_id', outreachDb.activity_id)
        } else {
          await supabase
            .from('outreach_activities')
            .insert(outreachRecord)
        }

        results.outreach_task = outreachResult
        console.log(`✅ Outreach task ${outreachResult.action}: ${outreachResult.taskId}`)
      }

    } catch (error) {
      const errorMsg = `Outreach Activity task failed: ${error.message}`
      console.error(`❌ ${errorMsg}`)
      results.errors.push(errorMsg)
    }

    // ========================================================================
    // SUMMARY
    // ========================================================================

    const success = results.course_task && results.contact_tasks.length > 0 && results.outreach_task

    console.log(`\n${'='.repeat(70)}`)
    console.log(`${success ? '✅' : '⚠️'} ClickUp Sync Complete`)
    console.log(`${'='.repeat(70)}`)
    console.log(`Course Task: ${results.course_task ? results.course_task.action : 'FAILED'}`)
    console.log(`Contact Tasks: ${results.contact_tasks.length}/${contactsData.length} ${results.contact_tasks[0]?.action || 'N/A'}`)
    console.log(`Outreach Task: ${results.outreach_task ? results.outreach_task.action : 'FAILED'}`)
    if (results.errors.length > 0) {
      console.log(`Errors: ${results.errors.length}`)
      results.errors.forEach(err => console.log(`  - ${err}`))
    }
    console.log(`${'='.repeat(70)}`)

    return new Response(
      JSON.stringify({
        success: success,
        course_id: payload.course_id,
        results: results
      }),
      {
        status: success ? 200 : 207,
        headers: { 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('❌ ClickUp sync catastrophic error:', error)
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
