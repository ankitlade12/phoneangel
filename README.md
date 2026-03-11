# PhoneAngel — AI Phone Call Agent & Coach for Autistic Adults

> **An accessibility tool that helps autistic adults prepare for, get coached through, and delegate phone calls — powered by DigitalOcean Gradient AI.**

Built for the [DigitalOcean Gradient AI Hackathon](https://digitalocean.devpost.com/) (March 2026).

---

## The Problem

Phone calls are one of the biggest barriers in autistic adults' daily lives. The unpredictability of conversations, implied social meaning, real-time processing demands, and sensory overload of voice-only communication cause severe anxiety. As a result, many autistic adults:

- Let medical conditions go untreated because they can't call to schedule appointments
- Accumulate debt from bills they couldn't call to dispute
- Lose housing from maintenance issues they couldn't report
- Miss job opportunities because phone interviews are overwhelming

**No product exists that addresses this.** PhoneAngel is the first accessibility-focused phone call tool for neurodivergent adults.

---

## Three Modes

### Mode 1: Call Prep (Before the Call)
Tell PhoneAngel what you need. It generates a **visual conversation flowchart**, a **word-for-word opening script**, every **likely question** with pre-filled answers, and **anxiety notes** explaining what's normal.

### Mode 2: Live Coach (During the Call)
Put the call on speaker. PhoneAngel listens via real-time speech-to-text and displays on-screen coaching prompts — auto-filled answers, plain-English translations of confusing phrases, and reassurance during hold/silence.

### Mode 3: AI Proxy (The Call Is Made For You)
The AI makes the call entirely via Twilio. You set objectives and decision boundaries. You receive a transcript, summary, and any decisions needing confirmation.

---

## DigitalOcean Gradient AI Usage

| Feature | How PhoneAngel Uses It |
|---|---|
| **Serverless Inference** | Chat completions power all three agents |
| **Knowledge Base (RAG)** | Phone scripts, common patterns, phrase decodings |
| **Agent Platform** | Managed agents with custom instructions per mode |
| **Guardrails** | Prevents sharing sensitive user data |
| **Function Calling** | Calendar, profile, and history lookups |
| **Agent Routing** | Routes between prep, coach, and proxy agents |

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI/LLM | DigitalOcean Gradient AI (Inference + Agents + KB) |
| Backend | Python 3.12, FastAPI, SQLModel, WebSockets |
| Frontend | React 18, TypeScript, TailwindCSS, D3.js |
| Speech-to-Text | Deepgram (real-time streaming) |
| Telephony | Twilio (outbound calls) |
| Package Mgmt | uv |
| Deployment | DigitalOcean App Platform |

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/phoneangel.git
cd phoneangel

# Install with uv
uv sync

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run backend
uv run uvicorn phoneangel.app:app --reload --port 8000

# Run frontend (separate terminal)
cd frontend && npm install && npm run dev
```

API docs at `http://localhost:8000/docs`

---

## Project Structure

```
phoneangel/
├── src/phoneangel/
│   ├── app.py                    # FastAPI entry point
│   ├── config.py                 # Environment config
│   ├── agents/
│   │   ├── gradient_client.py    # Gradient AI SDK wrapper
│   │   ├── prep_agent.py         # Mode 1: Call preparation
│   │   ├── coach_agent.py        # Mode 2: Live coaching
│   │   └── proxy_agent.py        # Mode 3: AI proxy caller
│   ├── api/routes.py             # REST + WebSocket endpoints
│   ├── models/
│   │   ├── database.py           # Async SQLModel engine
│   │   └── schemas.py            # All data models
│   └── knowledge_base/
│       └── phone_scripts.md      # RAG content for Gradient KB
├── frontend/                      # React app
├── tests/                         # Test suite
├── pyproject.toml                 # uv project config
├── .env.example                   # Env template
└── LICENSE                        # MIT
```

---

## 9-Day Sprint Plan

| Day | Date | Focus | Deliverable |
|-----|------|-------|-------------|
| 1-2 | Mar 10-11 | Foundation | Backend scaffold, DB, Gradient AI client, deploy to DO |
| 3-4 | Mar 12-13 | Mode 1: Prep | Flowchart generation, React visualizer, profile auto-fill |
| 5-6 | Mar 14-15 | Mode 2: Coach | Deepgram STT, WebSocket pipeline, coaching overlay UI |
| 7 | Mar 16 | Mode 3: Proxy | Twilio integration, proxy agent, transcript viewer |
| 8 | Mar 17 | Polish | E2E testing, accessibility UI, error handling, history |
| 9 | Mar 18 | Ship | Demo video, Devpost submission, final deploy |

---

## License

MIT — see [LICENSE](LICENSE).
