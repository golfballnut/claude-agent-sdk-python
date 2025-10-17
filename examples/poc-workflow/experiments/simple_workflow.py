#!/usr/bin/env python3
"""
Proof of Concept: Simple Multi-Agent Workflow

This demonstrates:
1. Creating custom tools with @tool decorator
2. Defining multiple agents with AgentDefinition
3. Sequential agent execution
4. Complete workflow from start to finish
"""

import anyio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


# Custom tool: Calculator
@tool(
    "calculate",
    "Performs mathematical calculations. Returns the result of the expression.",
    {"expression": str}
)
async def calculate(args):
    """Calculate mathematical expressions"""
    expression = args["expression"]
    try:
        # Simple eval for demo (in production, use a safe math parser)
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "content": [
                {"type": "text", "text": f"Result: {result}"}
            ]
        }
    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error: {str(e)}"}
            ],
            "isError": True
        }


async def main():
    print("🚀 Starting Multi-Agent Workflow POC")
    print("=" * 70)

    # Create MCP server with custom tools
    calc_server = create_sdk_mcp_server(
        name="calculator",
        version="1.0.0",
        tools=[calculate]
    )

    # Define agents
    options = ClaudeAgentOptions(
        agents={
            "calculator": AgentDefinition(
                description="Performs mathematical calculations and solves math problems",
                prompt=(
                    "You are a calculator agent. Use the calculate tool to solve "
                    "mathematical expressions. Always show your work."
                ),
                tools=["mcp__calculator__calculate"],
                model="sonnet"
            ),
            "summarizer": AgentDefinition(
                description="Summarizes results and creates formatted reports",
                prompt=(
                    "You are a summarizer agent. Take calculation results and "
                    "create clear, well-formatted summaries. Use markdown formatting."
                ),
                tools=None,  # Inherits all tools (but won't need calculator)
                model="sonnet"
            )
        },
        mcp_servers={"calculator": calc_server},
        allowed_tools=["mcp__calculator__calculate"],
        permission_mode="acceptEdits"
    )

    # The workflow prompt
    workflow_prompt = """
    Please complete this workflow:

    1. Use the calculator agent to compute: (25 + 15) * 2
    2. Use the calculator agent to compute: 100 / 4
    3. Use the summarizer agent to create a brief summary of the results

    Execute these steps in sequence.
    """

    print("\n📝 Workflow Prompt:")
    print(workflow_prompt)
    print("\n" + "=" * 70)
    print("🤖 Executing Workflow...\n")

    # Execute the workflow
    async for message in query(prompt=workflow_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"💬 Claude: {block.text}")
                    print()

        elif isinstance(message, ResultMessage):
            print("=" * 70)
            print("✅ Workflow Complete!")
            print(f"⏱️  Duration: {message.duration_ms / 1000:.2f}s")
            print(f"🔄 Turns: {message.num_turns}")
            if message.total_cost_usd:
                print(f"💰 Cost: ${message.total_cost_usd:.4f}")
            print(f"📊 Session ID: {message.session_id}")


if __name__ == "__main__":
    anyio.run(main)
