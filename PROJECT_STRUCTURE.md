# Project Structure Guide

**Last Updated:** October 18, 2024

This document provides a complete overview of the claude-agent-sdk-python project structure.

## Overview

This repository contains **two distinct systems**:

1. **Claude Agent SDK** - Python library for building Claude-powered agents
2. **Multi-Agent Workflows** - Production-ready orchestrated agent teams

## Directory Structure

```
claude-agent-sdk-python/
│
├── 📦 src/                          # SDK Library (Python Package)
│   └── claude_agent_sdk/
│       ├── client.py                # ClaudeSDKClient
│       ├── query.py                 # One-shot queries
│       ├── types.py                 # Type definitions
│       └── _internal/               # Internal implementation
│
├── 🤝 shared/                       # Shared Across All Teams
│   ├── agents/                      # Common reusable agents
│   ├── utils/                       # Shared utilities
│   │   ├── env_loader.py           # Environment config
│   │   └── json_parser.py          # JSON parsing
│   └── templates/                   # Team scaffolding
│
├── 👥 teams/                        # Agent Team Development
│   └── golf-enrichment/            # Golf course enrichment team
│       ├── agents/                 # 8 specialized agents
│       ├── orchestrator.py         # Workflow coordinator
│       ├── tests/                  # Team tests
│       ├── docker-compose.yml      # Local testing
│       └── README.md               # Team docs
│
├── 🚀 production/                   # Production Deployments
│   ├── golf-enrichment/            # Production for golf team
│   │   ├── Dockerfile              # Container config
│   │   ├── api.py                  # FastAPI wrapper
│   │   ├── render.yaml             # Render deployment
│   │   ├── agents/                 # Production agents
│   │   └── template/utils/         # Production utilities
│   └── scripts/
│       └── sync_to_production.py   # Sync script
│
├── 🧪 testing/                      # Testing Infrastructure
│   ├── sdk/                        # SDK tests
│   │   ├── unit/                   # Unit tests (12 files)
│   │   └── integration/            # E2E tests (8 files)
│   ├── integration/                # Cross-team tests
│   ├── docker/                     # Shared Docker configs
│   └── data/                       # Shared test data
│
├── 📚 docs/                         # Documentation
│   ├── sdk/                        # SDK documentation
│   ├── architecture/               # Architecture docs
│   │   └── multi_team_design.md   # Multi-team guide
│   ├── teams/                      # Team-specific docs
│   └── runbooks/                   # Operational guides
│
├── 📝 examples/                     # SDK Examples
│   ├── quick_start.py              # Basic usage
│   ├── streaming_mode.py           # Streaming
│   └── mcp_calculator.py           # MCP integration
│
├── 📦 archive/                      # Historical Code
│   ├── backups/                    # Backup files
│   └── poc-workflow/               # Original POC
│
└── 🛠️ scripts/                     # Utility Scripts
    ├── update_version.py           # Version management
    └── initial-setup.sh            # Setup automation
```

## Three Core Folders

### 1. 🧪 `testing/` - Build and Test Environment

**Purpose:** All testing happens here

**Structure:**
- `testing/sdk/unit/` - SDK unit tests
- `testing/sdk/integration/` - SDK integration tests
- `testing/integration/` - Cross-team integration tests
- `testing/docker/` - Shared Docker configs
- `testing/data/` - Shared test data

**Usage:**
```bash
# Run SDK tests
pytest testing/sdk/

# Run specific test
pytest testing/sdk/unit/test_client.py
```

### 2. 🚀 `production/` - Docker Deployment Folder

**Purpose:** Production code sent to Render (NEVER edit directly)

**Structure:**
- One folder per team (e.g., `golf-enrichment/`)
- Each contains: Dockerfile, api.py, render.yaml, agents/

**Usage:**
```bash
# Sync from teams/ to production/
python production/scripts/sync_to_production.py golf-enrichment

# Deploy to Render
cd production/golf-enrichment
git add . && git commit -m "Update" && git push
```

**Important:** Production is auto-synced from `teams/` and `shared/`. Never edit production code directly.

### 3. 📚 `docs/` - Documentation Folder

**Purpose:** All project documentation

**Structure:**
- `docs/sdk/` - SDK documentation
- `docs/architecture/` - Architecture guides
- `docs/teams/` - Team-specific docs
- `docs/runbooks/` - Operational procedures

## Workflows

### SDK Development
```bash
# 1. Make changes to src/
# 2. Update tests in testing/sdk/
# 3. Run tests
pytest testing/sdk/
# 4. Lint & format
python -m ruff check src/ testing/ --fix
python -m ruff format src/ testing/
# 5. Type check
python -m mypy src/
```

### Agent Team Development
```bash
# 1. Develop in teams/your-team/
cd teams/golf-enrichment
# ... modify agents, orchestrator ...

# 2. Test individual agents
pytest tests/test_agent1.py

# 3. Test locally with Docker
docker-compose up --build

# 4. Test production mirror
docker-compose -f docker-compose.production-mirror.yml up

# 5. Sync to production
python ../../production/scripts/sync_to_production.py golf-enrichment

# 6. Deploy
cd ../../production/golf-enrichment
git add . && git commit -m "Update golf-enrichment" && git push
```

### Creating New Team
```bash
# 1. Create team structure
mkdir -p teams/new-team/{agents,tests/test_data}

# 2. Copy template files
cp teams/golf-enrichment/docker-compose.yml teams/new-team/
cp teams/golf-enrichment/.env.example teams/new-team/

# 3. Develop agents and orchestrator
# ... create your agents ...

# 4. Create production structure
mkdir -p production/new-team/agents

# 5. Copy deployment files
cp production/golf-enrichment/{Dockerfile,api.py,render.yaml} production/new-team/

# 6. Update render.yaml with new team name

# 7. Sync and deploy
python production/scripts/sync_to_production.py new-team
```

## Key Files

### Root Level
- `CLAUDE.md` - Codebase structure and workflows
- `PROJECT_STRUCTURE.md` - This file
- `pyproject.toml` - Python project configuration
- `README.md` - Main SDK documentation

### Configuration
- `.gitignore` - Git ignore rules
- `.github/workflows/` - CI/CD pipelines

## Deployment Architecture

### Render Setup
**One Workspace, Multiple Services:**
- Each team = separate web service
- All share same Supabase database
- Independent deployment per team

**Current Teams:**
1. `golf-enrichment-api` - Golf course enrichment (deployed)

**Future Teams (planned for 4-6 total):**
2. `real-estate-api` - Real estate lead generation
3. `legal-research-api` - Legal document research
4. ... etc

## Important Notes

### Production Safety
⚠️ **NEVER edit `production/` directly!**
- Always develop in `teams/`
- Sync to production with script
- Production is auto-deployed to Render

### Testing
✅ **Always test before deploying:**
1. Unit tests: `pytest teams/your-team/tests/`
2. Docker local: `docker-compose up`
3. Production mirror: `docker-compose -f docker-compose.production-mirror.yml up`
4. Then deploy

### Environment Variables
🔐 **Never commit secrets:**
- Use `.env.example` for templates
- Set actual keys in Render dashboard
- Never commit `.env` files

## Quick Reference

### Common Commands
```bash
# SDK Tests
pytest testing/sdk/

# Lint & Format
python -m ruff check src/ testing/ --fix
python -m ruff format src/ testing/

# Type Check
python -m mypy src/

# Sync to Production
python production/scripts/sync_to_production.py <team-name>

# Local Docker Test
cd teams/<team-name>
docker-compose up --build
```

### File Locations
- SDK source: `src/claude_agent_sdk/`
- SDK tests: `testing/sdk/`
- Team code: `teams/<team-name>/`
- Production: `production/<team-name>/`
- Shared utils: `shared/utils/`
- Documentation: `docs/`

## Next Steps

1. **For SDK Development:** See `docs/sdk/`
2. **For New Agent Team:** See `teams/README.md`
3. **For Deployment:** See `docs/runbooks/`
4. **For Architecture:** See `docs/architecture/multi_team_design.md`

---

**Questions?** Check `docs/` or ask in project chat.
