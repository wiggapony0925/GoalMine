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

logger = logging.getLogger(__name__)

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
    
    logger.info(f"Starting Swarm for {home} vs {away}...")
    
    # 1. Parallel Execution of Swarm
    task_log = logistics_agent.analyze(match_info.get('venue_from', 'MetLife_NY'), match_info.get('venue_to', 'Azteca_Mexico'))
    task_tac = tactics_agent.analyze("team_a_id", "team_b_id") 
    task_mkt = market_agent.analyze() # Fetches own data
    task_nar_a = narrative_agent.analyze(home)
    task_nar_b = narrative_agent.analyze(away)
    
    # Execute all
    results = await asyncio.gather(task_log, task_tac, task_mkt, task_nar_a, task_nar_b)
    
    log_res, tac_res, mkt_res, nar_a, nar_b = results
    
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
    system_prompt = """
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
       
    3. VETO RULE: If the Quant Edge is < 2.0% OR 'Narrative' is highly negative, output a "NO BET" warning instead.
    
    KNOWLEDGE BASE:
    - You know standard bets: Moneyline, Spread (Asian Handicap), Totals (Over/Under).
    - You represent 'GoalMine' engine.
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
        return None
        
    msg = "🌞 World Cup Daily Brief\nToday's Matches:\n\n"
    for i, m in enumerate(todays):
        time = m['date_iso'].split("T")[1][:5]
        msg += f"{i+1}. {m['team_home']} vs {m['team_away']} ({time})\n"
    msg += "\nReply with '1' or '2' to get an edge before kick-off!"
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
    You are a Data Extraction Assistant.
    Extract the two football teams mentioned in the user's text.
    Also, identify the likely 'Venue' if mentioned, otherwise default to 'Unknown'.
    For World Cup 2026, valid venues are US/Mexico/Canada cities.
    
    Output JSON ONLY:
    {
      "home_team": "Name",
      "away_team": "Name",
      "venue_from": "MetLife_NY",
      "venue_to": "Azteca_Mexico"
    }
    (If venues are unknown, default venue_from='MetLife_NY' and venue_to='Azteca_Mexico' for the logistics engine to work).
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
