# Perplexity Sonar Pro API Reference

**Model:** sonar-pro
**Use Case:** Web research with citations (PRIMARY option for Phase 2.5)
**Cost:** ~$0.005 per request = **$75 for 15,000 courses**

---

## API Endpoint

```
POST https://api.perplexity.ai/chat/completions
```

**Headers:**
```json
{
  "Authorization": "Bearer <PERPLEXITY_API_KEY>",
  "Content-Type": "application/json"
}
```

---

## Request Format

```json
{
  "model": "sonar-pro",
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
  "return_citations": true,
  "return_related_questions": false,
  "search_recency_filter": "month",
  "search_domain_filter": []
}
```

---

## Critical Parameters

### `return_citations` (REQUIRED)
**Type:** boolean
**Default:** false
**Value:** **true** ← **MUST SET THIS**

**Purpose:** Returns citations array with source URLs

**Without this:** Perplexity returns text but no source attribution
**With this:** Response includes `citations` array with URLs

**Example Response:**
```json
{
  "id": "...",
  "model": "sonar-pro",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "<V2 JSON RESPONSE>"
      },
      "finish_reason": "stop"
    }
  ],
  "citations": [
    "https://thetraditiongolfclub.com/",
    "https://golf.bman.com/golf-course/the-tradition-golf-club/",
    "https://www.linkedin.com/in/chris-eichstaedt-38a265139"
  ],
  "usage": {
    "prompt_tokens": 1250,
    "completion_tokens": 850,
    "total_tokens": 2100
  }
}
```

### `search_recency_filter` (OPTIONAL)
**Type:** string
**Options:** `month`, `week`, `day`, `hour`
**Recommended:** `month`

**Purpose:** Prioritizes recent search results (helpful for pricing, contacts)

### `temperature` (RECOMMENDED)
**Type:** number (0.0 - 2.0)
**Recommended:** **0.2**

**Purpose:** Lower temperature = more factual, less creative
**Why:** We want consistent, accurate data extraction

### `max_tokens` (REQUIRED)
**Type:** integer
**Recommended:** **4000**

**Purpose:** V2 JSON responses typically 2k-3k tokens
**Why:** Allows full response without truncation

---

## Response Format

```json
{
  "id": "req_abc123",
  "model": "sonar-pro",
  "created": 1730505600,
  "choices": [
    {
      "index": 0,
      "finish_reason": "stop",
      "message": {
        "role": "assistant",
        "content": "{\n  \"section1\": {...},\n  \"section2\": {...},\n  ...}"
      },
      "delta": null
    }
  ],
  "citations": [
    "https://example.com/source1",
    "https://example.com/source2"
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
const citations = result.citations  // Array of URLs
const cost = result.usage.total_tokens * 0.001 / 1000  // Estimate
```

---

## Pricing

**Model:** sonar-pro (with web search included)

**Cost Structure:**
- **Per request:** ~$0.005 (flat rate, includes search)
- **No token-based pricing** (unlike Claude/OpenAI)

**Budget for 15,000 courses:**
- 15,000 requests × $0.005 = **$75 total**

**Rate Limits:**
- **Free tier:** 50 requests/day
- **Pro tier:** 1,000 requests/day ($20/month)

**Recommendation for 15k courses:**
- Upgrade to Pro tier immediately
- Process 1,000 courses/day = 15 days total
- Monthly cost: $20 + $75 requests = **$95 total**

---

## Rate Limit Handling

### Free Tier (50 req/day)
```typescript
const BATCH_SIZE = 10
const DELAY_BETWEEN_REQUESTS = 1800000  // 30 minutes (48 per day)

// Process 10 courses every 5 hours
// 15,000 courses ÷ 48/day = 312 days (unacceptable)
```

### Pro Tier (1,000 req/day)
```typescript
const BATCH_SIZE = 10
const DELAY_BETWEEN_REQUESTS = 90000  // 1.5 minutes (960 per day)

// Process 10 courses every 1.5 minutes
// 15,000 courses ÷ 960/day = 16 days (ACCEPTABLE)
```

**Recommendation:** Use Pro tier ($20/month for faster processing)

---

## Citation Quality Assessment

### What to Check

**CRITICAL:** Citations array must contain:
- ✅ **Actual URLs** (not generic "source: website")
- ✅ **Verifiable sources** (click link, content exists)
- ✅ **Relevant to claims** (matches data in JSON)

**Example GOOD citations:**
```json
{
  "citations": [
    "https://thetraditiongolfclub.com/course-rates/",
    "https://www.linkedin.com/in/chris-eichstaedt-38a265139",
    "https://golf.bman.com/golf-course/the-tradition-golf-club/"
  ]
}
```

**Example BAD citations:**
```json
{
  "citations": [
    "Various golf websites",
    "LinkedIn",
    "General course information"
  ]
}
```

**Validation Script:**
```typescript
function validateCitations(citations: string[]): boolean {
  // Must have at least 3 citations
  if (citations.length < 3) return false

  // Each citation must be a valid URL
  for (const citation of citations) {
    try {
      new URL(citation)  // Throws if invalid
    } catch {
      return false  // Not a valid URL
    }
  }

  return true
}
```

---

## Error Handling

### Common Errors

**Rate Limit Exceeded:**
```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error"
  }
}
```

**Solution:** Add delay, reduce batch size, upgrade to Pro tier

**Invalid API Key:**
```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error"
  }
}
```

**Solution:** Check `PERPLEXITY_API_KEY` secret in Supabase

**Timeout:**
```json
{
  "error": {
    "message": "Request timeout",
    "type": "timeout_error"
  }
}
```

**Solution:** Increase fetch timeout to 60 seconds

---

## Example Edge Function Code

```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

serve(async (req) => {
  const { course_name, state_code } = await req.json()

  try {
    const response = await fetch('https://api.perplexity.ai/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('PERPLEXITY_API_KEY')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'sonar-pro',
        messages: [
          {
            role: 'system',
            content: await Deno.readTextFile('../../../prompts/v2_research_prompt.md')
          },
          {
            role: 'user',
            content: `Research golf course: ${course_name} in ${state_code}. Return ONLY valid JSON with all 5 sections.`
          }
        ],
        temperature: 0.2,
        max_tokens: 4000,
        return_citations: true,  // CRITICAL
        return_related_questions: false
      })
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    const result = await response.json()
    const v2_json = JSON.parse(result.choices[0].message.content)

    return new Response(JSON.stringify({
      success: true,
      v2_json: v2_json,
      citations: result.citations,
      tokens_used: result.usage.total_tokens,
      cost_usd: 0.005  // Flat rate per request
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

**Before approving Perplexity for full automation:**

- [ ] All 3 test courses return valid JSON
- [ ] Citations array contains ≥3 URLs per course
- [ ] URLs are clickable and lead to real sources
- [ ] Tier classification matches manual results (3/3 correct)
- [ ] Contact count averages ≥3 per course
- [ ] Email OR LinkedIn present for GM or Superintendent
- [ ] Cost per course ≤$0.01
- [ ] Response time ≤30 seconds

**If ALL checked → Perplexity APPROVED for Phase 2.6**

---

## Resources

**Official Docs:** https://docs.perplexity.ai/reference/post_chat_completions
**Pricing:** https://docs.perplexity.ai/docs/pricing
**Playground:** https://playground.perplexity.ai/

---

**Status:** Ready for Phase 2.5.1 implementation
