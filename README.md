# GoalMine: Autonomous World Cup 2026 Prediction Engine

**GoalMine** is an event-driven hybrid intelligence system designed to provide professional-grade betting insights for the 2026 FIFA World Cup.

It operates on a sophisticated architecture that merges **deterministic mathematical modeling** (Quant Engine) with **semantic AI reasoning** (Agent Swarm). The system delivers high-confidence, real-time strategic advice directly via WhatsApp, acting as an automated "Human-in-the-Loop" advisor.

---

## 1. System Architecture

GoalMine is built for **scalability** and **persistence**. The core is an **Agent Swarm** orchestration pattern combined with **Fail-Safe Redundancy**.

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
        MEM[("memory.json (Persistence)")]
    end
    
    subgraph Agent Swarm
        TAC[Tactics Agent] <--> MONKS[SportMonks API v3]
        LOG[Logistics Agent] <--> METEO[Open-Meteo API]
        MKT[Market Agent] <--> ODDS[The Odds API]
        NAR[Narrative Agent] <--> GOOG[News] & REDDIT[Reddit]
    end

    subgraph Synthesis
        QUANT[Quant Engine (NumPy Matrix)]
        ORCH[Orchestrator Service]
        MODELS[("model_config.json")]
    end

    USER -->|Message| WEBHOOK
    WEBHOOK --> CONV
    CONV <--> MEM
    
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
*   **Fallback**: "Geographic Estimator" (Uses historical climate averages).

### 2.3 Tactics Agent
*   **Role**: Team Performance & Tactical Analyst.
*   **Primary Data**: **SportMonks API v3** (Live Scores, Squads, Recent Form).
*   **Operational Logic**:
    *   **Pre-Match**: Analyzes Roster Depth and Form (Last 5 Games).
    *   **Live Monitoring**: Reports real-time minutes and scorelines.
*   **Fallback**: "Internal Knowledge Base" (Estimates xG based on team tiers).

### 2.4 Market Agent
*   **Persona**: "The Vegas Sharp"
*   **Primary Data**: **The Odds API** (Live Lines from DraftKings, FanDuel).
*   **Function**: Identifies Arbitrage, Trap Lines, and "Sharp" money moves.

### 2.5 Narrative Agent (Social Sentiment)
*   **Dual-Scan**: Checks **Google News RSS** and **Reddit** (via PRAW).
*   **Config**: Uses `data/reddit_config.json` to monitor specific subreddits (r/soccer, r/worldcup).
*   **Function**: Scrapes headers for Morale, Scandals, and Locker Room friction.

### 2.6 The Quant Engine (Math Core)
*   **Logic**: Vectorized Poisson Matrix + Kelly Criterion Staking.
*   **Dynamic Staking**: Automatically recalculates exact dollar amounts based on the user's specified budget.

---

## 3. Advanced Features

### 3.1 Model Routing (`data/model_config.json`)
Allows you to swap AI models for each agent instantly. You can route simple tasks to `gpt-4o-mini` and complex synthesis to `gpt-4o`.

### 3.2 Persistent Memory (`data/memory.json`)
Saves the "God View" of matches per user. This allows the bot to answer follow-up questions (e.g., *"Why did you recommend that?"*) without re-running the expensive agent swarm.

### 3.3 Dynamic Settings
- **`bet_types.json`**: Define which markets the bot is authorized to recommend.
- **`reddit_config.json`**: Manage your social intelligence streams effortlessly.

---

## 4. 🧠 The "God View" JSON Payload
This is the heart of the engine—the synthesized data block that the final Orchestrator uses to generate advice.

```json
{
  "match_context": {
    "fixture": "France vs Brazil",
    "venue": "Azteca (High Altitude)",
    "kickoff_weather": "28°C, 35% Humidity"
  },
  "tactical_intel": {
    "live_status": "HT",
    "score": "0-1",
    "key_insight": "Mbappe isolated. Brazil controlling midfield."
  },
  "quant_verdict": {
    "win_prob": {"home": 32.1, "away": 45.4, "draw": 22.5},
    "value_edge": "Bet Brazil Win @ +140 (>5% EV)",
    "top_plays": [
      {"type": "Moneyline Brazil", "odds": 2.20, "stake": "$42.00"}
    ]
  }
}
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
*   Python 3.14+
*   Meta Developer Account (WhatsApp Cloud API)
*   OpenAI API Key

### 2. Installation
```bash
git clone https://github.com/YourUsername/GoalMine.git
cd GoalMine
pip install -r requirements.txt
```

### 3. Environment Variables (.env)
```bash
OPENAI_API_KEY=sk-...
ODDS_API_KEY=...
SPORTMONKS_API_TOKEN=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
```

### 4. Launch
```bash
python app.py
```

---

## 🧪 WhatsApp Usage
- **"Analyze [Team]"**: Runs the full swarm intelligence.
- **"Give me 3 bets"**: Multi-bet synthesis with Kelly staking.
- **"I have $100 budget"**: Automatically updates all staking recommendations.
- **"What's the weather?"**: Context-aware Q&A based on memory.

---

**Status**: 🟢 Production Ready (Live Data + Hybrid Sentiment)
**Developer**: Jeffrey Fernandez
