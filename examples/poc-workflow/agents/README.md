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

## Agent 3: Email Finder

**File:** `agent3_email_finder.py`

**What it does:**
Finds professional email addresses for contacts using Hunter.io API + fallback searches

**Performance:**
- Success Rate: 50% (Hunter.io coverage)
- Cost: $0.0119/contact (40% under budget)
- Confidence: 95-98% when found
- Speed: ~8s per contact

**Usage:**
```python
from agent3_email_finder import find_email

contact = {
    "name": "Stacy Foster",
    "title": "General Manager",
    "company": "Richmond Country Club",
    "domain": "richmondcountryclubva.com"
}

result = await find_email(contact)
print(result["email"])  # sfoster@richmondcountryclubva.com
```

**Input:** Contact dict (from Agent 2)
**Output:**
```json
{
  "email": "sfoster@richmondcountryclubva.com",
  "email_method": "hunter_io",
  "email_confidence": 98,
  "steps_attempted": ["hunter_io"]
}
```

**Pattern:**
- Custom tool with Hunter.io API
- 5-step fallback (Hunter → search → search → general → manual flag)
- SDK MCP server (in-process)
- max_turns: 2

**Note:** LinkedIn enrichment moved to Agent 4

---

## Agent 4: LinkedIn Specialist

**Status:** 📋 Planned

**Goal:** Find LinkedIn URLs for contacts
**Target:** < $0.01 per contact

---

## Using These Agents

1. Review the agent file
2. Understand the pattern (smart tool + config)
3. Adapt for your use case
4. Test before production
5. Follow same pattern for new agents
