"""
Section 3 Parser: Volume Indicator (Annual Rounds)

Purpose: Parse estimated annual rounds per year

V2 Section 3 Structure:
{
  "estimated_annual_rounds": 27000,
  "volume_range": "22k-32k",
  "estimation_basis": [
    {"source": "https://...", "claim": "..."}
  ],
  "confidence": 0.7
}

Output:
{
  "estimate": int,  // Midpoint or explicit estimate
  "range": str,     // Text range
  "confidence": float,
  "sources": List[str]
}

Created: 2025-10-31
"""

from typing import Dict, Any, List
import re


def parse(section3: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Section 3: Volume Indicator

    Args:
        section3: Section 3 JSON object

    Returns:
        {
            "estimate": int,  // Annual rounds estimate
            "range": str,     // "20k-30k" format
            "confidence": float,
            "sources": List[str]  // Source URLs
        }
    """
    if not section3:
        return {
            "estimate": None,
            "range": "",
            "confidence": 0.0,
            "sources": []
        }

    # Extract estimate
    estimate = section3.get("estimated_annual_rounds", section3.get("estimate"))

    # Extract range
    volume_range = section3.get("volume_range", section3.get("range", ""))

    # If estimate is None but range exists, calculate midpoint
    if estimate is None and volume_range:
        estimate = _calculate_midpoint_from_range(volume_range)

    # Ensure estimate is int or None
    if estimate is not None:
        estimate = int(estimate)

    # Extract confidence
    confidence = section3.get("confidence", 0.7)
    if isinstance(confidence, str):
        confidence = confidence.replace("%", "").strip()
        confidence = float(confidence)
        if confidence > 1.0:
            confidence = confidence / 100.0
    confidence = float(confidence)

    # Extract sources
    estimation_basis = section3.get("estimation_basis", [])
    sources = []
    if isinstance(estimation_basis, list):
        for item in estimation_basis:
            if isinstance(item, dict) and "source" in item:
                sources.append(item["source"])
            elif isinstance(item, str):
                sources.append(item)

    return {
        "estimate": estimate,
        "range": volume_range,
        "confidence": round(confidence, 3),
        "sources": sources
    }


def _calculate_midpoint_from_range(range_str: str) -> int:
    """
    Calculate midpoint from range string like "22k-32k" or "20000-30000"

    Args:
        range_str: Range string

    Returns:
        Midpoint as integer
    """
    # Clean string
    range_str = range_str.lower().replace(",", "").strip()

    # Try to extract numbers
    # Match patterns like "22k-32k" or "20000-30000"
    match = re.search(r'(\d+\.?\d*)k?\s*-\s*(\d+\.?\d*)k?', range_str)

    if not match:
        return None

    low = float(match.group(1))
    high = float(match.group(2))

    # If 'k' in string, multiply by 1000
    if 'k' in range_str:
        low *= 1000
        high *= 1000

    midpoint = (low + high) / 2
    return int(midpoint)
