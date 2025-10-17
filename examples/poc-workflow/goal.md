# POC Goal: Two-Agent Workflow for Business Data Extraction

## Mission

Build and prove a cost-effective, accurate two-agent workflow pattern that can scale to 500+ agents for automated business data extraction.

## Workflow

```
Agent 1 (URL Finder) → Agent 2 (Data Extractor) → Structured Output
```

### Agent 1: URL Finder
**Input:** Course/business name
**Task:** Find listing URL from directory
**Output:** https://vsga.org/courselisting/[ID]
**Status:** ✅ COMPLETE

### Agent 2: Data Extractor
**Input:** URL from Agent 1
**Task:** Extract contact data (name, address, phone, email, website)
**Output:** Structured JSON with contact info
**Status:** 🔄 IN PROGRESS

### Orchestrator (Future)
**Task:** Manage Agent 1 → Agent 2 flow, handle errors, validate results
**Status:** 📋 PLANNED

## Success Criteria

- ✅ **Cost:** < $0.02 per agent (< $0.04 total per workflow)
- ✅ **Accuracy:** 100% correct data extraction
- ✅ **Speed:** < 10 seconds per workflow
- ✅ **Reliability:** No hallucinations, no failures
- ✅ **Scalability:** Pattern works for 500+ agents

## Current Status

**Agent 1 Results:**
- Cost: $0.0153 avg (24% under budget) ✅
- Accuracy: 100% (5/5 correct URLs) ✅
- Speed: 3.4s avg ✅
- **STATUS: PRODUCTION READY** ✅

**Test Data:**
- 5 course URLs stored in `results/agent1_test_results.json`
- Ready for Agent 2 testing

## Next Steps

1. Build Agent 2 with same winning pattern
2. Test Agent 2 with 5 URLs from Agent 1
3. Build orchestrator to connect Agent 1 + 2
4. Full workflow test
5. Deploy to cloud (Cloud Run / Railway)

## Production Deployment

**Target:** Supabase Edge Function triggers SDK workflow
**Scale:** 500 workflows/day = $15/day = $450/month
**Architecture:** Single deployment, agent registry pattern
