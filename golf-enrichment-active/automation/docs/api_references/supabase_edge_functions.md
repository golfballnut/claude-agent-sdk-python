# Supabase Edge Functions Deployment Guide

**Purpose:** Deploy and manage edge functions for LLM API testing and automation

---

## Quick Reference

**Deploy:** `supabase functions deploy <function-name> --project-ref oadmysogtfopkbmrulmq`
**Secrets:** `supabase secrets set KEY=value --project-ref oadmysogtfopkbmrulmq`
**List:** `supabase functions list --project-ref oadmysogtfopkbmrulmq`
**Logs:** `supabase functions logs <function-name> --project-ref oadmysogtfopkbmrulmq`

---

## Project Information

**Project ID:** oadmysogtfopkbmrulmq
**Project Name:** golf-course-outreach
**Region:** us-east-2
**URL:** https://oadmysogtfopkbmrulmq.supabase.co

---

## Deployment Workflow

### Step 1: Create Edge Function

```bash
cd /automation/edge_functions
supabase functions new <function-name>
```

This creates:
```
edge_functions/
└── <function-name>/
    └── index.ts
```

### Step 2: Write Function Code

**Template:**
```typescript
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
    const { param1, param2 } = await req.json()

    // Initialize Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Your logic here
    const result = await doSomething(param1, param2)

    return new Response(
      JSON.stringify({ success: true, data: result }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
```

### Step 3: Deploy to Supabase

```bash
supabase functions deploy <function-name> --project-ref oadmysogtfopkbmrulmq
```

**Example for Phase 2.5:**
```bash
cd /automation/edge_functions
supabase functions deploy test-perplexity-research --project-ref oadmysogtfopkbmrulmq
```

**Output:**
```
Deployed Functions on project oadmysogtfopkbmrulmq: test-perplexity-research
You can inspect your deployment in the Dashboard: https://supabase.com/dashboard/project/oadmysogtfopkbmrulmq/functions
```

### Step 4: Configure Secrets

**Set API keys:**
```bash
supabase secrets set PERPLEXITY_API_KEY=pplx-... --project-ref oadmysogtfopkbmrulmq
supabase secrets set ANTHROPIC_API_KEY=sk-ant-... --project-ref oadmysogtfopkbmrulmq
supabase secrets set OPENAI_API_KEY=sk-... --project-ref oadmysogtfopkbmrulmq
```

**List secrets:**
```bash
supabase secrets list --project-ref oadmysogtfopkbmrulmq
```

**Note:** Secret values are never shown, only key names

---

## Environment Variables

### Auto-Available in All Edge Functions

```typescript
Deno.env.get('SUPABASE_URL')              // Project URL
Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') // Service role key
Deno.env.get('SUPABASE_ANON_KEY')         // Anon key
```

### Custom Secrets (Set via CLI)

```typescript
Deno.env.get('PERPLEXITY_API_KEY')  // Your Perplexity key
Deno.env.get('ANTHROPIC_API_KEY')   // Your Claude key
Deno.env.get('OPENAI_API_KEY')      // Your OpenAI key
```

---

## Invoking Edge Functions

### From Command Line (Testing)

```bash
curl -X POST "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/<function-name>" \
  -H "Authorization: Bearer <anon-key>" \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
```

**Get anon key:**
```bash
# Via Supabase MCP
mcp__supabase__get_publishable_keys({ project_id: "oadmysogtfopkbmrulmq" })
```

### From Database Trigger (Automatic)

**Example:** validate-v2-research is called via database trigger

```sql
CREATE OR REPLACE FUNCTION call_edge_function()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM net.http_post(
    url := current_setting('app.supabase_url') || '/functions/v1/validate-v2-research',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.supabase_service_key')
    ),
    body := json_build_object('staging_id', NEW.id)::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### From Another Edge Function

```typescript
const response = await fetch('https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/other-function', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ param: 'value' })
})
```

---

## Scheduling Edge Functions (Cron)

### Via Supabase Dashboard

1. Go to: https://supabase.com/dashboard/project/oadmysogtfopkbmrulmq/functions
2. Select edge function
3. Click "Settings" tab
4. Scroll to "Cron Schedule"
5. Enter cron expression

**Examples:**
- Every 5 minutes: `*/5 * * * *`
- Every hour: `0 * * * *`
- Every day at 2am: `0 2 * * *`

### Cron Expression Format

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-6, Sunday=0)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)
```

**Our use case:** `*/5 * * * *` (every 5 minutes)
- Processes 10 courses per batch
- 12 batches/hour = 120 courses/hour
- 15,000 courses ÷ 120/hour = 125 hours = 5.2 days

---

## Monitoring & Debugging

### View Logs

```bash
supabase functions logs test-perplexity-research --project-ref oadmysogtfopkbmrulmq --tail
```

**Shows:**
- console.log() outputs
- Errors and stack traces
- Request/response details
- Execution time

### Check Function Status

**Via Supabase MCP:**
```typescript
mcp__supabase__list_edge_functions({ project_id: "oadmysogtfopkbmrulmq" })
```

**Via Dashboard:**
https://supabase.com/dashboard/project/oadmysogtfopkbmrulmq/functions

---

## Common Issues & Solutions

### Issue: "Cannot connect to Docker daemon"

**Cause:** Docker Desktop not running
**Fix:**
```bash
open -a Docker
sleep 10
# Retry deployment
```

### Issue: "Invalid JWT" when calling function

**Cause:** Wrong or expired authorization token
**Fix:** Use correct anon key or service role key:
```typescript
// For external calls: use anon key
Authorization: Bearer eyJhbGc...

// For internal/admin calls: use service role key
Authorization: Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}
```

### Issue: "Module not found" error

**Cause:** Import path incorrect
**Fix:** Use full ESM CDN URLs:
```typescript
// ✅ Correct
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

// ❌ Wrong
import { serve } from 'std/http/server.ts'
```

### Issue: Function times out

**Cause:** Long-running operation (LLM API call)
**Fix:** Increase timeout in dashboard settings (max: 60 seconds)

### Issue: "Secret not found"

**Cause:** Secret not set or typo in environment variable name
**Fix:**
```bash
supabase secrets set PERPLEXITY_API_KEY=your-key --project-ref oadmysogtfopkbmrulmq
supabase secrets list --project-ref oadmysogtfopkbmrulmq  # Verify
```

---

## File Organization

### Recommended Structure

```
edge_functions/
├── test-perplexity-research/
│   └── index.ts                 # Perplexity API test
├── test-claude-research/
│   └── index.ts                 # Claude API test
├── test-openai-research/
│   └── index.ts                 # OpenAI API test
├── batch-llm-research/
│   ├── index.ts                 # Production automation
│   └── v2_prompt.md             # Embedded V2 prompt
└── validate-v2-research/
    └── index.ts                 # Already deployed
```

**Note:** Each function is self-contained in its own directory

---

## Testing Locally (Optional)

### Serve Function Locally

```bash
supabase functions serve test-perplexity-research --env-file /path/to/.env
```

**Required in .env:**
```
SUPABASE_URL=https://oadmysogtfopkbmrulmq.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your-service-key>
PERPLEXITY_API_KEY=<your-perplexity-key>
```

**Test locally:**
```bash
curl -X POST http://localhost:54321/functions/v1/test-perplexity-research \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Test Course", "state_code": "NC"}'
```

---

## Best Practices

### 1. CORS Handling
Always include CORS headers for browser access:
```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}
```

### 2. Error Handling
Catch all errors and return structured responses:
```typescript
try {
  // Logic
} catch (error) {
  console.error('Error:', error)
  return new Response(
    JSON.stringify({ error: error.message, stack: error.stack }),
    { status: 500, headers: corsHeaders }
  )
}
```

### 3. Logging
Use console.log for debugging:
```typescript
console.log('Processing course:', course_name)
console.log('API response:', result)
console.error('Error occurred:', error)
```

### 4. Timeouts
Set appropriate timeouts for external API calls:
```typescript
const response = await fetch(url, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify(data),
  signal: AbortSignal.timeout(60000)  // 60 second timeout
})
```

### 5. Rate Limiting
Add delays between requests:
```typescript
await new Promise(resolve => setTimeout(resolve, 5000))  // 5 second delay
```

---

## Phase 2.5 Deployment Checklist

**For test-perplexity-research:**
- [ ] Function code written in `/automation/edge_functions/test-perplexity-research/index.ts`
- [ ] Includes `return_citations: true` parameter
- [ ] Deployed to Supabase
- [ ] PERPLEXITY_API_KEY secret configured
- [ ] Tested with curl command
- [ ] Logs show no errors

**For test-claude-research:**
- [ ] Function code written
- [ ] Uses `system` parameter for V2 prompt
- [ ] Deployed to Supabase
- [ ] ANTHROPIC_API_KEY secret configured
- [ ] Tested successfully

**For test-openai-research:**
- [ ] Function code written
- [ ] Includes `response_format: { type: "json_object" }`
- [ ] Deployed to Supabase
- [ ] OPENAI_API_KEY secret configured
- [ ] Tested successfully

---

## Phase 2.6 Production Deployment

**For batch-llm-research:**

1. **Create function** with selected API from Phase 2.5
2. **Deploy** to Supabase
3. **Configure cron schedule:** `*/5 * * * *` (every 5 minutes)
4. **Monitor logs** for first 100 courses
5. **Verify** validation success rate ≥90%
6. **Enable production tables:** Update Render `USE_TEST_TABLES=false`
7. **Let it run** for 15,000 courses

---

## Useful Commands

```bash
# Deploy
supabase functions deploy <name> --project-ref oadmysogtfopkbmrulmq

# View logs (live tail)
supabase functions logs <name> --project-ref oadmysogtfopkbmrulmq --tail

# List all functions
supabase functions list --project-ref oadmysogtfopkbmrulmq

# Delete function
supabase functions delete <name> --project-ref oadmysogtfopkbmrulmq

# Set secret
supabase secrets set KEY=value --project-ref oadmysogtfopkbmrulmq

# List secrets
supabase secrets list --project-ref oadmysogtfopkbmrulmq

# Unset secret
supabase secrets unset KEY --project-ref oadmysogtfopkbmrulmq
```

---

**Ready for deployment!** Follow Phase 2.5.1 plan to build test functions.
