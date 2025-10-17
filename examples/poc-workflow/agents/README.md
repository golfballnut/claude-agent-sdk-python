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

**Status:** 🔄 Coming next

**Goal:** Extract contact information from course URLs
**Target:** < $0.02 per extraction

---

## Using These Agents

1. Review the agent file
2. Understand the pattern (smart tool + config)
3. Adapt for your use case
4. Test before production
5. Follow same pattern for new agents
