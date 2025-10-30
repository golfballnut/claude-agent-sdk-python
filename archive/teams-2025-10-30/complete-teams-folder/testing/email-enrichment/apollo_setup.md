# Apollo.io Search API Setup Guide

**Last Updated:** October 29, 2025
**Purpose:** Setup Apollo.io People Search API for email enrichment waterfall

---

## Overview

Apollo.io provides a **Search API** for finding contact emails from their 275M+ contact database. We use this as Tier 2 in our email enrichment waterfall (Hunter.io → Apollo.io → null).

**API Documentation:** https://docs.apollo.io/reference/people-search

---

## Step 1: Sign Up for Apollo.io

1. Go to https://app.apollo.io/signup
2. Create account with business email
3. Choose plan:
   - **Recommended:** Professional ($79/month)
   - 6,000 credits/month
   - API access included
   - 14-day free trial available

---

## Step 2: Choose the Right API

**IMPORTANT:** Apollo.io has TWO different APIs

### ✅ Search API (What we need)
- **Purpose:** Find NEW emails in Apollo's 275M contact database
- **Use case:** Search by name + company/domain → get email
- **Endpoint:** `/api/v1/people/search`
- **Perfect for:** Our email enrichment waterfall

### ❌ Enrichment API (What we DON'T need)
- **Purpose:** Update EXISTING contact records
- **Use case:** Keep your CRM records up to date
- **Not for:** Finding new emails

**When prompted, click "Get started" on Search API (right card)**

---

## Step 3: Create API Key

1. Navigate to: https://app.apollo.io/#/settings/integrations/api
2. Click "Create New API Key"
3. Name: `Golf Enrichment - Agent 3.5`
4. **Enable these permissions:**
   - ☑️ `api/v1/people/search` ← PRIMARY (required)
   - ☑️ `api/v1/people/match` ← BACKUP (optional)
   - ☑️ `api/v1/organizations/enrich` ← BONUS (optional company data)
5. Click "Create"
6. Copy the API key (starts with something like `kJf9x...`)

**⚠️ Save the key immediately - you won't see it again!**

---

## Step 4: Configure Locally

Add to `.env` file in project root:

```bash
# Apollo.io API Key (Search API)
# Plan: Professional ($79/mo, 6,000 credits)
# Created: 2025-10-29
APOLLO_API_KEY=your_api_key_here
```

**Security:**
- Never commit `.env` to git
- `.env` is already in `.gitignore`
- Rotate key if accidentally exposed

---

## Step 5: Test API Connection

Create a test script to verify the API works:

```python
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_apollo_search():
    """Test Apollo.io People Search API"""

    api_key = os.getenv("APOLLO_API_KEY")

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "https://api.apollo.io/v1/people/search"
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
        payload = {
            "api_key": api_key,
            "q_organization_name": "Richmond Country Club",
            "person_titles": ["General Manager"],
            "organization_domains": ["richmondcountryclubva.com"]
        }

        r = await client.post(url, headers=headers, json=payload)
        data = r.json()

        if data.get("people"):
            person = data["people"][0]
            print(f"✅ Found: {person.get('name')}")
            print(f"   Email: {person.get('email')}")
            print(f"   Status: {person.get('email_status')}")
            print(f"   Phone: {person.get('phone_numbers', [{}])[0].get('raw_number')}")
        else:
            print("❌ No results found")

# Run test
import anyio
anyio.run(test_apollo_search)
```

**Expected output:**
```
✅ Found: Stacy Foster
   Email: sfoster@richmondcountryclubva.com
   Status: verified
   Phone: +1-xxx-xxx-xxxx
```

---

## API Endpoint: People Search

**Official Documentation:** https://docs.apollo.io/reference/people-search

### Endpoint
```
POST https://api.apollo.io/v1/people/search
```

### Request Format

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Cache-Control": "no-cache"
}
```

**Payload:**
```json
{
  "api_key": "YOUR_API_KEY",
  "q_organization_name": "Company Name",
  "person_titles": ["General Manager", "Director of Golf"],
  "organization_domains": ["example.com"],
  "page": 1,
  "per_page": 10
}
```

**Alternative (more specific):**
```json
{
  "api_key": "YOUR_API_KEY",
  "first_name": "John",
  "last_name": "Smith",
  "organization_domains": ["example.com"]
}
```

### Response Format

```json
{
  "people": [
    {
      "id": "abc123",
      "first_name": "John",
      "last_name": "Smith",
      "name": "John Smith",
      "title": "General Manager",
      "email": "jsmith@example.com",
      "email_status": "verified",
      "organization_name": "Example Golf Club",
      "linkedin_url": "https://linkedin.com/in/johnsmith",
      "phone_numbers": [
        {
          "raw_number": "+1-555-123-4567",
          "sanitized_number": "+15551234567",
          "type": "work_hq"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_entries": 1,
    "total_pages": 1
  }
}
```

### Key Response Fields

| Field | Description | Example |
|-------|-------------|---------|
| `email` | Contact's email address | "jsmith@example.com" |
| `email_status` | Verification status | "verified", "likely", "guessed" |
| `name` | Full name | "John Smith" |
| `title` | Job title | "General Manager" |
| `linkedin_url` | LinkedIn profile | "https://..." |
| `phone_numbers` | Array of phone numbers | [{"raw_number": "..."}] |

### Email Status Values

| Status | Confidence | Accept? |
|--------|-----------|---------|
| `verified` | 95%+ | ✅ Yes (90%+ threshold) |
| `likely` | 80-90% | ❌ No (below 90%) |
| `guessed` | 60-80% | ❌ No (below 90%) |

**Our filtering rule:** Only accept `email_status: "verified"` to meet 90%+ confidence requirement

---

## Integration with Agent 3.5

### Waterfall Logic

```python
async def enrich_contact_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Email enrichment waterfall:
    1. Hunter.io (90%+ confidence)
    2. Apollo.io (verified only)
    3. Return null
    """

    results = {
        "email": None,
        "email_method": None,
        "email_confidence": 0,
        "linkedin_url": None,
        "phone": None,
        "steps_attempted": []
    }

    # STEP 1: Hunter.io
    hunter_result = await try_hunter_io(args)
    if hunter_result and hunter_result["confidence"] >= 90:
        results.update(hunter_result)
        results["email_method"] = "hunter_io"
        return results

    # STEP 2: Apollo.io (if Hunter.io failed)
    apollo_result = await try_apollo_io(args)
    if apollo_result and apollo_result["email_status"] == "verified":
        results["email"] = apollo_result["email"]
        results["email_method"] = "apollo_io"
        results["email_confidence"] = 95  # verified = 95%
        results["linkedin_url"] = apollo_result.get("linkedin_url")
        results["phone"] = apollo_result.get("phone_numbers", [{}])[0].get("raw_number")
        return results

    # STEP 3: Not found
    results["email_method"] = "not_found"
    return results
```

### Apollo.io Search Function

```python
async def try_apollo_io(contact: dict) -> dict:
    """
    Search Apollo.io for contact email

    Args:
        contact: {name, title, company, domain}

    Returns:
        {email, email_status, linkedin_url, phone_numbers} or None
    """
    apollo_api_key = os.getenv("APOLLO_API_KEY")

    if not apollo_api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/v1/people/search"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache"
            }

            # Search by name + domain
            payload = {
                "api_key": apollo_api_key,
                "first_name": contact["name"].split()[0],
                "last_name": contact["name"].split()[-1],
                "organization_domains": [contact["domain"]],
                "page": 1,
                "per_page": 1
            }

            r = await client.post(url, headers=headers, json=payload)
            data = r.json()

            if data.get("people") and len(data["people"]) > 0:
                person = data["people"][0]

                # Only return if verified (90%+ confidence)
                if person.get("email_status") == "verified":
                    return person

            return None

    except Exception as e:
        print(f"   ⚠️ Apollo.io error: {e}")
        return None
```

---

## Cost Analysis

**Plan:** Professional ($79/month, 6,000 credits)

**Cost per contact:**
- 1 search = 1 credit
- Cost per search: $79 / 6,000 = $0.013

**Budget impact:**
- Current (Hunter.io only): $0.0116/contact
- With Apollo.io waterfall:
  - Hunter finds 50%: 50% × $0.0116 = $0.0058
  - Apollo finds 15%: 15% × $0.013 = $0.00195
  - Not found 35%: 35% × $0.0116 = $0.00406
  - **Total: ~$0.012/contact** ✅ Under $0.02 budget

**Monthly usage (500 courses, 4 contacts each):**
- Total contacts: 2,000
- Hunter finds: 1,000 (50%)
- Apollo searches needed: 1,000 (50%)
- Apollo credits used: 1,000
- Credits remaining: 5,000 ✅ Plenty of buffer

---

## Rate Limits

**Professional Plan:**
- 5,000 requests/day
- No hourly limits
- Concurrent requests: Up to 5

**For our use case:**
- Average: ~70 contacts/day (500 courses/week)
- Apollo searches: ~35/day (50% Hunter.io hits first)
- **Well below 5,000/day limit** ✅

---

## Error Handling

**Common errors:**

1. **401 Unauthorized**
   - API key invalid or expired
   - Check `.env` file
   - Regenerate key if needed

2. **403 Forbidden**
   - API permission not enabled
   - Enable `api/v1/people/search` permission

3. **429 Too Many Requests**
   - Rate limit exceeded
   - Implement exponential backoff
   - Wait 60 seconds and retry

4. **500 Server Error**
   - Apollo.io service issue
   - Retry with exponential backoff
   - Fall through to next tier (return null)

**Retry logic:**
```python
import asyncio

async def try_apollo_io_with_retry(contact: dict, max_retries=3):
    """Apollo.io with exponential backoff"""

    for attempt in range(max_retries):
        try:
            result = await try_apollo_io(contact)
            return result

        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait)
            else:
                return None  # All retries failed
```

---

## Testing Checklist

Before using in production:

- [ ] API key created and saved to `.env`
- [ ] Permissions enabled: `api/v1/people/search`
- [ ] Test script runs successfully
- [ ] Verified response format matches expectations
- [ ] Error handling tested (invalid key, rate limit)
- [ ] Cost tracking implemented
- [ ] Integration with Agent 3.5 tested
- [ ] E2E test on 20 courses completed

---

## Next Steps

1. ✅ Complete Apollo.io signup and API key setup
2. ⬜ Run Test 2: Apollo.io NC baseline validation
3. ⬜ Build Agent 3.5 waterfall (Hunter → Apollo)
4. ⬜ Integration testing (20 courses)
5. ⬜ Production deployment

---

## References

- **Official API Docs:** https://docs.apollo.io/reference/people-search
- **API Settings:** https://app.apollo.io/#/settings/integrations/api
- **Pricing:** https://www.apollo.io/pricing
- **Support:** support@apollo.io

---

**Questions?** Review official docs or test with sample contacts first.
