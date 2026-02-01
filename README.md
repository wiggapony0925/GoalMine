# GoalMine: Autonomous World Cup 2026 Prediction Engine

**GoalMine** is an event-driven hybrid intelligence system designed to provide professional-grade betting insights for the 2026 FIFA World Cup.

It operates on a sophisticated architecture that merges **deterministic mathematical modeling** (Quant Engine) with **semantic AI reasoning** (Agent Swarm). The system delivers high-confidence, real-time strategic advice directly via WhatsApp, acting as an automated "Human-in-the-Loop" advisor.

---

## 1. System Architecture

The core of GoalMine is an **Agent Swarm** orchestration pattern combined with **Fail-Safe Redundancy**. The system is built to handle live data ingestion, multi-agent consensus, and quantitative validation.

![GoalMine Flow Architecture](goalmine_n8n_flow_diagram.png)

### 1.1 The Intelligence Flow

```mermaid
graph TD
    subgraph Sources
        USER([User Interface (WhatsApp)])
        SCHED[("schedule.json (Calendar)")]
        BETS[("bet_types.json (Market Taxonomy)")]
    end

    subgraph Processing Step
        WEBHOOK[Flask Gateway]
        GATE{Gatekeeper AI}
        ORCH[Orchestrator Service]
    end
    
    subgraph Agent Swarm
        TAC[Tactics Agent] <--> MONKS[SportMonks API v3]
        LOG[Logistics Agent] <--> METEO[Open-Meteo API]
        MKT[Market Agent] <--> ODDS[The Odds API]
        NAR[Narrative Agent] <--> GOOG[Google News System]
    end

    subgraph Synthesis
        QUANT[Quant Engine (Math Model)]
        CLOSER[The Closer (LLM Finalizer)]
    end

    USER -->|Message| WEBHOOK
    WEBHOOK --> GATE
    
    GATE -- "Chit Chat" --> USER
    GATE -- "Betting Intent" --> ORCH
    
    SCHED --> ORCH
    
    ORCH -->|Trigger| TAC
    ORCH -->|Trigger| LOG
    ORCH -->|Trigger| MKT
    ORCH -->|Trigger| NAR
    
    TAC -->|xG / Squad Data| QUANT
    LOG -->|Fatigue Score| QUANT
    MKT -->|Live Odds| QUANT
    NAR -->|Sentiment Score| QUANT
    
    QUANT -->|Probability & Edge| CLOSER
    BETS --> CLOSER
    
    CLOSER -->|Final Advisory| USER
```

---

## 2. Agent Capabilities & Fallback Protocols

Each agent is designed with a **Primary Live Mode** and a **Crisis Fallback Mode**. If an external API fails, the Agent seamlessly switches to an internal estimation protocol, ensuring system reliability.

### 2.1 The Gatekeeper
*   **Role**: Traffic Controller & Intent Classifier.
*   **Technology**: Asynchronous LLM Classification.
*   **Function**: Dynamically parses user natural language (e.g., "Analyze the France game" vs "Hello") to route requests efficiently.

### 2.2 Logistics Agent
*   **Role**: Environmental & Physiological Analyst.
*   **Primary Data**: **Open-Meteo API** (Live Weather, Elevation Data).
*   **Operational Logic**: Calculates "Altitude Shock" (e.g., Sea Level to Mexico City) and travel fatigue penalties.
*   **Fallback**: "Geographic Estimator" (Uses historical climate averages for the region).

### 2.3 Tactics Agent
*   **Role**: Team Performance & Tactical Analyst.
*   **Primary Data**: **SportMonks API v3** (Live Scores, Squads, Recent Form).
*   **Operational Logic**:
    *   **Pre-Match**: Analyzes Roster Depth and Form (Last 5 Games).
    *   **Live Monitoring**: reports real-time minutes and scorelines.
    *   **Half-Time Strategy**: Identifies specific "Comeback" or "Next Goal" opportunities during the break.
*   **Fallback**: "Internal Knowledge Base" (Estimates xG based on team tiers).

### 4. 📉 Market Agent (`agents/market`)
*   **Persona**: "The Vegas Sharp"
*   **Primary Data**: **The Odds API** (Live Lines from DraftKings, FanDuel).
*   **Crisis Fallback**: "Vegas Estimator" (Sets its own fair lines if the market is down).
*   **Function**: Identifies Arbitrage and "Trap Lines".

### 5. 📰 Narrative Agent (`agents/narrative`)
*   **Persona**: "Investigative Journalist"
*   **Primary Data**: **Google News RSS** (Real-time Headlines).
*   **Crisis Fallback**: "Archive Recall" (Historical reputation analysis).
*   **Function**: Scrapes headers for Morale, Scandals, and Locker Room friction.

---

### 6. 🎛 The Orchestrator & Quant Fusion
*   **Role**: The Conductor.
*   **Process**:
    1.  **Parallel Execution**: Triggers all 4 Agents simultaneously (`asyncio.gather`).
    2.  **Data Fusion**: Aggregates JSON outputs (Logistics Fatigue + Tactics xG + Market Odds + Narrative Sentiment).
    3.  **Quant Weighting**: Applies mathematical penalties (e.g., *Multiplies Away Team xG by 0.85 if Altitude Fatigue > 8*).
    4.  **The Closer**: The final LLM receives this synthesized "God View" JSON to write the final WhatsApp briefing.

*   **Kick-Off Alerts**: Scans `schedule.json` every 15 minutes. If a game starts in < 60 mins, it texts the user: *"🚨 Alert: Match Starting!"*
*   **Morning Brief**: At 8:00 AM, checks the **Real Calendar Date**. If games exist, it sends a briefing. If not, it stays silent.
*   **Awareness**: If you text "Betting" on a day with no games, GoalMine replies: *"No games scheduled today. I can simulate one if you like."*

---

## ⚙️ Technical Stack

*   **Core**: Python 3.14+, Flask (Webhook Gateway).
*   **Async**: `asyncio` for parallel agent execution.
*   **LLM**: OpenAI GPT-4o via `AsyncOpenAI`.
*   **APIs**: SportMonks (Tactics), Open-Meteo (Logistics), The Odds API (Market), Google News (Narrative).

---

### 7. 🧠 The "God View" JSON Payload
This is the heart of the engine—the synthesized data block that the final LLM receives to generate its advice. It is designed to be **context-rich** and **action-oriented**.

```json
{
  "match_context": {
    "fixture": "France vs Brazil",
    "stage": "Semi-Final",
    "venue": "Azteca (High Altitude)",
    "kickoff_weather": "28°C, 35% Humidity (Heat Stress Alert)"
  },
  "tactical_intel": {
    "live_status": "HT",
    "score": "0-1",
    "possession": "42% vs 58%",
    "key_insight": "France lost midfield control. Mbappe isolated (0 touches in box).",
    "roster_health": "Varane limping (42')."
  },
  "market_pulse": {
    "pre_match_line": "France -110",
    "live_line": "France +220 (Drastic drift)",
    "smart_money_move": "Sharp money hitting Brazil -0.5 heavily."
  },
  "narrative_vibe": {
    "home_sentiment": "Toxic (Coach arguing with bench)",
    "away_sentiment": "Confident / Flow State"
  },
  "quant_verdict": {
    "win_prob": {"home": 32.1, "away": 45.4, "draw": 22.5},
    "value_edge": "Bet Brazil 2nd Goal @ +140 (>5% EV)"
  }
}
```

*   **Multi-Game Handling**: If multiple games are active, the Orchestrator generates a **List** of these JSON blocks (`[Match_A_Payload, Match_B_Payload]`).
*   **The Closer** iterates through this list and prioritizes the match with the **Highest 'Value Edge'** to present first.

### 1. Prerequisites
*   Python 3.10+
*   Meta Developer Account (WhatsApp Cloud API)

### 2. Installation
```bash
git clone https://github.com/YourUsername/GoalMine.git
cd GoalMine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file (See `.env.example`).
**CRITICAL**: You must provide `OPENAI_API_KEY` and specific data keys (`ODDS_API_KEY`, `SPORTMONKS_API_TOKEN`) for full "Live" mode.

### 4. Launch
```bash
python app.py
```
*You will see the "GoalMine AI" Banner and System Check logs.*

---

**Status**: 🟢 Production Ready (Live Data + Fallback Logic Active)
**Developer**: Jeffrey Fernandez
