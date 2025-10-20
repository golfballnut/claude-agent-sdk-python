# Stage 2: MCP Tool Testing (The Critical Stage!)

**Purpose:** Test agent logic with MCP tools BEFORE writing agent code.

**This is THE MOST IMPORTANT STAGE** - catches hallucination, validates accuracy, saves hours of debugging.

---

## Why Stage 2 Matters

**Without MCP Testing (The Old Way):**
```
Design agent → Write code → Test in Docker → Find issues → Debug → Rebuild (2 min) → Repeat
Result: Hours wasted, expensive iteration, low confidence
```

**With MCP Testing (The Framework Way):**
```
Design agent → Test with MCP (10 sec) → Validate → THEN write code → Works first time!
Result: 10x faster, proven before coding, high confidence
```

---

## The MCP Testing Process

### **Step 1: Identify What to Test**

**For each agent, define:**
- Input data (what it receives)
- Processing method (what tool/API it uses)
- Output data (what it should return)
- Success criteria (how to validate)

**Example: Agent 4 (LinkedIn Finder)**
```
Input: Contact name, title, company
Processing: Search web for LinkedIn profile
Output: LinkedIn URL or NULL
Success: Find correct person's profile
```

### **Step 2: Test with Primary MCP Tool**

**Choose the tool the agent will eventually use:**

```bash
# Agent will use Firecrawl → Test Firecrawl MCP first
mcp__firecrawl__firecrawl_search(
    query="Dustin Betthauser Manager Brambleton Golf LinkedIn",
    limit=5
)

# Result: Found linkedin.com/in/dustin-betthauser ✅
# Confidence: It works! Can proceed to implementation
```

### **Step 3: Cross-Validate with 2nd Tool**

**Test same query with different tool:**

```bash
# Validate Firecrawl result with Jina
mcp__jina__jina_search(
    query="Dustin Betthauser Manager site:linkedin.com",
    count=5
)

# Result: Same URL found ✅
# Confidence: HIGH - two independent tools agree
```

### **Step 4: Verify with 3rd Tool (Optional)**

**For critical data, test with 3rd tool:**

```bash
# Triple-validate with BrightData
mcp__BrightData__search_engine(
    query="Dustin Betthauser Brambleton LinkedIn"
)

# Result: Same URL again ✅
# Confidence: 100% - three tools agree!
```

### **Step 5: Validate Result Accuracy**

**Scrape the result and verify it's correct:**

```bash
# Verify the LinkedIn profile is the right person
mcp__BrightData__scrape_as_markdown(
    url="https://www.linkedin.com/in/dustin-betthauser"
)

# Check:
# - Name matches ✅
# - Company matches (Brambleton/NVRPA) ✅
# - Title matches (Park Manager) ✅
# - It's the correct person! ✅
```

---

## Real Example: Agent 7 Water Hazards

### **Initial MCP Test (Caught Hallucination!)**

**Test A: Perplexity**
```bash
mcp__perplexity-ask__perplexity_ask([{
    "role": "user",
    "content": "How many water hazards on Brambleton Golf Course Virginia?"
}])

# Result: "8 water hazards" (six on front nine, two on back)
# Source: Official NOVA Parks site
```

**Test B: SkyGolf Database**
```bash
mcp__firecrawl__firecrawl_search(
    query="Brambleton Golf Course site:skygolf.com"
)

# Found: smclubsg.skygolf.com/courses/course/15901/
# Scrape it:

mcp__BrightData__scrape_as_markdown(url)

# Result: "Water Hazards: Scarce"
```

**Test C: User Validation**
```
User (knows the course): "Scarce is accurate"
```

**FINDING:** Perplexity counted creeks/streams (not real hazards!)
**DECISION:** Use SkyGolf instead
**IMPACT:** 100% accurate, $0 cost (vs $0.006), no hallucination

---

## Cross-Validation Matrix

**Use this checklist for every agent:**

| Tool/Source | Result | Match? | Notes |
|-------------|--------|--------|-------|
| Primary Tool | ___ | - | Main tool agent will use |
| Validation Tool | ___ | ✅/❌ | 2nd independent source |
| Ground Truth | ___ | ✅/❌ | Official source, user knowledge |

**If all 3 match → Confidence: 100%**
**If 2/3 match → Investigate discrepancy**
**If all differ → Don't trust any, find better source**

---

## MCP Tools by Use Case

### **Web Search:**
- `mcp__firecrawl__firecrawl_search` - Fast, reliable
- `mcp__jina__jina_search` - Good for LinkedIn
- `mcp__BrightData__search_engine` - Google SERP

### **Web Scraping:**
- `mcp__BrightData__scrape_as_markdown` - Anti-bot, best for complex sites
- `mcp__firecrawl__firecrawl_scrape` - Clean markdown output
- `mcp__jina__jina_reader` - Free, simple, good for public pages

### **AI-Powered Search:**
- `mcp__perplexity-ask__perplexity_ask` - Good for aggregation, but validate!

### **Email/Contact:**
- `mcp__hunter-io__Email-Finder` - Professional emails
- `mcp__hunter-io__Domain-Search` - Company emails

### **Database:**
- `mcp__supabase__execute_sql` - Query for ground truth

---

## Testing Checklist

**Before implementing any agent:**

- [ ] Tested primary tool with MCP
- [ ] Cross-validated with 2nd tool
- [ ] Compared to ground truth
- [ ] User validated result (if domain expert available)
- [ ] Documented which tools work best
- [ ] Identified success rate (realistic expectations)
- [ ] Measured cost (via MCP usage)
- [ ] Confirmed no hallucination

**Only implement agent code after all checkboxes ✅**

---

## Time & Cost Estimates

**MCP Testing Phase:**
- Simple agent (URL finder): 10-15 minutes
- Complex agent (enrichment): 20-30 minutes
- Critical agent (segmentation): 30-45 minutes

**Savings:**
- Avoided debugging: 1-3 hours per agent
- Avoided wrong deployments: Priceless
- ROI: 10-20x time savings

---

## Common Pitfalls

### **Pitfall 1: Trusting Single AI Source**
❌ **Don't:** Query Perplexity once, assume it's right
✅ **Do:** Cross-validate with objective source (website, database)

**Example:** Agent 7 Perplexity said "8 hazards", SkyGolf said "Scarce" → SkyGolf was right!

### **Pitfall 2: Implementing Without Testing**
❌ **Don't:** Write agent code, hope MCP tools work the same
✅ **Do:** Test MCP tools first, prove they work, THEN implement

**Example:** Agent 6.5 LinkedIn scraping - should have tested BrightData MCP thoroughly first

### **Pitfall 3: Accepting Vague Results**
❌ **Don't:** Perplexity says "several holes" → Agent returns 7 (guessed!)
✅ **Do:** Demand specific data or return NULL (no guessing!)

**Example:** Agent 7 had "several holes" → 7 guessing logic. DELETED!

---

## Success Stories

**Agent 4 (LinkedIn):**
- MCP tested: 3 tools, all found same URL
- Implemented: Used Firecrawl pattern
- Result: 50% success, accurate
- Time saved: Worked first try (no debugging)

**Agent 7 (Water Hazards):**
- MCP caught: Perplexity hallucination
- MCP validated: SkyGolf accurate
- Implemented: SkyGolf scraping
- Result: 100% accurate, free

**Agent 6 (Segmentation):**
- MCP caught: Perplexity wrong (said "Budget")
- MCP found: SkyGolf has green fees
- Implemented: Fee-based logic
- Result: 100% accurate, free

**Pattern:** MCP testing caught 3 major issues before Docker!

---

## Next Steps

**After completing Stage 2 MCP testing:**
1. Document which tools worked best
2. Note success rate and cost
3. Proceed to Stage 3 (implement agent code)
4. Use exact same tools/patterns that MCP validated

**See other stage files for detailed instructions.**
