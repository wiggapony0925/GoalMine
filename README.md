# 🏆 GoalMine — Multi-Agent AI Betting Intelligence Platform

<p align="center">
  <strong>Professional-grade sports betting intelligence delivered via WhatsApp</strong><br>
  <em>5 AI agents • 20-second analysis • $0.038 per match • Production-ready</em>
</p>

---

## Overview

**GoalMine** is a production-grade, autonomous betting intelligence platform built for the **2026 FIFA World Cup**. It orchestrates a multi-agent AI swarm to analyze matches from every angle — logistics, tactics, market odds, narrative sentiment, and quantitative modeling — then synthesizes everything into high-conviction betting recommendations.

**Key Numbers:**

| Metric | Value |
|---|---|
| Analysis Speed | 20 seconds (parallel agents) |
| Cost per Match | $0.038 |
| Agents | 5 specialized AI + 1 quant engine |
| Delivery | WhatsApp Cloud API |
| Uptime | 99.9% (cloud-hosted) |

---

## Architecture

```
User (WhatsApp) → app.py Webhook → Gatekeeper Agent
                                        │
                          ┌──────────────┴──────────────┐
                          ▼                             ▼
                   Button-Strict Mode          Conversational Mode
                          │                             │
                          └──────────────┬──────────────┘
                                         ▼
                              Orchestrator (Swarm)
                                         │
                    ┌───────┬────────┬────┴────┬────────┐
                    ▼       ▼        ▼         ▼        ▼
               Logistics  Tactics  Market  Narrative  Quant
                    │       │        │         │        │
                    └───────┴────────┴────┬────┴────────┘
                                         ▼
                               God View Builder → Supabase
                                         ▼
                              Bet Generator (Big Daddy)
                                         ▼
                               WhatsApp Response
```

---

## Project Structure

```
GoalMine/
├── app.py                              # Flask webhook entry point & scheduler
│
├── core/                               # Core infrastructure
│   ├── initializer/
│   │   ├── llm.py                      # OpenAI API wrapper (model routing, retries)
│   │   ├── whatsapp.py                 # WhatsApp Cloud API client
│   │   └── database.py                 # Supabase interface
│   ├── config.py                       # Settings manager (settings.json)
│   ├── log.py                          # Centralized logging
│   ├── utils.py                        # Shared utilities & HTTP helpers
│   └── generate_bets.py               # Bet generation synthesizer (Big Daddy)
│
├── agents/                             # AI Agent Swarm (parallel execution)
│   ├── gatekeeper/                     # Intent classification (gpt-4o-mini)
│   ├── logistics/                      # Travel fatigue & altitude (gpt-4o)
│   │   └── api/open_meteo.py           # Weather data
│   ├── tactics/                        # Tactical matchup analysis (gpt-4o)
│   │   └── api/sportmonks.py           # Team stats & form
│   ├── market/                         # Odds analysis & value detection (gpt-4o)
│   │   └── api/the_odds_api.py         # Live odds aggregator
│   ├── narrative/                      # Sentiment & morale (gpt-4o-mini)
│   │   └── api/                        # News, Reddit, web scraping
│   └── quant/                          # Dixon-Coles + Kelly Criterion (Python/NumPy)
│
├── services/                           # Orchestration & conversation flows
│   ├── orchestrator.py                 # Swarm coordinator (parallel agent execution)
│   ├── data_scout.py                   # Live schedule sync (Football-Data API)
│   └── interface/
│       ├── message_handler.py          # Button-based UI engine
│       ├── ui_manager.py               # WhatsApp interactive message builder
│       └── automatic/                  # Scheduled background services
│           ├── morning_brief.py        # Daily 5AM briefing
│           ├── kickoff_alerts.py       # Pre-match alerts (60 min before)
│           └── market_monitor.py       # Sharp line movement detection
│
├── prompts/                            # AI System Prompts (centralized)
│   ├── system_prompts.py              # All agent prompts with {variable} injection
│   └── messages_prompts.py            # UI text responses
│
├── data/                               # Static data & utilities
│   ├── schedule.json                   # 2026 World Cup calendar
│   ├── venues.json                     # Stadium metadata
│   ├── bet_types.json                  # Betting market catalog
│   └── scripts/
│       ├── data.py                     # Data loaders
│       └── godview_builder.py          # God View JSON constructor
│
├── test/                               # Test suites
│   ├── unit/                           # Unit tests
│   └── integration/                    # Integration tests
│
├── settings.json                       # Central configuration
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Container config
└── docker-compose.yml                  # Multi-service orchestration
```

---

## The Agent Swarm

Each agent is a domain expert with its own LLM configuration and data sources. All agents run **in parallel** via `asyncio.gather` for speed.

| Agent | Model | Temp | Domain | Key Output |
|---|---|---|---|---|
| **Gatekeeper** | gpt-4o-mini | 0.1 | Intent routing | BETTING / SCHEDULE |
| **Logistics** | gpt-4o | 0.3 | Physical factors | Fatigue score (0-10) |
| **Tactics** | gpt-4o | 0.3 | Style matchups | Adjusted xG |
| **Market** | gpt-4o | 0.3 | Odds analysis | Edge %, trap alerts |
| **Narrative** | gpt-4o-mini | 0.5 | Sentiment/morale | Morale score (0-10) |
| **Quant** | Pure Python | — | Probability math | Kelly-optimized stakes |

---

## The God View System

The **God View** is a comprehensive JSON intelligence matrix — the single source of truth that powers bet generation and follow-up queries.

### Schema (v3.0)

```json
{
  "match": "Argentina vs Brazil",
  "home_team": "Argentina",
  "away_team": "Brazil",
  "timestamp": "2026-06-15T18:30:00",

  "logistics": {
    "fatigue_score": 7,
    "distance_km": 2847,
    "risk": "Altitude",
    "stamina_impact": "Moderate",
    "summary": "High-altitude stress at 2,240m"
  },

  "tactics": {
    "team_a_xg": 2.15,
    "team_b_xg": 1.05,
    "matchup_styles": "High Press vs Counter-Attack",
    "key_battle": "Midfield control",
    "game_script": "One-sided possession siege"
  },

  "market": {
    "best_odds": { "home": 1.85, "draw": 3.40, "away": 4.20 },
    "market_math": {
      "vig": 4.2,
      "is_arbitrage": false,
      "fair_probs": { "home": 58.7, "draw": 24.1, "away": 17.2 }
    },
    "value_score": "A-",
    "edge_percentage": 12.5,
    "trap_alert": "None",
    "sharp_signal": "None",
    "best_bet": "Argentina"
  },

  "narrative": {
    "home": {
      "team": "Argentina",
      "score": 8.5,
      "morale": "Boost",
      "adjustment": 0.15,
      "headline": "Messi returns to World Cup stage"
    },
    "away": {
      "team": "Brazil",
      "score": 4.2,
      "morale": "Drop",
      "adjustment": -0.10,
      "headline": "Neymar injury concerns"
    }
  },

  "quant": {
    "probabilities": { "team_a_win": 58.7, "draw": 24.1, "team_b_win": 17.2 },
    "top_plays": [
      {
        "selection": "Argentina Win",
        "odds": 1.85,
        "bookie": "DraftKings",
        "confidence_pct": 58.7,
        "edge": 12.5,
        "stake": 15
      }
    ]
  },

  "final_xg": {
    "home": 2.30,
    "away": 0.81,
    "total": 3.11,
    "differential": 1.49
  },

  "convergence": {
    "dominant_direction": "home",
    "agreeing_agents": 4,
    "total_signals": 4,
    "conviction_level": "Elite"
  },

  "meta": {
    "schema_version": "3.0",
    "cache_key": "argentina_vs_brazil",
    "generated_at": "2026-06-15T18:30:00",
    "agents_executed": {
      "logistics": "OK",
      "tactics": "OK",
      "market": "OK",
      "narrative_home": "OK",
      "narrative_away": "OK"
    },
    "data_quality": {
      "agent_scores": {
        "logistics": 1.0,
        "tactics": 1.0,
        "market": 0.8,
        "narrative": 1.0
      },
      "overall_completeness": 0.95,
      "grade": "A"
    },
    "xg_adjustment_chain": {
      "base_tactics": { "home": 2.15, "away": 1.05 },
      "narrative_adj": { "home": 0.15, "away": -0.10 },
      "logistics_penalty": 0.85,
      "final": { "home": 2.30, "away": 0.81 }
    }
  }
}
```

**Storage:** `sessions.god_view` (Supabase JSONB)  
**TTL:** 3 hours (configurable)

---

## Automated Services

Three background services run on APScheduler to keep users informed:

| Service | Schedule | Purpose |
|---|---|---|
| **Morning Brief** | Daily at 5:00 AM | Sends today's match count, featured fixture, and full fixture list |
| **Kickoff Alerts** | Every 15 minutes | Alerts users 60 minutes before any match kicks off |
| **Market Monitor** | Every 30 minutes | Detects significant odds movements (>15% threshold) and sends sharp money alerts |

All scheduling parameters are configurable in `settings.json` under `GLOBAL_APP_CONFIG.scheduling`.

---

## Prompt Engineering

All system prompts use `{variable}` injection for dynamic context. This makes agents:

- **Context-aware** — each prompt receives match-specific data at runtime
- **Precise** — variables like `{home_team}`, `{base_a:.2f}`, `{intelligence}` eliminate ambiguity
- **Maintainable** — prompts are centralized in `prompts/system_prompts.py`

Every prompt includes:

- **Role identity** with clear mission
- **Chain-of-Thought** reasoning steps
- **Few-shot examples** for consistent output
- **Strict JSON output format** with constraints
- **Negative constraints** (what NOT to do)

---

## Setup & Deployment

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
WHATSAPP_TOKEN=EAAxxxxxxx
PHONE_NUMBER_ID=12345
VERIFY_TOKEN=your_webhook_verify_token
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...

# Optional API Keys
SPORTMONKS_API_KEY=xxx
THE_ODDS_API_KEY=xxx
FOOTBALL_DATA_API_TOKEN=xxx
```

### Install & Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PYTHONPATH:$(pwd)
python app.py
```

Server runs on `http://localhost:8000`

### Docker

```bash
docker build -t goalmine-ai .
docker run -p 8000:8000 --env-file .env goalmine-ai
```

#### Automated Production Builds

This repository is configured with GitHub Actions to automatically build and publish the Docker image to the **GitHub Container Registry (GHCR)** on every push to the `main` branch.

- **Registry:** `ghcr.io/wiggapony0925/goalmine`
- **Latest Tag:** `:main`
- **Release Tags:** `:vX.X.X`

To pull the latest production image:

```bash
docker pull ghcr.io/wiggapony0925/goalmine:main
```

### Database (Supabase)

```sql
CREATE TABLE sessions (
  phone TEXT PRIMARY KEY,
  god_view JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_sessions_created_at ON public.sessions (created_at);

CREATE TABLE system_storage (
  key TEXT PRIMARY KEY,
  value JSONB,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE public.system_storage ENABLE ROW LEVEL SECURITY;

CREATE TABLE predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_phone TEXT NOT NULL,
  match_id TEXT NOT NULL,
  predicted_outcome TEXT NOT NULL,
  odds NUMERIC,
  confidence TEXT,
  stake NUMERIC,
  model_version TEXT DEFAULT 'v2.1_dixon_coles',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_predictions_user_phone FOREIGN KEY (user_phone)
    REFERENCES public.sessions (phone) ON DELETE CASCADE
);
CREATE INDEX idx_predictions_user_phone ON public.predictions (user_phone);
CREATE INDEX idx_predictions_created_at ON public.predictions (created_at);
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
```

---

## Testing

```bash
# Unit tests
python -m pytest test/unit/ -v

# All tests
python test/run_all_tests.py

# With coverage
python test/run_all_tests.py --coverage
```

---

## Design Principles

1. **Separation of Concerns** — Infrastructure (`llm.py`) vs business logic (`generate_bets.py`) vs domain expertise (agents)
2. **Single Source of Truth** — God View persisted in database for follow-up queries
3. **Hybrid Intelligence** — LLMs for subjective reasoning + Python for deterministic math
4. **Parallel Execution** — All agents run simultaneously (`asyncio.gather`) — 4x speed improvement
5. **Graceful Degradation** — Individual agent failures don't crash the system
6. **Cost Optimization** — gpt-4o-mini for simple tasks, gpt-4o only for complex reasoning

---

## Security

- All API keys stored in `.env` (never committed)
- WhatsApp webhook signature verification
- Supabase Row Level Security on sensitive tables
- GDPR/CCPA data deletion endpoint (`/data-deletion`)
- Rate limiting built into API clients
- Docker containerization for isolation

---

**Developer:** Jeffrey Fernandez  
**Version:** 3.0 (God View v3 + Prompt Engineering v2)  
**Status:** 🟢 Production Ready  
**License:** Proprietary
