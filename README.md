# GoalMine 🏆 - World Cup 2026 Betting Engine

**GoalMine** is a state-of-the-art, event-driven hybrid intelligence system designed to function as a "Human-in-the-Loop" betting advisor for the 2026 FIFA World Cup.

It operates on a sophisticated architecture that merges **deterministic mathematical modeling** (Quant Engine) with **semantic AI reasoning** (Agent Swarm) to deliver high-confidence, professional-grade betting insights directly via WhatsApp.

---

## 🏗 System Architecture

The core of GoalMine is an **Agent Swarm** orchestration pattern. Unlike simple chatbots, GoalMine does not just "reply"; it actively thinks, researches, calculates, and synthesizes information from multiple live sensors before formulating a response.

### 🔄 The Intelligence Flow

```mermaid
graph TD
    User([User (WhatsApp)]) -->|Message| Webhook[Flask Gateway]
    
    Webhook --> Gatekeeper{Gatekeeper AI}
    
    Gatekeeper -- Chit Chat / Off Topic --> DirectResponse[Simple AI Reply]
    Gatekeeper -- Betting Intent --> Orchestrator[Orchestrator Service]
    
    subgraph "The Agent Swarm (Parallel Execution)"
        Orchestrator -->|Analyze| Logistics[Logistics Agent]
        Orchestrator -->|Analyze| Tactics[Tactics Agent]
        Orchestrator -->|Analyze| Market[Market Agent]
        Orchestrator -->|Analyze| Narrative[Narrative Agent]
        
        Logistics -->|Fatigue & Travel Data| Quant[Quant Engine]
        Tactics -->|xG & Injury Data| Quant
        Market -->|Live Odds| Quant
        Narrative -->|Sentiment Score| Quant
    end
    
    Quant -->|Win Probabilities & Edge| Closer[The Closer (LLM)]
    
    Closer -->|Final Briefing| User
```

---

## 🧠 The Agent Swarm

GoalMine relies on 4 specialized sub-agents and 1 master decision maker. Each agent is an **Object-Oriented Class** situated in `agents/` that partners with a specific external API.

### 1. 👮 The Gatekeeper (`agents/gatekeeper`)
*   **Role**: Traffic Controller.
*   **Logic**: Uses OpenAI to classify incoming messages into `BETTING` (High Value) vs `CHIT_CHAT` (Low Value).
*   **Purpose**: Prevents wasting expensive API calls on messages like "Hello" or "Thanks".

### 2. � Logistics Agent (`agents/logistics`)
*   **Persona**: Senior Logistics Coordinator.
*   **Partner API**: `WeatherAPI`.
*   **Function**:
    *   Calculates **Haversine Distance** between venues (e.g., MetLife NJ to Azteca Mexico).
    *   Analyzes **Altitude Shock** (e.g., playing at 2,240m elevation).
    *   Determines **Travel Fatigue** impact on player performance.

### 3. ♟️ Tactics Agent (`agents/tactics`)
*   **Persona**: World-Class Tactician (Pep Guardiola style).
*   **Partner API**: `SportMonks` / `API-Football`.
*   **Function**:
    *   Fetches **Expected Goals (xG)** stats.
    *   Analyzes recent form and **Key Injuries**.
    *   Uses LLM to predict "Game Flow" (Possession vs Counter-Attack).

### 4. 📉 Market Agent (`agents/market`)
*   **Persona**: Quantitative Market Sniper.
*   **Partner API**: `The Odds API`.
*   **Function**:
    *   Scans books (DraftKings, FanDuel, BetMGM).
    *   Identifies **Arbitrage** opportunities and **Line Shopping** value.
    *   Detects "Trap Lines" where implied probability disagrees with stats.

### 5. 📰 Narrative Agent (`agents/narrative`)
*   **Persona**: Sports Psychologist & Media Analyst.
*   **Partner API**: `NewsAPI`.
*   **Function**:
    *   Scrapes global news headlines.
    *   Uses LLM to generate a **Sentiment Score** (0-10).
    *   Detects non-stat factors: locker room scandals, manager friction, motivation levels.

---

## 🧮 The Quant Engine & Decision Core

The brain of the operation isn't just an LLM; it's a rigorous math model found in `agents/quant/quant.py`.

### The Math: Monte Carlo & Poisson
*   **Simulation**: Runs **10,000 matches** between the two teams using their adjusted xG (Expected Goals).
*   **Poisson Distribution**: Models the probability of every possible scoreline (0-0, 1-0, 2-1, etc.).
*   **Kelly Criterion**: Calculates the mathematically optimal bet size (% of bankroll) based on the calculated **Edge** vs the Bookmaker's Odds.

### The Closer (`services/orchestrator.py`)
*   **Persona**: Senior Hedge Fund Risk Manager.
*   **Function**: The Final Boss.
*   **Input**: Receives the raw math from the Quant Engine + the qualitative "Vibes" from the Narrative/Tactics agents.
*   **Veto Power**: If the Quant Engine says "Bet" (Edge > 2%) but the Narrative Agent signals "Crisis" (Score < 3), The Closer **VETOES** the bet.
*   **Output**: A concise, professional, "Wall Street" style memo sent to WhatsApp.

---

## ⚙️ Technical Stack

*   **Core**: Python 3.14+, Flask (Webhook Gateway).
*   **Async**: `asyncio` for parallel agent execution (High Performance).
*   **Scheduling**: `APScheduler` for the 8:00 AM Morning Brief.
*   **LLM**: OpenAI GPT-4o via `AsyncOpenAI` client.
*   **database**: JSON (Mock) / Postgres (Production).

---

## 🚀 Setup Guide

### 1. Prerequisites
*   Python 3.10+
*   Meta Developer Account (WhatsApp Cloud API)
*   OpenAI API Key
*   The Odds API Key (Free Tier)
*   NewsAPI Key (Free Tier)

### 2. Installation
```bash
git clone https://github.com/YourUsername/GoalMine.git
cd GoalMine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```ini
# Meta / WhatsApp
VERIFY_TOKEN=my_secure_verify_token
WHATSAPP_TOKEN=EAAG... (System User Token)
PHONE_NUMBER_ID=100...

# Intelligence
OPENAI_API_KEY=sk-...

# Data Partners
ODDS_API_KEY=...
NEWS_API_KEY=...
```

### 4. Launch
```bash
python app.py
```
*You should see the "GoalMine AI" Banner and System Check logs.*

---

**Status**: 🏗 Alpha (Logic Complete / Mock Data Active)
**Developer**: Jeffrey Fernandez
**License**: Proprietary
