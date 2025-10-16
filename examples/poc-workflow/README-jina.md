# Jina MCP Scraper POC

Real-world web scraping using the Jina MCP server with the Claude Agent SDK.

## What This Demonstrates

1. **External MCP Server Integration** - Using Jina's MCP server for web scraping
2. **API Key Configuration** - Properly passing credentials to MCP servers in the SDK
3. **Real Web Scraping** - Extracting data from actual websites
4. **Agent-Based Data Extraction** - Using a specialized scraper agent

## Setup

### 1. Get Jina API Key

Visit https://jina.ai/?sui=apikey and get a free API key.

### 2. Set Environment Variable

```bash
# Option 1: Export in terminal (temporary)
export JINA_API_KEY='your_api_key_here'

# Option 2: Create .env file (persistent)
cp .env.example .env
# Edit .env and add your API key
```

### 3. Run the Scraper

```bash
# Make sure you're in the project root
cd /path/to/claude-agent-sdk-python

# Run the POC
python examples/poc-workflow/jina_scraper.py
```

## The Task

This POC demonstrates:
- **Target URL**: https://vsga.org/member-clubs
- **Goal**: Find "Raspberry Falls Golf & Hunt Club"
- **Extract**: The course's detail page URL
- **Expected Result**: `https://vsga.org/courselisting/11945?hsLang=en`

## Key Difference: SDK vs CLI

### Claude Code CLI (`.mcp.json`)
```json
{
  "mcpServers": {
    "jina": {
      "command": "npx",
      "args": ["-y", "@jina-ai/mcp-server-jina"],
      "env": {
        "JINA_API_KEY": "${JINA_API_KEY}"
      }
    }
  }
}
```

### Claude Agent SDK (Python)
```python
mcp_servers = {
    "jina": {
        "command": "npx",
        "args": ["-y", "@jina-ai/mcp-server-jina"],
        "env": {
            "JINA_API_KEY": os.environ.get("JINA_API_KEY")
        }
    }
}
```

**Key Point**: The SDK requires the `env` field with actual values (not template strings), passed programmatically.

## Available Jina Tools

The Jina MCP server provides:
- `mcp__jina__fetch` - Fetch and parse web page content
- `mcp__jina__search` - Search the web using Jina's search API

## Troubleshooting

### "JINA_API_KEY environment variable not set"
- Make sure you've exported the environment variable
- Check: `echo $JINA_API_KEY`

### "MCP server failed to start"
- Ensure Node.js is installed: `node --version`
- Try installing manually: `npm install -g @jina-ai/mcp-server-jina`

### "Connection timeout"
- Check your internet connection
- Verify API key is valid
- Check Jina API status at https://jina.ai

## Expected Output

```
🌐 Starting Web Scraping POC with Jina MCP
======================================================================
✅ Jina API Key found: jsa_xxxxx...

📝 Task:
   URL: https://vsga.org/member-clubs
   Looking for: Raspberry Falls Golf & Hunt Club

======================================================================
🤖 Executing Scraper Agent...

💬 Claude: [Uses Jina tools to scrape and find the URL]

======================================================================
✅ Scraping Complete!
⏱️  Duration: XX.XXs
🔄 Turns: X
💰 Cost: $X.XXXX

======================================================================
🎯 RESULT FOUND:
   https://vsga.org/courselisting/11945?hsLang=en
======================================================================
```

## Next Steps

After this works:
1. Try scraping different websites
2. Extract different types of data
3. Add a second agent to process the scraped data
4. Store results in a database (Supabase)
