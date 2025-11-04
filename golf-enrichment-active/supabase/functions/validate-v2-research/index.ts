/**
 * Edge Function: validate-v2-research
 *
 * Purpose: Orchestrates V2 JSON validation workflow
 * Trigger: Database trigger on llm_research_staging INSERT
 *
 * Workflow:
 * 1. Receive staging_id from database trigger
 * 2. Fetch v2_json from llm_research_staging table
 * 3. Call Render validator API to validate + write to database
 * 4. Update staging table status based on result
 * 5. ClickUp sync triggers automatically on contact insert
 *
 * Created: 2025-10-31
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // ========================================================================
    // STEP 1: Parse request payload from database trigger
    // ========================================================================
    const { staging_id, course_id, course_name, state_code } = await req.json()

    console.log(`🚀 Validation triggered for: ${course_name} (${state_code})`)
    console.log(`   Staging ID: ${staging_id}`)
    console.log(`   Course ID: ${course_id || 'NEW COURSE'}`)

    // ========================================================================
    // STEP 2: Initialize Supabase client
    // ========================================================================
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    })

    // ========================================================================
    // STEP 3: Fetch v2_json from staging table
    // ========================================================================
    const { data: stagingRecord, error: fetchError } = await supabase
      .from('llm_research_staging')
      .select('v2_json, status')
      .eq('id', staging_id)
      .single()

    if (fetchError) {
      console.error('❌ Failed to fetch staging record:', fetchError)
      return new Response(
        JSON.stringify({ error: 'Staging record not found', details: fetchError.message }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Verify status is pending (prevent duplicate processing)
    if (stagingRecord.status !== 'pending') {
      console.log(`⚠️  Skipping - status is ${stagingRecord.status}, not pending`)
      return new Response(
        JSON.stringify({ message: 'Already processed', status: stagingRecord.status }),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    console.log('✅ Fetched v2_json from staging table')

    // ========================================================================
    // STEP 4: Update status to processing
    // ========================================================================
    await supabase
      .from('llm_research_staging')
      .update({ status: 'processing' })
      .eq('id', staging_id)

    console.log('⏳ Status updated to processing')

    // ========================================================================
    // STEP 5: Call Render validator API
    // ========================================================================
    const renderValidatorUrl = Deno.env.get('RENDER_VALIDATOR_URL')
    if (!renderValidatorUrl) {
      throw new Error('RENDER_VALIDATOR_URL environment variable not set')
    }

    console.log(`📡 Calling Render validator: ${renderValidatorUrl}/validate-and-write`)

    const renderPayload = {
      staging_id,
      course_id,
      course_name,
      state_code,
      v2_json: stagingRecord.v2_json
    }

    const renderResponse = await fetch(`${renderValidatorUrl}/validate-and-write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(renderPayload)
    })

    const renderResult = await renderResponse.json()

    // ========================================================================
    // STEP 6: Handle validation result
    // ========================================================================
    if (!renderResponse.ok) {
      // Validation failed - update staging with error
      console.error('❌ Render validator failed:', renderResult.error || renderResult.detail)

      await supabase
        .from('llm_research_staging')
        .update({
          status: 'validation_failed',
          validation_error: renderResult.error || renderResult.detail || 'Unknown validation error',
          processed_at: new Date().toISOString()
        })
        .eq('id', staging_id)

      return new Response(
        JSON.stringify({
          success: false,
          error: renderResult.error || renderResult.detail || 'Validation failed',
          staging_id
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validation succeeded - update staging
    console.log('✅ Render validator succeeded')
    console.log(`   Course ID: ${renderResult.course_id}`)
    console.log(`   Contacts created: ${renderResult.contacts_created}`)
    console.log(`   Validation flags: ${JSON.stringify(renderResult.validation_flags || [])}`)

    await supabase
      .from('llm_research_staging')
      .update({
        status: 'validated',
        processed_at: new Date().toISOString()
      })
      .eq('id', staging_id)

    // ========================================================================
    // STEP 7: Return success response
    // ========================================================================
    // Note: ClickUp sync will trigger automatically via contact insert trigger
    return new Response(
      JSON.stringify({
        success: true,
        message: 'Validation complete. ClickUp tasks will be created automatically.',
        staging_id,
        course_id: renderResult.course_id,
        contacts_created: renderResult.contacts_created,
        validation_flags: renderResult.validation_flags || [],
        next_steps: [
          'Database records written to golf_courses and golf_course_contacts',
          'ClickUp sync triggered by contact insert (automatic)',
          'Contact enrichment (Apollo/Hunter) can be triggered manually in Phase 2.2'
        ]
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    // ========================================================================
    // ERROR HANDLING: Unexpected errors
    // ========================================================================
    console.error('❌ Unexpected error in validate-v2-research:', error)

    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        details: error.message,
        stack: error.stack
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
