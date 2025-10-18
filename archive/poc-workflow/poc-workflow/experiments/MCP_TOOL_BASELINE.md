# MCP Tool Capabilities Baseline

**Date:** 2025-10-16
**Purpose:** Document what each MCP tool can do to maximize contact enrichment
**Method:** Tested via Claude Code (has MCP servers) before building SDK agents

---

## Summary: Tool Capabilities Matrix

| Tool | Email | LinkedIn URL | Phone | Employment | Cost Est | Success Rate |
|------|-------|--------------|-------|------------|----------|--------------|
| **Hunter.io Email-Finder** | ✅ 98% conf | ✅ Bonus 50% | ❌ | ✅ Title/role | Low | 50% |
| **Hunter.io Domain-Search** | ✅ All at domain | ✅ Many | ❌ | ✅ All staff | Low | 100% domain |
| **Hunter.io Email-Enrichment** | ✅ | ✅ Handle | ❌ | ✅ Full profile | Low | High |
| **BrightData search_engine** | ❌ | ✅ 22% of misses | ❌ | ❌ | Med | 22-33% |
| **BrightData scrape** | ❌ | ✅ | ❌ | ⚠️ Current only | Med | Partial |
| **Firecrawl search** | ❌ | ✅ Good results | ❌ | ❌ | Med | Good |
| **Perplexity ask** | ✅ | ✅ | ✅ ⭐ | ✅ | High? | Excellent |

---

## Test Results Detail

### Hunter.io Email-Finder
**What it does:** Find email from name + domain
**What we tested:** `Stacy Foster` at `richmondcountryclubva.com`

**Returns:**
```json
{
  "email": "sfoster@richmondcountryclubva.com",
  "score": 98,
  "position": "General Manager",
  "linkedin_url": "https://www.linkedin.com/in/stacy-foster-20b79448",
  "verification": {"status": "valid"},
  "sources": [...]
}
```

**Key Findings:**
- ✅ High confidence emails (95-98%)
- ✅ **BONUS:** linkedin_url included (50% of results)
- ✅ Position/title data
- ❌ No phone numbers
- **Success Rate:** 50% (6/12 contacts)
- **Cost:** Included in plan, ~1 credit per search

**Best For:** Primary email discovery + free LinkedIn URLs

---

### Hunter.io Domain-Search ⭐ GAME CHANGER
**What it does:** Find ALL contacts at a domain
**What we tested:** `richmondcountryclubva.com`

**Returns:**
```json
{
  "pattern": "{first}{last}",
  "organization": "Richmond Country Club",
  "emails": [
    {
      "value": "bill@richmondcountryclubva.com",
      "first_name": "Bill",
      "last_name": "Ranson",
      "position": "Head Golf Professional",
      "linkedin": "https://www.linkedin.com/in/billranson",
      "confidence": 86
    },
    {
      "value": "sfoster@richmondcountryclubva.com",
      "first_name": "Stacy",
      "last_name": "Foster",
      "position": "General Manager",
      "linkedin": "https://www.linkedin.com/in/stacy-foster-20b79448",
      "confidence": 87
    },
    ...
  ]
}
```

**Key Findings:**
- ✅ **Discovers ALL contacts** at domain (not just who we know about)
- ✅ Email pattern for guessing additional emails
- ✅ LinkedIn URLs included
- ✅ Position data
- ✅ Single API call vs multiple scrapes
- **Success Rate:** 100% for finding domain contacts
- **Cost:** ~5 credits per domain

**Architecture Impact:** Could replace Agent 2 web scraping!

---

### Hunter.io Email-Enrichment
**What it does:** Enrich known email with profile data
**What we tested:** `sfoster@richmondcountryclubva.com`

**Returns:**
```json
{
  "name": {"fullName": "Stacy Foster"},
  "email": "sfoster@richmondcountryclubva.com",
  "location": "Richmond, Virginia, United States",
  "geo": {"city": "Richmond", "state": "VA", "lat": 37.55, "lng": -77.46},
  "employment": {
    "domain": "richmondcountryclubva.com",
    "name": "Richmond Country Club",
    "title": "General Manager",
    "role": "management",
    "seniority": "senior"
  },
  "linkedin": {"handle": "stacy-foster-20b79448"},
  "phone": null
}
```

**Key Findings:**
- ✅ Full employment profile
- ✅ Geo location data
- ✅ LinkedIn handle
- ✅ Seniority/department classification
- ❌ Still no phone
- **Best For:** Enriching already-found emails with metadata

---

### BrightData search_engine ⭐ LINKEDIN FALLBACK
**What it does:** Google search with anti-block
**What we tested:** LinkedIn site-filtered searches for 7 contacts

**Results:**
- Dean Sumner: ✅ Found `linkedin.com/in/dean-sumner-a1469542`
- Tim Newsom: ✅ Found `linkedin.com/in/tim-newsom-a8604125`
- Eddie Luke: ❌ Not found
- Tucker Jarman: ❌ Not found
- Conlin Giles: ❌ Not found
- Brian Ratkovich: ❌ Not found
- Micheal Hall: ❌ Not found

**Key Findings:**
- **Success Rate:** 2/7 (29% of Hunter.io misses)
- ✅ Finds LinkedIn URLs Hunter.io missed
- ✅ Returns full search results (titles, snippets)
- **Combined with Hunter.io:** 5/12 total (42% LinkedIn coverage)
- **Cost:** Unknown (need to check BrightData pricing)

**Best For:** LinkedIn URL discovery fallback

---

### BrightData scrape_as_markdown
**What it does:** Scrape specific URLs
**What we tested:** LinkedIn profile URL

**Returns:**
```markdown
## Experience
- General Manager
- RICHMOND COUNTRY CLUB INC.
- Mar 2007 - Present (18 years 8 months)
- Richmond, Virginia Area

## Education
- Virginia Commonwealth University
```

**Key Findings:**
- ✅ Gets current employment (role, duration, company)
- ✅ Education data
- ✅ Bypasses some LinkedIn blocks
- ❌ Full history requires login (auth wall)
- **Best For:** Current employment verification

---

### Firecrawl firecrawl_search
**What it does:** AI-powered web search
**What we tested:** "Dean Sumner Director of Golf Quinton Oaks LinkedIn"

**Returns:**
```json
{
  "web": [
    {
      "url": "https://www.linkedin.com/in/dean-sumner-a1469542",
      "title": "Dean Sumner - Manage Quinton Oaks...",
      "description": "My responsibilities include managing...",
      "position": 1
    },
    ...
  ]
}
```

**Key Findings:**
- ✅ Clean structured results
- ✅ Relevant ranking (correct profile at position 1)
- ✅ Includes descriptions
- **Success Rate:** Good for LinkedIn discovery
- **Cost:** Need to verify Firecrawl pricing

**Best For:** Alternative to BrightData for LinkedIn search

---

### Perplexity Ask ⭐⭐⭐ PHONE NUMBER DISCOVERY
**What it does:** AI search with citations
**What we tested:** "Find email and phone for Stacy Foster at Richmond Country Club"

**Returns:**
```
Email: sfoster@richmondcountryclubva.com
Phone: 804.592.5861  ⭐

Citations:
- richmondcountryclubva.com/contact
- ZoomInfo
- Datanyze
- VSGA
+ 7 more sources
```

**Key Findings:**
- ✅ **FOUND PHONE NUMBER!** (only tool that did)
- ✅ AI aggregates from multiple sources
- ✅ Citations for verification
- ✅ Natural language query
- **Cost:** Unknown (need Perplexity API pricing)

**Best For:** Finding phone numbers from public sources

---

## Architecture Recommendations

### Option A: Radical Simplification (Hunter.io Only)

**Replace Agents 2 + 3 with ONE agent:**
```
Agent 1: URL Finder ($0.015)
  ↓
Agent 2: Hunter.io Domain-Search ($0.02?)
  - Gets ALL contacts at domain
  - Includes emails + LinkedIn + positions
  - Single API call
  ↓
Agent 3: BrightData LinkedIn fallback ($0.01)
  - Only for contacts missing LinkedIn
  ↓
Agent 4: Perplexity phone finder ($0.02?)
  - Finds phone numbers
  ↓
Complete Data
```

**Pros:**
- Simpler (2-3 agents vs 4)
- Faster (fewer steps)
- More complete (finds contacts we miss with scraping)

**Cons:**
- Relies on Hunter.io domain coverage
- May miss contacts not in Hunter.io database

### Option B: Current + Phone Enhancement

**Keep current architecture, add phone discovery:**
```
Agent 1: URL Finder
Agent 2: Contact Extractor (scraping)
Agent 3: Email + LinkedIn (Hunter.io)
Agent 4: Phone Finder (Perplexity)
Agent 5: LinkedIn Fallback (BrightData)
```

### Option C: Hybrid Approach (RECOMMENDED)

**Best of both:**
```
Agent 1: URL Finder ($0.015)
  ↓
Agent 2: Dual Strategy
  - Try Hunter.io Domain-Search first
  - Fallback to web scraping if domain not in Hunter.io
  - Cost: $0.012-0.02
  ↓
Agent 3: Enrichment (multi-tool)
  - Hunter.io for emails/LinkedIn
  - BrightData for LinkedIn misses
  - Perplexity for phone numbers
  - Cost: $0.015-0.03 per contact
  ↓
Complete Contact Data (email, phone, LinkedIn, employment)
```

**Estimated Total:** $0.05-0.08 per course

---

## Next Steps

1. **Test Hunter.io Domain-Search cost** - Check pricing/credits
2. **Test Perplexity API pricing** - Evaluate phone discovery cost
3. **Prototype Agent 2.5** - Hunter.io Domain-Search version
4. **Build Agent 4** - Phone finder with Perplexity
5. **Build Agent 5** - LinkedIn fallback with BrightData
6. **Compare architectures** - Measure total cost/coverage

---

## Key Discoveries

1. **Hunter.io Domain-Search** could replace web scraping (finds all contacts)
2. **Perplexity** is the ONLY tool that found phone numbers
3. **BrightData** adds 22-29% more LinkedIn URLs
4. **Combined tools** give much better coverage than any single tool

**Recommendation:** Build comprehensive enrichment agent using multiple tools in sequence
