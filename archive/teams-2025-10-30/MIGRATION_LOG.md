# Migration Log - Teams to AgentTesting
**Date:** October 30, 2025
**From:** `teams/golf-enrichment/`
**To:** `agenttesting/golf-enrichment/`

## Migration Summary

- **Files Migrated:** 45 essential files
- **Files Archived:** 35+ historical files
- **Reduction:** 44% fewer active files
- **Structure:** Reorganized into clean Docker-first layout

---

## File-by-File Migration Map

### Docker Configurations (5 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/Dockerfile` | `agenttesting/docker/Dockerfile` |
| `teams/golf-enrichment/Dockerfile.test` | `agenttesting/docker/Dockerfile.test` |
| `teams/golf-enrichment/docker-compose.yml` | `agenttesting/docker/docker-compose.yml` |
| `teams/golf-enrichment/docker-compose.test.yml` | `agenttesting/docker/docker-compose.test.yml` |
| `teams/golf-enrichment/docker-compose.apollo.yml` | `agenttesting/docker/docker-compose.apollo.yml` |

---

### Agent Code (11 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/agents/agent1_url_finder.py` | `agenttesting/golf-enrichment/agents/agent1_url_finder.py` |
| `teams/golf-enrichment/agents/agent2_apollo_discovery.py` | `agenttesting/golf-enrichment/agents/agent2_apollo_discovery.py` |
| `teams/golf-enrichment/agents/agent2_1_linkedin_company.py` | `agenttesting/golf-enrichment/agents/agent2_1_linkedin_company.py` |
| `teams/golf-enrichment/agents/agent2_2_perplexity_research.py` | `agenttesting/golf-enrichment/agents/agent2_2_perplexity_research.py` |
| `teams/golf-enrichment/agents/agent2_data_extractor.py` | `agenttesting/golf-enrichment/agents/agent2_data_extractor.py` |
| `teams/golf-enrichment/agents/agent3_contact_enricher.py` | `agenttesting/golf-enrichment/agents/agent3_contact_enricher.py` |
| `teams/golf-enrichment/agents/agent4_linkedin_finder.py` | `agenttesting/golf-enrichment/agents/agent4_linkedin_finder.py` |
| `teams/golf-enrichment/agents/agent5_phone_finder.py` | `agenttesting/golf-enrichment/agents/agent5_phone_finder.py` |
| `teams/golf-enrichment/agents/agent6_course_intelligence.py` | `agenttesting/golf-enrichment/agents/agent6_course_intelligence.py` |
| `teams/golf-enrichment/agents/agent7_water_hazard_counter.py` | `agenttesting/golf-enrichment/agents/agent7_water_hazard_counter.py` |
| `teams/golf-enrichment/agents/agent8_supabase_writer.py` | `agenttesting/golf-enrichment/agents/agent8_supabase_writer.py` |

---

### Orchestrators (2 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/orchestrator.py` | `agenttesting/golf-enrichment/orchestrators/orchestrator.py` |
| `teams/golf-enrichment/orchestrator_apollo.py` | `agenttesting/golf-enrichment/orchestrators/orchestrator_apollo.py` |

---

### API & Utils (3 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/api.py` | `agenttesting/golf-enrichment/api/api.py` |
| `teams/golf-enrichment/template/utils/env_loader.py` | `agenttesting/golf-enrichment/template/utils/env_loader.py` |
| `teams/golf-enrichment/template/utils/json_parser.py` | `agenttesting/golf-enrichment/template/utils/json_parser.py` |

---

### Unit Tests (2 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/testing/agents/test_agent1.py` | `agenttesting/golf-enrichment/tests/unit/test_agent1.py` |
| `teams/golf-enrichment/testing/agents/test_apollo_validation.py` | `agenttesting/golf-enrichment/tests/unit/test_apollo_validation.py` |

---

### Integration Tests (1 file)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/testing/integration/test_contact_waterfall_full.py` | `agenttesting/golf-enrichment/tests/integration/test_contact_waterfall_full.py` |

---

### Pipeline Tests (5 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/test_final_pipeline.py` | `agenttesting/golf-enrichment/tests/pipeline/test_final_pipeline.py` |
| `teams/golf-enrichment/test_apollo_enrichment.py` | `agenttesting/golf-enrichment/tests/pipeline/test_apollo_enrichment.py` |
| `teams/golf-enrichment/test_apollo_fixes.py` | `agenttesting/golf-enrichment/tests/pipeline/test_apollo_fixes.py` |
| `teams/golf-enrichment/test_apollo_search.py` | `agenttesting/golf-enrichment/tests/pipeline/test_apollo_search.py` |
| `teams/golf-enrichment/test_direct_scrape.py` | `agenttesting/golf-enrichment/tests/pipeline/test_direct_scrape.py` |

---

### Test Data (4 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/testing/data/belmont.json` | `agenttesting/golf-enrichment/data/belmont.json` |
| `teams/golf-enrichment/testing/data/richmond.json` | `agenttesting/golf-enrichment/data/richmond.json` |
| `teams/golf-enrichment/testing/data/stonehenge.json` | `agenttesting/golf-enrichment/data/stonehenge.json` |
| `teams/golf-enrichment/testing/data/apollo_duplicate_contacts.json` | `agenttesting/golf-enrichment/data/apollo_duplicate_contacts.json` |

---

### Test Scripts (3 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/testing/docker/test_apollo_fixes.sh` | `agenttesting/golf-enrichment/scripts/test_apollo_fixes.sh` |
| `teams/golf-enrichment/testing/docker/test_failed_courses_docker.sh` | `agenttesting/golf-enrichment/scripts/test_failed_courses.sh` |
| `teams/golf-enrichment/testing/debug_apollo_api.sh` | `agenttesting/golf-enrichment/scripts/debug_apollo_api.sh` |

---

### Documentation (2 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/testing/SESSION_SUMMARY_OCT30.md` | `agenttesting/golf-enrichment/docs/SESSION_SUMMARY_OCT30.md` |
| `teams/golf-enrichment/testing/APOLLO_DEBUG_HANDOFF_OCT30.md` | `agenttesting/golf-enrichment/docs/APOLLO_DEBUG_HANDOFF_OCT30.md` |

---

### Configuration Files (6 files)

| Old Location | New Location |
|--------------|--------------|
| `teams/golf-enrichment/requirements.txt` | `agenttesting/requirements.txt` + `agenttesting/golf-enrichment/requirements.txt` |
| `teams/golf-enrichment/.env.example` | `agenttesting/.env.example` |
| `teams/golf-enrichment/README.md` | `agenttesting/golf-enrichment/README.md` (updated for new structure) |
| N/A (created new) | `agenttesting/.gitignore` |
| N/A (created new) | `agenttesting/README.md` |
| N/A (created new) | `agenttesting/golf-enrichment/results/.gitkeep` |

---

## Files Archived (Not Migrated)

### Email Enrichment Research (ARCHIVED)
- `teams/golf-enrichment/testing/email-enrichment/test_apollo_two_step.py`
- `teams/golf-enrichment/testing/email-enrichment/test_apollo_mixed_people.py`
- `teams/golf-enrichment/testing/email-enrichment/test_apollo_export_email.py`
- `teams/golf-enrichment/testing/email-enrichment/test_apollo_contacts_endpoint.py`
- `teams/golf-enrichment/testing/email-enrichment/test_apollo_org_search_filtered.py`
- `teams/golf-enrichment/testing/email-enrichment/test_hunter_nc_baseline.py`
- `teams/golf-enrichment/testing/email-enrichment/test_hunter_mcp_validation.py`
- `teams/golf-enrichment/testing/email-enrichment/test_hunter_vs_apollo_real.py`
- `teams/golf-enrichment/testing/email-enrichment/test_apollo_vs_database_10_courses.py`
- `teams/golf-enrichment/testing/email-enrichment/test_apollo_api_connection.py`
- `teams/golf-enrichment/testing/email-enrichment/test_apollo_people_match.py`
- `teams/golf-enrichment/testing/email-enrichment/test_hunter_fallback_integration.py`
- `teams/golf-enrichment/testing/email-enrichment/test_agent2_apollo_5_courses.py`
- `teams/golf-enrichment/testing/email-enrichment/test_orchestrator_apollo_fixes.py`
- Plus 6 documentation files

**Reason:** Research completed Oct 29-30. Final implementation is in agent2_apollo_discovery.py.

### Redundant Root Test Files (ARCHIVED)
- `teams/golf-enrichment/test_apollo_fixes_direct.py`
- `teams/golf-enrichment/test_jina_fallback.py`
- `teams/golf-enrichment/test_firecrawl_fallback.py`
- `teams/golf-enrichment/test_quick.py`
- `teams/golf-enrichment/agents/test_agent2_firecrawl.py`

**Reason:** Duplicate tests or exploratory work not part of core Docker validation.

### Old Agent Unit Tests (ARCHIVED)
- `teams/golf-enrichment/testing/agents/test_agent2.py`
- `teams/golf-enrichment/testing/agents/test_agent2_configs.py`
- `teams/golf-enrichment/testing/agents/test_agent2_simple.py`
- `teams/golf-enrichment/testing/agents/test_agent3.py`
- `teams/golf-enrichment/testing/agents/test_agent3_confidence.py`
- `teams/golf-enrichment/testing/agents/test_agent4.py`
- `teams/golf-enrichment/testing/agents/test_agent5.py`
- `teams/golf-enrichment/testing/agents/test_agent6.py`
- `teams/golf-enrichment/testing/agents/test_hunter_confidence.py`

**Reason:** Many agents replaced by agent2_apollo_discovery.py. Old implementation tests not needed.

### Historical Docker Configs/Results (ARCHIVED)
- `teams/golf-enrichment/testing/docker/APOLLO_DOCKER_TEST_RESULTS_OCT29.md`
- `teams/golf-enrichment/testing/docker/IMPLEMENTATION_SUMMARY_102825.md`
- `teams/golf-enrichment/testing/docker/docker_waterfall_results_102825.md`
- `teams/golf-enrichment/testing/docker/compare_to_docker.py`
- `teams/golf-enrichment/testing/docker/run_baseline.py`
- `teams/golf-enrichment/testing/docker/Dockerfile.apollo-fix`
- `teams/golf-enrichment/testing/docker/docker-compose.apollo-fix.yml`

**Reason:** Historical test results and old Docker configs. Current configs at agenttesting/docker/.

### Integration Test Redundancy (ARCHIVED)
- `teams/golf-enrichment/testing/integration/test_fallback_sources.py`
- `teams/golf-enrichment/testing/integration/test_water_hazard_detection.py`

**Reason:** test_contact_waterfall_full.py is the comprehensive E2E test. Narrow tests not essential.

### Monitoring Tests (ARCHIVED)
- `teams/golf-enrichment/monitoring/tests/test_anthropic_usage.py`
- `teams/golf-enrichment/monitoring/tests/test_jina_limits.py`
- `teams/golf-enrichment/monitoring/tests/test_supabase_metrics.py`
- `teams/golf-enrichment/monitoring/tests/test_firecrawl_api.py`
- `teams/golf-enrichment/monitoring/tests/test_hunter_api.py`
- `teams/golf-enrichment/monitoring/tests/test_perplexity_api.py`
- `teams/golf-enrichment/monitoring/tests/test_clickup_usage.py`
- `teams/golf-enrichment/monitoring/tests/test_render_metrics.py`
- `teams/golf-enrichment/monitoring/tests/test_brightdata_api.py`

**Reason:** API monitoring tests - useful for operations but not essential for Docker agent testing.

---

## Path Changes Summary

### Before (teams/)
```
teams/golf-enrichment/
├── Dockerfile, docker-compose.yml (root)
├── agents/ (11 files)
├── orchestrator.py, orchestrator_apollo.py (root)
├── api.py (root)
├── template/utils/ (2 files)
├── test_*.py (5 files at root)
├── testing/
│   ├── agents/ (12 test files)
│   ├── integration/ (3 test files)
│   ├── docker/ (scripts + results)
│   ├── email-enrichment/ (16 files)
│   └── data/ (4 files)
└── docs/ (operational docs)
```

### After (agenttesting/)
```
agenttesting/
├── docker/ (5 Docker configs)
├── golf-enrichment/
│   ├── agents/ (11 files)
│   ├── orchestrators/ (2 files)
│   ├── api/ (1 file)
│   ├── template/utils/ (2 files)
│   ├── tests/
│   │   ├── unit/ (2 files)
│   │   ├── integration/ (1 file)
│   │   └── pipeline/ (5 files)
│   ├── data/ (4 test data files)
│   ├── scripts/ (3 test runners)
│   ├── results/ (gitignored)
│   └── docs/ (2 essential docs)
├── .env.example
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Benefits of New Structure

1. **Clarity:** Docker configs in obvious location (`docker/`)
2. **Organization:** Tests separated by type (unit/integration/pipeline)
3. **Clean:** Only 45 essential files (vs 81 before)
4. **Scalable:** Easy to add new teams
5. **Fast:** New developers find tests in seconds

---

## Validation Checklist

After migration, verified:
- [x] Docker builds successfully
- [x] Docker runs and API responds at port 8001
- [x] Health endpoint returns 200 OK
- [x] File structure matches plan
- [x] All essential files present
- [x] Archive complete

---

**Migration Completed:** October 30, 2025
**Status:** Successful
**Docker Build:** ✅ Working
**API Health:** ✅ Healthy
