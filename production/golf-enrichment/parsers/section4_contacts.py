"""
Section 4 Parser: Decision Makers (Contacts)

Purpose: Parse contact information for decision makers

V2 Section 4 Structure:
{
  "contacts": [
    {
      "name": "John Doe",
      "title": "General Manager",
      "work_email": "jdoe@course.com",
      "linkedin_url": "https://linkedin.com/in/...",
      "phone": "(555) 123-4567",
      "employment_verified": true,
      "sources": ["https://...", "https://..."]
    },
    ...
  ]
}

Output:
[
  {
    "name": str,
    "title": str,
    "email": Optional[str],
    "linkedin_url": Optional[str],
    "phone": Optional[str],
    "employment_verified": bool,
    "sources": List[str]
  },
  ...
]

Created: 2025-10-31
"""

from typing import Dict, Any, List


def parse(section4: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse Section 4: Contacts

    Args:
        section4: Section 4 JSON object

    Returns:
        List of contact dictionaries

    Note:
        - Empty list is valid (NO_CONTACTS_FOUND flag will be raised)
        - Each contact must have name + title at minimum
    """
    if not section4:
        return []

    contacts_raw = section4.get("contacts", [])
    if not isinstance(contacts_raw, list):
        return []

    parsed_contacts = []

    for contact in contacts_raw:
        if not isinstance(contact, dict):
            continue

        # Required fields
        name = contact.get("name", "").strip()
        title = contact.get("title", "").strip()

        if not name or not title:
            # Skip contacts without name or title
            continue

        # Optional contact methods
        email = contact.get("work_email", contact.get("email", "")).strip() or None
        linkedin_url = contact.get("linkedin_url", "").strip() or None
        phone = contact.get("phone", "").strip() or None

        # Employment verification
        employment_verified = contact.get("employment_verified", False)
        if isinstance(employment_verified, str):
            employment_verified = employment_verified.lower() in ["true", "yes", "verified"]

        # Sources
        sources = contact.get("sources", [])
        if not isinstance(sources, list):
            sources = [sources] if sources else []

        # Clean sources (ensure strings)
        sources = [str(s) for s in sources if s]

        parsed_contacts.append({
            "name": name,
            "title": title,
            "email": email,
            "linkedin_url": linkedin_url,
            "phone": phone,
            "employment_verified": bool(employment_verified),
            "sources": sources
        })

    return parsed_contacts
