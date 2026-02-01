import logging
import asyncio
import json
from datetime import datetime
from agents.logistics.logistics import LogisticsAgent
from agents.tactics.tactics import TacticsAgent
from agents.market.market import MarketAgent
from agents.narrative.narrative import NarrativeAgent
from agents.quant.quant import run_quant_engine # Still function based for now
from core.llm import query_llm

logger = logging.getLogger("GoalMine")

# Initialize Agents
logistics_agent = LogisticsAgent()
tactics_agent = TacticsAgent()
market_agent = MarketAgent()
narrative_agent = NarrativeAgent()

def load_json_data(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

SCHEDULE = load_json_data('data/schedule.json')
BET_TYPES = load_json_data('data/bet_types.json')

def format_to_12hr(date_iso):
    """Converts ISO timestamp to 12-hour format: 5:00 PM."""
    dt = datetime.fromisoformat(date_iso)
    return dt.strftime("%I:%M %p").lstrip("0")

async def generate_betting_briefing(match_info, user_budget=100):
    """
    Orchestrates the analysis across all agents in PARALLEL.
    NOW USING OO AGENTS.
    """
    home = match_info.get('home_team', 'Team A')
    away = match_info.get('away_team', 'Team B')
    
    logger.info(f"🚀 GoalMine Swarm Activated: {home} vs {away}")
    
    # 1. Start Agents in Parallel
    task_log = logistics_agent.analyze(
        match_info.get('venue_from', 'MetLife Stadium, East Rutherford'), 
        match_info.get('venue', 'Estadio Azteca, Mexico City')
    )
    task_tac = tactics_agent.analyze(home, away)
    task_mkt = market_agent.analyze(home, away)
    task_nar_a = narrative_agent.analyze(home)
    task_nar_b = narrative_agent.analyze(away)
    
    # Execute all
    results = await asyncio.gather(task_log, task_tac, task_mkt, task_nar_a, task_nar_b)
    
    log_res, tac_res, mkt_res, nar_a, nar_b = results
    
    logger.info(f"✅ Logistics: Fatigue Score {log_res.get('fatigue_score', 'N/A')}")
    logger.info(f"✅ Tactics: xG {tac_res.get('team_a_xg', 'N/A')} vs {tac_res.get('team_b_xg', 'N/A')}")
    logger.info(f"✅ Market: Best Entry found on {mkt_res.get('best_odds', {}).get('Team_A_Win', {}).get('platform', 'N/A')}")
    
    logger.info(f"✅ Narrative Analysis: {home} (Score: {nar_a.get('score', 5)}) vs {away} (Score: {nar_b.get('score', 5)})")
    
    # 2. Extract Data & Apply Multipliers
    base_xg_a = tac_res.get('team_a_xg', 1.5)
    base_xg_b = tac_res.get('team_b_xg', 1.1)
    
    # Logic: If Logistics finds high fatigue for Team B, reduce their xG
    log_penalty = 0.90 if log_res.get('fatigue_score', 0) > 7 else 1.0
    
    # Logic: Narrative Sentiment scales xG linearly (+/- 10%)
    sent_mult_a = 1 + (nar_a.get('score', 5) - 5) * 0.04
    sent_mult_b = 1 + (nar_b.get('score', 5) - 5) * 0.04
    
    final_xg_a = base_xg_a * sent_mult_a
    final_xg_b = base_xg_b * sent_mult_b * log_penalty
    
    # Connect REAL market odds to the Quant Engine
    live_odds = mkt_res.get('best_odds')
    
    logger.info(f"🤖 Quant Engine processing: Adj xG {round(final_xg_a,2)} vs {round(final_xg_b,2)}")
    quant_res = run_quant_engine(final_xg_a, final_xg_b, live_odds, user_budget)
    
    return {
        "match": f"{home} vs {away}",
        "logistics": log_res,
        "tactics": tac_res,
        "market": mkt_res,
        "narrative": {"home": nar_a, "away": nar_b},
        "quant": quant_res,
        "final_xg": {"home": round(final_xg_a, 2), "away": round(final_xg_b, 2)}
    }

async def format_the_closer_report(briefing, num_bets=1):
    """
    PERSONA: The Closer
    The Final Boss. Senior Hedge Fund Manager. 
    Synthesis of all agent data into a final text output.
    """
    # Load Betting Knowledge Base
    try:
        with open('data/bet_types.json', 'r') as f:
            bet_types_kb = json.load(f)
    except FileNotFoundError:
        bet_types_kb = "Standard Bets: Moneyline, Spread, Totals."

    system_prompt = f"""
    # IDENTITY: 'The Closer' (Senior Portfolio Manager)
    
    # MISSION
    You are the final decision-maker for a Billion-Dollar Betting Syndicate. You synthesize intelligence from 4 elite intelligence branches (Logistics, Tactics, Market, Narrative) and the Quant Engine to issue the final 'Capital Deployment' order.

    # REPORTING STRUCTURE (WHATSAPP MARKDOWN)
    
    🏆 *GOALMINE ELITE BRIEFING*
    ⚽ *Fixture:* {{match}}
    
    (Provide Betting Intel here):
    💎 *HIGH-ALPHA OPPORTUNITIES*
    [List up to {num_bets} bets from 'top_plays']
    - *[Selection]* (@ [Odds]) [[Platform]]
    - *Stake:* $[Amount] (Kelly Adjusted)
    
    (If no plays, use):
    ⚠️ *MARKET ADVISORY:* No Edge Detected. capital preservation mode active.
    
    ---
    🧠 *INTELLIGENCE SYNTHESIS*
    
    🎯 *QUANT:* [Combine edge percentage and true probability in 1 sentence].
    ⚔️ *TACTICS:* [Synthesize the mismatch and xG correction in 1 sentence].
    🚛 *LOGISTICS:* [Detail the physiological penalty or home-field environmental edge].
    📰 *NARRATIVE:* [The 'Scoop' and sentiment impact on performance].
    
    ---
    🔥 *CONFIDENCE COEFFICIENT:* [PROBABILITY-WEIGHTED %]
    
    # COMMANDS
    - Use code-like bolding for teams and odds.
    - Keep sentences 'Wall Street Sharp'—dense with information, zero fluff.
    - Always use the agent data provided to justify the capital risk.
    """
    
    user_prompt = f"""
    Match: {briefing['match']}
    
    AGENT REPORTS:
    1. Logistics: {briefing['logistics']}
    2. Tactics: {briefing['tactics']}
    3. Market: {briefing['market']}
    4. Narrative: {briefing['narrative']}
    5. QUANT ENGINE RESULT (IMPORTANT): {briefing['quant']}
    
    The user is looking for {num_bets} bet(s).
    Generate the final WhatsApp message now.
    """
    
    response = await query_llm(system_prompt, user_prompt, config_key="orchestrator")
    return response

async def answer_follow_up_question(memory, user_message, num_bets=1):
    """
    Handles 'Chat with Data' requests.
    """
    if not memory: return None

    system_prompt = f"""
    # IDENTITY: GoalMine Intelligence Liaison (Data Assistant)
    
    # MISSION
    You provide high-speed, accurate answers to specific user queries using the 'God View' intelligence packet provided below. You are the bridge between raw agent data and the user's curiosity.

    # GOD VIEW INTELLIGENCE:
    {json.dumps(memory, indent=2)}

    # ANALYTICAL GUIDELINES:
    1. **DATA-FIRST**: If the data isn't in the 'God View', admit it—don't hallucinate.
    2. **FIELD RETRIEVAL**: 
       - For "xG" or "formations" -> Query **tactics**.
       - For "weather" or "travel fatigue" -> Query **logistics**.
       - For "public opinion" or "news" -> Query **narrative**.
       - For "odds" or "value" -> Query **market** or **quant**.
    3. **RECALCULATION**: If the user provides a budget (e.g., "$100"), use the 'true_probability' from the quant data to suggest a fractional Kelly stake.

    # FORMATTING:
    - Use code-style *WHATSAPP BOLDING* for all entities and numbers.
    - Response must be concise (max 80 words).
    - Tone: Sharp, Analytical, Responsive.
    """
    user_prompt = f"User Question: {user_message}"
    
    try:
        response = await query_llm(system_prompt, user_prompt, config_key="qa_assistant")
        return response
    except Exception as e:
        logger.error(f"Q&A Failed: {e}")
        return None

async def handle_general_conversation(user_message):
    """
    Handles non-betting, non-schedule chats.
    Now enhanced with Tournament & Betting Context.
    """
    # Check for greeting
    if any(w in user_message.lower().strip() for w in ["hi", "hello", "hola", "sup", "hey", "start", "yo"]):
        from core.responses import Responses
        return Responses.get_greeting()

    # Get a snapshot of context for the LLM
    now = datetime.now()
    next_match = None
    for m in SCHEDULE:
        if datetime.fromisoformat(m['date_iso']) > now:
            next_match = m
            break
            
    context_str = f"""
    MATCH CONTEXT:
    Next Match: {next_match['team_home'] if next_match else 'N/A'} vs {next_match['team_away'] if next_match else 'N/A'}
    Tournament Structure: {BET_TYPES.get('meta', {}).get('structure', 'Round robin + knockouts')}
    
    USER QUERY: {user_message}
    """

    system_prompt = """
    You are the 'GoalMine AI' Analyst. You are an expert in World Cup 2026 and sports betting.
    
    MISSION: 
    - Answer greetings and general World Cup questions using your internal knowledge + the provided context.
    - If the user asks about the tournament structure or bets, use the data provided.
    - BE HIGHLY CONVERSATIONAL. Don't use bullet points unless necessary. Feel like a sharp, friendly betting partner.
    - If they want a specific match analysis, gently guide them: "Just say 'Analyze [Team] vs [Team]' and I'll launch the swarm."
    - Keep it concise (under 60 words).
    - Use *bolding* for teams and key terms.
    """
    try:
        return await query_llm(system_prompt, context_str, config_key="narrative") 
    except Exception as e:
        logger.error(f"General Conv Failed: {e}")
        from core.responses import Responses
        return Responses.get_greeting()

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
    now = datetime.now()
    upcoming = [m for m in SCHEDULE if datetime.fromisoformat(m['date_iso']) > now][:limit]
    
    if not upcoming:
        return "📅 I've checked the schedule, and it looks like there aren't any matches coming up soon."

    msg = f"⚽ *Upcoming Fixtures:*\n\n"
    for m in upcoming:
        time_str = format_to_12hr(m['date_iso'])
        msg += f"• *{m['team_home']} vs {m['team_away']}* (today at {time_str})\n"
    
    msg += "\nWhich one should we look into? You can also ask for the 'Full Schedule' if you want to see the whole week."
    return msg

def get_schedule_brief(days=7):
    """
    Returns the comprehensive 7-day schedule summary.
    """
    now = datetime.now()
    cutoff = now + timedelta(days=days)
    upcoming = [m for m in SCHEDULE if now.date() <= datetime.fromisoformat(m['date_iso']).date() <= cutoff.date()]

    if not upcoming:
        return "📅 It looks like the calendar is clear for the next few days. No official matches scheduled yet!"

    grouped = {}
    for m in upcoming:
        date_str = datetime.fromisoformat(m['date_iso']).strftime('%A, %b %d')
        if date_str not in grouped: grouped[date_str] = []
        grouped[date_str].append(m)

    if days == 1:
        msg = "☀️ *Good Morning! GoalMine AI is online.*\n\nHere is today's World Cup lineup:\n"
    else:
        msg = f"🗓️ *World Cup Schedule (Next {days} Days)*\n"

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

async def extract_match_details_from_text(text):
    """
    Uses LLM to extract teams from natural language.
    e.g. "Tell me about France vs Brazil" -> {'home_team': 'France', ...}
    """
    system_prompt = """
    You are a Data Extraction Assistant for World Cup 2026.
    Extract the two football teams mentioned in the user's text.
    
    RULES:
    1. Handle Abbreviations: "Mex" -> "Mexico", "Arg" -> "Argentina", "US/USA" -> "USA".
    2. Correct Spelling: "Braizl" -> "Brazil".
    3. Return FULL English Country Names.
    
    Also, identify the likely 'Venue' if mentioned, otherwise default to 'Unknown'.
    For World Cup 2026, valid venues are US/Mexico/Canada cities.
    
    Output JSON ONLY:
    {
      "home_team": "Name",
      "away_team": "Name",
      "venue_from": "MetLife Stadium, East Rutherford",
      "venue_to": "Estadio Azteca, Mexico City"
    }
    (If venues are unknown, default venue_from='MetLife Stadium, East Rutherford' and venue_to='Estadio Azteca, Mexico City').
    """
    user_prompt = f"Extract from: {text}"
    
    try:
        # Clean response to ensure it's just JSON
        resp = await query_llm(system_prompt, user_prompt, config_key="extractor", temperature=0.1)
        # Naive json parsing (cleanup markdown code blocks if present)
        resp = resp.replace("```json", "").replace("```", "").strip()
        data = json.loads(resp)
        return data
    except Exception as e:
        logger.error(f"LLM Extraction failed: {e}")
        return None

def validate_match_request(extracted_data):
    """
    Verifies if the extracted teams are actually playing in the official schedule.
    Returns True/False.
    """
    if not extracted_data: return False
    
    target_home = extracted_data.get('home_team', '').lower()
    target_away = extracted_data.get('away_team', '').lower()
    
    for m in SCHEDULE:
        sched_home = m['team_home'].lower()
        sched_away = m['team_away'].lower()
        
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
