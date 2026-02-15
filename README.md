# 🤖 OnboardAI — AI Employee Onboarding Agent

> **Hackathon Project** — Built with [Archestra](https://github.com/archestra-ai/archestra), the open-source MCP-native secure AI platform.

An intelligent agent that automates employee onboarding across **GitHub**, **Slack**, **Google Drive**, and **internal wikis** — all orchestrated through Archestra's secure MCP platform with built-in governance, cost monitoring, and prompt injection protection.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🚀 **One-Command Onboarding** | Tell the agent to onboard someone, it handles everything |
| 🔗 **GitHub Integration** | Org invites, repo access, dev setup issues |
| 💬 **Slack Integration** | Welcome DMs, channel invites, team introductions |
| 📁 **Google Drive** | Share handbooks, create personal folders |
| 🌐 **Wiki Browsing** | Playwright MCP navigates internal documentation |
| 📊 **Live Dashboard** | Beautiful dark-theme UI tracks onboarding progress |
| 🔒 **Secure by Design** | Archestra's Dual LLM prevents prompt injection |
| 💰 **Cost Controlled** | Built-in token limits and cost optimization |
| 🎯 **Role-Based Workflows** | Different checklists for Engineering, Design, etc. |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Archestra Platform                  │
│  ┌───────────────┐  ┌────────────────────────────┐  │
│  │  Chat UI /    │  │   Security Engine          │  │
│  │  Agent Builder│  │   (Dual LLM, Dynamic Tools)│  │
│  └──────┬────────┘  └────────────────────────────┘  │
│         │                                            │
│  ┌──────▼────────────────────────────────────────┐  │
│  │         MCP Gateway & Orchestrator             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────┐  │  │
│  │  │ Onboard  │ │Playwright│ │  Cost/Limits   │  │  │
│  │  │ MCP Srv  │ │ MCP Srv  │ │  Monitoring    │  │  │
│  │  └──────────┘ └──────────┘ └───────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└──────────┬──────────────────────────────────────────┘
           │
    ┌──────▼──────┐
    │  Dashboard  │
    │  (Web UI)   │
    └─────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- [Docker](https://www.docker.com/) installed and running
- An LLM API key (OpenAI, Anthropic, Google, or free [Cerebras](https://cerebras.ai/))

### 1. Clone & Start

```bash
git clone https://github.com/your-username/onboard-agent.git
cd onboard-agent

# Start Archestra + Onboarding MCP Server
cd archestra
docker-compose up -d
```

### 2. Set Up the Agent

Follow the detailed [Setup Guide](archestra/setup-guide.md) to:
1. Register the custom MCP server in Archestra
2. Install Playwright MCP
3. Create the Onboarding Agent
4. Add your LLM API key

### 3. Open the Dashboard

Open `dashboard/index.html` in your browser for the onboarding tracker UI.

### 4. Start Onboarding!

Go to Archestra Chat UI at **http://localhost:3000** and try:

```
Onboard Sarah Chen as a Software Engineer on the Platform team.
Her email is sarah.chen@acme-corp.com and GitHub is sarahchen.
```

---

## 📁 Project Structure

```
onboard-agent/
├── mcp-server/                 # Custom MCP Server (Python)
│   ├── server.py               # FastMCP server with 8 tools
│   ├── models.py               # Pydantic data models
│   ├── store.py                # Data persistence layer
│   ├── requirements.txt        # Python dependencies
│   └── integrations/
│       ├── github_integration.py
│       ├── slack_integration.py
│       └── gdrive_integration.py
├── workflows/                  # Role-based onboarding templates
│   ├── general.json
│   ├── engineering.json
│   └── design.json
├── archestra/                  # Archestra Platform Config
│   ├── agent-config.yaml       # Agent definition & system prompt
│   ├── docker-compose.yml      # Full local stack
│   └── setup-guide.md          # Step-by-step setup instructions
├── dashboard/                  # Onboarding Dashboard (Web UI)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── Dockerfile                  # Container image for MCP server
├── .env.example                # Environment variables template
└── README.md
```

---

## 🛠️ MCP Tools

| Tool | Description |
|------|-------------|
| `onboard_new_hire` | Full onboarding orchestration |
| `github_invite_to_org` | GitHub org invite + repo access |
| `slack_send_welcome` | Slack DM + channel invites |
| `gdrive_share_docs` | Share Drive documents & folders |
| `check_onboarding_status` | Real-time progress check |
| `get_onboarding_checklist` | Role-specific task list |
| `complete_task` | Mark a task as done |
| `list_all_employees` | List all onboarding employees |

---

## 🔒 Security with Archestra

This project leverages Archestra's enterprise security features:

- **Dual LLM** — Tool responses are processed by a separate security model, preventing prompt injections from tool outputs
- **Dynamic Tools** — Tools are only exposed when needed, reducing the attack surface
- **Cost Limits** — Per-conversation token and tool call limits prevent runaway costs
- **Observability** — Full tracing of every tool call for audit

---

## 🔧 Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | No | GitHub PAT for real org invites |
| `SLACK_BOT_TOKEN` | No | Slack bot token for real messages |
| `GDRIVE_SERVICE_ACCOUNT_KEY` | No | Google service account JSON path |

> **Note:** All integrations work in **mock mode** without tokens — perfect for demos!

---

## 🤝 Built With

- [Archestra](https://archestra.ai) — MCP-native secure AI platform
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP server framework
- [Playwright MCP](https://github.com/microsoft/playwright-mcp) — Browser automation
- [Pydantic](https://pydantic.dev) — Data validation
- [Starlette](https://www.starlette.io) — REST API for dashboard

---

## 📄 License

MIT License — Built for a hackathon, use it however you like! 🎉
