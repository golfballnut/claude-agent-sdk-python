#!/usr/bin/env python3
"""
SDK Agent POC Test Script

Tests the SDK agent + MCP tools architecture on 3 NC golf courses.
Compares results against edge function baseline from Session 12.

Usage:
    python test_sdk_agent.py              # Run all 3 test courses
    python test_sdk_agent.py --single     # Run single course test
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from orchestrator import (
    GolfCourseResearchOrchestrator,
    research_test_courses
)


async def test_single_course():
    """Test on a single course (The Tradition)"""
    print("🧪 Testing SDK Agent - Single Course POC\n")

    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")

    orchestrator = GolfCourseResearchOrchestrator(supabase_url, supabase_key)

    result = await orchestrator.research_course(
        course_name="The Tradition Golf Club",
        city="Charlotte",
        state_code="NC"
    )

    print("\n✅ Single course test complete!")
    return result


async def test_all_courses():
    """Test on all 3 NC courses"""
    print("🧪 Testing SDK Agent - Full POC (3 courses)\n")

    results = await research_test_courses()

    print("\n✅ Full POC test complete!")
    return results


def check_environment():
    """Check required environment variables"""
    required = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
    ]

    recommended = [
        "FIRECRAWL_API_KEY",
        "HUNTER_API_KEY",
        "JINA_API_KEY",
        "PERPLEXITY_API_KEY",
    ]

    print("🔍 Checking environment variables...\n")

    # Check required
    missing_required = []
    for var in required:
        if var in os.environ:
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing (REQUIRED)")
            missing_required.append(var)

    # Check recommended
    missing_recommended = []
    for var in recommended:
        if var in os.environ:
            print(f"✅ {var}: Set")
        else:
            print(f"⚠️  {var}: Missing (Recommended for best results)")
            missing_recommended.append(var)

    if missing_required:
        print(f"\n❌ Error: Missing required environment variables: {', '.join(missing_required)}")
        print("\nPlease set these variables and try again.")
        return False

    if missing_recommended:
        print(f"\n⚠️  Warning: Missing recommended API keys: {', '.join(missing_recommended)}")
        print("Results may be limited. For best accuracy, configure all MCP tools.\n")

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test SDK Agent POC")
    parser.add_argument(
        "--single",
        action="store_true",
        help="Test on single course only (faster)"
    )
    parser.add_argument(
        "--skip-env-check",
        action="store_true",
        help="Skip environment variable check"
    )

    args = parser.parse_args()

    # Check environment
    if not args.skip_env_check:
        if not check_environment():
            sys.exit(1)
        print()

    # Run test
    try:
        if args.single:
            asyncio.run(test_single_course())
        else:
            asyncio.run(test_all_courses())

        print("\n🎉 POC test completed successfully!")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error during POC test: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
