# Agent Skills Research
**Feature:** New Claude capability (announced 2025-01-16)
**Purpose:** Study for potential use in future agents
**Status:** Research phase - not implemented yet

---

## What Are Agent Skills?

**Definition:** Modular, filesystem-based capabilities that extend Claude's functionality through progressive disclosure.

**Key Insight:** "Agents need very specific tasks with mini goals" - Skills package domain expertise for automatic discovery and execution.

---

## How Skills Differ from Tools

| Aspect | Tools | Skills |
|--------|-------|--------|
| **Scope** | General utilities (web search, code execution) | Domain-specific expertise packages |
| **Loading** | Always available | Progressive disclosure (loaded on-demand) |
| **Instructions** | Minimal | Comprehensive (full procedural guidance) |
| **Resources** | Code only | Instructions + scripts + templates + data |
| **Discovery** | Explicit invocation | Automatic contextual matching |
| **Storage** | In-memory | Filesystem-based (persistent) |

---

## Progressive Disclosure Model

**3-Level Loading:**

**Level 1: Metadata (Always Loaded)**
- Skill name, description
- When to use (triggers)
- Input/output types
- **Token Cost:** Minimal (~50-100 tokens)

**Level 2: Instructions (On-Demand)**
- Full procedural guidance
- Rubrics, decision trees
- Examples
- **Token Cost:** Moderate (~500-2000 tokens)
- **Loaded:** When skill matches user request

**Level 3: Resources (As-Needed)**
- Scripts, templates, data files
- Reference documentation
- Historical examples
- **Token Cost:** Zero (executed, not loaded)
- **Accessed:** Via filesystem during execution

**Benefit:** Can have extensive domain knowledge without context bloat

---

## Architecture Pattern

**Filesystem Structure:**
```
.claude/skills/
├── golf_course_segmentation/
│   ├── skill.md               # Instructions (Level 2)
│   ├── metadata.yaml          # Discovery info (Level 1)
│   └── resources/             # Scripts/data (Level 3)
│       ├── segmentation_rubric.json
│       ├── industry_benchmarks.csv
│       └── scoring_algorithm.py
```

**Metadata (YAML Frontmatter):**
```yaml
---
skill_id: golf_course_segmentation
name: Golf Course Segmentation
description: Classifies golf courses as high-end, budget, or both based on indicators
version: 1.0
triggers:
  - golf course
  - segmentation
  - classify
  - high-end vs budget
inputs:
  - company_intel (text)
  - competitive_intel (text)
outputs:
  - segment (high-end|budget|both)
  - confidence (1-10)
  - signals (list of reasons)
---
```

**Instructions (Markdown):**
```markdown
# Golf Course Segmentation Skill

## When to Use
- User provides golf course intelligence data
- Need to classify as high-end, budget, or both
- Require evidence-based segmentation

## Instructions

1. Analyze company intelligence for indicators...
2. Score each indicator 1-10...
3. Apply decision tree (see resources/rubric.json)...
4. Return segment + confidence + signals

## Examples
[Examples of successful segmentations]
```

---

## Potential Skills for Our Workflow

### Skill 1: Golf Course Segmentation

**Purpose:** Classify golf courses (high-end vs budget vs both)

**Metadata:**
```yaml
skill_id: golf_course_segmentation
triggers: ["golf course", "segmentation", "classify"]
```

**Instructions:**
- High-end indicators (private, premium, ratings 4.5+)
- Budget indicators (public, affordable, ratings 3.5-4.5)
- Scoring rubric
- Confidence calculation

**Resources:**
- `segmentation_rubric.json` - Decision tree
- `training_examples.json` - 50 known cases (Richmond CC = high-end, etc.)
- `industry_benchmarks.csv` - Average ratings, pricing by segment

**Would Replace:** Part of Agent 6 segmentation logic

---

### Skill 2: Opportunity Scoring

**Purpose:** Score 6 range ball opportunity types (1-10)

**Metadata:**
```yaml
skill_id: range_ball_opportunity_scoring
triggers: ["opportunity", "score opportunities", "range ball"]
```

**Instructions:**
- Scoring logic per opportunity type
- Evidence requirements for high scores (9-10)
- Conservative scoring guidelines

**Resources:**
- `opportunity_definitions.json` - Criteria per opportunity
- `conversion_data.csv` - Historical: which scores converted
- `scoring_algorithm.py` - Automated scoring script

**Would Replace:** Part of Agent 6 opportunity scoring

---

### Skill 3: Value-Prop Conversation Generator

**Purpose:** Create personalized conversation starters based on segment + opportunities

**Metadata:**
```yaml
skill_id: value_prop_conversation_generator
triggers: ["conversation starter", "outreach message", "email opener"]
```

**Instructions:**
- Templates per value prop (buy, sell, lease)
- Personalization rules
- Relevance scoring
- Tone guidelines per segment

**Resources:**
- `templates/high_end_buy.txt` - High-end buy program starters
- `templates/budget_sell.txt` - Budget sell program starters
- `best_performing.json` - Highest response-rate starters
- `personalization_rules.py` - Dynamic field insertion

**Would Replace:** Part of Agent 6 conversation generation

---

### Skill 4: Business Intel Aggregator

**Purpose:** Combine multiple Perplexity queries into structured intelligence

**Metadata:**
```yaml
skill_id: business_intel_aggregator
triggers: ["business intelligence", "gather intel", "research company"]
```

**Instructions:**
- Query templates (company, industry, competitive)
- Data extraction patterns
- Synthesis rules

**Resources:**
- `query_templates.json` - Perplexity query formats
- `extraction_patterns.py` - Regex/parsing for key data
- `synthesis_rubric.md` - How to combine intel

**Would Replace:** Part of Agent 6 data gathering

---

## When to Use Skills (Decision Framework)

### Use Skills When:
✅ **Reusable across multiple agents**
- Example: Segmentation logic used by Agent 6, 7, 8+

✅ **Complex domain knowledge**
- Example: Opportunity scoring has many rules/edge cases

✅ **Evolves based on data**
- Example: Conversation starters improve as we learn what works

✅ **Benefits from progressive disclosure**
- Example: Large instruction sets that aren't always needed

### Use Custom Tools (Current Approach) When:
✅ **Simple, specific task**
- Example: Call Perplexity API (straightforward)

✅ **One-off functionality**
- Example: Parse specific JSON format (not reused)

✅ **Real-time external API**
- Example: Hunter.io email lookup (can't be pre-packaged)

✅ **Requires state/secrets**
- Example: API keys, session management

---

## Potential Migration Path

### Phase 1: Keep Current Agents (Custom Tools)
**Now:** All agents use custom tools (proven, working)
**Reason:** Don't introduce new complexity while building infrastructure

### Phase 2: Build First Skill (Small Scope)
**When:** After orchestrator complete
**Skill:** Conversation Generator (least critical, easy to test)
**Reason:** Learn skills pattern without risking core functionality

### Phase 3: Migrate High-Value Skills
**When:** After Phase 2 success
**Skills:**
1. Segmentation (reused across multiple agents)
2. Opportunity Scoring (complex rubric, benefits from resources)
**Reason:** Highest ROI for skills architecture

### Phase 4: Evaluate
**Question:** Did skills improve maintainability/performance?
**If Yes:** Migrate remaining logic
**If No:** Keep custom tools

---

## Skills for Future Agents (Beyond Golf Courses)

If system expands to other industries:

**Skill: Industry Segmentation**
- Generalize golf course segmentation
- Support: Hotels, restaurants, retail, etc.
- Use resources/industry_name.json for industry-specific rules

**Skill: Opportunity Discovery**
- Generalize opportunity scoring
- Learn from patterns across industries
- Auto-suggest new opportunities based on data

**Skill: Multi-Channel Outreach**
- Beyond email: LinkedIn, phone, direct mail
- Channel selection based on segment
- A/B testing framework built-in

---

## Code Examples (from Claude Docs)

### Using a Pre-Built Skill (PowerPoint)

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
        ]
    },
    messages=[{"role": "user", "content": "Create a presentation on our Q4 results"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

### Creating Custom Skill (Structure)

**File:** `.claude/skills/my_skill/skill.md`

```markdown
---
skill_id: my_skill
name: My Custom Skill
description: What this skill does
version: 1.0
triggers:
  - keyword1
  - keyword2
---

# My Custom Skill Instructions

## When to Use
[Conditions for using this skill]

## Procedure
1. Step 1...
2. Step 2...
3. Step 3...

## Resources Available
- /resources/template.json
- /resources/script.py

## Output Format
[Expected output structure]
```

---

## Research Questions (To Answer Later)

1. **Can skills call other skills?**
   - Would enable: Segmentation skill → Opportunity skill → Conversation skill

2. **Can skills use external APIs?**
   - Would enable: Intel skill calling Perplexity directly

3. **How do skills handle state?**
   - Important for: Multi-step workflows

4. **Can skills be tested independently?**
   - Important for: Quality assurance

5. **Do skills work in Claude SDK?**
   - **Critical:** All our agents use Claude SDK, not API directly

---

## Next Steps

**Immediate:**
- [x] Document skills feature (this file)
- [ ] Test if SDK supports skills (probably not yet)
- [ ] Monitor Claude SDK updates for skills support

**Short-Term (After Phase 4):**
- [ ] Build first skill prototype (conversation generator)
- [ ] Test skills vs custom tools performance
- [ ] Measure maintainability benefits

**Long-Term (After Production):**
- [ ] Migrate high-value logic to skills
- [ ] Build skill library for golf course outreach
- [ ] Generalize skills for other industries

---

**Recommendation:** Study skills, but don't use yet. Current custom tools pattern is proven and working.

**Revisit:** When Claude SDK adds skills support OR when we need to scale to multiple industries.

---

**Last Updated:** 2025-01-17
**Status:** Research complete, implementation future
