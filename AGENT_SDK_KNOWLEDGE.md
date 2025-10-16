# Claude Agent SDK - Comprehensive Knowledge Base

**Last Updated:** 2025-10-16
**SDK Version:** 0.1.3 (Alpha)
**Purpose:** Foundation knowledge for building 500+ agent workflows

---

## 1. Core Architecture

### 1.1 What Is the Agent SDK?

The Claude Agent SDK is a Python/TypeScript framework for building **production-ready AI agents** powered by Claude. It's built on the same foundation as Claude Code CLI but designed for **programmatic integration**.

**Key Principle:** The SDK provides a **harness** around Claude's API that manages:
- Context management (automatic compaction to prevent overflow)
- Tool ecosystem (file ops, code execution, web search, MCP extensibility)
- Permission systems (fine-grained control over tool access)
- Session management (single-shot or multi-turn conversations)

### 1.2 SDK vs CLI: Critical Differences

| Feature | Claude Code CLI | Agent SDK (Python) |
|---------|----------------|-------------------|
| **Purpose** | Interactive development | Programmatic integration |
| **Configuration** | `.mcp.json`, `.claude/` files | Runtime via `ClaudeAgentOptions` |
| **MCP Servers** | Auto-loaded from `.mcp.json` | Must pass programmatically |
| **Settings** | Auto-loads `CLAUDE.md`, `settings.json` | Isolated by default (opt-in via `setting_sources`) |
| **System Prompt** | Auto-applies Claude Code prompt | Empty by default (must set explicitly) |
| **Deployment** | Developer machine only | CI/CD, servers, cloud functions |

**⚠️ Critical:** The SDK is **intentionally isolated** from filesystem configs to ensure predictable behavior in deployed environments.

### 1.3 Two Modes of Operation

#### Mode 1: Single Message (`query()` function)

```python
from claude_agent_sdk import query

async for message in query(prompt="What is 2+2?"):
    print(message)
```

**Characteristics:**
- Stateless (each call is independent)
- One-shot request-response
- Simpler API
- No hooks or custom tools support
- Good for: Batch processing, serverless functions, simple automation

#### Mode 2: Streaming (`ClaudeSDKClient` class)

```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient(options=options) as client:
    await client.query("First message")
    async for msg in client.receive_response():
        print(msg)
```

**Characteristics:**
- Stateful (maintains conversation context)
- Bidirectional communication
- Supports hooks, custom tools, images
- Can interrupt, change permissions mid-session
- Good for: Interactive apps, complex workflows, tool integration

**🔑 Key Decision:** Use streaming mode for anything with MCP servers, custom tools, or hooks.

---

## 2. Agents & Subagents

### 2.1 What Are Agents?

Agents are **specialized configurations** of Claude with:
1. **Description** - When to use this agent (triggers automatic invocation)
2. **Prompt** - System instructions defining the agent's role
3. **Tools** - Which tools the agent can access
4. **Model** - Which Claude model to use (sonnet, opus, haiku, inherit)

**Important:** Agents are NOT separate processes. They're **configuration** that Claude uses to route work.

### 2.2 Agent Definition

```python
from claude_agent_sdk import AgentDefinition

agents = {
    "scraper": AgentDefinition(
        description="Scrapes websites and extracts specific information",
        prompt="You are a web scraping specialist. Use tools to fetch and parse content.",
        tools=["mcp__jina__read", "mcp__jina__search"],
        model="sonnet"
    ),
    "processor": AgentDefinition(
        description="Processes and stores scraped data",
        prompt="You are a data processor. Store data in databases and CRMs.",
        tools=["mcp__supabase__insert", "mcp__clickup__create"],
        model="sonnet"
    )
}

options = ClaudeAgentOptions(agents=agents)
```

### 2.3 How Agents Get Invoked

Claude **automatically selects agents** based on:
1. **Description matching** - Compares task to agent descriptions
2. **User explicit request** - "Use the scraper agent to..."
3. **Context** - Previous conversation flow

**Example:**
```python
# Prompt: "Scrape vsga.org and find the course URL"
# Claude sees "scrape" → matches "scraper" agent description → uses that agent
```

### 2.4 Sequential vs Parallel Execution

**Sequential** (one agent finishes before next starts):
```python
prompt = """
1. Use scraper agent to get data from URL
2. Use processor agent to store the data
"""
# Agents run one after another
```

**Parallel** (multiple agents run concurrently):
```python
# Documentation states: "Multiple subagents can run concurrently"
# Achieved by framing the task to allow parallel work
prompt = """
Run these tasks in parallel:
- Agent A: analyze code style
- Agent B: check security
- Agent C: verify tests
"""
```

---

## 3. MCP (Model Context Protocol) Integration

### 3.1 Three Types of MCP Servers

#### Type 1: External stdio Servers

**What:** Separate subprocess communicating via stdin/stdout

```python
# CORRECT: Use "jina-mcp-tools" (not "@jina-ai/mcp-server-jina")
mcp_servers = {
    "jina": {
        "command": "npx",
        "args": ["-y", "jina-mcp-tools"],
        "env": {
            "JINA_API_KEY": os.environ.get("JINA_API_KEY")
        }
    }
}
```

**Pros:** Standard MCP servers work as-is
**Cons:** Subprocess overhead, potential connection issues

#### Type 2: HTTP/SSE Servers

**What:** Remote servers accessed via network

```python
mcp_servers = {
    "remote-service": {
        "type": "sse",
        "url": "https://api.example.com/mcp",
        "headers": {
            "Authorization": f"Bearer {api_key}"
        }
    }
}
```

#### Type 3: SDK MCP Servers (In-Process)

**What:** Tools running directly in your Python process

```python
@tool("custom_tool", "Description", {"param": str})
async def my_tool(args):
    # Your logic here
    return {"content": [{"type": "text", "text": "result"}]}

server = create_sdk_mcp_server("my-tools", tools=[my_tool])

mcp_servers = {"my-tools": server}
```

**Pros:** No subprocess, faster, easier debugging
**Cons:** Must implement tool logic yourself

### 3.2 MCP Server Lifecycle

1. **SDK starts** → Spawns subprocess (for stdio) or connects (for HTTP/SSE)
2. **Initialization** → SDK sends init request, waits for response
3. **Tool discovery** → SDK queries available tools
4. **Runtime** → Claude requests tools, SDK routes to server
5. **Shutdown** → SDK closes connections/processes

**Debug Point:** Check `SystemMessage` with `init` subtype for MCP server status:
```python
if message.subtype == "init":
    mcp_servers = message.data.get('mcp_servers', [])
    # Check: [{'name': 'jina', 'status': 'connected'}] or 'failed'
```

### 3.3 Tool Naming Convention

All MCP tools follow: `mcp__{server_name}__{tool_name}`

**Examples:**
- SDK server "jina-tools" with tool "read" → `mcp__jina-tools__read`
- External server "supabase" with tool "insert" → `mcp__supabase__insert`

**In allowed_tools:**
```python
allowed_tools = [
    "mcp__jina-tools__read",
    "mcp__jina-tools__search"
]
```

### 3.4 Common MCP Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `status: 'failed'` | Server won't start | Check command, args, PATH |
| No tools available | Server started but no tools exported | Check server implementation |
| Authorization error | Missing/invalid API key | Verify `env` config |
| Using `query()` | Simple mode doesn't fully support MCP | Use `ClaudeSDKClient` instead |

---

## 4. Custom Tools (`@tool` decorator)

### 4.1 Tool Structure

```python
from claude_agent_sdk import tool

@tool(
    "tool_name",              # Unique identifier
    "What this tool does",    # Description for Claude
    {"param1": str, "param2": int}  # Input schema
)
async def my_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Tool implementation"""
    # Access parameters
    value = args["param1"]

    # Do work
    result = process(value)

    # Return in MCP format
    return {
        "content": [
            {"type": "text", "text": f"Result: {result}"}
        ]
    }
```

### 4.2 Tool Return Format

**Success:**
```python
return {
    "content": [
        {"type": "text", "text": "Your result here"}
    ]
}
```

**Error:**
```python
return {
    "content": [
        {"type": "text", "text": "Error message"}
    ],
    "is_error": True
}
```

### 4.3 Creating SDK MCP Server

```python
from claude_agent_sdk import create_sdk_mcp_server

server = create_sdk_mcp_server(
    name="my-tools",
    version="1.0.0",
    tools=[tool1, tool2, tool3]
)

options = ClaudeAgentOptions(
    mcp_servers={"my-tools": server},
    allowed_tools=[
        "mcp__my-tools__tool1",
        "mcp__my-tools__tool2"
    ]
)
```

### 4.4 Best Practices for Custom Tools

1. **Keep tools focused** - One tool, one clear purpose
2. **Add good descriptions** - Claude uses these to decide when to call
3. **Handle errors gracefully** - Return `is_error` instead of throwing
4. **Use type hints** - Better IDE support and validation
5. **Make tools async** - Enables concurrent operations

---

## 5. Permissions System

### 5.1 Four Permission Modes

| Mode | Behavior | Use When |
|------|----------|----------|
| `default` | Normal permission checks | Production, user oversight needed |
| `plan` | Planning mode (SDK: not fully supported) | Architecture/planning tasks |
| `acceptEdits` | Auto-approve file operations only | Safe file manipulation |
| `bypassPermissions` | Auto-approve ALL tools | Testing, trusted environments only |

### 5.2 Permission Flow

```
User requests tool use
    ↓
PreToolUse Hook (if configured)
    ↓
Deny Rules (from settings.json)
    ↓
Allow Rules (from settings.json)
    ↓
Ask Rules (from settings.json)
    ↓
Permission Mode Check
    ↓
canUseTool Callback (if configured)
    ↓
PostToolUse Hook (if configured)
    ↓
Tool executes
```

### 5.3 canUseTool Callback

```python
async def check_tool_use(tool_name: str, tool_input: dict, context) -> PermissionResult:
    if tool_name == "Bash" and "rm -rf" in tool_input.get("command", ""):
        return PermissionResultDeny(message="Dangerous command blocked")
    return PermissionResultAllow()

options = ClaudeAgentOptions(
    can_use_tool=check_tool_use
)
```

---

## 6. Message Types & Flow

### 6.1 Message Types

**UserMessage:**
```python
UserMessage(content="Hello", parent_tool_use_id=None)
```

**AssistantMessage:**
```python
AssistantMessage(
    content=[
        TextBlock(text="Response"),
        ToolUseBlock(id="...", name="Read", input={...})
    ],
    model="claude-sonnet-4-5"
)
```

**SystemMessage:**
```python
SystemMessage(
    subtype="init",  # or "error_during_execution", etc.
    data={...}
)
```

**ResultMessage:**
```python
ResultMessage(
    duration_ms=1000,
    num_turns=3,
    total_cost_usd=0.05,
    usage={...}
)
```

### 6.2 Content Blocks

- `TextBlock` - Plain text from Claude
- `ThinkingBlock` - Claude's internal reasoning
- `ToolUseBlock` - Tool invocation request
- `ToolResultBlock` - Result from tool execution

---

## 7. Common Patterns

### 7.1 Simple One-Shot Query

```python
from claude_agent_sdk import query

async for message in query(prompt="What is 2+2?"):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
```

### 7.2 Multi-Turn Conversation

```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient() as client:
    # Turn 1
    await client.query("Explain quantum computing")
    async for msg in client.receive_response():
        print(msg)

    # Turn 2 - maintains context
    await client.query("How does entanglement work?")
    async for msg in client.receive_response():
        print(msg)
```

### 7.3 Multi-Agent Workflow

```python
options = ClaudeAgentOptions(
    agents={
        "agent1": AgentDefinition(...),
        "agent2": AgentDefinition(...)
    }
)

async with ClaudeSDKClient(options=options) as client:
    prompt = """
    1. Use agent1 to fetch data
    2. Use agent2 to process data
    """
    await client.query(prompt)
    async for msg in client.receive_response():
        process(msg)
```

### 7.4 Custom Tools + Agents

```python
# Define tools
@tool("scrape", "Scrapes web pages", {"url": str})
async def scrape(args):
    # Implementation
    pass

# Create server
server = create_sdk_mcp_server("tools", tools=[scrape])

# Configure with agents
options = ClaudeAgentOptions(
    agents={
        "scraper": AgentDefinition(
            description="Web scraping specialist",
            prompt="You scrape websites...",
            tools=["mcp__tools__scrape"]
        )
    },
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__scrape"]
)
```

---

## 8. Debugging & Troubleshooting

### 8.1 Enable MCP Server Debugging

Check `SystemMessage` with `init` subtype:

```python
async for message in client.receive_messages():
    if isinstance(message, SystemMessage) and message.subtype == "init":
        mcp_servers = message.data.get('mcp_servers', [])
        for server in mcp_servers:
            print(f"Server: {server['name']}, Status: {server['status']}")
```

### 8.2 Common Issues

**Agent not invoked:**
- Check agent description matches task
- Ensure tools are in `allowed_tools`
- Try explicit "Use the {agent_name} agent to..."

**MCP server fails:**
- Use `ClaudeSDKClient`, not `query()`
- Check command is in PATH (`npx`, `python`, etc.)
- Verify `env` variables are set
- Look at stderr output

**Hallucinations:**
- Agent doesn't have access to needed tools
- Tools return incomplete data
- Agent description is too vague

---

## 9. Key Takeaways for 500-Agent System

### 9.1 Architecture Decisions

1. **One deployment with agent registry**
   - All agents defined in code/database
   - Shared MCP servers and tools
   - Single process handles all workflows

2. **Use streaming mode (`ClaudeSDKClient`)**
   - Full MCP support
   - Hooks for validation
   - Better error handling

3. **Prefer SDK MCP servers over external**
   - Faster (no subprocess)
   - Easier debugging
   - More reliable

4. **Agent descriptions are critical**
   - Must clearly describe when to use
   - Used for automatic routing
   - Be specific, not generic

### 9.2 Testing Strategy

1. **Test locally first** with simple agents
2. **Verify MCP servers connect** (`status: 'connected'`)
3. **Check agent invocation** (right agent for task?)
4. **Validate results** (not hallucinations)
5. **Monitor costs** (`ResultMessage.total_cost_usd`)

---

## 10. Next Steps

- [x] Build knowledge base
- [ ] Fix Jina MCP server connection
- [ ] Test external MCP servers properly
- [ ] Create template system for building agents
- [ ] Deploy first production workflow