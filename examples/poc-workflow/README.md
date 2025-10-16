# Proof of Concept: Multi-Agent Workflow

This is a simple demonstration of the Claude Agent SDK's multi-agent capabilities.

## What This Demonstrates

1. **Custom Tools** - Creating in-process MCP tools with `@tool` decorator
2. **Multiple Agents** - Defining specialized agents with different roles
3. **Sequential Execution** - Agents working together to complete a task
4. **Complete Workflow** - End-to-end example from start to finish

## The Workflow

This POC creates a workflow with two agents:

### Agent 1: Calculator
- **Role**: Performs mathematical calculations
- **Tools**: Custom `calculate` tool
- **Model**: Sonnet

### Agent 2: Summarizer
- **Role**: Creates formatted summaries
- **Tools**: Standard tools (no custom tools needed)
- **Model**: Sonnet

## How It Works

```
User Prompt → Calculator Agent → Summarizer Agent → Final Result
              (does math)        (formats output)
```

## Running the POC

```bash
# Make sure you're in the project root
cd /path/to/claude-agent-sdk-python

# Run the POC
python examples/poc-workflow/simple_workflow.py
```

## Expected Output

You should see:
1. The workflow prompt
2. Claude using the calculator agent to perform calculations
3. Claude using the summarizer agent to create a summary
4. Final statistics (duration, cost, turns)

## Code Structure

- **Custom Tool Definition**: `@tool` decorator creates the calculator
- **MCP Server**: `create_sdk_mcp_server()` bundles tools
- **Agent Definitions**: `AgentDefinition` configures each agent's behavior
- **Workflow Execution**: `query()` runs the entire workflow

## What to Learn

Pay attention to:
- How agents are defined (description, prompt, tools, model)
- How custom tools are created
- How the SDK automatically routes work to the right agents
- How agents can work sequentially

## Next Steps

After seeing this work:
1. Try modifying the agents' prompts
2. Add another custom tool
3. Add a third agent
4. Change the workflow logic
