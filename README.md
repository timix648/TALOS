# TALOS — The Self-Healing DevOps Species

<div align="center">

![TALOS Banner](https://img.shields.io/badge/TALOS-Self--Healing%20Agent-cyan?style=for-the-badge&logo=github)
[![Vetrox Hackathon](https://img.shields.io/badge/Vetrox-Agentic%203.0-purple?style=for-the-badge)](https://vetrox.ai)
[![Gemini 3](https://img.shields.io/badge/Powered%20by-Gemini%203-blue?style=for-the-badge&logo=google)](https://ai.google.dev)
[![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)](https://nextjs.org)

**Autonomous CI/CD Repair • Zero Configuration • Real-Time Observability**

[Install on GitHub](https://github.com/apps/talos-healer) • [Live Dashboard](#-neural-dashboard) • [Documentation](#-architecture)

</div>

---

## Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [The Cognitive Core](#-the-cognitive-core)
- [Security](#-security)
- [Neural Dashboard](#-neural-dashboard)
- [Deployment](#-deployment)
- [Tech Stack](#-tech-stack)
- [Contributing](#-contributing)
- [License](#-license)

---

## The Problem

Every developer knows the pain: you push code, grab a coffee, and return to a **red CI badge**. The error log is cryptic. The stack trace points to a file you didn't touch. You spend 30 minutes deciphering what went wrong.

**Traditional CI/CD tools are blind.** They execute scripts and report exit codes—but they don't *understand* the errors they produce.

### The Cost of Broken Builds

| Impact | Reality |
|--------|---------|
| **Developer Time** | Average 23 minutes per failed build investigation |
| **Lost Productivity** | $100K+ annually for mid-size teams |
| **Context Switching** | Breaks flow state, delays feature delivery |
| **Repeated Failures** | Same error patterns occur across projects |

---

## The Solution

**TALOS** (The Autonomous Lifecycle Operations System) is not a pipeline. It's a **digital organism** that:

1. **Observes** — Watches your GitHub repos via webhooks for build failures
2. **Reasons** — Uses Gemini 3 to analyze logs, build dependency graphs, and identify the *root cause*
3. **Heals** — Generates fixes in an isolated sandbox, verifies them, and opens a Pull Request
4. **Shows** — Streams its "thought process" to a real-time dashboard, so you see exactly what it's doing

> *"TALOS doesn't just tell you what's broken—it fixes it for you."*

### Before TALOS
```
Build Failed → Read Logs → Debug → Fix → Push → Wait → Hope
```

### After TALOS
```
Build Failed → TALOS Fixes It → Review PR → Merge
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Patient Zero Detection** | Distinguishes between where the error *manifests* vs. where the bug *originates* using dependency graph analysis |
| **Verification Loop** | Tests fixes in isolated E2B Firecracker microVMs before proposing them |
| **Real-Time Neural Dashboard** | Watch the agent think and act via Server-Sent Events (SSE) streaming |
| **Multi-Attempt Reasoning** | If a fix fails verification, TALOS learns from the error and tries again (up to 3 attempts) |
| **Zero-Config Security** | GitHub App model with fine-grained permissions, HMAC webhook verification |
| **Polyglot Support** | Node.js, Python, TypeScript, Rust—auto-detected, no setup needed |
| **Duplicate PR Prevention** | Automatically detects existing TALOS PRs to avoid spam |
| **Allow Retry** | Dashboard button to bypass duplicate detection when you want a fresh fix attempt |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TALOS ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   GitHub                      FastAPI Backend            Frontend       │
│   ───────                     ──────────────            ─────────       │
│                                                                         │
│   ┌─────────┐     Webhook     ┌─────────────┐          ┌──────────┐   │
│   │workflow │────────────────▶│  Nervous    │   SSE    │  Neural  │   │
│   │  _run   │                 │  System     │─────────▶│Dashboard │   │
│   │ failure │                 └──────┬──────┘          └──────────┘   │
│   └─────────┘                        │                                 │
│                                      ▼                                 │
│   ┌─────────┐              ┌─────────────────┐                        │
│   │Supabase │◀─────────────│   Event Bus     │                        │
│   │   DB    │  Persistence │   (Redis)       │                        │
│   └─────────┘              └────────┬────────┘                        │
│                                     │                                  │
│                                     ▼                                  │
│                            ┌─────────────────┐                        │
│                            │    Gemini 3     │ ◀── ReAct Loop         │
│                            │    (Brain)      │     Chain of Thought   │
│                            │  Flash + Pro    │     Dual-Model System  │
│                            └────────┬────────┘                        │
│                                     │                                  │
│                                     ▼                                  │
│                            ┌─────────────────┐                        │
│                            │  E2B Sandbox    │ ◀── Firecracker μVM   │
│                            │    (Hands)      │     ~150ms boot time   │
│                            └────────┬────────┘                        │
│                                     │                                  │
│                                     ▼                                  │
│   ┌─────────┐              ┌─────────────────┐                        │
│   │  Pull   │◀─────────────│    GitHub       │                        │
│   │ Request │   PR Created │      API        │                        │
│   └─────────┘              └─────────────────┘                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### The OODA Loop

TALOS implements the **OODA (Observe-Orient-Decide-Act)** cognitive loop, a decision-making framework used by fighter pilots:

| Phase | Component | Action |
|-------|-----------|--------|
| **Observe** | Webhook Handler | Receives `workflow_run` failure events from GitHub |
| **Orient** | Repomix + Perception | Assembles code context, normalizes logs, extracts stack trace DNA |
| **Decide** | Gemini 3 + ReAct | Reasons about root cause, generates targeted fix |
| **Act** | E2B Sandbox | Applies fix, runs verification, creates PR |

### The Healing Pipeline

```
┌──────────┐   ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌────────┐   ┌──────────┐
│ 1.Detect │──▶│2.Analyze│──▶│3.Diagnose│──▶│ 4. Fix  │──▶│5.Verify│──▶│ 6.Deploy │
│          │   │         │   │          │   │         │   │        │   │          │
│  Webhook │   │  Logs   │   │  Gemini  │   │  Patch  │   │Sandbox │   │   PR     │
│ Received │   │ Parsed  │   │ Reasons  │   │ Applied │   │ Tests  │   │ Created  │
└──────────┘   └─────────┘   └──────────┘   └─────────┘   └────────┘   └──────────┘
```

---

## Quick Start

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Redis** (for real-time event streaming)
- **GitHub Account** (to install the app)
- **API Keys**: Gemini, E2B, Supabase

### 1. Install TALOS on GitHub

Click the button to install the GitHub App on your repositories:

[![Install TALOS](https://img.shields.io/badge/Install-TALOS%20on%20GitHub-cyan?style=for-the-badge&logo=github)](https://github.com/apps/talos-healer)

### 2. Clone the Repository

```bash
git clone https://github.com/timix648/TALOS.git
cd TALOS
```

### 3. Set Up the Backend

```bash
# Create virtual environment
cd api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .

# Create .env file (see Configuration section)
cp .env.example .env
# Edit .env with your keys

# Start Redis (in a separate terminal)
redis-server

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Set Up the Frontend

```bash
cd web
npm install

# Create .env.local file
cp .env.example .env.local
# Edit .env.local with your settings

# Start the development server
npm run dev
```

### 5. Expose Webhook (Development)

For GitHub to send webhooks to your local machine:

```bash
# Using Cloudflared (recommended)
cloudflared tunnel --url http://localhost:8000

# Or using ngrok
ngrok http 8000
```

Update your GitHub App webhook URL to the tunnel URL.

### 6. Trigger a Failure

Push a bug to a watched repo. TALOS will:
1. Detect the failure via webhook
2. Clone the repo into an isolated sandbox
3. Analyze the error with Gemini 3
4. Generate and verify a fix
5. Open a Pull Request

---

## 🔧 Configuration

### Environment Variables (API)

Create `api/.env`:

```env
# --- API CONFIG ---
ENV=development
PORT=8000

# --- GITHUB APP SECRETS ---
GITHUB_APP_ID=123456
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_PRIVATE_KEY_PATH=/path/to/your-private-key.pem

# --- GEMINI BRAIN ---
# Comma-separated keys for automatic rotation on rate limits
GEMINI_API_KEYS=key1,key2,key3

# --- E2B SANDBOX ---
E2B_API_KEY=your_e2b_key

# --- REDIS (Required for SSE) ---
REDIS_URL=redis://localhost:6379

# --- SUPABASE MEMORY ---
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
```

### Environment Variables (Web)

Create `web/.env.local`:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# GitHub OAuth (for dashboard login)
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# GitHub App URL
NEXT_PUBLIC_GITHUB_APP_URL=https://github.com/apps/your-app-name
```

### Getting Your API Keys

| Service | How to Get |
|---------|------------|
| **GitHub App** | [Create a GitHub App](https://github.com/settings/apps/new) with `workflow_run`, `pull_request`, `contents` permissions |
| **Gemini API** | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| **E2B** | [E2B Dashboard](https://e2b.dev/dashboard) |
| **Supabase** | [Supabase Dashboard](https://supabase.com/dashboard) |
| **Redis** | Local: `brew install redis` / `apt install redis-server` |

---

## API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check - returns TALOS status and capabilities |
| `/webhook` | POST | GitHub webhook receiver (HMAC verified) |
| `/debug/auth` | GET | Test GitHub App authentication |

### Event Streaming

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events/stream/{run_id}` | GET | SSE stream for real-time updates |
| `/events/history/{run_id}` | GET | Get past events for a completed run |

### Healing Runs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/runs/` | GET | List recent healing runs (paginated) |
| `/runs/{run_id}` | GET | Get details for a specific run |
| `/runs/{run_id}` | DELETE | Delete a run from history |
| `/runs/{run_id}/allow-retry` | POST | Allow TALOS to create a new fix PR |
| `/runs/stats` | GET | Aggregate statistics |
| `/runs/latest/active` | GET | Get the currently running heal (if any) |

### Installation Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/installations/{id}/repos` | GET | List repos for an installation |
| `/installations/{id}/repos/{repo}/watch` | POST | Enable TALOS for a repo |
| `/installations/{id}/repos/{repo}/unwatch` | POST | Disable TALOS for a repo |

### Statistics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stats` | GET | Global healing statistics |

---

## The Cognitive Core

### Dual-Model Architecture

TALOS uses Gemini 3 model for different cognitive tasks:

| Model | Role | Use Case |
|-------|------|----------|
| **Gemini 3 Flash** | Fast Responder | Log analysis, quick fixes, syntax errors |
| **Gemini 3 FLASH** | Deep Thinker | Complex logic bugs, multi-file fixes |

### Error Classification

TALOS automatically classifies errors for targeted fixes:

| Category | Examples | Fix Strategy |
|----------|----------|--------------|
| **Syntax Errors** | Missing brackets, typos, malformed imports | Direct pattern-based fix |
| **Type Errors** | Wrong types, null references | Type coercion, null checks |
| **Logic Bugs** | Off-by-one, wrong conditionals | Semantic analysis, test-driven |
| **Config Issues** | Missing deps, wrong scripts | Package.json/requirements fix |
| **Import Errors** | Module not found, circular deps | Dependency graph analysis |

### The Patient Zero Algorithm

Not all errors originate where they crash. TALOS uses triangulation:

```
                    Stack Trace
                         │
                         ▼
              ┌─────────────────────┐
              │  Where did it CRASH │  ← "Crash Site"
              │   (symptom file)    │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌───────────┐  ┌───────────┐  ┌───────────┐
   │ Dependency│  │  Git Diff │  │  Import   │
   │   Graph   │  │  (recent) │  │  Analysis │
   └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
         │              │              │
         └──────────────┼──────────────┘
                        ▼
              ┌─────────────────────┐
              │  PATIENT ZERO       │  ← Actual bug location
              │   (root cause)      │
              └─────────────────────┘
```

**Logic:**
1. Parse stack trace to find "crash site"
2. Build dependency graph (who imports what)
3. Correlate with `git diff` (what changed recently)
4. Triangulate: If crash file wasn't modified, but a caller was → **Caller is Patient Zero**

### Log Normalization

Raw CI logs are noisy. TALOS cleans them:

```
Raw Log                           Normalized Log
─────────────────────────────────────────────────────────
[0m[91mError: Cannot find...   →   Error: Cannot find module 'xyz'
npm WARN deprecated...             (stripped)
████████████░░░░░░░ 60%            (stripped)
[2026-01-29T12:30:45Z] FAIL       →   FAIL tests/app.test.js
```

---

## Security

TALOS is designed with security-first principles:

| Feature | Implementation |
|---------|----------------|
| **HMAC Webhook Verification** | Constant-time signature comparison prevents timing attacks |
| **Short-Lived Tokens** | GitHub Installation Access Tokens expire in 1 hour |
| **Isolated Execution** | E2B Firecracker microVMs boot in ~150ms, fully sandboxed |
| **Minimal Permissions** | Only requests necessary scopes, repo-specific access |
| **No Credential Storage** | Tokens generated on-demand, never persisted |
| **Private Key Protection** | `.gitignore` blocks all `.pem` and `.env` files |

### GitHub App Permissions

| Scope | Access | Why |
|-------|--------|-----|
| `actions` | Read | Fetch workflow run logs |
| `contents` | Write | Create branches, push fixes |
| `pull_requests` | Write | Open PRs with fixes |
| `metadata` | Read | Repository information |

---

## Neural Dashboard

The real-time dashboard streams TALOS's thought process:

### Event Color Coding

| Color | Phase | Events |
|-------|-------|--------|
| 🔵 **Blue** | Initialization | `mission_start`, `cloning` |
| 🟡 **Yellow** | Perception | `scouting`, `reading_code` |
| 🟢 **Cyan** | Cognition | `thinking`, `analyzing`, `diagnosing` |
| 🟢 **Green** | Action | `applying_fix`, `verifying`, `creating_pr`, `success` |
| 🔴 **Red** | Error | `failure`, `error_log` |
| 🟠 **Orange** | Retry | `retry` |
| 🟣 **Purple** | Meta | `thought_stream`, `mission_end` |
| 🩷 **Pink** | Code | `code_diff` |

### Dashboard Features

- **Stats Overview**: Protected repos, success rate, total heals
- **Run History**: Click any past run to replay its timeline
- **Live Indicator**: Pulses when a run is in progress
- **Auto-Scroll**: Follows live runs, pauses for historical viewing
- **Expandable Events**: Click to see metadata and code diffs
- **↩Allow Retry Button**: Request a new fix attempt

---

## Deployment

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

**Services:**
| Service | Port | Description |
|---------|------|-------------|
| `talos-api` | 8000 | FastAPI backend |
| `talos-web` | 3000 | Next.js dashboard |
| `talos-redis` | 6379 | Event bus (internal) |

### Supabase Setup

Run the schema in your Supabase SQL Editor:

```sql
-- Located in: api/db/schema.sql
-- Creates:
--   • installations (GitHub App installs)
--   • watched_repos (monitored repositories)
--   • healing_runs (repair history)
--   • healing_events (timeline events)
```

### Production Checklist

- [ ] Set `ENV=production` in `.env`
- [ ] Configure proper CORS origins (not `*`)
- [ ] Use managed Redis (e.g., Upstash, Redis Cloud)
- [ ] Set up SSL/TLS termination
- [ ] Enable Supabase Row Level Security
- [ ] Rotate API keys regularly
- [ ] Set up monitoring/alerting

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | Async Python web framework |
| **Python 3.11+** | Runtime with modern typing |
| **Pydantic** | Data validation and settings |
| **Redis** | Pub/Sub for SSE streaming |
| **Supabase** | PostgreSQL database |
| **httpx** | Async HTTP client |

### AI/ML
| Technology | Purpose |
|------------|---------|
| **Gemini 3 Flash** | Fast reasoning, log analysis,Deep reasoning, complex fixes |
| **E2B** | Firecracker microVM sandboxes |
| **Repomix** | Codebase context assembly |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 15** | React framework with App Router |
| **React 19** | UI components |
| **Tailwind CSS** | Styling |
| **Framer Motion** | Animations |
| **Lucide Icons** | Icon library |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Cloudflared** | Secure tunneling |
| **GitHub Apps** | OAuth + Webhooks |

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/TALOS.git

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# Run tests
cd api && pytest
cd web && npm test
```

---

| Criteria | How TALOS Excels |
|----------|------------------|
| **The Code** | Clean monorepo architecture, strict typing, modular design |
| **The Demo** | Real-time Neural Dashboard with SSE streaming |
| **The Philosophy** | "Species" that lives in the ecosystem, not a tool you invoke |
| **Gemini Integration** | Dual-model system, ReAct loop, Chain of Thought reasoning |
| **Security** | GitHub Apps, HMAC verification, isolated sandboxes |
| **Innovation** | Patient Zero algorithm, Visual Regression (planned) |

### What Makes TALOS Different

| Traditional Tools | TALOS |
|-------------------|-------|
| Report errors | **Fix** errors |
| Exit codes | **Understanding** |
| After-the-fact | **Real-time** |
| Manual intervention | **Autonomous** |
| Black box | **Transparent** (Neural Dashboard) |

<div align="center">

### TALOS — Because your CI/CD pipeline should heal itself.

**[Install Now](https://github.com/apps/talos-healer)** • **[View Demo](#-neural-dashboard)** • **[Star This Repo](https://github.com/timix648/TALOS)**

</div>
