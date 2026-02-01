# GoalMine: Autonomous World Cup 2026 Prediction Engine

**GoalMine** is a production-grade, event-driven hybrid intelligence system designed for professional-grade betting insights for the 2026 FIFA World Cup.

It operates on a sophisticated architecture that merges **deterministic mathematical modeling** (Quant Engine) with **semantic AI reasoning** (Agent Swarm). The system delivers high-confidence, real-time strategic advice directly via WhatsApp, acting as an automated "Human-in-the-Loop" advisor for sports syndicates.

---

## 1. System Architecture

The core of GoalMine is an **Agent Swarm** orchestration pattern. It is designed to be **Cloud-Native**, with strictly enforced persistence and modular intelligence.

### 1.1 The Intelligence Flow

```mermaid
graph TD
    subgraph Sources
        USER([User Interface (WhatsApp)])
        SCHED[("schedule.json (Calendar)")]
        BETS[("bet_types.json (Market Taxonomy)")]
        RDT_CFG[("reddit_config.json")]
    end

    subgraph Processing Layer
        WEBHOOK[Flask Gateway]
        CONV[Conversation Handler]
        DB[(Supabase Cloud Database)]
    end
    
    subgraph Agent Swarm
        TAC[Tactics Agent] <--> MONKS[SportMonks V3 (Lineups/Coaches)]
        LOG[Logistics Agent] <--> METEO[Open-Meteo API (Weather/Alt)]
        MKT[Market Agent] <--> ODDS[The Odds API (Live Lines)]
        NAR[Narrative Agent] <--> NEWS[Google News] & REDDIT[No-Key Scraper]
    end

    subgraph Synthesis
        QUANT[Quant Engine (NumPy Matrix)]
        ORCH[Orchestrator Service]
        MODELS[("model_config.json (LLM Routing)")]
    end

    USER -->|Message| WEBHOOK
    WEBHOOK --> CONV
    CONV <--> DB
    
    CONV -->|Trigger Analysis| ORCH
    ORCH --> MODELS
    
    ORCH -->|Trigger| TAC
    ORCH -->|Trigger| LOG
    ORCH -->|Trigger| MKT
    ORCH -->|Trigger| NAR
    
    TAC --> QUANT
    LOG --> QUANT
    MKT --> QUANT
    NAR --> QUANT
    
    QUANT -->|God View JSON| ORCH
    ORCH -->|Final Synthetic Advisory| USER
```

---

## 2. Agent Capabilities & Fallback Protocols

Each agent is designed with a **Primary Live Mode** and a **Crisis Fallback Mode**, ensuring the system never fails even if APIs are down.

### 2.1 The Gatekeeper (Intelligence Router)
*   **Role**: Traffic Controller & Intent Classifier.
*   **Technology**: Asynchronous LLM Classification via `model_config.json`.
*   **Function**: Dynamically parses user natural language (e.g., "Analyze the France game") and extracts metadata like **Budget** and **Bet Count**.

### 2.2 Logistics Agent
*   **Role**: Environmental & Physiological Analyst.
*   **Primary Data**: **Open-Meteo API** (Live Weather, Elevation Data).
*   **Operational Logic**: Calculates "Altitude Shock" (e.g., Sea Level to Mexico City) and temperature stress penalties.

### 2.3 Tactics Agent (Pro)
*   **Role**: Team Performance & Tactical Analyst.
*   **Primary Data**: **SportMonks V3** (Live Scores, Lineups, Coaches).
*   **Operational Logic**:
    *   **Pre-Match**: Analyzes specific **Starting Eleven Lineups** and **Head Coach reputations**.
    *   **Lineup Analysis**: Evaluates tactical surprises or missing star players.

### 2.4 Market Agent
*   **Persona**: "The Vegas Sharp"
*   **Primary Data**: **The Odds API** (Live Lines from DraftKings, FanDuel).
*   **Function**: Identifies Arbitrage, Trap Lines, and "Sharp" money moves.

### 2.5 Narrative Agent (Social Sentiment)
*   **Dual-Scan**: Checks **Google News RSS** and **Reddit (No-Key Scraper)**.
*   **Config**: Uses `data/reddit_config.json` to monitor specific subreddits (r/soccer, r/worldcup).
*   **Function**: Scrapes headers for Morale, Scandals, and Locker Room friction without requiring API keys.

---

## 3. Production Features

### 3.1 Cloud Persistence (Supabase)
The system strictly enforces cloud persistence. Every "God View" and user session is saved to **Supabase**, ensuring that the bot retains memory even across server restarts or ephemeral cloud deployments.

#### 🛠️ Database Setup (Supabase)
To enable persistence, create a table in your Supabase project:
1.  **Table Name:** `sessions`
2.  **Primary Key:** `phone` (Type: `text`)
3.  **Column:** `god_view` (Type: `jsonb`)

### 3.2 Dynamic Model Routing (`data/model_config.json`)
Allows you to swap AI models for each agent instantly. You can route simple tasks to `gpt-4o-mini` and complex synthesis to `gpt-4o`.

---

## ⚙️ Setup & Installation

### 1. Prerequisites
*   Python 3.12+
*   Supabase Account (Database)
*   Docker (Optional, for Cloud deployment)

### 2. Environment Variables (.env)
```bash
# Core
OPENAI_API_KEY=sk-...
SUPABASE_URL=...
SUPABASE_KEY=...

# WhatsApp
WHATSAPP_TOKEN=...
PHONE_NUMBER_ID=...
VERIFY_TOKEN=...

# Intelligence Agents
ODDS_API_KEY=...
SPORTMONKS_API_TOKEN=...
```

### 3. Deployment (Docker)
The project includes a professional `Dockerfile` for one-command deployment.
```bash
docker build -t goalmine-ai .
docker run -p 8000:8000 goalmine-ai
```

---

## 🧪 WhatsApp Usage
- **"Analyze [Match]"**: Full swarm intelligence + Lineup analysis.
- **"Give me 3 bets with $100 budget"**: Multi-bet synthesis with Kelly staking.
- **"What's the weather?"**: Context-aware Q&A using Supabase session memory.

---

**Status**: � Cloud-Native / Production Ready
**Developer**: Jeffrey Fernandez
