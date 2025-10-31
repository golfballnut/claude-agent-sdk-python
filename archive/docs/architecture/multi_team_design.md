# Multi-Team Agent Architecture

## Overview

This project supports multiple orchestrated agent teams, each deployed as independent services on Render. The architecture separates development, testing, and production to enable safe iteration and scaling to 4-6+ teams.

## Project Structure

```
claude-agent-sdk-python/
├── src/                    # SDK library (core product)
├── shared/                 # Shared across all teams
│   ├── agents/            # Common reusable agents
│   ├── utils/             # Shared utilities
│   └── templates/         # Team scaffolding templates
├── teams/                  # Development area for all teams
│   ├── golf-enrichment/   # Team 1: Golf course enrichment
│   ├── real-estate/       # Team 2: (future)
│   └── legal-research/    # Team 3: (future)
├── production/             # Production deployments (isolated)
│   ├── golf-enrichment/   # Prod for team 1
│   ├── scripts/           # Deployment automation
│   └── ...                # Prod for teams 2-6
├── testing/                # All testing infrastructure
│   ├── sdk/               # SDK tests
│   ├── integration/       # Cross-team tests
│   └── docker/            # Shared test configs
└── docs/                   # Documentation
```

## Key Principles

### 1. **Team Isolation**
- Each team has its own directory in `teams/`
- Teams can have custom agents + shared agents
- Independent testing and deployment

### 2. **Production Isolation**
- `production/` is completely separate from `teams/`
- Production code synced via `sync_to_production.py`
- Never edit production directly

### 3. **Shared Components**
- Common utilities in `shared/utils/`
- Reusable agents in `shared/agents/` (as we identify them)
- Templates for creating new teams

### 4. **Testing at All Levels**
- **Unit**: Individual agent testing
- **Integration**: Team workflow testing
- **Docker**: Local production-mirror testing
- **Staging**: Test tables in Supabase

## Deployment Model

### Render Workspace Structure

**One Workspace, Multiple Services:**

```
Render Workspace: "llama-agents-platform"
├── Service 1: golf-enrichment-api (starter plan)
├── Service 2: real-estate-api (starter plan)
├── Service 3: legal-research-api (starter plan)
└── Shared: Supabase database
```

**Benefits:**
- Cost effective (each service independently scalable)
- Shared monitoring and logging
- Single billing account
- Easy to add new teams

## Team Lifecycle

### Creating a New Team

```bash
# 1. Use template to scaffold new team
python scripts/create_new_team.py legal-research

# 2. Develop agents in teams/legal-research/
cd teams/legal-research
# ... build agents, orchestrator, tests ...

# 3. Test locally with Docker
docker-compose up --build

# 4. Sync to production
python ../../production/scripts/sync_to_production.py legal-research

# 5. Deploy to Render
cd production/legal-research
git add . && git commit -m "Add legal-research team" && git push
```

### Deploying Updates

```bash
# 1. Develop in teams/your-team/
# ... make changes to agents ...

# 2. Test locally
cd teams/your-team
pytest tests/
docker-compose up

# 3. Sync to production
python ../../production/scripts/sync_to_production.py your-team

# 4. Deploy
cd production/your-team
git add . && git commit -m "Update: description" && git push
# Auto-deploys if render.yaml has autoDeploy: true
```

## Agent Sharing Strategy

### When to Share Agents

Move agents to `shared/agents/` when:
- Used by 2+ teams
- Truly generic (no team-specific logic)
- Well-tested and stable

### When to Keep Private

Keep in `teams/*/agents/` when:
- Team-specific business logic
- Experimental or changing rapidly
- Single-team use case

### Example

```python
# shared/agents/email_finder.py - Generic email finding
# teams/golf-enrichment/agents/water_hazard_counter.py - Golf-specific
```

## Testing Strategy

### Level 1: Unit Tests (Individual Agents)
```bash
cd teams/golf-enrichment
pytest tests/test_agent1.py -v
```

### Level 2: Integration Tests (Full Workflow)
```bash
cd teams/golf-enrichment
pytest tests/test_orchestrator.py -v
```

### Level 3: Docker Testing (Local Environment)
```bash
cd teams/golf-enrichment
docker-compose up --build
# Test via API: curl http://localhost:8000/enrich-course ...
```

### Level 4: Production Mirror
```bash
cd teams/golf-enrichment
docker-compose -f docker-compose.production-mirror.yml up
# Exact production environment locally
```

## Cost Management

### Current Setup (Golf Enrichment)
- 1 Render service: $7/month (starter plan)
- Supabase: Free tier
- **Total: $7/month**

### With 6 Teams
- 6 Render services: 6 × $7 = $42/month
- Supabase: May need paid tier
- **Total: ~$50-60/month**

### Optimization Options
- Use cron jobs for scheduled workflows (cheaper than web services)
- Share services where workflows are similar
- Scale plans based on usage

## Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use Render dashboard for secrets
   - All teams share same API keys (via Render)

2. **Database Access**
   - Use test tables during development
   - Production tables only in prod environment
   - Service role keys via environment only

3. **Code Isolation**
   - No cross-team imports
   - Shared code only via `shared/`

## Monitoring & Debugging

### Render Dashboard
- View logs per service
- Monitor CPU/memory usage
- Track deployments

### Supabase Dashboard
- Monitor database writes
- Check RLS policies
- View table data

### Local Debugging
```bash
# Run with debug logging
LOG_LEVEL=DEBUG docker-compose up

# View agent output
docker logs golf-enrichment-test -f
```

## Future Enhancements

1. **CI/CD Pipeline**
   - Auto-test on PR
   - Auto-deploy on merge to main
   - Separate staging/production branches

2. **Shared Agent Library**
   - Extract common patterns
   - Version shared agents
   - Publish internal package

3. **Cross-Team Workflows**
   - Teams calling other teams
   - Shared event bus
   - Workflow chaining

## Questions?

See:
- `docs/runbooks/deploying_new_team.md` - Step-by-step team creation
- `docs/runbooks/testing_workflow.md` - Testing guidelines
- `docs/teams/golf-enrichment/README.md` - Example team structure
