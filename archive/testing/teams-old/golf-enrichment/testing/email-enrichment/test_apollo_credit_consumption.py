#!/usr/bin/env python3
"""
Test A: Apollo.io Credit Consumption Analysis

Critical test to understand exactly how credits are consumed:
- How many credits per /people/search?
- How many credits per /people/match enrichment?
- Total credits needed for our workflow?

This determines if Apollo is affordable for our use case.
"""

import anyio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


async def get_credit_usage():
    """Get current credit usage from Apollo API"""

    api_key = os.getenv("APOLLO_API_KEY")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/v1/auth/health"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": api_key.strip()
            }

            r = await client.get(url, headers=headers)

            if r.status_code == 200:
                # Health check doesn't return credits
                # Need to check dashboard or usage endpoint
                return "Check dashboard at https://app.apollo.io/usage"

            return None

    except Exception as e:
        return None


async def test_search_cost():
    """Test credit cost of /people/search"""

    api_key = os.getenv("APOLLO_API_KEY")

    print("Testing: /people/search credit cost")
    print("-" * 80)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/search"
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": api_key.strip()
            }

            # Search for people at one organization with title filter
            payload = {
                "q_organization_name": "Alamance Country Club",
                "person_titles": ["General Manager", "Director of Golf"],
                "page": 1,
                "per_page": 10
            }

            print(f"Searching: Alamance Country Club")
            print(f"Filter: General Manager, Director of Golf")
            print(f"Limit: 10 results")
            print()

            r = await client.post(url, headers=headers, json=payload)

            if r.status_code == 200:
                data = r.json()
                people = data.get("people", [])

                print(f"✅ Results: {len(people)} people found")

                for person in people:
                    print(f"   - {person.get('name')}: {person.get('title')}")

                print()
                print(f"Credits consumed: CHECK DASHBOARD")
                print(f"URL: https://app.apollo.io/usage")

                return len(people)
            else:
                print(f"❌ Error: {r.status_code}")
                print(f"Response: {r.text[:200]}")
                return 0

    except Exception as e:
        print(f"❌ Exception: {e}")
        return 0


async def test_enrich_cost():
    """Test credit cost of /people/match enrichment"""

    api_key = os.getenv("APOLLO_API_KEY")

    print()
    print("Testing: /people/match enrichment credit cost")
    print("-" * 80)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/match"
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": api_key.strip()
            }

            # Enrich a known person
            payload = {
                "first_name": "Drake",
                "last_name": "Woodside",
                "domain": "alamancecc.net",  # Correct domain!
                "organization_name": "Alamance Country Club"
            }

            print(f"Enriching: Drake Woodside")
            print(f"Domain: alamancecc.net")
            print()

            r = await client.post(url, headers=headers, json=payload)

            if r.status_code == 200:
                data = r.json()
                person = data.get("person")

                if person:
                    print(f"✅ Enriched: {person.get('name')}")
                    print(f"   Email: {person.get('email')}")
                    print(f"   Status: {person.get('email_status')}")
                    print()
                    print(f"Credits consumed: CHECK DASHBOARD")
                    print(f"URL: https://app.apollo.io/usage")

                    return 1
            else:
                print(f"❌ Error: {r.status_code}")
                print(f"Response: {r.text[:200]}")
                return 0

    except Exception as e:
        print(f"❌ Exception: {e}")
        return 0


async def main():
    """Test credit consumption"""

    print("=" * 80)
    print("Apollo.io Credit Consumption Test")
    print("=" * 80)
    print()
    print("BEFORE: Check your current credits at https://app.apollo.io/usage")
    print("Note the 'Credits used' count")
    print()
    input("Press Enter when ready to start tests...")
    print()

    # Test 1: Search
    search_results = await test_search_cost()

    print()
    print("=" * 80)
    print("CHECKPOINT 1: Check credits after search")
    print("=" * 80)
    print(f"Go to: https://app.apollo.io/usage")
    print(f"Note credits consumed")
    print()
    input("Press Enter to continue...")
    print()

    # Test 2: Enrichment
    enrich_result = await test_enrich_cost()

    print()
    print("=" * 80)
    print("CHECKPOINT 2: Check credits after enrichment")
    print("=" * 80)
    print(f"Go to: https://app.apollo.io/usage")
    print(f"Note TOTAL credits consumed")
    print()
    input("Press Enter to see analysis...")
    print()

    # Analysis
    print("=" * 80)
    print("CREDIT ANALYSIS")
    print("=" * 80)
    print()
    print("Manual calculation needed:")
    print()
    print("1. Credits before tests: ____ (you noted)")
    print("2. Credits after search: ____ (you noted)")
    print("3. Credits after enrich: ____ (you noted)")
    print()
    print("Calculation:")
    print("- Search cost = (credits after search) - (credits before)")
    print("- Enrich cost = (credits after enrich) - (credits after search)")
    print()
    print("=" * 80)
    print("PROJECTED COSTS")
    print("=" * 80)
    print()
    print("Scenario 1: Apollo for email enrichment only (Agent 3 waterfall)")
    print(f"- Per course: 4 contacts × (search + enrich) credits")
    print(f"- If search=1, enrich=1: 4 × 2 = 8 credits/course")
    print(f"- Monthly: 500 courses × 8 = 4,000 credits (exactly your limit!)")
    print()
    print("Scenario 2: Apollo for contact discovery (replace Agent 2)")
    print(f"- Per course: 1 search (filtered to GM/Director only)")
    print(f"- If search returns 2-4 people: Need 2-4 enrichments")
    print(f"- Total: 1 + 4 = 5 credits per course")
    print(f"- Monthly: 500 courses × 5 = 2,500 credits (under limit!)")
    print()
    print("Scenario 3: Full Apollo workflow (discovery + enrichment)")
    print(f"- Contact discovery: 1 search per course")
    print(f"- Email enrichment: 4 enrichments per course")
    print(f"- Total: ~5 credits per course")
    print(f"- Monthly: 500 courses × 5 = 2,500 credits")
    print()
    print("=" * 80)
    print("RECOMMENDATION PENDING")
    print("=" * 80)
    print()
    print("After you note the actual credit consumption:")
    print("1. Document exact costs")
    print("2. Calculate if 4,000 credits/month is sufficient")
    print("3. Decide on Apollo usage strategy")
    print()


if __name__ == "__main__":
    anyio.run(main)
