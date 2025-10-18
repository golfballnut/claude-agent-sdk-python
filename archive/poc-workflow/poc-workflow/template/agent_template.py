#!/usr/bin/env python3
"""
Agent {N}: {Agent Name} ({Specialist Type})
{One-sentence description of what this agent does}

Performance Targets:
- Success Rate: {X}%
- Cost: < ${X} per {operation}
- Speed: < {X}s per {operation}

Pattern:
- Custom SDK tool with {API/Service name}
- {N}-step discovery (NO FALLBACKS - nulls if not found)
- SDK MCP server (in-process)
- Haiku 4.5 model for cost optimization

Data Quality Rule: Returns null if not found - NEVER guesses or uses fallbacks

Usage:
    from agent{N}_{name} import {function_name}

    result = await {function_name}(input_data)
    print(result)
"""

import anyio
import json
from typing import Any, Dict
from pathlib import Path

# Add utils to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from env_loader import load_project_env, get_api_key
from json_parser import extract_json_from_text

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


# ============================================================================
# CUSTOM TOOL DEFINITION
# ============================================================================

@tool("{tool_name}", "{Tool description}", {
    "param1": str,
    "param2": str,
    # Add parameters as needed
})
async def {tool_name}_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Custom tool implementation

    Steps:
    1. {Primary method - e.g., API call}
    2. {Fallback method 1 - if needed}
    3. {Fallback method 2 - if needed}
    4. Return nulls if not found (NO GUESSING)

    Args:
        args: Dict with tool parameters

    Returns:
        MCP-formatted response with JSON data
    """
    import httpx
    import re

    # Extract parameters
    param1 = args["param1"]
    param2 = args["param2"]

    # Initialize results with nulls
    results = {
        "field1": None,
        "field2": None,
        "method": None,
        "confidence": 0,
        "steps_attempted": [],
    }

    # Load environment variables
    load_project_env()
    api_key = get_api_key("{API_KEY_NAME}")

    # STEP 1: Primary method (e.g., API call)
    if api_key:
        results["steps_attempted"].append("primary_method")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Make API call
                url = "https://api.example.com/endpoint"
                params = {
                    "param": param1,
                    "api_key": api_key
                }
                r = await client.get(url, params=params)
                data = r.json()

                # Extract results
                if data.get("data"):
                    results["field1"] = data["data"].get("field1")
                    results["field2"] = data["data"].get("field2")
                    results["method"] = "primary_method"
                    results["confidence"] = data["data"].get("confidence", 100)

                    # If found, return early
                    if results["field1"]:
                        return {
                            "content": [{
                                "type": "text",
                                "text": json.dumps(results)
                            }]
                        }
        except Exception as e:
            print(f"   ✗ Step 1 failed: {e}")

    # STEP 2: Fallback method (if needed)
    if not results["field1"]:
        results["steps_attempted"].append("fallback_method")
        try:
            # Implement fallback logic
            # Example: web search, alternative API, etc.
            pass
        except Exception as e:
            print(f"   ✗ Step 2 failed: {e}")

    # STEP 3: Not found (return honest nulls - NO GUESSING)
    if not results["field1"]:
        results["steps_attempted"].append("not_found")
        results["method"] = "not_found"

    # Return JSON only (for easy parsing)
    return {
        "content": [{
            "type": "text",
            "text": json.dumps(results)
        }]
    }


# ============================================================================
# AGENT FUNCTION
# ============================================================================

async def {agent_function}(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main agent entry point

    Args:
        input_data: Dict with required input fields

    Returns:
        Dict with original input + enriched data (nulls if not found)

    Example:
        >>> input = {"name": "John Doe", "company": "ACME Corp"}
        >>> result = await {agent_function}(input)
        >>> print(result["field1"])  # None if not found
    """

    # Create SDK MCP server with custom tool
    server = create_sdk_mcp_server("{server_name}", tools=[{tool_name}_tool])

    # Configure agent options
    options = ClaudeAgentOptions(
        mcp_servers={"{server_name}": server},
        allowed_tools=["mcp__{server_name}__{tool_name}"],
        disallowed_tools=["WebSearch", "WebFetch", "Task", "TodoWrite", "Bash", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        max_turns=2,  # Limit iterations for cost control
        model="claude-haiku-4-5",  # Cheapest model
        system_prompt=(
            "Use {tool_name} tool. It returns pure JSON. "
            "OUTPUT ONLY THE EXACT JSON - NO MARKDOWN, NO FORMATTING."
        ),
    )

    result_data = None
    result_message = None

    # Run agent
    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Process: {input_data}")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        # Parse JSON from response
                        result_data = extract_json_from_text(block.text, required_field="field1")

            if isinstance(msg, ResultMessage):
                result_message = msg

    # Merge results with input
    output = input_data.copy()
    if result_data:
        output.update(result_data)

    # Add metadata
    output["_cost"] = result_message.total_cost_usd if result_message else None
    output["_turns"] = result_message.num_turns if result_message else None

    return output


# ============================================================================
# BATCH PROCESSING (Optional)
# ============================================================================

async def process_batch(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Process multiple items through the agent

    Args:
        items: List of input dicts

    Returns:
        List of enriched dicts
    """
    results = []

    for i, item in enumerate(items, 1):
        print(f"\n[{i}/{len(items)}] Processing: {item.get('name', 'Unknown')}")

        try:
            result = await {agent_function}(item)

            # Check success
            if result.get("field1"):
                print(f"   ✅ Found: {result['field1']}")
            else:
                print(f"   ❌ Not found (clean null)")

            print(f"   Cost: ${result.get('_cost', 0):.4f}")

            results.append(result)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_item = item.copy()
            error_item["_error"] = str(e)
            results.append(error_item)

    return results


# ============================================================================
# DEMO / TEST
# ============================================================================

async def main():
    """Demo agent usage"""
    print("🔍 Agent {N}: {Agent Name}")
    print("="*70)

    # Test input
    test_input = {
        "param1": "test value 1",
        "param2": "test value 2"
    }

    print(f"Input: {test_input}\n")

    result = await {agent_function}(test_input)

    print(f"\n📊 Result:")
    print(f"   Field1: {result.get('field1', 'Not found')}")
    print(f"   Field2: {result.get('field2', 'Not found')}")
    print(f"   Method: {result.get('method', 'N/A')}")
    print(f"   Confidence: {result.get('confidence', 0)}%")
    print(f"   Cost: ${result.get('_cost', 0):.4f}")

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    anyio.run(main)
