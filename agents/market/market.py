from core.llm import query_llm
from .the_odds_api import fetch_latest_odds

class MarketAgent:
    """
    PERSONA: Market Sniper AI
    ROLE: Identifies discrepancies, arbitrage, and 'trap' lines in sportsbook odds.
    """
    def __init__(self):
        self.branch_name = "market_sniper"

    async def analyze(self, odds_data=None):
        # If orchestrator didn't pass data, fetch it now using the helper
        if odds_data is None:
            odds_data = fetch_latest_odds()

        if isinstance(odds_data, dict) and "error" in odds_data:
            return odds_data

        system_prompt = """
        You are a professional Sports Better (Sharp).
        Analyze the provided odds from various bookmakers (DraftKings, FanDuel, etc.).
        Identify:
        1. The Best Price for each outcome (Line Shopping).
        2. Any 'Implied Probability' anomalies.
        3. Recommended Bookmaker for this specific match.
        """
        
        user_prompt = f"Odds Data: {str(odds_data)[:2000]}" # Truncate to avoid context limit
        
        llm_analysis = await query_llm(system_prompt, user_prompt)
        
        return {
            "branch": self.branch_name,
            "analysis": llm_analysis,
            "best_books": "See detailed analysis."
        }
