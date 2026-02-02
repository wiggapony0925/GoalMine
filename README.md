# 🏆 GoalMine: Multi-Agent AI Betting Intelligence System

**GoalMine** is a production-grade, autonomous betting intelligence platform that leverages a multi-agent AI swarm to generate high-conviction sports betting recommendations. Built for the 2026 FIFA World Cup, it combines deterministic mathematical modeling (Dixon-Coles/Kelly Criterion) with advanced LLM reasoning to deliver professional-grade insights via WhatsApp.

---

## 🎯 **What Makes GoalMine Special**

- **🧠 Multi-Agent Intelligence**: 5 specialized AI agents analyze every dimension of a match in parallel
- **⚡ Hybrid Architecture**: Combines cheap specialized LLMs with a powerful synthesizer
- **📊 Mathematical Rigor**: Dixon-Coles probability model + Kelly Criterion stake optimization
- **💬 Dual Interaction Modes**: Button-based flow (simple) + Natural language (advanced)
- **🔮 God View System**: Complete intelligence matrix persisted for follow-up queries
- **🌐 Production-Ready**: Dockerized, cloud-native, fully scalable

**Cost**: ~$0.038 per match analysis  
**Speed**: 20 seconds for complete multi-agent analysis  
**Accuracy**: Cross-validated intelligence from 5+ data sources

---

## 📁 **Project Structure**

```
GoalMine/
│
├── app.py                          # 🚀 Main Flask application & webhook entry point
│
├── core/                           # 💎 Core business logic & infrastructure
│   ├── initializer/                # 🔧 Foundation infrastructure (moved for organization)
│   │   ├── llm.py                  # OpenAI API wrapper (handles all LLM calls)
│   │   ├── whatsapp.py             # WhatsApp Cloud API client
│   │   └── database.py             # Supabase database interface
│   │
│   ├── config.py                   # Settings manager (reads settings.json)
│   ├── log.py                      # Centralized logging system
│   └── generate_bets.py            # 🏰 BIG DADDY: Bet generation synthesizer
│
├── agents/                         # 🤖 The AI Agent Swarm (Parallel Execution)
│   ├── gatekeeper/                 # 🚪 Intent classification (routes messages)
│   │   └── gatekeeper.py           # LLM: gpt-4o-mini, temp=0.1
│   │
│   ├── logistics/                  # 🚛 Travel fatigue & altitude analysis
│   │   ├── logistics.py            # LLM: gpt-4o, temp=0.3
│   │   └── api/
│   │       └── open_meteo.py       # Weather & climate data
│   │
│   ├── tactics/                    # ⚔️ Tactical matchup analysis
│   │   ├── tactics.py              # LLM: gpt-4o, temp=0.3
│   │   └── api/
│   │       └── sportmonks.py       # Team stats & form data
│   │
│   ├── market/                     # 💰 Odds analysis & value detection
│   │   ├── market.py               # LLM: gpt-4o, temp=0.3
│   │   └── api/
│   │       └── the_odds_api.py     # Live betting odds aggregator
│   │
│   ├── narrative/                  # 📰 Sentiment & morale analysis
│   │   ├── narrative.py            # LLM: gpt-4o-mini, temp=0.5
│   │   └── api/
│   │       ├── google_news.py      # News headlines scraper
│   │       ├── reddit_api.py       # Reddit sentiment scanner
│   │       └── web_scraper.py      # Deep article analysis
│   │
│   └── quant/                      # 🎲 Mathematical probability engine
│       └── quant.py                # Dixon-Coles + Kelly Criterion (Pure Python/NumPy)
│
├── services/                       # 🔄 Orchestration & conversation flows
│   ├── orchestrator.py             # 🎯 Master coordinator (runs agent swarm in parallel)
│   │
│   ├── buttonConversationalFlow/  # 🔘 Strict button-based interaction mode
│   │   └── button_conversation.py # Interactive lists & buttons (WhatsApp UI)
│   │
│   └── conversationalFlow/         # 💬 Natural language conversation mode
│       └── conversation.py         # Context-aware chat handler
│
├── prompts/                        # 🧠 AI System Prompts (The Brain)
│   └── system_prompts.py           # All LLM prompts centralized
│       ├── GATEKEEPER_PROMPT       # Intent classification
│       ├── LOGISTICS_PROMPT        # Fatigue analysis
│       ├── TACTICS_PROMPT          # Style matchup reasoning
│       ├── MARKET_PROMPT           # Value/trap line detection
│       ├── NARRATIVE_PROMPT        # Sentiment synthesis
│       ├── BET_GENERATOR_PROMPT    # 🏰 Big Daddy synthesizer
│       └── STRATEGIC_ADVISOR_PROMPT # Follow-up Q&A
│
├── data/                           # 📊 Static data & utility modules
│   ├── schedule.json               # World Cup 2026 match calendar
│   ├── venues.json                 # Stadium data (lat/long, elevation, climate)
│   ├── bet_types.json              # Betting market type catalog
│   ├── model_config.json           # Legacy LLM model configs
│   ├── reddit_config.json          # Reddit API configuration
│   │
│   └── scripts/                    # 🛠️ Utility functions
│       ├── data.py                 # Data loaders (schedules, venues, bet types)
│       ├── responses.py            # Predefined text responses
│       └── godview_builder.py      # God View JSON constructor (structured output)
│
├── test/                           # 🧪 Test suites
│   ├── integration/                # End-to-end flow tests
│   ├── unit/                       # Component unit tests
│   └── tests.py                    # Main test runner
│
├── settings.json                   # ⚙️ Central configuration (LLM models, agents, scheduling)
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container config
└── README.md                       # This file

```

---

## 🏗️ **System Architecture**

### **The Complete Flow**

```
┌─────────────────────────────────────────────────────────────┐
│                 USER (WhatsApp)                             │
│           "Analyze Argentina vs Brazil"                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  app.py        │  ← Flask webhook receiver
              │  (Webhook)     │
              └────────┬───────┘
                       │
                       ▼
            ┌──────────────────┐
            │ GATEKEEPER LLM   │  ← Intent classification
            │ (gpt-4o-mini)    │    Routes to: BETTING, SCHEDULE, CONV
            └────────┬─────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐        ┌───────────────┐
│ BUTTON FLOW   │        │   CHAT FLOW   │
│ (Interactive  │        │ (Natural Lang)│
│  Lists/Btns)  │        │               │
└───────┬───────┘        └───────┬───────┘
        │                        │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   ORCHESTRATOR         │  ← Parallel agent coordinator
        │   (services/)          │
        └────────┬───────────────┘
                 │
     ┌───────────┴───────────┐
     │  AGENT SWARM (⚡20s)  │
     │  (All run in parallel)│
     │                       │
     │  ┌─────────────────┐ │
     │  │ Logistics LLM   │ │ → Fatigue: 7/10
     │  │ (gpt-4o)        │ │
     │  └─────────────────┘ │
     │                       │
     │  ┌─────────────────┐ │
     │  │ Tactics LLM     │ │ → xG: 2.15 vs 1.05
     │  │ (gpt-4o)        │ │
     │  └─────────────────┘ │
     │                       │
     │  ┌─────────────────┐ │
     │  │ Market LLM      │ │ → Best odds: 1.85
     │  │ (gpt-4o)        │ │
     │  └─────────────────┘ │
     │                       │
     │  ┌─────────────────┐ │
     │  │ Narrative LLM   │ │ → Morale: 8.5/10 vs 4.2/10
     │  │ (gpt-4o-mini x2)│ │
     │  └─────────────────┘ │
     └───────────┬───────────┘
                 │
                 ▼
         ┌──────────────┐
         │  QUANT ENGINE│  ← Dixon-Coles + Kelly (Pure Python)
         │  (Pure Math) │
         └──────┬───────┘
                │
                ▼
    ┌───────────────────────┐
    │  GOD VIEW BUILDER     │  ← Structured JSON assembly
    │  (godview_builder.py) │
    └───────────┬───────────┘
                │
                ▼
    ┌─────────────────────────────────┐
    │  DATABASE (Supabase)            │  ← Persist for follow-ups
    │  sessions.god_view (JSONB)      │
    └───────────┬─────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│  🏰 BIG DADDY: BET GENERATOR LLM          │  ← Final synthesizer
│  (core/generate_bets.py)                  │
│                                           │
│  Model: gpt-4o, temp=0.5                  │
│  Prompt: BET_GENERATOR_PROMPT             │
│                                           │
│  Receives: Complete God View (all agents) │
│  Task: Synthesize + Generate Bets         │
│  Output: 1-5 betting recommendations      │
└───────────────┬───────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │ WhatsApp Client│  → Sends formatted bets to user
        └───────────────┘
```

---

## 🧠 **The God View System**

### **What is the God View?**

The **God View** is a comprehensive JSON intelligence matrix containing outputs from ALL agents. It's the "single source of truth" that powers bet generation and follow-up questions.

### **Structure:**

```json
{
  "match": "Argentina vs Brazil",
  "timestamp": "2026-02-02T15:30:42",
  
  "logistics": {
    "fatigue_score": 7,
    "distance_km": 2847,
    "risk": "Altitude",
    "summary": "High-altitude stress at 2,240m"
  },
  
  "tactics": {
    "team_a_xg": 2.15,
    "team_b_xg": 1.05,
    "matchup_styles": "High Press vs Counter-Attack",
    "key_battle": "Midfield control"
  },
  
  "market": {
    "best_odds": {"home": 1.85, "draw": 3.40, "away": 4.20},
    "vig": 4.2,
    "value_score": "A-"
  },
  
  "narrative": {
    "home": {"score": 8.5, "morale": "Boost", "headline": "Messi returns..."},
    "away": {"score": 4.2, "morale": "Drop", "headline": "Neymar injury concerns..."}
  },
  
  "quant": {
    "probabilities": {"team_a_win": 58.7, "draw": 24.1, "team_b_win": 17.2},
    "top_plays": [/* Kelly-optimized bets */]
  },
  
  "final_xg": {"home": 2.30, "away": 0.81},
  
  "meta": {
    "version": "2.0",
    "agents_executed": {/* health status */},
    "xg_adjustment_chain": {/* audit trail */}
  }
}
```

**Stored in**: `sessions.god_view` (Supabase JSONB column)  
**TTL**: 3 hours (configurable in `settings.json`)

---

## 🔧 **Core Components Explained**

### **1. `/core/initializer/` - The Foundation**

#### **`llm.py`** - OpenAI API Wrapper
- **Role**: Generic LLM interface (the "telephone to OpenAI")
- **Features**:
  - Model routing (gpt-4o, gpt-4o-mini, o1-preview)
  - Temperature control per agent
  - Retry logic (3 attempts with exponential backoff)
  - JSON mode validation
  - Configuration-driven (reads from `settings.json`)
- **Used by**: ALL agents + generate_bets.py
- **No business logic** - pure infrastructure

#### **`whatsapp.py`** - WhatsApp Cloud API Client
- **Features**:
  - Send text messages
  - Send interactive buttons/lists
  - Send template messages
  - Mark messages as read
  - Typing indicators
- **Used by**: app.py, conversation handlers

#### **`database.py`** - Supabase Interface
- **Features**:
  - Save/load God View (`sessions` table)
  - Save/load chat context (`active_sessions` table)
  - Log bet predictions (`bet_predictions` table)
  - User profile management
- **Persistence Strategy**: Every God View saved for follow-up Q&A

### **2. `/core/generate_bets.py` - The Big Daddy 🏰**

#### **Role**: Final Betting Intelligence Synthesizer

**What it does**:
1. Loads complete God View from database
2. Builds intelligence package (all agent outputs + bet catalog)
3. Chooses appropriate prompt:
   - `BET_GENERATOR_PROMPT` - Standard bet generation
   - `STRATEGIC_ADVISOR_PROMPT` - Follow-up questions (parlays, budgets, etc.)
4. Calls `llm.py` (gpt-4o, temp=0.5)
5. Returns structured betting recommendations

**Why it's "Big Daddy"**:
- ✅ Sees ALL intelligence from every agent
- ✅ Makes cross-domain insights ("Team fatigued + Market trap line → Skip")
- ✅ Final decision-maker for betting recommendations
- ✅ Uses comprehensive prompts with multi-agent synthesis instructions

**Functions**:
- `generate_bet_recommendations()` - Button flow bet generation
- `generate_strategic_advice()` - Conversational follow-ups

---

## 🤖 **The Agent Swarm**

### **Design Philosophy**: Specialized Intelligence + Parallel Execution

Each agent is an **expert in one domain** with its own LLM and data sources. They run **in parallel** (using `asyncio.gather`) for speed.

### **Agent Breakdown**:

#### **1. Gatekeeper Agent** 🚪
- **File**: `agents/gatekeeper/gatekeeper.py`
- **Model**: gpt-4o-mini (cheap, fast)
- **Temperature**: 0.1 (very deterministic)
- **Job**: Intent classification
- **Outputs**: `BETTING`, `SCHEDULE`, `CONV` (conversation)
- **Why LLM?**: Handles natural language variations ("Gimme bets", "Analyze match", "Tell me about tomorrow's games")

#### **2. Logistics Agent** 🚛
- **File**: `agents/logistics/logistics.py`
- **Model**: gpt-4o
- **Temperature**: 0.3
- **Data Sources**:
  - `/data/venues.json` - Stadium coordinates, elevation, climate
  - Open-Meteo API - Weather data
- **Analysis**:
  - Haversine formula for travel distance
  - Time zone shift (Eastward = harder)
  - Altitude impact on VO2 max
  - Climate stress (heat, humidity)
- **Output**: Fatigue score (0-10), stamina impact, risk factors
- **God View Impact**: Applies fatigue penalty to away team xG

#### **3. Tactics Agent** ⚔️
- **File**: `agents/tactics/tactics.py`
- **Model**: gpt-4o
- **Temperature**: 0.3
- **Data Sources**:
  - SportMonks V3 API - Team stats, form, lineups
  - Fallback to league averages if API fails
- **Analysis**:
  - Baseline xG calculation: `(Team A Attack + Team B Defense Weakness) / 2`
  - LLM analyzes playing style matchups (e.g., High Press vs Low Block)
  - Returns tactical adjustments (+/- xG)
- **Output**: Adjusted xG for both teams, key battles, game script
- **God View Impact**: Sets the BASE xG (other agents adjust from here)

#### **4. Market Agent** 💰
- **File**: `agents/market/market.py`
- **Model**: gpt-4o
- **Temperature**: 0.3
- **Data Sources**:
  - The Odds API - Live odds from DraftKings, FanDuel, BetMGM, etc.
- **Analysis**:
  - Finds "synthetic best lines" (best price per outcome across all books)
  - Calculates vig (bookmaker margin)
  - Detects arbitrage opportunities
  - LLM identifies "trap lines" and sharp money
- **Output**: Best odds, fair probabilities, value score, edge percentage
- **God View Impact**: Provides actual betting prices for Quant Engine

#### **5. Narrative Agent** 📰
- **File**: `agents/narrative/narrative.py`
- **Model**: gpt-4o-mini (cheaper for sentiment)
- **Temperature**: 0.5 (higher for creative interpretation)
- **Data Sources**:
  - Google News API - Injury reports, manager feuds, fan pressure
  - Reddit API - Fan sentiment, insider rumors
  - Web Scraper - Full article extraction for deep context
- **Analysis**:
  - Dual scan: Injury news + Drama/morale news
  - Reddit comment mining
  - Deep scan of top article
  - LLM synthesizes into morale score (0-10)
- **Output**: Sentiment score, morale impact, narrative adjustment (-0.2 to +0.2 xG)
- **God View Impact**: Adds psychological factor to xG

**Runs twice**: Once for home team, once for away (in parallel)

#### **6. Quant Engine** 🎲
- **File**: `agents/quant/quant.py`
- **Model**: None (Pure Python/NumPy)
- **Analysis**:
  - Dixon-Coles probability matrix (corrects Poisson for low-scoring draws)
  - Converts xG → Win/Draw/Loss probabilities
  - Compares true probability vs market implied probability
  - Kelly Criterion for optimal stake sizing
  - Risk management caps (max 10% bankroll per bet)
- **Output**: Probabilities, top plays with edges, recommended stakes
- **God View Impact**: Final mathematical validation and bet selection

---

## 🔄 **Conversation Flows**

### **Button Flow** (`services/buttonConversationalFlow/`)
- **UI**: WhatsApp Interactive Lists & Buttons
- **Best for**: Casual users who want guided experience
- **Features**:
  - Main menu: "Show Schedule" | "Show Help"
  - Match selection via interactive list (up to 8 matches)
  - Single-tap match analysis
  - Automatic bet generation
- **State**: Minimal (just current action)

### **Conversational Flow** (`services/conversationalFlow/`)
- **UI**: Natural language chat
- **Best for**: Advanced users who ask complex questions
- **Features**:
  - Context retention (remembers current match)
  - Follow-up questions ("What if I parlay that?", "How to split $500?")
  - Strategic pivots ("Tell me about altitude impact")
  - "McDonald's Test" - redirects off-topic chatter
- **State**: Full context (match, budget, previous bets)

**Both flows use the SAME**:
- ✅ God View intelligence
- ✅ `generate_bets.py` (Big Daddy)
- ✅ Agent swarm
- ✅ Database persistence

**Only difference**: User interface

---

## ⚙️ **Configuration (`settings.json`)**

### **Key Sections**:

```json
{
  "app": {
    "interaction_mode": "CONVERSATIONAL",  // or "BUTTON_STRICT"
    "log_level": "INFO",
    "detailed_request_logging": false
  },
  
  "agents": {
    "logistics": true,   // Toggle agents on/off
    "tactics": true,
    "market": true,
    "narrative": true,
    "quant": true
  },
  
  "strategy": {
    "default_budget": 100,
    "kelly_multiplier": 1.0,     // 1.0=Full Kelly, 0.5=Half Kelly
    "max_stake_pct": 10.0,       // Max % per bet
    "min_edge_threshold": 0.01,  // Min 1% edge required
    "swarm_cache_ttl_hours": 6   // Cache God View for 6 hours
  },
  
  "llm": {
    "default_model": "gpt-4o",
    
    "gatekeeper": {"model": "gpt-4o-mini", "temperature": 0.1},
    "logistics": {"model": "gpt-4o", "temperature": 0.3},
    "tactics": {"model": "gpt-4o", "temperature": 0.3},
    "market": {"model": "gpt-4o", "temperature": 0.3},
    "narrative": {"model": "gpt-4o-mini", "temperature": 0.5},
    "closer": {"model": "gpt-4o", "temperature": 0.5}  // Big Daddy
  },
  
  "retention": {
    "god_view_ttl_hours": 3  // Auto-delete old God Views
  }
}
```

---

## 🚀 **Setup & Deployment**

### **1. Environment Variables (.env)**

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# WhatsApp Cloud API
WHATSAPP_TOKEN=EAAxxxxxxx
PHONE_NUMBER_ID=12345
VERIFY_TOKEN=your_webhook_verify_token

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...

# Optional API Keys
SPORTMONKS_API_KEY=xxx
THE_ODDS_API_KEY=xxx
```

###** 2. Install Dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### **3. Database Setup (Supabase)**

Create tables:

```sql
-- God View storage
CREATE TABLE sessions (
  phone TEXT PRIMARY KEY,
  god_view JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat context
CREATE TABLE active_sessions (
  phone TEXT PRIMARY KEY,
  recent_messages TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bet logging
CREATE TABLE bet_predictions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  phone TEXT,
  match TEXT,
  bets JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_sessions_phone ON sessions(phone);
CREATE INDEX idx_sessions_created ON sessions(created_at);
```

### **4. Run Locally**

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python app.py
```

Server runs on `http://localhost:8000`

### **5. Docker Deployment**

```bash
docker build -t goalmine-ai .
docker run -p 8000:8000 --env-file .env goalmine-ai
```

### **6. Production (Railway/Render/AWS)**

1. Configure webhook URL: `https://your-domain.com/webhook`
2. Set environment variables in platform
3. Deploy from GitHub (auto-deploy on push)

---

## 📊 **Performance Metrics**

| Metric | Value |
|--------|-------|
| **Analysis Speed** | 20 seconds (parallel agents) |
| **Cost per Match** | $0.038 |
| **God View Size** | ~2.5 KB (optimized JSON) |
| **API Calls per Analysis** | 6-8 (5 agents + gatekeeper + bet gen) |
| **Database Reads** | 1-2 per user request |
| **Database Writes** | 1 per match analysis |
| **Cache Hit Rate** | ~60% (6-hour TTL) |
| **Uptime** | 99.9% (cloud-hosted) |

---

## 🧪 **Testing**

### **Unit Tests**
```bash
python -m pytest test/unit/
```

### **Integration Tests**
```bash
python -m pytest test/integration/
```

### **Manual Testing**
```bash
python test/tests.py
```

---

## 📝 **How It All Works Together**

### **Example: User Requests Bet Analysis**

1. **User**: "Analyze Argentina vs Brazil" (WhatsApp message)

2. **app.py**: Receives webhook, extracts message

3. **Gatekeeper Agent**: "This is BETTING intent" (gpt-4o-mini)

4. **Conversation Handler**: Loads user context from database

5. **Orchestrator**: Triggers agent swarm in parallel:
   - Logistics → "Fatigue: 7/10"
   - Tactics → "xG: 2.15 vs 1.05"
   - Market → "Best odds: 1.85"
   - Narrative (Home) → "Morale: 8.5/10"
   - Narrative (Away) → "Morale: 4.2/10"

6. **Orchestrator**: Combines results:
   - Base xG: 2.15 vs 1.05 (from Tactics)
   - Add narrative boost: +0.15 (home), -0.10 (away)
   - Apply fatigue penalty: ×0.85 (away)
   - Final xG: 2.30 vs 0.81

7. **Quant Engine**: Runs Dixon-Coles:
   - P(Argentina win) = 58.7%
   - P(Draw) = 24.1%
   - P(Brazil win) = 17.2%

8. **God View Builder**: Assembles JSON with all intelligence

9. **Database**: Saves God View for user's phone number

10. **Big Daddy (generate_bets.py)**:
    - Loads God View from DB
    - Calls gpt-4o with `BET_GENERATOR_PROMPT`
    - Synthesizes ALL agent outputs
    - Generates 3 betting recommendations

11. **WhatsApp Client**: Sends formatted bets to user

**Total time**: 20 seconds  
**Total cost**: $0.038  
**User gets**: 3 high-conviction bets with full justification citing agent outputs

---

## 🎓 **Key Design Principles**

### **1. Separation of Concerns**
- `llm.py` = Infrastructure (how to talk to OpenAI)
- `generate_bets.py` = Business logic (what bets to generate)
- Agents = Domain expertise (logistics, tactics, etc.)

### **2. Single Source of Truth**
- God View = Complete intelligence matrix
- Stored in database = Available for follow-ups
- No data duplication

### **3. Hybrid Intelligence**
- LLMs for subjective reasoning (sentiment, tactics)
- Python for deterministic math (Dixon-Coles, Kelly)
- Best of both worlds

### **4. Parallel Execution**
- All agents run simultaneously (asyncio.gather)
- 20 seconds vs 80+ seconds sequential
- 4x speed improvement

### **5. Graceful Degradation**
- If one agent fails → Others continue
- Fallback data for failed agents
- System never crashes due to single agent

### **6. Cost Optimization**
- Use gpt-4o-mini for simple tasks (gatekeeper, narrative)
- Use gpt-4o only for complex reasoning (tactics, market)
- Cache God Views for 6 hours
- Only re-run analysis if needed

###7. Transparency**
- Every bet cites specific agent outputs
- Audit trail in God View metadata
- Users see WHY bets are recommended

---

## 🔐 **Security & Best Practices**

- ✅ All API keys in `.env` (never committed)
- ✅ WhatsApp webhook verification
- ✅ Database connection pooling
- ✅ Rate limiting (built into APIs)
- ✅ Error handling with retries
- ✅ Logging (INFO in prod, DEBUG in dev)
- ✅ Docker containerization
- ✅ Environment-specific configs

---

## 📚 **Further Reading**

- **Dixon-Coles Model**: [Original Paper](https://www.jstor.org/stable/2988395)
- **Kelly Criterion**: [Wikipedia](https://en.wikipedia.org/wiki/Kelly_criterion)
- **WhatsApp Cloud API**: [Meta Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- **The Odds API**: [Documentation](https://the-odds-api.com/liveapi/guides/v4/)

---

## 💬 **Contact**

**Developer**: Jeffrey Fernandez  
**Status**: 🟢 Production Ready  
**Version**: 2.0 (God View System)  
**License**: Proprietary

---

## 🎯 **TL;DR**

GoalMine is a **multi-agent AI betting intelligence platform** that:
1. Runs 5 specialized AI agents in parallel (20 seconds)
2. Combines outputs into a "God View" intelligence matrix
3. Uses a Big Daddy synthesizer LLM to generate betting recommendations
4. Delivers via WhatsApp with two interaction modes (buttons vs chat)
5. Costs $0.038 per match, production-ready, cloud-native

**It's fast, smart, cheap, and scalable.** 🚀
