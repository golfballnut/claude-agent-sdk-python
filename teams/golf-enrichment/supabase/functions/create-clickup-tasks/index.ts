import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface Contact {
  contact_id: string
  golf_course_id: number
  contact_name: string
  contact_title: string
  contact_email?: string
  contact_phone?: string
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
  segment_confidence?: number
  range_intel?: any
}

Deno.serve(async (req) => {
  try {
    const contact: Contact = await req.json()

    console.log(`📋 Creating ClickUp task for: ${contact.contact_name}`)

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

    // Determine segment for task routing
    const segment = contact.segment || course?.segment || 'both'

    // SINGLE LIST ARCHITECTURE - Use one list for all segments, filter by Target Segment field
    const listId = '901413111587' // Outreach Activities list

    // Format conversation starters
    const startersText = contact.conversation_starters
      ?.map((s: any, i: number) => `${i+1}. [${s.relevance}/10] ${s.text}`)
      .join('\n') || 'No conversation starters available'

    // Format opportunities
    const opportunitiesText = contact.opportunities
      ? Object.entries(contact.opportunities)
          .sort(([,a]: any, [,b]: any) => (b as number) - (a as number))
          .map(([key, score]) => `- ${key}: ${score}/10`)
          .join('\n')
      : 'No opportunities scored'

    // Get top 2 opportunities
    const topOpportunities = contact.opportunities
      ? Object.entries(contact.opportunities)
          .sort(([,a]: any, [,b]: any) => (b as number) - (a as number))
          .slice(0, 2)
      : []

    // Create ClickUp task
    const clickupResponse = await fetch(`https://api.clickup.com/api/v2/list/${listId}/task`, {
      method: 'POST',
      headers: {
        'Authorization': Deno.env.get('CLICKUP_API_KEY')!,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: `${contact.contact_name} - ${contact.contact_title} | ${course?.course_name}`,
        description: `## Contact Info
- **Email:** ${contact.contact_email || 'Not found'}
- **Phone:** ${contact.contact_phone || 'Not found'}
- **LinkedIn:** ${contact.linkedin_url || 'Not found'}
- **Company:** ${course?.course_name}
- **Website:** ${course?.website || 'N/A'}

## Business Intelligence
- **Segment:** ${segment.toUpperCase()} (${course?.segment_confidence || 'N/A'}/10 confidence)

## Top Opportunities
${opportunitiesText}

## Pre-Written Conversation Starters
${startersText}

## Range Intel
${course?.range_intel ? JSON.stringify(course.range_intel, null, 2) : 'N/A'}
`,
        status: 'to do',
        priority: topOpportunities[0]?.[1] >= 8 ? 2 : 3,
        custom_fields: [
          { id: 'c52d0d6d-5f3e-4c5e-aa1f-256c27a1a212', value: segment }, // Target Segment
          { id: '31bb96ce-439c-47b2-8bd6-8cdffd523fc7', value: topOpportunities[0]?.[0] }, // Top Opp #1
          { id: '1c6f30b2-930d-45d0-a14f-e28cc5c738b1', value: topOpportunities[0]?.[1] }, // Top Opp #1 Score
          { id: '2bfb13d6-be8b-4f80-84d8-4e07a44153b4', value: topOpportunities[1]?.[0] }, // Top Opp #2
          { id: '9c1a8615-5953-4826-9492-a77f74e9aa37', value: topOpportunities[1]?.[1] }  // Top Opp #2 Score
        ]
      })
    })

    if (!clickupResponse.ok) {
      const errorText = await clickupResponse.text()
      console.error(`⚠️ ClickUp API error: ${errorText}`)
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
      .eq('contact_id', contact.contact_id)

    return new Response(
      JSON.stringify({
        success: true,
        contact_id: contact.contact_id,
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
