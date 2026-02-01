from core.llm import query_llm
from .api.the_odds_api import fetch_latest_odds

class MarketAgent:
    """
    PERSONA: Market Sniper AI
    ROLE: Identifies discrepancies, arbitrage, and 'trap' lines in sportsbook odds.
    """
    def __init__(self):
        self.branch_name = "market_sniper"

    async def analyze(self, odds_data=None):
        data_source = "LIVE_ODDS_API"
        
        if odds_data is None:
            try:
                odds_data = fetch_latest_odds()
            except Exception:
                odds_data = {"error": "API Failure"}
        
        if isinstance(odds_data, dict) and "error" in odds_data:
            data_source = "VEGAS_ESTIMATOR_FALLBACK"

        system_prompt = """
        IDENTITY: You are a 'Vegas Sharp'—a legendary sports bettor who moves lines.
        MISSION: Find value. If the Feed is LIVE, find Arbitrage. If the Feed is DOWN, ESTIMATE the true line yourself.
        
        INPUT STATUS: {source}
        
        PROTOCOL:
        1. **Live Analysis**: If odds exist, identify the specific book (DK/FanDuel) with the best price.
        2. **Fallback Analysis**: If odds are missing, use your internal probability model to SET the line.
        
        OUTPUT (Compact Betting Notation):
        - Best Home Odds: (Decimal)
        - Best Away Odds: (Decimal)
        - Implied Probability Gap: (Does the market underestimate the favorite?)
        - Verdict: "Bet Home", "Bet Away", or "Stay Away"
        """
        
        user_prompt = f"Available Odds Data: {str(odds_data)[:1500]}" 
        
        llm_analysis = await query_llm(system_prompt.format(source=data_source), user_prompt)
        
        return {
            "branch": self.branch_name,
            "data_source": data_source,
            "analysis": llm_analysis,
            "best_books": "Analysis pending in summary"
        }
