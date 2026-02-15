# 🛠️ Archestra Setup Guide

## Step 1: Start the Stack

```bash
cd archestra
docker-compose up -d --build
```

Wait ~60 seconds for Archestra to initialize, then open **http://localhost:3000**.

This starts 3 services:
- **Archestra Platform** → http://localhost:3000 (UI) + http://localhost:9000 (MCP Gateway)
- **Onboarding MCP Server** → http://localhost:8000 (SSE transport for Archestra)
- **Onboarding REST API** → http://localhost:8080 (for the dashboard)

## Step 2: Register the Custom MCP Server

1. Go to **MCP Registry** in the Archestra sidebar
2. Click **Add New** → **Remote MCP Server**
3. Fill in:
   - **Name**: `onboarding-mcp`
   - **URL**: `http://host.docker.internal:8000/sse`
4. Click **Save**

> **Why Remote?** The MCP server runs as a separate container with SSE transport. Using `host.docker.internal` lets Archestra's container reach the MCP server on your host machine.

## Step 3: Install Playwright MCP

1. In **MCP Registry**, click **Add New** → **Search Public**
2. Search for `microsoft__playwright-mcp`
3. Click **Install**

## Step 4: Create the Onboarding Agent

1. Go to **Agents** in the sidebar
2. Click **Create Agent**
3. Copy the system prompt from [`agent-config.yaml`](./agent-config.yaml)
4. In the **Tools** section:
   - Enable **all tools** from `onboarding-mcp`
   - Enable `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type` from `microsoft__playwright-mcp`
5. Under **Security**, enable **Dual LLM** mode
6. Click **Save**

## Step 5: Add an LLM Provider

1. Go to **Settings** → **LLM API Keys**
2. Add your preferred provider:
   - **OpenAI** (GPT-4o recommended)
   - **Anthropic** (Claude 3.5 Sonnet)
   - **Google** (Gemini 2.0)
   - **Free**: [Cerebras](https://cerebras.ai/) or local [Ollama](https://ollama.com/)

## Step 6: Try It!

1. Go to **Chat** and select the **Onboarding Agent**
2. Try these prompts:

```
Onboard Sarah Chen as a Software Engineer on the Platform team.
Her email is sarah.chen@acme-corp.com and her GitHub username is sarahchen.
```

```
What's the onboarding checklist for a Product Designer?
```

```
Show me the status of all employees being onboarded.
```

## Step 7: Set Up MCP Gateway (Optional)

To use the agent from Claude Desktop or other MCP clients:

1. Go to **MCP Gateways** → **Create New**
2. Add the **Onboarding Agent** as a sub-agent
3. Copy the MCP configuration
4. Add to your MCP client

🎉 **You're all set!**
