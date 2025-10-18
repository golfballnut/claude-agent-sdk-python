"""
Utility: Standard .env Loading

Provides consistent environment variable loading across all agents.
.env is located 4 levels up from agents/ directory.
"""

import os
from pathlib import Path
from typing import Optional


def load_project_env() -> bool:
    """
    Load .env from project root

    Directory structure:
    - agents/agent_file.py (current file)
    - agents/ -> poc-workflow/ -> examples/ -> claude-agent-sdk-python/ -> .env

    Returns:
        bool: True if .env loaded, False if not found
    """
    # Calculate path: 4 levels up from agents/
    env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"

    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
        return True

    return False


def get_api_key(key_name: str) -> Optional[str]:
    """
    Get API key from environment

    Args:
        key_name: Name of environment variable (e.g., "HUNTER_API_KEY")

    Returns:
        API key string or None if not set
    """
    return os.getenv(key_name)


def require_api_key(key_name: str) -> str:
    """
    Get required API key, raise error if not set

    Args:
        key_name: Name of environment variable

    Returns:
        API key string

    Raises:
        ValueError: If key not set
    """
    key = os.getenv(key_name)
    if not key:
        raise ValueError(f"{key_name} not set in environment")
    return key
