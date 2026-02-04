# 🏦 GoalMine Confluence: The Master Intelligence Blueprint
**Version:** 2.0 ("Ghost Logic" Edition)  
**Project Lead:** Jeffrey Fernandez  
**Operational Status:** 🟢 Production Ready  
**Core Purpose:** Autonomous multi-agent betting intelligence for the 2026 FIFA World Cup.

---

## 📖 1. Mission Statement & Strategy
GoalMine is not a simple prediction bot; it is a **Human-in-the-Loop Betting Intelligence System**. The primary objective is to find **Alpha** (mathematical edges) by synthesizing deterministic data (statistics/weather) with semantic intelligence (news/market vibes).

### The "Ghost Logic" Paradigm
Standard bots use a single prompt. **Ghost Logic** uses a specialized swarm. By separating "Logistics" from "Tactics," we prevent the AI from becoming biased. Each agent acts as a witness; the "Closer" (Big Daddy) acts as the judge.

---

## 📈 2. The Decision Flow Architecture (Logic Graph)

```text
     [Daily 5AM Alarm]          [WhatsApp User Message]
             │                            │
             ▼                            ▼
   [Morning Brief Service]       [Gatekeeper Agent]
             │                            │
             ▼                            ▼
      [Merged Context] --------▶ [Check settings.json]
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
           [BUTTON-STRICT MODE]                      [CONVERSATIONAL MODE]
           (Strict UI Loops)                         (LLM Contextual Chat)
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         ▼
                               [Orchestrator Service]
                                         │
            ┌───────────────┼───────────────┬───────────────┐
            ▼               ▼               ▼               ▼
    [Logistics Agent] [Tactics Agent] [Market Agent] [Narrative Agent]
            │               │               │               │
            └───────────────┼───────────────┴───────────────┘
                            ▼
                    [Quant Engine (Math)]
                            │
                            ▼
                    [God View Builder]
                            │
                            ▼
                    [Supabase Database]
                            │
                            ▼
                [GENERATE BET AGT: Big Daddy]
                            │
                            ▼
                    [WhatsApp Client]
```

---

## 🛰️ 3. Ingestion Layer: The DataScout
The **DataScout Service** (`services/data_scout.py`) is the engine's central nervous system. It solves the "Static Data" problem by partnering local knowledge with live feeds.

*   **Foundation:** `data/schedule.json` (Custom venue altitude/notes).
*   **Live Feed:** Football-Data.org API v4.
*   **Merge Logic:** Every 60 minutes, the Scout overlays the API results onto the local file.
*   **TBD Resolution:** Automatically swaps placeholder "TBD" teams with real qualifiers (e.g., "USA vs TBD" becomes "USA vs Panama").
*   **Persistence:** Stores the "Active Schedule" in Supabase `system_storage` for instant system-wide availability.

---

## 🤖 4. The Agentic Swarm (Deep Dive)

### 🏗️ Agent 1: The Gatekeeper (`gpt-4o-mini`)
*   **Role:** Traffic Controller.
*   **Logic:** Classifies input into `BETTING`, `SCHEDULE`, or `CONV`. 
*   **Standards:** Deterministic (temp=0.1). High accuracy to prevent token waste on off-topic chatter.

### 🚛 Agent 2: Logistics Agent (`gpt-4o`)
*   **Role:** Calculating human physiological limits.
*   **Data:** Venue coordinates, Open-Meteo climate API.
*   **Equation:** Haversine(Dist) + Altitude(VO2_Shock) + Humidity(Stamina_Drain).
*   **Output:** Fatigue Penalty (reduces away team's xG).

### ⚔️ Agent 3: Tactics Agent (`gpt-4o`)
*   **Role:** The Head Coach.
*   **Data:** SportMonks/API-Football form data.
*   **Logic:** Matchup style analysis (e.g., "High-Press vs Low-Block").
*   **Output:** Base Adjusted xG.

### 💰 Agent 4: Market Agent (`gpt-4o`)
*   **Role:** The Sharp Bettor.
*   **Data:** The Odds API.
*   **Logic:** Calculates **Vig (Juice)** and detects "Trap Lines" (where the line makes no sense compared to stats).
*   **Output:** Value Score (A-F).

### 📰 Agent 5: Narrative Agent (`gpt-4o-mini`)
*   **Role:** The Journalist.
*   **Data:** Reddit API, Google News, Web Scrapers.
*   **Logic:** Sentiment mining. Can detect a "Locker Room Crisis" or "Hero Narrative."
*   **Output:** Vibe Multiplier (+/- 0.2 xG).

### 🎲 Agent 6: Quant Engine (Pure Python)
*   **Role:** The Mathematician.
*   **Model:** Dixon-Coles Probability Matrix.
*   **Standard:** **Kelly Criterion** for staking (Standard=0.5x, Aggressive=1.0x).

### 🏰 Agent 7: The Bet Generator Agent (Big Daddy / The Closer)
*   **Role:** Terminal Synthesizer & Bet Generator.
*   **Job:** Reads the **God View**, performs a final sanity check, and writes the WhatsApp message.
*   **Logic**: It reviews the conflicting reports (e.g., Tactics says 'Bet High' but Logistics says 'Team is Exhausted') and makes a final consensus decision.
*   **Authority:** It has the power to **VETO** a bet if the Narrative agent reports a critical last-minute injury or the Market agent flags a suspicious trap.

---

## 🗄️ 5. Data Persistence: The God View System
We do not pass strings between agents. We pass a **God View** object via Supabase.

| Table | Column | Type | Purpose |
| :--- | :--- | :--- | :--- |
| **sessions** | `god_view` | `JSONB` | Stores the 2.5KB intelligence matrix for a match. |
| **sessions** | `context` | `JSONB` | Remembers the "last match" for conversational follow-ups. |
| **system_storage** | `live_schedule` | `JSONB` | Stores the current merged 2026 World Cup calendar. |
| **predictions** | `payload` | `JSONB` | Archives every bet sent to every user for ROI tracking. |

---

## 🔑 6. API Management & Credential Audit
Ensure these keys are active in `.env` and `settings.json`:

1.  **OpenAI_API_KEY:** The reasoning heart.
2.  **WHATSAPP_TOKEN:** (Permanent System User Token required for production).
3.  **FOOTBALL_DATA_API_TOKEN:** `d0bcb25a490b4a3ebc278b88f256f59f` (10 req/min).
4.  **THE_ODDS_API_KEY:** (500 req/month free tier).
5.  **SUPABASE_URL/KEY:** Persistent state hub.

---

## ⚖️ 7. Gravity Rules: Engineering Standards
1.  **Strict Typing:** `typing.List`, `typing.Dict` in every function. No `any`.
2.  **Async/Await:** Blocking calls are illegal in the Orchestrator.
3.  **Prompt Separation:** Keep logic and "vibe" (prompts) separate.
4.  **Error Handling:** Always provide a `FALLBACK_XG` if an agent hits a rate limit.
5.  **Clean State:** I/O is always through the `Database` client.

---

## 🧠 8. Agentic Reasoning Chains (The Audit Trail)

Every recommendation generated by GoalMine carries a "Reasoning Chain" stored in the God View metadata. This ensures transparency and allows for human audit:

- **Tactics Justification**: *"Home team uses a high-press (85% efficiency) against an away team with low press-resistance (35th percentile). Baseline xG adjusted +0.25."*
- **Logistics Justification**: *"Away team playing at 2,400m after 4,000km travel. Estimated 12% drop in high-intensity sprints. Applying -0.15 xG penalty."*
- **Narrative Justification**: *"Social sentiment analysis (Reddit/Twitter) confirms squad morale boost following manager's public backing. Morale +0.10 adjustment."*

---

## 🚀 9. Future Roadmap: The "Flow" Phase
*   **Bankroll Onboarding:** Implement a WhatsApp Flow for encrypted budget setup.
*   **ROI Dashboard:** A web-view for users to track their GoalMine P&L.
*   **Automated Results:** The DataScout will eventually settle bets automatically by comparing API scores with the `predictions` table.

---
*Generated by the GoalMine AI Assistant. This document remains the Primary Source of Truth for the architecture.*
