---
name: Agent Testing SOP
description: Complete 6-stage methodology for testing AI agents with architecture patterns for agent consolidation, data flow optimization, and production deployment. Covers MCP validation, implementation, database integration, Docker testing, and controlled production rollout. Validates data accuracy, eliminates hallucination, reduces costs through rapid iteration. Use when developing new agents, fixing bugs, optimizing architecture, or validating changes before production.
allowed-tools: Read, Bash, Edit, Write, mcp__firecrawl__firecrawl_search, mcp__firecrawl__firecrawl_scrape, mcp__BrightData__search_engine, mcp__BrightData__scrape_as_markdown, mcp__jina__jina_search, mcp__jina__jina_reader, mcp__perplexity-ask__perplexity_ask, mcp__supabase__execute_sql, mcp__supabase__list_tables
---

# Agent Testing SOP - Local Validation with MCP Tools

**Purpose:** Test AI agents with MCP tools BEFORE writing code. Catch hallucination, validate accuracy, iterate quickly.

**Proven:** This methodology was developed during golf enrichment testing (Oct 20, 2025) and caught 3 critical hallucination/accuracy issues.

---

## 🎯 The Golden Rule

> **"Never write agent code until you've proven it works with MCP tools first."**

**Why:**
- **10x faster iteration:** MCP test in 10s vs agent rebuild in 2min
- **Catch hallucination early:** Found Agent 7 counting creeks as hazards
- **Validate accuracy:** Triple-test with multiple tools
- **Save money:** Free MCP testing vs expensive agent retries
- **High confidence:** Know it works before implementing

---

## 📐 The 6-Stage Testing Process

### **Stage 1: Design Agent Logic**
Define what the agent should do (inputs, outputs, success criteria).

**See:** `STAGE1_DESIGN.md` (placeholder)

### **Stage 2: Test with MCP Tools** ⭐ CRITICAL
Test the concept with MCP tools to prove it works.

**See:** `STAGE2_MCP_TESTING.md`

### **Stage 3: Implement in Agent Code**
Only after MCP validation, write the agent.py file.

**See:** `STAGE3_IMPLEMENT.md` (placeholder)

### **Stage 4: Cross-Validate**
Test agent with 2-3 different tools to ensure consistency.

**See:** `STAGE4_VALIDATE.md` (placeholder)

### **Stage 5: Database Integration** ⭐ NEW!
Validate agents write data correctly using test tables that mirror production.

**See:** `STAGE5_DATABASE_INTEGRATION.md`

### **Stage 6: Docker & Deployment** ⭐ NEW!
Test in Docker container, compare to baseline, deploy to production.

**See:** `STAGE6_DOCKER_TESTING.md`

---

## 🚨 Red Flags (When to Stop and Test More)

**Stop implementing if you see:**
- ❌ Agent returns data you can't verify
- ❌ Results seem too good (100% success on hard tasks)
- ❌ AI is "interpreting" vs extracting facts
- ❌ No way to compare to ground truth
- ❌ Using single source without validation

**Do this instead:**
1. Test with 2-3 different MCP tools
2. Compare results - do they match?
3. Find ground truth (website, official source)
4. Only proceed when validated

---

## ✅ Examples from Golf Enrichment

**See `EXAMPLES.md` for complete case studies:**

### **Example 1: Agent 7 Water Hazards** (Caught Hallucination!)
- **MCP Test:** Perplexity said "8 water hazards" for Brambleton
- **Ground Truth:** SkyGolf says "Scarce" (few hazards)
- **User Validation:** Confirmed SkyGolf is correct
- **Finding:** Perplexity counted creeks, not hazards!
- **Fix:** Switched to SkyGolf database
- **Result:** 100% accurate, $0 cost (was $0.006)

### **Example 2: Agent 4 LinkedIn** (Triple-Validated!)
- **MCP Test A:** Firecrawl found Dustin's LinkedIn ✅
- **MCP Test B:** Jina found same LinkedIn ✅
- **MCP Test C:** BrightData found same LinkedIn ✅
- **Verification:** Scraped profile, confirmed correct person ✅
- **Confidence:** 100% (3 tools agree)
- **Implementation:** Used Firecrawl pattern in agent

### **Example 3: Agent 6 Segmentation** (Caught Wrong Logic!)
- **MCP Test:** Perplexity said Bristow = "Budget"
- **Objective Data:** Weekend fee $75-99 (high-end!)
- **User Validation:** Confirmed it's mid-to-high-end
- **Finding:** AI interpretation unreliable
- **Fix:** Used objective green fees instead
- **Result:** 100% accurate, $0 cost (was $0.037)

### **Example 4: Agent 4/6.5 Consolidation** (Data Already There!)
- **MCP Test:** Firecrawl search descriptions have tenure!
- **Discovery:** Don't need separate LinkedIn scraping
- **Fix:** Agent 4 extracts tenure from search (no Agent 6.5 needed)
- **Result:** 9→8 agents, faster, cheaper, more reliable
- **Validation:** Complete 6-stage testing (MCP → Docker)

---

## 🎓 Lessons Learned

### **What Works:**
- ✅ Testing with MCP tools before coding (10x faster)
- ✅ Cross-validation with 3 tools (catches discrepancies)
- ✅ Ground truth comparison (websites, official sources)
- ✅ Objective data over AI interpretation (fees > Perplexity)
- ✅ User validation (domain expert confirms accuracy)

### **What Doesn't Work:**
- ❌ Trusting single AI source (Perplexity hallucinated)
- ❌ Implementing before testing (wasted time on Agent 6.5)
- ❌ Subjective AI reasoning for facts (Agent 6 segmentation)
- ❌ Skipping validation (would have deployed wrong data)

---

## 📚 Quick Reference

**When to use this skill:**
- Designing new agent
- Fixing agent bug
- Validating agent accuracy
- Switching data sources
- Before Docker testing

**Time investment:**
- Stage 2 MCP testing: 10-30 minutes
- Saves: Hours of debugging later
- ROI: 10x time savings

**Cost:**
- MCP testing: Usually free or <$0.10
- Saves: Expensive agent retries

---

## 📚 Supporting Documentation

**Stage-Specific Guides:**
- `STAGE2_MCP_TESTING.md` - MCP validation methodology ⭐ CRITICAL
- `STAGE5_DATABASE_INTEGRATION.md` - Database testing with test tables
- `STAGE6_DOCKER_TESTING.md` - Docker validation & deployment

**Design & Architecture:**
- `ARCHITECTURE_PATTERNS.md` - Agent design patterns (consolidation, specialization, data reuse) ⭐ NEW!

**Real Examples:**
- `EXAMPLES.md` - 4 case studies from golf enrichment

**Placeholders (to be created):**
- `STAGE1_DESIGN.md` - Agent design principles
- `STAGE3_IMPLEMENT.md` - Implementation patterns
- `STAGE4_VALIDATE.md` - Cross-validation strategies

---

**For detailed instructions, see the stage-specific files above.**
