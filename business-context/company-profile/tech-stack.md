# Links Choice Tech Stack

**Last Updated:** October 31, 2025
**Status:** "Confusing tech stack" (user's words) - needs consolidation/optimization

---

## Core Business Systems

### NetSuite ERP
**Purpose:** Enterprise resource planning
**Used For:**
- Inventory management
- Order management
- Financial operations
- B2B and B2C channels
- Reporting and analytics

**Status:** Primary system of record

---

## Data & Workflow Systems

### Supabase
**Purpose:** PostgreSQL database + backend services
**Used For:**
- Golf course enrichment data
- Contact discovery storage
- Course intelligence database
- AI agent data storage

**Current Use Cases:**
- `golf_courses` table
- `golf_course_contacts` table
- `llm_discovery_raw` table (planned)
- `enrichment_queue` table (planned)

### ClickUp
**Purpose:** Project management / CRM
**Used For:**
- Golf course outreach task management
- Contact qualification tracking
- Sales pipeline management
- Team collaboration

**Current Use Cases:**
- Golf course outreach tasks
- Contact enrichment workflows
- Custom fields for course data

### Render
**Purpose:** Cloud hosting for AI agents
**Used For:**
- Hosting enrichment agents (Docker containers)
- Edge functions (parsing, enrichment, sync)
- API endpoints for workflow automation

**Current Use Cases:**
- Golf enrichment API
- LLM parsing agent
- Apollo/Hunter enrichment agent
- ClickUp sync agent

---

## E-Commerce Platforms (B2C)

### Shopify
**Purpose:** Direct-to-consumer storefront
**Channel:** Golf Ball Nut
**Used For:**
- Consumer website
- Order processing
- Payment processing
- Product catalog

### Amazon
**Purpose:** Marketplace sales
**Channel:** Golf Ball Nut
**Used For:**
- Consumer golf ball sales
- Amazon FBA/FBM
- Prime eligibility

### Walmart Marketplace
**Purpose:** Marketplace sales
**Channel:** Golf Ball Nut
**Used For:**
- Consumer golf ball sales
- Walmart.com listings

### eBay
**Purpose:** Marketplace sales
**Channel:** Golf Ball Nut
**Used For:**
- Consumer golf ball sales
- Auction and fixed-price listings

---

## Fulfillment & Logistics

### Shipstation
**Purpose:** Multi-channel order fulfillment
**Used For:**
- Order aggregation from all sales channels
- Shipping label generation
- Carrier integration
- Tracking management

**Integrations:**
- Shopify
- Amazon
- Walmart
- eBay
- NetSuite

---

## AI & Automation Tools

### Current AI Stack (Golf Outreach)

**Data Sources:**
- Perplexity (LLM contact discovery) - via MCP
- Hunter.io (email verification) - via MCP
- Apollo (contact enrichment) - via API
- Supabase (data storage) - via MCP
- ClickUp (CRM sync) - via MCP

**Processing:**
- Claude (LLM parsing and enrichment)
- Render (agent hosting)
- Docker (containerization)

**Orchestration:**
- Supabase triggers (database-driven workflow)
- Render edge functions (API endpoints)

---

## Integration Challenges

### Current Pain Points

**Fragmentation:**
- "Confusing tech stack" (user's assessment)
- Many systems = many integration points
- Data sync complexity across platforms
- No unified view of inventory/customers

**Opportunities for Consolidation:**
- Unified inventory management (NetSuite + marketplaces)
- Single source of truth for golf course data (Supabase)
- Centralized workflow automation (Render agents)

### Future State Vision

**Ideal Architecture:**
```
NetSuite (ERP - core business)
    ↓
Supabase (unified data layer)
    ↓
    ├─→ B2B Sales (ClickUp + Render agents)
    ├─→ B2C Sales (Shopify, Amazon, Walmart, eBay)
    └─→ Fulfillment (Shipstation)
```

**AI Agent Opportunities:**
- Inventory allocation agent (B2B vs B2C)
- Pricing optimization agent (across channels)
- Customer service agent (unified inbox)
- Procurement agent (vendor management)

---

## MCP Tools in Use

### Current MCP Servers

**Supabase MCP:**
- `mcp__supabase__execute_sql` - Database queries
- `mcp__supabase__list_tables` - Schema exploration
- `mcp__supabase__apply_migration` - Schema updates

**ClickUp MCP:**
- `mcp__clickup__create_task` - Create outreach tasks
- `mcp__clickup__update_task` - Update task data
- `mcp__clickup__get_task` - Retrieve task info
- `mcp__clickup__get_workspace_tasks` - Bulk task queries

**Hunter.io MCP:**
- `mcp__hunter-io__Email-Verifier` - Email deliverability
- `mcp__hunter-io__Email-Finder` - Email discovery
- `mcp__hunter-io__Domain-Search` - Company research

**Perplexity MCP:**
- `mcp__perplexity-ask__perplexity_ask` - LLM research

**Firecrawl MCP:**
- `mcp__firecrawl__firecrawl_search` - Web search
- `mcp__firecrawl__firecrawl_scrape` - Content extraction

---

## Documentation Gaps

### What We Need to Document

**System Integration Map:**
- How data flows between systems
- Where is single source of truth for each data type
- What triggers what (workflow dependencies)

**Access & Credentials:**
- Who has access to what systems
- API keys and authentication
- Backup/recovery procedures

**Cost Structure:**
- What each system costs
- Per-transaction fees (Hunter, Apollo)
- Infrastructure costs (Render, Supabase)

**Performance Metrics:**
- System uptime/reliability
- API rate limits
- Data sync latency

**TODO:** Create detailed integration architecture doc

---

## Future Considerations

### System Consolidation Opportunities

**Short Term:**
- Centralize golf course data in Supabase (in progress)
- Unify AI agents on Render (in progress)
- Standardize MCP tool usage

**Medium Term:**
- Evaluate NetSuite alternatives (too expensive?)
- Marketplace integration simplification
- Unified customer service platform

**Long Term:**
- AI-powered ERP (NetSuite replacement?)
- Autonomous inventory management
- Cross-channel pricing optimization

---

## Related Documents

- **Links Choice Overview:** `links-choice-overview.md`
- **Enrichment Requirements:** `../enrichment-requirements/workflow-mapping.md`
