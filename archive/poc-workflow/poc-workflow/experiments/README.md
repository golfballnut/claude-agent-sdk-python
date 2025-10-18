# Experiments & Learning Archive

This directory contains experimental code and failed attempts. Each file taught us something important.

## What Worked

### simple_workflow.py
- ✅ First working multi-agent example
- ✅ Proved agents + custom tools work
- **Lesson:** Calculator example is too simple for real-world use

### jina_custom_scraper.py
- ✅ In-process custom tools calling Jina API
- ✅ MCP server connected successfully
- **Lesson:** Custom tools more reliable than external MCP for simple APIs

## What Didn't Work (But Taught Us)

### jina_scraper.py
- ❌ External Jina MCP server connection failures
- **Lesson:** External MCP servers unreliable, use SDK MCP instead

### agent1_jina.py
- ❌ Cost $1.00+, hallucinations, token overflow
- **Lesson:** Need smart tools that pre-process data

### agent1_brightdata.py
- ❌ Agents asked for permission instead of executing
- **Lesson:** Need `bypassPermissions` mode

### agent1_lean.py
- ❌ Still too expensive ($0.03-0.04)
- **Lesson:** Need Haiku model, not Sonnet

### agent1_ultra_lean.py
- ⚠️ Got cheap ($0.0199) but agent gave up on large pages
- **Lesson:** Need smart tools AND persistence

### two_agent_*.py files
- ⚠️ Agents worked but used wrong tools
- **Lesson:** Need strict allowed_tools + disallowed_tools

## Key Breakthroughs

Each experiment contributed to the final pattern:

**Final Pattern (see agents/agent1_url_finder.py):**
1. Smart tool (pre-process data)
2. SDK MCP server (in-process)
3. Haiku 4.5 model
4. max_turns=2
5. Strict tool restrictions
6. Clear system prompt

**Results:**
- $0.0153/search (76% under budget)
- 100% accuracy
- 3.4s average

## Don't Delete These Files

They document our learning process and prevent repeating mistakes.

## Reference

See `/BREAKTHROUGH.md` for detailed debugging sessions.
