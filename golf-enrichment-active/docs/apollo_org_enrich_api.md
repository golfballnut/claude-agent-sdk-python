# Apollo Organization Enrichment API - Reference Documentation

**Source:** https://docs.apollo.io/reference/organization-enrichment
**Extracted:** Oct 30, 2025
**Status:** NOT accessible on our API plan (403 Forbidden)

---

## Single Organization Enrich

### Endpoint
```
GET https://api.apollo.io/api/v1/organizations/enrich
```

### Authentication
**Header:** `x-api-key: YOUR_API_KEY` (lowercase header name per OpenAPI spec)

### Parameters

#### Query Parameters
- **domain** (string) - **REQUIRED**
  - The domain of the company to enrich
  - Do NOT include: `www.`, `@` symbol, `http://`, `https://`
  - Examples: `apollo.io`, `microsoft.com`, `charlottecountryclub.org`

### Request Example
```bash
curl -X GET "https://api.apollo.io/api/v1/organizations/enrich?domain=apollo.io" \
  -H "x-api-key: YOUR_API_KEY"
```

### Response Schema

#### Success (200 OK)
```json
{
  "organization": {
    "id": "5e66b6381e05b4008c8331b8",
    "name": "Apollo.io",
    "website_url": "http://www.apollo.io",
    "blog_url": null,
    "angellist_url": null,
    "linkedin_url": "http://www.linkedin.com/company/apolloio",
    "twitter_url": "https://twitter.com/meetapollo/",
    "facebook_url": "https://www.facebook.com/MeetApollo",
    "primary_phone": {},
    "languages": [],
    "alexa_ranking": 3514,
    "phone": null,
    "linkedin_uid": "18511550",
    "founded_year": 2015,
    "publicly_traded_symbol": null,
    "publicly_traded_exchange": null,
    "logo_url": "https://zenprospect-production.s3.amazonaws.com/uploads/pictures/...",
    "crunchbase_url": null,
    "primary_domain": "apollo.io",
    "industry": "information technology & services",
    "keywords": [
      "sales engagement",
      "lead generation",
      "predictive analytics",
      ...
    ],
    "estimated_num_employees": 1600,
    "industries": ["information technology & services"],
    "secondary_industries": [],
    "snippets_loaded": true,
    "industry_tag_id": "5567cd4773696439b10b0000",
    "industry_tag_hash": {
      "information technology & services": "5567cd4773696439b10b0000"
    },
    "retail_location_count": 0,
    "raw_address": "415 Mission St, Floor 37, San Francisco, California 94105, US",
    "street_address": "415 Mission St",
    "city": "San Francisco",
    "state": "California",
    "postal_code": "94105-2301",
    "country": "United States",
    "owned_by_organization_id": null,
    "seo_description": "Search, engage, and convert over 275 million contacts..."
  }
}
```

#### Key Fields
- **id** - Organization ID (use this for people search!)
- **name** - Company name
- **primary_domain** - Primary domain
- **estimated_num_employees** - Employee count
- **industry** - Industry classification
- **founded_year** - When company was founded
- **linkedin_url** - Company LinkedIn
- **street_address**, **city**, **state**, **postal_code** - Full address

---

## Bulk Organization Enrich

### Endpoint
```
POST https://api.apollo.io/api/v1/organizations/bulk_enrich
```

### Parameters
- **domains[]** (array[string]) - **REQUIRED**
  - Up to 10 domains per request
  - Same format rules as single enrich

### Request Example
```bash
curl -X POST "https://api.apollo.io/api/v1/organizations/bulk_enrich?domains[]=apollo.io&domains[]=microsoft.com" \
  -H "x-api-key: YOUR_API_KEY"
```

### Response
```json
{
  "status": "success",
  "total_requested_domains": 2,
  "unique_domains": 2,
  "unique_enriched_records": 2,
  "missing_records": 0,
  "organizations": [
    { ... },  // Same schema as single enrich
    { ... }
  ]
}
```

---

## Error Codes

### 401 Unauthorized
```json
{
  "error": "Invalid access credentials."
}
```
**Cause:** Invalid API key

---

### 403 Forbidden
```json
{
  "error": "api/v1/organizations/enrich is not accessible with this api_key",
  "error_code": "API_INACCESSIBLE"
}
```
**Cause:** API plan doesn't include org enrichment access
**Our Status:** ❌ This is what we get (Oct 30, 2025)

---

### 422 Unprocessable Entity
```json
{
  "error": "Required parameter 'domain' missing"
}
```
**Cause:** Missing required domain parameter

```json
{
  "error": "API key must be passed in the X-Api-Key header for security reasons"
}
```
**Cause:** API key in wrong location (query param or body instead of header)

---

### 429 Rate Limit
```json
{
  "message": "The maximum number of api calls allowed for api/v1/organizations/enrich is 600 times per hour. Please upgrade your plan from https://app.apollo.io/#/settings/plans/upgrade."
}
```
**Cause:** Exceeded rate limit
**Limit:** 600 calls/hour for single enrich
**Bulk:** 50% of single rate per minute, 100% hourly/daily

---

## Using Organization ID in People Search

### After Getting Org ID from Enrich

**Endpoint:** `POST https://api.apollo.io/api/v1/people/search`

**Use organization_ids parameter:**
```json
{
  "organization_ids": ["5d91b93a74686945fa632b0b"],
  "person_titles": ["General Manager", "Director of Golf", "Head Professional"],
  "page": 1,
  "per_page": 10
}
```

**Expected:** More accurate results than domain string matching

---

## Our Test Results (Oct 30, 2025)

### Current API Key: DPyR74ac7h9w2y9DMAE90g

**Tested Endpoints:**

| Endpoint | Method | Status | Error |
|----------|--------|--------|-------|
| `/api/v1/organizations/enrich` | GET (X-Api-Key header) | **403** | API_INACCESSIBLE |
| `/api/v1/organizations/enrich` | POST (api_key body) | 422 | Wrong auth method |
| `/api/v1/organizations/enrich` | GET (api_key param) | 422 | Wrong auth method |
| `/api/v1/organizations/bulk_enrich` | POST (query params) | **403** | API_INACCESSIBLE |
| `/api/v1/organizations/bulk_enrich` | POST (JSON body) | **403** | API_INACCESSIBLE |

**Conclusion:** All org enrichment endpoints return 403 - not on our plan

---

### Test Domains

**Tested with:**
- charlottecountryclub.org (KNOWN to exist in Apollo - screenshot proof)
- andersoncreekgolf.com

**Screenshot Evidence:**
- Charlotte CC exists with org ID: `5d91b93a74686945fa632b0b`
- Has 160 employees in Apollo database
- Has emails available for staff (Quinn Moe, Tracy Rivers, etc.)

**But:** We can't access the org enrich endpoint to get that data programmatically

---

## Workarounds

### Option 1: Upgrade Apollo Plan
**Requirement:** Unknown plan tier needed
**Cost:** Unknown additional monthly fee
**Benefit:** Access to org enrich endpoints
**Risk:** May still have data gaps for small clubs

### Option 2: Use Web Scraping (RECOMMENDED)
**Based on:** LLM testing showed 80% success without Apollo org access
**Sources:** PGA.org, club websites, vendor sites, associations
**Cost:** $0.03-0.08 per course (Jina, Perplexity)
**Benefit:** Higher success rate than Apollo alone

### Option 3: Hybrid Approach
**Flow:**
1. Try Apollo people search by domain (free, fast)
2. If fails → Web scraping (comprehensive)
3. Best of both worlds

---

## Related Documentation

**Apollo API Docs:**
- Organization Enrich: https://docs.apollo.io/reference/organization-enrichment
- People Search: https://docs.apollo.io/reference/people-search
- People Enrichment: https://docs.apollo.io/reference/people-enrichment
- Rate Limits: https://docs.apollo.io/reference/rate-limits
- API Pricing: https://docs.apollo.io/docs/api-pricing

**Our Project Docs:**
- API Limitations: `results/docker/apollo_api_limitations_oct30.md`
- LLM Patterns: `results/docker/llm_discovery_patterns.md`
- Comparison: `results/docker/llm_vs_agent_comparison.md`

---

## Future Testing (If New API Key Created)

**Test Plan:**
1. Get new Apollo API key with org enrich access
2. Test org enrich on Charlotte CC
3. Use org ID to search people
4. Compare to domain string search
5. Measure improvement (if any)
6. Decide if upgrade is worth it

**Decision Criteria:**
- If org search finds 3-5x more contacts → Consider upgrade
- If org search still fails on small clubs → Skip upgrade, use web scraping
- If cost is prohibitive → Skip upgrade regardless

---

**Status:** Documentation saved. Ready for new API key testing when available.
