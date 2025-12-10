# Connect Claude Code to tools via MCP

Claude Code can connect to hundreds of external tools and data sources through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction), an open source standard for AI-tool integrations. MCP servers give Claude Code access to your tools, databases, and APIs.

## What you can do with MCP

With MCP servers connected, you can ask Claude Code to:

- **Implement features from issue trackers**: "Add the feature described in JIRA issue ENG-4521 and create a PR on GitHub."
- **Analyze monitoring data**: "Check Sentry and Statsig to check the usage of the feature described in ENG-4521."
- **Query databases**: "Find emails of 10 random users who used feature ENG-4521, based on our PostgreSQL database."
- **Integrate designs**: "Update our standard email template based on the new Figma designs that were posted in Slack"
- **Automate workflows**: "Create Gmail drafts inviting these 10 users to a feedback session about the new feature."

## Popular MCP servers

Here are some commonly used MCP servers you can connect to Claude Code:

> **Warning:** Use third party MCP servers at your own risk - Anthropic has not verified the correctness or security of all these servers. Make sure you trust MCP servers you are installing. Be especially careful when using MCP servers that could fetch untrusted content, as these can expose you to prompt injection risk.

### Third-Party Services

**[Day AI](https://day.ai/mcp)**
- Analyze & update CRM records
- Command: `claude mcp add day-ai --transport http https://day.ai/api/mcp`

**[Fellow.ai](https://help.fellow.ai/en/articles/12622641-fellow-s-mcp-server)**
- Chat with your meetings to uncover actionable insights
- Command: `claude mcp add fellow-ai --transport http https://fellow.app/mcp`

**[Scholar Gateway](https://docs.scholargateway.ai/)**
- Enhance responses with scholarly research and citations
- Command: `claude mcp add scholar-gateway --transport http https://connector.scholargateway.ai/mcp`

**[Ticket Tailor](https://help.tickettailor.com/en/articles/11892797-how-to-connect-ticket-tailor-to-your-favourite-ai-agent)**
- Event platform for managing tickets, orders & more
- Command: `claude mcp add --transport http tickettailor https://mcp.tickettailor.ai/mcp`

**[Linear](https://linear.app/docs/mcp)**
- Manage issues, projects & team workflows in Linear
- Command: `claude mcp add --transport http linear https://mcp.linear.app/mcp`

**[Netlify](https://docs.netlify.com/build/build-with-ai/netlify-mcp-server/)**
- Create, deploy, manage, and secure websites on Netlify
- Command: `claude mcp add --transport http netlify https://netlify-mcp.netlify.app/mcp`

**[Hugging Face](https://huggingface.co/settings/mcp)**
- Access the HF Hub and thousands of Gradio Apps
- Command: `claude mcp add --transport http hugging-face https://huggingface.co/mcp`

**[ActiveCampaign](https://developers.activecampaign.com/page/mcp)**
- Autonomous marketing to transform how you work
- Requires user-specific URL. [Get your URL here](https://developers.activecampaign.com/page/mcp).

**[Asana](https://developers.asana.com/docs/using-asanas-model-control-protocol-mcp-server)**
- Connect to Asana to coordinate tasks, projects, and goals
- Command: `claude mcp add --transport sse asana https://mcp.asana.com/sse`

**[Atlassian](https://www.atlassian.com/platform/remote-mcp-server)**
- Access Jira & Confluence from Claude
- Command: `claude mcp add --transport sse atlassian https://mcp.atlassian.com/v1/sse`

**[Aura](https://docs.getaura.ai/)**
- Company intelligence & workforce analytics
- Command: `claude mcp add --transport http auraintelligence https://mcp.auraintelligence.com/mcp`

**[BioRender](https://help.biorender.com/hc/en-gb/articles/30870978672157-How-to-use-the-BioRender-MCP-connector)**
- Search for and use scientific templates and icons
- Command: `claude mcp add biorender --transport http https://mcp.services.biorender.com/mcp`

**[MT Newswires](https://console.blueskyapi.com/docs/EDGE/news/MT_NEWSWIRES_Global#mcp)**
- Trusted real-time global financial news provider
- Command: `claude mcp add --transport http mtnewswire`

**[Canva](https://www.canva.dev/docs/connect/canva-mcp-server-setup/)**
- Search, create, autofill, and export Canva designs from a prompt
- Command: `claude mcp add --transport http canva https://mcp.canva.com/mcp`

**[CData Connect AI](https://cloud.cdata.com/docs/Claude-Client.html)**
- Connect 270+ enterprise sources to Claude
- Command: `claude mcp add cdata-connect-ai --transport http https://mcp.cloud.cdata.com/mcp`

**[PubMed](https://support.claude.com/en/articles/12614801-using-the-pubmed-connector-in-claude)**
- Search biomedical literature from PubMed
- Command: `claude mcp add pubmed --transport http https://pubmed.mcp.claude.com/mcp`

**[Cloudflare](https://developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/)**
- Build applications with compute, storage, and AI
- Command: `claude mcp add --transport http cloudflare https://bindings.mcp.cloudflare.com/mcp`

**[Cloudinary](https://cloudinary.com/documentation/cloudinary_llm_mcp#available_mcp_servers)**
- Manage, transform and deliver your images & videos
- Command: `claude mcp add --transport http cloudinary https://asset-management.mcp.cloudinary.com/sse`

**[Crossbeam](https://help.crossbeam.com/en/articles/12601327-crossbeam-mcp-server-beta)**
- Explore partner data and ecosystem insights in Claude
- Command: `claude mcp add crossbeam --transport http https://mcp.crossbeam.com`

**[Databricks](https://docs.databricks.com/aws/en/generative-ai/mcp/connect-external-services)**
- Managed MCP servers with Unity Catalog and Mosaic AI
- Requires user-specific URL. [Get your URL here](https://docs.databricks.com/aws/en/generative-ai/mcp/connect-external-services).

**[Egnyte](https://developers.egnyte.com/docs/Remote_MCP_Server)**
- Securely access and analyze Egnyte content
- Command: `claude mcp add --transport http egnyte https://mcp-server.egnyte.com/mcp`

**[Figma](https://help.figma.com/hc/en-us/articles/32132100833559)**
- Create better code with Figma context
- Command: `claude mcp add --transport http figma-remote-mcp https://mcp.figma.com/mcp`

**[Clockwise](https://support.getclockwise.com/article/238-connecting-to-clockwise-mcp)**
- Advanced scheduling and time management for work
- Command: `claude mcp add --transport http clockwise https://mcp.getclockwise.com/mcp`

**[Intercom](https://developers.intercom.com/docs/guides/mcp)**
- AI access to Intercom data for better customer insights
- Command: `claude mcp add --transport http intercom https://mcp.intercom.com/mcp`

**[Jotform](https://www.jotform.com/developers/mcp)**
- Create forms & analyze submissions inside Claude
- Command: `claude mcp add --transport http jotform https://mcp.jotform.com/`

**[Kiwi.com Flights](https://mcp-install-instructions.alpic.cloud/servers/kiwi-com-flight-search)**
- Search Kiwi.com flights in AI chats
- Command: `claude mcp add kiwi-com-flights --transport http https://mcp.kiwi.com`

**[Melon](https://tech.kakaoent.com/ai/using-melon-mcp-server-en/)**
- Browse music charts & your personalized music picks
- Command: `claude mcp add melon --transport http https://mcp.melon.com/mcp/`

**[Monday](https://developer.monday.com/apps/docs/mondaycom-mcp-integration)**
- Manage projects, boards, and workflows in monday.com
- Command: `claude mcp add --transport http monday https://mcp.monday.com/mcp`

**[NetSuite](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/article_7200233106.html)**
- Connect Claude to NetSuite data for analysis & insights
- Requires user-specific URL. [Get your URL here](https://system.netsuite.com/mcp/mcpinfo.nl).

**[Notion](https://developers.notion.com/docs/mcp)**
- Connect your Notion workspace to search, update, and power workflows across tools
- Command: `claude mcp add --transport http notion https://mcp.notion.com/mcp`

**[PayPal](https://developer.paypal.com/tools/mcp-server/)**
- Access PayPal payments platform
- Command: `claude mcp add --transport http paypal https://mcp.paypal.com/mcp`

**[Ramp](https://docs.ramp.com/developer-api/v1/guides/ramp-mcp-remote)**
- Search, access, and analyze your Ramp financial data
- Command: `claude mcp add --transport http ramp https://ramp-mcp-remote.ramp.com/mcp`

**[Snowflake](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)**
- Retrieve both structured and unstructured data
- Requires user-specific URL. [Get your URL here](https://docs.snowflake.com/en/user-guide/admin-account-identifier#label-account-name-find).

**[Square](https://developer.squareup.com/docs/mcp)**
- Search and manage transaction, merchant, and payment data
- Command: `claude mcp add --transport sse square https://mcp.squareup.com/sse`

**[Stripe](https://docs.stripe.com/mcp)**
- Payment processing and financial infrastructure tools
- Command: `claude mcp add --transport http stripe https://mcp.stripe.com`

**[Trivago](https://mcp.trivago.com/docs)**
- Find your ideal hotel at the best price
- Command: `claude mcp add --transport http trivago https://mcp.trivago.com/mcp`

**[Vercel](https://vercel.com/docs/mcp/vercel-mcp)**
- Analyze, debug, and manage projects and deployments
- Command: `claude mcp add --transport http vercel https://mcp.vercel.com`

**[Visier](https://docs.visier.com/developer/agents/mcp/mcp-server.htm)**
- Find people, productivity and business impact insights
- Requires user-specific URL. [Get your URL here](https://docs.visier.com/developer/agents/mcp/mcp-server-set-up.htm).

**[Workato](https://docs.workato.com/en/mcp/mcp-cloud.html)**
- Automate workflows and connect your business apps
- Requires user-specific URL. [Get your URL here](https://app.workato.com/ai_hub/mcp).

**[Zapier](https://mcp.zapier.app/home)**
- Automate workflows across thousands of apps via conversation
- Requires user-specific URL. [Get your URL here](https://mcp.zapier.com/mcp/servers?client=claudeai).

**[ZoomInfo](https://docs.zoominfo.com/docs/zi-api-mcp-overview/)**
- Enrich contacts & accounts with GTM intelligence
- Command: `claude mcp add --transport http zoominfo https://mcp.zoominfo.com/mcp`

**[Jam](https://jam.dev/docs/debug-a-jam/mcp)**
- Record screen and collect automatic context for issues
- Command: `claude mcp add --transport http jam https://mcp.jam.dev/mcp`

**[Sentry](https://docs.sentry.io/product/sentry-mcp/)**
- Search, query, and debug errors intelligently
- Command: `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp`

**[Stytch](https://stytch.com/docs/workspace-management/stytch-mcp)**
- Manage your Stytch Project
- Command: `claude mcp add stytch --transport http https://mcp.stytch.dev/mcp`

**[Coupler.io](https://help.coupler.io/article/592-coupler-local-mcp-server)**
- Access business data from hundreds of sources
- Command: `claude mcp add --transport http coupler https://mcp.coupler.io/mcp`

**[Airtable](https://github.com/domdomegg/airtable-mcp-server)**
- Read and write Airtable databases

**[Honeycomb](https://docs.honeycomb.io/troubleshoot/product-lifecycle/beta/mcp/)**
- Query and explore observability data and SLOs
- Command: `claude mcp add honeycomb --transport http https://mcp.honeycomb.io/mcp`

**[Synapse.org](https://github.com/susheel/synapse-mcp?tab=readme-ov-file#synapse-mcp-server)**
- Search and metadata tools for Synapse scientific data
- Command: `claude mcp add synapse-org --transport http https://mcp.synapse.org/mcp`

**[Chronograph](https://lp-help.chronograph.pe/article/735-chronograph-mcp)**
- Interact with your Chronograph data directly in Claude
- Command: `claude mcp add --transport http chronograph https://ai.chronograph.pe/mcp`

**[Hex](https://learn.hex.tech/docs/administration/mcp-server)**
- Answer questions with the Hex agent
- Requires user-specific URL. [Get your URL here](https://learn.hex.tech/docs/administration/mcp-server#connect-to-claude).

**Need a specific integration?** [Find hundreds more MCP servers on GitHub](https://github.com/modelcontextprotocol/servers), or build your own using the [MCP SDK](https://modelcontextprotocol.io/quickstart/server).

## Installing MCP servers

MCP servers can be configured in three different ways depending on your needs:

### Option 1: Add a remote HTTP server

HTTP servers are the recommended option for connecting to remote MCP servers. This is the most widely supported transport for cloud-based services.

```bash
# Basic syntax
claude mcp add --transport http <name> <url>

# Real example: Connect to Notion
claude mcp add --transport http notion https://mcp.notion.com/mcp

# Example with Bearer token
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer your-token"
```

### Option 2: Add a remote SSE server

> **Note:** The SSE (Server-Sent Events) transport is deprecated. Use HTTP servers instead, where available.

```bash
# Basic syntax
claude mcp add --transport sse <name> <url>

# Real example: Connect to Asana
claude mcp add --transport sse asana https://mcp.asana.com/sse

# Example with authentication header
claude mcp add --transport sse private-api https://api.company.com/sse \
  --header "X-API-Key: your-key-here"
```

### Option 3: Add a local stdio server

Stdio servers run as local processes on your machine. They're ideal for tools that need direct system access or custom scripts.

```bash
# Basic syntax
claude mcp add --transport stdio <name> <command> [args...]

# Real example: Add Airtable server
claude mcp add --transport stdio airtable --env AIRTABLE_API_KEY=YOUR_KEY \
  -- npx -y airtable-mcp-server
```

**Understanding the "—" parameter:**
The `--` (double dash) separates Claude's own CLI flags from the command and arguments that get passed to the MCP server. Everything before `--` are options for Claude (like `--env`, `--scope`), and everything after `--` is the actual command to run the MCP server.

For example:
- `claude mcp add --transport stdio myserver -- npx server` → runs `npx server`
- `claude mcp add --transport stdio myserver --env KEY=value -- python server.py --port 8080` → runs `python server.py --port 8080` with `KEY=value` in environment

This prevents conflicts between Claude's flags and the server's flags.

### Managing your servers

Once configured, you can manage your MCP servers with these commands:

```bash
# List all configured servers
claude mcp list

# Get details for a specific server
claude mcp get github

# Remove a server
claude mcp remove github

# (within Claude Code) Check server status
/mcp
```

**Tips:**
- Use the `--scope` flag to specify where the configuration is stored:
  - `local` (default): Available only to you in the current project (was called `project` in older versions)
  - `project`: Shared with everyone in the project via `.mcp.json` file
  - `user`: Available to you across all projects (was called `global` in older versions)
- Set environment variables with `--env` flags (for example, `--env KEY=value`)
- Configure MCP server startup timeout using the MCP_TIMEOUT environment variable (for example, `MCP_TIMEOUT=10000 claude` sets a 10-second timeout)
- Claude Code will display a warning when MCP tool output exceeds 10,000 tokens. To increase this limit, set the `MAX_MCP_OUTPUT_TOKENS` environment variable (for example, `MAX_MCP_OUTPUT_TOKENS=50000`)
- Use `/mcp` to authenticate with remote servers that require OAuth 2.0 authentication

**Windows Users**: On native Windows (not WSL), local MCP servers that use `npx` require the `cmd /c` wrapper to ensure proper execution.

```bash
# This creates command="cmd" which Windows can execute
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package
```

Without the `cmd /c` wrapper, you'll encounter "Connection closed" errors because Windows cannot directly execute `npx`.

### Plugin-provided MCP servers

[Plugins](https://code.claude.com/docs/en/plugins) can bundle MCP servers, automatically providing tools and integrations when the plugin is enabled. Plugin MCP servers work identically to user-configured servers.

**How plugin MCP servers work:**
- Plugins define MCP servers in `.mcp.json` at the plugin root or inline in `plugin.json`
- When a plugin is enabled, its MCP servers start automatically
- Plugin MCP tools appear alongside manually configured MCP tools
- Plugin servers are managed through plugin installation (not `/mcp` commands)

**Example plugin MCP configuration:**

In `.mcp.json` at plugin root:

```json
{
  "database-tools": {
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
    "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
    "env": {
      "DB_URL": "${DB_URL}"
    }
  }
}
```

Or inline in `plugin.json`:

```json
{
  "name": "my-plugin",
  "mcpServers": {
    "plugin-api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/api-server",
      "args": ["--port", "8080"]
    }
  }
}
```

**Plugin MCP features:**
- **Automatic lifecycle**: Servers start when plugin enables, but you must restart Claude Code to apply MCP server changes (enabling or disabling)
- **Environment variables**: Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- **User environment access**: Access to same environment variables as manually configured servers
- **Multiple transport types**: Support stdio, SSE, and HTTP transports (transport support may vary by server)

**Viewing plugin MCP servers:**

```bash
# Within Claude Code, see all MCP servers including plugin ones
/mcp
```

Plugin servers appear in the list with indicators showing they come from plugins.

**Benefits of plugin MCP servers:**
- **Bundled distribution**: Tools and servers packaged together
- **Automatic setup**: No manual MCP configuration needed
- **Team consistency**: Everyone gets the same tools when plugin is installed

## MCP installation scopes

MCP servers can be configured at three different scope levels, each serving distinct purposes for managing server accessibility and sharing. Understanding these scopes helps you determine the best way to configure servers for your specific needs.

### Local scope

Local-scoped servers represent the default configuration level and are stored in `~/.claude.json` under your project's path. These servers remain private to you and are only accessible when working within the current project directory. This scope is ideal for personal development servers, experimental configurations, or servers containing sensitive credentials that shouldn't be shared.

```bash
# Add a local-scoped server (default)
claude mcp add --transport http stripe https://mcp.stripe.com

# Explicitly specify local scope
claude mcp add --transport http stripe --scope local https://mcp.stripe.com
```

### Project scope

Project-scoped servers enable team collaboration by storing configurations in a `.mcp.json` file at your project's root directory. This file is designed to be checked into version control, ensuring all team members have access to the same MCP tools and services. When you add a project-scoped server, Claude Code automatically creates or updates this file with the appropriate configuration structure.

```bash
# Add a project-scoped server
claude mcp add --transport http paypal --scope project https://mcp.paypal.com/mcp
```

The resulting `.mcp.json` file follows a standardized format:

```json
{
  "mcpServers": {
    "shared-server": {
      "command": "/path/to/server",
      "args": [],
      "env": {}
    }
  }
}
```

For security reasons, Claude Code prompts for approval before using project-scoped servers from `.mcp.json` files. If you need to reset these approval choices, use the `claude mcp reset-project-choices` command.

### User scope

User-scoped servers are stored in `~/.claude.json` and provide cross-project accessibility, making them available across all projects on your machine while remaining private to your user account. This scope works well for personal utility servers, development tools, or services you frequently use across different projects.

```bash
# Add a user server
claude mcp add --transport http hubspot --scope user https://mcp.hubspot.com/anthropic
```

### Choosing the right scope

Select your scope based on:
- **Local scope**: Personal servers, experimental configurations, or sensitive credentials specific to one project
- **Project scope**: Team-shared servers, project-specific tools, or services required for collaboration
- **User scope**: Personal utilities needed across multiple projects, development tools, or frequently used services

**Where are MCP servers stored?**
- **User and local scope**: `~/.claude.json` (in the `mcpServers` field or under project paths)
- **Project scope**: `.mcp.json` in your project root (checked into source control)
- **Enterprise managed**: `managed-mcp.json` in system directories (see Enterprise MCP configuration)

### Scope hierarchy and precedence

MCP server configurations follow a clear precedence hierarchy. When servers with the same name exist at multiple scopes, the system resolves conflicts by prioritizing local-scoped servers first, followed by project-scoped servers, and finally user-scoped servers. This design ensures that personal configurations can override shared ones when needed.

### Environment variable expansion in `.mcp.json`

Claude Code supports environment variable expansion in `.mcp.json` files, allowing teams to share configurations while maintaining flexibility for machine-specific paths and sensitive values like API keys.

**Supported syntax:**
- `${VAR}` - Expands to the value of environment variable `VAR`
- `${VAR:-default}` - Expands to `VAR` if set, otherwise uses `default`

**Expansion locations:**
Environment variables can be expanded in:
- `command` - The server executable path
- `args` - Command-line arguments
- `env` - Environment variables passed to the server
- `url` - For HTTP server types
- `headers` - For HTTP server authentication

**Example with variable expansion:**

```json
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}
```

If a required environment variable is not set and has no default value, Claude Code will fail to parse the config.

## Practical examples

### Example: Monitor errors with Sentry

```bash
# 1. Add the Sentry MCP server
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp

# 2. Use /mcp to authenticate with your Sentry account
> /mcp

# 3. Debug production issues
> "What are the most common errors in the last 24 hours?"
> "Show me the stack trace for error ID abc123"
> "Which deployment introduced these new errors?"
```

### Example: Connect to GitHub for code reviews

```bash
# 1. Add the GitHub MCP server
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# 2. In Claude Code, authenticate if needed
> /mcp
# Select "Authenticate" for GitHub

# 3. Now you can ask Claude to work with GitHub
> "Review PR #456 and suggest improvements"
> "Create a new issue for the bug we just found"
> "Show me all open PRs assigned to me"
```

### Example: Query your PostgreSQL database

```bash
# 1. Add the database server with your connection string
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \
  --dsn "postgresql://readonly:pass@prod.db.com:5432/analytics"

# 2. Query your database naturally
> "What's our total revenue this month?"
> "Show me the schema for the orders table"
> "Find customers who haven't made a purchase in 90 days"
```

## Authenticate with remote MCP servers

Many cloud-based MCP servers require authentication. Claude Code supports OAuth 2.0 for secure connections.

### Step 1: Add the server that requires authentication

For example:

```bash
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```

### Step 2: Use the /mcp command within Claude Code

In Claude code, use the command:

```
> /mcp
```

Then follow the steps in your browser to login.

**Tips:**
- Authentication tokens are stored securely and refreshed automatically
- Use "Clear authentication" in the `/mcp` menu to revoke access
- If your browser doesn't open automatically, copy the provided URL
- OAuth authentication works with HTTP servers

## Add MCP servers from JSON configuration

If you have a JSON configuration for an MCP server, you can add it directly:

### Step 1: Add an MCP server from JSON

```bash
# Basic syntax
claude mcp add-json <name> '<json>'

# Example: Adding an HTTP server with JSON configuration
claude mcp add-json weather-api '{"type":"http","url":"https://api.weather.com/mcp","headers":{"Authorization":"Bearer token"}}'

# Example: Adding a stdio server with JSON configuration
claude mcp add-json local-weather '{"type":"stdio","command":"/path/to/weather-cli","args":["--api-key","abc123"],"env":{"CACHE_DIR":"/tmp"}}'
```

### Step 2: Verify the server was added

```bash
claude mcp get weather-api
```

**Tips:**
- Make sure the JSON is properly escaped in your shell
- The JSON must conform to the MCP server configuration schema
- You can use `--scope user` to add the server to your user configuration instead of the project-specific one

## Import MCP servers from Claude Desktop

If you've already configured MCP servers in Claude Desktop, you can import them:

### Step 1: Import servers from Claude Desktop

```bash
# Basic syntax
claude mcp add-from-claude-desktop
```

### Step 2: Select which servers to import

After running the command, you'll see an interactive dialog that allows you to select which servers you want to import.

### Step 3: Verify the servers were imported

```bash
claude mcp list
```

**Tips:**
- This feature only works on macOS and Windows Subsystem for Linux (WSL)
- It reads the Claude Desktop configuration file from its standard location on those platforms
- Use the `--scope user` flag to add servers to your user configuration
- Imported servers will have the same names as in Claude Desktop
- If servers with the same names already exist, they will get a numerical suffix (for example, `server_1`)

## Use Claude Code as an MCP server

You can use Claude Code itself as an MCP server that other applications can connect to:

```bash
# Start Claude as a stdio MCP server
claude mcp serve
```

You can use this in Claude Desktop by adding this configuration to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "claude-code": {
      "type": "stdio",
      "command": "claude",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

**Configuring the executable path**: The `command` field must reference the Claude Code executable. If the `claude` command is not in your system's PATH, you'll need to specify the full path to the executable.

To find the full path:

```bash
which claude
```

Then use the full path in your configuration:

```json
{
  "mcpServers": {
    "claude-code": {
      "type": "stdio",
      "command": "/full/path/to/claude",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

Without the correct executable path, you'll encounter errors like `spawn claude ENOENT`.

**Tips:**
- The server provides access to Claude's tools like View, Edit, LS, etc.
- In Claude Desktop, try asking Claude to read files in a directory, make edits, and more.
- Note that this MCP server is only exposing Claude Code's tools to your MCP client, so your own client is responsible for implementing user confirmation for individual tool calls.

## MCP output limits and warnings

When MCP tools produce large outputs, Claude Code helps manage the token usage to prevent overwhelming your conversation context:

- **Output warning threshold**: Claude Code displays a warning when any MCP tool output exceeds 10,000 tokens
- **Configurable limit**: You can adjust the maximum allowed MCP output tokens using the `MAX_MCP_OUTPUT_TOKENS` environment variable
- **Default limit**: The default maximum is 25,000 tokens

To increase the limit for tools that produce large outputs:

```bash
# Set a higher limit for MCP tool outputs
export MAX_MCP_OUTPUT_TOKENS=50000
claude
```

This is particularly useful when working with MCP servers that:
- Query large datasets or databases
- Generate detailed reports or documentation
- Process extensive log files or debugging information

If you frequently encounter output warnings with specific MCP servers, consider increasing the limit or configuring the server to paginate or filter its responses.

## Use MCP resources

MCP servers can expose resources that you can reference using @ mentions, similar to how you reference files.

### Reference MCP resources

**Step 1: List available resources**

Type `@` in your prompt to see available resources from all connected MCP servers. Resources appear alongside files in the autocomplete menu.

**Step 2: Reference a specific resource**

Use the format `@server:protocol://resource/path` to reference a resource:

```
> Can you analyze @github:issue://123 and suggest a fix?
```

```
> Please review the API documentation at @docs:file://api/authentication
```

**Step 3: Multiple resource references**

You can reference multiple resources in a single prompt:

```
> Compare @postgres:schema://users with @docs:file://database/user-model
```

**Tips:**
- Resources are automatically fetched and included as attachments when referenced
- Resource paths are fuzzy-searchable in the @ mention autocomplete
- Claude Code automatically provides tools to list and read MCP resources when servers support them
- Resources can contain any type of content that the MCP server provides (text, JSON, structured data, etc.)

## Use MCP prompts as slash commands

MCP servers can expose prompts that become available as slash commands in Claude Code.

### Execute MCP prompts

**Step 1: Discover available prompts**

Type `/` to see all available commands, including those from MCP servers. MCP prompts appear with the format `/mcp__servername__promptname`.

**Step 2: Execute a prompt without arguments**

```
> /mcp__github__list_prs
```

**Step 3: Execute a prompt with arguments**

Many prompts accept arguments. Pass them space-separated after the command:

```
> /mcp__github__pr_review 456
```

```
> /mcp__jira__create_issue "Bug in login flow" high
```

**Tips:**
- MCP prompts are dynamically discovered from connected servers
- Arguments are parsed based on the prompt's defined parameters
- Prompt results are injected directly into the conversation
- Server and prompt names are normalized (spaces become underscores)

## Enterprise MCP configuration

For organizations that need centralized control over MCP servers, Claude Code supports enterprise-managed MCP configurations. This allows IT administrators to:

- **Control which MCP servers employees can access**: Deploy a standardized set of approved MCP servers across the organization
- **Prevent unauthorized MCP servers**: Optionally restrict users from adding their own MCP servers
- **Disable MCP entirely**: Remove MCP functionality completely if needed

### Setting up enterprise MCP configuration

System administrators can deploy an enterprise MCP configuration file alongside the managed settings file. See [settings files](https://code.claude.com/docs/en/settings#settings-files) for the `managed-mcp.json` file locations on each platform.

The `managed-mcp.json` file uses the same format as a standard `.mcp.json` file:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp"
    },
    "company-internal": {
      "type": "stdio",
      "command": "/usr/local/bin/company-mcp-server",
      "args": ["--config", "/etc/company/mcp-config.json"],
      "env": {
        "COMPANY_API_URL": "https://internal.company.com"
      }
    }
  }
}
```

### Restricting MCP servers with allowlists and denylists

In addition to providing enterprise-managed servers, administrators can control which MCP servers users are allowed to configure using `allowedMcpServers` and `deniedMcpServers` in the managed settings file.

#### Restriction options

Each entry in the allowlist or denylist can restrict servers in two ways:

1. **By server name** (`serverName`): Matches the configured name of the server
2. **By command** (`serverCommand`): Matches the exact command and arguments used to start stdio servers

**Important**: Each entry must have **either** `serverName` **or** `serverCommand`, not both.

#### Example configuration

```json
{
  "allowedMcpServers": [
    // Allow by server name
    { "serverName": "github" },
    { "serverName": "sentry" },

    // Allow by exact command (for stdio servers)
    { "serverCommand": ["npx", "-y", "@modelcontextprotocol/server-filesystem"] },
    { "serverCommand": ["python", "/usr/local/bin/approved-server.py"] }
  ],
  "deniedMcpServers": [
    // Block by server name
    { "serverName": "dangerous-server" },

    // Block by exact command (for stdio servers)
    { "serverCommand": ["npx", "-y", "unapproved-package"] }
  ]
}
```

#### How command-based restrictions work

**Exact matching:**
- Command arrays must match **exactly** - both the command and all arguments in the correct order
- Example: `["npx", "-y", "server"]` will NOT match `["npx", "server"]` or `["npx", "-y", "server", "--flag"]`

**Stdio server behavior:**
- When the allowlist contains **any** `serverCommand` entries, stdio servers **must** match one of those commands
- Stdio servers cannot pass by name alone when command restrictions are present
- This ensures administrators can enforce which commands are allowed to run

**Non-stdio server behavior:**
- Remote servers (HTTP, SSE, WebSocket) always match by name only
- Command restrictions do not apply to remote servers

**Example: Command-only allowlist**

```json
{
  "allowedMcpServers": [
    { "serverCommand": ["npx", "-y", "approved-package"] }
  ]
}
```

**Result:**
- Stdio server with `["npx", "-y", "approved-package"]`: ✅ Allowed (matches command)
- Stdio server with `["node", "server.js"]`: ❌ Blocked (doesn't match command)
- HTTP server named "my-api": ❌ Blocked (no name entries to match)

**Example: Mixed name and command allowlist**

```json
{
  "allowedMcpServers": [
    { "serverName": "github" },
    { "serverCommand": ["npx", "-y", "approved-package"] }
  ]
}
```

**Result:**
- Stdio server named "local-tool" with `["npx", "-y", "approved-package"]`: ✅ Allowed (matches command)
- Stdio server named "local-tool" with `["node", "server.js"]`: ❌ Blocked (command entries exist but doesn't match)
- Stdio server named "github" with `["node", "server.js"]`: ❌ Blocked (stdio servers must match commands when command entries exist)
- HTTP server named "github": ✅ Allowed (matches name)
- HTTP server named "other-api": ❌ Blocked (name doesn't match)

**Example: Name-only allowlist**

```json
{
  "allowedMcpServers": [
    { "serverName": "github" },
    { "serverName": "internal-tool" }
  ]
}
```

**Result:**
- Stdio server named "github" with any command: ✅ Allowed (no command restrictions)
- Stdio server named "internal-tool" with any command: ✅ Allowed (no command restrictions)
- HTTP server named "github": ✅ Allowed (matches name)
- Any server named "other": ❌ Blocked (name doesn't match)

#### Allowlist behavior (`allowedMcpServers`)

- `undefined` (default): No restrictions - users can configure any MCP server
- Empty array `[]`: Complete lockdown - users cannot configure any MCP servers
- List of entries: Users can only configure servers that match by name or command

#### Denylist behavior (`deniedMcpServers`)

- `undefined` (default): No servers are blocked
- Empty array `[]`: No servers are blocked
- List of entries: Specified servers are explicitly blocked across all scopes

#### Important notes

- These restrictions apply to all scopes: user, project, local, and even enterprise servers from `managed-mcp.json`
- **Denylist takes absolute precedence**: If a server matches a denylist entry (by name or command), it will be blocked even if it's on the allowlist
- Name-based and command-based restrictions work together: a server passes if it matches **either** a name entry **or** a command entry (unless blocked by denylist)

**Enterprise configuration precedence**: The enterprise MCP configuration has the highest precedence and cannot be overridden by user, local, or project configurations.
