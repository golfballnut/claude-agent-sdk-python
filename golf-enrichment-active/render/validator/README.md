# V2 Golf Course Research Validator

**Purpose:** Validates V2 LLM research JSON and writes to Supabase
**Architecture:** FastAPI service deployed on Render
**Phase:** 2.0 - Data Flow Validation

---

## Architecture

```
Manual V2 JSON paste → llm_research_staging table
    ↓ DATABASE TRIGGER
Edge Function: validate-v2-research
    ↓ HTTP POST
Render Validator API: /validate-and-write (THIS SERVICE)
    ↓ VALIDATES + PARSES
5 Section Parsers (tier, hazards, volume, contacts, intel)
    ↓ WRITES
Supabase: golf_courses + golf_course_contacts
    ↓ DATABASE TRIGGER (on contact insert)
Edge Function: create-clickup-tasks (automatic)
```

---

## Validation Strategy

### CRITICAL Validations (Hard Failures)
- All 5 sections present and parseable
- Tier field exists with valid value (Premium/Mid/Budget)
- Tier confidence ≥ 0.5
- ~~At least 1 contact~~ (changed: 0 contacts allowed, will flag)

### QUALITY Validations (Soft Warnings → ClickUp Flags)
- `LOW_TIER_CONFIDENCE`: tier_confidence < 0.7
- `NO_CONTACTS_FOUND`: zero contacts discovered
- `NO_CONTACT_METHODS`: contacts exist but no emails/LinkedIn
- `NO_VOLUME_DATA`: volume estimate is None

---

## Directory Structure

```
render/validator/
├── api.py                     # FastAPI endpoints
├── validator.py               # Main validation orchestrator
├── parsers/
│   ├── __init__.py
│   ├── section1_tier.py       # Course tier classification
│   ├── section2_hazards.py    # Water hazards assessment
│   ├── section3_volume.py     # Annual rounds estimate
│   ├── section4_contacts.py   # Decision makers
│   └── section5_intel.py      # Basic intelligence
├── writers/
│   ├── __init__.py
│   └── supabase_writer.py     # Database writer (mirrors Agent 8)
├── requirements.txt
├── Dockerfile
└── README.md                  # This file
```

---

## Local Development

### Prerequisites
- Python 3.11+
- Supabase project with migrations applied (013, 014)

### Setup
```bash
cd render/validator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-role-key"

# Run server
python api.py
```

### Test Endpoint
```bash
# Health check
curl http://localhost:8000/health

# Validate test JSON
curl -X POST http://localhost:8000/validate-and-write \
  -H "Content-Type: application/json" \
  -d @test_v2_json.json
```

---

## Deployment to Render

### Step 1: Create Render Web Service

1. **Go to:** https://dashboard.render.com/
2. **New → Web Service**
3. **Connect repository** (if deploying from Git)
4. **Settings:**
   - Name: `golf-v2-validator`
   - Region: Same as Supabase (e.g., `US East`)
   - Branch: `main`
   - Root Directory: `agenttesting/golf-enrichment/render/validator`
   - Runtime: `Docker`
   - Instance Type: `Starter` ($7/month)

### Step 2: Set Environment Variables

In Render dashboard → Environment:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
PORT=8000
```

### Step 3: Deploy

Click **Create Web Service** → Render will:
1. Build Docker image
2. Deploy to production
3. Provide URL: `https://golf-v2-validator.onrender.com`

### Step 4: Update Supabase Edge Function

Update `validate-v2-research/index.ts` with Render URL:
```typescript
const renderValidatorUrl = Deno.env.get('RENDER_VALIDATOR_URL')
// Set in Supabase → Edge Functions → Environment Variables
// RENDER_VALIDATOR_URL=https://golf-v2-validator.onrender.com
```

---

## Testing End-to-End

### Prerequisites
1. Supabase migrations applied (013, 014)
2. Render service deployed
3. Edge function `validate-v2-research` deployed
4. Environment variable `RENDER_VALIDATOR_URL` set in Supabase

### Test Steps

**1. Prepare V2 JSON**
Run V2 prompt on a test course (e.g., Cape Fear National) and copy JSON output.

**2. Open Supabase Studio**
```
https://supabase.com/dashboard/project/YOUR_PROJECT/editor
```

**3. Insert into staging table**
```sql
INSERT INTO llm_research_staging (course_name, state_code, v2_json)
VALUES (
  'Cape Fear National',
  'NC',
  '{"section1": {...}, "section2": {...}, ...}'::jsonb
);
```

**4. Verify trigger fired**
Check Supabase Logs → Edge Functions:
```
🚀 Validation triggered for: Cape Fear National (NC)
```

**5. Verify Render logs**
Check Render → Logs:
```
🔍 Validating V2 JSON for: Cape Fear National
✅ Structure validation passed
📋 Parsing Section 1: Course Tier
...
💾 Writing to Supabase...
✅ Course record written: abc-123-def
✅ Total contacts written: 4
```

**6. Verify database writes**
Check Supabase → Table Editor:
- `golf_courses` → Find Cape Fear National
  - `course_tier` = "Premium"
  - `annual_rounds_estimate` = 27000
  - `v2_research_json` = {full JSON}
- `golf_course_contacts` → 4 contacts created

**7. Verify ClickUp tasks**
Check ClickUp → Lists:
- Golf Course task created
- 4 Contact tasks created
- Outreach Activity task created with relationships

**8. Check for validation flags**
If any warnings, check `golf_courses.v2_validation_flags`:
```sql
SELECT course_name, v2_validation_flags
FROM golf_courses
WHERE course_name = 'Cape Fear National';
```

---

## Troubleshooting

### 🔴 Edge function times out
- **Cause:** Render service cold start (free tier)
- **Fix:** Upgrade to Starter plan or wait 30s for service to wake

### 🔴 "Missing required sections" error
- **Cause:** V2 JSON structure invalid
- **Fix:** Verify JSON has `section1` through `section5` keys

### 🔴 "Tier confidence too low" error
- **Cause:** tier_confidence < 0.5
- **Fix:** Re-run V2 prompt with better research sources

### 🔴 Contacts not creating ClickUp tasks
- **Cause:** `enriched_at` field not triggering database trigger
- **Fix:** Check trigger exists: `on_contact_inserted` on `golf_course_contacts`

### 🔴 Render build fails
- **Cause:** Missing dependencies or Python version mismatch
- **Fix:** Check Dockerfile uses `python:3.11-slim` and requirements.txt is valid

---

## API Reference

### POST /validate-and-write

**Request:**
```json
{
  "staging_id": "uuid",
  "course_id": "uuid or null",
  "course_name": "Cape Fear National",
  "state_code": "NC",
  "v2_json": {
    "section1": {...},
    "section2": {...},
    "section3": {...},
    "section4": {...},
    "section5": {...}
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "course_id": "abc-123-def",
  "contacts_created": 4,
  "validation_flags": ["LOW_TIER_CONFIDENCE"]
}
```

**Response (Failure):**
```json
{
  "detail": "Missing required section1"
}
```
Status: 400

### GET /health

**Response:**
```json
{
  "status": "healthy",
  "service": "golf-v2-validator",
  "version": "1.0.0",
  "env_vars_configured": true
}
```

---

## Next Steps

**Phase 2.1:** Database cleanup (remove redundant tables)
**Phase 2.2:** Contact enrichment (Apollo/Hunter for email discovery)
**Phase 3:** Organization & scoring
**Phase 4:** ClickUp integration enhancements

---

**Created:** 2025-10-31
**Status:** Phase 2.0 Complete
