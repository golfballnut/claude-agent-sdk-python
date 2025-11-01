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

// V2 Research Prompt Template
const V2_PROMPT = `# Golf Course Research Prompt - Enhanced v1

You are researching **{COURSE_NAME}** in **{CITY}, {STATE}** to gather comprehensive intelligence for a range ball and golf supply business.

**CRITICAL INSTRUCTIONS:**
1. Provide SOURCE URL for EVERY factual claim
2. Focus on CURRENT information (2024-2025 only)
3. Return response as valid JSON matching the schema below
4. Use \`null\` or \`"not_found"\` when data is unavailable
5. Be thorough - this is comprehensive research, not a quick lookup

---

## SECTION 1: RANGE BALL OPPORTUNITY CLASSIFICATION ⚠️ CRITICAL

**Objective:** Determine if this course represents a BUY, SELL, or BOTH opportunity for range ball services.

### BUY OPPORTUNITY (We purchase their waste balls)
Look for signals that the course has waste/used range balls they need to dispose of:
- "Throwing away old balls" / "discarding worn practice balls"
- "Storage full" / "too many old balls"
- "Recycling program" / "selling used balls"
- Large practice range (50+ stations) at a busy course
- Premium/resort course (high ball turnover)

**If found, gather:**
- Specific quotes mentioning ball disposal
- Estimated range size (# of stations)
- Course tier (affects ball volume/quality)
- Any mentions of current ball recycling/sales

### SELL OPPORTUNITY (They need to purchase from a supplier)
Look for pain points indicating they need a better range ball supplier:
- "Practice ball costs too high" / "budget concerns"
- "Range balls poor quality" / "worn out"
- "Member complaints about practice balls"
- "Looking for ball supplier"
- "Current supplier unreliable"

**If found, gather:**
- Specific pain points (cost vs quality vs reliability)
- Current supplier name (if mentioned)
- Budget/procurement timing mentions
- Quotes from reviews, newsletters, or announcements

### CLASSIFICATION RULES
- **BOTH**: Shows BOTH waste disposal needs AND purchasing pain points (HIGHEST VALUE)
- **BUY**: Only disposal/excess ball signals found
- **SELL**: Only purchasing pain/need signals found
- **INSUFFICIENT_DATA**: Cannot determine from available information

**Output for this section:**
\`\`\`json
{
  "classification": "BOTH | BUY | SELL | INSUFFICIENT_DATA",
  "confidence": "high | medium | low",
  "buy_signals": [
    {
      "signal": "Quote or fact",
      "source": "https://..."
    }
  ],
  "sell_signals": [
    {
      "signal": "Quote or fact",
      "source": "https://..."
    }
  ],
  "recommended_strategy": "buy_first | sell_first | approach_both | insufficient_data",
  "reasoning": "1-2 sentences explaining the classification"
}
\`\`\`

---

## SECTION 2: WATER HAZARDS (EXPANSION OPPORTUNITY)

**Objective:** Assess potential for ball retrieval services (secondary offering).

Look for:
- Total count of ponds, lakes, water hazards on the course
- Mentions of specific hazards (e.g., "island green on hole 7")
- High-traffic holes with water (signature holes, par 3s over water)
- Ball retrieval service mentions (current provider or need)

**Output for this section:**
\`\`\`json
{
  "water_hazards": {
    "total_count": 0,
    "details": [
      {
        "location": "Hole 7, island green",
        "type": "pond | lake | stream",
        "notes": "High-traffic par 3",
        "source": "https://..."
      }
    ],
    "ball_accumulation_estimate": "high | medium | low | unknown",
    "current_retrieval_service": "Company name or null",
    "source": "https://... (for retrieval service info)"
  }
}
\`\`\`

---

## SECTION 3: PRACTICE FACILITIES (CRITICAL FOR VOLUME ESTIMATES)

**Objective:** Understand the size and quality of practice facilities.

Look for:
- Number of hitting stations / range size
- Range type: grass tees, mat tees, or both
- Practice area amenities
- Current practice ball supplier (if mentioned)

**Output for this section:**
\`\`\`json
{
  "practice_facilities": {
    "range": {
      "stations": 0,
      "type": "grass | mat | both | unknown",
      "size_description": "Brief description",
      "source": "https://..."
    },
    "current_supplier": {
      "name": "Supplier name or null",
      "source": "https://..."
    },
    "quality_mentions": [
      {
        "mention": "Quote about ball quality",
        "sentiment": "positive | negative | neutral",
        "source": "https://..."
      }
    ]
  }
}
\`\`\`

---

## SECTION 4: DECISION MAKERS (CRITICAL - REQUIRED FOR OUTREACH)

**Objective:** Find verified contact information for key decision makers.

**Priority order:**
1. General Manager / Owner (HIGHEST PRIORITY)
2. Golf Course Superintendent / Director of Agronomy
3. Director of Golf / Head Golf Professional

**For each contact, find:**
- Full name
- Exact current title
- **Work email** (search: club newsletters, staff pages, directories)
- Phone number (direct line preferred)
- LinkedIn profile URL
- Employment verification (must be CURRENT 2024-2025)

**Output for this section:**
\`\`\`json
{
  "decision_makers": [
    {
      "name": "John Smith",
      "title": "General Manager",
      "priority": 1,
      "email": "jsmith@example.com or null",
      "email_source": "https://...",
      "phone": "+1-555-123-4567 or null",
      "linkedin": "https://linkedin.com/in/... or null",
      "employment_verified": true,
      "verification_source": "https://..."
    }
  ]
}
\`\`\`

---

## SECTION 5: COURSE TIER CLASSIFICATION

**Objective:** Classify the course to estimate ball volume and quality needs.

Look for:
- **Pricing:** Daily green fees OR membership/initiation fees
- **Course type:** Private, semi-private, public, municipal, resort
- **Volume indicators:** Estimated annual rounds
- **Quality indicators:** Rankings, awards, tournament hosting

**Classification guidelines:**
- **Premium:** $75+ green fees, ranked courses, high-end private clubs
- **Medium:** $40-75 green fees, quality public or semi-private
- **Budget:** <$40 green fees, municipal courses

**Output for this section:**
\`\`\`json
{
  "course_tier": {
    "classification": "premium | medium | budget",
    "confidence": "high | medium | low",
    "pricing": {
      "green_fee_range": "$40-60 or null",
      "source": "https://..."
    },
    "course_type": "private | semi-private | public | municipal | resort",
    "quality_indicators": [
      {
        "indicator": "Ranked #47 in state",
        "source": "https://..."
      }
    ]
  }
}
\`\`\`

---

## FINAL JSON RESPONSE STRUCTURE

Combine all sections into a single JSON response:

\`\`\`json
{
  "course_name": "{COURSE_NAME}",
  "city": "{CITY}",
  "state": "{STATE}",
  "research_date": "2025-01-01",
  "section1_classification": { ... },
  "section2_water_hazards": { ... },
  "section3_practice_facilities": { ... },
  "section4_decision_makers": [ ... ],
  "section5_course_tier": { ... }
}
\`\`\`

**Now, begin comprehensive research on {COURSE_NAME} in {CITY}, {STATE}.**
`

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
    const prompt = V2_PROMPT
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
