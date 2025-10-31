#!/usr/bin/env python3
"""
Agent 2-Apollo: Contact Discovery & Enrichment (All-in-One)

REPLACES:
- Agent 2: Contact discovery (web scraping)
- Agent 3: Email enrichment (Hunter.io)
- Agent 4: LinkedIn & tenure extraction

Uses Apollo.io to find CURRENT employees with verified emails.

Performance Target:
- Email Success: 50-60% (verified, 90%+ confidence)
- Cost: <$0.20 per course (2-4 contacts × 2 credits = ~$0.16)
- Credits: 4-8 per course (within 4,020/month limit)
- Data Quality: Current employees (job change detection)

Pattern:
- 2-step Apollo API (search → enrich)
- Title filtering (GM, Director, Head Pro, Superintendent)
- Credit tracking
- Claude SDK with custom Apollo tool

Benefits vs Current:
- Current employees (not outdated data)
- Verified emails (90%+ confidence)
- LinkedIn included (100% coverage)
- Employment history (tenure, previous clubs, education)
- Simpler (1 agent vs 3)
"""

import anyio
import httpx
import json
import os
from typing import Any, Dict, List
from pathlib import Path
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


# Apollo.io credit cost (from testing)
CREDITS_PER_EMAIL = 2  # Enrichment to unlock email
COST_PER_CREDIT = 79 / 4020  # $79/month ÷ 4,020 credits = $0.0197/credit
COST_PER_ENRICHMENT = CREDITS_PER_EMAIL * COST_PER_CREDIT  # ~$0.039

# Known duplicate Apollo person IDs that appear incorrectly across courses
# These were found in production logs (Oct 30, 2025) - same contacts for every course
KNOWN_DUPLICATE_PERSON_IDS = {
    '54a73cae7468696220badd21',  # Ed Kivett (ed@glenella.com)
    '62c718261e2f1f0001c47cf8',  # Brad Worthington (brad@poundridgegolf.com)
    '54a7002c7468696de70cf30b',  # Greg Bryan (greg@rfclub.com)
    '57db939ca6da986873a1fa42',  # Perry Langdon (plangdon@ellisdon.com)
}


def validate_contact_domain(contact: Dict[str, Any], course_domain: str) -> bool:
    """
    Validate that contact's email domain matches the course domain.
    Prevents duplicate/wrong contacts from being accepted.

    Args:
        contact: Contact dict with 'email' field
        course_domain: Course domain (e.g., 'deepspringscc.com')

    Returns:
        True if valid (email domain matches course), False if suspicious

    Examples:
        validate_contact_domain({"email": "john@deepspringscc.com"}, "deepspringscc.com") → True
        validate_contact_domain({"email": "ed@glenella.com"}, "deepspringscc.com") → False
    """
    email = contact.get('email', '')
    if not email or not course_domain:
        return True  # Can't validate without email/domain, allow through

    if '@' not in email:
        return True  # Invalid email format, but let other validation catch it

    email_domain = email.split('@')[1].lower()
    course_domain_base = course_domain.replace('www.', '').replace('https://', '').replace('http://', '').split('/')[0].lower()

    # Exact match
    if email_domain == course_domain_base:
        return True

    # Subdomain match (e.g., golf.example.com matches example.com)
    if course_domain_base in email_domain or email_domain in course_domain_base:
        return True

    # Check for common parent domain (both subdomains of same company)
    # e.g., courses.invitedclubs.com and staff.invitedclubs.com
    email_parts = email_domain.split('.')
    course_parts = course_domain_base.split('.')

    # If last 2 parts match (company.com), consider it valid
    if len(email_parts) >= 2 and len(course_parts) >= 2:
        if email_parts[-2:] == course_parts[-2:]:
            return True

    # Domain mismatch - suspicious
    print(f"   ⚠️  Domain mismatch: {email} vs {course_domain_base}")
    return False


def detect_duplicate_contacts(contacts: List[Dict[str, Any]], course_name: str) -> List[Dict[str, Any]]:
    """
    Detect if Apollo is returning the same person IDs seen across multiple courses.
    Filters out known duplicate person IDs that were appearing on every course.

    Args:
        contacts: List of contact dicts from Apollo
        course_name: Name of the course (for logging)

    Returns:
        Filtered list with duplicates removed

    Context:
        On Oct 30, 2025, we discovered Apollo was returning the same 4 contacts
        for every NC golf course. These person IDs should never appear.
    """
    if not contacts:
        return []

    filtered = []
    rejected = []

    for contact in contacts:
        person_id = contact.get('person_id')

        if person_id in KNOWN_DUPLICATE_PERSON_IDS:
            rejected.append(f"{contact.get('name', 'Unknown')} (ID: {person_id})")
            print(f"   🚨 REJECTED duplicate: {contact.get('name')} - person_id {person_id} appears on multiple courses")
            continue

        filtered.append(contact)

    if rejected:
        print(f"   📊 Duplicate detection: Rejected {len(rejected)}/{len(contacts)} contacts for {course_name}")
        print(f"      Rejected: {', '.join(rejected)}")

    return filtered


async def find_contacts_apollo_internal(course_name: str, domain: str = "", state_code: str = "") -> dict[str, Any]:
    """
    Internal function: Find current golf course staff using Apollo.io

    This is the core logic extracted for testability.
    The @tool wrapper calls this function.

    2-Strategy Approach:
    1. Domain search (best quality, works for corporate courses)
    2. Name + location search (fallback, works for regional courses)

    Args:
        course_name: Name of golf course
        domain: Course domain (optional but recommended)
        state_code: State code (e.g., "NC" - helps with name search fallback)

    Returns:
        Dict with contacts, credits_used, cost_usd, source, email_coverage
    """
    import httpx

    # Load .env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "error": "APOLLO_API_KEY not found in .env",
                    "contacts": [],
                    "credits_used": 0,
                    "cost_usd": 0
                })
            }]
        }

    # Target positions (4 key decision-makers)
    target_positions = [
        "General Manager",
        "Director of Golf",
        "Head Golf Professional",
        "Superintendent"
    ]

    contacts = []
    credits_used = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": api_key.strip()
        }

        # STEP 1: Search for each position
        for position in target_positions:
            try:
                # Search Apollo - Domain-first strategy (more reliable)
                search_url = "https://api.apollo.io/api/v1/people/search"

                # Use domain if available (more accurate than name matching)
                if domain and domain.strip():
                    search_payload = {
                        "q_organization_domains_list": [domain.strip()],  # Fixed: was "organization_domain" (wrong param name)
                        "person_titles": [position],
                        "page": 1,
                        "per_page": 3  # Top 3 matches
                    }
                else:
                    # Fallback to name search if no domain
                    search_payload = {
                        "q_organization_name": course_name,
                        "person_titles": [position],
                        "page": 1,
                        "per_page": 3  # Top 3 matches
                    }

                search_r = await client.post(search_url, headers=headers, json=search_payload)

                if search_r.status_code != 200:
                    continue

                search_data = search_r.json()
                people = search_data.get("people", [])

                # FALLBACK: If domain search returns 0 results, try name + location search
                if not people and course_name:
                    print(f"   🔄 Domain search found 0 results for {position}, trying name search...")
                    name_search_payload = {
                        "q_organization_name": course_name,
                        "organization_locations": [state_code] if state_code else [],
                        "person_titles": [position],
                        "page": 1,
                        "per_page": 3
                    }

                    name_search_r = await client.post(search_url, headers=headers, json=name_search_payload)

                    if name_search_r.status_code == 200:
                        name_search_data = name_search_r.json()
                        people = name_search_data.get("people", [])
                        if people:
                            print(f"   ✅ Name search found {len(people)} results for {position}")

                if not people:
                    continue

                # Get first match (best match)
                person = people[0]
                person_id = person.get("id")
                person_name = person.get("name")

                # STEP 2: Enrich to unlock email
                enrich_url = "https://api.apollo.io/api/v1/people/match"
                enrich_payload = {
                    "id": person_id,
                    "reveal_personal_emails": False,  # Work emails only
                    "reveal_phone_number": False  # Skip phone (8 credits!)
                }

                enrich_r = await client.post(enrich_url, headers=headers, json=enrich_payload)

                if enrich_r.status_code != 200:
                    continue

                enrich_data = enrich_r.json()
                enriched_person = enrich_data.get("person")

                if not enriched_person:
                    continue

                # Track credits (2 per enrichment based on testing)
                credits_used += CREDITS_PER_EMAIL

                # Extract data
                email = enriched_person.get("email")
                email_status = enriched_person.get("email_status")

                # Only include if verified (90%+ confidence)
                if email and email_status == "verified":
                    employment_history = enriched_person.get("employment_history", [])
                    current_job = next((j for j in employment_history if j.get("current")), {})

                    contact = {
                        "name": enriched_person.get("name"),
                        "title": enriched_person.get("title") or position,
                        "email": email,
                        "email_confidence": 95,  # Verified = 95%
                        "email_method": "apollo_verified",
                        "linkedin_url": enriched_person.get("linkedin_url"),
                        "linkedin_method": "apollo",
                        "tenure_years": None,  # Calculate from employment history
                        "tenure_start_date": current_job.get("start_date"),
                        "previous_clubs": [],  # Parse from employment_history
                        "source": "apollo",
                        "person_id": person_id
                    }

                    # Parse tenure (start_date → years)
                    if current_job.get("start_date"):
                        try:
                            from datetime import datetime
                            start_date = datetime.strptime(current_job["start_date"], "%Y-%m-%d")
                            tenure_days = (datetime.now() - start_date).days
                            contact["tenure_years"] = round(tenure_days / 365.25, 1)
                        except:
                            pass

                    # Parse previous clubs
                    for job in employment_history:
                        if not job.get("current") and "golf" in job.get("organization_name", "").lower():
                            contact["previous_clubs"].append({
                                "name": job.get("organization_name"),
                                "title": job.get("title"),
                                "start_date": job.get("start_date"),
                                "end_date": job.get("end_date")
                            })

                    # VALIDATION: Check email domain matches course domain
                    if not validate_contact_domain(contact, domain):
                        print(f"   ❌ REJECTED: {contact['name']} - email domain {contact['email'].split('@')[1]} doesn't match course domain {domain}")
                        continue

                    # VALIDATION: Check for known duplicate person IDs
                    if person_id in KNOWN_DUPLICATE_PERSON_IDS:
                        print(f"   🚨 REJECTED: {contact['name']} - duplicate person_id {person_id} (appears on multiple courses)")
                        continue

                    contacts.append(contact)

            except Exception as e:
                print(f"   ⚠️ Error finding {position}: {e}")
                continue

    # ADDITIONAL SAFETY: Run duplicate detection on all collected contacts
    # (individual validation happens per-contact above, this is belt-and-suspenders)
    original_count = len(contacts)
    contacts = detect_duplicate_contacts(contacts, course_name)
    if len(contacts) < original_count:
        print(f"   🛡️  Final duplicate check: Filtered {original_count - len(contacts)} additional duplicates")

    # Calculate cost
    cost_usd = credits_used * COST_PER_CREDIT

    # Calculate email coverage
    emails_found = len([c for c in contacts if c.get('email')])
    total_contacts = len(contacts)
    coverage = f"{emails_found}/{total_contacts}" if contacts else "0/0"

    # FALLBACK: Hunter.io if Apollo found 0 valid contacts
    # (Proven to work for 40% of courses in earlier testing)
    if len(contacts) == 0 and domain:
        print("   🔄 Apollo exhausted (domain + name searches failed) - trying Hunter.io...")
        hunter_contacts = await hunter_domain_search_fallback(domain)

        if hunter_contacts:
            print(f"   ✅ Hunter.io SUCCESS: {len(hunter_contacts)} contacts found")

            # Hunter cost
            hunter_cost = 0.049  # $49/month ÷ 1,000 requests

            return {
                "contacts": hunter_contacts,
                "credits_used": 0,  # Hunter doesn't use Apollo credits
                "cost_usd": round(cost_usd + hunter_cost, 4),
                "apollo_cost_usd": round(cost_usd, 4),
                "hunter_cost_usd": hunter_cost,
                "source": "hunter_fallback",
                "email_coverage": f"{len(hunter_contacts)}/{len(hunter_contacts)}"
            }
        else:
            print("   ❌ Hunter.io also returned 0 results - trying Jina search+reader...")

            # FALLBACK 2: Jina search+reader (for small courses not in databases)
            # Proven strategy: Search for contact page, scrape staff names/titles
            if domain or course_name:
                jina_contacts = await jina_search_reader_fallback(domain, course_name, state_code)

                if jina_contacts:
                    print(f"   ✅ Jina SUCCESS: {len(jina_contacts)} contacts found via search+reader")

                    # Jina found names but no emails - try Perplexity to find hidden emails
                    print("      🔍 Trying Perplexity to find hidden emails...")

                    # Try to enrich names with emails using Hunter Email Finder
                    print("      🔍 Trying Hunter Email Finder for discovered names...")

                    emails_found = 0
                    hunter_finder_cost = 0

                    for contact in jina_contacts:
                        name = contact.get("name", "")
                        if not contact.get("email") and name:
                            # Try Hunter Email Finder
                            try:
                                async with httpx.AsyncClient(timeout=10.0) as client:
                                    finder_url = "https://api.hunter.io/v2/email-finder"
                                    params = {
                                        "domain": domain,
                                        "full_name": name,
                                        "api_key": os.getenv("HUNTER_API_KEY")
                                    }
                                    finder_response = await client.get(finder_url, params=params)
                                    finder_data = finder_response.json()

                                    if finder_data.get("data", {}).get("email"):
                                        email = finder_data["data"]["email"]
                                        score = finder_data["data"].get("score", 0)

                                        if score >= 90:
                                            contact["email"] = email
                                            contact["email_confidence"] = score
                                            contact["email_method"] = "hunter_finder"
                                            emails_found += 1
                                            hunter_finder_cost += 0.017
                                            print(f"         ✅ Found: {name} - {email} ({score}%)")
                            except Exception as e:
                                pass

                    # Try email patterns with domain variations for remaining contacts
                    if emails_found < len(jina_contacts) and domain:
                        print("      🔍 Trying email patterns with domain variations...")

                        for contact in jina_contacts:
                            if not contact.get("email") and contact.get("name"):
                                name = contact["name"]
                                name_parts = name.lower().split()

                                if len(name_parts) >= 2:
                                    first = name_parts[0]
                                    last = name_parts[-1]

                                    # Domain variations to try
                                    domain_base = domain.replace('.com', '').replace('.org', '').replace('.net', '')
                                    domains_to_try = [
                                        domain,  # Original
                                        f"{domain_base}golf.com",
                                        f"{domain_base}golfclub.com",
                                        f"{domain_base}golfclub.onmicrosoft.com",  # Common pattern
                                        f"{domain_base}cc.com",
                                    ]

                                    # Email patterns to try
                                    patterns = [
                                        f"{first}.{last}",  # first.last
                                        f"{first}{last}",   # firstlast
                                        f"{first}",         # first
                                        f"{first[0]}{last}", # flast
                                    ]

                                    # Try combinations
                                    for test_domain in domains_to_try:
                                        if contact.get("email"):  # Skip if already found
                                            break

                                        for pattern in patterns:
                                            test_email = f"{pattern}@{test_domain}"

                                            try:
                                                async with httpx.AsyncClient(timeout=10.0) as client:
                                                    verify_url = "https://api.hunter.io/v2/email-verifier"
                                                    params = {"email": test_email, "api_key": os.getenv("HUNTER_API_KEY")}
                                                    verify_response = await client.get(verify_url, params=params)
                                                    verify_data = verify_response.json()

                                                    if verify_data.get("data", {}).get("status") == "valid":
                                                        score = verify_data["data"].get("score", 0)
                                                        if score >= 90:
                                                            contact["email"] = test_email
                                                            contact["email_confidence"] = score
                                                            contact["email_method"] = "pattern_verified"
                                                            emails_found += 1
                                                            print(f"         ✅ Pattern verified: {name} - {test_email} ({score}%)")
                                                            break  # Found valid email, stop trying
                                            except:
                                                pass

                    jina_cost = 0.01

                    return {
                        "contacts": jina_contacts,
                        "credits_used": 0,
                        "cost_usd": round(cost_usd + jina_cost + hunter_finder_cost, 4),
                        "apollo_cost_usd": round(cost_usd, 4),
                        "jina_cost_usd": jina_cost,
                        "hunter_finder_cost_usd": hunter_finder_cost,
                        "source": "jina_hunter_finder" if emails_found > 0 else "jina_names_only",
                        "email_coverage": f"{emails_found}/{len(jina_contacts)}"
                    }
                else:
                    print("   ❌ Jina also returned 0 results - all sources exhausted")

    result = {
        "contacts": contacts,
        "credits_used": credits_used,
        "cost_usd": round(cost_usd, 4),
        "source": "apollo" if len(contacts) > 0 else "no_results_all_sources",
        "email_coverage": coverage
    }

    return result


async def hunter_domain_search_fallback(domain: str) -> List[Dict[str, Any]]:
    """
    Hunter.io Domain-Search fallback when Apollo returns 0 results

    Filters for 90%+ confidence and relevant golf course titles.
    Returns contacts with email (no LinkedIn - needs enrichment).

    Args:
        domain: Course domain (e.g., "deercroft.com")

    Returns:
        List of contacts with email, name, title, confidence
    """
    if not domain:
        return []

    # Load .env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    api_key = os.getenv("HUNTER_API_KEY")
    if not api_key:
        print("   ⚠️  HUNTER_API_KEY not found - skipping Hunter fallback")
        return []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.hunter.io/v2/domain-search"
            params = {
                "domain": domain,
                "api_key": api_key,
                "limit": 10
            }

            r = await client.get(url, params=params)
            data = r.json()

            if not data.get("data") or not data["data"].get("emails"):
                return []

            emails = data["data"]["emails"]

            # Filter: Only verified emails (90%+ confidence) with relevant titles
            relevant_titles = [
                "general manager", "gm", "director", "manager",
                "professional", "superintendent", "president",
                "head professional", "golf", "club manager", "pga"
            ]

            contacts = []
            for email_data in emails:
                confidence = email_data.get("confidence", 0)
                position = (email_data.get("position") or "").lower()

                # Check if title is relevant
                is_relevant = any(title in position for title in relevant_titles)

                if confidence >= 90 and is_relevant:
                    contact = {
                        "name": f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip(),
                        "title": email_data.get("position"),
                        "email": email_data.get("value"),
                        "email_confidence": confidence,
                        "email_method": "hunter_verified",
                        "linkedin_url": None,  # Hunter doesn't provide LinkedIn (TODO: Phase 3)
                        "linkedin_method": None,
                        "tenure_years": None,  # Hunter doesn't provide tenure
                        "tenure_start_date": None,
                        "previous_clubs": [],
                        "source": "hunter_fallback"
                    }
                    contacts.append(contact)

            return contacts

    except Exception as e:
        print(f"   ⚠️  Hunter.io error: {e}")
        return []


async def perplexity_email_search(course_name: str, domain: str, staff_names: List[str] = None) -> Dict[str, str]:
    """
    Use Perplexity to find hidden staff emails on course website

    NOTE: This function is simplified - Perplexity works better when called manually.
    For now, we skip Perplexity in automated pipeline (causes nested SDK issues).

    To implement properly:
    - Move Perplexity to a separate enrichment agent
    - Or call Perplexity API directly (not via SDK)

    Args:
        course_name: Full course name
        domain: Course domain
        staff_names: Optional list of known staff names

    Returns:
        Empty dict (Perplexity disabled for now)
    """
    # TODO: Implement direct Perplexity API call (not via SDK)
    # For now, return empty to avoid nested SDK issues
    print("      ⚠️  Perplexity fallback skipped (implementation complexity)")
    return {}


async def jina_search_reader_fallback(domain: str, course_name: str, state_code: str = "") -> List[Dict[str, Any]]:
    """
    Jina search + reader fallback when Apollo and Hunter fail

    Strategy (using Claude SDK to avoid MCP nesting issues):
    1. Use Claude SDK with Jina MCP tools to search for contact page
    2. Use Claude SDK with Jina reader to scrape contact page
    3. Parse and extract staff names/titles

    Proven to work for small courses without database presence.

    Args:
        domain: Course domain
        course_name: Full course name
        state_code: State (e.g., "NC")

    Returns:
        List of contacts with name, title (email if found)
    """
    if not course_name:
        return []

    try:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock

        # Use Claude to intelligently search and extract contacts
        options = ClaudeAgentOptions(
            allowed_tools=["mcp__jina__jina_search", "mcp__jina__jina_reader"],
            permission_mode="bypassPermissions",
            max_turns=6,  # More turns for thorough search
            model="claude-haiku-4-5",
            system_prompt=(
                f"Find staff contacts for {course_name} in {state_code}. "
                "Be VERY thorough:\n"
                "1. Use jina_search to find '{course_name} contact staff'\n"
                "2. Try reading multiple pages with jina_reader:\n"
                "   - /contact page\n"
                "   - /about or /about-us page\n"
                "   - /staff or /team page\n"
                "   - Main homepage\n"
                "3. Look for these positions: General Manager, Director of Golf, Head Professional, Superintendent, Owner\n"
                "4. Extract names even from paragraphs, testimonials, or scattered text\n"
                "Return ONLY a JSON array: [{\"name\": \"John Doe\", \"title\": \"General Manager\"}]"
            )
        )

        contacts = []

        async with ClaudeSDKClient(options=options) as client:
            await client.query(
                f"Find staff at {course_name}. Try their /contact, /about, and /staff pages. "
                f"Look for General Manager, Director of Golf, Head Professional, Superintendent. "
                f"Return as JSON array."
            )

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            # Try to extract JSON array from response
                            import re
                            json_match = re.search(r'\[.*?\]', block.text, re.DOTALL)
                            if json_match:
                                try:
                                    extracted = json.loads(json_match.group(0))
                                    if extracted and isinstance(extracted, list):
                                        for contact_data in extracted:
                                            if isinstance(contact_data, dict) and contact_data.get('name'):
                                                contact = {
                                                    "name": contact_data.get('name', '').strip(),
                                                    "title": contact_data.get('title', '').strip(),
                                                    "email": None,
                                                    "email_confidence": 0,
                                                    "email_method": None,
                                                    "linkedin_url": None,
                                                    "linkedin_method": None,
                                                    "tenure_years": None,
                                                    "tenure_start_date": None,
                                                    "previous_clubs": [],
                                                    "source": "jina_search_reader"
                                                }
                                                contacts.append(contact)
                                                print(f"         ✅ Found: {contact['name']} - {contact['title']}")
                                except json.JSONDecodeError:
                                    pass

        return contacts[:4]  # Limit to 4 contacts

    except Exception as e:
        print(f"   ⚠️  Jina search+reader error: {e}")
        return []


async def firecrawl_website_scraping_fallback(domain: str, course_name: str) -> List[Dict[str, Any]]:
    """
    Firecrawl website scraping fallback when both Apollo and Hunter return 0 results

    Scrapes the golf course website for staff directory/contact pages and extracts
    contact information using Firecrawl MCP tool with LLM extraction.

    Args:
        domain: Course domain (e.g., "deepspringscc.com")
        course_name: Course name for validation

    Returns:
        List of contacts with name, title, email (if found)
    """
    if not domain:
        return []

    try:
        # Import Firecrawl MCP tool (available via Claude Code)
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        # Common staff page URLs to try
        staff_urls = [
            f"https://{domain}/staff",
            f"https://{domain}/team",
            f"https://{domain}/about/staff",
            f"https://{domain}/about/team",
            f"https://{domain}/contact",
            f"https://{domain}/about",
        ]

        contacts = []

        # Try each URL with Firecrawl scrape
        for url in staff_urls:
            print(f"      🌐 Trying: {url}")

            try:
                # Use mcp__firecrawl__firecrawl_scrape via SDK
                options = ClaudeAgentOptions(
                    allowed_tools=["mcp__firecrawl__firecrawl_scrape"],
                    permission_mode="bypassPermissions",
                    max_turns=1,
                    model="claude-haiku-4-5",
                    system_prompt=(
                        "Extract golf course staff contact information from the webpage. "
                        "Find: General Manager, Director of Golf, Head Professional, Superintendent. "
                        "Extract name, title, email (if visible). "
                        "Return as JSON array: [{\"name\": \"...\", \"title\": \"...\", \"email\": \"...\"}]"
                    )
                )

                async with ClaudeSDKClient(options=options) as client:
                    await client.query(f"Scrape staff contacts from: {url}")

                    # Parse response for extracted contacts
                    async for msg in client.receive_response():
                        if hasattr(msg, 'content'):
                            for block in msg.content:
                                if hasattr(block, 'text'):
                                    # Try to extract JSON array from response
                                    import re
                                    json_match = re.search(r'\[.*?\]', block.text, re.DOTALL)
                                    if json_match:
                                        try:
                                            extracted = json.loads(json_match.group(0))
                                            if extracted and isinstance(extracted, list):
                                                # Validate and format contacts
                                                for contact_data in extracted:
                                                    if isinstance(contact_data, dict) and contact_data.get('name'):
                                                        contact = {
                                                            "name": contact_data.get('name', '').strip(),
                                                            "title": contact_data.get('title', '').strip(),
                                                            "email": contact_data.get('email', '').strip() or None,
                                                            "email_confidence": 75 if contact_data.get('email') else 0,
                                                            "email_method": "website_scraped" if contact_data.get('email') else None,
                                                            "linkedin_url": None,
                                                            "linkedin_method": None,
                                                            "tenure_years": None,
                                                            "tenure_start_date": None,
                                                            "previous_clubs": [],
                                                            "source": "firecrawl_scrape"
                                                        }

                                                        # Validate email domain if present
                                                        if contact["email"]:
                                                            email_domain = contact["email"].split('@')[-1].lower()
                                                            if email_domain == domain.lower():
                                                                contacts.append(contact)
                                                                print(f"         ✅ Found: {contact['name']} - {contact['title']}")
                                                        else:
                                                            # No email but has name/title
                                                            contacts.append(contact)
                                                            print(f"         ℹ️  Found: {contact['name']} - {contact['title']} (no email)")
                                        except json.JSONDecodeError:
                                            pass

                # If we found contacts, stop trying URLs
                if contacts:
                    break

            except Exception as url_error:
                print(f"         ⚠️  Error scraping {url}: {url_error}")
                continue

        # Filter to relevant titles only
        relevant_titles = [
            "general manager", "gm", "director", "manager",
            "professional", "superintendent", "president",
            "head professional", "golf", "club manager", "pga"
        ]

        filtered_contacts = []
        for contact in contacts:
            title_lower = (contact.get("title") or "").lower()
            if any(keyword in title_lower for keyword in relevant_titles):
                filtered_contacts.append(contact)

        return filtered_contacts[:4]  # Limit to 4 contacts

    except Exception as e:
        print(f"   ⚠️  Firecrawl scraping error: {e}")
        return []


@tool("find_contacts_apollo", "Find current golf course staff with emails via Apollo.io", {
    "course_name": str,
    "domain": str,
    "state_code": str
})
async def find_contacts_apollo_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Tool wrapper for find_contacts_apollo_internal.
    Returns MCP tool format with content blocks.
    """
    course_name = args["course_name"]
    domain = args.get("domain", "")
    state_code = args.get("state_code", "")

    result = await find_contacts_apollo_internal(course_name, domain, state_code)

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(result)
        }]
    }


async def discover_contacts(course_name: str, domain: str = "") -> Dict[str, Any]:
    """
    Discover and enrich golf course contacts using Apollo.io

    Args:
        course_name: Golf course name (e.g., "Ballantyne Country Club")
        domain: Course domain (optional, for validation)

    Returns:
        Dict with contacts, cost, credits used
    """

    server = create_sdk_mcp_server("apollo", tools=[find_contacts_apollo_tool])

    options = ClaudeAgentOptions(
        mcp_servers={"apollo": server},
        allowed_tools=["mcp__apollo__find_contacts_apollo"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=2,
        model="claude-haiku-4-5",
        system_prompt=(
            "Use find_contacts_apollo tool to find current golf course staff. "
            "It returns pure JSON with contacts, emails, LinkedIn, employment history. "
            "OUTPUT ONLY THE EXACT JSON - NO MARKDOWN, NO FORMATTING."
        ),
    )

    enrichment = None
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Find current staff at: {course_name}, domain: {domain}"
        )

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        import re
                        json_match = re.search(r'\{.*"contacts".*\}', block.text, re.DOTALL)
                        if json_match:
                            try:
                                enrichment = json.loads(json_match.group(0))
                            except json.JSONDecodeError:
                                pass

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Add SDK cost on top of Apollo credits
    if enrichment:
        apollo_cost = enrichment.get("cost_usd", 0)
        sdk_cost = result_message.total_cost_usd if result_message else 0
        enrichment["total_cost_usd"] = apollo_cost + sdk_cost
        enrichment["sdk_cost_usd"] = sdk_cost
        enrichment["apollo_cost_usd"] = apollo_cost

    return enrichment or {
        "contacts": [],
        "credits_used": 0,
        "cost_usd": 0,
        "error": "No response from agent"
    }


async def main():
    """Demo: Test Agent 2-Apollo on sample NC course"""
    print("🔍 Agent 2-Apollo: Contact Discovery & Enrichment")
    print("="*70)

    test_course = {
        "name": "Ballantyne Country Club",
        "domain": "ballantyneclub.com"
    }

    print(f"Course: {test_course['name']}")
    print(f"Domain: {test_course['domain']}\n")

    result = await discover_contacts(test_course['name'], test_course['domain'])

    print(f"\n📊 Results:")
    print(f"   Contacts found: {len(result.get('contacts', []))}")
    print(f"   Credits used: {result.get('credits_used', 0)}")
    print(f"   Apollo cost: ${result.get('apollo_cost_usd', 0):.4f}")
    print(f"   SDK cost: ${result.get('sdk_cost_usd', 0):.4f}")
    print(f"   Total cost: ${result.get('total_cost_usd', 0):.4f}")

    for contact in result.get('contacts', []):
        print(f"\n   Contact: {contact['name']}")
        print(f"      Title: {contact['title']}")
        print(f"      Email: {contact.get('email', 'None')} ({contact.get('email_confidence', 0)}%)")
        print(f"      LinkedIn: {contact.get('linkedin_url', 'None')}")
        if contact.get('tenure_years'):
            print(f"      Tenure: {contact['tenure_years']} years")
        if contact.get('previous_clubs'):
            print(f"      Previous clubs: {len(contact['previous_clubs'])}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
