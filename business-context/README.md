# Links Choice Business Context

**Last Updated:** October 31, 2025
**Purpose:** Business intelligence foundation for AI-powered golf course outreach

---

## 30,000 Foot Overview

### Who We Are

**Links Choice** is a B2B golf ball processing company with a **world-class competitive advantage**: We're the only company that can remove original clear coat and reapply it, making 80% of recycled golf balls look brand new.

**Operating Structure:**
- **Links Choice** (B2B) - Primary focus, this outreach program
- **Golf Ball Nut** (B2C) - Consumer channel, future AI agent opportunity
- Both operate under one federal ID

**Core Competency:** Golf ball processing
- Recycling golf balls (remove/recoat clear coat)
- Refinishing golf balls (full recoat, rebrand)
- Service work for companies that can't refinish

---

## What We Sell (Green Grass Channel)

### High-End Courses (Country Clubs, Resorts)

1. **Purchase Practice Balls** - Pay them for balls they'd throw away
2. **Protective Coating Service** - Extend practice ball life another season
3. **Ball Retrieval Service** - Harvest balls from water hazards
4. **Maintenance Ball Purchase** - Buy balls collected by grounds crews
5. **Subscription Practice Program** - Swap premium range balls 2x/year

### Low-End Courses (Daily-Fee, Municipal)

1. **Retrieval Services** - Get balls from their water hazards
2. **Discounted Range Balls** - 50% off new ball pricing
3. **Trade Programs** - Retrieved balls = credit toward our range balls
4. **Resell Packages** - Counter balls, packaged product
5. **One-Stop Shop** - Practice balls + Pride/Champ accessories (tees, brushes)

### All Courses

1. **Outing Packages** - Ball + accessory bundles for corporate events

---

## Our Competitive Advantage

### Processing Technology
**No one else in the world can do what we do:**

- Remove original clear coat without damaging ball
- Reapply professional-grade clear coat
- Result: 80% of recycled balls look brand new
- Fallback: If recycling fails, refinish high-end models or convert to practice balls

### Business Model Benefits
- **For High-End Courses:** Turn waste into revenue, better quality range balls
- **For Low-End Courses:** 50% cost savings on practice balls
- **For Links Choice:** Multiple revenue streams per customer (not one-time sale)

---

## Why This Matters for Outreach

### Current Gap
The existing enrichment workflow (v1) captures:
- ✅ Contact names, emails, LinkedIn
- ✅ Course ownership, recent projects
- ❌ **Opportunity qualification data**

### What We Need to Add
To qualify leads properly, we need:

1. **Water Hazards** - Retrieval opportunity size (ponds, lakes, ball accumulation spots)
2. **Course Tier** - Determines which service offering fits (pricing, rounds/year)
3. **Practice Facilities** - Range size, ball quality, current supplier
4. **Buying Signals** - Waste mentions, cost complaints, upcoming projects
5. **Decision Authority** - Who approves contracts vs who influences vs who uses

---

## Documentation Structure

```
business-context/
├── README.md (you are here)          # Start here, 30,000ft view
├── v1_current_state.md               # Snapshot of today's understanding
│
├── company-profile/
│   ├── links-choice-overview.md      # B2B business details
│   ├── golf-ball-nut-overview.md     # B2C (future AI work)
│   ├── core-competencies.md          # Processing advantage
│   └── tech-stack.md                 # Systems we use
│
├── service-offerings/
│   ├── high-end-courses.md           # CC/Resort service menu
│   ├── low-end-courses.md            # Daily-fee/Municipal menu
│   ├── all-courses.md                # Universal offerings
│   └── pricing-strategy.md           # How we price
│
├── customer-segmentation/
│   ├── ideal-customer-profile.md     # What = great fit
│   ├── course-tiers.md               # High vs low criteria
│   ├── qualification-criteria.md     # Data = qualified lead
│   └── disqualification-rules.md     # When to skip
│
├── buyer-personas/
│   ├── general-manager.md            # Contract approval
│   ├── superintendent.md             # Maintenance, retrieval
│   ├── director-of-golf.md           # Range quality, pro shop
│   └── decision-hierarchy.md         # Authority by service
│
├── sales-process/
│   ├── entry-points.md               # Ways to start relationship
│   ├── typical-journey.md            # First service → expand
│   ├── objection-handling.md         # Common pushback
│   └── success-metrics.md            # What = qualified opp
│
└── enrichment-requirements/
    ├── data-priorities.md            # What to collect (priority order)
    ├── workflow-mapping.md           # Business needs → LLM prompts
    └── changelog.md                  # Track changes

```

---

## Version Control Strategy

**Philosophy:** Keep it simple, avoid confusion

- **README.md** - Always current, "start here" doc
- **v1_current_state.md** - Snapshot of initial understanding (Oct 31, 2025)
- **Individual files** - Living documents, update as we learn
- **changelog.md** - Track major changes with dates
- **No v2, v3, v4 files** - Update in place, use git for history

### When You Learn Something New
1. Update the relevant file
2. Add entry to `enrichment-requirements/changelog.md`
3. DON'T create new version files

---

## Quick Reference

**Start Here:**
- New to Links Choice? → Read this file, then `company-profile/links-choice-overview.md`
- Building enrichment workflow? → `enrichment-requirements/workflow-mapping.md`
- Qualifying a lead? → `customer-segmentation/qualification-criteria.md`
- Talking to a contact? → `buyer-personas/[role].md`

**Key Files:**
- Service menu: `service-offerings/` folder
- Who buys what: `buyer-personas/decision-hierarchy.md`
- What data to collect: `enrichment-requirements/data-priorities.md`

---

## Next Steps

After documenting business context:
1. Enhance LLM discovery prompt with qualification fields
2. Update enrichment schema for opportunity data
3. Test on 3 courses to validate we're capturing the RIGHT data
4. Iterate based on what we learn

---

**Current Status:** ✅ Foundation complete, ready for workflow enhancement
