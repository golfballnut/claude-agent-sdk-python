import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface WebhookPayload {
  course_id: number
  success: boolean
  course_name: string
  state_code: string
}

Deno.serve(async (req) => {
  try {
    const payload: WebhookPayload = await req.json()

    console.log(`📥 Webhook received for: ${payload.course_name}`)
    console.log(`   Course ID: ${payload.course_id}`)
    console.log(`   Success: ${payload.success}`)

    // ========================================================================
    // NO DATABASE WRITES HERE!
    // Agent 8 (in orchestrator) already wrote everything to database
    // This webhook only triggers ClickUp sync
    // ========================================================================

    if (!payload.success) {
      console.log(`⚠️ Enrichment failed for course ${payload.course_id}, skipping ClickUp sync`)
      return new Response(
        JSON.stringify({
          success: true,
          message: 'Enrichment failed, ClickUp sync skipped'
        }),
        { headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Trigger ClickUp sync (reads fresh data from database)
    console.log(`\n📋 Triggering ClickUp sync...`)

    try {
      const clickupSyncResponse = await fetch(
        `${Deno.env.get('SUPABASE_URL')}/functions/v1/create-clickup-tasks`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            course_id: payload.course_id,
            course_name: payload.course_name,
            state_code: payload.state_code
          })
        }
      )

      if (!clickupSyncResponse.ok) {
        const errorText = await clickupSyncResponse.text()
        console.error(`⚠️ ClickUp sync failed (non-blocking): ${errorText}`)

        return new Response(
          JSON.stringify({
            success: true,
            message: 'Database updated by Agent 8, ClickUp sync failed',
            clickup_error: errorText
          }),
          {
            status: 207, // Multi-status: DB success, ClickUp failed
            headers: { 'Content-Type': 'application/json' }
          }
        )
      }

      const clickupResult = await clickupSyncResponse.json()
      console.log(`✅ ClickUp sync completed: ${clickupResult.success ? 'success' : 'partial'}`)

      return new Response(
        JSON.stringify({
          success: true,
          message: 'Database updated by Agent 8, ClickUp synced',
          clickup_result: clickupResult
        }),
        { headers: { 'Content-Type': 'application/json' } }
      )

    } catch (error) {
      console.error(`⚠️ ClickUp sync error (non-blocking): ${error.message}`)

      return new Response(
        JSON.stringify({
          success: true,
          message: 'Database updated by Agent 8, ClickUp sync error',
          error: error.message
        }),
        {
          status: 207,
          headers: { 'Content-Type': 'application/json' }
        }
      )
    }

  } catch (error) {
    console.error('❌ Webhook processing error:', error)
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
