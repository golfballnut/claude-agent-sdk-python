import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface Course {
  id: number
  course_name: string
  state_code: string
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

    // Extract domain from website for Apollo search
    const domain = course.website
      ? course.website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
      : ''

    console.log(`📋 Domain for Apollo: ${domain || 'Not provided'}`)

    // Call Render API (Agent Workflow with Apollo)
    const renderUrl = Deno.env.get('GOLF_ENRICHMENT_API_URL') ||
                      'https://agent7-water-hazards.onrender.com'

    const response = await fetch(`${renderUrl}/enrich-course`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        course_name: course.course_name,
        state_code: course.state_code,
        course_id: course.id,
        domain: domain, // NEW: For Apollo contact search
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
