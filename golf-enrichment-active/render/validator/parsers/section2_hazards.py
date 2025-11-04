"""
Section 2 Parser: Water Hazards Assessment

Purpose: Parse water hazard data for retrieval expansion opportunity

V2 Section 2 Structure:
{
  "has_water_hazards": true,
  "hazard_count": 18,  // Number of holes with hazards
  "hazard_details": "18/18 holes have water in play...",
  "source": "https://..."
}

Output:
{
  "count": int,  // Number of holes with hazards
  "rating": str,  // hazard_details text
  "source": str,
  "confidence": float
}

Created: 2025-10-31
"""

from typing import Dict, Any


def parse(section2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Section 2: Water Hazards

    Args:
        section2: Section 2 JSON object

    Returns:
        {
            "count": int,  // Holes with hazards (0-18)
            "rating": str,  // Description of hazards
            "source": str,
            "confidence": float
        }
    """
    if not section2:
        # No water hazards mentioned
        return {
            "count": 0,
            "rating": "No water hazards information available",
            "source": "",
            "confidence": 0.5
        }

    # Extract has_water_hazards boolean
    has_hazards = section2.get("has_water_hazards", False)

    # Extract hazard count
    hazard_count = section2.get("hazard_count", 0)

    # If has_hazards is true but count is 0, try to infer from details
    if has_hazards and hazard_count == 0:
        # Look for count in details string
        details = section2.get("hazard_details", "")
        if "18/18" in details or "all 18" in details.lower():
            hazard_count = 18
        elif details:
            # Default to 1 if details exist but count unknown
            hazard_count = 1

    # Extract hazard details (rating description)
    hazard_rating = section2.get("hazard_details", section2.get("rating", ""))
    if not hazard_rating and hazard_count > 0:
        hazard_rating = f"{hazard_count} holes have water hazards"
    elif not hazard_rating:
        hazard_rating = "No water hazards information available"

    # Extract source
    source = section2.get("source", "")

    # Calculate confidence based on data quality
    confidence = 1.0  # Default high confidence
    if not source:
        confidence = 0.7  # Lower confidence if no source
    if hazard_count == 0 and has_hazards:
        confidence = 0.6  # Conflicting data

    return {
        "count": int(hazard_count),
        "rating": hazard_rating,
        "source": source,
        "confidence": round(confidence, 3)
    }
