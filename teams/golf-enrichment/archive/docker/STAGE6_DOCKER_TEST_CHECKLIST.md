# Stage 6 Docker Testing Checklist - Agent 4 Validation

**Following SOP:** Test in Docker BEFORE production deployment
**Course:** 142 (Country Club of Fairfax) - User requested
**Critical:** Validate Agent 4 works in containerized environment

---

## Pre-Test Checklist

- [x] Docker build succeeded
- [ ] Agent 4 enhanced with comprehensive data extraction
- [ ] BRIGHTDATA_API_TOKEN in docker-compose.yml env vars
- [ ] .env file has BRIGHTDATA_API_TOKEN value

---

## Test Execution

### 1. Start Docker Container
```bash
docker-compose up
```

**Expected:**
```
✅ golf-enrichment-test container starts
✅ Uvicorn running on http://0.0.0.0:8000
✅ Health check passes
```

### 2. Test Health Endpoint
```bash
curl http://localhost:8000/health
```

**Expected:** `{"status": "healthy"}`

### 3. Enrich Course 142
```bash
curl -X POST http://localhost:8000/enrich-course \
  -H 'Content-Type: application/json' \
  -d '{
    "course_id": 142,
    "course_name": "Country Club of Fairfax",
    "state_code": "VA",
    "use_test_tables": true
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "course_name": "Country Club of Fairfax",
  "summary": {
    "contacts_enriched": 3,
    "total_cost_usd": 0.15
  }
}
```

---

## Validation Checklist

### Docker Logs Validation

**Check Agent 4 is called:**
```bash
docker-compose logs | grep "Agent 4"
```

**Must see:**
```
✅ "🔗 Agent 4: Finding LinkedIn + Tenure (specialist)..."
```

**Check BrightData MCP tools called:**
```bash
docker-compose logs | grep -E "search_engine|scrape_as_markdown"
```

**Must see:**
```
✅ mcp__brightdata__search_engine called
✅ mcp__brightdata__scrape_as_markdown called
```

**Check comprehensive data extracted:**
```bash
docker-compose logs | grep -E "tenure|title|company|education"
```

**Must see:**
```
✅ Tenure: X.X years
✅ Full title extracted
✅ Company name extracted
✅ Education/certifications extracted
```

### Database Validation

```sql
SELECT
    contact_name,
    linkedin_url,
    tenure_years,
    linkedin_full_title,
    linkedin_company,
    previous_golf_roles,
    industry_experience_years,
    education,
    certifications
FROM test_golf_course_contacts
WHERE golf_course_id = (
    SELECT id FROM test_golf_courses
    WHERE course_name ILIKE '%Fairfax%'
);
```

**Expected (3 contacts):**
```
Brandon Sage:
- linkedin_url: NOT NULL
- tenure_years: X.X (if LinkedIn found)
- linkedin_full_title: NOT NULL
- linkedin_company: NOT NULL
- previous_golf_roles: [...] or []
- industry_experience_years: X or NULL
- education: [...] or []
- certifications: [...] or []

Linda Gaudi: (same structure)
Mike Owens: (same structure)
```

---

## Success Criteria

**✅ Docker test PASSES if:**
- [ ] Agent 4 print statement appears in logs
- [ ] Both BrightData tools called (search + scrape)
- [ ] At least 1/3 contacts has comprehensive LinkedIn data
- [ ] No silent Agent 4 failures
- [ ] Cost per course < $0.20
- [ ] All 8 agents ran successfully

**❌ Docker test FAILS if:**
- Agent 4 not mentioned in logs → Orchestrator integration broken
- No BrightData tool calls → MCP configuration issue
- All tenure_years are NULL → Scraping not working
- Silent errors (check orchestrator exception handling)

---

## If Docker PASSES → Proceed to Stage 7

```bash
# Commit enhanced Agent 4
git add .
git commit -m "feat: Agent 4 comprehensive LinkedIn data extraction with hosted HTTP MCP"

# Deploy
git push origin main

# Monitor Render deployment
# Test Course 133 in production
# Validate 3-4/4 contacts with comprehensive data
```

## If Docker FAILS → Debug Before Production

**Common issues:**
1. **BRIGHTDATA_API_TOKEN not in Docker env** → Add to docker-compose.yml
2. **Hosted MCP URL invalid** → Check token format
3. **npm package @brightdata/mcp not found** → Not needed for hosted HTTP!
4. **Agent 4 crashes silently** → Add try/except logging
5. **Orchestrator doesn't call Agent 4** → Check import and function call

---

**Current Status:** Docker building (step 10/14)
**Next:** Start container, test Course 142, validate logs & database
**Time Estimate:** 30-40 minutes for full Stage 6 validation
