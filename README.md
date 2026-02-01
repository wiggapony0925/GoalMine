# GoalMine 🏆 - World Cup 2026 Betting Engine

**GoalMine** is a state-of-the-art, event-driven hybrid intelligence system designed to function as a "Human-in-the-Loop" betting advisor for the 2026 FIFA World Cup.

It operates on a sophisticated architecture that merges **deterministic mathematical modeling** (Quant Engine) with **semantic AI reasoning** (Agent Swarm) to deliver high-confidence, professional-grade betting insights directly via WhatsApp.

---

## 🏗 System Architecture

The core of GoalMine is an **Agent Swarm** orchestration pattern combined with **Fail-Safe Redundancy**.

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

## 🧠 The Agent Swarm (Redundant & Robust)

Each agent is designed with a **"Live"** mode and a **"Crisis Fallback"** mode. If an API fails, the Agent switches personas to estimation mode, ensuring zero downtime.

### 1. 👮 The Gatekeeper
*   **Role**: Traffic Controller.
*   **Tech**: Uses Async LLM Classification (`BETTING` vs `CHIT_CHAT` vs `OFF_TOPIC`).
*   **Function**: dynamically interprets user intent from natural language (e.g., "Analyze France vs Brazil" is automatically parsed).

### 2. 🚚 Logistics Agent (`agents/logistics`)
*   **Persona**: "Mission Control"
*   **Primary Data**: **Open-Meteo API** (Real Elevation & Live Weather).
*   **Crisis Fallback**: "Geographic Estimator" (Uses latitude/month averages).
*   **Function**: Calculates precise "Altitude Shock" (MetLife -> Azteca) and physiological travel penalties.

### 3. ♟️ Tactics Agent (`agents/tactics`)
*   **Persona**: "The Pep Guardiola of Analytics"
*   **Primary Data**: **SportMonks API v3** (Real xG, Form, Squads).
*   **Crisis Fallback**: "Internal Knowledge" (Estimates xG based on team tiers).
*   **Function**: Deconstructs match-ups and predicts "Game Flow" (e.g., Low Block vs High Press).

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

## 🕰 Dynamic Scheduling & Alerts

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

## 🚀 Setup Guide

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
