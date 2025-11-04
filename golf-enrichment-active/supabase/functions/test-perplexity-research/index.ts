// Test Perplexity Sonar Pro API for Golf Course Research
// Phase 2.5.1: LLM API Testing - PRIMARY TEST ($75 for 15k courses)
//
// CRITICAL: This function MUST set return_citations: true
// Citation quality is the make-or-break criterion for Perplexity approval

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Simple 5-Section Research Prompt
const SIMPLE_PROMPT = `Research {COURSE_NAME} in {CITY}, {STATE} and provide:

## 1. COURSE CLASSIFICATION
Classify as: Premium, Mid, or Budget
- Premium: $75+ green fees OR high-end private
- Mid: $40-75 green fees OR quality public/semi-private
- Budget: <$40 green fees OR municipal

Provide pricing evidence, course type, and confidence level.

## 2. WATER HAZARDS
Are there lots of water hazards in play?
Include: count, high-traffic holes, ball accumulation estimate, retrieval difficulty.

## 3. VOLUME ESTIMATE
Estimated annual rounds per year?
Base estimate on: tee times availability, course type, location, facility size.

## 4. DECISION MAKERS (CRITICAL)
Find contacts for:
- General Manager/Owner
- Golf Course Superintendent
- Director of Golf/Head Pro

For each contact provide: name, title, work email, LinkedIn URL, phone, and SOURCE URLs.

## 5. COURSE INTELLIGENCE
- Ownership structure
- Recent changes (last 2 years)
- Tech/equipment vendors
- Unique selling points

Return as JSON with inline citations for ALL facts.

**JSON Structure:**
\`\`\`json
{
  "course_name": "{COURSE_NAME}",
  "city": "{CITY}",
  "state": "{STATE}",
  "section1_classification": {
    "tier": "premium | mid | budget",
    "confidence": "high | medium | low",
    "green_fees": "$XX-YY",
    "course_type": "private | semi-private | public | municipal",
    "source": "https://..."
  },
  "section2_water_hazards": {
    "count": 0,
    "details": "Description",
    "accumulation": "high | medium | low",
    "source": "https://..."
  },
  "section3_volume": {
    "annual_rounds": 0,
    "basis": "Explanation",
    "source": "https://..."
  },
  "section4_contacts": [
    {
      "name": "Full Name",
      "title": "Exact Title",
      "email": "email@domain.com",
      "phone": "+1-XXX-XXX-XXXX",
      "linkedin": "https://linkedin.com/in/...",
      "source": "https://..."
    }
  ],
  "section5_intelligence": {
    "ownership": "Details",
    "recent_changes": "Details",
    "vendors": ["Vendor names"],
    "unique_points": "Details",
    "source": "https://..."
  }
}
\`\`\`

Begin research now.`

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Parse request
    const { course_name, state_code, city } = await req.json()

    if (!course_name || !state_code) {
      throw new Error('Missing required fields: course_name and state_code')
    }

    const startTime = Date.now()

    // Prepare prompt with course details
    const prompt = SIMPLE_PROMPT
      .replace(/{COURSE_NAME}/g, course_name)
      .replace(/{CITY}/g, city || state_code)
      .replace(/{STATE}/g, state_code)

    console.log(`🔍 Testing Perplexity API for: ${course_name}, ${state_code}`)

    // Call Perplexity Sonar Pro API
    const apiKey = Deno.env.get('PERPLEXITY_API_KEY')
    if (!apiKey) {
      throw new Error('PERPLEXITY_API_KEY not configured')
    }

    const perplexityResponse = await fetch('https://api.perplexity.ai/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'sonar-pro',
        messages: [
          {
            role: 'system',
            content: prompt
          },
          {
            role: 'user',
            content: `Research: ${course_name}, ${state_code}`
          }
        ],
        temperature: 0.2,
        max_tokens: 4000,
        return_citations: true,  // CRITICAL: Must return citations
        return_related_questions: false,
        search_recency_filter: 'month'  // Focus on recent data
      })
    })

    if (!perplexityResponse.ok) {
      const errorText = await perplexityResponse.text()
      throw new Error(`Perplexity API error: ${perplexityResponse.status} - ${errorText}`)
    }

    const result = await perplexityResponse.json()
    const responseTime = Date.now() - startTime

    // Extract response content and citations
    const content = result.choices?.[0]?.message?.content || ''
    const citations = result.citations || []

    // Parse JSON from content (may be wrapped in ```json blocks)
    let parsedJson = null
    try {
      const jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/) || content.match(/(\{[\s\S]*\})/)
      if (jsonMatch) {
        parsedJson = JSON.parse(jsonMatch[1])
      }
    } catch (parseError) {
      console.error('Failed to parse JSON from response:', parseError)
    }

    // Calculate estimated cost (Perplexity flat rate ~$0.005 per request)
    const estimatedCost = 0.005

    // Build response with all test data
    const testResult = {
      success: true,
      metadata: {
        course_name,
        state_code,
        city,
        api_provider: 'perplexity',
        model: 'sonar-pro',
        response_time_ms: responseTime,
        timestamp: new Date().toISOString()
      },

      // Critical quality metrics
      quality_metrics: {
        citations_provided: citations.length > 0,
        citation_count: citations.length,
        citations_have_urls: citations.every((c: any) =>
          typeof c === 'string' ? c.startsWith('http') : c.url?.startsWith('http')
        ),
        json_parsed_successfully: parsedJson !== null,
        has_tier_classification: parsedJson?.section5_course_tier?.classification !== undefined,
        contact_count: parsedJson?.section4_decision_makers?.length || 0
      },

      // Cost data
      cost_metrics: {
        estimated_cost_usd: estimatedCost,
        token_usage: result.usage || null
      },

      // Full data for analysis
      raw_response: {
        content,
        citations,
        usage: result.usage,
        full_api_response: result
      },

      parsed_json: parsedJson,

      // Validation flags
      validation: {
        ready_for_staging: parsedJson !== null && citations.length > 0,
        issues: []
      }
    }

    // Add validation issues
    if (!testResult.quality_metrics.citations_provided) {
      testResult.validation.issues.push('NO_CITATIONS: Perplexity did not return citations')
    }
    if (!testResult.quality_metrics.json_parsed_successfully) {
      testResult.validation.issues.push('INVALID_JSON: Could not parse JSON from response')
    }
    if (testResult.quality_metrics.contact_count === 0) {
      testResult.validation.issues.push('NO_CONTACTS: No decision makers found')
    }

    console.log(`✅ Perplexity test complete for ${course_name}:`, {
      citations: testResult.quality_metrics.citation_count,
      contacts: testResult.quality_metrics.contact_count,
      cost: estimatedCost,
      time: responseTime + 'ms'
    })

    return new Response(JSON.stringify(testResult, null, 2), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })

  } catch (error) {
    console.error('❌ Error in Perplexity test:', error)

    return new Response(JSON.stringify({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
