import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface AgentResults {
  course_id: number
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
        segment_signals: payload.agent_results?.agent6?.segmentation?.signals,
        opportunities: payload.agent_results?.agent6?.opportunities,
        range_intel: payload.agent_results?.agent6?.range_intel,

        // Agent 7 results
        water_hazards: payload.agent_results?.agent7?.water_hazard_count,
        water_hazard_confidence: payload.agent_results?.agent7?.confidence,

        // Cost tracking
        agent_cost_usd: payload.summary?.total_cost_usd
      })
      .eq('id', payload.course_id)

    if (courseError) {
      throw new Error(`Failed to update course: ${courseError.message}`)
    }

    console.log(`✅ Course updated: ${payload.course_name}`)

    // 2. Insert contacts (triggers ClickUp task creation!)
    if (payload.contacts && payload.contacts.length > 0) {
      const contactsToInsert = payload.contacts.map(contact => ({
        golf_course_id: payload.course_id,
        contact_name: contact.name,
        contact_title: contact.title,
        contact_email: contact.email,
        email_confidence: contact.email ? 95 : null,
        linkedin_url: contact.linkedin,
        contact_phone: contact.phone,
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
