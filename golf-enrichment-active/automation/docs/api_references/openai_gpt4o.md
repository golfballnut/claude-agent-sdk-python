# OpenAI GPT-4o API Reference

**Model:** gpt-4o
**Use Case:** Web research with same model as ChatGPT-5 Pro (FALLBACK #2)
**Cost:** ~$0.045 per course = **$675 for 15,000 courses**

---

## API Endpoint

```
POST https://api.openai.com/v1/chat/completions
```

**Headers:**
```json
{
  "Authorization": "Bearer <OPENAI_API_KEY>",
  "Content-Type": "application/json"
}
```

---

## Request Format

```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "<YOUR V2 RESEARCH PROMPT>"
    },
    {
      "role": "user",
      "content": "Research: <COURSE_NAME>, <STATE_CODE>"
    }
  ],
  "temperature": 0.2,
  "max_tokens": 4000,
  "response_format": { "type": "json_object" }
}
```

---

## Critical Parameters

### `model`
**Value:** `"gpt-4o"`

**Why GPT-4o:**
- **Same model as ChatGPT-5 Pro** (your manual baseline)
- Should produce identical quality
- Proven citation quality from manual testing

### `response_format` (OPTIONAL but RECOMMENDED)
**Type:** object
**Value:** `{ "type": "json_object" }`

**Purpose:** Forces GPT-4o to return valid JSON
**Benefit:** Reduces parsing errors, ensures structured output

**Usage:**
```json
{
  "model": "gpt-4o",
  "response_format": { "type": "json_object" },
  "messages": [
    {
      "role": "system",
      "content": "You are a golf course researcher. Return results as JSON with 5 sections..."
    }
  ]
}
```

**Important:** When using `json_object`, system prompt MUST mention "JSON" or "json"

### `temperature`
**Type:** number (0.0 - 2.0)
**Recommended:** **0.2**

**Purpose:** Consistent, factual responses

### `max_tokens`
**Type:** integer
**Recommended:** **4000**

**Purpose:** V2 JSON typically 2k-3k tokens

---

## Response Format

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1730505600,
  "model": "gpt-4o-2024-11-20",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\n  \"section1\": {...},\n  \"section2\": {...},\n  ...}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1250,
    "completion_tokens": 850,
    "total_tokens": 2100
  }
}
```

**Parse JSON:**
```typescript
const result = await response.json()
const v2_json = JSON.parse(result.choices[0].message.content)

// Calculate cost
const input_cost = result.usage.prompt_tokens * 2.50 / 1_000_000
const output_cost = result.usage.completion_tokens * 10.00 / 1_000_000
const total_cost = input_cost + output_cost
```

---

## Pricing

**Input tokens:** $2.50 per 1M tokens
**Output tokens:** $10.00 per 1M tokens

**Estimated per course:**
- Input: V2 prompt (~1k) + course context (~9k) = 10k tokens × $2.50/1M = $0.025
- Output: V2 JSON response (~2k tokens) × $10/1M = $0.020
- **Total per course:** ~$0.045

**Budget for 15,000 courses:**
- 15,000 × $0.045 = **$675 total**

**vs Perplexity:** 9x more expensive ($675 vs $75)
**vs Claude:** 25% cheaper ($675 vs $900)

---

## Rate Limits

**Tier-based limits:**
- **Tier 1 (Free):** 500 RPM, 200k TPM
- **Tier 2 ($50+ spend):** 5k RPM, 2M TPM
- **Tier 3 ($1k+ spend):** 10k RPM, 4M TPM

**For our use case:**
- Processing 12 courses/hour = 12 requests/hour
- Well within Tier 1 limits
- No risk of rate limiting

---

## Citation Handling

### Challenge
OpenAI doesn't have Perplexity's `return_citations` parameter.

### Solution
**Prompt engineering:** Explicitly request citation URLs in JSON schema.

**Enhanced system prompt:**
```
You are a golf course researcher. Research the provided golf course and return your findings as JSON.

CRITICAL: Include source URLs for ALL data points.

Required JSON structure:
{
  "section1": {
    "tier": "Premium|Mid|Budget",
    "tier_confidence": 0.0-1.0,
    "tier_reasoning": "Based on pricing evidence...",
    "tier_citations": [
      "https://example.com/rates",  // REQUIRED: Direct URLs
      "https://example.com/membership"
    ]
  },
  "section2": {
    "has_water_hazards": true/false,
    "hazards_citations": ["url1", "url2"]  // REQUIRED
  },
  ...
}

Every section MUST have a "*_citations" array with verifiable URLs.
Do NOT use generic sources like "course website" - provide actual URLs.
```

### Validation
```typescript
function validateCitations(v2_json: any): boolean {
  const required_citation_fields = [
    'section1.tier_citations',
    'section2.hazards_citations',
    'section3.volume_citations',
    'section5.intelligence_citations'
  ]

  for (const field of required_citation_fields) {
    const citations = field.split('.').reduce((obj, key) => obj?.[key], v2_json)
    if (!citations || !Array.isArray(citations) || citations.length === 0) {
      return false
    }

    // Verify URLs are valid
    for (const url of citations) {
      try {
        new URL(url)
      } catch {
        return false
      }
    }
  }

  return true
}
```

---

## Advantages Over Perplexity/Claude

1. **Same model as manual baseline:** GPT-4o = ChatGPT-5 Pro
2. **Proven quality:** Your manual tests used this model
3. **JSON mode:** `response_format: json_object` ensures valid JSON
4. **Moderate cost:** Cheaper than Claude, reasonable vs Perplexity

## Disadvantages

1. **9x more expensive than Perplexity:** $675 vs $75
2. **No built-in citations:** Requires prompt engineering
3. **No web search built-in:** Unlike Perplexity

---

## When to Use OpenAI

**Use OpenAI API if:**
- ✅ Both Perplexity and Claude fail quality checks
- ✅ Need guaranteed quality (same model as manual)
- ✅ Budget allows $675 for proven results
- ✅ Citations can be enforced via prompt engineering

**Skip OpenAI if:**
- ❌ Perplexity passes all checks (save $600)
- ❌ Claude passes all checks (save $225 but less reasoning)

---

## Example Edge Function Code

```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

serve(async (req) => {
  const { course_name, state_code, website } = await req.json()

  try {
    const system_prompt = await Deno.readTextFile('../../../prompts/v2_research_prompt.md')

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content: system_prompt + `\n\nIMPORTANT: Return ONLY valid JSON. Include "*_citations" arrays with URLs in every section.`
          },
          {
            role: 'user',
            content: `Research golf course: ${course_name} in ${state_code}.\n\nCourse website: ${website || 'Not provided'}\n\nReturn complete V2 JSON with all 5 sections.`
          }
        ],
        temperature: 0.2,
        max_tokens: 4000,
        response_format: { type: 'json_object' }  // Force JSON
      })
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    const result = await response.json()
    const v2_json = JSON.parse(result.choices[0].message.content)

    // Calculate cost
    const input_cost = result.usage.prompt_tokens * 2.50 / 1_000_000
    const output_cost = result.usage.completion_tokens * 10.00 / 1_000_000

    return new Response(JSON.stringify({
      success: true,
      v2_json: v2_json,
      tokens_used: result.usage.total_tokens,
      cost_usd: input_cost + output_cost
    }), {
      headers: { 'Content-Type': 'application/json' }
    })

  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
})
```

---

## Testing Checklist

**Before approving OpenAI for full automation:**

- [ ] All 3 test courses return valid JSON
- [ ] Each section has `*_citations` array with URLs
- [ ] Citations are clickable and verifiable
- [ ] Tier classification matches manual baseline (3/3)
- [ ] Contact count averages ≥3 per course
- [ ] Email OR LinkedIn for GM/Superintendent
- [ ] Cost per course ≤$0.06
- [ ] Quality score ≥90/100 (vs manual)

**If ALL checked → OpenAI APPROVED for Phase 2.6**

---

## Expected Quality

**Prediction:** Should be **identical to manual ChatGPT-5 Pro results**

**Why:**
- Same GPT-4o model
- Same capabilities (web browsing, reasoning)
- Only difference: API vs ChatGPT interface

**If OpenAI fails quality checks:**
- Problem is NOT the model (proven in manual testing)
- Problem is likely: prompt formatting, JSON schema instructions
- **Action:** Debug prompt, adjust parameters, re-test

---

## Resources

**Official Docs:** https://platform.openai.com/docs/api-reference/chat
**Pricing:** https://openai.com/api/pricing/
**Models:** https://platform.openai.com/docs/models/gpt-4o

---

**Status:** Ready for Phase 2.5.4 (ONLY if Perplexity AND Claude fail)
