# GoalMine: Autonomous World Cup 2026 Prediction Engine

**GoalMine** is a production-grade, event-driven hybrid intelligence system designed for professional-grade betting insights for the 2026 FIFA World Cup.

It operates on a sophisticated architecture that merges **deterministic mathematical modeling** (Quant Engine) with **semantic AI reasoning** (Agent Swarm). The system delivers high-confidence, real-time strategic advice directly via WhatsApp, acting as an automated "Human-in-the-Loop" advisor for sports syndicates.

---

## 🚀 2.0 Update: The "Ghost Logic" Revolution
GoalMine now features **Ghost Logic**, a context-aware conversational engine that moves beyond rigid menus. It remembers your previous match discussions, handles complex strategic pivots, and gracefully redirects off-topic chatter (The "McDonald's Test") while maintaining a sharp, professional persona.

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
        PROM[("system_prompts.py (The Brain)")]
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
        STRAT[Strategic Advisor (AI Specialist)]
    end

    USER -->|Natural Language| WEBHOOK
    WEBHOOK --> CONV
    CONV <--> DB
    
    CONV -->|Trigger Analysis| ORCH
    ORCH --> PROM
    
    ORCH -->|Trigger| Agent Swarm
    
    Agent Swarm --> QUANT
    
    QUANT -->|God View JSON| ORCH
    ORCH --> STRAT
    STRAT -->|Final Synthetic Advisory| USER
```

---

## 2. Core Components

### 2.1 The Ghost Logic (Conversational IQ)
*   **Context Persistence**: Remembers the match you're analyzing across multiple turns.
*   **Strategic Pivot**: Switch from "Analyze Mexico" to "What about the altitude?" instantly.
*   **Off-Topic Redirection**: Gracefully handles "The McDonald's Test" by guiding users back to football.
*   **Mutually Exclusive Logic**: Automatically detects and corrects impossible parlays (e.g., Mexico to Win vs. Draw in the same legs).

### 2.2 Centralized Intelligence (`prompts/system_prompts.py`)
All AI "Personalities" are now centralized in a single source of truth. This allows for instant updates to agent behavior, identity enforcement, and security rules across the entire swarm.

### 2.3 Agent Swarm Capabilities
*   **Logistics**: Calculates "Altitude Shock" (VO2 Max drop) and Travel Fatigue.
*   **Tactics**: Analyzes Starting XI, Coach Reputations, and Style Clashes.
*   **Market**: Scans for Arbitrage, Edge, and "Trap Lines" via The Odds API.
*   **Narrative**: Real-time sentiment analysis from News RSS and Reddit.

---

## 3. Deployment & Persistence

### 3.1 Cloud Persistence (Supabase)
The system strictly enforces cloud persistence. Every "God View" and user session is saved to **Supabase**, ensuring that the bot retains memory even across server restarts.

#### 🛠️ Database Setup
1.  **Table `sessions`**: Stores "God View" JSON (Phone PK, god_view JSONB).
2.  **Table `active_sessions`**: Stores recent message strings for context.

### 3.2 Dockerized Production
```bash
docker build -t goalmine-ai .
docker run -p 8000:8000 --env-file .env goalmine-ai
```

---

## 🧪 Advanced Usage & Testing

### Endurance Testing
The system includes a 100+ line conversation endurance test that challenges the AI on Persona, Arithmetic, and Context Memory.
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python test/test_user_journey_expanded.py
```

### WhatsApp Commands
- **"Hey, who are you?"**: Bot introduces its persona and capabilities.
- **"Analyze Mexico vs South Africa"**: Full swarm intelligence deployment.
- **"How should I split $500 on this?"**: Strategic advisor calculates +EV stakes.
- **"What if I parlay that with a Morocco win?"**: Cross-match parlay strategy analysis.

---

**Status**: 🟢 Production Ready (Ghost Logic 2.0)
**Developer**: Jeffrey Fernandez
