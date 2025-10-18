---
name: Golf Course Enrichment Pipeline
description: Orchestrate multi-agent workflow to enrich golf courses with contact data, business intelligence, and water hazard detection. Use when deploying agents, debugging the pipeline, or enriching golf course data for range ball outreach.
allowed-tools: Read, Bash, Grep, Glob, mcp__supabase__*, mcp__clickup__*
---

# Golf Course Enrichment Pipeline

## Overview

This skill guides you through the 8-agent enrichment pipeline that transforms a golf course name into fully qualified sales leads with business intelligence.

**Pipeline:** Agent 1 → 2 → 6 → 7 → (3, 5, 6.5 per contact) → 8

**Performance:**
- Cost: $0.155 per course (avg 3 contacts)
- Time: 3 minutes per course
- Success: 100% (when PATH configured)

---

## When to Use This Skill

- Deploying agents to Railway/Render
- Debugging agent failures
- Understanding the enrichment workflow
- Running manual enrichment tests
- Integrating with Supabase or ClickUp
- Troubleshooting cost or performance issues

---

## Agent Architecture

### **Agent 1: URL Finder**
**File:** `agents/agent1_url_finder.py`
**Purpose:** Find VSGA directory URL for golf course
**Input:** Course name, state code
**Output:** `{url, cost, turns}`
**Cost:** $0.021
**Status:** ✅ Working (VA only, needs multi-state support)

### **Agent 2: Data Extractor**
**File:** `agents/agent2_data_extractor.py`
**Purpose:** Extract course info + staff from VSGA listing
**Input:** VSGA URL
**Output:** `{course_name, website, phone, staff[]}`
**Cost:** $0.013
**Status:** ⚠️ Intermittent (WebFetch dependency)

### **Agent 6: Course-Level Intelligence**
**File:** `agents/agent6_course_intelligence.py`
**Purpose:** Classify course (high-end/budget) + opportunity scoring
**Input:** Course name, website, water hazard count
**Output:** `{segmentation, range_intel, opportunities}`
**Cost:** $0.036
**Runs:** ONCE per course (not per contact)
**Status:** ✅ Working

### **Agent 7: Water Hazard Counter**
**File:** `agents/agent7_water_hazard_counter.py`
**Purpose:** Count water hazards for ball retrieval opportunity
**Input:** Course name, state, website
**Output:** `{water_hazard_count, confidence, details}`
**Cost:** $0.006
**Success:** 100% (5/5 courses)
**Status:** ✅ READY FOR POC DEPLOYMENT

### **Agent 3: Contact Enricher**
**File:** `agents/agent3_contact_enricher.py`
**Purpose:** Find email + LinkedIn via Hunter.io
**Input:** Contact dict (name, title, company, domain)
**Output:** `{email, email_confidence, email_method, linkedin_url}`
**Cost:** $0.012 per contact
**Success:** 56% (expected ~50%)
**Status:** ✅ Working

### **Agent 5: Phone Finder**
**File:** `agents/agent5_phone_finder.py`
**Purpose:** Find phone via Perplexity AI
**Input:** Contact dict (name, title, company, state)
**Output:** `{phone, phone_method, confidence}`
**Cost:** $0.012 per contact
**Success:** 78%
**Status:** ✅ Working

### **Agent 6.5: Contact Background**
**File:** `agents/agent65_contact_enrichment.py`
**Purpose:** Find tenure, previous clubs, industry experience
**Input:** Contact dict (name, title, company)
**Output:** `{tenure_years, previous_clubs[], industry_experience_years, responsibilities[], career_notes}`
**Cost:** $0.010 per contact
**Status:** ✅ Working

### **Agent 8: Data Writer**
**Files:**
- `agent8_json_writer_backup.py` - Outputs JSON (working)
- `agent8_supabase_writer.py` - Writes to Supabase (not tested)

**Purpose:** Persist enrichment data
**Input:** Course data, course intel, water data, enriched contacts
**Output:** `{success, course_id, contacts_written}`
**Cost:** $0.000
**Status:** ⚠️ Supabase version blocked by deployment testing

---

## Orchestrator Flow

### **File:** `agents/orchestrator.py`

### **Sequential Execution:**

```python
# Step 1: Course-level enrichment (run ONCE)
url = await agent1_find_url(course_name, state_code)
course = await agent2_extract(url)
course_intel = await agent6_enrich_course(course_name, website, water_count)
water = await agent7_count_hazards(course_name, state, website)

# Step 2: Contact-level enrichment (per contact)
enriched_contacts = []
for staff in course.staff:
    contact = await agent3_enrich(staff)
    contact = await agent5_find_phone(contact)
    contact = await agent65_background(contact)
    enriched_contacts.append(contact)

# Step 3: Write to database
await agent8_write(course, course_intel, water, enriched_contacts)
```

### **Error Handling:**
- All-or-nothing (if any agent fails, entire course fails)
- Retry at course level (not agent level)
- Detailed error messages with agent name + reason

### **Cost Breakdown:**
```
Agent 1:    $0.021
Agent 2:    $0.013
Agent 6:    $0.036 (once)
Agent 7:    $0.006 (once)
Agent 3:    $0.012 × 3 = $0.036
Agent 5:    $0.012 × 3 = $0.036
Agent 6.5:  $0.010 × 3 = $0.030
Agent 8:    $0.000
─────────────────────────
TOTAL:      $0.155/course
```

---

## Deployment Architecture

### **🚨 CRITICAL: Deployment Not Yet Validated**

**Local (Current):**
- Agents use Claude Code CLI subprocess
- PATH dependency: `/Users/stevemcmillian/.npm-global/bin/claude`
- Works when PATH is set

**Production (Target):**
- Docker container with Claude CLI installed
- FastAPI wrapper exposing REST endpoints
- Railway/Render hosting
- Same agent code, different execution environment

### **Deployment Requirements:**

**Dockerfile must include:**
```dockerfile
# Install Node.js
RUN apt-get update && apt-get install -y nodejs npm

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Verify installation
RUN claude --version
```

**Environment Variables:**
```bash
HUNTER_API_KEY=xxx          # Agent 3
PERPLEXITY_API_KEY=xxx      # Agents 5, 6, 6.5, 7
ANTHROPIC_API_KEY=xxx       # Claude SDK
SUPABASE_URL=xxx            # Agent 8
SUPABASE_SERVICE_ROLE_KEY=xxx
CLICKUP_API_KEY=xxx         # ClickUp sync
```

---

## Database Schema (Supabase)

### **Test Tables (Migrations Applied):**
- `test_golf_courses`
- `test_golf_course_contacts`

### **Production Tables (Ready for Migrations):**
- `golf_courses` (358 existing rows)
- `golf_course_contacts` (236 existing rows)

### **Key Fields:**

**Course-Level (Agent 6, 7):**
- `segment` (high-end, budget, both, unknown)
- `segment_confidence` (1-10)
- `segment_signals` (JSONB array)
- `range_intel` (JSONB object)
- `opportunity_scores` (JSONB: buy, sell, lease, retrieval, etc.)
- `water_hazard_count` (integer)
- `water_hazard_confidence` (high, medium, low, none)

**Contact-Level (Agent 3, 5, 6.5):**
- `email`, `email_confidence`, `email_method`
- `linkedin_url`, `linkedin_method`
- `phone`, `phone_method`, `phone_confidence`
- `tenure_years`, `tenure_confidence`
- `previous_clubs` (JSONB array)
- `industry_experience_years`
- `responsibilities` (JSONB array)
- `career_notes` (TEXT)

**Migrations:**
- `migrations/001_add_agent_enrichment_fields.sql`
- `migrations/002_agent_refactor_update.sql`

---

## ClickUp Integration

### **Structure (Existing):**

**📇 Contacts List (ID: 901413061863):**
- 1 task per contact
- Format: "⛳ Name - Title (Course)"
- Custom Fields: Email, LinkedIn URL, Position, Course (relationship), State

**🏌️ Golf Courses List (ID: 901413061864):**
- 1 task per course
- Format: "🏌️ Course Name"

**📞 Outreach Activities List (ID: 901413111587):**
- 1 task per campaign
- Links to contacts

### **Custom Fields to Add:**

**Contacts:**
- Email Confidence (number: 0-100)
- Email Method (dropdown: hunter_io, web_search)
- Phone Confidence (number: 0-100)
- Tenure Years (number)
- Segment (dropdown: high-end, budget, both)

**Golf Courses:**
- Segment (dropdown)
- Segment Confidence (number: 1-10)
- Water Hazards (number)
- Has Range (checkbox)
- Top Opportunity (dropdown)

---

## Running the Pipeline

### **Manual Test (Local):**

```bash
# Set PATH (required for local testing)
export PATH="/Users/stevemcmillian/.npm-global/bin:$PATH"

# Run orchestrator
python3 agents/orchestrator.py

# Output: JSON file in results/enrichment/
```

### **Production (After Deployment POC):**

```bash
# API endpoint
curl -X POST https://your-app.railway.app/enrich-course \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "course_name": "Richmond Country Club",
    "state_code": "VA"
  }'

# Response: Full enrichment data + Supabase course_id
```

---

## Troubleshooting

### **"Claude Code not found" Error**

**Cause:** SDK can't find `claude` CLI in PATH

**Solutions:**
1. **Local:** `export PATH="/Users/stevemcmillian/.npm-global/bin:$PATH"`
2. **Docker:** Ensure `npm install -g @anthropic-ai/claude-code` in Dockerfile
3. **Verify:** `which claude` should return path

### **Agent Returns No JSON**

**Cause:** Agent output doesn't match expected format

**Solutions:**
1. Check agent's system_prompt (must specify JSON format)
2. Use `extract_json_from_text()` utility (handles edge cases)
3. Add debug output to see raw agent response
4. Verify agent has required tools (check allowed_tools list)

### **Intermittent Failures**

**Cause:** External API issues (Hunter.io, Perplexity rate limits)

**Solutions:**
1. Check API key validity
2. Check rate limits (Perplexity: 50 req/day free)
3. Implement retry logic (exponential backoff)
4. Monitor API status pages

### **Cost Overruns**

**Expected:** $0.155 per course

**If higher:**
- Agent 6 using Sonnet instead of Haiku? (3× cost)
- Agent 2 retrying too many times?
- Check `result_message.total_cost_usd` per agent

---

## Testing Checklist

### **Before Deployment:**
- [ ] All agents run locally with PATH set
- [ ] Test on 3+ courses (different types)
- [ ] JSON outputs validated
- [ ] Cost per course < $0.16
- [ ] Success rate > 95%

### **Deployment POC (Agent 7):**
- [ ] Dockerfile builds successfully
- [ ] Container runs locally (docker run)
- [ ] API responds within 15s
- [ ] Results match local tests
- [ ] Deployed to Railway/Render
- [ ] Production endpoint works
- [ ] Load test (100 requests)

### **Full Pipeline Deployment:**
- [ ] All agents work in container
- [ ] Orchestrator API endpoint functional
- [ ] Supabase writes successful
- [ ] ClickUp sync working
- [ ] End-to-end test (course → ClickUp task)

---

## File References

**Core Documentation:**
- [Next Session Handoff](../../docs/next_session_handoff.md) - Current status + blocker
- [Orchestrator Test Results](../../docs/orchestrator_test_results.md) - Performance data
- [Supabase Schema Design](../../docs/supabase_schema_design.md) - Database structure
- [Infrastructure Architecture](../../docs/infrastructure_architecture.md) - System diagram

**Test Results:**
- [Agent 7 Test Results](../../results/agent7_test_results.json) - 100% success baseline
- [Enrichment Outputs](../../results/enrichment/) - 5 complete JSON files

**Migration Files:**
- [Migration 001](../../migrations/001_add_agent_enrichment_fields.sql) - Agent 6/7 fields
- [Migration 002](../../migrations/002_agent_refactor_update.sql) - Agent 3/5/6.5 fields

---

## Cost Optimization

### **Current Costs:**
| Agent | Cost | Optimization Potential |
|-------|------|------------------------|
| Agent 1 | $0.021 | Cache VSGA directory (save 90%) |
| Agent 2 | $0.013 | Switch to Jina custom tool |
| Agent 6 | $0.036 | Use Haiku instead of Sonnet (save 66%) |
| Agent 7 | $0.006 | Already optimized ✅ |
| Agent 3 | $0.036 | Already optimized ✅ |
| Agent 5 | $0.036 | Already optimized ✅ |
| Agent 6.5 | $0.030 | Already optimized ✅ |

**Target:** $0.12 per course (20% reduction possible)

### **Optimization Strategies:**
1. **Cache VSGA directory** (refresh daily, save Agent 1 costs)
2. **Use Haiku for Agent 6** (test segmentation quality first)
3. **Parallel contact processing** (3× faster, same cost)
4. **Batch Perplexity queries** (if API supports)

---

## Data Flow

### **JSON Output Structure:**

```json
{
  "course_name": "Richmond Country Club",
  "agent1": {"url": "...", "cost_usd": 0.021},
  "agent2": {"course_name": "...", "website": "...", "staff": [...]},
  "agent6": {
    "segmentation": {"primary_target": "high-end", "confidence": 9},
    "opportunities": {"range_ball_buy": 8, "range_ball_lease": 7}
  },
  "agent7": {"water_hazard_count": 7, "confidence": "low"},
  "contacts": [
    {
      "name": "Stacy Foster",
      "agent3": {"email": "...", "linkedin_url": "..."},
      "agent5": {"phone": "...", "confidence": 90},
      "agent65": {
        "tenure_years": null,
        "previous_clubs": [],
        "responsibilities": [...]
      }
    }
  ],
  "summary": {"total_cost_usd": 0.155, "contacts_enriched": 3}
}
```

### **Supabase Tables:**
```sql
test_golf_courses (migrations applied)
  ├── segment, segment_confidence, segment_signals
  ├── range_intel, opportunity_scores
  ├── water_hazard_count, water_hazard_confidence
  └── agent6_enriched_at, agent7_enriched_at

test_golf_course_contacts (migrations applied)
  ├── email, email_confidence, email_method
  ├── linkedin_url, linkedin_method
  ├── phone, phone_method, phone_confidence
  ├── tenure_years, tenure_confidence, previous_clubs
  ├── industry_experience_years, responsibilities, career_notes
  └── agent65_enriched_at
```

### **ClickUp Tasks:**
```
📇 Contacts List:
  ⛳ Stacy Foster - General Manager (Richmond CC)
    ├── Custom Fields: Email, Phone, LinkedIn, Tenure, Segment
    └── Description: Career notes, responsibilities, enrichment details

🏌️ Golf Courses List:
  🏌️ Richmond Country Club
    ├── Custom Fields: Segment, Water Hazards, Opportunities
    └── Tags: va, golf course
```

---

## Common Workflows

### **1. Deploy Agent 7 POC**

```bash
# Create deployment directory
mkdir deployment
cd deployment

# Create Dockerfile (see template below)
# Create api.py (FastAPI wrapper)
# Create requirements.txt

# Test locally
docker build -t agent7-poc .
docker run -p 8000:8000 -e PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY agent7-poc

# Test endpoint
curl -X POST http://localhost:8000/count-hazards \
  -d '{"course": "Richmond Country Club", "state": "VA"}'

# Deploy to Railway
railway login
railway init
railway up

# Test production
curl https://agent7-poc.railway.app/count-hazards \
  -d '{"course": "Belmont Golf Course", "state": "VA"}'
```

### **2. Run Full Enrichment (Local)**

```bash
# Ensure PATH is set
export PATH="/Users/stevemcmillian/.npm-global/bin:$PATH"

# Run orchestrator
python3 agents/orchestrator.py

# Check output
ls -lt results/enrichment/

# Review JSON
cat results/enrichment/enrichment_*.json | jq .
```

### **3. Apply Migrations to Supabase**

**Via MCP Tools (programmatic):**
```python
from mcp__supabase__apply_migration import apply_migration

# Read migration file
with open('migrations/001_add_agent_enrichment_fields.sql') as f:
    migration_sql = f.read()

# Apply to test tables
apply_migration(
    project_id='oadmysogtfopkbmrulmq',
    name='add_agent6_7_fields',
    query=migration_sql
)
```

**Via SQL Editor (manual):**
1. Go to Supabase dashboard
2. SQL Editor → New Query
3. Paste migration SQL
4. Run

### **4. Sync to ClickUp (Manual)**

```bash
# After orchestrator writes to Supabase
python3 agents/clickup_sync.py --course-id <uuid>

# Creates:
# - 1 task in Golf Courses list
# - 3 tasks in Contacts list (one per contact)
# - All custom fields populated
```

---

## Key Insights

### **Agent Design Principles:**

1. **Course-Level vs Contact-Level Split**
   - Agent 6 runs ONCE (segmentation is course-wide)
   - Agent 6.5 runs per contact (tenure is individual)
   - 38% cost savings by eliminating redundant queries

2. **Direct API > MCP Tools**
   - Agents 5, 6, 6.5, 7: Direct Perplexity API (100% reliable)
   - Agent 2: WebFetch (intermittent)
   - Lesson: Use direct APIs for critical paths

3. **JSON-First Development**
   - Output to JSON before committing to schema
   - Caught field mapping issues early
   - Validated data structure across course types

4. **Public vs Private Courses**
   - Private clubs: 83% email success
   - Public courses: 0% email success
   - This is expected, not a bug

### **Business Intelligence:**

**Segmentation Signals (Agent 6):**
- High-End: Private club, 4.5+ rating, recent renovations, premium positioning
- Budget: Public course, 3.5-4.5 rating, "good value" reviews, cost concerns
- Both: Features of both segments

**Opportunity Scores (1-10):**
- `range_ball_buy`: High-end clubs (buy their used balls)
- `range_ball_sell`: Budget clubs (sell reconditioned balls)
- `range_ball_lease`: All clubs (subscription model)
- `ball_retrieval`: Based on water_hazard_count (7+ hazards = high value)

**Water Hazard Value:**
- 15+ hazards = PREMIUM ($30K-60K lost balls/year)
- 10-14 hazards = HIGH ($15K-30K/year)
- 5-9 hazards = MODERATE ($5K-15K/year)

---

## Next Steps (After Deployment POC)

**Phase 1: Deployment** (CURRENT BLOCKER)
- Deploy Agent 7 to Railway/Render
- Validate SDK works in production
- **DO NOT proceed without this**

**Phase 2: Full Pipeline**
- Deploy orchestrator (all agents)
- Test with 10+ courses
- Validate cost/performance

**Phase 3: Supabase Integration**
- Apply production migrations
- Test Agent 8 Supabase writer
- Validate data integrity

**Phase 4: ClickUp Sync**
- Build sync script
- Add custom fields
- Test end-to-end (course → Supabase → ClickUp)

**Phase 5: Automation**
- Supabase triggers (ON INSERT)
- Edge functions (webhook receivers)
- ClickUp automations (outreach sequences)

**Phase 6: Multi-State Expansion**
- Agent 1 update (support DC, WV, SC, TN, NJ, NY, OH)
- State directory mapping
- Test across all 12 states

**Phase 7: Data Freshness**
- Monthly LinkedIn checks (job changes)
- Email verification
- Contact updates

---

## Success Metrics

**Pipeline (When Working):**
- ✅ 100% success rate (3/3 courses)
- ✅ 100% segmentation accuracy
- ✅ $0.155 avg cost per course
- ✅ 3 minutes per course
- ✅ 56% email success (expected)
- ✅ 78% phone success (exceeds expectations)

**Business Impact:**
- 97% cost reduction vs manual ($4,000 → $125/month)
- 500 courses/month capacity
- Qualified leads with business intelligence
- Sales team has segment, opportunities, contact history

---

## Critical Files

**Must Not Break:**
- `agents/agent7_water_hazard_counter.py` (POC deployment candidate)
- `agents/orchestrator.py` (coordinates all agents)
- `migrations/001_*.sql` and `002_*.sql` (database schema)

**Safe to Modify:**
- `agents/agent8_json_writer_backup.py` (development only)
- Test scripts (test_*.py)
- Documentation (docs/*.md)

**Backup Before Changing:**
- All agents (agents/agent*.py)
- Orchestrator (agents/orchestrator.py)

---

## Contact & Support

**Project:** Golf Course Outreach Automation
**Owner:** Steve McMillian
**Company:** Links Choice / Golf Ball Nut

**Key Contacts:**
- Golf Course data: 358 courses, 236 contacts in Supabase
- Target: 500 courses/month at scale
- Focus: Range ball procurement + ball retrieval programs

---

**Last Updated:** 2025-01-17
**Status:** Agents built, deployment validation required
**Next Action:** Deploy Agent 7 POC to Railway/Render
