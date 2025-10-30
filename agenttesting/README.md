# Agent Testing Infrastructure

Clean, Docker-first testing environment for multi-agent workflows.

## Quick Start

### Run Docker Tests

```bash
# Build and start the service
docker-compose -f docker/docker-compose.apollo.yml up --build

# In another terminal, run tests
cd golf-enrichment
bash scripts/test_apollo_fixes.sh
```

### Check API Health

```bash
curl http://localhost:8000/health
```

## Structure

```
agenttesting/
├── docker/                    # Docker configurations
├── golf-enrichment/           # Golf course enrichment team
│   ├── agents/               # Production agent code
│   ├── orchestrators/        # Workflow coordinators
│   ├── api/                  # FastAPI wrapper
│   ├── utils/                # Shared utilities
│   ├── tests/                # Test files (unit/integration/pipeline)
│   ├── data/                 # Test fixtures
│   ├── scripts/              # Test runner scripts
│   ├── results/              # Test outputs (gitignored)
│   └── docs/                 # Testing documentation
└── shared/                    # Shared across teams (future)
```

## Team Folders

### Golf Enrichment

5-agent Apollo workflow for golf course prospecting automation.

- **Agents:** URL finder, Apollo discovery, course intelligence, water hazards, Supabase writer
- **Success Rate:** 80% (4/5 courses)
- **Cost:** $0.052/course (74% under budget)

See `golf-enrichment/docs/` for details.

## Docker Configurations

- `docker-compose.yml` - Standard test environment
- `docker-compose.test.yml` - Agent-specific testing
- `docker-compose.apollo.yml` - Apollo enrichment testing
- `Dockerfile` - Production container
- `Dockerfile.test` - Test container

## Adding a New Team

1. Create `{team-name}/` folder
2. Copy structure from `golf-enrichment/`
3. Add team-specific agents and tests
4. Update Docker configs if needed

## Migration Notes

This structure was created 2025-10-30 to consolidate testing infrastructure.

- **Archived:** `teams-golf-enrichment-archive-2025-10-30/`
- **Essential Files:** 45 files (44% reduction from 81 files)
- **Benefits:** Clear organization, Docker-first, scalable

See archive for historical testing work and exploration files.
