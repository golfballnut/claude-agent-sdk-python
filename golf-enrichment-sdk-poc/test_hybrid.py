#!/usr/bin/env python3
"""
Test Hybrid Orchestrator
Session 16: Direct API integration testing
"""

import asyncio
import sys
from pathlib import Path

# Load environment variables from golf-enrichment-active/docker/.env
env_file = Path(__file__).parent.parent / "golf-enrichment-active" / "docker" / ".env"

if env_file.exists():
    print(f"📋 Loading environment from: {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # Remove quotes if present
                value = value.strip('"').strip("'")
                import os
                os.environ[key] = value
    print("✅ Environment variables loaded\n")
else:
    print(f"⚠️  Warning: {env_file} not found")
    print("   API calls may fail without proper credentials\n")

# Import orchestrator after loading environment
from orchestrator_hybrid import test_single_course, test_batch_courses


def main():
    """Run tests based on command line argument"""

    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        print("🎯 Running BATCH test (3 courses)...\n")
        asyncio.run(test_batch_courses())
    else:
        print("🎯 Running SINGLE course test...\n")
        asyncio.run(test_single_course())


if __name__ == "__main__":
    main()
