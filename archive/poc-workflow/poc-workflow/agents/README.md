# Production-Ready Agents

This directory contains tested, production-ready agent implementations.

## Agent 1: URL Finder

**File:** `agent1_url_finder.py`

**What it does:**
Finds golf course listing URLs from VSGA member directory

**Performance:**
- Cost: $0.0153/search
- Accuracy: 100%
- Speed: 3.4s average

**Usage:**
```bash
# Edit the query in the script, then run:
python agent1_url_finder.py
```

**Input:** Course name (string)
**Output:** https://vsga.org/courselisting/[ID]?hsLang=en

**Pattern:**
- Smart tool: Pre-processes 78K → 2K tokens
- Model: claude-haiku-4-5
- SDK MCP server (in-process)
- max_turns: 2
- Cost optimized

---

## Agent 2: Data Extractor

**File:** `agent2_data_extractor.py`

**What it does:**
Extracts contact information (name, website, phone, staff) from golf course URLs

**Performance:**
- Cost: $0.0123/extraction (38% under budget)
- Accuracy: 100%
- Speed: 8.5s average

**Usage:**
```python
from agent2_data_extractor import extract_contact_data

result = await extract_contact_data("https://vsga.org/courselisting/11950")
print(result["data"])
```

**Input:** Golf course URL (from Agent 1)
**Output:**
```json
{
  "course_name": "Richmond Country Club",
  "website": "https://www.richmondcountryclubva.com/",
  "phone": "(804) 784-5663",
  "staff": [
    {"name": "Stacy Foster", "title": "General Manager"}
  ]
}
```

**Pattern:**
- Built-in WebFetch tool (simpler than custom)
- Model: claude-haiku-4-5
- max_turns: 4
- Structured JSON output

---

## Agent 3: Contact Enricher

**File:** `agent3_contact_enricher.py`

**What it does:**
Enriches contacts with professional emails AND LinkedIn URLs using Hunter.io API

**Performance:**
- Email Success: 50% (6/12 contacts)
- LinkedIn Success: 25% (3/12 contacts - bonus!)
- Cost: $0.0116/contact (42% under budget)
- Confidence: 95-98% when found
- Speed: ~8s per contact

**Usage:**
```python
from agent3_contact_enricher import enrich_contact

contact = {
    "name": "Stacy Foster",
    "title": "General Manager",
    "company": "Richmond Country Club",
    "domain": "richmondcountryclubva.com"
}

result = await enrich_contact(contact)
print(result["email"])       # sfoster@richmondcountryclubva.com
print(result["linkedin_url"]) # https://linkedin.com/in/stacy-foster-...
```

**Input:** Contact dict (from Agent 2)
**Output:**
```json
{
  "email": "sfoster@richmondcountryclubva.com",
  "email_method": "hunter_io",
  "email_confidence": 98,
  "linkedin_url": "https://www.linkedin.com/in/stacy-foster-20b79448",
  "linkedin_method": "hunter_io",
  "steps_attempted": ["hunter_io"]
}
```

**Pattern:**
- Custom tool with Hunter.io API
- 3-step discovery (Hunter → web search → focused search)
- **NO FALLBACKS** - returns null if not found (never guesses!)
- SDK MCP server (in-process)
- max_turns: 2

**Data Quality Rule:** Returns honest nulls instead of guessed fallbacks

**Key Discovery:** Hunter.io Email-Finder includes linkedin_url field!
- Single API call returns both email + LinkedIn
- No extra cost for LinkedIn data
- 50% of emails also include LinkedIn URLs

---

## Data Quality Principle

**All agents follow:** Never guess or use generic fallbacks

```python
# ❌ BAD: Guessing
if not found:
    return f"info@{domain}"  # Unreliable guess

# ✅ GOOD: Honest null
if not found:
    return None  # Clean, accurate
```

**Why:** Better to have accurate nulls than unreliable data

---

## Using These Agents

1. Review the agent file
2. Understand the pattern (smart tool + config)
3. Adapt for your use case
4. Test before production
5. Follow same pattern for new agents

---

## Key Learnings

1. **Pre-processing saves tokens:** 78K → 2K = 97% savings (Agent 1)
2. **Test MCP tools in Claude Code first:** Establish baseline before building SDK
3. **Custom SDK tools required:** SDK subprocess has no MCP servers (`mcp_servers: []`)
4. **Direct API calls:** Hunter.io, Jina, etc. called directly (not via MCP)
5. **Haiku 4.5 for cost:** 10x cheaper than Sonnet, accurate with good tools
6. **No fallbacks policy:** Return `null` instead of guessing (data quality!)
7. **Hunter.io Email-Finder bonus:** Includes LinkedIn URLs (50% of results)
8. **Specialist pattern:** One agent, one clear responsibility
9. **max_turns=2-3:** Prevents runaway costs
10. **Block unnecessary tools:** Explicitly disallow WebSearch, Task, TodoWrite, etc.

---

## Building New Agents

**See:** `../template/` folder

Contains:
- Complete agent template
- Test framework template
- Development guide (step-by-step)
- Shared utilities (env loading, JSON parsing)

**Quick start:**
```bash
cp ../template/agent_template.py agent4_new_agent.py
# Follow ../template/DEVELOPMENT.md
```
