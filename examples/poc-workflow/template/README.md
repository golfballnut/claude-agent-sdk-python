# Claude SDK Agent Template

**Purpose:** Reusable templates for building production-ready SDK agents
**Based on:** Proven patterns from POC workflow (Agents 1, 2, 3)

---

## What's Included

### Templates
- **`agent_template.py`** - Complete agent with custom tool, utilities, demo
- **`test_template.py`** - Testing framework with batch processing, metrics

### Utilities
- **`utils/env_loader.py`** - Standard .env loading (4 levels up from agents/)
- **`utils/json_parser.py`** - Extract JSON from agent text responses

### Documentation
- **`DEVELOPMENT.md`** - Step-by-step guide for building new agents
- **`README.md`** - This file

---

## Quick Start

```bash
# 1. Copy agent template
cp template/agent_template.py agents/agent4_linkedin_finder.py

# 2. Copy test template
cp template/test_template.py tests/test_agent4.py

# 3. Find and replace placeholders:
#    {N} → 4
#    {name} → linkedin_finder
#    {Agent Name} → LinkedIn Finder
#    {tool_name} → find_linkedin
#    {agent_function} → find_linkedin_url
#    {server_name} → linkedin
#    {API_KEY_NAME} → BRIGHTDATA_API_TOKEN

# 4. Implement tool logic in {tool_name}_tool()

# 5. Test
python agents/agent4_linkedin_finder.py  # Demo
python tests/test_agent4.py              # Full test
```

---

## Key Principles (From POC Learnings)

### 1. Data Quality > Quantity
**Rule:** Return null if not found - NEVER guess or use fallbacks

```python
# ❌ BAD:
if not email:
    email = f"info@{domain}"  # Guessing!

# ✅ GOOD:
if not email:
    results["email"] = None  # Honest null
    results["method"] = "not_found"
```

### 2. Test MCP Tools First
**Before building SDK agent:**
1. Test tool in Claude Code (has MCP servers)
2. Document what works, costs, success rate
3. Build SDK tool that replicates behavior

**Why:** SDK agents can't use MCP tools directly (subprocess has `mcp_servers: []`)

### 3. Custom Tools = Proven Pattern
**All successful agents use custom SDK tools:**
- Agent 1: Custom fetch tool (Jina API)
- Agent 2: Built-in WebFetch
- Agent 3: Custom enrich tool (Hunter.io API)

**Pattern:**
```python
@tool("name", "desc", {params})
async def tool(args):
    # Direct API call (NOT via MCP)
    # Pre-process data (reduce tokens)
    # Return JSON only
```

### 4. Cost Optimization
**Proven strategies:**
- Use Haiku 4.5 (10x cheaper than Sonnet)
- Set max_turns=2-3
- Pre-process data in tools (78K → 2K = 97% savings)
- Block expensive tools (WebSearch = $0.03/call!)
- Use free APIs when possible (Jina Reader)

### 5. Specialist Agents
**One agent, one responsibility:**
- Agent 1: URLs only
- Agent 2: Contacts only
- Agent 3: Emails + LinkedIn only
- (Agent 4): Additional LinkedIn fallback

**Not:**
- Agent 1: URLs + contacts + enrichment (too complex!)

---

## File Organization

```
poc-workflow/
├── template/              # This folder
│   ├── README.md         # This file
│   ├── DEVELOPMENT.md    # Step-by-step guide
│   ├── agent_template.py # Agent template
│   ├── test_template.py  # Test template
│   └── utils/           # Shared utilities
│       ├── env_loader.py
│       └── json_parser.py
│
├── agents/               # Production agents
│   ├── README.md        # Usage docs
│   ├── agent1_url_finder.py
│   ├── agent2_contact_extractor.py
│   └── agent3_contact_enricher.py
│
├── tests/               # Test scripts
│   ├── test_agent1.py
│   ├── test_agent2.py
│   └── test_agent3.py
│
├── results/             # Test outputs
│   └── agent{N}_results.json
│
└── experiments/         # Archive + learnings
    ├── MCP_TOOL_BASELINE.md
    └── agent{N}_testing/
```

---

## Common Patterns

### Pattern A: Email Finder (Hunter.io API)
See: `agents/agent3_contact_enricher.py`
- Cost: $0.0116/contact
- Success: 50%
- Bonus: LinkedIn URLs included

### Pattern B: Web Scraper (Jina Reader)
See: `agents/agent1_url_finder.py`
- Cost: $0.0153/operation
- Success: 100%
- Key: Pre-process 78K → 2K tokens

### Pattern C: Data Extractor (WebFetch)
See: `agents/agent2_contact_extractor.py`
- Cost: $0.0123/operation
- Success: 100%
- Key: Simple, built-in tool

---

## Next Steps

1. Read `DEVELOPMENT.md` for detailed guide
2. Review working agents in `agents/` folder
3. Check `experiments/MCP_TOOL_BASELINE.md` for tool capabilities
4. Start building!

---

## Support

**Issues?** Check:
- `/AGENT_SDK_KNOWLEDGE.md` - Complete SDK docs
- `progress.md` - What we learned building POC
- Working agent files - Real examples

**Questions?** Review the POC agents - they're fully documented and tested.
