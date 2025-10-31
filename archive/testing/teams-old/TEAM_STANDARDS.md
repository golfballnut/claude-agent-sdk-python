# Agent Team Standards - Multi-Team SOP

**Purpose:** Rules ALL agent teams must follow
**Applies To:** Any team in `teams/` folder
**Last Updated:** October 18, 2024

---

## 🎯 **Why These Standards Exist**

**Lesson Learned (Oct 18, 2024):**
- Golf team created 14+ .md files scattered everywhere
- Had to reorganize documentation TWICE in one day
- Wasted 2 hours on cleanup
- Could have been prevented with clear rules!

**These standards prevent:**
- ✅ Documentation sprawl
- ✅ Duplicate files
- ✅ Cost overruns
- ✅ Production incidents
- ✅ Confusion for new contributors

---

## 📋 **MANDATORY STANDARDS (All Teams)**

### **Standard #1: 5-File Limit at Team Root** ⭐ **CRITICAL**

**MAX 5 markdown files** at `teams/your-team/` root level:

**Required (2 files):**
1. ✅ `START_HERE.md` - Entry point for contributors
2. ✅ `README.md` - Team overview

**Optional (3 files max):**
3. `CLAUDE.md` - Team-specific rules (recommended)
4. `CHANGELOG.md` - Version history (if needed)
5. [One flex spot] - For urgent/temporary notes

**Everything else → docs/** in organized folders

---

### **Standard #2: Organized docs/ Structure**

**Three folders ONLY:**

```
teams/your-team/docs/
├── 1_IMPLEMENTATION/ (what to build)
│   ├── Specifications
│   ├── Migrations
│   ├── Templates
│   └── Integration guides
│
├── 2_OPERATIONS/ (how to run it)
│   ├── Playbooks
│   ├── Monitoring guides
│   ├── Cost optimization
│   └── Troubleshooting
│
└── 3_REFERENCE/ (background context)
    ├── Business goals
    ├── Roadmaps
    └── Historical docs
```

**Don't create:** docs/architecture/, docs/specs/, docs/guides/ (use 1-2-3 structure!)

---

### **Standard #3: START_HERE.md is Source of Truth**

**START_HERE.md must contain:**
1. What this team does (2-3 sentences)
2. Current status (✅ built, 📋 next, ❌ blocked)
3. What's ready to build (links to implementation docs)
4. Quick start for new contributors
5. Documentation map (where to find things)

**Update START_HERE.md instead of creating:**
- PROGRESS.md, STATUS.md, UPDATES.md
- NEXT_STEPS.md, TODO.md, ROADMAP.md
- Any "latest update" type file

**Why:** One entry point >> 5 status files

---

### **Standard #4: Cost Discipline**

**Every team must:**
- Define cost target (e.g., < $0.20/operation)
- Track cost per agent in tests
- Document in `docs/2_OPERATIONS/COST_OPTIMIZATION.md`
- Alert if costs exceed 125% of target

**Cost testing required:**
```python
# In tests/test_costs.py
def test_agent_costs():
    """Verify all agents under budget"""
    assert agent1_cost < 0.02
    assert agent2_cost < 0.02
    assert total_cost < 0.20  # Team target
```

**Monthly review:**
- Actual vs target costs
- Optimization opportunities
- Update cost docs

---

### **Standard #5: Production Safety**

**NEVER:**
- ❌ Edit `production/your-team/` directly
- ❌ Deploy without testing locally
- ❌ Skip docker-compose test
- ❌ Commit secrets (.env files)
- ❌ Force push to main

**ALWAYS:**
- ✅ Develop in `teams/your-team/`
- ✅ Test: unit → integration → docker → production-mirror
- ✅ Sync via script: `python production/scripts/sync_to_production.py your-team`
- ✅ Deploy from `production/your-team/` folder only
- ✅ Monitor deployment logs

---

### **Standard #6: ClickUp Integration (If Applicable)**

**Rules:**
- Use existing ClickUp lists (don't create new structure)
- Max 20 custom fields per list
- Use tags for simple categories (yes/no, status)
- Use custom fields for sortable/filterable data
- Document field IDs in config file: `config/clickup-field-mapping.json`
- Create custom views for filtering

**Before adding field:**
1. Check if tag works instead
2. Check if existing field can be reused
3. Document purpose in CLICKUP_ARCHITECTURE.md

---

### **Standard #7: Edge Case Documentation**

**Every team must have:** `docs/2_OPERATIONS/EDGE_CASE_PLAYBOOK.md`

**Minimum 5 edge cases documented:**
1. API failure/timeout
2. Invalid/missing data
3. Duplicate detection
4. Cost overrun
5. [Team-specific critical scenario]

**Format for each:**
- Scenario description
- Detection method
- Supabase actions (if applicable)
- ClickUp actions (if applicable)
- Recovery procedure
- Prevention strategy

---

### **Standard #8: Testing Requirements**

**Test coverage required:**
- [ ] Unit tests for each agent (>80% coverage)
- [ ] Integration test for orchestrator
- [ ] Cost validation tests
- [ ] Edge case tests (top 5 scenarios)
- [ ] Docker compose test passes

**Test before every deploy:**
```bash
# Required sequence
pytest teams/your-team/tests/              # All tests pass
docker-compose up --build                   # Local test works
docker-compose -f production-mirror.yml up  # Staging test works
# Only then: sync and deploy
```

---

## 🏗️ **Team Creation Template**

### **When Creating New Team (Use This Checklist):**

```bash
# 1. Create structure
mkdir -p teams/new-team/{agents,tests/test_data,migrations,config}
mkdir -p teams/new-team/docs/{1_IMPLEMENTATION,2_OPERATIONS,3_REFERENCE}

# 2. Create required files (5 only!)
touch teams/new-team/START_HERE.md  # Required
touch teams/new-team/README.md      # Required
touch teams/new-team/CLAUDE.md      # Recommended
touch teams/new-team/orchestrator.py
touch teams/new-team/docker-compose.yml

# 3. Copy team template files
cp teams/golf-enrichment/CLAUDE.md teams/new-team/
cp teams/golf-enrichment/docker-compose.yml teams/new-team/
# Customize for new team

# 4. Create minimum docs (only what's needed now!)
# DON'T create 10 docs on day 1!
# Start with START_HERE.md only
# Add implementation docs as you build

# 5. Create production structure
mkdir -p production/new-team/agents

# 6. Test locally before deploying
```

---

## 📊 **Team Health Metrics**

**Every team should track:**

| Metric | Target | Alert If |
|--------|--------|----------|
| Documentation files at root | ≤ 5 | > 5 |
| Cost per operation | Team-defined | > 125% of target |
| Test coverage | > 80% | < 70% |
| Deployment success rate | > 95% | < 90% |
| Production incidents/month | 0 | > 2 |

**Review monthly** in team standup

---

## 🚨 **Escalation (When Standards Violated)**

**If team has > 5 files at root:**
1. Consolidate status files into START_HERE.md
2. Move detailed specs to docs/1_IMPLEMENTATION/
3. Move background to docs/3_REFERENCE/
4. Delete temporary/duplicate files

**If costs exceed target by 25%:**
1. Review COST_OPTIMIZATION.md
2. Implement quick wins (contact filtering, etc.)
3. Test cost reduction
4. Update cost targets if justified

**If tests skipped before deploy:**
1. Rollback deployment if issues
2. Run full test suite
3. Document why tests were skipped
4. Add to CI/CD to prevent future

---

## 📖 **Standard File Locations (ALL Teams)**

| File Type | Location | Example |
|-----------|----------|---------|
| Entry point | teams/your-team/START_HERE.md | Required |
| Team overview | teams/your-team/README.md | Required |
| Team rules | teams/your-team/CLAUDE.md | Recommended |
| Agents | teams/your-team/agents/ | agent1.py, agent2.py |
| Orchestrator | teams/your-team/orchestrator.py | One file |
| Tests | teams/your-team/tests/ | test_agent1.py |
| Migrations | teams/your-team/migrations/ | 001_*.sql |
| Config | teams/your-team/config/ | field-mapping.json |
| Implementation docs | teams/your-team/docs/1_IMPLEMENTATION/ | Specs, templates |
| Operations docs | teams/your-team/docs/2_OPERATIONS/ | Playbooks |
| Reference docs | teams/your-team/docs/3_REFERENCE/ | Goals, roadmaps |
| Production code | production/your-team/ | (synced, don't edit) |

**Don't create:** teams/your-team/documentation/, teams/your-team/specs/, teams/your-team/guides/

---

## 🎓 **Learning from Golf Enrichment Team**

**What they did right:**
- ✅ Organized agents in agents/ folder
- ✅ Comprehensive edge case documentation
- ✅ Cost tracking and optimization
- ✅ Production/development separation

**What they learned (and you should avoid):**
- ⚠️ Created 14 .md files (took 2 hours to reorganize)
- ⚠️ Duplicated files between root and team
- ⚠️ Mixed implementation and reference docs
- ⚠️ No clear entry point initially

**Apply their lessons:** Follow 5-file limit from day 1!

---

## 🚀 **Quick Start for New Team**

**Day 1: Structure Only (Don't Over-Document!)**
```bash
# Create minimum structure
mkdir -p teams/new-team/{agents,tests,migrations}
mkdir -p teams/new-team/docs/{1_IMPLEMENTATION,2_OPERATIONS,3_REFERENCE}

# Create START_HERE.md ONLY (don't create 10 files!)
echo "# New Team - START HERE\n\nStatus: Just created\n\nNext: Build first agent" > teams/new-team/START_HERE.md

# Create README.md
echo "# New Team\n\nPurpose: {what this team does}" > teams/new-team/README.md

# That's it! Only 2 files on day 1
# Add docs as you build, not before!
```

**Day 2-7: Build Agents (Document As You Go)**
```bash
# Build agent
vim teams/new-team/agents/agent1.py

# Document in implementation (only when ready!)
vim teams/new-team/docs/1_IMPLEMENTATION/AGENT_SPECS.md

# Update entry point
vim teams/new-team/START_HERE.md
# Add: "Agent 1 complete, next: Agent 2"
```

**Don't:** Create goal.md, roadmap.md, vision.md, mission.md on day 1
**Do:** Add one "Background" section to START_HERE.md

---

## ✅ **Compliance Checklist (Before Team Goes to Production)**

- [ ] ≤ 5 .md files at team root
- [ ] START_HERE.md exists and is up-to-date
- [ ] docs/ organized into 1_IMPLEMENTATION, 2_OPERATIONS, 3_REFERENCE
- [ ] All agents have tests
- [ ] Cost documented and under target
- [ ] EDGE_CASE_PLAYBOOK.md exists with 5+ scenarios
- [ ] Production safety: Develop in teams/, deploy from production/
- [ ] Docker compose files exist (testing + production-mirror)
- [ ] No secrets committed

**Review:** Before first production deployment

---

**Last Updated:** October 18, 2024
**Maintained By:** Project lead
**Review Frequency:** Quarterly or when new pattern/anti-pattern discovered
