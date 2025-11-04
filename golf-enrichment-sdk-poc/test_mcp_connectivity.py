#!/usr/bin/env python3
"""
Simple MCP Connectivity Test

Tests if the SDK can successfully connect to and use MCP tools.
This validates the .mcp.json configuration before running the full POC test.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions


async def test_mcp_connectivity():
    """Test MCP tool connectivity"""

    print("🧪 Testing MCP Connectivity\n")
    print("="*60)

    # Path to .mcp.json
    mcp_config_path = Path(__file__).parent / ".mcp.json"

    if not mcp_config_path.exists():
        print(f"❌ Error: .mcp.json not found at {mcp_config_path}")
        return False

    print(f"✅ Found .mcp.json at: {mcp_config_path}\n")

    # Configure SDK with MCP servers
    options = ClaudeAgentOptions(
        mcp_servers=str(mcp_config_path),
        allowed_tools=[
            # Start with just Jina (simplest MCP tool)
            "mcp__jina__jina_reader",
            "mcp__jina__jina_search",
        ]
    )

    print("📋 Testing Jina MCP Server...\n")

    try:
        async with ClaudeSDKClient(options=options) as client:
            # Simple test: Use Jina to read a well-known URL
            await client.query("Use the jina_reader tool to read https://example.com and tell me what you find.")

            print("📝 Agent response:\n")

            tool_used = False
            async for message in client.receive_response():
                # Check if tools were used
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text') and block.text:
                            print(f"  {block.text[:200]}...")

                        # Check for tool use
                        if hasattr(block, 'name'):
                            print(f"  🔧 Tool used: {block.name}")
                            tool_used = True

            print()

            if tool_used:
                print("✅ SUCCESS: MCP tool was successfully called!")
                print("✅ MCP configuration is working correctly")
                return True
            else:
                print("⚠️  WARNING: No MCP tools were used")
                print("⚠️  Agent may not have permission or tools not properly configured")
                return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""

    # Check environment variables
    print("🔍 Checking environment variables...")
    required = ["JINA_API_KEY"]

    missing = []
    for var in required:
        if var in os.environ:
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: Missing")
            missing.append(var)

    if missing:
        print(f"\n❌ Missing required environment variables: {', '.join(missing)}")
        print("Run this script via ./run_poc_test.sh to load environment automatically")
        return 1

    print()

    # Run connectivity test
    success = asyncio.run(test_mcp_connectivity())

    if success:
        print("\n🎉 MCP connectivity test PASSED")
        print("   You can now run the full POC test with ./run_poc_test.sh --single")
        return 0
    else:
        print("\n❌ MCP connectivity test FAILED")
        print("   Fix configuration issues before running full POC test")
        return 1


if __name__ == "__main__":
    sys.exit(main())
