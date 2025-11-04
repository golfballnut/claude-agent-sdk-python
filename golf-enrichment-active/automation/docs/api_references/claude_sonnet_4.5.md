# Claude Sonnet 4.5 API Reference

**Model:** claude-sonnet-4-5-20250929
**Use Case:** Web research with reasoning (FALLBACK #1 if Perplexity fails)
**Cost:** ~$0.06 per course = **$900 for 15,000 courses**

---

## API Endpoint

```
POST https://api.anthropic.com/v1/messages
```

**Headers:**
```json
{
  "x-api-key": "<ANTHROPIC_API_KEY>",
  "anthropic-version": "2023-06-01",
  "Content-Type": "application/json"
}
```

---

## Request Format

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 4000,
  "temperature": 0.2,
  "system": "<YOUR V2 RESEARCH PROMPT>",
  "messages": [
    {
      "role": "user",
      "content": "Research: <COURSE_NAME>, <STATE_CODE>"
    }
  ]
}
```

---

## Key Differences from OpenAI/Perplexity

### System Prompt
- **Separate parameter** (not in messages array)
- Use `system` field for V2 prompt
- `messages` array only has user query

### Response Format
- Different structure than OpenAI ChatCompletion
- Content in `content` array (not `message.content`)

### No Built-in Web Search
- Claude doesn't search web automatically
- Need to provide context in prompt OR use MCP tools
- **Workaround:** Include course website in user message if available

---

## Request Example

```typescript
const response = await fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  headers: {
    'x-api-key': Deno.env.get('ANTHROPIC_API_KEY'),
    'anthropic-version': '2023-06-01',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'claude-sonnet-4-5-20250929',
    max_tokens: 4000,
    temperature: 0.2,
    system: await Deno.readTextFile('../../../prompts/v2_research_prompt.md'),
    messages: [
      {
        role: 'user',
        content: `Research golf course: ${course_name} in ${state_code}.

Course website (if available): ${website || 'Not provided'}

Return ONLY valid JSON with all 5 sections (section1-section5).
Include citations with URLs for all claims.`
      }
    ]
  })
})
```

---

## Response Format

```json
{
  "id": "msg_abc123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "{\n  \"section1\": {...},\n  \"section2\": {...},\n  ...}"
    }
  ],
  "model": "claude-sonnet-4-5-20250929",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 1250,
    "output_tokens": 850
  }
}
```

**Parse JSON:**
```typescript
const result = await response.json()
const v2_json = JSON.parse(result.content[0].text)
const tokens = result.usage.input_tokens + result.usage.output_tokens

// Calculate cost
const input_cost = result.usage.input_tokens * 3 / 1_000_000
const output_cost = result.usage.output_tokens * 15 / 1_000_000
const total_cost = input_cost + output_cost
```

---

## Pricing

**Input tokens:** $3.00 per 1M tokens
**Output tokens:** $15.00 per 1M tokens

**Estimated per course:**
- Input: V2 prompt (~1k) + course context (~9k) = 10k tokens × $3/1M = $0.03
- Output: V2 JSON response (~2k tokens) × $15/1M = $0.03
- **Total per course:** ~$0.06

**Budget for 15,000 courses:**
- 15,000 × $0.06 = **$900 total**

**vs Perplexity:** 12x more expensive ($900 vs $75)
**vs OpenAI:** 1.3x more expensive ($900 vs $675)

---

## Rate Limits

**Standard tier:** No hard limits (usage-based billing)
**Burst limits:** 4,000 requests per minute (RPM)

**For our use case:**
- Processing 12 courses/hour = well within limits
- No risk of rate limit errors
- Can increase batch size if needed

---

## Citation Handling

### Challenge
Claude doesn't have Perplexity's `return_citations` parameter.

### Solution
**Prompt engineering:** Instruct Claude to include citation URLs inline with each data point.

**Enhanced user message:**
```typescript
const user_message = `Research golf course: ${course_name} in ${state_code}.

IMPORTANT: For EVERY piece of data you include:
1. Provide the source URL where you found it
2. Include URLs in the relevant section's "citations" array
3. Be specific - link directly to the page with the information

Return ONLY valid JSON with structure:
{
  "section1": {
    "tier": "Premium|Mid|Budget",
    "tier_confidence": 0.0-1.0,
    "tier_reasoning": "...",
    "tier_citations": ["url1", "url2"]  // REQUIRED
  },
  ...
}
`
```

### Validation
Agent must verify Claude includes `*_citations` arrays in each section:
- `tier_citations`
- `hazards_citations`
- `volume_citations`
- `intelligence_citations`

**If citations missing → Claude test FAILS, proceed to OpenAI**

---

## Advantages Over Perplexity

1. **Better reasoning:** Claude excels at analysis and synthesis
2. **Longer context:** 200k tokens (can include full course website if needed)
3. **Better instruction following:** More likely to return perfect JSON
4. **No rate limit concerns:** Standard tier handles our volume easily

## Disadvantages

1. **12x more expensive:** $900 vs $75
2. **No built-in web search:** Need to provide context
3. **Citation parameter:** Requires prompt engineering, not API parameter

---

## When to Use Claude

**Use Claude API if:**
- ✅ Perplexity fails citation quality checks
- ✅ Perplexity tier accuracy <90%
- ✅ Budget allows $900 for better data quality
- ✅ Willing to trade 12x cost for better reasoning

**Skip Claude if:**
- ❌ Perplexity passes all checks (save $825)
- ❌ Budget limited to <$200

---

## Testing Checklist

**Before approving Claude for full automation:**

- [ ] All 3 test courses return valid JSON
- [ ] Each section has `*_citations` array with URLs
- [ ] URLs are clickable and verifiable
- [ ] Tier classification matches manual (3/3 correct)
- [ ] Contact count averages ≥3 per course
- [ ] Email OR LinkedIn for key contacts
- [ ] Cost per course ≤$0.10
- [ ] Response time ≤20 seconds

**If ALL checked → Claude APPROVED for Phase 2.6**

---

## Resources

**Official Docs:** https://docs.anthropic.com/en/api/messages
**Pricing:** https://docs.anthropic.com/en/api/pricing
**Models:** https://docs.anthropic.com/en/docs/about-claude/models

---

**Status:** Ready for Phase 2.5.3 (ONLY if Perplexity fails)
