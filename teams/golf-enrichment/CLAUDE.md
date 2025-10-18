# Claude Code Instructions - Golf Enrichment Team

**Team:** Golf Course Enrichment & Outreach Automation
**Last Updated:** October 18, 2024
**Purpose:** Standards and rules for developing this agent team

---

## 🚨 **CRITICAL RULES (Follow These!)**

### **Rule #1: Documentation Limit - MAX 5 Files at Team Root** ⭐

**ALLOWED at `teams/golf-enrichment/` root:**
1. ✅ START_HERE.md (entry point - REQUIRED)
2. ✅ README.md (team overview - REQUIRED)
3. ✅ CLAUDE.md (this file - team rules)
4. ✅ CHANGELOG.md (version history - optional)
5. ✅ [ONE flex spot for urgent notes]

**EVERYTHING ELSE goes in docs/**:
- Implementation specs → `docs/1_IMPLEMENTATION/`
- Operations guides → `docs/2_OPERATIONS/`
- Background context → `docs/3_REFERENCE/`

**Before creating new .md file, ask:**
1. Can this go in START_HERE.md? (if < 500 words, YES)
2. Can existing doc be updated instead?
3. Does this belong in docs/ subfolder?
4. Is this temporary? (use code comments or ClickUp task instead)

**If you create 6th .md file at root → STOP and consolidate!**

---

### **Rule #2: Update START_HERE.md, Don't Create New Status Files**

❌ **DON'T CREATE:**
- PROGRESS.md, STATUS.md, UPDATES.md
- NEXT_STEPS.md, TODO.md
- NOTES_[DATE].md

✅ **INSTEAD:**
- Update START_HERE.md "What's Next" section
- Update START_HERE.md "Current Status"
- Add dated section to START_HERE.md if needed

**Why:** One entry point is better than 5 status files

---

### **Rule #3: Cost Discipline - Every Agent < $0.02**

**Cost Targets:**
- Agent 1: < $0.02
- Agent 2: < $0.02
- Agents 3-7: < $0.02 each
- **Total per course: < $0.20** (with 4 contacts max)

**Test costs before deploying:**
```bash
pytest teams/golf-enrichment/tests/test_agent1.py -v
# Check output for cost data
```

**If agent exceeds budget:**
1. Optimize queries (reduce Perplexity calls)
2. Use cheaper model if possible
3. Cache results
4. Document in COST_OPTIMIZATION.md

**Track in:** `docs/2_OPERATIONS/COST_OPTIMIZATION.md`

---

### **Rule #4: Never Edit production/ Directly**

❌ **NEVER:**
```bash
# DON'T edit files in production/golf-enrichment/
vim production/golf-enrichment/agents/agent1.py  # NO!
```

✅ **INSTEAD:**
```bash
# Edit in teams folder
vim teams/golf-enrichment/agents/agent1.py

# Sync to production
python production/scripts/sync_to_production.py golf-enrichment

# Deploy
cd production/golf-enrichment
git add . && git commit -m "Update agent1" && git push
```

**Why:** Production is isolated, synced from development

---

### **Rule #5: Test Locally Before Deploying**

**Required testing sequence:**
```bash
# 1. Unit test
pytest teams/golf-enrichment/tests/test_agent1.py

# 2. Integration test
pytest teams/golf-enrichment/tests/test_orchestrator.py

# 3. Docker test
cd teams/golf-enrichment
docker-compose up --build

# 4. Production mirror test
docker-compose -f docker-compose.production-mirror.yml up

# 5. Only then: Sync and deploy
python ../../production/scripts/sync_to_production.py golf-enrichment
```

**Never skip steps 1-4!**

---

## 📁 **Project Structure (Where Things Go)**

### **Team Folder Organization:**

```
teams/golf-enrichment/
├── START_HERE.md ⭐ Entry point (update this for status)
├── README.md (team overview, rarely changes)
├── CLAUDE.md (this file - team rules)
├── CHANGELOG.md (version history - optional)
│
├── agents/ (all agent implementations)
│   ├── agent1_url_finder.py
│   ├── agent2_data_extractor.py
│   └── ... (8 agents total)
│
├── orchestrator.py (workflow coordinator)
│
├── tests/ (all test files)
│   ├── test_agent1.py
│   ├── test_orchestrator.py
│   └── test_data/
│
├── migrations/ (database migrations)
│   ├── 004_agent_integration_fields.sql
│   └── 005_outreach_tables.sql
│
├── docker-compose.yml (local testing)
├── docker-compose.production-mirror.yml (staging)
│
└── docs/ (detailed documentation - organized!)
    ├── 1_IMPLEMENTATION/ (what to build next)
    │   ├── CLICKUP_ARCHITECTURE.md
    │   ├── EDGE_FUNCTIONS.md
    │   └── OUTREACH_TASK_TEMPLATE.md
    ├── 2_OPERATIONS/ (how to operate)
    │   ├── RELIABILITY_PLAYBOOK.md
    │   ├── EDGE_CASE_PLAYBOOK.md
    │   └── COST_OPTIMIZATION.md
    └── 3_REFERENCE/ (background info)
        ├── goal.md
        ├── outreachgoalsv1_101725.md
        └── business_opportunities.md
```

**If you add a file not shown above → reconsider!**

---

## 🎯 **Development Workflow**

### **To Add New Agent:**

1. Create: `agents/agent9_new_capability.py`
2. Create: `tests/test_agent9.py`
3. Test: `pytest tests/test_agent9.py`
4. Update: `orchestrator.py` (add agent9 to workflow)
5. Update: `START_HERE.md` (note agent9 added)
6. Sync: `python ../../production/scripts/sync_to_production.py golf-enrichment`
7. Deploy: From production folder, git push

### **To Update Existing Agent:**

1. Edit: `agents/agent6_course_intelligence.py`
2. Test: `pytest tests/test_agent6.py`
3. Update: `docs/2_OPERATIONS/COST_OPTIMIZATION.md` if cost changed
4. Update: `START_HERE.md` with changes
5. Sync and deploy

### **To Add Documentation:**

**Ask first: Where does this belong?**

**Implementation detail** (migration, field spec, template)?
→ `docs/1_IMPLEMENTATION/FILENAME.md`

**Operations guide** (monitoring, errors, costs)?
→ `docs/2_OPERATIONS/FILENAME.md`

**Background context** (business goals, roadmap)?
→ `docs/3_REFERENCE/FILENAME.md`

**Quick status update**?
→ Update `START_HERE.md` (don't create new file!)

**Temporary note**?
→ Use code comment or ClickUp task (not .md file!)

---

## 📊 **Quality Standards**

### **Agent Quality Checklist:**

Every agent must have:
- [ ] Docstring with purpose, inputs, outputs
- [ ] Error handling (try/catch with meaningful errors)
- [ ] Cost tracking (log every API call cost)
- [ ] Type hints (use claude_agent_sdk types)
- [ ] Test file with 3+ test cases
- [ ] Cost < $0.02 target

### **Documentation Quality:**

Every implementation doc must have:
- [ ] Purpose statement
- [ ] Code examples
- [ ] Testing instructions
- [ ] Edge case notes
- [ ] Last updated date

### **Testing Requirements:**

Before deployment:
- [ ] Unit tests pass (all agents)
- [ ] Integration test passes (orchestrator)
- [ ] Cost test passes (< $0.20/course)
- [ ] Docker build succeeds
- [ ] Production mirror test works

---

## 🔧 **Common Tasks**

### **Update Agent Costs:**
```bash
# After optimizing agent
pytest tests/test_agent6.py

# Update cost doc
vim docs/2_OPERATIONS/COST_OPTIMIZATION.md
# Update: Agent 6 cost from $0.036 → $0.024

# Update START_HERE
vim START_HERE.md
# Update: "Cost per course: $0.19 → $0.17"
```

### **Add ClickUp Field:**
```bash
# 1. Add field in ClickUp UI
# 2. Get field ID from ClickUp API
# 3. Update config
vim config/clickup-field-mapping.json
# Add: {"new_field": "field_id_here"}

# 4. Update edge function
vim docs/1_IMPLEMENTATION/EDGE_FUNCTIONS.md
# Add field to create-outreach-task function

# 5. Document
vim docs/1_IMPLEMENTATION/CLICKUP_ARCHITECTURE.md
# Add to field list with purpose
```

### **Handle New Edge Case:**
```bash
# Discovered: "Contact on vacation auto-reply"

# 1. Document
vim docs/2_OPERATIONS/EDGE_CASE_PLAYBOOK.md
# Add: Edge Case #11: Vacation Auto-Reply

# 2. Update code if needed
vim agents/agent3_contact_enricher.py
# Add: Detection for vacation auto-reply

# 3. Update START_HERE
vim START_HERE.md
# Note: "Added vacation auto-reply handling"
```

---

## 💰 **Cost Monitoring (Weekly)**

**Check actual costs:**
```sql
-- In Supabase
SELECT
  DATE(enrichment_requested_at) as week,
  COUNT(*) as courses,
  AVG(agent_cost_usd) as avg_cost,
  SUM(agent_cost_usd) as total_cost
FROM golf_courses
WHERE enrichment_completed_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(enrichment_requested_at);
```

**If avg_cost > $0.25:**
1. Review: `docs/2_OPERATIONS/COST_OPTIMIZATION.md`
2. Implement: Contact filtering (limit to 4)
3. Implement: Agent 6 query consolidation
4. Test: Verify cost reduction
5. Update: START_HERE.md with new costs

---

## 🚀 **Deployment Checklist**

**Before every production deploy:**
- [ ] All tests pass locally
- [ ] Cost validated (< $0.20/course)
- [ ] Docker build succeeds
- [ ] START_HERE.md updated with changes
- [ ] Sync script run: `python production/scripts/sync_to_production.py golf-enrichment`
- [ ] Git commit from production folder
- [ ] Monitor Render deployment logs
- [ ] Test production endpoint: `curl https://agent7-water-hazards.onrender.com/health`

---

## 📚 **Documentation Maintenance**

### **Weekly:**
- Update START_HERE.md if status changed
- Review docs/ for outdated info
- Check if > 5 files at root (consolidate if so)

### **Monthly:**
- Update COST_OPTIMIZATION.md with actual costs
- Review EDGE_CASE_PLAYBOOK for new scenarios
- Update RELIABILITY_PLAYBOOK with learned issues

### **Quarterly:**
- Full docs review
- Archive outdated reference docs
- Update README.md if team mission changed

---

## 🎯 **Success Metrics**

**This team is successful if:**
- ✅ Cost < $0.20 per course (with 4 contacts)
- ✅ Success rate > 95% (enrichment completes)
- ✅ Documentation stays organized (< 5 root files)
- ✅ New contributors can start in < 30 minutes
- ✅ No production incidents from poor testing

**Track in:** START_HERE.md "Success Metrics" section

---

## 🚫 **Anti-Patterns (DON'T DO THIS)**

### **Documentation Anti-Patterns:**
❌ Creating PROGRESS.md at root (update START_HERE instead)
❌ Creating dated notes files (NOTES_OCT_18.md)
❌ Duplicating files (root + team folder)
❌ Mixing code and docs (orchestrator.py in docs/)
❌ Creating > 5 files at root without consolidating

### **Code Anti-Patterns:**
❌ Editing production/ directly
❌ Skipping tests before deploy
❌ Committing .env files
❌ Creating agents without cost tracking
❌ Deploying without docker-compose test

### **Cost Anti-Patterns:**
❌ Enriching all 7+ contacts (filter to 4!)
❌ Not tracking cost per agent
❌ Deploying optimizations without testing
❌ Ignoring cost alerts (> $0.25/course)

---

## 📖 **Quick Reference**

### **Where is...?**

**Entry point for new contributors:**
→ `START_HERE.md`

**What to build next:**
→ `docs/1_IMPLEMENTATION/`

**How to handle errors:**
→ `docs/2_OPERATIONS/RELIABILITY_PLAYBOOK.md`

**Why we built this:**
→ `docs/3_REFERENCE/goal.md`

**Current production URL:**
→ https://agent7-water-hazards.onrender.com

**Testing:**
→ `tests/` folder

**Database migrations:**
→ `migrations/` folder

---

## 🔄 **This File**

**When to update CLAUDE.md:**
- New critical rule discovered
- Common mistake pattern identified
- Development workflow changes
- New anti-pattern to avoid

**Who maintains:** Team lead + contributors
**Review frequency:** When onboarding new developers

---

## 📞 **Questions?**

- **Team questions:** Read START_HERE.md first
- **SDK questions:** See root README.md
- **Project structure:** See root PROJECT_STRUCTURE.md

---

**Remember: Keep it simple, keep it organized, keep costs low!** 🎯
