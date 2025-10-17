# SDK Agent Development Guide

**Purpose:** Step-by-step guide for building production-ready Claude SDK agents
**Based on:** Proven patterns from Agents 1, 2, 3 (POC workflow)

---

## Quick Start (5 Minutes)

```bash
# 1. Copy template
cp template/agent_template.py agents/agent{N}_{name}.py

# 2. Copy test
cp template/test_template.py tests/test_agent{N}.py

# 3. Replace placeholders
# {N}, {name}, {agent_function}, {tool_name}, etc.

# 4. Implement tool logic

# 5. Test
python agents/agent{N}_{name}.py        # Demo
python tests/test_agent{N}.py           # Full test
```

---

## Step-by-Step Development Process

### Step 1: Define Agent Purpose (10 min)

**Questions to answer:**
- What ONE thing does this agent do? (stay focused!)
- What input does it need?
- What output does it provide?
- What's the success criteria?

**Document in agent docstring:**
```python
"""
Agent {N}: {Name} ({Specialist})
{One clear sentence}

Performance Targets:
- Success Rate: {X}%
- Cost: < ${X}
- Speed: < {X}s

Data Quality Rule: No guessing - nulls if not found
"""
```

### Step 2: Test MCP Tools via Claude Code (30-60 min)

**CRITICAL:** Test tools in Claude Code BEFORE building SDK agent!

**Why:**
- Claude Code has MCP servers configured
- SDK agents run in subprocess (no MCP servers)
- Testing establishes baseline of what's possible

**Process:**
1. Open Claude Code
2. Test each tool manually with real data
3. Document: success rate, cost, what data returned
4. Choose winning tool(s)

**Example:**
```
# In Claude Code:
Use mcp__hunter-io__Email-Finder to find email for "John Doe" at "example.com"

# Document result:
- Found: john.doe@example.com
- Confidence: 95%
- Bonus: linkedin_url included!
- Cost: ~1 credit
```

**Save findings to:** `experiments/mcp_{tool}_baseline.md`

### Step 3: Design Custom SDK Tool (20 min)

**SDK agents can't use MCP tools directly!**

Solution: Build custom tool that replicates MCP tool behavior via direct API calls.

**Template:**
```python
@tool("tool_name", "Description", {"param": str})
async def tool_name_tool(args):
    # Load API key
    load_project_env()
    api_key = get_api_key("API_KEY_NAME")

    # Call API directly (not via MCP)
    async with httpx.AsyncClient() as client:
        r = await client.get(api_url, params={...})
        data = r.json()

    # Extract and return
    return {"content": [{"type": "text", "text": json.dumps(results)}]}
```

**Key Principles:**
- ✅ Return JSON only (no markdown)
- ✅ Return nulls if not found (no guessing!)
- ✅ Use direct API calls (not MCP tools)
- ✅ Handle errors gracefully

### Step 4: Build Agent (30 min)

**Use template:**
1. Copy `template/agent_template.py` → `agents/agent{N}_{name}.py`
2. Replace all `{placeholders}`
3. Implement custom tool logic
4. Configure options (model, max_turns, allowed_tools)
5. Add demo in `main()`

**Configuration checklist:**
- [ ] `model="claude-haiku-4-5"` (cheapest)
- [ ] `max_turns=2` (cost control)
- [ ] `allowed_tools=["mcp__{server}__{tool}"]` (only what's needed)
- [ ] `disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"]`
- [ ] `permission_mode="bypassPermissions"` (testing only)

### Step 5: Test Single Case (15 min)

**Run demo:**
```bash
python agents/agent{N}_{name}.py
```

**Verify:**
- ✅ Tool loads correctly
- ✅ API calls work
- ✅ Returns expected JSON structure
- ✅ Nulls returned (not guesses) when data missing
- ✅ Cost is reasonable

### Step 6: Build Batch Test (20 min)

**Use template:**
1. Copy `template/test_template.py` → `tests/test_agent{N}.py`
2. Define test cases
3. Set ground truth (if applicable)
4. Configure success criteria

**Run:**
```bash
python tests/test_agent{N}.py
```

**Track:**
- Success rate
- Average cost
- Total cost
- Edge cases / failures

### Step 7: Optimize (Variable)

**If tests fail criteria:**

**Too expensive?**
- Try cheaper model (Haiku vs Sonnet)
- Reduce max_turns
- Optimize tool (pre-process more data)
- Cache results

**Low success rate?**
- Add fallback methods (but return nulls, don't guess!)
- Try different API/tool
- Improve search queries
- Better data extraction

**Too slow?**
- Use SDK MCP server (not external)
- Parallel processing for batch
- Reduce timeout values

### Step 8: Document & Commit (10 min)

**Update docs:**
- `agents/README.md` - Add agent description
- `progress.md` - Mark complete, add metrics
- `goal.md` - Update workflow if needed

**Commit:**
```bash
git add -A
git commit -m "feat: Agent {N} complete - {description}"
git push
```

---

## Best Practices (Learned from POC)

### ✅ DO:

1. **Test MCP tools in Claude Code first** - Establishes baseline
2. **Use custom SDK tools** - More reliable than MCP routing
3. **Return honest nulls** - Never guess or use fallbacks
4. **Keep tools focused** - One tool, one purpose
5. **Use Haiku 4.5** - 10x cheaper than Sonnet, works great with good tools
6. **Limit max_turns** - Prevents runaway costs
7. **Block unnecessary tools** - Explicitly disallow Task, TodoWrite, etc.
8. **Pre-process in tools** - Return minimal data to agent (saves tokens)
9. **Use SDK MCP servers** - In-process is faster than external
10. **Track costs religiously** - ResultMessage.total_cost_usd

### ❌ DON'T:

1. **Don't use external MCP servers** - Subprocess overhead, connection issues
2. **Don't use `query()` for MCP** - Use `ClaudeSDKClient` instead
3. **Don't return raw large data** - Pre-process in tool first
4. **Don't guess missing data** - Return null instead
5. **Don't skip MCP testing** - You'll waste time building wrong thing
6. **Don't use WebSearch in SDK** - Expensive ($0.03/call)
7. **Don't assume MCP tools available** - SDK subprocess has mcp_servers: []
8. **Don't use fallback emails** - "info@domain" is not reliable
9. **Don't build Agent 4 before testing Agent 3** - Might be unnecessary!
10. **Don't skip batch testing** - Single case success != production ready

---

## Proven Patterns

### Pattern 1: API-Powered Tool (Agent 3)

**When:** You need external data (Hunter.io, BrightData, etc.)

**Structure:**
```python
@tool("tool_name", "desc", {params})
async def tool(args):
    load_project_env()
    api_key = get_api_key("KEY_NAME")

    # Direct API call
    async with httpx.AsyncClient() as client:
        r = await client.get(api_url, params={..., "api_key": api_key})
        data = r.json()

    # Extract, return JSON
    return {"content": [{"type": "text", "text": json.dumps(results)}]}
```

**Cost:** Variable (API pricing)
**Success:** High (if API has data)

### Pattern 2: Web Scraping Tool (Agent 1, Agent 2)

**When:** You need to extract data from web pages

**Structure:**
```python
@tool("scrape", "desc", {params})
async def tool(args):
    # Use Jina Reader (free)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://r.jina.ai/{url}")
        content = r.text

    # Extract ONLY what you need (regex, parsing)
    # 78K → 2K = 97% token savings!
    extracted = extract_relevant_data(content)

    return {"content": [{"type": "text", "text": extracted}]}
```

**Cost:** Low (Jina is free/cheap)
**Success:** High for static content

### Pattern 3: Built-in Tool (Agent 2)

**When:** WebFetch is enough (no pre-processing needed)

**Structure:**
```python
# No custom tool!
options = ClaudeAgentOptions(
    allowed_tools=["WebFetch"],
    system_prompt="Use WebFetch to get {url}. Extract {data}. Return JSON."
)
```

**Cost:** Very low
**Success:** Good for simple extraction

---

## Debugging Checklist

**Agent not finding data?**
- [ ] Tested MCP tool in Claude Code first?
- [ ] API key loaded? (`get_api_key()` returns value?)
- [ ] API call succeeding? (check response status)
- [ ] JSON parsing working? (print raw tool output)
- [ ] Agent actually using your tool? (check `tools_used`)

**Cost too high?**
- [ ] Using Haiku 4.5?
- [ ] max_turns set low (2-3)?
- [ ] Tool pre-processing data?
- [ ] Blocking expensive tools (WebSearch)?

**Agent hallucinating?**
- [ ] Tool returns structured data?
- [ ] System prompt clear?
- [ ] allowed_tools restrictive enough?

---

## Cost Targets

Based on proven agents:

| Agent Type | Target Cost | Actual (POC) |
|------------|-------------|--------------|
| URL Finder | < $0.02 | $0.0153 ✅ |
| Data Extractor | < $0.02 | $0.0123 ✅ |
| Contact Enricher | < $0.02 | $0.0116 ✅ |
| Per Contact | < $0.02 | $0.0116 ✅ |
| Per Course (2.4 contacts) | < $0.05 | $0.0392 ✅ |

**Rule of thumb:** If agent > $0.03, optimize or reconsider approach

---

## File Naming Conventions

**Agents:** `agent{N}_{purpose}.py`
- `agent1_url_finder.py`
- `agent2_contact_extractor.py`
- `agent3_contact_enricher.py`

**Tests:** `test_agent{N}.py`
- `test_agent1.py`
- `test_agent2.py`
- `test_agent3.py`

**Results:** `agent{N}_results.json`
- One results file per agent
- Contains all test outputs

---

## Next Steps After Building Agent

1. Update `agents/README.md` with usage
2. Update `progress.md` with metrics
3. Add to workflow in `goal.md`
4. Archive experiments in `experiments/agent{N}_testing/`
5. Commit and push
6. Build next agent or orchestrator

---

## Questions?

Review:
- `/AGENT_SDK_KNOWLEDGE.md` - Complete SDK reference
- `experiments/MCP_TOOL_BASELINE.md` - Tool capabilities
- Working agents in `agents/` - Real examples
- `progress.md` - What we learned
