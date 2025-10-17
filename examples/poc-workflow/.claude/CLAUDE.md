# Context for Engineers / Claude Sessions

## What We're Building

A two-agent workflow proving the pattern for a 500-agent production system.

**Workflow:** URL Finder → Data Extractor → Structured Output

## Current State

### ✅ Agent 1 Complete (debug_agent.py)

**What it does:** Finds golf course listing URLs from VSGA directory

**Performance:**
- Cost: $0.0153/search (76% under $0.02 budget)
- Accuracy: 100%
- Speed: 3.4s average

**The Winning Pattern:**
```python
# Smart tool - pre-processes data
@tool("fetch", "Get course links", {"url": str})
async def fetch(args):
    content = await get_page()  # 78K chars
    links = extract_only_links(content)  # → 2K chars
    return links  # 97% token reduction!

# Cost-optimized config
ClaudeAgentOptions(
    model="claude-haiku-4-5",  # Cheapest
    max_turns=2,  # Limit iterations
    allowed_tools=["mcp__t__fetch"],  # ONLY what's needed
    disallowed_tools=["Task", "TodoWrite"],  # Block extras
    permission_mode="bypassPermissions"
)
```

**Test Data:**
- 5 course URLs in `results/agent1_test_results.json`
- Ready for Agent 2 input

### 🔄 Agent 2 Next

**Goal:** Extract contact data from course URLs

**Requirements:**
- Input: URL from Agent 1
- Extract: Name, address, phone, email, website
- Cost target: < $0.02
- Use same winning pattern as Agent 1

**Tools to consider:**
- Brightdata MCP (external) - PRO_MODE with 60+ tools
- Custom tool calling Brightdata API
- Playwright for JS rendering (course pages use dynamic content)

## Key Learnings

### What Works

1. **SDK MCP Servers (in-process) > External MCP**
   - No subprocess overhead
   - More reliable
   - Easier debugging

2. **Smart Tools = Cost Savings**
   - Pre-process data in tool
   - Return minimal, focused results
   - 78K → 2K = 97% savings

3. **Haiku 4.5 for Focused Tasks**
   - 10x cheaper than Sonnet
   - Fast and accurate when tools do heavy lifting

4. **max_turns=2-3 Controls Cost**
   - Prevents runaway iterations
   - Predictable costs

### What Doesn't Work

1. ❌ External MCP servers (connection issues)
2. ❌ Using `query()` for MCP (use `ClaudeSDKClient`)
3. ❌ Returning raw large data from tools
4. ❌ Not blocking Task/TodoWrite tools

## File Organization

```
poc-workflow/
├── goal.md                          # This file's parent
├── .claude/CLAUDE.md               # This file
├── progress.md                      # Status tracking
│
├── agents/                          # Production-ready agents
│   └── [working agents]
│
├── tests/                           # Test scripts
│   └── [test scripts]
│
├── results/                         # Test outputs (JSON)
│   └── agent1_test_results.json
│
└── archive/                         # Failed experiments
    └── [old attempts with notes]
```

## How to Continue

1. **Read goal.md** - Understand the mission
2. **Check progress.md** - See what's done
3. **Review results/** - See test data
4. **Read BREAKTHROUGH.md** (in root) - Key learnings
5. **Build next agent** using proven pattern

## Reference Docs

- `/AGENT_SDK_KNOWLEDGE.md` - Complete SDK reference
- `/BREAKTHROUGH.md` - Debugging discoveries
- `debug_agent.py` - Working Agent 1 example
- `agent1_test_results.json` - Real test data

## Cost Targets

- Agent 1: $0.015 avg ✅ (under $0.02)
- Agent 2: $0.015 target
- Full workflow: $0.03 target
- 500 workflows/day: $15/day budget

## Next Engineer: Start Here

1. Review goal.md and progress.md
2. Study debug_agent.py (working Agent 1)
3. Build Agent 2 using same pattern
4. Test with data in results/agent1_test_results.json
5. Update progress.md when done
