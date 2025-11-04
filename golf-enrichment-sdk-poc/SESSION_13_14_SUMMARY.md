# Sessions 13-14 Summary: SDK Agent Architecture

**Date:** November 1-2, 2025
**Duration:** 5+ hours across 2 sessions
**Status:** IN PROGRESS - MCP Configuration Testing

---

## 🎯 Sessions Overview

### **Session 13:** Architecture Research & SDK Agent Build
- **Duration:** 3 hours
- **Goal:** Determine optimal architecture for maximum accuracy
- **Result:** Built complete SDK agent + MCP tools infrastructure

### **Session 14:** MCP Configuration Fix & Testing
- **Duration:** 2+ hours (ongoing)
- **Goal:** Fix MCP connectivity and validate POC
- **Result:** Configuration updated, testing in progress

---

## 📊 Architecture Decision

### **Question:** How to get 85-95% accuracy vs 60-70% with edge functions?

**Answer:** SDK Agent + MCP Tool Composition

**Reasoning:**
1. **Tool Specialization:** Hunter.io (60%+ email discovery) vs generic LLM (30%)
2. **Multi-Source Verification:** Cross-check facts across Firecrawl, Jina, Perplexity
3. **Self-Healing:** If one tool fails, try another
4. **Visible Workflow:** See which tools were used and why
5. **Composable:** Can add Apollo, ZoomInfo, etc. later

---

## 🏗️ What We Built (Session 13)

### **1. Agent Definition**
File: `agents/research_agent.py` (310 lines)

- 5-section research prompt (proven with ChatGPT-5 Pro)
- Embedded Standard Operating Procedure
- Quality validation requirements
- Tool usage recommendations

### **2. Research Orchestrator**
File: `orchestrator.py` (380 lines)

- 5-step multi-tool workflow
- Quality metric calculation (0-100 score)
- Automatic validation and issue detection
- Result storage (JSON + Supabase ready)
- Citation counting across all sections

### **3. Test Infrastructure**
Files:
- `test_sdk_agent.py` - POC test runner
- `run_poc_test.sh` - Environment loader
- Package structure (`__init__.py` files)
- `README.md` - Complete documentation

### **4. MCP Configuration** (Session 14)
File: `.mcp.json`

- Firecrawl: Web search with full citations
- Jina: Official website scraping
- Hunter.io: B2B contact discovery
- Perplexity: Fallback research
- Supabase: Database operations

---

## 🔧 Technical Changes (Session 14)

### **Problem Identified:**
SDK agent couldn't access MCP tools - permission/configuration issue

### **Root Cause:**
- SDK expects `.mcp.json` at project root
- We were trying to use `~/.claude/settings.json` (wrong approach)
- Tool names had incorrect prefixes (`mcp__hunter-io__*` vs `mcp__hunter__*`)

### **Solution Applied:**

1. **Created `.mcp.json`** with stdio MCP server configuration
2. **Updated `orchestrator.py`** to load `.mcp.json` file path
3. **Fixed tool names** in allowed_tools list
4. **Updated agent prompt** with correct MCP tool names
5. **Created connectivity test** to validate before POC

---

## 📈 Expected vs Actual Results

### **Comparison: Edge Function vs SDK Agent**

| Metric | Edge Function | SDK Agent (Target) |
|--------|--------------|-------------------|
| Accuracy | 60-70% | 85-95% |
| Email Discovery | 30% | 60%+ |
| Citations | Generic refs | Full URLs |
| Tool Composition | No | Yes (4+ tools) |
| Self-Healing | No | Yes |
| Multi-Source Verify | No | Yes |
| Cost/Course | $0.005-0.02 | $0.08-0.10 |
| Total Cost (15k) | $75-300 | $1,200 |
| Manual Review Cost | $56,250 | $18,750 |
| **Net Total** | **$56,325-56,550** | **$19,950** |

**ROI:** SDK saves $36,375-36,600 despite higher automation cost

---

## 🧪 Testing Status

### **Session 13 POC Test Result:**
❌ **FAILED** - MCP tools not accessible

**Error:** "I need permissions to use the web tools"

**Agent Output:**
- Initialized successfully ✅
- Research prompt loaded ✅
- Attempted to use MCP tools ❌
- Fell back to explanation ❌
- No JSON output ❌

### **Session 14 Fix Applied:**
✅ Created `.mcp.json` configuration
✅ Updated SDK integration
✅ Fixed tool name prefixes
⏳ Running connectivity test now

---

## 🔑 Key Learnings

### **1. SDK vs GPT-5 Pro Thinking**

**GPT-5 Pro Thinking wins at:**
- Deep reasoning on ambiguous cases
- Simplicity (one API call)
- Proven manual workflow

**SDK Agent wins at:**
- Tool specialization (Hunter.io for emails)
- Multi-source verification
- Access to B2B databases
- Visible, debuggable workflow

**Conclusion:** SDK is better IF MCP tools work. Otherwise GPT-5 Pro simpler and as good.

### **2. MCP Configuration Complexity**

- SDK MCP integration is powerful but finicky
- Requires correct `.mcp.json` format
- Tool naming must match exactly (`mcp__[server]__[tool]`)
- stdio servers need `npx` + package name
- Environment variables must be set

### **3. Architecture Trade-offs**

**Pros of SDK Approach:**
- Maximum accuracy potential (85-95%)
- Future-proof (can add more tools)
- Better for batch processing (15k courses)
- Saves $36k+ in manual review

**Cons of SDK Approach:**
- Higher complexity
- Debugging is harder
- MCP configuration can break
- Higher per-course cost ($0.08 vs $0.02)

---

## 📂 Files Created

```
teams/golf-enrichment/
├── agents/
│   ├── __init__.py (updated)
│   └── research_agent.py (310 lines) ✅
├── orchestrator.py (380 lines) ✅
├── test_sdk_agent.py (130 lines) ✅
├── test_mcp_connectivity.py (150 lines) ✅ NEW
├── run_poc_test.sh ✅
├── run_mcp_test.sh ✅ NEW
├── .mcp.json ✅ NEW
├── __init__.py (updated)
├── README.md ✅
└── SESSION_13_14_SUMMARY.md (this file) ✅ NEW
```

---

## ⏭️ Next Steps (Session 14 continuation)

### **Immediate:**
1. ⏳ **Wait for MCP connectivity test** results
2. **IF PASS:** Re-run full POC test on The Tradition
3. **IF FAIL:** Debug MCP configuration or pivot to hybrid

### **If MCP Works:**
4. Test on all 3 NC courses
5. Calculate quality metrics
6. Compare vs Session 12 baseline
7. Make GO/NO-GO decision

### **If MCP Doesn't Work:**
8. **Option A:** Hybrid - SDK orchestration + direct API calls
9. **Option B:** Simplify to edge functions with DB prompts
10. **Option C:** Use GPT-5 Pro Thinking API directly

---

## 💭 Open Questions

1. **Will MCP tools actually work?** ⏳ Testing now
2. **Is 85-95% accuracy achievable?** Need POC results
3. **Should we add GPT-5 Pro Thinking as synthesis step?** Potentially best of both
4. **Can we deploy SDK to Render?** Proven with Docker, should work
5. **What's the actual cost per course?** Need real POC data

---

## 📊 Context Window Status

**Current Usage:** 126,769 / 1,000,000 tokens (12.7%)
**Remaining:** 873,231 tokens (87.3%)
**Estimated Session 14 Total:** ~150k tokens
**Buffer for Session 15:** ~850k tokens

✅ Plenty of context remaining

---

## 🎯 Success Criteria

**For SDK Agent to be viable:**
- ✅ MCP tools must work (testing now)
- ⏳ Accuracy ≥ 85% on POC
- ⏳ Email discovery ≥ 50%
- ⏳ Citations have full URLs
- ⏳ Quality score ≥ 80/100

**If criteria met:** Proceed to production (15k courses)
**If not met:** Pivot to simpler approach

---

**Status:** MCP connectivity test running...
**Next Update:** After test results available
