import asyncio
import json
from datetime import datetime
from core.log import get_logger
from agents.logistics.logistics import LogisticsAgent
from agents.tactics.tactics import TacticsAgent
from agents.market.market import MarketAgent
from agents.narrative.narrative import NarrativeAgent
from agents.quant.quant import run_quant_engine # Still function based for now
from core.initializer.llm import query_llm
from data.scripts.data import SCHEDULE, BET_TYPES
from core.config import settings

logger = get_logger("Orchestrator")

# Initialize Agents
logistics_agent = LogisticsAgent()
tactics_agent = TacticsAgent()
market_agent = MarketAgent()
narrative_agent = NarrativeAgent()

# Internal Cache to prevent redundant swarm triggers
SWARM_CACHE = {}
CACHE_TTL_HOURS = settings.get('strategy.swarm_cache_ttl_hours', 6)

def format_to_12hr(date_iso):
    """Converts ISO timestamp to 12-hour format: 5:00 PM."""
    dt = datetime.fromisoformat(date_iso)
    return dt.strftime("%I:%M %p").lstrip("0")

async def generate_betting_briefing(match_info, user_budget=100):
    """
    Orchestrates the analysis across all agents in PARALLEL.
    Checks SWARM_CACHE first to avoid redundant API/LLM costs.
    """
    home = match_info.get('home_team', 'Team A')
    away = match_info.get('away_team', 'Team B')
    match_key = f"{home}_vs_{away}".lower().replace(" ", "_")
    
    # Check Cache
    if match_key in SWARM_CACHE:
        cache_entry = SWARM_CACHE[match_key]
        cache_time = datetime.fromisoformat(cache_entry['timestamp'])
        age = (datetime.utcnow() - cache_time).total_seconds() / 3600
        
        if age < CACHE_TTL_HOURS:
            logger.info(f"♻️ Cache Hit for {home} vs {away} (Age: {round(age, 2)}h). Skipping swarm.")
            cached_briefing = cache_entry['data'].copy()
            # Update dynamic fields
            cached_briefing['quant'] = run_quant_engine(
                cached_briefing['final_xg']['home'], 
                cached_briefing['final_xg']['away'], 
                cached_briefing['market'].get('best_odds'), 
                user_budget, home, away
            )
            return cached_briefing

    logger.info(f"🚀 GoalMine Swarm Activated: {home} vs {away}")
    
    # 1. Start Agents in Parallel with toggle checks
    tasks = []
    
    # Logistics
    if settings.get('agents.logistics', True):
        tasks.append(logistics_agent.analyze(
            match_info.get('venue_from', 'MetLife Stadium, East Rutherford'), 
            match_info.get('venue', 'Estadio Azteca, Mexico City')
        ))
    else:
        logger.info("⏸️ Logistics Agent disabled via settings.")
        tasks.append(asyncio.sleep(0, result={"branch": "logistics", "status": "DISABLED", "fatigue_score": 5}))

    # Tactics
    if settings.get('agents.tactics', True):
        tasks.append(tactics_agent.analyze(home, away))
    else:
        logger.info("⏸️ Tactics Agent disabled via settings.")
        tasks.append(asyncio.sleep(0, result={"branch": "tactics", "status": "DISABLED", "team_a_xg": 1.5, "team_b_xg": 1.2}))

    # Market
    if settings.get('agents.market', True):
        tasks.append(market_agent.analyze(home, away))
    else:
        logger.info("⏸️ Market Agent disabled via settings.")
        tasks.append(asyncio.sleep(0, result={"branch": "market", "status": "DISABLED", "best_odds": "N/A"}))

    # Narrative
    if settings.get('agents.narrative', True):
        tasks.append(narrative_agent.analyze(home))
        tasks.append(narrative_agent.analyze(away))
    else:
        logger.info("⏸️ Narrative Agent disabled via settings.")
        tasks.append(asyncio.sleep(0, result={"branch": "narrative", "status": "DISABLED", "score": 5}))
        tasks.append(asyncio.sleep(0, result={"branch": "narrative", "status": "DISABLED", "score": 5}))
    
    # Execute all with graceful degradation
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    log_res, tac_res, mkt_res, nar_a, nar_b = results
    
    # 2. Handle failures with fallback data
    # Logistics fallback
    if isinstance(log_res, Exception):
        logger.error(f"❌ Logistics Agent failed: {log_res}")
        log_res = {
            "branch": "logistics",
            "fatigue_score": 5,
            "summary": "Logistics data unavailable - using neutral baseline",
            "status": "FALLBACK"
        }
    else:
        logger.info(f"✅ Logistics: Fatigue Score {log_res.get('fatigue_score', 'N/A')}")
        logger.debug(f"📊 Logistics Full Response: {json.dumps(log_res, indent=2)}")
    
    # Tactics fallback
    if isinstance(tac_res, Exception):
        logger.error(f"❌ Tactics Agent failed: {tac_res}")
        tac_res = {
            "branch": "tactics",
            "team_a_xg": 1.5,
            "team_b_xg": 1.2,
            "summary": "Tactical data unavailable - using league averages",
            "status": "FALLBACK"
        }
    else:
        logger.info(f"✅ Tactics: xG {tac_res.get('team_a_xg', 'N/A')} vs {tac_res.get('team_b_xg', 'N/A')}")
        logger.debug(f"📊 Tactics Full Response: {json.dumps(tac_res, indent=2)}")
    
    # Market fallback
    if isinstance(mkt_res, Exception):
        logger.error(f"❌ Market Agent failed: {mkt_res}")
        mkt_res = {
            "branch": "market",
            "best_odds": {},
            "summary": "Market data unavailable - odds not available",
            "status": "FALLBACK"
        }
    else:
        logger.info(f"✅ Market: Best Entry found on {mkt_res.get('best_odds', {}).get('Team_A_Win', {}).get('platform', 'N/A')}")
        logger.debug(f"📊 Market Full Response: {json.dumps(mkt_res, indent=2)}")
    
    # Narrative A fallback
    if isinstance(nar_a, Exception):
        logger.error(f"❌ Narrative Agent ({home}) failed: {nar_a}")
        nar_a = {
            "branch": "narrative",
            "team": home,
            "score": 5,
            "summary": "Narrative data unavailable - neutral sentiment assumed",
            "status": "FALLBACK"
        }
    else:
        logger.info(f"✅ Narrative ({home}): Score {nar_a.get('score', 5)}")
        logger.debug(f"📊 Narrative ({home}) Full Response: {json.dumps(nar_a, indent=2)}")
    
    # Narrative B fallback
    if isinstance(nar_b, Exception):
        logger.error(f"❌ Narrative Agent ({away}) failed: {nar_b}")
        nar_b = {
            "branch": "narrative",
            "team": away,
            "score": 5,
            "summary": "Narrative data unavailable - neutral sentiment assumed",
            "status": "FALLBACK"
        }
    else:
        logger.info(f"✅ Narrative ({away}): Score {nar_b.get('score', 5)}")
        logger.debug(f"📊 Narrative ({away}) Full Response: {json.dumps(nar_b, indent=2)}")
    
    # 3. Extract Data & Apply Multipliers
    # Tactics provides the tactically-adjusted baseline (xG)
    base_xg_a = tac_res.get('team_a_xg', 1.5)
    base_xg_b = tac_res.get('team_b_xg', 1.1)
    
    # Logic: Logistics Fatigue Penalty
    # We apply a penalty based on fatigue score and stamina impact
    log_penalty_b = 1.0
    f_score_b = log_res.get('fatigue_score', 0)
    if f_score_b > 7:
        log_penalty_b = 0.85 # Serious drop
    elif f_score_b > 5:
        log_penalty_b = 0.93 # Moderate drop
        
    # Logic: Narrative Sentiment scales xG linearly (+/- 8% max)
    # Adjustment is now guided by the Narrative Agent's own adjustment field if available
    sent_adj_a = nar_a.get('adjustment', (nar_a.get('score', 5) - 5) * 0.02)
    sent_adj_b = nar_b.get('adjustment', (nar_b.get('score', 5) - 5) * 0.02)
    
    final_xg_a = max(0.1, base_xg_a + sent_adj_a)
    final_xg_b = max(0.1, (base_xg_b + sent_adj_b) * log_penalty_b)
    
    # Connect REAL market odds to the Quant Engine
    live_odds = mkt_res.get('best_odds')
    
    logger.info(f"🤖 Quant Engine processing: Adj xG {round(final_xg_a,2)} vs {round(final_xg_b,2)}")
    quant_res = run_quant_engine(final_xg_a, final_xg_b, live_odds, user_budget, home, away)
    
    # 4. Build Optimized God View JSON (Using centralized builder)
    from data.scripts.godview_builder import build_god_view
    
    god_view = build_god_view(
        home_team=home,
        away_team=away,
        match_key=match_key,
        logistics_data=log_res,
        tactics_data=tac_res,
        market_data=mkt_res,
        narrative_home=nar_a,
        narrative_away=nar_b,
        quant_data=quant_res,
        final_xg_home=final_xg_a,
        final_xg_away=final_xg_b,
        base_xg_home=base_xg_a,
        base_xg_away=base_xg_b,
        narrative_adj_home=sent_adj_a,
        narrative_adj_away=sent_adj_b,
        logistics_penalty=log_penalty_b
    )
    
    # [TRANSPARENCY LOG] Print the full God View for admin auditing
    logger.info(f"🔮 GOD VIEW MATRIX [{home} vs {away}]:\n{json.dumps(god_view, indent=2)}")

    
    # 5. Cache for future requests
    SWARM_CACHE[match_key] = {
        "timestamp": god_view["timestamp"],
        "data": god_view
    }
    
    return god_view

async def format_the_closer_report(briefing, num_bets=1):
    """
    Synthesizes the God View into the final Elite Briefing.
    """
    from prompts.system_prompts import CLOSER_PROMPT
    
    # Construct a high-density "Intelligence Summary" for the Closer LLM
    intel_matrix = {
        "quant": f"{briefing['final_xg']['home']} vs {briefing['final_xg']['away']} xG",
        "tactics": briefing['tactics'].get('tactical_analysis', 'Balanced'),
        "logistics": briefing['logistics'].get('summary', 'Neutral'),
        "narrative": f"Home morale: {briefing['narrative']['home'].get('morale')} | Away: {briefing['narrative']['away'].get('morale')}"
    }
    
    formatted_prompt = CLOSER_PROMPT.format(
        match=briefing['match'],
        intelligence=json.dumps(intel_matrix, indent=2)
    )
    
    user_prompt = f"USER REQUESTED: {num_bets} betting play(s).\n\nGOD VIEW DATA:\n{json.dumps(briefing['quant']['top_plays'][:3], indent=2)}"
    
    try:
        return await query_llm(formatted_prompt, user_prompt, config_key="closer", temperature=0.5)
    except Exception as e:
        logger.error(f"The Closer failed: {e}")
        return "Intelligence gathered, but the briefing failed to generate."

async def handle_general_conversation(user_message):
    """
    Redirects to ConversationHandler's specialized logic.
    """
    from prompts.system_prompts import CONVERSATION_ASSISTANT_PROMPT
    try:
        return await query_llm(CONVERSATION_ASSISTANT_PROMPT, user_message, config_key="closer")
    except:
        return "I'm focusing on the World Cup right now. How can I help with your bets?"

from datetime import datetime, timedelta

# ... (Keep existing imports)


def get_todays_matches():
    """
    Returns matches scheduled for 'today' (Real System Time).
    """
    target_date = datetime.now().date()
    
    todays_matches = []
    for m in SCHEDULE:
        # parsed iso format
        match_date = datetime.fromisoformat(m['date_iso']).date()
        if match_date == target_date:
            todays_matches.append(m)
            
    return todays_matches

def get_upcoming_matches():
    """
    Finds matches starting within the next 60-70 minutes (Real System Time).
    """
    now = datetime.now()
    cutoff = now + timedelta(minutes=65)
    
    upcoming = []
    for m in SCHEDULE:
        match_start = datetime.fromisoformat(m['date_iso'])
        if now < match_start <= cutoff:
            upcoming.append(m)
            
    return upcoming

def get_next_scheduled_match():
    """
    Finds the absolute next match in the schedule.
    """
    now = datetime.now()
    next_match = None
    for m in SCHEDULE:
        match_date = datetime.fromisoformat(m['date_iso'])
        if match_date > now:
            next_match = m
            break
            
    if next_match:
        return {
            'home_team': next_match['team_home'],
            'away_team': next_match['team_away'],
            'date_iso': next_match['date_iso'],
            'venue': next_match.get('venue', 'Estadio Azteca, Mexico City'),
            'venue_from': 'MetLife Stadium, East Rutherford' 
        }
    return None

def get_next_match_content():
    """
    Returns only the absolute next match (What the user had before).
    """
    now = datetime.now()
    next_match = None
    for m in SCHEDULE:
        if datetime.fromisoformat(m['date_iso']) > now:
            next_match = m
            break
    
    if next_match:
        time_str = format_to_12hr(next_match['date_iso'])
        return (f"🔮 *Next Up:* {next_match['team_home']} vs {next_match['team_away']}.\n"
                f"They kick off today at {time_str} in the Azteca stadium.\n\n"
                f"Would you like me to analyze this match for you? Just say 'Analyze' or ask about another fixture.")
    return "📅 Looking at the calendar, there are no upcoming matches scheduled right now."

def get_schedule_menu(limit=4):
    """
    Returns a more conversational menu for the next {limit} matches.
    """
    limit = min(limit, 15) # Cap at 15 for WhatsApp readability
    now = datetime.now()
    upcoming = [m for m in SCHEDULE if datetime.fromisoformat(m['date_iso']) > now][:limit]
    
    if not upcoming:
        return "📅 I've checked the schedule, and it looks like there aren't any matches coming up soon."

    msg = f"⚽ *Next {len(upcoming)} Fixtures:*\n\n"
    for m in upcoming:
        dt = datetime.fromisoformat(m['date_iso'])
        time_str = format_to_12hr(m['date_iso'])
        date_str = dt.strftime('%b %d')
        
        # Only say "today" if it's actually today
        day_label = "today" if dt.date() == now.date() else f"on {date_str}"
        msg += f"• *{m['team_home']} vs {m['team_away']}* ({day_label} at {time_str})\n"
    
    msg += "\nWhich one should we look into? Just say 'Analyze' followed by the teams."
    return msg

def get_schedule_brief(days=7):
    """
    Returns the comprehensive 7-day schedule summary.
    """
    now = datetime.now()
    cutoff = now + timedelta(days=days)
    upcoming = [m for m in SCHEDULE if now.date() <= datetime.fromisoformat(m['date_iso']).date() <= cutoff.date()]

    # Fallback: If no matches in the next week, show the next 5 match days regardless of date
    if not upcoming:
        upcoming = [m for m in SCHEDULE if datetime.fromisoformat(m['date_iso']) > now][:15]
        if not upcoming:
            return "📅 It looks like the calendar is clear. No future official matches found in the schedule!"
        msg_prefix = "📅 *Next Scheduled Matches:*\n"
    elif days == 1:
        msg_prefix = "☀️ *Good Morning! GoalMine AI is online.*\n\nHere is today's World Cup lineup:\n"
    else:
        msg_prefix = f"🗓️ *World Cup Schedule (Next {days} Days)*\n"

    grouped = {}
    for m in upcoming:
        date_str = datetime.fromisoformat(m['date_iso']).strftime('%A, %b %d')
        if date_str not in grouped: grouped[date_str] = []
        grouped[date_str].append(m)

    msg = msg_prefix
    for date, matches in grouped.items():
        msg += f"\n📅 *{date}*\n"
        for m in matches:
            time_str = format_to_12hr(m['date_iso'])
            msg += f"• *{m['team_home']} vs {m['team_away']}* (@ {time_str})\n"
    
    msg += "\nTo get a deep-dive analysis on any of these, just say 'Analyze' followed by the teams."
    return msg

def get_match_info_from_selection(selection_idx):
    todays = get_todays_matches()
    if selection_idx < len(todays):
        m = todays[selection_idx]
        return {
            'home_team': m['team_home'],
            'away_team': m['team_away'],
            'date_iso': m['date_iso'],
            'venue': m.get('venue', 'Estadio Azteca, Mexico City'),
            'venue_from': 'MetLife Stadium, East Rutherford' 
        }
    return None


def get_next_matches(limit=3):
    """
    Returns the next {limit} matches as a list of dictionaries.
    Useful for constructing menus/buttons.
    """
    now = datetime.now()
    upcoming = []
    
    # Sort schedule by date to be safe
    sorted_schedule = sorted(SCHEDULE, key=lambda x: datetime.fromisoformat(x['date_iso']))
    
    for m in sorted_schedule:
        match_dt = datetime.fromisoformat(m['date_iso'])
        if match_dt > now:
            upcoming.append(m)
            if len(upcoming) >= limit:
                break
                
    return upcoming

def _normalize_team(name):
    """Normalizes team names for robust matching, handling TBD synonyms."""
    if not name: return ""
    n = name.lower().strip()
    if n in ["tbd", "to be determined", "t.b.d", "unknown", "placeholder"]:
        return "tbd"
    return n

def find_match_by_home_team(team_name):
    """
    Finds a match where the home team matches the provided name (fuzzy).
    """
    if not team_name: return None
    target = _normalize_team(team_name)
    
    for m in SCHEDULE:
        if _normalize_team(m['team_home']) == target or target in m['team_home'].lower():
            return {
                'home_team': m['team_home'],
                'away_team': m['team_away'],
                'date_iso': m['date_iso'],
                'venue': m.get('venue', 'Estadio Azteca, Mexico City'),
                'venue_from': 'MetLife Stadium, East Rutherford' 
            }
    return None

def find_match_by_teams(home_team, away_team):
    """
    Finds a specific match between two teams with TBD normalization.
    """
    if not home_team or not away_team: return None
    
    h = _normalize_team(home_team)
    a = _normalize_team(away_team)
    
    for m in SCHEDULE:
        sched_h = _normalize_team(m['team_home'])
        sched_a = _normalize_team(m['team_away'])
        
        # Check standard and reverse to be helpful
        if (h == sched_h and a == sched_a) or (h == sched_a and a == sched_h):
            return {
                'home_team': m['team_home'],
                'away_team': m['team_away'],
                'date_iso': m['date_iso'],
                'venue': m.get('venue', 'Estadio Azteca, Mexico City'),
                'venue_from': 'MetLife Stadium, East Rutherford' 
            }
    return None

async def extract_match_details_from_text(text):
    """
    Uses LLM to extract teams from natural language.
    e.g. "Tell me about France vs Brazil" -> {'home_team': 'France', ...}
    """
    from prompts.system_prompts import TEAM_EXTRACTION_PROMPT
    user_prompt = f"Extract from: {text}"
    try:
        # Clean response to ensure it's just JSON
        resp = await query_llm(TEAM_EXTRACTION_PROMPT, user_prompt, config_key="extractor", temperature=0.1)
        # Naive json parsing (cleanup markdown code blocks if present)
        resp = resp.replace("```json", "").replace("```", "").strip()
        data = json.loads(resp)
        teams = data.get('teams', [])
        if not teams:
            return None
            
        return {
            "home_team": teams[0] if len(teams) > 0 else None,
            "away_team": teams[1] if len(teams) > 1 else None,
            "venue_from": "MetLife Stadium, East Rutherford",
            "venue_to": "Estadio Azteca, Mexico City"
        }
    except Exception as e:
        logger.error(f"LLM Extraction failed: {e}")
        return None

def validate_match_request(extracted_data):
    """
    Verifies if the extracted teams are actually playing in the official schedule.
    Returns True/False.
    """
    if not extracted_data: return False
    
    target_home = _normalize_team(extracted_data.get('home_team', ''))
    target_away = _normalize_team(extracted_data.get('away_team', ''))
    
    for m in SCHEDULE:
        sched_home = _normalize_team(m['team_home'])
        sched_away = _normalize_team(m['team_away'])
        
        # Check for A vs B
        match_found = (target_home in sched_home or sched_home in target_home) and \
                      (target_away in sched_away or sched_away in target_away)
                      
        # Check for B vs A (Reverse)
        match_found_reverse = (target_home in sched_away or sched_away in target_home) and \
                              (target_away in sched_home or sched_home in target_away)
                              
        if match_found or match_found_reverse:
            # ENRICH DATA: Sync the exact date/venue from official schedule
            extracted_data['date_iso'] = m.get('date_iso')
            extracted_data['venue'] = m.get('venue', 'Estadio Azteca, Mexico City') # Real Venue
            
            if match_found:
                extracted_data['home_team'] = m['team_home']
                extracted_data['away_team'] = m['team_away']
            else:
                # User asked in reverse, normalize to schedule order
                extracted_data['home_team'] = m['team_home']
                extracted_data['away_team'] = m['team_away']
                
            return True
            
    return False
