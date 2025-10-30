#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Apollo vs Our Database (10 Enriched NC Courses)

For 10 NC courses already enriched, compare:
- Our database contacts vs Apollo current employees
- Emails (ours vs Apollo)
- LinkedIn (ours vs Apollo)
- Track credit consumption

Tests 4 key positions per course:
1. General Manager
2. Director of Golf
3. Head Golf Professional
4. Superintendent
"""

import anyio
import httpx
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


# Our 10 enriched NC courses with existing contacts
TEST_COURSES = [
    {
        "course_id": 1189,
        "name": "Broadmoor Golf Links",
        "domain": "broadmoorgolflinks.com",
        "our_contacts": [
            {"name": "Trevor Kennedy", "title": "Assistant Professional", "email": None, "linkedin": None},
            {"name": "Bruce Andrews", "title": "Assistant Professional", "email": None, "linkedin": None},
            {"name": "John D Wyatt III", "title": "Head Professional at a Golf Course/Club", "email": None, "linkedin": None}
        ]
    },
    {
        "course_id": 1207,
        "name": "Black Mountain Golf Course",
        "domain": "blackmountaingolf.org",
        "our_contacts": [
            {"name": "Brent Miller", "title": "Golf Course Manager", "email": None, "linkedin": "https://www.linkedin.com/in/brent-miller-94064958"},
            {"name": "David Ballard", "title": "Golf Professional", "email": None, "linkedin": None}
        ]
    },
    {
        "course_id": 1233,
        "name": "Brook Valley Country Club",
        "domain": "brookvalleycc.com",
        "our_contacts": [
            {"name": "Kyle A. Hope", "title": "Assistant Professional", "email": None, "linkedin": None},
            {"name": "Dalton J Rich", "title": "Director of Golf", "email": None, "linkedin": None},
            {"name": "Sean Branagan, PGA", "title": "Head Professional at a Golf Course/Club", "email": None, "linkedin": "https://www.linkedin.com/in/sean-branagan-pga-5a4a20a"}
        ]
    },
    {
        "course_id": 1256,
        "name": "Ballantyne Country Club",
        "domain": "ballantyneclub.com",
        "our_contacts": [
            {"name": "Christopher R. White", "title": "Assistant Professional", "email": None, "linkedin": "https://www.linkedin.com/in/christopher-white-77baa4b"},
            {"name": "Dan Cordaro", "title": "Director of Golf", "email": None, "linkedin": "https://www.linkedin.com/in/dan-cordaro-pga-13b89872"},
            {"name": "Randy D. Joyner", "title": "Director of Instruction", "email": None, "linkedin": "https://www.linkedin.com/in/randy-joyner"},
            {"name": "Matthew H. Saggio", "title": "General Manager", "email": None, "linkedin": "https://www.linkedin.com/in/matthew-saggio-34202374"},
            {"name": "Ross A McCullough", "title": "Professional Development Program Requirements Deficit", "email": None, "linkedin": "https://www.linkedin.com/in/ross-mccullough-pga-realtor"}
        ]
    },
    {
        "course_id": 1275,
        "name": "Baywood Golf Club",
        "domain": "baywoodgc.com",
        "our_contacts": [
            {"name": "Dylan Peyton", "title": "Business Owner", "email": None, "linkedin": "https://www.linkedin.com/in/dylan-peyton-898868151"},
            {"name": "Stephen Strickland", "title": "Golf Course Superintendent", "email": None, "linkedin": "https://www.linkedin.com/in/stephen-strickland-97510240"}
        ]
    },
    {
        "course_id": 1368,
        "name": "Balsam Mountain Preserve",
        "domain": "balsammountainpreserve.com",
        "our_contacts": [
            {"name": "Allison Macke", "title": "Assistant Professional", "email": None, "linkedin": ""},
            {"name": "Chad D. Lauze", "title": "Assistant Professional", "email": None, "linkedin": "https://www.linkedin.com/in/chad-lauze-pga-988a16170"},
            {"name": "Travis P. Wilson", "title": "Director of Golf", "email": None, "linkedin": "https://www.linkedin.com/in/travispwilson"}
        ]
    },
    {
        "course_id": 1521,
        "name": "Bright's Creek Golf Club",
        "domain": "brightscreek.com",
        "our_contacts": [
            {"name": "Quinton D. Metz", "title": "Assistant Professional", "email": None, "linkedin": "https://www.linkedin.com/in/quinton-metz-b010521bb"},
            {"name": "William L. Bower, PGA", "title": "General Manager", "email": None, "linkedin": "https://www.linkedin.com/in/bill-bower-74058b10"},
            {"name": "Beau Burgess", "title": "Head Professional at a Golf Course/Club", "email": None, "linkedin": "https://www.linkedin.com/in/beau-burgess-pga-745579173"}
        ]
    },
    {
        "course_id": 1568,
        "name": "Bermuda Run Country Club West Course",
        "domain": "bermudaruncc.com",
        "our_contacts": [
            {"name": "Brian Meeks", "title": "General Manager", "email": None, "linkedin": None},
            {"name": "Paul Stephens", "title": "Membership Director", "email": None, "linkedin": "https://www.linkedin.com/in/paulthomasstephens"}
        ]
    },
    {
        "course_id": 1578,
        "name": "Birkdale Golf Club",
        "domain": "birkdale.com",
        "our_contacts": [
            {"name": "Jeffrey S. Thomas", "title": "Director of Golf", "email": None, "linkedin": "https://www.linkedin.com/in/jeff-thomas-4762a23b"},
            {"name": "Jeff Thomas", "title": "General Manager; Birkdale Golf Club", "email": None, "linkedin": "https://www.linkedin.com/in/jeff-thomas-838a2460"},
            {"name": "Benjamin Albrecht", "title": "Golf Course Superintendent", "email": None, "linkedin": "https://www.linkedin.com/in/ben-albrecht-640976a9"}
        ]
    },
    {
        "course_id": 1320,
        "name": "Brier Creek Golf Course",
        "domain": "Not found in scraped content",  # Bad domain - will skip
        "our_contacts": [
            {"name": "Robby Peters", "title": "General Manager", "email": None, "linkedin": None},
            {"name": "Cole Stiles", "title": "Director of Golf", "email": None, "linkedin": "https://www.linkedin.com/in/cole-stiles-675a7588"}
        ]
    }
]


async def search_apollo_by_position(course_name: str, position_title: str):
    """Search Apollo for specific position at a course"""

    api_key = os.getenv("APOLLO_API_KEY")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/search"
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": api_key.strip()
            }

            payload = {
                "q_organization_name": course_name,
                "person_titles": [position_title],
                "page": 1,
                "per_page": 3  # Top 3 matches
            }

            r = await client.post(url, headers=headers, json=payload)

            if r.status_code == 200:
                data = r.json()
                people = data.get("people", [])
                return people[:1] if people else []  # Return best match only

            return []

    except Exception:
        return []


async def enrich_person_by_id(person_id: str):
    """Enrich person to get actual email (unlock)"""

    api_key = os.getenv("APOLLO_API_KEY")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.apollo.io/api/v1/people/match"
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": api_key.strip()
            }

            payload = {"id": person_id}

            r = await client.post(url, headers=headers, json=payload)

            if r.status_code == 200:
                data = r.json()
                return data.get("person")

            return None

    except Exception:
        return None


async def main():
    """Run comprehensive comparison test"""

    print("=" * 80)
    print("COMPREHENSIVE TEST: Apollo vs Our Database")
    print("10 Enriched NC Courses - Contact & Email Comparison")
    print("=" * 80)
    print()
    print("Testing 4 key positions per course:")
    print("  1. General Manager")
    print("  2. Director of Golf")
    print("  3. Head Golf Professional")
    print("  4. Superintendent")
    print()
    print("⚠️  BEFORE: Note your current credits at https://app.apollo.io/usage")
    print()

    target_positions = [
        "General Manager",
        "Director of Golf",
        "Head Golf Professional",
        "Superintendent"
    ]

    all_results = []
    total_searches = 0
    total_enrichments = 0

    for i, course in enumerate(TEST_COURSES, 1):
        if "Not found" in course['domain']:
            print(f"\n[{i}/10] {course['name']} - SKIPPED (no domain)")
            continue

        print(f"\n[{i}/10] {course['name']}")
        print("=" * 80)
        print(f"Domain: {course['domain']}")
        print(f"Our contacts: {len(course['our_contacts'])}")
        print()

        course_results = {
            "course": course['name'],
            "positions": {}
        }

        for position in target_positions:
            print(f"\n   Position: {position}")
            print(f"   " + "-" * 70)

            # Search Apollo
            print(f"   Apollo: Searching...")
            apollo_people = await search_apollo_by_position(course['name'], position)
            total_searches += 1

            apollo_result = {"found": False, "name": None, "email": None, "linkedin": None}

            if apollo_people:
                person = apollo_people[0]
                person_id = person.get('id')
                person_name = person.get('name')
                print(f"   Apollo: Found {person_name}")

                # Enrich to get email
                print(f"   Apollo: Enriching to unlock email...")
                enriched = await enrich_person_by_id(person_id)
                total_enrichments += 1

                if enriched:
                    email = enriched.get('email')
                    email_status = enriched.get('email_status')
                    linkedin = enriched.get('linkedin_url')

                    print(f"   Apollo: ✅ {person_name}")
                    if email:
                        print(f"           Email: {email} ({email_status})")
                    else:
                        print(f"           Email: None")
                    if linkedin:
                        print(f"           LinkedIn: {linkedin}")

                    apollo_result = {
                        "found": True,
                        "name": person_name,
                        "email": email,
                        "email_status": email_status,
                        "linkedin": linkedin
                    }
            else:
                print(f"   Apollo: ❌ Not found")

            # Find in our database
            our_contact = None
            for contact in course['our_contacts']:
                if position.lower() in contact['title'].lower() or \
                   (position == "Head Golf Professional" and "Head Professional" in contact['title']):
                    our_contact = contact
                    break

            if our_contact:
                print(f"   Our DB: ✅ {our_contact['name']}")
                print(f"           Email: {our_contact['email'] or 'None'}")
                print(f"           LinkedIn: {our_contact['linkedin'] or 'None'}")
            else:
                print(f"   Our DB: ❌ No {position} in database")

            # Compare
            if apollo_result['found'] and our_contact:
                if apollo_result['name'].lower() == our_contact['name'].lower():
                    match_status = "✅ SAME PERSON"
                else:
                    match_status = f"⚠️  DIFFERENT PEOPLE (Apollo: {apollo_result['name']} vs Ours: {our_contact['name']})"
                print(f"   Match: {match_status}")
            elif apollo_result['found'] and not our_contact:
                print(f"   Match: 🆕 Apollo found NEW contact (we don't have this position)")
            elif not apollo_result['found'] and our_contact:
                print(f"   Match: ⚠️  We have contact, Apollo doesn't (may have left)")

            course_results["positions"][position] = {
                "our_db": our_contact,
                "apollo": apollo_result
            }

            await anyio.sleep(0.5)  # Rate limit courtesy

        all_results.append(course_results)

    # Analysis
    print("\n" + "=" * 80)
    print("COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    print()

    # Count metrics
    total_positions_searched = len(TEST_COURSES) * len(target_positions)
    our_db_has = 0
    apollo_found = 0
    both_have = 0
    emails_ours = 0
    emails_apollo = 0
    linkedin_ours = 0
    linkedin_apollo = 0
    same_person = 0
    different_person = 0

    for result in all_results:
        for position, data in result['positions'].items():
            if data['our_db']:
                our_db_has += 1
                if data['our_db']['email']:
                    emails_ours += 1
                if data['our_db']['linkedin']:
                    linkedin_ours += 1

            if data['apollo']['found']:
                apollo_found += 1
                if data['apollo']['email']:
                    emails_apollo += 1
                if data['apollo']['linkedin']:
                    linkedin_apollo += 1

            if data['our_db'] and data['apollo']['found']:
                both_have += 1
                # Check if same person (fuzzy match)
                our_name = data['our_db']['name'].lower().replace(',', '').replace('.', '')
                apollo_name = data['apollo']['name'].lower().replace(',', '').replace('.', '')
                if our_name in apollo_name or apollo_name in our_name:
                    same_person += 1
                else:
                    different_person += 1

    print(f"📊 Contact Coverage:")
    print(f"   Positions searched: {total_positions_searched} ({len(TEST_COURSES)} courses × 4 positions)")
    print(f"   Our database has: {our_db_has} contacts")
    print(f"   Apollo found: {apollo_found} contacts")
    print(f"   Both have: {both_have} contacts")
    print()

    print(f"📧 Email Coverage:")
    print(f"   Our database: {emails_ours}/{our_db_has} ({emails_ours/our_db_has*100 if our_db_has else 0:.1f}%)")
    print(f"   Apollo: {emails_apollo}/{apollo_found} ({emails_apollo/apollo_found*100 if apollo_found else 0:.1f}%)")
    print(f"   Improvement: +{emails_apollo - emails_ours} emails")
    print()

    print(f"🔗 LinkedIn Coverage:")
    print(f"   Our database: {linkedin_ours}/{our_db_has} ({linkedin_ours/our_db_has*100 if our_db_has else 0:.1f}%)")
    print(f"   Apollo: {linkedin_apollo}/{apollo_found} ({linkedin_apollo/apollo_found*100 if apollo_found else 0:.1f}%)")
    print()

    print(f"🎯 Data Accuracy:")
    print(f"   Same person (verified): {same_person}/{both_have}")
    print(f"   Different person (job change?): {different_person}/{both_have}")
    print(f"   Data accuracy: {same_person/both_have*100 if both_have else 0:.1f}%")
    print()

    # Credit consumption
    print("=" * 80)
    print("CREDIT CONSUMPTION")
    print("=" * 80)
    print()
    print(f"API Calls Made:")
    print(f"   Searches: {total_searches}")
    print(f"   Enrichments: {total_enrichments}")
    print(f"   Total operations: {total_searches + total_enrichments}")
    print()
    print(f"⚠️  NOW: Check https://app.apollo.io/usage")
    print(f"      Note credits consumed and tell Claude!")
    print()

    # Save results
    output = {
        "test_date": datetime.now().isoformat(),
        "courses_tested": len([c for c in TEST_COURSES if "Not found" not in c['domain']]),
        "total_searches": total_searches,
        "total_enrichments": total_enrichments,
        "our_db_contacts": our_db_has,
        "apollo_contacts": apollo_found,
        "emails_ours": emails_ours,
        "emails_apollo": emails_apollo,
        "linkedin_ours": linkedin_ours,
        "linkedin_apollo": linkedin_apollo,
        "data_accuracy_pct": same_person/both_have*100 if both_have else 0,
        "details": all_results
    }

    results_file = Path(__file__).parent / "results" / "apollo_vs_database_10_courses.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📁 Results saved: {results_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(main)
