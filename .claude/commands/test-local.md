Invoke the **golf-orchestrator** subagent to test golf enrichment locally for Course {{course_id}}.

This establishes the "baseline" - what we EXPECT Docker to produce.

**The golf-orchestrator subagent will:**
1. Query Course {{course_id}} from Supabase (get exact name)
2. Run all 8 agents locally using Claude Code MCP (not Docker)
3. Save baseline to `tests/baselines/course_{{course_id}}_baseline.json`
4. Display expected results (cost, contacts, segment, water hazards)
5. Provide Docker test command for next step

**Why Local Testing First:**
- ⚡ **Fast:** 45 seconds vs 2-3 minutes in Docker
- 💰 **Free:** No Docker overhead, uses local API keys
- 🎯 **Ground truth:** Establishes expected behavior
- 🐛 **Easy debugging:** Full visibility into agent execution
- ✅ **POC validation:** Prove it works before containerizing

**After Baseline Created:**
1. Run Docker test with same course_id
2. Use golf-docker-validator subagent to compare
3. Only deploy if Docker matches baseline

**Usage:** `/test-local {{course_id}}`

**Examples:**
- `/test-local 93` - Test Westlake Golf and Country Club
- `/test-local 98` - Test next course in sequence
- `/test-local 103` - Test another course
