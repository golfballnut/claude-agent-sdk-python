// Test OpenAI GPT-4o API for Golf Course Research
// Phase 2.5.1: LLM API Testing - FALLBACK #2 ($675 for 15k courses)
//
// CRITICAL: OpenAI uses response_format: { type: "json_object" } to force valid JSON
// This is the same model as manual ChatGPT-5 Pro baseline, should match perfectly

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

    console.log(`🔍 Testing OpenAI API for: ${course_name}, ${state_code}`)

    // Call OpenAI GPT-4o API
    const apiKey = Deno.env.get('OPENAI_API_KEY')
    if (!apiKey) {
      throw new Error('OPENAI_API_KEY not configured')
    }

    const openaiResponse = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4o',
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
        // CRITICAL: Force valid JSON response
        response_format: { type: "json_object" }
      })
    })

    if (!openaiResponse.ok) {
      const errorText = await openaiResponse.text()
      throw new Error(`OpenAI API error: ${openaiResponse.status} - ${errorText}`)
    }

    const result = await openaiResponse.json()
    const responseTime = Date.now() - startTime

    // Extract response content
    const content = result.choices?.[0]?.message?.content || ''

    // Parse JSON (should be valid due to response_format)
    let parsedJson = null
    try {
      parsedJson = JSON.parse(content)
    } catch (parseError) {
      console.error('Failed to parse JSON from response:', parseError)
    }

    // Count citations in parsed JSON (look for source fields)
    let citationCount = 0
    if (parsedJson) {
      const jsonStr = JSON.stringify(parsedJson)
      const sourceMatches = jsonStr.match(/"source":\s*"https?:\/\//g) || []
      citationCount = sourceMatches.length
    }

    // Calculate estimated cost
    const inputTokens = result.usage?.prompt_tokens || 0
    const outputTokens = result.usage?.completion_tokens || 0
    const inputCost = (inputTokens / 1000000) * 2.5  // $2.50 per 1M input tokens
    const outputCost = (outputTokens / 1000000) * 10.0  // $10 per 1M output tokens
    const estimatedCost = inputCost + outputCost

    // Build response with all test data
    const testResult = {
      success: true,
      metadata: {
        course_name,
        state_code,
        city,
        api_provider: 'openai',
        model: 'gpt-4o',
        response_time_ms: responseTime,
        timestamp: new Date().toISOString()
      },

      // Critical quality metrics
      quality_metrics: {
        citations_provided: citationCount > 0,
        citation_count: citationCount,
        citations_have_urls: citationCount > 0,
        json_parsed_successfully: parsedJson !== null,
        has_tier_classification: parsedJson?.section1_classification?.tier !== undefined,
        contact_count: parsedJson?.section4_contacts?.length || 0
      },

      // Cost data
      cost_metrics: {
        estimated_cost_usd: estimatedCost,
        input_tokens: inputTokens,
        output_tokens: outputTokens,
        cost_breakdown: {
          input_cost_usd: inputCost,
          output_cost_usd: outputCost
        }
      },

      // Full data for analysis
      raw_response: {
        content,
        usage: result.usage,
        full_api_response: result
      },

      parsed_json: parsedJson,

      // Validation flags
      validation: {
        ready_for_staging: parsedJson !== null && citationCount > 0,
        issues: []
      }
    }

    // Add validation issues
    if (!testResult.quality_metrics.citations_provided) {
      testResult.validation.issues.push('NO_CITATIONS: OpenAI did not provide citations')
    }
    if (!testResult.quality_metrics.json_parsed_successfully) {
      testResult.validation.issues.push('INVALID_JSON: Could not parse JSON from response')
    }
    if (testResult.quality_metrics.contact_count === 0) {
      testResult.validation.issues.push('NO_CONTACTS: No decision makers found')
    }

    console.log(`✅ OpenAI test complete for ${course_name}:`, {
      citations: testResult.quality_metrics.citation_count,
      contacts: testResult.quality_metrics.contact_count,
      cost: estimatedCost.toFixed(4),
      time: responseTime + 'ms'
    })

    return new Response(JSON.stringify(testResult, null, 2), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })

  } catch (error) {
    console.error('❌ Error in OpenAI test:', error)

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
