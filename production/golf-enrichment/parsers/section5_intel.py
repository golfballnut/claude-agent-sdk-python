"""
Section 5 Parser: Basic Intelligence

Purpose: Parse course intelligence (ownership, changes, vendors, selling points)

V2 Section 5 Structure:
{
  "ownership": {
    "type": "Private club" | "Municipal" | "Resort" | "Independent",
    "entity_name": "Heritage Golf Group",
    "source": "https://..."
  },
  "recent_changes": [
    {
      "change_type": "ownership" | "renovation" | "management",
      "description": "New owner in 2023",
      "date": "2023-03-15",
      "source": "https://..."
    }
  ],
  "current_vendors": [
    {
      "vendor_type": "range_balls" | "golf_balls" | "cart_fleet",
      "vendor_name": "Titleist",
      "source": "https://..."
    }
  ],
  "selling_points": [
    "Hosted US Open qualifier",
    "Ranked #1 in state"
  ]
}

Output:
{
  "ownership": {type, entity_name, source},
  "recent_changes": [...],
  "current_vendors": [...],
  "selling_points": [...]
}

Created: 2025-10-31
"""

from typing import Dict, Any


def parse(section5: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Section 5: Basic Intelligence

    Args:
        section5: Section 5 JSON object

    Returns:
        {
            "ownership": {type, entity_name, source},
            "recent_changes": [...],
            "current_vendors": [...],
            "selling_points": [...]
        }

    Note:
        - All fields are optional
        - Stored as JSONB in v2_intelligence column
        - Used for outreach personalization
    """
    if not section5:
        return {
            "ownership": {},
            "recent_changes": [],
            "current_vendors": [],
            "selling_points": []
        }

    # Parse ownership
    ownership = section5.get("ownership", {})
    if isinstance(ownership, dict):
        ownership = {
            "type": ownership.get("type", ""),
            "entity_name": ownership.get("entity_name", ""),
            "source": ownership.get("source", "")
        }
    else:
        ownership = {}

    # Parse recent changes
    recent_changes = section5.get("recent_changes", [])
    if not isinstance(recent_changes, list):
        recent_changes = []

    parsed_changes = []
    for change in recent_changes:
        if isinstance(change, dict):
            parsed_changes.append({
                "change_type": change.get("change_type", ""),
                "description": change.get("description", ""),
                "date": change.get("date", ""),
                "source": change.get("source", "")
            })

    # Parse current vendors
    current_vendors = section5.get("current_vendors", [])
    if not isinstance(current_vendors, list):
        current_vendors = []

    parsed_vendors = []
    for vendor in current_vendors:
        if isinstance(vendor, dict):
            parsed_vendors.append({
                "vendor_type": vendor.get("vendor_type", ""),
                "vendor_name": vendor.get("vendor_name", ""),
                "source": vendor.get("source", "")
            })

    # Parse selling points
    selling_points = section5.get("selling_points", [])
    if not isinstance(selling_points, list):
        selling_points = []

    # Ensure selling points are strings
    parsed_selling_points = [str(sp) for sp in selling_points if sp]

    return {
        "ownership": ownership,
        "recent_changes": parsed_changes,
        "current_vendors": parsed_vendors,
        "selling_points": parsed_selling_points
    }
