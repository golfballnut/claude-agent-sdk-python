# POC Goal: Golf Course Business Intelligence & Outreach System

## Mission

Build a cost-effective, scalable agent workflow that identifies golf course business opportunities and enables targeted outreach for range ball reconditioning services.

---

## Master Planning Documents

**📋 START HERE:** [outreachgoalsv1_101725.md](outreachgoalsv1_101725.md) - **Master Roadmap** (7 phases, timeline, full vision)

**Related Docs:**
- [outreach_funnel_goals.md](outreach_funnel_goals.md) - Phase 7 goals (future - don't forget!)
- [business_opportunities.md](business_opportunities.md) - 6 opportunity types + scoring framework
- [progress.md](progress.md) - Current progress tracking

**Technical Docs:**
- [docs/infrastructure_architecture.md](docs/infrastructure_architecture.md) - Full system diagram + data flow
- [docs/phase_checklists.md](docs/phase_checklists.md) - Validation criteria per phase
- [docs/agent_skills_research.md](docs/agent_skills_research.md) - New Claude Skills feature (future use)

**Current Phase:** Phase 1 (80%) + Phase 4 (Orchestrator - 0%)

---

## Business Context

### The Business: Range Ball Reconditioning & Golf Ball Retrieval

**Core Service:** Golf ball retrieval (pond/water hazard recovery)

**Innovation:** Used range ball reconditioning
- **Unique Value Proposition:** ONLY company worldwide that can clean + add protective coating to used range balls
- **Technology:** Clean balls <50% worn + apply protective coating
- **Market Opportunity:** High-end clubs throw away used balls (member complaints), budget clubs need affordable alternatives

**Revenue Streams:**
1. **Buy Program (High-End Clubs):** Purchase used range balls they currently dispose of
2. **Sell Program (Budget Clubs):** Sell reconditioned balls at 40-60% discount vs new
3. **Lease Program (All Clubs):** Lease range balls with 6-month swap cycle (always fresh)
4. **Core Service:** Golf ball retrieval contracts

**Future Opportunities:**
1. Pro shop e-commerce platform (one-stop shop for tees, brushes, accessories)
2. Buy found balls from superintendents (course maintenance pickups → staff event funding)
3. [Additional opportunities identified from data patterns]

---

## Workflow

```
Agent 1 (URL Finder)
  ↓
Agent 2 (Data Extractor)
  ↓
Agent 3 (Contact Enricher: Email + LinkedIn)
  ↓
Agent 6 (Business Intelligence: Segmentation + Opportunity Scoring)
  ↓
Targeted Outreach (Value-Prop Specific)
```

---

## Agent Descriptions

### Agent 1: URL Finder
**Input:** Course/business name
**Task:** Find listing URL from directory
**Output:** https://vsga.org/courselisting/[ID]
**Status:** ✅ COMPLETE

### Agent 2: Data Extractor
**Input:** URL from Agent 1
**Task:** Extract contact data (name, phone, website, staff)
**Output:** Structured JSON with contact info
**Status:** ✅ COMPLETE

### Agent 3: Contact Enricher
**Input:** Contacts from Agent 2
**Task:** Find emails + LinkedIn URLs (Hunter.io API)
**Output:** Email (50% success) + LinkedIn (25% bonus) + confidence scores
**Status:** ✅ COMPLETE

**Discovery:** Hunter.io Email-Finder returns linkedin_url field - no need for separate Agent 4!

### Agent 6: Business Intelligence (NEW)
**Input:** Contacts from Agent 3 + company context
**Task:** Gather business intelligence for targeted outreach
**Output:**
- **Segmentation:** High-end vs budget club classification
- **Opportunity Scoring:** 6 opportunity types scored 1-10
- **Range Intel:** Practice range presence, volume signals, quality complaints
- **Conversation Starters:** Value-prop specific openers

**Intelligence Gathering:**

#### Query 1: Range Ball & Budget Signals
- Practice range presence/size
- Member complaints about ball quality
- Budget constraints or cost-cutting
- Sustainability/waste reduction initiatives
- Recent capital investments

#### Query 2: Industry Pain Points (Role-Specific)
- Practice range operations challenges
- Budget pressures for consumables
- Member satisfaction with practice facilities
- Waste disposal concerns
- Supply chain inefficiencies

#### Query 3: Opportunity Identification
- Pro shop size and offerings
- Online ordering capabilities
- Superintendent team needs
- Environmental programs
- Vendor relationships

**Segmentation Logic:**

**High-End Club Indicators:**
- Positioned as "premium," "private," "exclusive," "championship"
- Ratings 4.5+ stars
- Recent renovations/upgrades
- Member complaints about ball quality (signal they discard worn balls)
- Pricing complaints (expensive = high-end)

**Budget Club Indicators:**
- Positioned as "public," "affordable," "value," "accessible"
- Ratings 3.5-4.5 stars
- Reviews mention "good value," "reasonable prices"
- Cost-cutting signals
- Older facilities without recent upgrades

**Opportunity Types (Scored 1-10):**
1. **range_ball_buy:** High-end clubs - buy their used balls
2. **range_ball_sell:** Budget clubs - sell reconditioned balls
3. **range_ball_lease:** All clubs - lease program fit
4. **proshop_ecommerce:** E-commerce platform opportunity
5. **superintendent_partnership:** Found ball buyback program
6. **ball_retrieval:** Core service contract opportunity

**Status:** ✅ COMPLETE (redesigned for business intel)

---

## Success Criteria

### Technical
- ✅ **Cost:** < $0.02 per agent (< $0.05 total per workflow)
- ✅ **Accuracy:** 100% correct data extraction
- ✅ **Speed:** < 10 seconds per agent
- ✅ **Reliability:** No hallucinations, no failures
- ✅ **Scalability:** Pattern works for 500+ agents

### Business
- ✅ **Segmentation Accuracy:** 80%+ correct high-end vs budget classification
- ✅ **Opportunity Relevance:** Top 2 opportunities align with business strategy
- ✅ **Conversation Starter Quality:** 8-10/10 relevance for value propositions
- ✅ **Actionable Intel:** Sales team can use output directly

---

## Current Status

**Agent 1 Results:**
- Cost: $0.0153 avg (24% under budget) ✅
- Accuracy: 100% (5/5 correct URLs) ✅
- Speed: 3.4s avg ✅
- **STATUS: PRODUCTION READY** ✅

**Agent 2 Results:**
- Cost: $0.0123 avg (38% under budget) ✅
- Accuracy: 100% (5/5 successful extractions) ✅
- Speed: 8.5s avg ✅
- **STATUS: PRODUCTION READY** ✅

**Agent 3 Results:**
- Email Success: 50% (6/12 via Hunter.io)
- LinkedIn Success: 25% (3/12 bonus from Hunter.io!)
- Cost: $0.0116 avg (42% under budget) ✅
- Confidence: 95-98% when found ✅
- Speed: ~8s per contact ✅
- **STATUS: PRODUCTION READY** ✅
- **Bonus Discovery:** Hunter.io includes LinkedIn URLs - Agent 4 not needed!

**Agent 6 Results (Business Intel Redesign):**
- Segmentation Success: [Testing in progress]
- Opportunity Scoring: [Testing in progress]
- Cost: ~$0.012 avg (target: <$0.05) ✅
- Quality: High-value business intelligence when successful
- **STATUS: TESTING** 🧪

**Combined Workflow (Agents 1+2+3+6):**
- Total Cost: ~$0.05 per course (with avg 2.4 contacts)
- Total Time: ~45s per workflow ✅

---

## Market Segmentation Strategy

### High-End Clubs (Buy Target)
**Value Proposition:** "Reduce waste, generate revenue from used balls you're currently throwing away"

**Conversation Starters:**
1. "Are you currently disposing of used range balls once they show wear?"
2. "We're the only company that can recondition your used balls to like-new quality - interested in turning waste into revenue?"
3. "Many premium clubs are exploring range ball recycling programs that reduce waste while maintaining member expectations"

**Key Pain Points:**
- Member complaints about worn balls
- Waste disposal costs
- Sustainability goals

---

### Budget Clubs (Sell Target)
**Value Proposition:** "Get near-new quality range balls at 40-60% off new ball prices"

**Conversation Starters:**
1. "Budget pressures are affecting every club - have you explored alternatives to buying new range balls?"
2. "We sell reconditioned range balls at half the price of new, with quality that members can't tell apart"
3. "Maintain your practice facility quality while controlling costs"

**Key Pain Points:**
- Budget constraints
- Cost-cutting pressure
- Need for affordable quality

---

### Lease Program (All Clubs)
**Value Proposition:** "Always have fresh range balls without upfront cost or storage - we swap them every 6 months"

**Conversation Starters:**
1. "Interested in a range ball subscription where you always have fresh inventory?"
2. "Eliminate the hassle of tracking ball wear - we handle everything"
3. "No upfront investment, predictable monthly cost, always happy members"

**Key Pain Points:**
- Ball management hassle
- Capital constraints
- Inconsistent quality over time

---

## Future Opportunity Identification

### From Data Patterns (Agent 6 Gathers Intel On):

**1. Pro Shop E-Commerce**
- Signal: Limited online presence, manual ordering
- Opportunity: One-stop shop for accessories (tees, brushes, towels, etc.)
- Value Prop: "Easy reordering, bulk discounts, next-day delivery"

**2. Superintendent Found Ball Buyback**
- Signal: Large maintenance teams, operational challenges
- Opportunity: Buy balls found during course work
- Value Prop: "Turn waste into revenue for staff events/bonuses"

**3. Tournament Ball Programs**
- Signal: Frequent tournament hosting
- Opportunity: Reconditioned premium balls for events
- Value Prop: "Tournament-quality balls at fraction of cost"

**4. Youth Program Support (CSR)**
- Signal: Junior golf programs, community outreach
- Opportunity: Donate refurbished balls to youth programs
- Value Prop: "Support community while reducing waste"

**5. Sustainability Partnerships**
- Signal: Environmental initiatives, green messaging
- Opportunity: Partner on waste reduction goals
- Value Prop: "Reduce 5,000+ balls/year from landfill"

**6. Equipment Leasing**
- Signal: Aging equipment, capital constraints
- Opportunity: Lease ball washers/equipment alongside ball programs
- Value Prop: "Bundle services for complete range management"

---

## Cost Projection

| Component | Target | Actual | Status |
|-----------|--------|--------|--------|
| Agent 1 | $0.02 | $0.0153 | ✅ Under |
| Agent 2 | $0.02 | $0.0123 | ✅ Under |
| Agent 3 | $0.02 | $0.0116 | ✅ Under |
| Agent 6 | $0.02 | $0.0120 | ✅ Under |
| Per Course | $0.06 | $0.0512 | ✅ Under |

**Daily Projection (500 courses, avg 2.4 contacts each):**
- Agent 1: $7.65/day
- Agent 2: $6.16/day
- Agent 3: $13.92/day (1200 contacts, includes LinkedIn!)
- Agent 6: $6.00/day (business intel)
- **Total: ~$33.73/day = ~$1,012/month** (full enrichment + business intel)

---

## Next Steps

1. ✅ ~~Build Agent 2 with same winning pattern~~
2. ✅ ~~Test Agent 2 with 5 URLs from Agent 1~~
3. ✅ ~~Build Agent 3 for email + LinkedIn enrichment~~
4. ❌ ~~Agent 4 cancelled - Hunter.io includes LinkedIn!~~
5. ✅ Build Agent 6 for business intelligence
6. 🧪 Test Agent 6 business intel accuracy (segmentation + opportunities)
7. 🔄 Build orchestrator to connect Agents 1 → 2 → 3 → 6
8. Full workflow test with business segmentation
9. Deploy to cloud (Cloud Run / Railway)

---

## Production Deployment

**Target:** Supabase Edge Function triggers SDK workflow
**Scale:** 500 workflows/day = ~$34/day = ~$1,012/month
**Architecture:** Microservices pattern (specialized agents)
**Output:** Segmented contacts with opportunity scores and value-prop specific conversation starters
**Status:** Agent 6 testing, orchestrator remaining
