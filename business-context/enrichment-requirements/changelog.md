# Business Context Changelog

**Purpose:** Track major changes to business understanding and requirements
**Update:** When business strategy, ICP, or data requirements change

---

## 2025-10-31 - v1 Initial Business Context Capture

### Summary
Comprehensive documentation of Links Choice B2B business model, service offerings, customer segmentation, and enrichment requirements.

### Company Profile
- **Documented:** Links Choice (B2B) and Golf Ball Nut (B2C) business models
- **Core Competency:** World-class golf ball processing (recycling + refinishing)
- **Competitive Advantage:** Only company that can remove/reapply clear coat (80% look-new quality)
- **Tech Stack:** NetSuite, Supabase, ClickUp, Render, multiple marketplaces

### Service Offerings Mapped
- **High-End Courses (Tier 1-2):** 5 service types
  - Subscription practice program (premium offering)
  - Ball retrieval with payment
  - Practice ball purchase
  - Protective coating service
  - Maintenance ball purchase

- **Low-End Courses (Tier 3-4):** 6 service types
  - Range balls (50% off new pricing - key message)
  - Trade programs (budget flexibility)
  - Free retrieval service
  - One-stop shop (balls + accessories)
  - Ball purchase with credit

- **All Courses:** Outing packages (event bundles)

### Customer Segmentation Defined
- **Course Tiers:** 4-tier classification (Elite, Premium, Mid-Market, Budget)
- **ICP (Primary):** Tier 2 Premium Private Country Clubs
  - Green fees $75-150
  - 3+ water hazards (retrieval opportunity)
  - 30+ station range (volume opportunity)
  - Multiple decision makers accessible

- **Qualification Scoring:** 10-point scale based on:
  - Opportunity size (40%): Water hazards + range size + course tier
  - Accessibility (30%): Decision makers found + contact quality
  - Buying readiness (30%): Pain points + timing signals + budget

### Buyer Personas Established
- **Decision Hierarchy:** Mapped authority by service type
  - **GM/Owner:** Contract approval, budget authority (Priority 1)
  - **Superintendent:** Retrieval decisions, maintenance procurement (Priority 1)
  - **Director of Golf:** Range ball decisions, outing packages (Priority 2)
  - **Head Pro/Event Coord:** Operational/influencer (Priority 3)

### Enrichment Requirements Prioritized

**Critical Data (Priority 1):**
- Water hazard count and locations ⭐ **HIGHEST PRIORITY**
- Practice range size and quality
- Decision maker contacts (emails required)
- Course tier classification

**High-Value Data (Priority 2):**
- Buying signals (pain points, timing)
- Course intelligence (projects, vendors, awards)

**Nice-to-Have (Priority 3):**
- Event program details
- Competitive intelligence

### Workflow Changes Required
- **Enhanced LLM Prompt:** Add 7 structured sections (water hazards, range, contacts, tier, signals, intelligence, events)
- **New Database Fields:** Water hazards, range data, buying signals, qualification scoring
- **ClickUp Enhancements:** Tier-specific lists, qualification scoring, service recommendations

### Key Insights Documented
1. **Water hazards = #1 data priority** (retrieval entry point + raw materials)
2. **Course tier determines service offering** (different pitch by tier)
3. **Multiple decision makers = different services** (Superintendent ≠ Director of Golf)
4. **Buying signals = urgency** (active pain = faster close)
5. **Range size predicts subscription fit** (50+ stations ideal)

---

## Future Changelog Entries

### When to Update

**Business Model Changes:**
- New service offerings added
- Pricing strategy changes
- Market expansion (new states/segments)

**ICP Refinements:**
- Win/loss analysis reveals new patterns
- Qualification criteria adjustments
- Tier definitions updated

**Data Requirement Changes:**
- New critical data fields discovered
- Existing fields proven unnecessary
- Data source strategies evolve

**Workflow Enhancements:**
- LLM prompt improvements
- Enrichment logic changes
- Scoring algorithm updates

### Template for Future Entries

```markdown
## YYYY-MM-DD - [Version] [Change Title]

### Summary
Brief description of what changed and why

### Changes
- **Added:** New thing 1
- **Modified:** Changed thing 2
- **Removed:** Deprecated thing 3

### Impact
- Workflow changes required
- Database schema updates needed
- ClickUp configuration adjustments

### Rationale
Why this change was made (data, feedback, strategy shift)
```

---

## Version Control Philosophy

**This Changelog:**
- Tracks major business context changes
- NOT for code changes (use git for that)
- NOT for minor doc updates (typos, formatting)
- YES for strategic shifts, requirement changes, major insights

**Individual Files:**
- Update in place (don't create v2, v3 files)
- Use git for detailed version history
- Changelog captures high-level milestones

**v1_current_state.md:**
- Snapshot of initial understanding (Oct 31, 2025)
- Preserved for reference (never updated)
- Compare future state to v1 to see evolution
