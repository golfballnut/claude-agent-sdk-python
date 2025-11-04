"""
V2 Section Parsers

Purpose: Parse each of the 5 V2 research sections into structured data

Parsers:
- section1_tier: Course tier (Premium/Mid/Budget) + confidence + evidence
- section2_hazards: Water hazards assessment
- section3_volume: Annual rounds estimate
- section4_contacts: Decision makers with contact info
- section5_intel: Basic intelligence (ownership, vendors, changes)

Created: 2025-10-31
"""

from . import section1_tier
from . import section2_hazards
from . import section3_volume
from . import section4_contacts
from . import section5_intel

__all__ = [
    "section1_tier",
    "section2_hazards",
    "section3_volume",
    "section4_contacts",
    "section5_intel"
]
