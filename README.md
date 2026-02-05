# 🧬 TALOS — The Self-Healing DevOps Species

<div align="center">

![TALOS Banner](https://img.shields.io/badge/TALOS-Self--Healing%20Agent-cyan?style=for-the-badge&logo=github)
[![Vetrox Hackathon](https://img.shields.io/badge/Vetrox-Agentic%203.0-purple?style=for-the-badge)](https://vetrox.ai)
[![Gemini 3](https://img.shields.io/badge/Powered%20by-Gemini%203-blue?style=for-the-badge&logo=google)](https://ai.google.dev)

**Autonomous CI/CD Repair • Zero Configuration • Real-Time Observability**

[Install on GitHub](https://github.com/apps/talos-healer) • [Live Dashboard](#) • [Documentation](#architecture)

</div>

---

## 🎯 The Problem

Every developer knows the pain: you push code, grab a coffee, and return to a **red CI badge**. The error log is cryptic. The stack trace points to a file you didn't touch. You spend 30 minutes deciphering what went wrong.

**Traditional CI/CD tools are blind.** They execute scripts and report exit codes—but they don't *understand* the errors they produce.

## 💡 The Solution

**TALOS** is not a pipeline. It's a **digital organism** that:

1. **🔭 Observes** — Watches your GitHub repos via webhooks for build failures
2. **🧠 Reasons** — Uses Gemini 3 to analyze logs, build dependency graphs, and identify the *root cause*
3. **🔧 Heals** — Generates fixes in an isolated sandbox, verifies them, and opens a Pull Request
4. **👁️ Shows** — Streams its "thought process" to a real-time dashboard, so you see exactly what it's doing

> *"TALOS doesn't just tell you what's broken—it fixes it for you."*

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🎯 Patient Zero Detection** | Distinguishes between where the error *manifests* vs. where the bug *originates* |
| **🔄 Verification Loop** | Tests fixes in isolated E2B sandboxes before proposing them |
| **📡 Real-Time Neural Dashboard** | Watch the agent think and act via SSE streaming |
| **🤖 Multi-Attempt Reasoning** | If a fix fails, TALOS learns from the error and tries again |
| **🔐 Zero-Config Security** | GitHub App model with fine-grained permissions |
| **🌐 Polyglot Support** | Node.js, Python, Rust—auto-detected, no setup needed |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TALOS ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   GitHub                    FastAPI Backend           Frontend      │
│   ───────                   ──────────────           ─────────      │
│                                                                     │
│   ┌─────────┐    Webhook    ┌─────────────┐         ┌──────────┐  │
│   │ workflow│──────────────▶│  Nervous    │   SSE   │  Neural  │  │
│   │ _run    │               │  System     │────────▶│Dashboard │  │
│   │ failure │               └──────┬──────┘         └──────────┘  │
│   └─────────┘                      │                              │
│                                    ▼                              │
│                            ┌─────────────┐                        │
│                            │   Gemini 3  │ ◀── ReAct Loop         │
│                            │   (Brain)   │     Chain of Thought   │
│                            └──────┬──────┘                        │
│                                    │                              │
│                                    ▼                              │
│                            ┌─────────────┐                        │
│                            │ E2B Sandbox │ ◀── Isolated Execution │
│                            │  (Hands)    │     Red/Green/Refactor │
│                            └──────┬──────┘                        │
│                                    │                              │
│                                    ▼                              │
│   ┌─────────┐              ┌─────────────┐                        │
│   │  Pull   │◀─────────────│   GitHub    │                        │
│   │ Request │   PR Created │    API      │                        │
│   └─────────┘              └─────────────┘                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 🧬 The OODA Loop

TALOS implements the **OODA (Observe-Orient-Decide-Act)** cognitive loop:

| Phase | Component | Action |
|-------|-----------|--------|
| **Observe** | Webhook Handler | Receives `workflow_run` failure events |
| **Orient** | Repomix + Perception | Assembles code context, normalizes logs, extracts stack trace DNA |
| **Decide** | Gemini 3 + ReAct | Reasons about root cause, generates fix |
| **Act** | E2B Sandbox | Applies fix, runs tests, creates PR |

---

## 🚀 Quick Start

### 1. Install TALOS on GitHub

Click the button to install the GitHub App on your repositories:

[![Install TALOS](https://img.shields.io/badge/Install-TALOS%20on%20GitHub-cyan?style=for-the-badge&logo=github)](https://github.com/apps/talos-healer)

### 2. Run the Backend

```bash
# Start Redis first (required for SSE streaming)
redis-server

# In a new terminal:
cd api
# Create .env file with your keys (see Configuration section)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Run the Frontend

```bash
cd web
npm install
npm run dev
```

### 4. Trigger a Failure

Push a bug to a watched repo. TALOS will:
1. Detect the failure via webhook
2. Clone the repo into an isolated sandbox
3. Analyze the error with Gemini 3
4. Generate and verify a fix
5. Open a Pull Request

---

## 🔧 Configuration

### Environment Variables

```env
# GitHub App
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PATH=talos-private-key.pem
GITHUB_WEBHOOK_SECRET=your_secret

# Gemini API (comma-separated for rotation)
GEMINI_API_KEYS=your_key_1,your_key_2,your_key_3

# E2B Sandbox
E2B_API_KEY=your_e2b_key

# Redis (for SSE streaming - must be running)
REDIS_URL=redis://localhost:6379

# Supabase (for persistence)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_key
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook` | POST | GitHub webhook receiver |
| `/events/stream/{run_id}` | GET | SSE stream for real-time updates |
| `/events/history/{run_id}` | GET | Get past events for a run |
| `/runs/` | GET | List recent healing runs |
| `/runs/{run_id}` | GET | Get details for a specific run |
| `/runs/stats` | GET | Aggregate statistics |

---

## 🧠 The Cognitive Core

### Error Classification

TALOS classifies errors into categories for targeted fixes:

- **Syntax Errors** — Typos, missing brackets, malformed imports
- **Logic Bugs** — Off-by-one errors, wrong conditionals
- **Configuration Issues** — Missing dependencies, wrong scripts
- **Dependency Conflicts** — Version mismatches
- **React Purity Violations** — Impure functions during render

### Patient Zero Algorithm

1. Parse stack trace to find "crash site"
2. Build dependency graph (who imports what)
3. Correlate with `git diff` (what changed recently)
4. Triangulate: Stack Trace + Dependency Graph + Git History = Patient Zero

---

## 🛡️ Security

| Feature | Implementation |
|---------|----------------|
| **HMAC Webhook Verification** | Constant-time signature comparison |
| **Short-Lived Tokens** | GitHub Installation Access Tokens (1hr expiry) |
| **Isolated Execution** | E2B Firecracker microVMs (~150ms boot) |
| **Minimal Permissions** | Only requested scopes, repo-specific access |
| **No Credential Storage** | Tokens generated on-demand, never stored |

---

## 👁️ Visual Regression (Killer Feature)

TALOS can **see** your UI, not just read your logs. Using Playwright + Gemini's multimodal vision:

```
1. Capture → Playwright takes screenshot of failed UI
2. Analyze → Gemini Vision identifies visual issues
3. Fix → CSS/Layout fixes are generated
4. Verify → Screenshot comparison confirms the fix
```

**Detected Issues:**
- Overlapping elements
- Z-index issues (buttons hidden behind modals)
- Layout breaks
- Color contrast problems
- Missing/broken images

---

## 🐳 Docker Deployment

```bash
# Quick start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

**Services:**
- `talos-api` — FastAPI backend (port 8000)
- `talos-web` — Next.js dashboard (port 3000)
- `talos-redis` — Event bus (port 6379)

---

## 📊 Supabase Setup

Run the schema in your Supabase SQL editor:

```bash
# The schema is in api/db/schema.sql
# Creates: installations, watched_repos, healing_runs, healing_events
```

---

## 🎨 Neural Dashboard

The real-time dashboard shows:

- **🔵 Blue** — Perception (cloning, reading code)
- **🟡 Yellow** — Cognition (thinking, analyzing)
- **🟢 Green** — Action (applying fix, verification passed)
- **🔴 Red** — Failure (error, retry needed)
- **🟣 Purple** — Thought stream (Gemini's reasoning)

Each event is timestamped and expandable, with metadata and code diffs.

---

## 📊 Hackathon Submission

### Why TALOS Wins

| Criteria | How TALOS Excels |
|----------|------------------|
| **The Code** | Monorepo architecture, strict typing, modular design |
| **The Demo** | Real-time Neural Dashboard with SSE streaming |
| **The Philosophy** | "Species" that lives in the ecosystem, not a tool you invoke |
| **Gemini Integration** | ReAct loop, Chain of Thought, multimodal vision ready |
| **Security** | GitHub Apps, HMAC, isolated sandboxes |

### Tech Stack

- **Backend:** FastAPI, Python 3.11+, Pydantic
- **AI:** Gemini 3 Flash + Pro, Chain of Thought
- **Sandbox:** E2B (Firecracker microVMs)
- **Frontend:** Next.js 15, React 19, Framer Motion
- **Database:** Supabase (PostgreSQL)
- **Messaging:** Redis (Pub/Sub for SSE)

---

## 📄 License

MIT License - Built for the Vetrox Agentic 3.0 Hackathon

---

<div align="center">

**🧬 TALOS — Because your CI/CD pipeline should heal itself.**

</div>
