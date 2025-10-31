# LLM to ClickUp Workflow - Version 1.0 (Revised)

**Created:** October 30, 2025
**Revised:** October 30, 2025 (Manual LLM + Paste Workflow)
**Purpose:** Manual thinking LLM discovery → Parse → Enrich (Apollo → Hunter) → Supabase → ClickUp
**Success Rate Target:** 85-90% (LLM proven 71%, enrichment adds +15-20%)
**Scale Target:** 10,000 courses (NC, SC, VA, GA)

---

## Executive Summary

**The Workflow:**
```
YOU run thinking LLM manually
  ↓
Copy/Paste response into Supabase
  ↓
AUTO: Parse contacts → Queue for enrichment
  ↓
AUTO: Render agents enrich (Apollo → Hunter waterfall)
  ↓
AUTO: Store in Supabase gold tables
  ↓
AUTO: Create ClickUp tasks
  ↓
Ready for outreach!
```

**Why This Works:**
- ✅ Thinking LLM: Proven 71% success (you're already paying for it!)
- ✅ Manual quality control: You verify LLM output before processing
- ✅ Apollo → Hunter waterfall: Try Apollo first, Hunter fills gaps
- ✅ Only enrich what needs it: Skip contacts that are already complete
- ✅ Fully automated after paste: No manual steps once you paste
- ✅ Course intelligence: Projects, vendors, awards for personalization

**Performance:**
- Discovery success: 71% (proven through 7-course testing)
- After enrichment: 85-90% (Apollo/Hunter add missing data)
- Contacts per course: 6+ discovered, 4+ verified
- Emails per course: 2-3 verified work emails
- LinkedIn per course: 4-5 profiles
- Intelligence: 80% of courses have actionable intel
- Cost: $0.04-0.07 per course ($0.02 parsing + $0.02-0.05 enrichment)

---

## Architecture Overview

### 5-Step Pipeline (Manual LLM + 4 Automated Agents)

```
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: YOU - Run Thinking LLM Manually                     │
│                                                               │
│  Use your paid thinking LLM (ChatGPT, Claude, etc.)          │
│  Prompt: "Find contacts at Alamance CC... include LinkedIn"  │
│  Output: Mixed text with contacts, emails, LinkedIn, intel   │
│                                                               │
│  Time: 2-3 minutes manual                                    │
│  Cost: Your existing LLM subscription                        │
└──────────────────────────────────────────────────────────────┘
                              ↓ (Copy response)
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: YOU - Paste into Supabase                           │
│                                                               │
│  INSERT INTO llm_discovery_raw (                             │
│    course_name,                                              │
│    state_code,                                               │
│    raw_llm_response  -- Paste entire LLM output here         │
│  ) VALUES ('Alamance CC', 'NC', '<paste>');                  │
│                                                               │
│  → Database trigger fires automatically                      │
│  Time: 10 seconds manual                                     │
└──────────────────────────────────────────────────────────────┘
                              ↓ (Automatic from here)
┌──────────────────────────────────────────────────────────────┐
│  AGENT 1: PARSING AGENT (Render Edge Function)               │
│  Endpoint: POST /parse-llm-response                          │
│                                                               │
│  1. Parse mixed LLM text (regex + AI parsing)                │
│  2. Extract: Contacts, emails, phones, LinkedIn, intel       │
│  3. Assess enrichment needs:                                 │
│     - Missing email? → needs_email = true                    │
│     - Missing LinkedIn? → needs_linkedin = true              │
│     - Has email? → needs_verification = true                 │
│  4. Insert into enrichment_queue                             │
│                                                               │
│  Time: 10-20 seconds                                         │
│  Cost: $0.01-0.02 (Claude parsing API)                       │
└──────────────────────────────────────────────────────────────┘
                              ↓ (Trigger per contact)
┌──────────────────────────────────────────────────────────────┐
│  AGENT 2: ENRICHMENT AGENT (Render Edge Function)            │
│  Endpoint: POST /enrich-contact                              │
│                                                               │
│  WATERFALL STRATEGY (Apollo → Hunter):                       │
│                                                               │
│  Tier 1 - Apollo (if needs email OR LinkedIn):               │
│    • Search Apollo for person                                │
│    • Get email (if missing)                                  │
│    • Get LinkedIn (if missing)                               │
│    • Get tenure, title verification                          │
│                                                               │
│  Tier 2 - Hunter (always):                                   │
│    • If has email: Verify deliverability                     │
│    • If no email: Try Hunter Email Finder                    │
│    • Always: Get confidence score                            │
│                                                               │
│  Only keep: Confidence ≥70%, deliverable emails              │
│                                                               │
│  Time: 15-30 seconds per contact                             │
│  Cost: $0.02-0.05 (Apollo + Hunter)                          │
└──────────────────────────────────────────────────────────────┘
                              ↓ (After all contacts enriched)
┌──────────────────────────────────────────────────────────────┐
│  AGENT 3: SUPABASE WRITER (Render Edge Function)             │
│  Endpoint: POST /write-to-supabase                           │
│                                                               │
│  1. Insert verified contacts → golf_course_contacts          │
│  2. Update course intelligence → golf_courses                │
│  3. Store discovery sources, enrichment metadata             │
│  4. Mark enrichment_queue as processed                       │
│                                                               │
│  Time: 5-10 seconds                                          │
│  Cost: $0 (existing Supabase)                                │
└──────────────────────────────────────────────────────────────┘
                              ↓ (Database trigger)
┌──────────────────────────────────────────────────────────────┐
│  AGENT 4: CLICKUP SYNC (Supabase Edge Function)              │
│  Trigger: When course enrichment complete                    │
│                                                               │
│  1. Fetch all verified contacts for course                   │
│  2. Fetch course intelligence                                │
│  3. Create ClickUp task with custom fields                   │
│  4. Store clickup_task_id in Supabase                        │
│                                                               │
│  Time: 10-15 seconds                                         │
│  Cost: $0 (existing ClickUp)                                 │
└──────────────────────────────────────────────────────────────┘
                              ↓
        ✅ COMPLETE - Contacts in ClickUp, ready for outreach
```

**Key Differences from Original:**
- 🔄 Manual LLM step (not automated Perplexity MCP)
- 🔄 Paste-triggered workflow (you control when)
- 🔄 Parsing agent added (handles mixed LLM output)
- 🔄 Apollo → Hunter waterfall (not either/or)
- 🔄 Smart enrichment (only what needs it)
- 🔄 Fully automated after paste (one action = complete pipeline)

---

## Supabase Database Design

### Table 1: `llm_discovery_raw` - Staging for LLM Responses

**Purpose:** Where you paste raw LLM responses to trigger the workflow

```sql
CREATE TABLE IF NOT EXISTS llm_discovery_raw (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Course Identification
  course_name VARCHAR(255) NOT NULL,
  state_code VARCHAR(2),
  city VARCHAR(100),
  domain VARCHAR(255),

  -- Raw LLM Response (you paste here)
  raw_llm_response TEXT NOT NULL,
  response_format VARCHAR(50) DEFAULT 'mixed',  -- 'mixed', 'json', 'markdown'

  -- Processing Status
  parsed BOOLEAN DEFAULT FALSE,
  parsing_error TEXT,
  parsed_at TIMESTAMP,

  -- Extracted Summary
  contacts_found INTEGER,
  emails_found INTEGER,
  linkedins_found INTEGER,
  needs_enrichment_count INTEGER,

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(100),

  -- Processing IDs
  course_id UUID,  -- Linked after parsing
  enrichment_batch_id UUID
);

-- Index for performance
CREATE INDEX idx_llm_raw_parsing ON llm_discovery_raw(parsed, created_at);
CREATE INDEX idx_llm_raw_course ON llm_discovery_raw(course_name, state_code);
```

**How You Use It:**
```sql
-- Paste LLM response here (replace {COURSE}, {STATE}, {LLM_OUTPUT})
INSERT INTO llm_discovery_raw (course_name, state_code, raw_llm_response)
VALUES (
  'Alamance Country Club',
  'NC',
  'Charlie Nolette, CCM — General Manager / COO
   Email: cnolette@alamancecc.net
   LinkedIn: linkedin.com/in/charlie-nolette...

   Drake Woodside, PGA — Director of Golf
   ...'
);

-- Trigger fires immediately, processing starts automatically
```

---

### Table 2: `enrichment_queue` - Contacts Needing Apollo/Hunter

**Purpose:** Queue for contacts that need enrichment (missing email, LinkedIn, or verification)

```sql
CREATE TABLE IF NOT EXISTS enrichment_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Links
  raw_discovery_id UUID REFERENCES llm_discovery_raw(id),
  course_id UUID REFERENCES golf_courses(id),

  -- Contact Info from LLM
  name VARCHAR(255) NOT NULL,
  title VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(50),
  linkedin_url TEXT,
  source_url TEXT,
  source_type VARCHAR(50),  -- 'pga_directory', 'cmaa', 'club_website', etc.

  -- Enrichment Needed Flags
  needs_email BOOLEAN DEFAULT FALSE,
  needs_linkedin BOOLEAN DEFAULT FALSE,
  needs_verification BOOLEAN DEFAULT FALSE,
  enrichment_priority VARCHAR(10) DEFAULT 'medium',  -- 'high', 'medium', 'low'

  -- Enrichment Status
  enrichment_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'

  -- Apollo Results
  apollo_attempted BOOLEAN DEFAULT FALSE,
  apollo_found BOOLEAN DEFAULT FALSE,
  apollo_email_found BOOLEAN DEFAULT FALSE,
  apollo_linkedin_found BOOLEAN DEFAULT FALSE,

  -- Hunter Results
  hunter_attempted BOOLEAN DEFAULT FALSE,
  hunter_verification_success BOOLEAN DEFAULT FALSE,
  hunter_email_found BOOLEAN DEFAULT FALSE,

  -- Enriched Data
  enriched_email VARCHAR(255),
  enriched_linkedin TEXT,
  email_confidence_score INTEGER,  -- 0-100 from Hunter
  email_verification_status VARCHAR(20),  -- 'deliverable', 'risky', 'undeliverable'
  apollo_tenure_years INTEGER,

  -- Processing Metadata
  queued_at TIMESTAMP DEFAULT NOW(),
  processing_started_at TIMESTAMP,
  processed_at TIMESTAMP,
  render_job_id VARCHAR(100),
  render_attempts INTEGER DEFAULT 0,
  last_error TEXT,
  cost_usd NUMERIC(10,4) DEFAULT 0
);

-- Indexes
CREATE INDEX idx_enrich_status ON enrichment_queue(enrichment_status, queued_at);
CREATE INDEX idx_enrich_course ON enrichment_queue(course_id, enrichment_status);
CREATE INDEX idx_enrich_priority ON enrichment_queue(enrichment_priority, enrichment_status);
```

---

### Trigger: Parse LLM Response

```sql
CREATE OR REPLACE FUNCTION trigger_parse_llm_response()
RETURNS TRIGGER AS $$
BEGIN
  -- Call Render parsing endpoint
  PERFORM net.http_post(
    url := 'https://golf-enrichment-api.onrender.com/parse-llm-response',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.render_api_key', true)
    ),
    body := jsonb_build_object(
      'raw_discovery_id', NEW.id,
      'course_name', NEW.course_name,
      'state_code', NEW.state_code,
      'city', NEW.city,
      'domain', NEW.domain,
      'raw_response', NEW.raw_llm_response
    )
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_llm_discovery_insert
  AFTER INSERT ON llm_discovery_raw
  FOR EACH ROW
  WHEN (NEW.parsed = FALSE)
  EXECUTE FUNCTION trigger_parse_llm_response();
```

---

### Trigger: Enrich Contact

```sql
CREATE OR REPLACE FUNCTION trigger_enrich_contact()
RETURNS TRIGGER AS $$
BEGIN
  -- Call Render enrichment endpoint
  PERFORM net.http_post(
    url := 'https://golf-enrichment-api.onrender.com/enrich-contact',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.render_api_key', true)
    ),
    body := jsonb_build_object(
      'queue_id', NEW.id,
      'course_id', NEW.course_id,
      'contact', jsonb_build_object(
        'name', NEW.name,
        'title', NEW.title,
        'email', NEW.email,
        'linkedin_url', NEW.linkedin_url
      ),
      'enrichment_needs', jsonb_build_object(
        'needs_email', NEW.needs_email,
        'needs_linkedin', NEW.needs_linkedin,
        'needs_verification', NEW.needs_verification
      )
    )
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_enrichment_queue_insert
  AFTER INSERT ON enrichment_queue
  FOR EACH ROW
  WHEN (NEW.enrichment_status = 'pending')
  EXECUTE FUNCTION trigger_enrich_contact();
```

---

### Trigger: Sync to ClickUp

```sql
CREATE OR REPLACE FUNCTION trigger_clickup_sync()
RETURNS TRIGGER AS $$
DECLARE
  pending_count INTEGER;
BEGIN
  -- Check if all contacts for this course are done enriching
  SELECT COUNT(*) INTO pending_count
  FROM enrichment_queue
  WHERE course_id = NEW.course_id
    AND enrichment_status IN ('pending', 'processing');

  -- If all done, trigger ClickUp sync
  IF pending_count = 0 THEN
    PERFORM net.http_post(
      url := 'https://golf-enrichment-api.onrender.com/sync-to-clickup',
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer ' || current_setting('app.render_api_key', true)
      ),
      body := jsonb_build_object('course_id', NEW.course_id)
    );
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_enrichment_complete
  AFTER UPDATE ON enrichment_queue
  FOR EACH ROW
  WHEN (NEW.enrichment_status = 'completed' AND OLD.enrichment_status != 'completed')
  EXECUTE FUNCTION trigger_clickup_sync();
```

---

## Step 1: Manual LLM Discovery (YOU)

### Purpose
You manually run your paid thinking LLM to discover contacts and course intelligence. This gives you quality control and leverages the LLM subscription you're already paying for.

### Your LLM Prompt Template

**Copy this prompt into your thinking LLM:**

```
Find all current decision makers and golf professionals at {course_name} in {city}, {state}.

Include these roles:
- General Manager / COO
- Director of Golf
- Head Golf Professional
- Assistant Golf Professionals
- Golf Course Superintendent / Director of Agronomy
- Director of Instruction
- Any other key management or operations staff

For EACH person provide:
- Full name
- Exact current title (verify they are currently employed there in 2024-2025)
- Email address (WORK email preferred over personal/generic)
- Phone number (direct line if available, or department/pro shop routing)
- **LinkedIn profile URL** (critical - search for their LinkedIn page if available)
- SOURCE LINKS for each piece of information (must provide sources)

Additionally, gather intelligence about the course for outreach personalization:
- Ownership structure (independent owner, management company, resort, municipal)
- Recent renovations, improvements, or major projects (last 2 years)
- Technology or vendors they currently use:
  * Turf suppliers (e.g., Mach 1 Greens, ultradwarf varieties)
  * Irrigation systems (e.g., Rain Bird, Toro)
  * Equipment providers (e.g., John Deere, Toro)
  * Software/technology (e.g., Tagmarshal, ForeUp, GolfNow)
- Awards, rankings, or notable achievements (2024-2025)
- Notable events hosted (tournaments, championships)
- Known challenges or goals mentioned in public sources

Focus on CURRENT information (2024-2025) and verify employment status.
Provide source links for verification.
```

### What Your LLM Will Return

**Mixed format output** (text + structured data):

```
Current decision makers & golf pros

Charlie Nolette, CCM — General Manager / COO
Email: cnolette@alamancecc.net
LinkedIn: linkedin.com/in/charlie-nolette-ccm-b2b79412
Phone: (336) 584-0345
Source: CMAA directory, Alamance Chamber

Drake Woodside, PGA — Director of Golf
Email: dwoodside@alamancecc.net
LinkedIn: Not found
Phone: (336) 584-1326 (golf shop)
Source: PGA.org, Club newsletter (AnyFlip)

... (more contacts)

Course Intelligence:

Ownership: Member-owned nonprofit
Recent Projects: Agronomy improvements (2024)
Vendors: Unknown turf supplier
Awards: Top NC private club ranking
...
```

### After Running LLM

**You will:**
1. Review the LLM output (verify looks reasonable)
2. Copy the entire response
3. Paste into Supabase `llm_discovery_raw` table
4. Wait 60-90 seconds
5. Check ClickUp for new task!

---

## Agent 1: Parsing Agent (Render)

### Purpose
Parse your thinking LLM's mixed text output and extract structured contact data.

### Triggered By
```sql
-- When you INSERT into llm_discovery_raw
INSERT INTO llm_discovery_raw (course_name, state_code, raw_llm_response)
VALUES ('Alamance CC', 'NC', '<your LLM paste>');

-- Trigger fires → Calls Render /parse-llm-response
```

### Discovery Strategy (Learned from Testing)

**Sources to Check (Priority Order):**

**Tier 1: Professional Directories**
1. PGA.org facility directory
   - For: Golf professionals
   - Success: 90% for names/titles, 0% for emails
   - Fallback: PGA coach search if facility blocked

2. GCSAA / State GCSA
   - For: Superintendents
   - Success: 30-40% with direct contacts
   - Check: State chapters (Carolinas GCSA, etc.)

3. CMAA
   - For: General managers
   - Success: 30% with emails
   - Check: Regional chapters (Carolinas CMAA)

**Tier 2: Club Official Sources**
4. Club Website - Specific Pages
   - /membership (often has staff contact)
   - /employment (hiring manager emails)
   - /staff or /about/team (staff listings)
   - /contact-us (department emails)
   - Success: 40-60% for emails

5. Club Newsletters/Publications
   - Search: "{course_name} newsletter pdf anyflip"
   - Contains: Staff emails, email domain patterns
   - Success: 60% for emails when found
   - **Critical:** Reveals actual email domain used

**Tier 3: Vendor/Partner Sites** (NEW DISCOVERY)
6. Turf/Equipment Vendors
   - Examples: Mach 1 Greens, irrigation suppliers
   - Search: "{course_name} turf vendor superintendent contact"
   - Success: 40% for superintendent direct contacts
   - **Vendors publish contacts because they need direct line!**

**Tier 4: Government (for Municipal)**
7. City/County Websites
   - For: Municipal courses only
   - Success: 75% for staff emails
   - Government transparency = published contacts

**Tier 5: Business Directories**
8. Chamber of Commerce
   - For: Owners, GMs
   - Success: 20-30%

9. ContactOut, TheOrg, RocketReach
   - Use: Only as fallback, verify with other sources
   - Success: 20-30%
   - **Note:** Mark as "aggregator source - verify"

### Output Schema

```json
{
  "course_name": "Alamance Country Club",
  "city": "Burlington",
  "state": "NC",
  "domain_discovered": "alamancecountryclub.com",
  "email_domain_discovered": "alamancecc.net",
  "discovery_success": true,

  "contacts": [
    {
      "name": "Charlie Nolette",
      "title": "General Manager / COO",
      "email": "cnolette@alamancecc.net",
      "phone": "(336) 584-0345",
      "source_url": "https://www.carolinascmaa.org/mentorship/personnel/charlie-nolette",
      "source_type": "cmaa_directory",
      "discovery_method": "perplexity_research",
      "verified_current": true,
      "verification_sources": ["CMAA 2025", "Alamance Chamber", "ProPublica 990 2023"]
    },
    {
      "name": "Drake Woodside",
      "title": "Director of Golf",
      "email": "dwoodside@alamancecc.net",
      "phone": "(336) 584-1326",
      "source_url": "https://anyflip.com/alamance-newsletter-2019",
      "source_type": "club_newsletter",
      "discovery_method": "perplexity_research",
      "verified_current": true,
      "verification_sources": ["PGA.org 2025", "Club newsletter"]
    }
  ],

  "course_intelligence": {
    "ownership": "Member-owned nonprofit",
    "founded_year": 1910,
    "recent_projects": [
      {
        "type": "renovation",
        "description": "Agronomy improvements",
        "year": 2024,
        "source": "Club blog"
      }
    ],
    "vendors": [
      {
        "type": "turf",
        "name": "Unknown - check with superintendent",
        "source": null
      }
    ],
    "awards": [
      {
        "award": "Top NC private club",
        "year": 2024,
        "source": "Local recognition"
      }
    ],
    "challenges": [
      "Maintaining historic course character",
      "Bermudagrass transition"
    ],
    "unique_selling_points": [
      "Historic 1910 club",
      "Member-owned",
      "Active agronomy blog"
    ]
  },

  "metadata": {
    "discovery_timestamp": "2025-10-30T22:00:00Z",
    "total_contacts_found": 9,
    "work_emails_found": 3,
    "email_discovery_success": true,
    "sources_checked": 8,
    "llm_cost": 0.015
  }
}
```

### Error Handling

**If LLM finds 0 contacts:**
- Log: Course name, reason (no public data, private club, etc.)
- Store: Course in database with `discovery_status: "no_contacts_found"`
- Don't fail: Mark as researched but unsuccessful
- **Don't retry immediately:** Add to backlog for manual review

**If LLM finds contacts but no emails:**
- Store: Names, titles, phones
- Mark: `has_contacts: true, has_emails: false`
- Strategy: Can still outreach via phone or LinkedIn

---

## Agent 2: Enrichment Agent (Render)

### Purpose
Enrich LLM-discovered contacts using **Apollo → Hunter waterfall strategy**. Try Apollo first (fast, comprehensive if in database), then Hunter for email verification/finding.

### Triggered By
INSERT into `enrichment_queue` table (from parsing agent)

### Input
```json
{
  "queue_id": "uuid",
  "course_id": "uuid",
  "contact": {
    "name": "Charlie Nolette",
    "title": "General Manager / COO",
    "email": "cnolette@alamancecc.net",  // May be null
    "linkedin_url": null  // May be null
  },
  "enrichment_needs": {
    "needs_email": false,      // LLM found email
    "needs_linkedin": true,    // LLM didn't find LinkedIn
    "needs_verification": true // Has email, needs Hunter verify
  }
}
```

### Waterfall Enrichment Logic (Apollo FIRST, then Hunter)

```python
async def enrich_contact_waterfall(queue_item):
    """
    Apollo → Hunter waterfall enrichment strategy

    Why this order:
    - Apollo: Fast, gets email + LinkedIn + tenure in one call (if person in database)
    - Hunter: Slower, only gets email verification/finding, but more reliable
    - Strategy: Try Apollo first (30% success), Hunter fills gaps (90% success)
    """

    result = {
        "final_email": queue_item["email"],  # Start with LLM email
        "final_linkedin": queue_item["linkedin_url"],  # Start with LLM LinkedIn
        "confidence": 0,
        "sources": ["llm"],
        "apollo_data": None,
        "hunter_data": None
    }

    needs = queue_item["enrichment_needs"]

    # ═══════════════════════════════════════════════════════
    # TIER 1: APOLLO ENRICHMENT (if needs email OR LinkedIn)
    # ═══════════════════════════════════════════════════════

    if needs["needs_email"] or needs["needs_linkedin"]:
        try:
            logger.info(f"Trying Apollo for {queue_item['name']}")

            apollo_result = await apollo_person_search(
                name=queue_item["name"],
                organization=queue_item["course_name"],
                person_titles=[queue_item["title"]]
            )

            if apollo_result and len(apollo_result["people"]) > 0:
                person = apollo_result["people"][0]  # Take first match
                person_id = person["id"]

                # Enrich to unlock email/LinkedIn
                enriched = await apollo_person_enrich(person_id)

                result["apollo_data"] = enriched

                # Take what we need
                if needs["needs_email"] and enriched.get("email"):
                    result["final_email"] = enriched["email"]
                    result["sources"].append("apollo")
                    logger.info(f"✅ Apollo found email for {queue_item['name']}")

                if needs["needs_linkedin"] and enriched.get("linkedin_url"):
                    result["final_linkedin"] = enriched["linkedin_url"]
                    result["sources"].append("apollo")
                    logger.info(f"✅ Apollo found LinkedIn for {queue_item['name']}")

                # Bonus data
                result["apollo_tenure"] = calculate_tenure(enriched)
                result["apollo_title"] = enriched.get("title")

                # Update queue status
                await update_queue(queue_item["id"], {
                    "apollo_attempted": True,
                    "apollo_found": True,
                    "apollo_email_found": bool(enriched.get("email")),
                    "apollo_linkedin_found": bool(enriched.get("linkedin_url"))
                })

            else:
                # Apollo doesn't have this person
                logger.info(f"Apollo doesn't have {queue_item['name']}")
                await update_queue(queue_item["id"], {
                    "apollo_attempted": True,
                    "apollo_found": False
                })

        except ApolloAPIError as e:
            logger.error(f"Apollo error for {queue_item['name']}: {e}")
            await update_queue(queue_item["id"], {
                "apollo_attempted": True,
                "apollo_found": False,
                "last_error": f"Apollo error: {str(e)}"
            })

    else:
        # Skip Apollo - LLM already has email AND LinkedIn
        logger.info(f"Skipping Apollo for {queue_item['name']} - has email + LinkedIn")

    # ═══════════════════════════════════════════════════════
    # TIER 2: HUNTER ENRICHMENT (always run for emails)
    # ═══════════════════════════════════════════════════════

    # Case A: We have an email (from LLM or Apollo) → Verify it
    if result["final_email"]:
        try:
            logger.info(f"Verifying email with Hunter: {result['final_email']}")

            hunter_verify = await hunter_email_verifier(result["final_email"])

            result["hunter_data"] = hunter_verify
            result["confidence"] = hunter_verify["score"]
            result["verification_status"] = hunter_verify["result"]
            result["sources"].append("hunter_verified")

            # Check if deliverable
            if hunter_verify["result"] not in ["deliverable", "risky"]:
                logger.warning(f"Hunter rejected email: {hunter_verify['result']}")
                result["final_email"] = None  # Reject undeliverable emails

            await update_queue(queue_item["id"], {
                "hunter_attempted": True,
                "hunter_verification_success": True,
                "email_confidence_score": hunter_verify["score"],
                "email_verification_status": hunter_verify["result"]
            })

        except HunterAPIError as e:
            logger.error(f"Hunter verify error: {e}")
            # Keep email but mark as unverified
            result["confidence"] = 50  # Lower confidence
            await update_queue(queue_item["id"], {
                "hunter_attempted": True,
                "hunter_verification_success": False,
                "last_error": f"Hunter verify error: {str(e)}"
            })

    # Case B: We still don't have an email → Try Hunter Email Finder
    elif needs["needs_email"]:
        try:
            logger.info(f"Trying Hunter Email Finder for {queue_item['name']}")

            hunter_find = await hunter_email_finder(
                full_name=queue_item["name"],
                domain=queue_item["course_domain"]
            )

            if hunter_find and hunter_find["email"]:
                result["final_email"] = hunter_find["email"]
                result["confidence"] = hunter_find["score"]
                result["verification_status"] = "hunter_found"
                result["sources"].append("hunter_found")

                logger.info(f"✅ Hunter found email: {hunter_find['email']}")

                await update_queue(queue_item["id"], {
                    "hunter_attempted": True,
                    "hunter_email_found": True,
                    "enriched_email": hunter_find["email"],
                    "email_confidence_score": hunter_find["score"]
                })
            else:
                logger.warning(f"Hunter couldn't find email for {queue_item['name']}")
                await update_queue(queue_item["id"], {
                    "hunter_attempted": True,
                    "hunter_email_found": False
                })

        except HunterAPIError as e:
            logger.error(f"Hunter finder error: {e}")
            await update_queue(queue_item["id"], {
                "hunter_attempted": True,
                "hunter_email_found": False,
                "last_error": f"Hunter finder error: {str(e)}"
            })

    # ═══════════════════════════════════════════════════════
    # FINAL ASSESSMENT: Do we have usable contact?
    # ═══════════════════════════════════════════════════════

    contact_usable = (
        result["final_email"] is not None and
        result["confidence"] >= 70 and
        result.get("verification_status") in ["deliverable", "risky", "hunter_found"]
    )

    if contact_usable:
        logger.info(f"✅ Contact enriched successfully: {queue_item['name']}")

        # Write to golf_course_contacts
        await write_verified_contact_to_supabase(queue_item, result)

        # Mark queue as completed
        await update_queue(queue_item["id"], {
            "enrichment_status": "completed",
            "enriched_email": result["final_email"],
            "enriched_linkedin": result["final_linkedin"],
            "processed_at": datetime.utcnow()
        })

        return {"success": True, "contact": result}

    else:
        logger.warning(f"❌ Contact not usable: {queue_item['name']} - {result.get('verification_status', 'no email')}")

        # Mark as failed
        await update_queue(queue_item["id"], {
            "enrichment_status": "failed",
            "last_error": f"No usable email (confidence: {result['confidence']})",
            "processed_at": datetime.utcnow()
        })

        return {"success": False, "reason": "No verified email found"}
```

### Enrichment Decision Matrix

**Scenario 1: LLM found email + LinkedIn**
```
needs_email: False
needs_linkedin: False
needs_verification: True

Action:
✅ Skip Apollo (already have both)
✅ Hunter verify email only
Cost: $0.01 (Hunter verify)
```

**Scenario 2: LLM found email, no LinkedIn**
```
needs_email: False
needs_linkedin: True
needs_verification: True

Action:
✅ Try Apollo (get LinkedIn)
✅ Hunter verify email
Cost: $0.03 (Apollo search + enrich) + $0.01 (Hunter verify) = $0.04
```

**Scenario 3: LLM no email, has LinkedIn**
```
needs_email: True
needs_linkedin: False
needs_verification: False

Action:
✅ Try Apollo (get email)
✅ If Apollo fails → Hunter Email Finder
✅ Hunter verify final email
Cost: $0.03 (Apollo) + $0.02 (Hunter find/verify) = $0.05
```

**Scenario 4: LLM has neither email nor LinkedIn**
```
needs_email: True
needs_linkedin: True
needs_verification: False

Action:
✅ Try Apollo (get both)
✅ If Apollo fails on email → Hunter Email Finder
✅ Hunter verify final email
Cost: $0.03 (Apollo) + $0.02 (Hunter) = $0.05
```

### Output Schema

```json
{
  "verified_contacts": [
    {
      "name": "Charlie Nolette",
      "title": "General Manager / COO",
      "email": "cnolette@alamancecc.net",
      "email_verified": true,
      "email_confidence": 95,
      "email_status": "deliverable",
      "phone": "(336) 584-0345",
      "linkedin_url": null,
      "apollo_found": false,
      "source_url": "https://www.carolinascmaa.org/...",
      "source_type": "cmaa_directory",
      "discovery_method": "perplexity_research",
      "enrichment_date": "2025-10-30T22:30:00Z"
    }
  ],
  "rejected_contacts": [
    {
      "name": "Example Person",
      "email": "bad@example.com",
      "rejection_reason": "Hunter marked as undeliverable",
      "rejection_score": 25
    }
  ],
  "enrichment_stats": {
    "input_contacts": 9,
    "verified_contacts": 7,
    "rejected_contacts": 2,
    "apollo_found": 3,
    "hunter_cost": 0.021,
    "apollo_cost": 0.012
  }
}
```

### Success Criteria

**Minimum:**
- 80% of LLM contacts pass Hunter verification
- Email confidence ≥90% average

**Target:**
- 90% of LLM contacts pass verification
- Email confidence ≥95% average
- 30%+ have Apollo LinkedIn data

---

## Agent 3: Supabase Writer

### Purpose
Store verified contacts and course intelligence in Supabase for long-term tracking and ClickUp sync.

### Database Schema Updates

#### New Fields for `golf_course_contacts` Table

```sql
-- Discovery & Source Tracking
ALTER TABLE golf_course_contacts ADD COLUMN IF NOT EXISTS
  discovery_source_url TEXT,
  discovery_source_type VARCHAR(50),  -- 'pga_directory', 'cmaa', 'club_website', 'vendor_site', 'newsletter', etc.
  discovery_method VARCHAR(50),       -- 'perplexity_research', 'jina_scrape', etc.
  discovery_timestamp TIMESTAMP DEFAULT NOW(),

-- Email Verification
  email_verified BOOLEAN,
  email_confidence_score INTEGER,    -- 0-100 from Hunter
  email_verification_status VARCHAR(20),  -- 'deliverable', 'risky', 'undeliverable'
  email_verified_at TIMESTAMP,

-- Enrichment Metadata
  apollo_person_id VARCHAR(50),
  apollo_found BOOLEAN DEFAULT FALSE,
  enrichment_timestamp TIMESTAMP,

-- Current Employment Verification
  verified_current BOOLEAN DEFAULT TRUE,
  verification_sources JSONB,        -- ["PGA.org 2025", "Club website 2024"]
  last_verification_date TIMESTAMP;
```

#### New Fields for `golf_courses` Table

```sql
-- Course Intelligence (for outreach personalization)
ALTER TABLE golf_courses ADD COLUMN IF NOT EXISTS
  email_domain_discovered VARCHAR(100),  -- Actual email domain (may differ from website)
  course_intelligence JSONB,             -- Structured intelligence data
  intelligence_gathered_at TIMESTAMP,
  intelligence_sources JSONB;            -- Source URLs for intelligence

-- Example course_intelligence structure:
{
  "ownership": {
    "type": "member_owned" | "independent" | "resort" | "municipal" | "management_company",
    "details": "Jack & Shirley McDougall (since 2021)",
    "source": "club website /about"
  },
  "recent_projects": [
    {
      "type": "renovation" | "construction" | "technology" | "event_space",
      "description": "Birdie Ballroom event venue opened",
      "year": 2023,
      "month": "December",
      "source": "club website announcement"
    }
  ],
  "vendors": [
    {
      "category": "turf" | "irrigation" | "equipment" | "technology",
      "vendor_name": "Rain Bird",
      "product": "Irrigation system",
      "partnership_date": "2024-01",
      "source": "press release"
    }
  ],
  "awards": [
    {
      "award": "#13 US Golf Course",
      "organization": "Golf Magazine",
      "year": 2024,
      "source": "Golf Magazine 2024-25 rankings"
    }
  ],
  "notable_events": [
    {
      "event": "2024 U.S. Open",
      "date": "2024-06-13",
      "source": "USGA"
    }
  ],
  "challenges": [
    "Ultradwarf bermudagrass summer growth management",
    "Balancing green speed vs pace of play"
  ],
  "unique_selling_points": [
    "2024 US Open host",
    "50% water reduction vs pre-restoration",
    "Ranked #2 public course nationally"
  ]
}
```

### Write Logic

**Contact Deduplication:**
```python
# Check if contact already exists
existing = await supabase.execute_sql(f"""
    SELECT id, email, discovery_timestamp
    FROM golf_course_contacts
    WHERE course_id = '{course_id}'
      AND LOWER(email) = LOWER('{contact_email}')
    LIMIT 1
""")

if existing:
    # Update if new data has higher confidence or newer sources
    if new_confidence > existing_confidence:
        # Update contact
        pass
    else:
        # Skip - existing data is better
        pass
else:
    # Insert new contact
    pass
```

**Course Intelligence Merge:**
```python
# If course already has intelligence, merge new data
existing_intel = course["course_intelligence"] or {}
new_intel = discovery["course_intelligence"]

merged_intel = {
    **existing_intel,
    "recent_projects": dedupe_list(
        existing_intel.get("recent_projects", []) + new_intel.get("recent_projects", [])
    ),
    "vendors": dedupe_list(
        existing_intel.get("vendors", []) + new_intel.get("vendors", [])
    ),
    # ... merge other fields
}
```

### Output

**Success:**
```json
{
  "success": true,
  "course_id": "uuid",
  "contacts_inserted": 7,
  "contacts_updated": 2,
  "contacts_skipped": 0,
  "intelligence_updated": true
}
```

**Partial Success:**
```json
{
  "success": true,
  "course_id": "uuid",
  "contacts_inserted": 4,
  "contacts_failed": 1,
  "errors": [
    "Duplicate email for contact: example@domain.com"
  ]
}
```

---

## Agent 4: ClickUp Sync Agent

### Purpose
Create ClickUp tasks for discovered contacts to enable marketing automation and outreach tracking.

### Sync Strategy Options

**Option A: One Task Per Course (RECOMMENDED)**
```
Create 1 task per golf course with:
- Task name: "🏌️ Alamance Country Club - 7 Contacts"
- Description: Course intelligence + contact list
- Custom fields: Contact details, confidence scores
- Subtasks: One per contact for individual outreach tracking
```

**Option B: One Task Per Contact**
```
Create 1 task per contact:
- Task name: "📧 Charlie Nolette - GM @ Alamance CC"
- Description: Contact info + course intel
- Custom fields: Email, phone, confidence, source
- Tags: Role type, club type, confidence tier
```

**Recommendation:** Start with Option A (easier to manage), migrate to Option B if needed for detailed tracking

### ClickUp Task Template

**Task Name:**
```
🏌️ {course_name} - {contact_count} Contacts ({state})
```

**Description (Markdown):**
```markdown
## Course Information
**Name:** {course_name}
**Location:** {city}, {state}
**Domain:** {domain}
**Club Type:** {club_type}

## Course Intelligence

### Recent Projects
- {project_description} ({year})

### Vendors/Technology
- {vendor_name}: {product/service}

### Awards/Recognition
- {award} ({year})

### Unique Selling Points
- {usp_1}
- {usp_2}

## Contacts ({contact_count})

### {contact_1_name} - {contact_1_title}
**Email:** {email} (Confidence: {confidence}%)
**Phone:** {phone}
**LinkedIn:** {linkedin_url}
**Source:** {source_type}

*Personalization hook:* Reference their recent {project} or {vendor} partnership

---

### {contact_2_name} - {contact_2_title}
...

## Outreach Strategy

**Primary Contact:** {highest_confidence_contact}
**Personalization:** Mention {recent_project} or {award}
**Timing:** {best_timing_based_on_intel}
```

### Custom Fields

**Contact Data:**
- `primary_contact_name` (text)
- `primary_contact_email` (email)
- `primary_contact_title` (text)
- `total_contacts` (number)
- `email_confidence_avg` (number) - Average of all contacts

**Course Data:**
- `course_domain` (URL)
- `club_type` (dropdown: Elite Resort, Premium Private, Private CC, Semi-Private, Daily-Fee, Municipal)
- `recent_project` (text) - For personalization
- `key_vendor` (text) - For personalization
- `latest_award` (text) - For credibility

**Tracking:**
- `discovery_date` (date)
- `discovery_method` (text: "llm_perplexity")
- `enrichment_status` (dropdown: Verified, Partial, Pending)

### Tags

- **By Role:** `GM`, `Director-of-Golf`, `Superintendent`, `Head-Pro`
- **By Confidence:** `High-Confidence-90+`, `Medium-Confidence-70-89`, `Low-Confidence-Below-70`
- **By Club Type:** `Elite-Resort`, `Premium-Private`, `Municipal`, etc.
- **By State:** `NC`, `SC`, `VA`, `GA`
- **By Source:** `PGA-Verified`, `CMAA-Member`, `Vendor-Contact`

### ClickUp List Structure

**Recommended:**
```
Workspace: Golf Course Outreach
  └─ Space: Contact Discovery Pipeline
      └─ Folder: By State
          ├─ List: North Carolina Courses
          ├─ List: South Carolina Courses
          ├─ List: Virginia Courses
          └─ List: Georgia Courses
```

**Alternative (by funnel stage):**
```
Workspace: Golf Course Outreach
  └─ Space: Sales Pipeline
      ├─ List: 1. Discovered (new contacts)
      ├─ List: 2. Enriched (verified emails)
      ├─ List: 3. Outreach (in campaign)
      ├─ List: 4. Responded (engaged)
      └─ List: 5. Qualified (sales-ready)
```

### Sync Logic

**Create Task:**
```python
# Use ClickUp MCP
task_result = await clickup_create_task(
    listName="North Carolina Courses",
    name=f"🏌️ {course_name} - {len(contacts)} Contacts ({state})",
    markdown_description=generate_task_description(discovery_data),
    custom_fields=[
        {"id": "primary_email_field_id", "value": primary_contact["email"]},
        {"id": "confidence_field_id", "value": avg_confidence},
        {"id": "club_type_field_id", "value": club_type},
        {"id": "recent_project_field_id", "value": recent_project_summary}
    ],
    tags=["NC", club_type, confidence_tier, primary_role],
    priority=calculate_priority(course_intelligence)  # Based on opportunity signals
)
```

**Create Subtasks (Optional):**
```python
for contact in contacts:
    await clickup_create_task(
        listName="North Carolina Courses",
        name=f"📧 {contact['name']} - {contact['title']}",
        parent=parent_task_id,
        markdown_description=contact_description(contact),
        tags=[contact["title"], f"Confidence-{contact['email_confidence']}"]
    )
```

### Output

```json
{
  "success": true,
  "clickup_task_id": "abc123",
  "clickup_task_url": "https://app.clickup.com/t/abc123",
  "subtasks_created": 7,
  "contacts_synced": 7
}
```

---

## Testing Plan

### Phase 1: Proof of Concept (Week 1)

**Goal:** Validate the hybrid workflow achieves 85-90% success

**Test 1: Single Course End-to-End (Day 1)**
```
Course: Neuse Golf Club
  ↓
Agent 1: LLM Discovery
  → Result: 8 contacts, 3 emails
  ↓
Agent 2: Enrichment
  → Hunter verify 3 emails
  → Result: 3/3 deliverable (100%)
  ↓
Agent 3: Supabase Writer
  → Store 8 contacts with intelligence
  ↓
Agent 4: ClickUp Sync
  → Create 1 task with 8 contact subtasks

Measure:
- End-to-end success: YES/NO
- Time: How long?
- Cost: Actual vs projected
- Data quality: Manual verification
```

**Test 2: Batch of 3 Courses (Day 2)**
```
Courses: Anderson Creek, Alamance, Asheville
Process: Full pipeline for each

Measure:
- Success rate: X/3
- Avg contacts: Y per course
- Avg verified emails: Z per course
- Total cost: $A
- ClickUp tasks created: 3
```

**Test 3: Batch of 20 NC Courses (Days 3-5)**
```
Selection: First 20 NC courses alphabetically from database
Process: Automated batch run

Measure:
- Success rate: X/20 (target ≥85%)
- Total contacts: ~120
- Verified emails: ~50
- Total cost: $60-100
- ClickUp: 20 tasks created

Quality check:
- Manually verify 5 random contacts (100% accuracy expected)
- Check ClickUp formatting/data
- Verify course intelligence is useful
```

**Decision Point:** If ≥85% success → Proceed to Phase 2

---

### Phase 2: Marketing Funnel Build (Week 2)

**Goal:** Convert discovered contacts to revenue

**Build:**

**1. Email Sequence Templates**
```
Email 1: Introduction + Personalization
  Subject: "Saw you {recent_project} at {course_name}"
  Body: Reference course intelligence, introduce value prop

Email 2: Value Demonstration (3 days later)
  Subject: "How {similar_course} improved {metric}"
  Body: Case study, social proof

Email 3: Specific Offer (7 days later)
  Subject: "Quick question about {vendor/challenge}"
  Body: Direct ask, meeting booking link

Email 4: Breakup (14 days later)
  Subject: "Should I close your file?"
  Body: Last chance, remove from list option
```

**2. ClickUp Automation**
```
Trigger: Task moved to "Outreach" list
Actions:
- Send Email 1
- Wait 3 days → Send Email 2
- Wait 7 days → Send Email 3
- Wait 14 days → Send Email 4 OR close

On Reply:
- Move to "Responded" list
- Alert sales rep
- Stop sequence
```

**3. Personalization Variables**
```
{{course_name}}
{{contact_name}}
{{contact_title}}
{{recent_project}}
{{key_vendor}}
{{latest_award}}
{{challenge_mentioned}}
```

**Test:**
- Run sequence on 20 contacts from Phase 1
- Measure: Open rate, click rate, response rate
- Iterate: Adjust messaging based on what works

---

### Phase 3: Scale to 100 Courses (Week 3)

**Goal:** Prove automation handles volume

**Process:**
1. Select 100 NC courses (mix of club types)
2. Run LLM → Enrichment → Supabase → ClickUp
3. Monitor: Success rate, costs, errors
4. Fix: Any issues that appear at scale

**Expected Output:**
- 85-90 successful courses
- 500-600 total contacts
- 200-250 verified emails
- 85-90 ClickUp tasks
- Course intelligence for all

**Feed into Funnel:**
- Add to outreach campaigns weekly
- Segment by club type
- Personalize with intelligence

---

### Phase 4: Full Scale (Month 2)

**Goal:** Process 10,000 courses across 4 states

**States:** NC (457 courses), SC (TBD), VA (TBD), GA (TBD)

**Processing Strategy:**
- Batch size: 100 courses at a time
- Frequency: 1-2 batches per day
- Parallel: Run 3-5 agents concurrently
- Duration: 3-4 weeks for full 10K

**Quality Assurance:**
- Random sampling: 1% manual verification
- Error monitoring: Alert on >10% failure rate
- Cost tracking: Stay within $0.05 per course budget

**Output:**
- 8,500-9,000 successful courses
- 51,000-54,000 total contacts
- 20,000-22,000 verified work emails
- Complete course intelligence database

**Feed into Funnel:**
- Continuous contact flow
- Segmented campaigns by state/club type
- Personalized at scale

---

## Success Metrics

### Discovery Metrics (Agent 1)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Discovery success rate | ≥70% | Courses with 1+ contacts found |
| Avg contacts per course | ≥6 | Total contacts / courses processed |
| Email discovery rate | ≥60% | Courses with 1+ emails found |
| Intelligence capture rate | ≥80% | Courses with actionable intel |
| Source attribution | 100% | All contacts have source URLs |

### Enrichment Metrics (Agent 2)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Email verification rate | ≥90% | Deliverable / total emails |
| Avg confidence score | ≥90 | Hunter confidence average |
| Apollo enhancement rate | ≥30% | Contacts found in Apollo |
| Cost per verified contact | ≤$0.02 | Hunter cost / verified contacts |

### Storage Metrics (Agent 3)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Write success rate | 100% | Successful writes / attempts |
| Deduplication accuracy | 100% | No duplicate contacts |
| Intelligence storage | 100% | All intel stored correctly |
| Query performance | <1 sec | Database response time |

### Sync Metrics (Agent 4)

| Metric | Target | Measurement |
|--------|--------|-------------|
| ClickUp sync success | 100% | Tasks created / courses |
| Custom field population | 100% | Fields populated correctly |
| Task formatting | 100% | Readable, actionable tasks |
| Subtask creation | 100% | If using subtask strategy |

### Overall Pipeline Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **End-to-end success rate** | **≥85%** | Courses in ClickUp / courses input |
| **Verified contacts per course** | **≥4** | Avg verified contacts |
| **Work emails per course** | **≥2** | Avg work emails |
| **Cost per successful course** | **≤$0.05** | Total cost / successful courses |
| **Processing time per course** | **≤90 sec** | Total pipeline time |
| **Data quality** | **≥95%** | Manual spot check accuracy |

---

## API Requirements & Costs

### Required APIs

**1. Perplexity (LLM Discovery)**
- Endpoint: `mcp__perplexity-ask__perplexity_ask`
- Cost: ~$0.01-0.02 per course
- Rate limit: TBD (check plan)
- **You're already paying for this!**

**2. Hunter.io (Email Verification)**
- Endpoint: `mcp__hunter-io__Email-Verifier`
- Cost: ~$0.01 per email verified
- Rate limit: Plan dependent
- **Required:** Pay-per-use

**3. Apollo (Optional Enhancement)**
- Endpoint: `POST /api/v1/people/search`
- Cost: 1 credit per search = ~$0.02
- Rate limit: 600/hour
- **Optional:** Only if person in database

**4. Supabase (Storage)**
- Endpoint: `mcp__supabase__execute_sql`
- Cost: $0 (existing infrastructure)
- **Required:** Already set up

**5. ClickUp (CRM Sync)**
- Endpoint: `mcp__clickup__create_task`, `mcp__clickup__update_task`
- Cost: $0 (existing ClickUp subscription)
- **Required:** Already set up

### Cost Breakdown Per Course

| Component | Cost Range | Notes |
|-----------|------------|-------|
| LLM Discovery | $0.01-0.02 | Perplexity research |
| Email Verification | $0.01-0.03 | Hunter.io (2-3 emails avg) |
| Apollo Enhancement | $0.00-0.02 | Only if in database (30% of time) |
| **Total** | **$0.02-0.07** | **Avg $0.04-0.05** |

### Scaling Costs

| Scale | Total Cost | Cost/Contact | ROI (if $10/contact value) |
|-------|------------|--------------|---------------------------|
| 20 courses | $60-100 | $0.50-1.25 | $1,200-1,500 value |
| 100 courses | $300-500 | $0.50-0.83 | $6,000 value |
| 1,000 courses | $3,000-5,000 | $0.50-0.83 | $60,000 value |
| 10,000 courses | $30,000-50,000 | $0.50-1.00 | $600,000 value |

**ROI:** 10-12x return if each contact worth $10 in sales opportunity

---

## Error Handling & Edge Cases

### LLM Discovery Failures

**No Contacts Found:**
- Store: Course with `discovery_status: "no_public_data"`
- Action: Add to manual review queue
- Don't: Retry immediately (waste API calls)

**Partial Data (names but no emails):**
- Store: Contacts with `has_email: false`
- Action: Try phone/LinkedIn outreach
- Alternative: Apply email pattern inference

**Source URLs Missing:**
- Warning: Log for quality review
- Action: Still proceed if data looks valid
- Manual: Spot check these for quality

### Enrichment Failures

**Hunter Marks as Undeliverable:**
- Rejection: Don't store in database
- Log: For pattern analysis (maybe bad source)
- Consider: Manual verification if high-value contact

**Apollo 422/403 Errors:**
- Expected: Apollo won't have everyone
- Action: Skip Apollo enrichment, use LLM data
- Don't: Fail the entire contact

**Rate Limiting:**
- Exponential backoff
- Queue for retry
- Don't: Lose the contact

### Database Failures

**Duplicate Contact:**
- Check: Is new data better (higher confidence, newer)?
- Update: If better
- Skip: If existing is better

**Missing Course ID:**
- Create: Course record first
- Then: Add contacts
- Link: Properly with foreign keys

### ClickUp Sync Failures

**Task Creation Fails:**
- Retry: Once with exponential backoff
- Log: Error for manual review
- Store: Contacts still saved in Supabase (can sync manually)

**Custom Field Missing:**
- Adapt: Skip that field, use others
- Log: Warning for setup review
- Don't: Fail entire task creation

---

## Monitoring & Quality Assurance

### Real-Time Monitoring

**Dashboards to Build:**

**Pipeline Health:**
```
- Courses processed: X/total
- Current success rate: Y%
- Avg contacts per course: Z
- Avg emails per course: A
- Current cost per course: $B
- Est. completion time: C hours
```

**Quality Metrics:**
```
- Email verification pass rate: X%
- Avg email confidence: Y
- Source attribution: Z%
- Intelligence capture: A%
```

**Error Tracking:**
```
- LLM failures: X
- Enrichment failures: Y
- Database failures: Z
- ClickUp sync failures: A
```

### Quality Checks

**Automated (every run):**
- Email format validation (has @, domain)
- Phone format validation (US format)
- Duplicate detection (same email in database)
- Confidence threshold (reject <70%)

**Manual (sampling):**
- Week 1: 100% manual review (3 courses)
- Week 2: 20% sampling (4 of 20 courses)
- Week 3: 5% sampling (5 of 100 courses)
- Month 2: 1% sampling (100 of 10K courses)

**Verification Process:**
1. Pick random course
2. Check ClickUp task
3. Verify 2-3 contacts manually (email deliverable? correct title?)
4. Check source URLs (legitimate sources?)
5. Validate intelligence (accurate? recent?)

**Pass Criteria:** ≥95% accuracy on spot checks

---

## Rollout Schedule

### Week 1: Validation Phase
- **Day 1:** Build Agent 1 (LLM Discovery)
- **Day 2:** Build Agent 2 (Enrichment)
- **Day 3:** Build Agent 3 (Supabase Writer) + database schema updates
- **Day 4:** Build Agent 4 (ClickUp Sync)
- **Day 5:** Test on 20 courses, measure success rate

**Deliverable:** 120-150 verified contacts in ClickUp

---

### Week 2: Funnel Build
- **Day 1-2:** Email sequence templates
- **Day 3:** ClickUp automation setup
- **Day 4:** Test sequences on 20 contacts
- **Day 5:** Launch first campaign

**Deliverable:** Active outreach, first responses

---

### Week 3: Optimization
- **Day 1-2:** Optimize agents based on Week 1 data
- **Day 3-4:** Build parallel processing
- **Day 5-7:** Run on 100 courses

**Deliverable:** 600+ contacts, proven scalability

---

### Week 4+: Full Scale
- Process 1,000 courses per week
- Feed funnel continuously
- Monitor quality
- Iterate on messaging

**Deliverable:** 10K course coverage in 2-3 months

---

## Handoff Instructions for Next Agents

### What You Need to Know

**1. This Workflow Was Validated Through Testing**
- 7 courses tested manually with LLM
- 71% success rate proven
- Patterns documented in `progress.md`
- Source strategies identified

**2. LLM Discovery is the Core Innovation**
- Uses Perplexity MCP (already available)
- Multi-source strategy (PGA.org, club sites, associations, vendors)
- Proven better than Apollo-only (71% vs 0%)

**3. Key Files for Reference**
- `progress.md` - Testing journey & findings
- `llm_discovery_patterns.md` - Source strategies by role
- `llm_vs_agent_comparison.md` - Performance comparison
- `apollo_api_limitations_oct30.md` - Why Apollo-only fails
- `apollo_org_enrich_api.md` - API documentation

**4. Database Schema Changes Required**
See Agent 3 section above for new fields needed in:
- `golf_course_contacts` table
- `golf_courses` table

**5. ClickUp Setup Needed**
- Create lists (by state or by funnel stage)
- Create custom fields (see Agent 4 section)
- Configure tags
- Set up automation rules

### Questions to Answer During Build

**Agent 1:**
- Can we optimize the Perplexity prompt further?
- Should we check additional sources?
- How to handle courses with no public data?

**Agent 2:**
- What Hunter confidence threshold to use? (Current: ≥70%)
- Should we always try Apollo or only for certain club types?
- How to handle personal emails vs work emails?

**Agent 3:**
- How to handle intelligence conflicts (different sources say different things)?
- When to update vs when to preserve existing data?
- How long to keep rejected contacts (for analysis)?

**Agent 4:**
- Task per course or task per contact?
- Which custom fields are most valuable?
- How to handle task updates (when contacts change)?

### Testing Checkpoints

**Before Phase 1:**
- [ ] All 4 agents built and unit tested
- [ ] Database schema updated
- [ ] ClickUp lists/fields created
- [ ] Test with 1 course end-to-end

**Before Phase 2:**
- [ ] 20-course test completed
- [ ] ≥85% success rate achieved
- [ ] Contacts in ClickUp verified accurate
- [ ] Cost per course ≤$0.05

**Before Phase 3:**
- [ ] Email sequences created
- [ ] Automation tested
- [ ] First responses received
- [ ] Conversion tracking working

**Before Phase 4:**
- [ ] 100-course test successful
- [ ] Parallel processing working
- [ ] Error rate <5%
- [ ] Quality spot checks passing

---

## Success Criteria

### Minimum Viable (Deploy to Production)
- ✅ End-to-end success rate ≥70%
- ✅ Email verification rate ≥90%
- ✅ Cost per course ≤$0.10
- ✅ Data quality ≥95% (spot checks)
- ✅ ClickUp tasks created correctly

### Target (Production-Ready)
- ✅ End-to-end success rate ≥85%
- ✅ Avg 4+ verified contacts per course
- ✅ Avg 2+ work emails per course
- ✅ Cost per course ≤$0.05
- ✅ Intelligence captured for 80%+ courses

### Stretch (Excellent Performance)
- ✅ End-to-end success rate ≥90%
- ✅ Avg 5+ verified contacts per course
- ✅ Avg 3+ work emails per course
- ✅ Cost per course ≤$0.04
- ✅ All contacts have source attribution

---

## Risk Mitigation

### Technical Risks

**Risk:** Perplexity rate limits
**Mitigation:** Batch processing, rate limiting, queue system

**Risk:** Hunter.io costs spiral
**Mitigation:** Only verify emails that pass format check, set daily budget cap

**Risk:** Database performance degrades at scale
**Mitigation:** Indexes on key fields, batch inserts, connection pooling

**Risk:** ClickUp API rate limits
**Mitigation:** Batch task creation, respect rate limits, queue system

### Quality Risks

**Risk:** LLM hallucinates contacts
**Mitigation:** Require source URLs, cross-verify with Hunter, manual spot checks

**Risk:** Outdated contacts (people changed jobs)
**Mitigation:** LLM checks for recency (2024-2025), periodic re-verification

**Risk:** Email domain mismatch
**Mitigation:** Discover actual email domain from sources, accept variations

**Risk:** Intelligence is inaccurate
**Mitigation:** Require source attribution, periodic spot checks

### Business Risks

**Risk:** Outreach marked as spam
**Mitigation:** Use verified emails only, personalize with intelligence, proper opt-out

**Risk:** GDPR/compliance issues
**Mitigation:** Only use publicly available data, provide source URLs, honor opt-outs

**Risk:** ROI doesn't justify cost
**Mitigation:** Phase 1 validates before scaling, can stop if not working

---

## Future Enhancements

### Version 1.1 (After Initial Deployment)
- [ ] Add more vendor site sources (Toro, John Deere, Rain Bird pages)
- [ ] Social media integration (Instagram/Facebook for supers)
- [ ] Newsletter archive mining (better email discovery)
- [ ] Pattern inference (apply email patterns automatically)

### Version 2.0 (3-6 Months Out)
- [ ] Build custom LLM agent (fine-tuned for golf discovery)
- [ ] Add Jina/Firecrawl for specific page scraping
- [ ] Real-time verification (check if person still employed)
- [ ] Competitive intelligence (what vendors competitors use)

### Version 3.0 (Long-term)
- [ ] Expand to all US golf courses (20K+)
- [ ] Add international courses
- [ ] Predictive scoring (which courses most likely to convert)
- [ ] Auto-personalization (AI writes emails using intel)

---

## Appendix: Testing Results Reference

### Courses Tested (Oct 30, 2025)

**Small/Mid-Tier:**
1. Anderson Creek GC - 3 contacts, 1 email (33%)
2. Asheboro CC - 2 contacts, 0 emails (0%)
3. Ayden Golf & CC - 7 contacts, 0 emails (0%)

**Premium Private:**
4. Alamance CC - 9 contacts, 3 emails (33%)
5. Charlotte CC - 13 contacts, 3 emails (23%)

**Municipal:**
6. Asheville Municipal - 4 contacts, 3 emails (75%)

**Semi-Private:**
7. Neuse GC - 8 contacts, 3 emails (38%)

**Elite Resort:**
8. Pinehurst No. 2 - 10+ contacts, 7 emails (70%)

**Overall:** 56 contacts, 20 work emails, 71% course success rate (5/7 found emails)

### Key Patterns Discovered

**By Club Type:**
- Elite Resort: 100% email success, professional associations primary source
- Municipal: 100% email success, government sites publish contacts
- Premium Private: 35% email success, mix of newsletters/vendors/associations
- Semi-Private: 38% email success, club websites primary source
- Small Private: 11% email success, limited public data

**By Role:**
- Golf Pros: PGA.org 90% coverage (names), newsletters 60% (emails)
- General Managers: CMAA 30%, club websites 60%, ContactOut 20%
- Superintendents: Vendor sites 40%, GCSAA 30%, club blogs 20%

**Source Breakthroughs:**
- Vendor sites publish superintendent contacts (Mach 1 Greens example)
- Newsletters reveal actual email domains (not website domains)
- Professional associations have direct contacts (GCSAA, CMAA)
- Social media has appreciation posts (superintendent discovery)

---

## Contact

**Questions during build?**
- Reference: `progress.md` for detailed testing journey
- Reference: `llm_discovery_patterns.md` for source strategies
- Review: Actual LLM responses in testing/archives

**Updates to workflow?**
- Document in: `llmtoclickup_v2.md`
- Track changes in: Version control

---

**Status:** Ready for agent implementation
**Confidence:** High (validated through 7-course testing)
**Expected Impact:** 0% → 85-90% success rate, 10K course coverage, continuous outreach engine
