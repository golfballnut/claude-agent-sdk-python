# Breakthroughs & Debugging Sessions

This document captures critical debugging breakthroughs and lessons learned while building the 500-agent system.

---

## 2025-10-16 - Agent 1: Smart Tools + Cost Optimization

### 🔴 Problem

Building Agent 1 (URL Finder) with these issues:
- **High cost:** $0.10-$1.00+ per search (target: $0.02)
- **Hallucinations:** Agents returning wrong/made-up URLs
- **Tool restrictions not working:** Agents using Task, TodoWrite, Grep despite being disallowed
- **Token overflows:** 78K character pages overwhelming Claude
- **Permission prompts:** Agents asking for permission instead of executing

### 🔍 Investigation

**Attempts that failed:**
1. External Jina MCP server → Connection failures (`status: 'failed'`)
2. External Brightdata MCP server → Connection succeeded but agents asked for permission
3. Using `query()` function → Limited MCP support
4. Various model IDs → Wrong format caused 404 errors
5. Tool restrictions → Agents ignored allowed_tools, used everything

**What we tried:**
- Different MCP packages (`@jina-ai/mcp-server-jina` vs `jina-mcp-tools`)
- Different permission modes (`acceptEdits` vs `bypassPermissions`)
- Different models (Sonnet vs Haiku, various date versions)
- Custom tools vs external MCP servers
- Various prompt engineering approaches

### 💡 Breakthrough

**Three critical discoveries:**

#### 1. Tools Must Pre-Process Data
```python
# ❌ Returns 78,000 characters
@tool("fetch", "Fetch page", {"url": str})
async def fetch(args):
    content = await get_page()
    return {"content": [{"type": "text", "text": content}]}  # 78K chars!

# ✅ Returns ~2,000 characters
@tool("fetch", "Get course links", {"url": str})
async def fetch(args):
    content = await get_page()  # 78K chars

    # Extract ONLY what's needed
    links = re.findall(r'pattern', content)  # Filter to 292 links
    formatted = format_links(links)  # ~2K chars

    return {"content": [{"type": "text", "text": formatted}]}
```

**Impact:** 97% token reduction (78K → 2K)

#### 2. Model Selection Matters
```python
# ❌ Wrong model formats
model="claude-3-5-haiku-20241022"  # 404 error
model="claude-3-5-haiku-20250110"  # 404 error

# ✅ Correct format
model="claude-haiku-4-5"  # Works!

# Also valid:
model="claude-sonnet-4-5"
model="claude-opus-4-1"
```

#### 3. Cost Control Configuration
```python
options = ClaudeAgentOptions(
    max_turns=2,  # Limit iterations
    model="claude-haiku-4-5",  # Cheapest model
    permission_mode="bypassPermissions",  # No asking
    allowed_tools=["mcp__t__fetch"],  # ONLY what's needed
    disallowed_tools=["Task", "TodoWrite", "Grep", "Glob"]  # Block extras
)
```

### ✅ Solution

**The Winning Pattern:**

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions

# 1. Smart tool with data pre-processing
@tool("fetch", "Get golf course links", {"url": str})
async def fetch(args):
    import httpx, re

    # Fetch full page
    r = await httpx.AsyncClient().get(f"https://r.jina.ai/{args['url']}")
    content = r.text  # 78K characters

    # Extract ONLY course links
    links = re.findall(
        r'\[Club Name ([^\]]+)\]\((https://vsga\.org/courselisting/\d+[^\)]*)\)',
        content
    )

    # Return formatted, minimal data
    result = "\n".join([f"{name}: {url}" for name, url in links])
    return {"content": [{"type": "text", "text": result}]}

# 2. Create SDK MCP server (in-process, no subprocess)
server = create_sdk_mcp_server("t", tools=[fetch])

# 3. Configure for cost and accuracy
options = ClaudeAgentOptions(
    mcp_servers={"t": server},
    allowed_tools=["mcp__t__fetch"],
    disallowed_tools=["Task", "TodoWrite", "Grep", "Glob"],
    permission_mode="bypassPermissions",
    max_turns=2,
    model="claude-haiku-4-5",
    system_prompt="Use fetch to get https://vsga.org/member-clubs. Find the course and return ONLY its URL."
)

# 4. Execute with ClaudeSDKClient (streaming mode required for MCP)
async with ClaudeSDKClient(options=options) as client:
    await client.query("Find URL for: [course name]")
    async for msg in client.receive_response():
        # Process messages
```

### 📊 Impact

**Performance:**
- ✅ **Cost:** $0.0153 avg/course (24% under $0.02 target)
- ✅ **Accuracy:** 100% (5/5 correct URLs found)
- ✅ **Speed:** 3.4s avg per course
- ✅ **Reliability:** Tool restrictions work, no hallucinations

**Scalability:**
- $0.0153 × 500 courses = **$7.65 to process 500 courses**
- $0.0153 × 10,000 courses = **$153 for 10K courses**
- Sustainable at scale!

### 🎯 Pattern for Future Agents

**Template for all future agents:**

```python
# STEP 1: Design smart tools
@tool("tool_name", "What it does", {schema})
async def smart_tool(args):
    # Fetch/get raw data
    raw_data = await get_data()

    # Process/filter BEFORE returning
    processed = extract_only_relevant(raw_data)

    # Return minimal, focused data
    return {"content": [{"type": "text", "text": processed}]}

# STEP 2: Use SDK MCP servers (not external)
server = create_sdk_mcp_server("name", tools=[smart_tool])

# STEP 3: Configure for cost
options = ClaudeAgentOptions(
    mcp_servers={"name": server},
    allowed_tools=["mcp__name__tool"],  # Specific
    disallowed_tools=["Task", "TodoWrite"],  # Block management tools
    permission_mode="bypassPermissions",
    max_turns=2-3,  # Limit iterations
    model="claude-haiku-4-5",  # Cheapest
    system_prompt="Clear, direct task description"
)

# STEP 4: Use ClaudeSDKClient (not query())
async with ClaudeSDKClient(options=options) as client:
    await client.query("Direct, simple question")
    async for msg in client.receive_response():
        process(msg)
```

### ⚠️ What Doesn't Work

**Anti-patterns to avoid:**

1. **❌ Returning raw data from tools**
   - 78K chars → token overflow
   - High cost, slow performance

2. **❌ Using `query()` for MCP servers**
   - Limited MCP support
   - Use `ClaudeSDKClient` instead

3. **❌ External MCP servers for simple tasks**
   - Subprocess overhead
   - Connection failures
   - Use SDK MCP servers instead

4. **❌ Sonnet when Haiku works**
   - Haiku is 10x cheaper
   - Use Sonnet only when needed

5. **❌ Not setting max_turns**
   - Agents can loop indefinitely
   - Set max_turns=2-3 for cost control

### 📁 Files Created

```
examples/poc-workflow/
├── debug_agent.py              # Working Agent 1 implementation
├── agent1_batch_test.py        # Batch testing framework
└── agent1_test_results.json    # 5 course URLs for Agent 2 testing

AGENT_SDK_KNOWLEDGE.md          # Comprehensive SDK reference
BREAKTHROUGH.md                 # This file
```

---

## Next Breakthrough

_[Space for Agent 2 learnings]_

---

## Questions Answered

**Q: Is the agent using MCP tools?**
**A:** Yes! Using SDK MCP tools (in-process) with `mcp__t__fetch` tool name.

**Q: Why SDK MCP vs external MCP?**
**A:**
- ✅ No subprocess overhead
- ✅ More reliable (no connection failures)
- ✅ Easier debugging
- ✅ Same MCP protocol
- ✅ Better for 500-agent system

**Q: Why Haiku instead of Sonnet?**
**A:**
- 10x cheaper ($0.015 vs $0.10+ per task)
- Fast enough for focused tasks
- Works great when tools do the heavy lifting

**Q: How to scale to 500 agents?**
**A:**
- Each agent: One SDK MCP server with smart tools
- Shared infrastructure: One deployment, agent registry
- Cost per workflow: $0.015 (Agent 1) + $0.015 (Agent 2) = $0.03
- 500 workflows/day = $15/day = $450/month (sustainable!)
