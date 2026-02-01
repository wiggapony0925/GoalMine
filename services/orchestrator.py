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

def load_schedule():
    try:
        with open('data/schedule.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

SCHEDULE = load_schedule()

async def generate_betting_briefing(match_info, user_budget=100):
    """
    Orchestrates the analysis across all agents in PARALLEL.
    NOW USING OO AGENTS.
    """
    home = match_info.get('home_team', 'Team A')
    away = match_info.get('away_team', 'Team B')
    
    logger.info(f"🚀 GoalMine Swarm Activated: {home} vs {away}")
    
    # 1. Parallel Execution of Swarm
    task_log = logistics_agent.analyze(match_info.get('venue_from', 'MetLife_NY'), match_info.get('venue_to', 'Azteca_Mexico'))
    task_tac = tactics_agent.analyze("team_a_id", "team_b_id") 
    task_mkt = market_agent.analyze() # Fetches own data
    task_nar_a = narrative_agent.analyze(home)
    task_nar_b = narrative_agent.analyze(away)
    
    # Execute all
    results = await asyncio.gather(task_log, task_tac, task_mkt, task_nar_a, task_nar_b)
    
    log_res, tac_res, mkt_res, nar_a, nar_b = results
    
    logger.info(f"✅ Logistics: Condition {log_res.get('weather', {}).get('condition', 'Unknown ☁️')}")
    logger.info(f"✅ Tactics: xG {tac_res.get('team_a_xg', 'N/A')} vs {tac_res.get('team_b_xg', 'N/A')}")
    logger.info(f"✅ Market: {len(mkt_res.get('bets', []))} Live Situations Found")
    
    sentiment = nar_a.get('sentiment', 'Neutral')
    logger.info(f"✅ Narrative: {home} Sentiment {sentiment} 📰")
    
    # 2. Quant Engine Synthesis
    base_xg_a = tac_res.get('team_a_xg', 1.5)
    base_xg_b = tac_res.get('team_b_xg', 1.1)
    
    # Adjustments (Simplified logic moved here or kept in quant)
    log_penalty = 0.85 if "High" in log_res.get('recommendation', '') else 1.0
    sent_mult_a = 1 + (nar_a.get('score', 5) - 5) * 0.05
    sent_mult_b = 1 + (nar_b.get('score', 5) - 5) * 0.05
    
    final_xg_a = base_xg_a * sent_mult_a
    final_xg_b = base_xg_b * sent_mult_b * log_penalty
    
    # Mocking odds for quant
    mock_best_odds = {
        'Team_A_Win': {'odds': 2.10, 'platform': 'DraftKings'}, 
        'Draw': {'odds': 3.20, 'platform': 'FanDuel'}, 
        'Team_B_Win': {'odds': 3.50, 'platform': 'BetMGM'}
    }
    
    logger.info(f"🤖 Quant Engine processing: Adj xG {round(final_xg_a,2)} vs {round(final_xg_b,2)}")
    quant_res = run_quant_engine(final_xg_a, final_xg_b, mock_best_odds, user_budget)
    
    return {
        "match": f"{home} vs {away}",
        "logistics": log_res,
        "tactics": tac_res,
        "market": mkt_res,
        "narrative": {"home": nar_a, "away": nar_b},
        "quant": quant_res,
        "final_xg": {"home": round(final_xg_a, 2), "away": round(final_xg_b, 2)}
    }

async def format_the_closer_report(briefing):
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
    You are 'The Closer', a Senior Risk Analyst for a high-stakes World Cup betting syndicate.
    Your goal is to synthesize data from 4 agents (Logistics, Tactics, Market, Narrative) and a Quant Engine.
    
    OUTPUT RULES:
    1. Tone: Professional, Concise, Wall Street/Hedge Fund style. No "Hello", no fluff.
    2. Format:
       🏆 OFFICIAL BET BRIEFING
       ⚽ Match: [Match Name]
       💰 The Play: [Bet Type] @ [Odds] ([Bookmaker])
       
       The Why:
       1. Math: Quant model gives [X]% prob (Edge: [Y]%).
       2. Intel: [One sharp sentence from Narrative/Tactics].
       3. Logistics: [One sharp sentence about travel/weather].
       
       *Confidence: [High/Med]*
       
    3. BET SELECTION STRATEGY:
       - Match the 'Tactical Insight' to the Best Bet Type from your Knowledge Base.
       - E.g., If Tactics says "Mbappe is isolated", suggest "Under 2.5 Goals" or "Mbappe Under 0.5 Goals".
       - E.g., If Logistics says "Home team fatigued", suggest "Away Team Moneyline".
       
    4. VETO RULE: If the Quant Edge is < 2.0% OR 'Narrative' is highly negative, output a "NO BET" warning instead.
    
    KNOWLEDGE BASE (VALID BET TYPES):
    {json.dumps(bet_types_kb, indent=2)}
    """
    
    user_prompt = f"""
    Match: {briefing['match']}
    
    AGENT REPORTS:
    1. Logistics: {briefing['logistics']}
    2. Tactics: {briefing['tactics']}
    3. Market: {briefing['market']}
    4. Narrative: {briefing['narrative']}
    5. QUANT ENGINE RESULT (IMPORTANT): {briefing['quant']}
    
    Generate the final WhatsApp message now.
    """
    
    response = await query_llm(system_prompt, user_prompt, temperature=0.5)
    return response

async def answer_follow_up_question(memory, user_message):
    """
    Handles 'Chat with Data' requests.
    """
    if not memory: return None

    system_prompt = f"""
    You are an Assistant Analyst for GoalMine AI.
    You have access to the full 'God View' data for a specific match.
    
    GOD VIEW DATA:
    {json.dumps(memory, indent=2)}
    
    Your goal is to answer the user's specific question based strictly on this data.
    - If they ask about "xG", look at 'tactics'.
    - If they ask about "weather", look at 'logistics'.
    - If they ask "why", explain the 'quant' or 'narrative' reasoning.
    
    Keep answers short (under 50 words) and factual.
    """
    
    user_prompt = f"User Question: {user_message}"
    
    try:
        response = await query_llm(system_prompt, user_prompt, temperature=0.3)
        return response
    except Exception as e:
        logger.error(f"Q&A Failed: {e}")
        return None

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

def get_morning_brief_content():
    todays = get_todays_matches()
    
    if not todays:
        # Find next upcoming match
        now = datetime.now()
        next_match = None
        for m in SCHEDULE:
            match_date = datetime.fromisoformat(m['date_iso'])
            if match_date > now:
                next_match = m
                break
        
        if next_match:
            date_str = datetime.fromisoformat(next_match['date_iso']).strftime('%A, %b %d')
            return (f"⛔ No World Cup matches today.\n\n"
                    f"🔜 **Next Clash:** {next_match['team_home']} vs {next_match['team_away']}\n"
                    f"📅 {date_str}\n\n"
                    f"Reply 'Analyze to get early intel on this matchup.")
        else:
            return "⛔ No upcoming matches found in the schedule."
        
    msg = "🌞 *Matchday Briefing*\n\n📅 **Today's Menu:**\n"
    for i, m in enumerate(todays):
        time = m['date_iso'].split("T")[1][:5]
        msg += f"{i+1}. {m['team_home']} vs {m['team_away']} @ {time}\n"
    
    msg += "\n🔮 *Action:* Reply with '1' or '2' to activate the Swarm."
    return msg

def get_match_info_from_selection(selection_idx):
    todays = get_todays_matches()
    if selection_idx < len(todays):
        m = todays[selection_idx]
        return {
            'home_team': m['team_home'],
            'away_team': m['team_away'],
            # Start inferring venues or defaulting to a central average if missing
            'venue_from': 'MetLife_NY', 
            'venue_to': 'Azteca_Mexico' 
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
      "venue_from": "MetLife_NY",
      "venue_to": "Azteca_Mexico"
    }
    (If venues are unknown, default venue_from='MetLife_NY' and venue_to='Azteca_Mexico').
    """
    user_prompt = f"Extract from: {text}"
    
    try:
        # Clean response to ensure it's just JSON
        resp = await query_llm(system_prompt, user_prompt, temperature=0.1)
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
            extracted_data['home_team'] = m['team_home'] # Correct formatting
            extracted_data['away_team'] = m['team_away']
            return True
            
    return False
