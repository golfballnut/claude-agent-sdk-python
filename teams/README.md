# Agent Teams

This directory contains all agent team development workspaces. Each team represents an independent orchestrated workflow deployed to Render.

## Current Teams

### Golf Enrichment (`golf-enrichment/`)
**Purpose:** Enrich golf course data with contact information, intelligence, and property details.

**Agents:**
- Agent 1: URL Finder
- Agent 2: Data Extractor
- Agent 3: Contact Enricher (Email + LinkedIn)
- Agent 4: LinkedIn Finder
- Agent 5: Phone Finder
- Agent 6: Course Intelligence
- Agent 6.5: Contact Background
- Agent 7: Water Hazard Counter
- Agent 8: Supabase Writer

**Orchestrator:** 8-agent pipeline for complete course enrichment

**Status:** ✅ Production (deployed to Render)

---

## Creating a New Team

### Quick Start

```bash
# 1. Copy template (when available)
# python scripts/create_new_team.py your-team-name

# OR manually:
mkdir -p teams/your-team-name/{agents,tests/test_data}
cd teams/your-team-name

# 2. Create your agents
# ... agent1.py, agent2.py, etc ...

# 3. Create orchestrator
# ... orchestrator.py ...

# 4. Create tests
# ... tests/test_agent1.py ...

# 5. Add docker-compose for testing
# ... docker-compose.yml ...

# 6. Test locally
docker-compose up --build

# 7. Sync to production
python ../../production/scripts/sync_to_production.py your-team-name

# 8. Deploy to Render
cd ../../production/your-team-name
git add . && git commit -m "Add your-team-name" && git push
```

### Team Structure

```
your-team-name/
├── agents/              # Team-specific agents
│   ├── agent1_*.py
│   ├── agent2_*.py
│   └── ...
├── orchestrator.py      # Workflow coordinator
├── tests/              # Team tests
│   ├── test_agent1.py
│   ├── test_orchestrator.py
│   └── test_data/
├── docker-compose.yml  # Local testing
├── requirements.txt    # Team dependencies
├── .env.example        # Environment template
└── README.md          # Team documentation
```

### Required Files

#### `orchestrator.py`
Main workflow coordinator that calls agents in sequence.

#### `requirements.txt`
Python dependencies for your team. Include:
```
claude-agent-sdk>=0.1.3
# ... other dependencies ...
```

#### `.env.example`
Template for environment variables:
```bash
ANTHROPIC_API_KEY=your_key_here
# ... other API keys ...
```

#### `docker-compose.yml`
For local testing (copy from `golf-enrichment/docker-compose.yml`)

## Best Practices

### Agent Design
- Keep agents focused (single responsibility)
- Use shared utilities from `../../shared/utils/`
- Return structured data (dicts/lists, not strings)
- Include error handling
- Add docstrings with usage examples

### Testing
- Test each agent independently
- Test orchestrator with mock data
- Use `use_test_tables=True` for Supabase
- Test locally before deploying

### Documentation
- Document your workflow in README.md
- Include example requests/responses
- Document environment variables needed
- Note any special setup requirements

## Shared Resources

### Utilities (`../../shared/utils/`)
- `env_loader.py` - Load environment variables
- `json_parser.py` - Parse JSON from responses

### Templates (`../../shared/templates/`)
- `agent_template.py` - Boilerplate for new agents
- `orchestrator_template.py` - Orchestrator skeleton

## Deployment

See:
- `docs/architecture/multi_team_design.md` - Architecture overview
- `docs/runbooks/deploying_new_team.md` - Deployment guide
- `production/scripts/sync_to_production.py` - Sync script

## Questions?

Ask in project chat or see documentation in `docs/`.
