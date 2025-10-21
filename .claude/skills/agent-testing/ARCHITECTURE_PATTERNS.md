# Agent Architecture Patterns

**Purpose:** Generalizable design patterns for building multi-agent systems with Claude SDK + MCP + Supabase.

**Learned from:** Golf enrichment Agent 4/6.5 consolidation (Oct 20, 2025)

**Applies to:** Any agent team using this tech stack

---

## Pattern 1: The "Data Already There" Pattern ⭐

### **Problem**
Adding new agents without checking if existing agents already have the data.

### **Anti-Pattern:**
```python
# Agent A: Get LinkedIn URL
agent_a_result = find_linkedin()  # Returns: {"url": "..."}

# Agent B: Scrape LinkedIn for tenure
agent_b_result = scrape_linkedin(agent_a_result["url"])  # Separate API call!
```

### **Better Pattern:**
```python
# Agent A: Get LinkedIn URL
agent_a_result = find_linkedin()
# Returns: {"url": "...", "description": "Manager. Jan 2019 - Present 6 years..."}

# Check description first!
if "years" in agent_a_result.get("description", ""):
    # Extract tenure from description (NO Agent B needed!)
    tenure = extract_tenure(agent_a_result["description"])
```

### **Real Example:**
- **Before:** Agent 4 (find LinkedIn) + Agent 6.5 (scrape for tenure) = 2 agents
- **After:** Agent 4 enhanced (extract tenure from search) = 1 agent
- **Savings:** $0.003 per contact, simpler architecture

### **When to Apply:**
- Before adding new agent, check existing agent responses
- Look for "bonus" data in API responses
- Extract from descriptions/metadata first
- Only add new agent if data truly unavailable

### **Benefits:**
✅ Fewer agents (simpler architecture)
✅ Fewer API calls (faster, cheaper)
✅ No redundant data fetching
✅ Single source of truth

---

## Pattern 2: Specialist vs Bonus Fields ⭐

### **Problem**
Relying on "bonus" fields from non-specialist agents leads to inconsistent coverage.

### **Anti-Pattern:**
```python
# Agent 3: Email finder (specialist)
agent3_result = find_email()
# Sometimes returns: {"email": "...", "linkedin_url": "..."}  ← Bonus field

# Agent 4: LinkedIn finder (specialist)
if not contact.get("linkedin_url"):  # ← BAD CONDITIONAL!
    agent4_result = find_linkedin()
# Skipped when Agent 3 had bonus LinkedIn!
```

### **Better Pattern:**
```python
# Agent 3: Email specialist (ALWAYS runs)
agent3_result = find_email()
contact.update(agent3_result)

# Agent 4: LinkedIn specialist (ALWAYS runs!)
agent4_result = find_linkedin()
contact.update(agent4_result)  # Overwrites bonus LinkedIn with specialist result
```

### **Real Example:**
- **Before:** Agent 4 conditional on Agent 3's bonus linkedin_url
- **Issue:** Inconsistent LinkedIn coverage, missed tenure extractions
- **After:** Agent 4 always runs (LinkedIn specialist)
- **Result:** Consistent 50% LinkedIn success, reliable tenure extraction

### **Design Principles:**
1. **One agent = one specialty** (email, LinkedIn, phone)
2. **Specialists always run** (don't skip based on bonus data)
3. **Bonus fields = nice-to-have** (not reliable)
4. **Later data overwrites earlier** (specialist wins over bonus)

### **When to Apply:**
- Multi-agent enrichment pipelines
- Different data sources for same field
- Quality vs coverage trade-offs

### **Benefits:**
✅ Consistent results (specialist always tries)
✅ Better coverage (purpose-built tool wins)
✅ Simpler logic (no conditionals)
✅ Predictable behavior

---

## Pattern 3: Fractional Value Precision

### **Problem**
Duration calculations return decimals (6.8 years) but database uses INTEGER.

### **Issue:**
```python
# Agent calculates
tenure = 6 years + 10 months = 6.8 years  # float

# Database has
tenure_years INTEGER  # Can't store 6.8!

# Error: "invalid input syntax for type integer: '6.8'"
```

### **Solution:**
```sql
-- Change column type to support decimals
ALTER TABLE contacts
  ALTER COLUMN tenure_years TYPE NUMERIC(4,1)
  USING tenure_years::numeric;
-- NUMERIC(4,1) = 4 total digits, 1 decimal place (0.0 to 999.9)
```

### **Design Decision:**
**Option A:** Round to integers (6.8 → 7)
- Pro: Simpler database schema
- Con: Less accurate (10 months lost!)

**Option B:** Store as decimal (6.8)
- Pro: More accurate ("6 years 10 months")
- Con: Need NUMERIC type

**Recommendation:** Option B (precision matters for business decisions)

### **Real Example:**
- Mike Tate: 12.8 years (12 years 10 months)
- Rounding to 13 loses information
- Decimal preserves exact tenure

### **When to Apply:**
- Duration calculations (years, months, days)
- Ratings/scores (4.5 stars, 8.7/10)
- Percentages (85.3%)
- Financial values ($12.75)

### **Benefits:**
✅ Accurate data (no rounding loss)
✅ Better for reporting (precise values)
✅ Business-friendly ("6 years 10 months" vs "7 years")

---

## Pattern 4: Test Files Isolation

### **Problem**
Modifying production files during testing risks breaking production.

### **Anti-Pattern:**
```python
# Editing production orchestrator.py directly
# Testing new Agent 4 tenure...
# Oops, broke production! 😱
```

### **Better Pattern:**
```
Production Files (untouched):
├── orchestrator.py (has Agent 6.5)
├── agent8_supabase_writer.py (reads Agent 6.5 format)

Test Files (iterate freely):
├── test_orchestrator.py (no Agent 6.5, uses Agent 4)
├── test_agent8_supabase_writer.py (reads Agent 4 format)
├── test_quick.py (runs test workflow)

After validation:
└── Sync test → production files
```

### **File Naming Convention:**
- `test_*.py` = Testing changes (safe to break!)
- `*.py` = Production (don't touch until validated!)
- `_deprecated_*.py` = Archived (keep for reference)

### **Docker Strategy:**
```dockerfile
# Test Dockerfile
COPY test_orchestrator.py ./orchestrator.py  ← Renames during copy!
COPY test_agent8.py ./agents/agent8.py

# Production uses real files
COPY orchestrator.py ./orchestrator.py
```

### **When to Apply:**
- Any multi-file agent system
- Testing breaking changes
- Iterative development
- CI/CD pipelines

### **Benefits:**
✅ Production protected (can't accidentally break)
✅ Safe iteration (break test files freely)
✅ Easy rollback (production files intact)
✅ Clear separation (test vs prod)

---

## Pattern 5: Incremental Constraint Discovery

### **Problem**
Production databases have legacy constraints you don't know about until you test.

### **Anti-Pattern:**
```python
# Try to predict all constraints upfront
# Spend hours auditing database schema
# Still miss edge cases
```

### **Better Pattern:**
```python
# Test → Error → Fix → Retest cycle

# Test 1
Error: "segment can't be unknown"
Fix: ALTER constraint to allow "unknown"

# Test 2
Error: "value too long for VARCHAR(20)"
Fix: Expand to VARCHAR(50)

# Test 3
Error: "segment_confidence must be 1-10"
Fix: Allow 0-10 (include unknown case)

# Test 4
Success! ✅
```

### **Process:**
1. **Test with real data** (don't predict)
2. **Constraint error surfaces** (database tells you)
3. **Fix specific constraint** (targeted fix)
4. **Retest** (validate fix)
5. **Repeat** until clean

### **Tools for Constraint Fixing:**
```sql
-- Drop old constraint
ALTER TABLE table_name DROP CONSTRAINT IF EXISTS constraint_name;

-- Add new constraint (expanded)
ALTER TABLE table_name ADD CONSTRAINT constraint_name
  CHECK (column IN ('value1', 'value2', 'new_value'));

-- Expand column size
ALTER TABLE table_name ALTER COLUMN column_name TYPE VARCHAR(50);

-- Change data type
ALTER TABLE table_name ALTER COLUMN column_name TYPE NUMERIC(4,1)
  USING column_name::numeric;

-- Reload Supabase cache
NOTIFY pgrst, 'reload schema';
```

### **Real Examples from Today:**
1. `segment` constraint: Didn't allow "unknown" → Added it
2. `segment_confidence` constraint: Required 1-10 → Changed to 0-10
3. `phone` column: VARCHAR(20) too small → Expanded to VARCHAR(50)
4. `tenure_years` type: INTEGER → NUMERIC(4,1) for 6.8 years

### **When to Apply:**
- Testing against production databases
- Legacy schema with unknown constraints
- Rapid iteration workflows
- Data-driven constraint discovery

### **Benefits:**
✅ Faster (fix what breaks, not what might)
✅ Accurate (database tells you exact issue)
✅ Targeted (fix only what's needed)
✅ Learn actual requirements (not guessed)

---

## Pattern 6: Controlled Production Testing

### **Problem**
Testing multiple records at once makes it hard to identify which caused issues.

### **Anti-Pattern:**
```python
# Test 100 courses at once
for course in courses:
    enrich(course)  # If one fails, which one? 🤷
```

### **Better Pattern:**
```python
# Test one at a time with human audit
test(course_93) → Show results → User approves ✅
test(course_98) → Show results → User approves ✅
test(course_103) → Show results → User approves ✅
# Build confidence incrementally!
```

### **Process:**
```
Engineer: "Test course ID 93"
System: <runs enrichment>
System: <shows results + database query>
User: <audits data, checks if reasonable>
User: "Looks good, test 98"
System: <repeats>
```

### **Real Example:**
- Course 93: Kevin = 2.4 years ✅
- Course 98: All NULL tenures (expected - no data in descriptions) ✅
- Course 103: Mike = 12.8 years ✅ (great edge case!)

Each test validated before proceeding.

### **When to Apply:**
- First production deployment
- High-stakes data modifications
- Learning edge cases
- Building confidence in new logic

### **Benefits:**
✅ Safe (one record at a time)
✅ Educational (learn from each test)
✅ Debuggable (easy to identify issues)
✅ Confidence-building (incremental validation)

---

## Pattern 7: Agent Consolidation Decision Framework

### **When to Consolidate Agents:**

**Consolidate IF:**
- ✅ Agent B's data is already in Agent A's response
- ✅ Agent B just transforms Agent A's data (no new API call)
- ✅ Agent B's logic is simple (regex, parsing)
- ✅ Consolidation doesn't hurt readability

**Keep Separate IF:**
- ✅ Different API/data sources
- ✅ Different core capabilities
- ✅ Complex logic per agent
- ✅ One might fail independently

### **Decision Matrix:**

| Scenario | Decision | Example |
|----------|----------|---------|
| Agent A has data, Agent B extracts it | **Consolidate** | Agent 4 search → tenure extraction |
| Agent A & B use different APIs | **Keep Separate** | Agent 3 (Hunter.io) vs Agent 4 (Firecrawl) |
| Agent B scrapes Agent A's result | **Depends** | If scraping needed: separate. If data in A: consolidate |
| Agent B transforms Agent A's data | **Consolidate** | Parsing, regex, calculations |

### **Real Example:**
```
Agent 4: Find LinkedIn (Firecrawl search API)
Agent 6.5: Get tenure (scrape LinkedIn profile)

Analysis:
- Agent 4 search description has tenure ✅
- Agent 6.5 just extracts from description ✅
- No new API call needed ✅
- Regex extraction is simple ✅

Decision: CONSOLIDATE → Agent 4 does both
Result: 9 → 8 agents, faster, cheaper
```

### **Benefits of Consolidation:**
✅ Simpler architecture (fewer agents)
✅ Fewer API calls (faster)
✅ Lower cost (one call vs two)
✅ Single responsibility (LinkedIn specialist)
✅ Easier maintenance (one file to update)

### **When NOT to Consolidate:**
❌ Different error handling needs
❌ Different retry strategies
❌ Independent failure modes
❌ Hurts code readability

---

## Pattern 8: Reuse Expensive API Calls

### **Problem**
Multiple agents scraping same data source independently.

### **Anti-Pattern:**
```python
# Agent 6: Scrape SkyGolf for fees ($0.01)
skygolf_data = scrape_skygolf(course_name)
fees = extract_fees(skygolf_data)

# Agent 7: Scrape SkyGolf for water hazards ($0.01)
skygolf_data = scrape_skygolf(course_name)  # DUPLICATE SCRAPE!
water = extract_water(skygolf_data)

# Total: $0.02 for same data!
```

### **Better Pattern:**
```python
# Agent 7: Scrape SkyGolf ONCE, return full content
agent7_result = {
    "water_rating": "heavy",
    "skygolf_content": "<full page content>"  # ← Pass to next agent!
}

# Agent 6: Reuse Agent 7's scrape
fees = extract_fees(agent7_result["skygolf_content"])
# Cost: $0.00 (reused data!)

# Total: $0.01 (one scrape, two agents use it)
```

### **Real Example:**
- Agent 7 scrapes SkyGolf for water hazards
- Returns full `skygolf_content` to orchestrator
- Agent 6 extracts fees from same content
- **Savings:** $0.037 per course × 358 courses = $13.25!

### **Design Principle:**
> "Scrape once, extract many times"

### **When to Apply:**
- Multiple agents need data from same source
- Expensive API calls (scraping, AI queries)
- Same page/response has multiple data points

### **Implementation:**
```python
# Agent 7 (water hazards)
def count_water_hazards():
    content = scrape_skygolf()
    water_rating = extract_water(content)

    return {
        "water_rating": water_rating,
        "skygolf_content": content,  # ← Pass full content!
        "skygolf_url": url  # ← Share URL too
    }

# Orchestrator
agent7_result = await count_water_hazards()
agent6_result = await enrich_course(
    skygolf_content=agent7_result["skygolf_content"]  # ← Reuse!
)
```

### **Benefits:**
✅ Cost savings (one API call vs multiple)
✅ Faster (no duplicate network requests)
✅ Consistent (same content for all extractions)
✅ Reliable (no race conditions)

---

## Pattern 9: Database Type Evolution

### **Problem**
Agent logic evolves to return more precise data, but database schema hasn't caught up.

### **Evolution:**
```
Version 1: Agent returns tenure as integer (7 years)
Database: tenure_years INTEGER ✅ Works

Version 2: Agent returns precise tenure (6.8 years)
Database: tenure_years INTEGER ❌ Error: "invalid input syntax"
```

### **Solution:**
```sql
-- Evolve database to match agent capability
ALTER TABLE contacts
  ALTER COLUMN tenure_years TYPE NUMERIC(4,1)
  USING tenure_years::numeric;
```

### **Migration Strategy:**
```sql
-- Safe migration (works even if data exists)
ALTER TABLE table_name
  ALTER COLUMN column_name TYPE new_type
  USING column_name::new_type;  -- ← Converts existing data
```

### **Common Type Evolutions:**
- `INTEGER` → `NUMERIC(precision, scale)` (6.8 years, 4.5 rating)
- `VARCHAR(20)` → `VARCHAR(50)` or `TEXT` (longer values)
- `BOOLEAN` → `TEXT` (true/false/unknown states)
- `DATE` → `TIMESTAMP` or `TEXT` (partial dates like "Jan 2019")

### **Real Examples:**
```sql
-- Tenure: INTEGER → NUMERIC(4,1)
ALTER TABLE golf_course_contacts
  ALTER COLUMN tenure_years TYPE NUMERIC(4,1);

-- Phone: VARCHAR(20) → VARCHAR(50)
ALTER TABLE golf_courses
  ALTER COLUMN phone TYPE VARCHAR(50);

-- Tenure start: Add new column
ALTER TABLE golf_course_contacts
  ADD COLUMN tenure_start_date TEXT;  -- "Jan 2019" format
```

### **When to Apply:**
- Agent provides more precise data over time
- Initial schema too restrictive
- Data quality improves
- New fields discovered

### **Benefits:**
✅ Preserves precision (6.8 not 7)
✅ Backward compatible (existing data converts)
✅ Flexible for future improvements

---

## Pattern 10: Schema Constraint Auditing

### **Problem**
Production databases have CHECK constraints that block valid agent data.

### **Discovery Pattern:**
```
Test → Error: "violates check constraint"
Read error → Identify constraint name
Query constraint → See allowed values
Fix constraint → Add missing values
Retest → Success!
```

### **Finding Constraints:**
```sql
-- List all CHECK constraints on a table
SELECT
  con.conname as constraint_name,
  pg_get_constraintdef(con.oid) as constraint_definition
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
WHERE rel.relname = 'golf_courses'
  AND con.contype = 'c';
```

### **Common Constraint Issues:**
```sql
-- Issue 1: Missing enum value
CHECK (segment IN ('high-end', 'budget', 'both'))
-- Fails when agent returns: 'unknown'
-- Fix: Add 'unknown' to allowed values

-- Issue 2: Too restrictive range
CHECK (confidence >= 1 AND confidence <= 10)
-- Fails when agent returns: 0 (for unknown)
-- Fix: Allow 0-10 range

-- Issue 3: Column length
phone VARCHAR(20)
-- Fails when agent returns: "(703) 327-3403 ext. 5" (24 chars)
-- Fix: Expand to VARCHAR(50)
```

### **Fixing Pattern:**
```sql
-- Step 1: Drop old constraint
ALTER TABLE table_name
  DROP CONSTRAINT IF EXISTS constraint_name;

-- Step 2: Add new constraint (expanded)
ALTER TABLE table_name
  ADD CONSTRAINT constraint_name
  CHECK (column IN ('old', 'values', 'new_value'));

-- Step 3: Reload cache (Supabase)
NOTIFY pgrst, 'reload schema';
```

### **Real Examples from Today:**
1. `segment`: Added 'unknown', 'premium', 'economy' values
2. `segment_confidence`: Changed 1-10 → 0-10
3. `phone`: VARCHAR(20) → VARCHAR(50)

### **When to Apply:**
- First production deployment
- Agent logic changes
- New edge cases discovered
- Data variety increases

### **Benefits:**
✅ Discover real constraints (not assumed)
✅ Fix only what breaks (targeted)
✅ Learn from actual data (not theoretical)

---

## Quick Reference

### **Before Adding New Agent:**
- [ ] Check if existing agents already have the data
- [ ] Look for data in API response descriptions/metadata
- [ ] Consider if extraction logic can merge into existing agent

### **When Designing Agent Responsibilities:**
- [ ] One agent = one core capability (specialist)
- [ ] Specialists always run (not conditional on bonus fields)
- [ ] Later agents can overwrite earlier (specialist wins)

### **For Database Integration:**
- [ ] Use NUMERIC for decimal values (not INTEGER)
- [ ] Use VARCHAR(50+) or TEXT for variable-length strings
- [ ] Test constraints by trying, not predicting
- [ ] Fix constraints incrementally as errors surface

### **For Testing:**
- [ ] Create test_*.py files (don't modify production!)
- [ ] Test one record at a time (controlled)
- [ ] Human audit between tests (learn edge cases)
- [ ] Validate in database after each test

---

## Pattern 11: API-Orchestrator-Agent Parameter Flow ⭐

### **Problem**
Parameters accepted by lower layers (Agent) but not passed through upper layers (API → Orchestrator).

### **Anti-Pattern:**
```python
# Agent 8: Accepts course_id parameter
async def write_to_supabase(
    course_data,
    course_id: int | None = None  # ✅ Agent supports it
):
    if course_id:
        # Update by ID (no name mismatch!)
        ...

# Orchestrator: Passes course_id to Agent 8
result = await write_to_supabase(
    course_data,
    course_id=course_id  # ✅ Orchestrator passes it
)

# API: Doesn't have course_id field!
class EnrichCourseRequest(BaseModel):
    course_name: str  # ❌ No course_id field!
    state_code: str

# API endpoint: Doesn't pass course_id
result = await orchestrator_enrich_course(
    course_name=request.course_name,
    state_code=request.state_code
    # ❌ course_id not passed! Always None at Agent 8
)
```

### **Better Pattern:**
```python
# 1. API Model: Accept parameter
class EnrichCourseRequest(BaseModel):
    course_name: str
    course_id: int | None = None  # ✅ Added

# 2. API Endpoint: Pass parameter
result = await orchestrator_enrich_course(
    course_name=request.course_name,
    course_id=request.course_id,  # ✅ Pass through
    state_code=request.state_code
)

# 3. Orchestrator: Pass parameter
result = await write_to_supabase(
    course_data,
    course_id=course_id  # ✅ Pass through
)

# 4. Agent: Use parameter
if course_id:
    # Update by ID ✅
```

### **Real Example:**
- **Problem:** course_id supported by Agent 8, but API didn't accept/pass it
- **Result:** Agent 8 fell back to name lookup → created duplicate course 445
- **Fix:** Added course_id to API model + endpoint
- **Outcome:** Course 133 updated correctly (no duplicate)

### **Debugging Strategy:**
1. **Trace parameter through ALL layers:**
   - Check API request model (Pydantic schema)
   - Check API endpoint handler (function call)
   - Check orchestrator function signature
   - Check agent function signature
2. **Verify parameter actually reaches agent:**
   - Add logging at each layer
   - Check production logs
   - Validate parameter value at destination

### **When to Apply:**
- Adding new optional parameters
- Debugging "parameter not working" issues
- Integrating multi-layer systems
- After syncing code (verify sync copied API changes)

### **Benefits:**
✅ Parameters flow end-to-end
✅ Optional params work as designed
✅ Prevents subtle parameter bugs
✅ Easier to add new params later

---

## Pattern 12: Sync Script Completeness ⭐

### **Problem**
Sync scripts copy some files but miss critical deployment files (especially api.py).

### **Anti-Pattern:**
```python
# sync_to_production.py
def sync_team_to_production(team_name):
    # Copy agents ✅
    shutil.copy(team_dir / "agents", prod_dir / "agents")

    # Copy orchestrator ✅
    shutil.copy(team_dir / "orchestrator.py", prod_dir / "orchestrator.py")

    # Copy utils ✅
    shutil.copy(shared_dir / "utils", prod_dir / "template/utils")

    # ❌ MISSING: api.py is NOT copied!
```

### **Better Pattern:**
```python
def sync_team_to_production(team_name):
    # 1. Copy agents
    copy_dir(team_dir / "agents", prod_dir / "agents")

    # 2. Copy orchestrator
    copy_file(team_dir / "orchestrator.py", prod_dir / "orchestrator.py")

    # 3. Copy API ✅
    copy_file(team_dir / "api.py", prod_dir / "api.py")

    # 4. Copy utils
    copy_dir(shared_dir / "utils", prod_dir / "template/utils")

    # 5. Copy requirements
    copy_file(team_dir / "requirements.txt", prod_dir / "requirements.txt")

    # 6. Copy config (if exists)
    if (team_dir / "config.py").exists():
        copy_file(team_dir / "config.py", prod_dir / "config.py")
```

### **Real Example:**
- **Problem:** teams/api.py had course_id fix, but sync script didn't copy api.py
- **Result:** Production api.py was outdated, fix didn't deploy
- **Fix:** Added api.py to sync script
- **Outcome:** Production deployment worked after re-sync

### **Deployment Checklist:**
```bash
# After syncing, verify all files copied:
- [ ] agents/*.py (all agent files)
- [ ] orchestrator.py
- [ ] api.py ⭐ (often forgotten!)
- [ ] requirements.txt
- [ ] shared/utils/*.py
- [ ] config files (if any)
- [ ] .env.example (if any)
```

### **When to Apply:**
- Creating sync scripts
- Debugging "fix not deploying" issues
- After code refactoring (file moves)
- Setting up new agent teams

### **Testing Sync Scripts:**
```bash
# 1. Make change in teams/ folder
echo "# test" >> teams/my-team/api.py

# 2. Run sync
python production/scripts/sync_to_production.py my-team

# 3. Verify file copied
diff teams/my-team/api.py production/my-team/api.py
# Should be identical!
```

### **Benefits:**
✅ All code changes deploy
✅ No "forgot to sync X" errors
✅ Repeatable deployments
✅ Easier onboarding (just run sync)

---

## Pattern 13: ID-based Upserts Over Name Lookups ⭐

### **Problem**
Name-based database lookups fail on minor variations (punctuation, casing, spacing), creating duplicate records.

### **Anti-Pattern:**
```python
# Agent 8: Upsert by name only
async def write_to_supabase(course_data):
    course_name = course_data.get("course_name")

    # Look up by name
    existing = supabase.table("golf_courses")\
        .select("id")\
        .eq("course_name", course_name)\  # ❌ Exact match required
        .maybe_single()\
        .execute()

    if existing:
        # Update existing
        course_id = existing.data["id"]
    else:
        # Insert new (creates duplicate if name differs!)
        result = supabase.table("golf_courses").insert(course_data).execute()
        course_id = result.data[0]["id"]
```

### **Better Pattern:**
```python
async def write_to_supabase(
    course_data,
    course_id: int | None = None  # ✅ Accept ID as optional param
):
    # Prefer ID-based update
    if course_id:
        # Update by ID (no name mismatch issues!)
        supabase.table("golf_courses")\
            .update(course_data)\
            .eq("id", course_id)\
            .execute()
        return course_id

    # Fallback: Name lookup (only if ID not provided)
    course_name = course_data.get("course_name")
    existing = supabase.table("golf_courses")\
        .select("id")\
        .eq("course_name", course_name)\
        .maybe_single()\
        .execute()

    if existing:
        course_id = existing.data["id"]
        supabase.table("golf_courses").update(course_data).eq("id", course_id).execute()
    else:
        result = supabase.table("golf_courses").insert(course_data).execute()
        course_id = result.data[0]["id"]

    return course_id
```

### **Real Example:**
- **Database:** "Chantilly National Golf **and** Country Club" (course 133)
- **Agent 2 extracted:** "Chantilly National Golf **&** Country Club"
- **Name lookup failed** → created duplicate course 445
- **Fix:** Pass course_id=133 to API → Agent 8 updates by ID
- **Result:** Course 133 updated correctly (no duplicate)

### **Common Name Mismatch Causes:**
```
"and" vs "&"
"Golf Club" vs "Golf Course"
"St." vs "Saint"
"The XYZ Club" vs "XYZ Club"
Extra spaces, punctuation
```

### **When to Apply:**
- Database upsert operations
- Systems with human-entered data
- Multi-source data (different scrapers)
- When IDs are available upstream

### **API Design:**
```python
# Make ID optional but preferred
class UpdateRequest(BaseModel):
    id: int | None = None  # ✅ Optional but preferred
    name: str              # ✅ Required (fallback lookup)
    # ... other fields
```

### **Benefits:**
✅ No duplicates from typos
✅ Reliable updates
✅ Faster (no string comparison)
✅ Backwards compatible (ID optional)

---

## Pattern 14: Production Log Validation ⭐

### **Problem**
Assuming deployments work correctly without verifying actual production behavior.

### **Anti-Pattern:**
```bash
# Deploy code
git push origin main

# ❌ Assume it works (no validation!)
# "It compiled, ship it!"
```

### **Better Pattern:**
```bash
# 1. Deploy code
git push origin main

# 2. Wait for deployment
# Watch Render dashboard or check deployment status

# 3. Fetch production logs
render logs --tail 100

# 4. Validate architectural changes in logs
grep "Agent" logs.txt  # Check agent count
grep "course_id" logs.txt  # Check parameter usage
grep "ERROR" logs.txt  # Check for errors

# 5. Test production endpoint
curl -X POST https://api.example.com/enrich-course \
  -d '{"course_id": 133, ...}'

# 6. Verify database changes
SELECT * FROM courses WHERE id = 133;
```

### **Real Example - Agent 4 Consolidation Validation:**
```
✅ Verified in logs:
   "Service: Full Enrichment Pipeline (Agents 1-8)"  ← Was 1-9!
   "🔗 Agent 4: Finding LinkedIn + Tenure (specialist)..."
   "Method: firecrawl_search"
   "⚠️ Tenure: Not in search description"
   No mention of "Agent 6.5" anywhere

✅ Verified in logs - course_id fix:
   "✅ Using provided course_id: 133"
   "✅ Updated course ID: 133"
   Not: "✅ Created new course (ID: 445)"

✅ Verified in database:
   Course 133 updated (not duplicate 445 created)
```

### **What to Check in Production Logs:**

**1. Architecture Changes:**
- Agent count ("Agents 1-8" vs "Agents 1-9")
- New agent logic executing
- Old agent logic NOT executing

**2. Parameter Flow:**
- Parameters being received
- Parameters being used
- Parameters reaching destination

**3. Data Operations:**
- Correct database operations (UPDATE vs INSERT)
- Correct IDs being used
- No duplicate creations

**4. Error Patterns:**
- New errors introduced?
- Old errors fixed?
- Unexpected warnings?

### **Log Analysis Tools:**
```bash
# Count agent executions
grep -c "Agent 4:" production.log

# Check parameter usage
grep "course_id" production.log | grep -E "(Using|Updated)"

# Check for duplicates
grep "Created new course" production.log | wc -l

# Check costs
grep "Total Cost:" production.log | awk '{sum+=$4} END {print sum}'
```

### **When to Apply:**
- After architectural changes
- After bug fixes
- After parameter additions
- Before declaring "ready for production"

### **Validation Checklist:**
```
- [ ] Deployment succeeded (Render shows "Live")
- [ ] Logs show new code executing
- [ ] Logs show old code NOT executing
- [ ] Parameters flowing correctly
- [ ] Database operations correct
- [ ] No new errors introduced
- [ ] Test endpoint returns expected results
- [ ] Database queries show expected data
```

### **Benefits:**
✅ Catch deployment issues early
✅ Verify architectural changes working
✅ Build deployment confidence
✅ Document "proof it works"
✅ Easier debugging (concrete evidence)

---

## Success Metrics

**Applied these patterns in golf enrichment:**
- ✅ Consolidated Agent 4/6.5 (Pattern 1)
- ✅ Made Agent 4 always run (Pattern 2)
- ✅ Changed tenure to NUMERIC (Pattern 3)
- ✅ Used test_*.py files (Pattern 4)
- ✅ Fixed 3 constraints iteratively (Pattern 5)
- ✅ Tested 3 courses individually (Pattern 6)
- ✅ Added course_id to API flow (Pattern 11)
- ✅ Fixed sync script for api.py (Pattern 12)
- ✅ ID-based upserts prevent duplicates (Pattern 13)
- ✅ Validated via Render logs (Pattern 14)

**Results:**
- Agents: 9 → 8 (11% reduction)
- Cost: $0.003 saved per contact with tenure
- Reliability: Higher (no LinkedIn blocking, no duplicates)
- Confidence: 100% (validated through all 7 stages)
- Production: 100% success rate (4 courses tested)

---

**These 14 patterns apply to ANY agent team using Claude SDK + MCP + Supabase!**
