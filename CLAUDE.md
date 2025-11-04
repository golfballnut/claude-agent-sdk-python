# Claude Code Developer Guide

## 🎯 Quick Start (Fresh Session)

**Total orientation time: < 2 minutes**

### Current Active Work

**Golf Course Enrichment:** `/golf-enrichment-active/`
- **Entry:** `golf-enrichment-active/CLAUDE.md` (working directory guide)
- **Status:** `golf-enrichment-active/HANDOFF.md` (current session status)
- **Progress:** `golf-enrichment-active/docs/PROGRESS.md` (session log)
- **Architecture:** `golf-enrichment-active/docs/ARCHITECTURE.md` (technical design)

**SDK Development:** `/src/`
- **Entry:** `README.md` (root - SDK documentation)
- **Tests:** `testing/sdk/`
- **Code:** `src/claude_agent_sdk/`

### Specialized Projects

**SDK POC (Sessions 13-14):** `/golf-enrichment-sdk-poc/`
- MCP integration proof of concept
- Not actively developed
- Reference for SDK patterns

**Production Deployment:** `/production/golf-enrichment/`
- Live deployment code
- Synced from `golf-enrichment-active/` via scripts
- Deployed to Render

### Archive

**Location:** `.archive/` (hidden, gitignored)
- Historical work from Oct 2024 reorganization
- 168 .md files from previous iterations
- **Reference only** - not current work
- See `ARCHIVE_LOCATION.txt` for details

---

## 📐 Project Structure

```
claude-agent-sdk-python/
├── README.md                         # SDK documentation (external users)
├── CLAUDE.md                         # ← YOU ARE HERE (developers start here)
├── CHANGELOG.md                      # Version history
├── ARCHIVE_LOCATION.txt              # Where archive went
│
├── src/                              # SDK source code
│   └── claude_agent_sdk/
│       ├── client.py                 # ClaudeSDKClient for interactive sessions
│       ├── query.py                  # One-shot query function
│       ├── types.py                  # Type definitions
│       └── _internal/                # Internal implementation
│
├── examples/                         # SDK usage examples
├── scripts/                          # Utility scripts
│
├── golf-enrichment-active/           # ← CURRENT GOLF PROJECT WORK
│   ├── CLAUDE.md                    # Working directory guide
│   ├── HANDOFF.md                   # Current session status
│   ├── automation/                  # Edge functions & automation
│   ├── prompts/                     # LLM research prompts
│   ├── schemas/                     # JSON validation schemas
│   ├── docker/                      # Docker testing infrastructure
│   ├── testing/                     # Test data & fixtures
│   └── docs/
│       ├── PROGRESS.md              # Session-by-session log
│       ├── ARCHITECTURE.md          # Technical design
│       └── IMPLEMENTATION_MAP.md    # Business → code mapping
│
├── golf-enrichment-sdk-poc/         # SDK POC (not actively developed)
│   ├── README.md                    # POC overview
│   ├── agents/                      # Single research agent
│   └── orchestrator.py              # MCP test orchestrator
│
├── production/                       # Deployment targets
│   ├── golf-enrichment/             # Production golf enrichment
│   │   ├── Dockerfile
│   │   ├── api.py                   # FastAPI wrapper
│   │   └── render.yaml              # Render config
│   └── scripts/
│       └── sync_to_production.py    # Deployment sync script
│
├── testing/
│   ├── sdk/                         # SDK tests
│   │   ├── unit/                    # Unit tests
│   │   └── integration/             # Integration tests
│   └── data/                        # Shared test data
│
├── shared/                           # Shared utilities
│   ├── agents/                      # Common reusable agents
│   ├── utils/                       # Shared utilities
│   └── templates/                   # Project templates
│
├── docs/                            # General documentation
│   └── historical/                  # Archived design docs
│
├── .claude/                         # Claude Code configuration
│   ├── commands/                    # Slash commands
│   ├── skills/                      # Reusable skills (SOPs)
│   └── agents/                      # Specialized agents
│
└── .archive/                        # Hidden archive (gitignored)
    └── [168 .md files from Oct 2024]
```

---

## 🚀 Fresh Session Workflow

### For Golf Enrichment Work
1. Read this file (`CLAUDE.md`) - 60 seconds
2. Go to `golf-enrichment-active/HANDOFF.md` - Current session status
3. Check `golf-enrichment-active/docs/PROGRESS.md` - Recent work
4. **Start working** - Total orientation: < 2 minutes

### For SDK Development
1. Read `README.md` (root) - SDK overview
2. Browse `src/claude_agent_sdk/` - Source code
3. Check `testing/sdk/` - Test structure
4. **Start working**

### When User Says "Golf Enrichment"
→ Go to `/golf-enrichment-active/`
→ NOT agenttesting/ (renamed to golf-enrichment-active)
→ NOT teams/ (renamed to golf-enrichment-sdk-poc)
→ NOT archive/ (hidden in .archive/)

---

## 🛠️ Development Workflow

### SDK Development

```bash
# Lint and style
python -m ruff check src/ testing/ --fix
python -m ruff format src/ testing/

# Typecheck (only src/)
python -m mypy src/

# Run SDK tests
python -m pytest testing/sdk/

# Run specific test file
python -m pytest testing/sdk/unit/test_client.py
```

### Golf Enrichment Testing

**Prompt Testing:**
```bash
cd golf-enrichment-active
python test_prompt.py 1  # Phase 1: Single course
python test_prompt.py 2  # Phase 2: All courses
```

**Docker Testing:**
```bash
cd golf-enrichment-active/docker
cp .env.example .env  # Configure Supabase credentials
./test_validator.sh    # Run full validation suite
```

**Production Deployment:**
```bash
# Sync to production
python production/scripts/sync_to_production.py golf-enrichment

# Deploy (git push triggers Render build)
cd production/golf-enrichment
git add .
git commit -m "Deploy: [description]"
git push
```

---

## 📋 Navigation Rules

### Clear Naming Convention
- **`*-active/`** → Current development work
- **`*-poc/`** → Proof of concept / experimental
- **`*-sdk-poc/`** → SDK integration experiments
- **`production/`** → Deployment targets
- **`.archive/`** → Historical work (hidden)

### Documentation Hierarchy
1. **Root:** Minimal entry points only (5 files max)
2. **Project folders:** Project-specific docs in their own folders
3. **docs/:** General/shared documentation only
4. **No new root .md files** unless absolutely necessary

### Fresh Session Entry Points
1. `/README.md` - SDK users (external)
2. `/CLAUDE.md` - Developers (you start here) ← **SINGLE SOURCE OF TRUTH**
3. `/golf-enrichment-active/README.md` - Project overview
4. `/golf-enrichment-active/HANDOFF.md` - Current session

---

## 🎯 Project-Specific Guides

### Golf Course Enrichment

**Purpose:** Automated research, contact discovery, and outreach task creation for 15,000+ golf courses

**Key Areas:**
- **Research:** LLM-based web research (Claude/GPT prompts in `prompts/`)
- **Automation:** Supabase Edge Functions for ClickUp sync
- **Validation:** JSON schema validation and data quality checks
- **Deployment:** Render.com production service

**Documentation:**
- `golf-enrichment-active/CLAUDE.md` - Working directory guide
- `golf-enrichment-active/HANDOFF.md` - Current status (Session 14+)
- `golf-enrichment-active/docs/PROGRESS.md` - Detailed session log
- `golf-enrichment-active/docs/ARCHITECTURE.md` - System design

**Current Phase (Session 14):**
- Testing V2 5-section prompt with Claude Sonnet 4.5
- Building Render validator service
- Comparing V2 vs V1 research quality

### SDK Development

**Purpose:** Python SDK for building Claude-based agents with MCP tool support

**Key Files:**
- `src/claude_agent_sdk/client.py` - Interactive sessions
- `src/claude_agent_sdk/query.py` - One-shot queries
- `src/claude_agent_sdk/types.py` - Type definitions

**Testing:**
- `testing/sdk/unit/` - Unit tests
- `testing/sdk/integration/` - Integration tests

**Status:** Active development (Sessions 13-14: MCP integration)

---

## 🚨 Rules to Prevent Sprawl

1. **Archive is HIDDEN** - Never browse .archive/ during active work
2. **Root stays clean** - Max 5 .md files at root level
3. **One HANDOFF per project** - Update same file, don't create new ones
4. **Session notes go in docs/** - `docs/sessions/YYYY-MM-DD.md` if needed
5. **Clear naming** - active/poc/production suffixes required

---

## 📚 Additional Resources

### Claude Code Configuration
- **Slash commands:** `.claude/commands/` - Custom workflows
- **Skills:** `.claude/skills/` - Reusable SOPs (agent-debugging, supabase-to-clickup)
- **Agents:** `.claude/agents/` - Specialized task agents

### Skills Available
- `agent-debugging` - Production failure analysis methodology
- `supabase-to-clickup` - Database-to-CRM sync patterns
- `llm-api-testing` - LLM API testing strategies

### Important Documentation
- `golf-enrichment-active/docs/IMPLEMENTATION_MAP.md` - Business logic → code mapping
- `production/scripts/sync_to_production.py` - Deployment sync utility
- `docs/historical/` - Archived design documents

---

## 🎓 Tips for Productive Sessions

### Starting Fresh
1. **Don't explore the archive** - It's hidden for a reason
2. **Trust the naming** - "active" means current, "poc" means experimental
3. **Follow the pyramid** - CLAUDE.md → Project README → HANDOFF
4. **One source of truth** - This file (CLAUDE.md) is canonical

### During Development
- **Update HANDOFF.md** each session (don't create new status files)
- **Log in PROGRESS.md** for detailed session tracking
- **Archive old notes** to docs/sessions/ if keeping them
- **Keep root clean** - Move new docs to proper project folders

### Before Deploying
- Test in Docker first (`golf-enrichment-active/docker/`)
- Sync to production (`production/scripts/sync_to_production.py`)
- Monitor first deployments in Render logs
- Update HANDOFF.md with deployment status

---

**Last Updated:** 2024-11-03 (Navigation overhaul - Phase 1)
**Maintained By:** Development Team
**Questions?** See `.claude/NAVIGATION.md` for additional session guidance
