# Setup Guide: Agent Workflow Testing Framework

Step-by-step guide to implement the POC methodology for a new agent team.

---

## 📋 Prerequisites

- ✅ Agent team already created in `teams/[team-name]/`
- ✅ Agents working individually
- ✅ Orchestrator coordinates workflow
- ✅ Docker environment set up
- ✅ Claude Code installed with MCP access

---

## 🎯 Implementation Checklist

### Step 1: Create Directory Structure

```bash
cd teams/[team-name]

# Create testing directories
mkdir -p tests/local
mkdir -p tests/baselines

# Verify structure
ls -la tests/
# Should show:
# tests/
# ├── local/
# └── baselines/
```

---

### Step 2: Copy Framework Templates

```bash
# Copy baseline runner from golf-enrichment
cp ../golf-enrichment/tests/local/run_baseline.py tests/local/

# Copy comparison tool
cp ../golf-enrichment/tests/local/compare_to_docker.py tests/local/

# Copy README for reference
cp ../golf-enrichment/tests/local/README.md tests/local/ (if exists)
```

---

### Step 3: Adapt run_baseline.py

**Edit:** `tests/local/run_baseline.py`

**Changes needed:**

```python
# 1. Update import paths for YOUR agents
from agents.your_agent1 import agent1_function
from agents.your_agent2 import agent2_function
# ... import all your agents

# 2. Update workflow to match YOUR orchestration
async def run_local_baseline(entity_id, entity_name, ...):
    # Run Agent 1
    agent1_result = await your_agent1_function(...)

    # Run Agent 2 with Agent 1's output
    agent2_result = await your_agent2_function(agent1_result, ...)

    # ... continue for all agents

    # Save baseline
    baseline = {
        "entity_id": entity_id,
        "agent_results": {...},
        "summary": {...}
    }

    with open(f"tests/baselines/entity_{entity_id}_baseline.json", "w") as f:
        json.dump(baseline, f, indent=2)
```

**Key Adaptations:**
- Change "course" → your entity type
- Update agent function names
- Adjust workflow sequence
- Modify summary calculations

---

### Step 4: Adapt compare_to_docker.py

**Edit:** `tests/local/compare_to_docker.py`

**Changes needed:**

```python
# 1. Update field comparisons for YOUR data
def compare_results(entity_id, tolerance=None):
    # Default tolerance for YOUR metrics
    tolerance = {
        "cost": 0.02,
        "count": 0,  # Your count field
        "confidence": 1  # Your confidence field
    }

    # Compare YOUR critical fields
    baseline_field = baseline["agent_results"]["agentX"]["your_field"]
    docker_field = docker["agent_results"]["agentX"]["your_field"]

    # ... comparison logic
```

**Fields to Compare:**
- Entity count (exact match)
- Cost (within tolerance)
- Classifications (exact or tolerance)
- IDs (exact match)
- Required fields (presence check)

---

### Step 5: Set Tolerance Thresholds

**Define what's acceptable:**

```python
# In compare_to_docker.py
TOLERANCE = {
    # Must match exactly
    "entity_count": 0,
    "entity_id": 0,

    # Acceptable variance
    "cost": 0.02,  # ±$0.02
    "confidence_score": 1,  # ±1 point
    "classification": 0,  # Exact match for classifications

    # AI variance acceptable
    "description_length": 50,  # ±50 characters
    "optional_field_count": 1  # ±1 optional field
}
```

**Guidelines:**
- Deterministic fields: 0 tolerance
- API costs: ±$0.01-0.02
- AI outputs: ±1-2 points
- Counts: 0 tolerance

---

### Step 6: Create Team Testing Skill

**Create:** `.claude/skills/[team]-testing/SKILL.md`

**Copy template from:** `.claude/skills/golf-testing/SKILL.md`

**Adapt:**
- Replace "golf course" with your entity type
- Update field validation for your schema
- Customize audit queries for your database
- Add team-specific troubleshooting

**Include:**
- Testing workflow
- Field validation checklist
- Database audit queries
- Troubleshooting guide

---

### Step 7: Create Slash Command

**Create:** `.claude/commands/test-local.md`

```markdown
Test {{team}} agents locally for {{entity}} {{id}}

Run agents using Claude Code MCP to establish baseline.
Saves results to teams/{{team}}/tests/baselines/{{entity}}_{{id}}.json
```

**Benefits:**
- Easy invocation
- Consistent format
- Team members can use immediately

---

### Step 8: Test the Framework

**Test with one entity:**

```bash
# 1. Run local baseline
python tests/local/run_baseline.py 1 "Test Entity" [params]

# Verify:
- [ ] Baseline file created
- [ ] Expected results displayed
- [ ] Docker command provided

# 2. Run Docker test
docker-compose up --build -d
[run test command from baseline output]

# Verify:
- [ ] Docker completes successfully
- [ ] Results saved to /tmp/

# 3. Compare
python tests/local/compare_to_docker.py 1

# Verify:
- [ ] Comparison runs
- [ ] Shows matches/differences
- [ ] Pass/fail status clear
- [ ] Comparison report saved
```

---

## 📚 Documentation Requirements

### For Your Team

**Create these files:**

1. **README.md** in `tests/local/`
   - How to run baseline tests
   - How to run comparisons
   - Interpretation of results

2. **Team Testing Skill**
   - Testing procedures
   - Validation checklists
   - Database queries
   - Troubleshooting

3. **Tolerance Documentation**
   - What thresholds mean
   - Why certain tolerances set
   - When to adjust

---

## 🔍 Validation Checklist

**Framework is properly set up when:**

- [ ] `tests/local/run_baseline.py` imports your agents
- [ ] `tests/local/compare_to_docker.py` compares your fields
- [ ] Baseline script saves to `tests/baselines/`
- [ ] Docker test command includes your entity ID parameter
- [ ] Comparison script loads from correct paths
- [ ] Tolerance thresholds appropriate for your use case
- [ ] Team testing skill documents your procedures
- [ ] Slash command works for your team

---

## 🎓 Best Practices for Setup

### Start Simple

**Phase 1:** Test 1 agent locally
**Phase 2:** Test full workflow locally
**Phase 3:** Add Docker comparison
**Phase 4:** Add tolerance refinement

### Use Golf Enrichment as Template

Don't start from scratch - copy and adapt:

```bash
# Copy entire testing framework
cp -r teams/golf-enrichment/tests/local teams/my-team/tests/
cp -r .claude/skills/golf-testing .claude/skills/my-team-testing

# Then adapt imports, field names, entity types
```

### Document As You Go

- Note which fields need exact match
- Document acceptable AI variance
- Record tolerance threshold reasoning
- Keep examples of good vs bad comparisons

---

## 🚨 Common Setup Issues

### Issue 1: Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'agents'`

**Fix:**
```python
# Add team directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

---

### Issue 2: Baseline Not Saving

**Symptom:** Baseline file not created

**Fix:**
```python
# Ensure baselines directory exists
baseline_dir = Path(__file__).parent.parent / "baselines"
baseline_dir.mkdir(parents=True, exist_ok=True)
```

---

### Issue 3: Comparison Fails to Load Files

**Symptom:** Files not found

**Fix:**
```python
# Use correct relative paths
baseline_file = Path(__file__).parent.parent / "baselines" / f"entity_{id}_baseline.json"
docker_file = Path(f"/tmp/entity{id}-docker.json")
```

---

## 📊 Measuring Success

### After Setup

**Test metrics:**
- Time to run local baseline: < 30 seconds
- Time to run Docker test: 2-3 minutes
- Time to compare: < 1 second
- Setup time investment: 1-2 hours
- Time savings per session: 30-60 minutes

**ROI:** Pays for itself after 2-3 testing sessions

---

## 🔄 Iterative Improvement

### Phase 1: Basic Framework (Week 1)
- Local baseline runner
- Manual comparison

### Phase 2: Automation (Week 2)
- Automated comparison
- Tolerance thresholds
- Pass/fail reporting

### Phase 3: CI/CD Integration (Week 3)
- GitHub Actions
- Automated regression tests
- Deployment gates

### Phase 4: Team Adoption (Week 4)
- Training sessions
- Documentation review
- Slash command usage
- Skill refinement

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Reference:** Golf enrichment team implementation
**Status:** Production-ready
