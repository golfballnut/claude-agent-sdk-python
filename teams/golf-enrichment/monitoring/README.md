# API Monitoring System

**Purpose:** Monitor API balances and alert when credits run low
**Created:** October 23, 2025
**Status:** 🚧 In Development

---

## Overview

This system monitors API usage for the golf enrichment agents and creates ClickUp alerts when balances fall below configured thresholds.

**Monitored APIs:**
- 💰 Hunter.io (email finding & verification)
- 💰 Firecrawl (web scraping)
- 💰 Perplexity AI (AI search & phone finding)
- 💰 BrightData (LinkedIn scraping)

**Alert Destination:** ClickUp list https://app.clickup.com/9014129779/v/li/901409749476

---

## Quick Start

### Run API Tests

```bash
cd monitoring/tests

# Test all APIs
python test_hunter_api.py
python test_firecrawl_api.py
python test_perplexity_api.py
python test_brightdata_api.py
```

### Manual Balance Check

```bash
cd monitoring/scripts
python manual_api_check.py
```

### Deploy Edge Functions

```bash
cd ../..
npx supabase functions deploy check-api-balances --project-ref oadmysogtfopkbmrulmq --no-verify-jwt
```

---

## Architecture

### Components

**1. Test Scripts** (`tests/`)
- Verify API connectivity
- Document response formats
- Run before deploying automation

**2. Edge Functions** (`edge-functions/`)
- `check-api-balances`: Queries all API balance endpoints
- `update-monitoring-dashboard`: Updates ClickUp monitoring tasks

**3. Supabase pg_cron Scheduler**
- Runs check-api-balances every 6 hours
- Automatic, no manual trigger needed

**4. ClickUp Monitoring Tasks**
- One task per API showing current balance
- Auto-updated by edge functions
- Creates alert task when threshold breached

---

## API Endpoints Discovered

### Hunter.io ✅
```
GET https://api.hunter.io/v2/account?api_key={KEY}
```
**Fields:** `searches.available`, `verifications.available`, `reset_date`

### Firecrawl ✅
```
GET https://api.firecrawl.dev/v2/team/credit-usage
Authorization: Bearer {TOKEN}
```
**Fields:** `remainingCredits`, `planCredits`, `billingPeriodEnd`

### Perplexity ❌
**No balance endpoint**
**Strategy:** Monitor Render logs for 401 errors + manual dashboard checks

### BrightData ❓
**Status:** Research needed
**Action:** Check docs or MCP capabilities

---

## Alert Thresholds

Configured in `config/api_thresholds.json`:

| API | Warning | Critical | Urgent |
|-----|---------|----------|--------|
| Hunter.io Searches | < 100 | < 50 | < 20 |
| Hunter.io Verifications | < 100 | < 50 | < 20 |
| Firecrawl Credits | < 1000 | < 500 | < 100 |
| Perplexity Balance | $5 | $2 | Manual |
| BrightData | TBD | TBD | TBD |

---

## Workflow

```
pg_cron (every 6 hours)
  ↓
check-api-balances edge function
  ├─→ Call Hunter.io /v2/account
  ├─→ Call Firecrawl /v2/team/credit-usage
  ├─→ Skip Perplexity (no endpoint)
  └─→ Call BrightData (if endpoint found)
  ↓
update-monitoring-dashboard edge function
  ├─→ Update 4 ClickUp monitoring tasks
  ├─→ Check thresholds
  └─→ Create alert task if needed
  ↓
ClickUp Personal List
  - Shows current balance for each API
  - Alert task created if critical
```

---

## Development Status

**Current Phase:** Phase 1 - API Testing

**Progress Tracked In:** `PROGRESS.md`

**To build next:**
1. Run all API tests to verify connectivity
2. Create `check-api-balances` edge function
3. Create ClickUp monitoring tasks
4. Setup pg_cron scheduler
5. Test end-to-end automation

---

## Related Systems

**Error Notifications:** ✅ Already built
- Edge function: `notify-course-error`
- Creates task when course enrichment fails
- Example: https://app.clickup.com/t/86b77859y

**Queue Recovery:** ✅ Already built
- Trigger: `trigger_next_ready_course()`
- Continues processing even when courses error

**Region Field Fix:** ✅ Already deployed
- Fixed in `create-clickup-tasks` edge function
- All new outreach tasks will have Region populated

---

## Troubleshooting

**Test script fails:**
- Check `.env` file has all API keys
- Verify API keys are valid
- Check internet connection

**Edge function fails:**
- Check Supabase logs
- Verify API keys set in Supabase secrets
- Check ClickUp list ID is correct

**No alerts created:**
- Verify thresholds are set correctly
- Check pg_cron job is running
- Review edge function logs

---

**For detailed progress and context, see:** `PROGRESS.md`
