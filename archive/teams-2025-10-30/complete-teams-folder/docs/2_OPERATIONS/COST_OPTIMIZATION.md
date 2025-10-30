# Cost Optimization - Golf Course Enrichment System

**Last Updated:** October 18, 2024
**Current Cost:** $0.18-0.28 per course
**Target:** < $0.25 per course
**Status:** Optimization opportunities identified

---

## 💰 **Current Cost Breakdown (Per Course)**

### **Production Test Results:**

| Course | Contacts | Step 2 | Step 3 | Step 4 | Total | Target Met? |
|--------|----------|--------|--------|--------|-------|-------------|
| Country Club of Virginia | 7 | $0.02 | $0.017 | $0.2767 | **$0.3137** | ❌ 25% over |
| Belmont Country Club | 4 | $0.02 | $0.017 | $0.1761 | **$0.2131** | ✅ 15% under |

**Key Finding:** Cost directly correlates with contact count!

---

## 📊 **Detailed Step 4 (Agent) Cost Analysis**

### **Fixed Costs (Per Course):**

```
Agent 1 (URL Finder):         $0.0200
Agent 2 (Data Extractor):     $0.0060
Agent 6 (Course Intel):       $0.0360
Agent 7 (Water Hazards):      $0.0060  (included in Agent 6)
─────────────────────────────────────
Course-Level Subtotal:        $0.0620
```

### **Variable Costs (Per Contact):**

```
Agent 3 (Email + LinkedIn):   $0.0114  per contact
Agent 5 (Phone):              $0.0112  per contact
Agent 6.5 (Background):       $0.0096  per contact
─────────────────────────────────────
Per-Contact Subtotal:         $0.0322  per contact
```

### **Total Cost Formula:**

```
Total = $0.0620 + ($0.0322 × contact_count)

Examples:
3 contacts: $0.0620 + ($0.0322 × 3) = $0.1586 ✅
4 contacts: $0.0620 + ($0.0322 × 4) = $0.1908 ✅
5 contacts: $0.0620 + ($0.0322 × 5) = $0.2230 ✅
6 contacts: $0.0620 + ($0.0322 × 6) = $0.2552 ⚠️
7 contacts: $0.0620 + ($0.0322 × 7) = $0.2874 ❌
```

**Break-Even Point:** 5 contacts max to stay under $0.25

---

## 🎯 **Optimization Strategies**

### **Strategy 1: Contact Filtering** ⭐ **HIGH PRIORITY**

**Problem:** 7+ contacts blow the budget

**Solution:** Prioritize key decision-makers only

```python
# In orchestrator.py
PRIORITY_TITLES = [
    'general manager', 'gm',
    'director of golf', 'dog',
    'head golf professional', 'head pro',
    'superintendent', 'super'
]

def filter_contacts(contacts: list) -> list:
    """Keep only top 4 decision-makers"""
    # Sort by title priority
    priority_contacts = []
    other_contacts = []

    for contact in contacts:
        title_lower = contact['title'].lower()
        if any(pt in title_lower for pt in PRIORITY_TITLES):
            priority_contacts.append(contact)
        else:
            other_contacts.append(contact)

    # Take top 4: all priority, then fill with others if needed
    return (priority_contacts + other_contacts)[:4]
```

**Savings:**
- 7 contacts → 4 contacts = 3 × $0.0322 = **$0.0966 saved**
- New cost: $0.2874 - $0.0966 = **$0.1908** ✅ Under target!

**Implementation:**
- Update `teams/golf-enrichment/orchestrator.py`
- Add filter before contact enrichment loop
- Test with Country Club of Virginia (should drop to ~$0.19)

**Time to Implement:** 30 minutes

---

### **Strategy 2: Optimize Agent 6 Queries** ⭐ **MEDIUM PRIORITY**

**Problem:** Agent 6 makes 4 Perplexity API calls

**Current:**
```python
# 4 separate queries
query1 = water_hazards_query_1()  # $0.006
query2 = water_hazards_query_2()  # $0.006
query3 = company_intel_query()     # $0.012
query4 = competitive_query()       # $0.012
# Total: $0.036
```

**Optimized:**
```python
# 2 combined queries
combined_query_1 = """
Find:
1. Water hazard count (specific number)
2. Company size, budget signals, recent investments
3. Practice range details
"""  # $0.012

combined_query_2 = """
Find:
1. Competitive positioning
2. Member satisfaction signals
3. Opportunity indicators
"""  # $0.012
# Total: $0.024
```

**Savings:** $0.036 - $0.024 = **$0.012 per course**

**Implementation:**
- Update `teams/golf-enrichment/agents/agent6_course_intelligence.py`
- Combine queries while maintaining output quality
- Test segmentation accuracy remains > 90%

**Time to Implement:** 1-2 hours

---

### **Strategy 3: Make Agent 6.5 Selective** ⭐ **MEDIUM PRIORITY**

**Problem:** Contact background costs $0.0096 per contact, low ROI for some roles

**Current:** Enrich all contacts (even assistants)

**Optimized:**
```python
# Only enrich GM and Directors with background
VIP_ROLES = ['general manager', 'director of golf', 'head professional']

for contact in contacts:
    # Basic enrichment (email, phone) for all
    contact = await agent3_enrich(contact)
    contact = await agent5_phone(contact)

    # Background enrichment only for VIPs
    if any(role in contact['title'].lower() for role in VIP_ROLES):
        contact = await agent65_background(contact)
    else:
        contact['tenure_years'] = None
        contact['previous_clubs'] = []
```

**Savings (Example with 7 contacts, 3 VIPs):**
- Current: 7 × $0.0096 = $0.0672
- Optimized: 3 × $0.0096 = $0.0288
- **Savings:** $0.0384 per course

**Combined with Strategy 1:**
- Filter to 4 contacts (2 VIPs, 2 others)
- Only enrich 2 VIP backgrounds
- **Savings:** 5 × $0.0096 = $0.048

**Implementation:**
- Update `teams/golf-enrichment/orchestrator.py`
- Add VIP detection logic
- Test with various contact mixes

**Time to Implement:** 30 minutes

---

### **Strategy 4: Parallel Contact Enrichment** ⭐ **TIME OPTIMIZATION**

**Problem:** Sequential processing is slow

**Current:**
```python
# Sequential (70s per contact)
for contact in contacts:
    contact = await agent3_enrich(contact)   # 10s
    contact = await agent5_phone(contact)    # 12s
    contact = await agent65_background(contact) # 25s
# Total for 4 contacts: 4 × 70s = 280s (4.7 min)
```

**Optimized:**
```python
# Parallel within each contact
async def enrich_contact(contact):
    results = await asyncio.gather(
        agent3_enrich(contact),
        agent5_phone(contact),
        agent65_background(contact)
    )
    # All run simultaneously: max(10s, 12s, 25s) = 25s
    return merge_results(contact, results)

# Process contacts in parallel (max 3 concurrent)
enriched = await asyncio.gather(*[
    enrich_contact(c) for c in contacts[:4]
])
# Total: ~30s (vs 280s = 89% faster!)
```

**Savings:**
- **Cost:** $0 (same API calls)
- **Time:** 280s → 30s = **250s saved** (4+ minutes faster!)

**Benefits:**
- Faster response time
- Better user experience
- Same cost!

**Implementation:**
- Update `teams/golf-enrichment/orchestrator.py`
- Add asyncio.gather for parallel processing
- Test error handling (one agent fails, others continue)

**Time to Implement:** 1 hour

---

### **Strategy 5: Caching Strategy** ⭐ **LOW PRIORITY**

**Problem:** Re-enriching same course wastes money

**Solution:** Don't re-enrich if recent

```python
# Before triggering enrichment:
last_enriched = course.enrichment_completed_at

if last_enriched and (now() - last_enriched) < 90 days:
    # Skip OR only refresh contacts (people change, not course intel)
    skip_course_intel = True
    only_refresh_contacts = True
```

**Savings:**
- Skip Agent 6 & 7: Save $0.042 per re-enrichment
- Only on repeat enrichments (not initial)

**Diminishing Returns:**
- Most courses enriched once
- Re-enrichment = edge case

**Implementation:**
- Add check in edge function before calling Render
- OR add flag to Render API: `refresh_only=true`

**Time to Implement:** 2 hours

---

### **Strategy 6: Cheaper Models for Simple Tasks** ⭐ **LOW PRIORITY**

**Problem:** Using same model for all agents

**Current:** All agents use `claude-haiku-4-5` via Perplexity Sonar

**Potential Optimization:**
- Agent 5 (phone lookup) = simple task, could use cheaper model
- Agents 6, 6.5 (intelligence) = complex, keep current model

**Reality Check:**
- Perplexity doesn't offer model selection
- Would need to switch to different API (OpenAI, Anthropic direct)
- Complexity vs savings trade-off

**Savings:** ~$0.003-0.005 per course

**Recommendation:** **Not worth it** - complexity outweighs savings

---

## 📈 **Cost Projection at Scale**

### **Monthly Costs (500 courses, optimized)**

#### **Without Optimization:**

```
Step 2 (Find courses):       500 × $0.02   = $10.00
Step 3 (Google Places):      500 × $0.017  = $8.50
Step 4 (Agents, 5 contacts): 500 × $0.22   = $110.00
Step 5 (ClickUp sync):       500 × $0      = $0.00
Infrastructure:
  - Supabase Pro:                           $25.00
  - Render Starter:                         $7.00
──────────────────────────────────────────────────
TOTAL:                                      $160.50/month

Cost per course: $160.50 / 500 = $0.321
```

#### **With Optimizations (Strategies 1-4):**

```
Step 2:                      500 × $0.02   = $10.00
Step 3:                      500 × $0.017  = $8.50
Step 4 (Optimized):
  - Fixed (course-level):    500 × $0.050  = $25.00  (Agent 6 optimized)
  - Variable (4 contacts):   500 × $0.129  = $64.50  (4 × $0.0322)
  - Total Step 4:                           $89.50
Step 5:                      500 × $0      = $0.00
Infrastructure:                             $32.00
──────────────────────────────────────────────────
TOTAL:                                      $140.00/month

Cost per course: $140 / 500 = $0.28

Further with contact filtering:
  - 4 contacts only:         500 × $0.179  = $89.50
──────────────────────────────────────────────────
OPTIMIZED TOTAL:                            $140.00/month
Cost per course: $0.28
```

#### **Aggressive Optimization (3 contacts, Agent 6 combined):**

```
Step 4:
  - Fixed: $0.048           (2 queries instead of 4)
  - Variable: 3 × $0.0322   = $0.097
  - Total: $0.145 per course

Monthly (500 courses):      500 × $0.145  = $72.50
Plus Steps 2-3 + Infra:                     $50.50
──────────────────────────────────────────────────
AGGRESSIVE TOTAL:                           $123.00/month
Cost per course: $0.185 ✅✅ 26% under target!
```

---

## 🎯 **Optimization Implementation Roadmap**

### **Quick Wins (Implement Now):**

#### **1. Contact Filtering** - 30 minutes
**Impact:** ⭐⭐⭐⭐⭐ (Highest ROI)
**Savings:** $0.10 per 7-contact course
**Complexity:** ⭐ (Very easy)

```python
# Add to orchestrator before enrichment loop
contacts = filter_to_decision_makers(all_contacts, max_count=4)
```

**Implementation File:** `teams/golf-enrichment/orchestrator.py`

**Test:** Re-run Country Club of Virginia, verify cost drops to ~$0.19

---

#### **2. Make Agent 6.5 Selective** - 30 minutes
**Impact:** ⭐⭐⭐⭐ (High ROI)
**Savings:** $0.03-0.05 per course
**Complexity:** ⭐ (Easy)

```python
# Only run Agent 6.5 for GM/Directors
if is_vip_role(contact['title']):
    contact = await agent65_background(contact)
```

**Implementation File:** `teams/golf-enrichment/orchestrator.py`

**Test:** Verify segmentation still accurate without all backgrounds

---

### **Medium-Term (Implement Next Week):**

#### **3. Optimize Agent 6 Queries** - 1-2 hours
**Impact:** ⭐⭐⭐ (Medium ROI)
**Savings:** $0.012 per course
**Complexity:** ⭐⭐ (Moderate - requires testing)

**Implementation File:** `teams/golf-enrichment/agents/agent6_course_intelligence.py`

**Changes:**
- Combine water hazard queries: 2 queries → 1 query
- Combine business intel queries: 2 queries → 1 query
- Maintain output quality

**Test:** Verify segmentation accuracy remains > 90%

---

#### **4. Parallel Contact Enrichment** - 1 hour
**Impact:** ⭐⭐⭐ (Time savings, not cost)
**Savings:** 250 seconds (4 minutes) per course
**Complexity:** ⭐⭐ (Moderate)

**Implementation File:** `teams/golf-enrichment/orchestrator.py`

**Changes:**
```python
# Replace sequential loop with parallel processing
enriched_contacts = await asyncio.gather(*[
    enrich_contact_parallel(c) for c in contacts[:4]
])
```

**Test:** Verify all agents still complete successfully

---

### **Long-Term (Future Optimization):**

#### **5. Caching Layer** - 2-3 hours
**Impact:** ⭐⭐ (Only on repeats)
**Savings:** $0.042 per re-enrichment
**Complexity:** ⭐⭐⭐ (Complex)

**When to Implement:** After 1000+ courses enriched

---

## 💡 **Optimization Scenarios**

### **Scenario A: Aggressive Cost Reduction (Target: $0.15)**

**Changes:**
1. ✅ Filter to 3 contacts only
2. ✅ Agent 6: 2 queries instead of 4
3. ✅ Skip Agent 6.5 entirely

**Result:**
- Fixed: $0.048
- Variable: 3 × $0.0226 = $0.0678
- **Total: $0.1158** ✅✅ 54% under target!

**Trade-offs:**
- Fewer contacts enriched (only top 3)
- No background intel (tenure, previous clubs)
- May miss key contacts

**Recommendation:** **Too aggressive** - keep Agent 6.5 for VIPs

---

### **Scenario B: Balanced Optimization (Target: $0.20)** ⭐ **RECOMMENDED**

**Changes:**
1. ✅ Filter to 4 contacts max
2. ✅ Agent 6: 2 queries instead of 4
3. ✅ Agent 6.5: Only for GM + Directors (2 of 4)

**Result:**
- Fixed: $0.048 (optimized Agent 6)
- Variable:
  - All 4 get Agent 3+5: 4 × $0.0226 = $0.0904
  - 2 get Agent 6.5: 2 × $0.0096 = $0.0192
- **Total: $0.1576** ✅ 37% under target!

**Trade-offs:**
- Minimal - still enriching key contacts
- Background intel for decision-makers only
- Quality maintained

**Recommendation:** **Implement this!**

---

### **Scenario C: No Optimization (Current)**

**Result:** $0.28 average (12% over target)

**When Acceptable:**
- High-value prospects (worth extra $0.08)
- Comprehensive data needed
- Budget allows for overage

---

## 📊 **ROI Analysis**

### **Manual vs Automated Costs:**

**Manual Research (Per Course):**
```
Find course website:           15 min × $20/hr = $5.00
Find 4 contacts:               20 min × $20/hr = $6.67
Find email/phone per contact:  30 min × $20/hr = $10.00
Research company intel:        20 min × $20/hr = $6.67
──────────────────────────────────────────────────
Total Manual:                  85 min = $28.34 per course
```

**Automated (Optimized):**
```
All steps automated:           4-7 min = $0.18 per course
──────────────────────────────────────────────────
Savings per course:            $28.16 (99.4% reduction!)
```

**Monthly (500 courses):**
```
Manual:   500 × $28.34 = $14,170/month
Automated: 500 × $0.18 = $90/month + $32 infra = $122/month
──────────────────────────────────────────────────
Monthly Savings:             $14,048/month
Annual Savings:              $168,576/year
ROI:                         11,500% 🚀
```

---

## 🎯 **Recommended Implementation Plan**

### **Phase 1: Quick Wins (Today - 1 hour)**

1. **Implement contact filtering (30 min)**
   - File: `teams/golf-enrichment/orchestrator.py`
   - Change: Add `filter_contacts()` function
   - Test: Country Club of Virginia (expect $0.19)

2. **Make Agent 6.5 selective (30 min)**
   - File: `teams/golf-enrichment/orchestrator.py`
   - Change: Only run for VIP roles
   - Test: Belmont (should drop to ~$0.15)

**Expected Savings:** $0.08-0.10 per course
**New Target Cost:** $0.18-0.19 per course ✅

---

### **Phase 2: Agent Optimization (Next Week - 2 hours)**

1. **Optimize Agent 6 queries (1-2 hours)**
   - File: `teams/golf-enrichment/agents/agent6_course_intelligence.py`
   - Change: Combine 4 queries → 2 queries
   - Test: 10 courses, verify segmentation accuracy

2. **Parallel processing (1 hour)**
   - File: `teams/golf-enrichment/orchestrator.py`
   - Change: asyncio.gather for parallel enrichment
   - Test: Verify error handling

**Expected Savings:** $0.012 per course + 4 minutes faster

**New Target Cost:** $0.165-0.175 per course ✅✅

---

### **Phase 3: Monitoring (Ongoing)**

1. **Track actual costs post-optimization**
2. **Measure contact quality (email/phone success rates)**
3. **A/B test: 3 vs 4 vs 5 contacts**
4. **Refine filtering logic based on conversion data**

---

## 📊 **Cost Monitoring Queries**

### **Daily Cost Check:**

```sql
-- Total cost yesterday
SELECT
  DATE(enrichment_requested_at) as date,
  COUNT(*) as courses,
  SUM(agent_cost_usd) as total_cost,
  ROUND(AVG(agent_cost_usd), 4) as avg_cost,
  SUM(agent_cost_usd) as total_cost
FROM golf_courses
WHERE DATE(enrichment_requested_at) = CURRENT_DATE - 1
  AND enrichment_status = 'complete'
GROUP BY DATE(enrichment_requested_at);

-- Alert if total_cost > $50/day
```

### **Cost by Contact Count:**

```sql
-- Understand cost distribution
SELECT
  contact_count,
  COUNT(*) as courses,
  ROUND(AVG(agent_cost_usd), 4) as avg_cost,
  ROUND(MIN(agent_cost_usd), 4) as min_cost,
  ROUND(MAX(agent_cost_usd), 4) as max_cost
FROM (
  SELECT
    g.id,
    g.agent_cost_usd,
    COUNT(c.id) as contact_count
  FROM golf_courses g
  LEFT JOIN golf_course_contacts c ON g.id = c.golf_course_id
  WHERE g.enrichment_status = 'complete'
  GROUP BY g.id, g.agent_cost_usd
) t
GROUP BY contact_count
ORDER BY contact_count;
```

**Expected Output:**
```
contact_count | courses | avg_cost | min_cost | max_cost
      3       |    50   |  0.1586  |  0.1520  |  0.1650
      4       |   150   |  0.1908  |  0.1761  |  0.2050
      5       |   100   |  0.2230  |  0.2100  |  0.2380
      6       |    30   |  0.2552  |  0.2450  |  0.2680
      7       |    20   |  0.2874  |  0.2767  |  0.3000
```

**Action:** If many courses have 6-7 contacts, filtering is critical!

---

### **Cost Outlier Detection:**

```sql
-- Find expensive courses
SELECT
  g.id,
  g.course_name,
  g.agent_cost_usd,
  COUNT(c.id) as contact_count,
  g.enrichment_requested_at
FROM golf_courses g
LEFT JOIN golf_course_contacts c ON g.id = c.golf_course_id
WHERE g.agent_cost_usd > 0.30 -- More than 2x target
  AND g.enrichment_status = 'complete'
GROUP BY g.id, g.course_name, g.agent_cost_usd, g.enrichment_requested_at
ORDER BY g.agent_cost_usd DESC
LIMIT 20;
```

**Investigate:**
- Why did these cost so much?
- Too many contacts?
- Agent failure/retry?
- Data quality issue?

---

## 🎯 **Optimization Targets Summary**

| Strategy | Impact | Time | Savings/Course | Priority |
|----------|--------|------|----------------|----------|
| 1. Contact filtering (4 max) | ⭐⭐⭐⭐⭐ | 30 min | $0.10 | **NOW** |
| 2. Agent 6 query consolidation | ⭐⭐⭐ | 1-2 hr | $0.012 | Next week |
| 3. Agent 6.5 selective | ⭐⭐⭐⭐ | 30 min | $0.04 | **NOW** |
| 4. Parallel processing | ⭐⭐⭐ | 1 hr | 4 min faster | Next week |
| 5. Caching | ⭐⭐ | 2-3 hr | $0.04 (repeats) | Later |
| 6. Cheaper models | ⭐ | 4+ hr | $0.005 | Not worth it |

**Recommended First Steps:** Strategies 1 + 3 (1 hour total, $0.14 savings)

---

## 💰 **Break-Even Analysis**

### **Current Pricing (If Selling Service):**

**Cost to Enrich:** $0.18/course (optimized)
**Sell Price:** $2.00/course (11x markup)
**Margin:** $1.82 per course (91%)

**Monthly Revenue (500 courses):**
```
Revenue:   500 × $2.00   = $1,000/month
Costs:     500 × $0.18   = $90/month
Infra:                   = $32/month
──────────────────────────────────────
Net Profit:              = $878/month
Margin:                    87.8%
```

### **Internal Use (Cost Savings):**

**Manual Research Cost:** $28/course
**Automated Cost:** $0.18/course
**Savings:** $27.82 per course

**Break-Even:** After 1 course! (saved $27.82 > spent $0.18)

---

## 📚 **References**

- **Integration:** See `INTEGRATION_GUIDE.md` (root)
- **Edge Functions:** See `EDGE_FUNCTIONS.md`
- **Reliability:** See `RELIABILITY_PLAYBOOK.md`
- **Implementation:** See `teams/golf-enrichment/orchestrator.py`

---

## ✅ **Next Actions**

1. **Implement Strategies 1 + 3** (1 hour, save $0.14)
2. **Test on 5-10 courses** (verify cost reduction)
3. **Monitor for 1 week** (ensure quality maintained)
4. **Implement Strategy 2** (save additional $0.012)
5. **Achieve target** < $0.20/course ✅

---

**Last Updated:** October 18, 2024
**Target Met:** ⏳ In Progress (implementing optimizations)
**Expected:** ✅ Within 1 week
