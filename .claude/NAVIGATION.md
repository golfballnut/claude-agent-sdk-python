# Navigation Guide for Claude Code Sessions

**Purpose:** Quick reference for Claude to orient in fresh sessions

---

## 🎯 Entry Point Hierarchy

### 1. First Stop: `/CLAUDE.md`
**This is THE entry point for all development work.**

What it contains:
- Quick start guide (< 2 min orientation)
- Project structure overview
- Clear paths to all active work
- Development workflows
- Navigation rules

**Action:** Read CLAUDE.md first, always.

---

### 2. Golf Enrichment Work

**Path:** `/golf-enrichment-active/`

**Entry files (in order):**
1. `golf-enrichment-active/CLAUDE.md` - Working directory guide
2. `golf-enrichment-active/HANDOFF.md` - Current session status
3. `golf-enrichment-active/docs/PROGRESS.md` - Detailed session log

**When user says:**
- "Golf enrichment" → `/golf-enrichment-active/`
- "Golf project" → `/golf-enrichment-active/`
- "Current work" → `/golf-enrichment-active/`
- "Enrichment automation" → `/golf-enrichment-active/`

**Do NOT go to:**
- ❌ `agenttesting/` - RENAMED to golf-enrichment-active
- ❌ `teams/golf-enrichment/` - RENAMED to golf-enrichment-sdk-poc
- ❌ `.archive/` - Historical work only

---

### 3. SDK Development

**Path:** `/src/claude_agent_sdk/`

**Entry files:**
1. `/README.md` (root) - SDK documentation
2. `src/claude_agent_sdk/client.py` - Main client code
3. `testing/sdk/` - Test structure

**When user says:**
- "SDK" → `/src/`
- "Claude SDK" → `/src/claude_agent_sdk/`
- "Client code" → `src/claude_agent_sdk/client.py`

---

### 4. Reference Projects

**SDK POC:** `/golf-enrichment-sdk-poc/`
- Sessions 13-14 MCP integration work
- NOT actively developed
- Reference for SDK patterns

**Production:** `/production/golf-enrichment/`
- Live deployment code
- Synced from golf-enrichment-active
- DO NOT edit directly (sync from active)

---

## 📐 Navigation Rules

### Clear Naming Convention

**Directory suffixes tell you everything:**

| Suffix | Meaning | Example | Action |
|--------|---------|---------|--------|
| `-active` | Current development work | `golf-enrichment-active/` | Work here |
| `-poc` | Proof of concept | `golf-enrichment-sdk-poc/` | Reference only |
| `-sdk-poc` | SDK integration POC | Same as above | Reference only |
| `production/` | Deployment target | `production/golf-enrichment/` | Don't edit directly |
| `.archive/` | Historical work | `.archive/` | Don't browse |

**Rule:** If it says "active", work there. If it says "poc", it's reference. If it's hidden (starts with `.`), ignore it.

---

### The Archive Problem

**Location:** `.archive/` (hidden, gitignored)

**Contains:**
- 168 .md files from Oct 2024 reorganization
- Old project iterations (teams-old, teams-2025-10-30, poc-workflow)
- Multiple copies of golf-enrichment work
- Historical PROGRESS.md files

**Rules:**
1. ❌ **NEVER browse .archive/ during active work**
2. ❌ **NEVER reference archive files as current**
3. ❌ **NEVER suggest code from archive**
4. ✅ **IF asked about history, mention `.archive/` exists but is not current**

**Why it exists:** To remove noise (68% of all .md files were archived work)

**How to access:** Only if user explicitly asks for historical context

---

### Documentation Hierarchy

**Root level (5 files maximum):**
1. `README.md` - SDK documentation (external users)
2. `CLAUDE.md` - Developer entry point (THIS IS THE SOURCE OF TRUTH)
3. `CHANGELOG.md` - Version history
4. `ARCHIVE_LOCATION.txt` - Where archive went
5. `LICENSE` / `CONTRIBUTING.md` - Standard files

**Project level:**
- Each project has own `README.md` and `HANDOFF.md`
- `docs/` subfolder for detailed documentation
- No more than 2-3 status files per project

**General docs:**
- `/docs/` - Shared/general documentation only
- `/docs/historical/` - Archived design documents

**Rule:** If you need to create a new .md file, put it in the appropriate project folder, NOT at root.

---

## 🚀 Fresh Session Workflow

### Standard Entry (Golf Work)

```
1. Read /CLAUDE.md                              (60 sec)
   ↓
2. Go to golf-enrichment-active/HANDOFF.md      (15 sec)
   ↓
3. Check golf-enrichment-active/docs/PROGRESS.md (30 sec)
   ↓
4. START WORKING                                 (< 2 min total)
```

### SDK Development

```
1. Read /CLAUDE.md                              (60 sec)
   ↓
2. Read /README.md                              (60 sec)
   ↓
3. Browse src/claude_agent_sdk/                 (30 sec)
   ↓
4. START WORKING                                 (< 3 min total)
```

---

## 🎯 Common User Requests

### "What's the current status?"
→ Read `golf-enrichment-active/HANDOFF.md`

### "Show me the golf enrichment code"
→ Navigate to `golf-enrichment-active/`
→ Check `automation/` for edge functions
→ Check `prompts/` for LLM research prompts

### "How do I test this?"
→ Read `golf-enrichment-active/CLAUDE.md` (test workflows)
→ Or read `/CLAUDE.md` section "Development Workflow"

### "What was done in the last session?"
→ Read `golf-enrichment-active/docs/PROGRESS.md` (latest entries)

### "How does the SDK work?"
→ Read `/README.md` (SDK documentation)
→ Browse `src/claude_agent_sdk/`

### "Where's the production code?"
→ `production/golf-enrichment/` (deployment target)
→ Synced from `golf-enrichment-active/`

---

## 🚨 Red Flags (Stop and Redirect)

### If you find yourself...

**Browsing .archive/**
→ STOP. Ask: "Is this historical context or active work?"
→ Redirect to `golf-enrichment-active/` for current work

**Creating new root .md files**
→ STOP. Ask: "Does this belong in a project folder?"
→ Put in `golf-enrichment-active/docs/` or `docs/`

**Confused about teams/ folder**
→ RENAMED to `golf-enrichment-sdk-poc/` (POC only)
→ Active work is in `golf-enrichment-active/`

**Finding multiple PROGRESS.md files**
→ Current one: `golf-enrichment-active/docs/PROGRESS.md`
→ Others are in .archive/ (historical)

**Seeing agenttesting/ references**
→ RENAMED to `golf-enrichment-active/`
→ Update any references to new name

---

## 📋 Quick Reference Card

### Where is...

| What | Location |
|------|----------|
| Current golf work | `/golf-enrichment-active/` |
| Current session status | `/golf-enrichment-active/HANDOFF.md` |
| Session log | `/golf-enrichment-active/docs/PROGRESS.md` |
| SDK source code | `/src/claude_agent_sdk/` |
| SDK docs | `/README.md` (root) |
| Production deployment | `/production/golf-enrichment/` |
| SDK POC | `/golf-enrichment-sdk-poc/` |
| Archive | `.archive/` (hidden) |
| Developer guide | `/CLAUDE.md` ← START HERE |

### File Count (After Cleanup)

- **Before:** 245 .md files visible (168 archived)
- **After:** 77 .md files visible (68% reduction)
- **Archive:** 168 .md files hidden in .archive/

### Navigation Efficiency

- **Before:** 20+ minutes to orient, frequent confusion
- **After:** < 2 minutes to orient, clear hierarchy

---

## 🎓 Best Practices

### DO:
✅ Read `/CLAUDE.md` first every session
✅ Trust the naming convention (active/poc/production)
✅ Follow the entry point hierarchy
✅ Update HANDOFF.md (don't create new status files)
✅ Keep root level clean (max 5 .md files)

### DON'T:
❌ Browse .archive/ during active work
❌ Create new root .md files
❌ Reference old teams/ or agenttesting/ paths
❌ Create multiple PROGRESS.md or status files
❌ Edit production/ directly (sync from active)

---

## 🔧 Troubleshooting

### "I can't find the golf enrichment code"
→ It's in `/golf-enrichment-active/` (NOT agenttesting/, that was renamed)

### "There are multiple golf-enrichment folders"
→ **Active:** `golf-enrichment-active/` (current work)
→ **POC:** `golf-enrichment-sdk-poc/` (reference only)
→ **Production:** `production/golf-enrichment/` (deployment)
→ **Archive:** `.archive/` (historical, ignore)

### "The CLAUDE.md file points to wrong folders"
→ Should be fixed now (2024-11-03 update)
→ If still wrong, that's a bug - update CLAUDE.md

### "I see references to agenttesting/ or teams/"
→ Those were renamed:
  - `agenttesting/golf-enrichment/` → `golf-enrichment-active/`
  - `teams/golf-enrichment/` → `golf-enrichment-sdk-poc/`
→ Update the reference

### "Which PROGRESS.md is current?"
→ `golf-enrichment-active/docs/PROGRESS.md` is THE current one
→ All others are in .archive/ (historical)

---

## 📊 Success Metrics

**You know navigation is working when:**

✅ Fresh session orients in < 2 minutes
✅ Zero confusion about active vs archived
✅ Clear understanding of project structure
✅ No browsing .archive/ accidentally
✅ Finding HANDOFF.md immediately
✅ Working in correct folder (golf-enrichment-active/)

**Navigation has FAILED if:**

❌ Taking > 5 minutes to orient
❌ Confused about which folder is current
❌ Referencing archive files as current
❌ Creating new root .md files
❌ Can't find current status quickly

---

**Last Updated:** 2024-11-03 (Navigation overhaul - Phase 1)
**Part of:** Project navigation cleanup
**See also:** `/CLAUDE.md` (main entry point)
