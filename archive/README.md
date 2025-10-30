# Archive Directory

This directory contains all archived code, documentation, and historical work from the Claude Agent SDK project.

## Contents

### `poc-workflow/`
**Archived:** Pre-October 2025
**Contains:** Proof-of-concept workflow implementations
**Reason:** Initial POC work, superseded by production implementations

### `teams-2025-10-30/`
**Archived:** October 30, 2025
**Contains:** Complete `teams/golf-enrichment/` folder (81 files)
**Reason:** Testing infrastructure reorganization
- Original teams/ structure before migration to agenttesting/
- Email enrichment research (16 test files)
- Historical test results and configurations
- Old agent implementations (pre-Apollo)
- Complete session notes and planning documents

**See:** `teams-2025-10-30/ARCHIVE_README.md` for full details

### `teams-old/`
**Archived:** October 30, 2025
**Contains:** teams/ folder renamed during reorganization
**Reason:** Same as teams-2025-10-30 (this is the working copy that was renamed)
**Note:** This is identical to `teams-2025-10-30/complete-teams-folder/`

---

## Archive Policy

### What Gets Archived
- Completed research work (exploration files after final implementation)
- Superseded implementations (old code after major refactors)
- Historical test results and configurations
- POC/prototype code after production deployment
- Documentation for deprecated features

### What Stays Active
- Current implementations (`agenttesting/`, `production/`, `src/`)
- Active tests and test infrastructure
- Current documentation
- Configuration files in use

### Archive Organization
Archives are organized by:
1. **Date:** When archived (YYYY-MM-DD format)
2. **Category:** What type of work (teams/, poc/, research/, etc.)
3. **Reason:** Why archived (documented in README.md)

---

## Accessing Archived Material

### teams-2025-10-30 Archive
For golf enrichment historical work:

**Email enrichment research:**
```bash
cd archive/teams-2025-10-30/complete-teams-folder/testing/email-enrichment/
```

**Old agent implementations:**
```bash
cd archive/teams-2025-10-30/complete-teams-folder/agents/
```

**Historical test results:**
```bash
cd archive/teams-2025-10-30/complete-teams-folder/testing/docker/
```

**Session notes:**
```bash
cd archive/teams-2025-10-30/complete-teams-folder/archive/sessions/
```

---

## Current vs Archived

| Category | Current Location | Archived Location |
|----------|------------------|-------------------|
| **Agent Testing** | `agenttesting/golf-enrichment/` | `archive/teams-2025-10-30/` |
| **Production** | `production/golf-enrichment/` | N/A (still active) |
| **SDK Source** | `src/` | N/A (still active) |
| **SDK Tests** | `testing/` | N/A (still active) |
| **POC Work** | N/A (archived) | `archive/poc-workflow/` |

---

## Restoration (If Needed)

To reference archived material:
```bash
# View archived code
cat archive/teams-2025-10-30/complete-teams-folder/[path]

# Copy archived file for reference
cp archive/teams-2025-10-30/complete-teams-folder/[file] [destination]
```

⚠️ **Do not restore entire archived folders to active development** - extract specific files only if needed.

---

## Archive Maintenance

### Monthly
- Review archives for size and relevance
- Compress very old archives if needed
- Update this README if new archives added

### Quarterly
- Evaluate if very old archives can be removed
- Verify archive integrity
- Update documentation links

---

## Questions?

- **What's archived?** See individual archive README.md files
- **Where's my old code?** Check `teams-2025-10-30/` for golf enrichment work
- **Current structure?** See root README.md and `agenttesting/README.md`

---

**Last Updated:** October 30, 2025
**Maintained By:** Development team
**Total Archives:** 3 directories
