# POC Workflow: Production-Ready Multi-Agent System

**Status:** 3 Agents Complete ✅ | Orchestrator Next 🔄

---

## Quick Start

**New Engineers/Claude Sessions:**

1. **Read First:**
   - `goal.md` - Mission and success criteria
   - `progress.md` - Current status and metrics
   - `.claude/CLAUDE.md` - Quick context for handoffs

2. **Building New Agents:**
   - `template/README.md` - How to use templates
   - `template/DEVELOPMENT.md` - Step-by-step guide
   - `experiments/MCP_TOOL_BASELINE.md` - Tool capabilities

3. **Reference:**
   - `agents/` - Production code (learn from working examples)
   - `tests/` - Testing framework
   - `experiments/` - What we learned

---

## Directory Structure

```
poc-workflow/
├── README.md                    # This file
├── goal.md                      # Mission & success criteria
├── progress.md                  # Status tracker
├── .env.example                 # API key template
├── .claude/CLAUDE.md           # Session context
│
├── agents/                      # ✅ Production agents
│   ├── README.md               # Usage guide
│   ├── agent1_url_finder.py    # URL discovery ($0.015, 100%)
│   ├── agent2_contact_extractor.py  # Contact extraction ($0.012, 100%)
│   └── agent3_contact_enricher.py   # Email + LinkedIn ($0.012/contact, 50%/25%)
│
├── tests/                       # 🧪 Test scripts
│   ├── test_agent1.py          # Agent 1 batch test
│   ├── test_agent2.py          # Agent 2 batch test
│   └── test_agent3.py          # Agent 3 batch test
│
├── results/                     # 💾 Test outputs
│   ├── agent1_results.json     # 5 course URLs
│   ├── agent2_results.json     # 12 extracted contacts
│   └── agent3_batch_test_results.json  # 12 enriched contacts
│
├── template/                    # 📋 Reusable templates
│   ├── README.md               # Template guide
│   ├── DEVELOPMENT.md          # Build guide
│   ├── agent_template.py       # Agent template
│   ├── test_template.py        # Test template
│   └── utils/                  # Shared code
│       ├── env_loader.py       # .env loading
│       └── json_parser.py      # JSON parsing
│
└── experiments/                 # 📦 Archive
    ├── MCP_TOOL_BASELINE.md    # Tool testing results
    ├── agent2_testing/         # Agent 2 iterations
    └── agent3_testing/         # Agent 3 iterations
```

---

## Agents Overview

### Agent 1: URL Finder ✅
**What:** Finds golf course listing URLs from VSGA directory
**Cost:** $0.0153/search (24% under budget)
**Accuracy:** 100% (5/5)
**Pattern:** Custom Jina tool, pre-processes 78K → 2K tokens

### Agent 2: Contact Extractor ✅
**What:** Extracts staff contacts (name, title, phone) from course URLs
**Cost:** $0.0123/extraction (38% under budget)
**Accuracy:** 100% (5/5 courses, 12 contacts)
**Pattern:** Built-in WebFetch, structured JSON output

### Agent 3: Contact Enricher ✅
**What:** Finds emails + LinkedIn URLs via Hunter.io API
**Cost:** $0.0116/contact (42% under budget)
**Success:** 50% emails, 25% LinkedIn (bonus from same API call!)
**Pattern:** Custom Hunter.io tool, NO fallbacks (nulls if not found)

**Combined:** $0.0392 per course (22% under $0.05 budget)

---

## Key Principles

### 1. Data Quality > Quantity
**Never guess or use fallbacks.** Return `null` if data not found.

```python
# ❌ BAD: Guessing
if not email_found:
    return f"info@{domain}"

# ✅ GOOD: Honest null
if not email_found:
    return None
```

### 2. Test MCP Tools First
**Before building SDK agents:**
1. Test MCP tools in Claude Code (has MCP configured)
2. Document capabilities, costs, success rates
3. Build SDK custom tool replicating behavior

**Why:** SDK subprocess has `mcp_servers: []` (no MCP access)

### 3. Custom SDK Tools
**Winning pattern:**
- Build @tool with direct API calls
- Pre-process data (reduce tokens 97%!)
- Return JSON only
- Handle errors gracefully

### 4. Specialist Agents
**One agent = one responsibility**
- Simpler code
- Easier testing
- Better cost control
- Reusable components

---

## Running Agents

```bash
# Individual agents (demo)
python agents/agent1_url_finder.py
python agents/agent2_contact_extractor.py
python agents/agent3_contact_enricher.py

# Batch tests
python tests/test_agent1.py
python tests/test_agent2.py
python tests/test_agent3.py
```

---

## Building New Agents

**See:** `template/` folder

```bash
# Quick start
cp template/agent_template.py agents/agent4_new_agent.py
cp template/test_template.py tests/test_agent4.py

# Follow template/DEVELOPMENT.md guide
```

---

## Cost Performance

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Agent 1 | $0.02 | $0.0153 | ✅ 24% under |
| Agent 2 | $0.02 | $0.0123 | ✅ 38% under |
| Agent 3 | $0.02 | $0.0116 | ✅ 42% under |
| **Per Course** | **$0.05** | **$0.0392** | **✅ 22% under** |

**Scale (500 courses/day):**
- Daily: $27.73
- Monthly: $832

---

## Major Discoveries

1. **Hunter.io Email-Finder includes LinkedIn URLs** - No separate LinkedIn agent needed!
2. **Hunter.io Domain-Search finds ALL contacts** - Could replace web scraping
3. **Perplexity finds phone numbers** - Only tool that succeeded
4. **BrightData adds 22% more LinkedIn URLs** - Good fallback for Hunter.io misses
5. **SDK agents need custom tools** - MCP servers not available in subprocess

---

## Next Steps

1. **Build Agent 4** - LinkedIn fallback (BrightData for Hunter.io misses)
2. **Build Agent 5** - Phone finder (Perplexity)
3. **Build Orchestrator** - Connect all agents
4. **Deploy** - Cloud Run / Railway

---

## Reference Docs

- `/AGENT_SDK_KNOWLEDGE.md` - Complete SDK reference
- `experiments/MCP_TOOL_BASELINE.md` - Tool testing results
- `template/DEVELOPMENT.md` - Agent development guide
- `progress.md` - Detailed history
