"""
Section 1 Parser: Course Tier Classification

Purpose: Parse Premium/Mid/Budget classification with confidence and evidence

V2 Section 1 Structure:
{
  "tier": "Premium" | "Mid" | "Budget",
  "tier_confidence": 0.0-1.0,
  "pricing_evidence": [
    {"claim": "Weekend rate $80", "source": "https://..."},
    ...
  ]
}

Output:
{
  "tier": str,
  "confidence": float,
  "evidence": List[Dict]
}

Created: 2025-10-31
"""

from typing import Dict, Any, List


def parse(section1: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Section 1: Course Tier

    Args:
        section1: Section 1 JSON object

    Returns:
        {
            "tier": "Premium" | "Mid" | "Budget",
            "confidence": 0.0-1.0,
            "evidence": [{claim, source}]
        }

    Raises:
        ValueError: If tier is missing or invalid
    """
    if not section1:
        raise ValueError("Section 1 is empty or missing")

    # Extract tier (required)
    tier = section1.get("tier")
    if not tier:
        raise ValueError("Section 1 missing 'tier' field")

    if tier not in ["Premium", "Mid", "Budget"]:
        raise ValueError(f"Invalid tier: {tier}. Must be Premium, Mid, or Budget")

    # Extract confidence (required, default to 0.8 if missing)
    confidence = section1.get("tier_confidence", section1.get("confidence", 0.8))

    # Normalize confidence to float between 0 and 1
    if isinstance(confidence, str):
        # Handle percentage strings like "85%" or "0.85"
        confidence = confidence.replace("%", "").strip()
        confidence = float(confidence)
        if confidence > 1.0:
            confidence = confidence / 100.0

    confidence = float(confidence)

    # Validate confidence range
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"Confidence out of range: {confidence} (must be 0.0-1.0)")

    # Extract pricing evidence (optional)
    evidence = section1.get("pricing_evidence", [])
    if not isinstance(evidence, list):
        evidence = []

    # Ensure evidence has claim + source
    parsed_evidence = []
    for item in evidence:
        if isinstance(item, dict) and "claim" in item:
            parsed_evidence.append({
                "claim": item.get("claim", ""),
                "source": item.get("source", "")
            })

    return {
        "tier": tier,
        "confidence": round(confidence, 3),
        "evidence": parsed_evidence
    }
