# Workflow

```bash
# Lint and style
# Check for issues and fix automatically
python -m ruff check src/ testing/ --fix
python -m ruff format src/ testing/

# Typecheck (only done for src/)
python -m mypy src/

# Run SDK tests
python -m pytest testing/sdk/

# Run specific test file
python -m pytest testing/sdk/unit/test_client.py
```

# Codebase Structure

## SDK (Core Library)
- `src/claude_agent_sdk/` - Main package
  - `client.py` - ClaudeSDKClient for interactive sessions
  - `query.py` - One-shot query function
  - `types.py` - Type definitions
  - `_internal/` - Internal implementation details
    - `transport/subprocess_cli.py` - CLI subprocess management
    - `message_parser.py` - Message parsing logic

## Agent Teams (Multi-Agent Workflows)
- `teams/` - Development for all agent teams
  - `golf-enrichment/` - Golf course enrichment workflow
    - `agents/` - Team-specific agents
    - `orchestrator.py` - Workflow orchestration
    - `tests/` - Team tests
    - `docker-compose.yml` - Local testing

- `shared/` - Shared across all teams
  - `agents/` - Common reusable agents
  - `utils/` - Shared utilities
  - `templates/` - Team templates

## Production (Deployment)
- `production/` - Production code (isolated from development)
  - `golf-enrichment/` - Production deployment for golf team
    - `Dockerfile` - Container configuration
    - `api.py` - FastAPI wrapper
    - `render.yaml` - Render deployment config
    - `agents/` - Production agent code
  - `scripts/` - Deployment scripts
    - `sync_to_production.py` - Sync team code to production

## Testing
- `testing/` - All testing infrastructure
  - `sdk/unit/` - SDK unit tests
  - `sdk/integration/` - SDK e2e tests
  - `integration/` - Cross-team integration tests
  - `docker/` - Shared Docker configs
  - `data/` - Shared test data
