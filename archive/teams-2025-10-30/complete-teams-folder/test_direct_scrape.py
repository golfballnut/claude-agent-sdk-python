#!/usr/bin/env python3
"""
Test direct web scraping without LLM - more deterministic

Strategy: Directly fetch and parse /contact, /about pages
"""

import anyio
import httpx
import re


async def direct_web_scrape_contacts(domain: str, course_name: str):
    """Direct HTTP scraping without LLM"""

    # Try multiple page URLs
    urls_to_try = [
        f"https://{domain}/contact",
        f"https://{domain}/contact-us",
        f"https://{domain}/about",
        f"https://{domain}/about-us",
        f"https://{domain}/staff",
        f"https://{domain}/team",
        f"https://{domain}",  # Homepage
    ]

    contacts = []

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for url in urls_to_try:
            try:
                print(f"  Trying: {url}")

                # Use Jina reader for clean text extraction
                response = await client.get(f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"})
                text = response.text

                if not text or len(text) < 100:
                    continue

                # Look for staff patterns in text
                lines = text.split('\n')

                positions = [
                    "general manager", "gm", "director of golf",
                    "head professional", "head pro", "golf professional",
                    "superintendent", "golf course superintendent",
                    "club manager", "owner", "president", "ceo"
                ]

                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()

                    # Check if line contains a position
                    for position in positions:
                        if position in line_lower:
                            # Look for a name nearby (within 3 lines)
                            for offset in range(-2, 3):
                                check_idx = i + offset
                                if 0 <= check_idx < len(lines):
                                    potential_name = lines[check_idx].strip()

                                    # Name pattern: 2-4 words, starts with capital, no numbers
                                    words = potential_name.split()
                                    if (2 <= len(words) <= 4 and
                                        potential_name[0].isupper() and
                                        not any(char.isdigit() for char in potential_name) and
                                        len(potential_name) < 60):

                                        # Exclude non-names (expanded list)
                                        if not any(x in potential_name.lower() for x in
                                                 ['phone', 'email', '@', 'http', 'www', '.com', 'address', 'fax',
                                                  'markdown', 'content', 'published', 'time', 'date', 'copyright',
                                                  'reserved', 'privacy', 'policy', 'terms', 'conditions']):

                                            contact = {
                                                "name": potential_name,
                                                "title": line.strip()
                                            }

                                            # Avoid duplicates
                                            if not any(c["name"] == contact["name"] for c in contacts):
                                                contacts.append(contact)
                                                print(f"    ✅ Found: {potential_name} - {line.strip()}")
                                                break

                # If we found contacts, stop trying URLs
                if contacts:
                    break

            except Exception as e:
                print(f"    Error: {e}")
                continue

    return contacts[:4]


async def test_direct_scrape():
    """Test direct scraping on failed courses"""

    test_courses = [
        {"name": "Deep Springs Country Club", "domain": "deepspringscc.com"},
        {"name": "Deercroft Golf & Country Club", "domain": "deercroft.com"},
        {"name": "Densons Creek Golf Course", "domain": "densoncreekgolf.com"},
    ]

    print("🔍 Testing Direct Web Scraping (No LLM)")
    print("=" * 70)

    results = []
    for course in test_courses:
        print(f"\n📍 {course['name']}")
        print("-" * 70)

        contacts = await direct_web_scrape_contacts(course['domain'], course['name'])

        result = {
            "course": course['name'],
            "success": len(contacts) > 0,
            "contacts": contacts
        }
        results.append(result)

        if contacts:
            print(f"\n✅ SUCCESS: {len(contacts)} contacts")
        else:
            print(f"\n❌ FAILED")

    # Summary
    print("\n" + "=" * 70)
    successful = len([r for r in results if r['success']])
    print(f"Success: {successful}/3 ({successful/3*100:.0f}%)")
    print(f"\nTotal projected: {2 + successful}/5 ({(2+successful)/5*100:.0f}%)")

    if (2 + successful) / 5 >= 0.9:
        print("🎉 READY: ≥90%!")
    else:
        print(f"⚠️ Need {int(5*0.9)-2-successful} more")


if __name__ == "__main__":
    anyio.run(test_direct_scrape)
