"""
Utility: JSON Response Parser

Standard way to extract JSON from agent text responses.
Handles common parsing patterns and edge cases.
"""

import json
import re
from typing import Optional, Dict, Any


def extract_json_from_text(text: str, required_field: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from agent text response

    Args:
        text: Text from agent (may include markdown, explanations, etc.)
        required_field: Optional field that must be present in JSON

    Returns:
        Parsed dict or None if not found/invalid

    Examples:
        >>> extract_json_from_text('Here is the data: {"email": "test@example.com"}')
        {'email': 'test@example.com'}

        >>> extract_json_from_text('```json\n{"result": 42}\n```')
        {'result': 42}
    """
    if not text:
        return None

    # Try to find JSON object
    # Pattern handles optional markdown code blocks
    if required_field:
        pattern = rf'\{{.*"{required_field}".*\}}'
    else:
        pattern = r'\{.*\}'

    json_match = re.search(pattern, text, re.DOTALL)

    if json_match:
        try:
            data = json.loads(json_match.group(0))

            # Validate required field if specified
            if required_field and required_field not in data:
                return None

            return data
        except json.JSONDecodeError:
            return None

    return None


def extract_json_array_from_text(text: str) -> Optional[list]:
    """
    Extract JSON array from text

    Args:
        text: Text containing JSON array

    Returns:
        Parsed list or None
    """
    if not text:
        return None

    array_match = re.search(r'\[.*\]', text, re.DOTALL)

    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            return None

    return None
