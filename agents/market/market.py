from core.llm import query_llm
from .api.the_odds_api import fetch_latest_odds

class MarketAgent:
    """
    PERSONA: Market Sniper AI
    ROLE: Identifies discrepancies, arbitrage, and 'trap' lines in sportsbook odds.
    """
    def __init__(self):
        self.branch_name = "market_sniper"

    async def analyze(self, team_a, team_b, odds_data=None):
        data_source = "LIVE_ODDS_API"
        
        if odds_data is None:
            try:
                odds_data = fetch_latest_odds()
            except Exception:
                odds_data = {"error": "API Failure"}
        
        extracted_odds = self._extract_best_odds(team_a, team_b, odds_data)
        
        if not extracted_odds or (isinstance(odds_data, dict) and "error" in odds_data):
            data_source = "VEGAS_ESTIMATOR_FALLBACK"

        system_prompt = """
        # IDENTITY: The Market Sniper (Vegas Sharp AI)
        
        # MISSION
        Identify market inefficiencies, line movements, and asymmetric risk/reward opportunities across global sportsbooks. You don't just read odds; you find where the books are exposed.

        # DATA STREAM: {source}

        # SNIPER PROTOCOLS
        1. **IMPLIED vs TRUE PROBABILITY**: 
           - Convert decimal odds to implied probabilities. 
           - Compare against the 'GoalMine Quant Model' outputs. Any deviation > 3% is a 'Vulnerability'.
        2. **STEAM & FADE**: 
           - Identify 'Steam Moves' (rapid line changes indicating sharp money). 
           - Suggest when to 'Fade the Public' (betting against the crowd on inflated lines).
        3. **BOOKMAKER EXPOSURE**: 
           - Which book (DraftKings, FanDuel, BetMGM) offers the 'Best-in-Market' price?
           - Identify 'Trap Lines'—odds that look too good to be true based on the narrative.

        # OUTPUT REQUIREMENTS (MARKDOWN)
        - **Sharp View**: 1-sentence assessment of the current line (e.g., "Market Overvaluing the Favorite").
        - **Best Entry**: Specific platform and decimal odds for maximum ROI.
        - **Value Grade**: (A+ to F based on the mathematical edge).
        - **Risk Warning**: Identify 'Liability' factors (e.g., "Public heavy on Over 2.5, line potentially inflated").
        """
        
        user_prompt = f"Target Match: {team_a} vs {team_b}\nAvailable Odds Data: {str(odds_data)[:1500]}" 
        
        llm_analysis = await query_llm(system_prompt.format(source=data_source), user_prompt)
        
        return {
            "branch": self.branch_name,
            "data_source": data_source,
            "analysis": llm_analysis,
            "best_odds": extracted_odds or self._get_default_odds() 
        }

    def _extract_best_odds(self, team_a, team_b, odds_data):
        """Helper to find the best market prices for specific teams."""
        if not isinstance(odds_data, list): return None
        
        best = {'Team_A_Win': {'odds': 0}, 'Draw': {'odds': 0}, 'Team_B_Win': {'odds': 0}}
        
        for event in odds_data:
            home = event.get('home_team', '')
            away = event.get('away_team', '')
            
            # Simple fuzzy match for names
            if team_a.lower() in home.lower() and team_b.lower() in away.lower():
                for book in event.get('bookmakers', []):
                    for market in book.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                name = outcome['name']
                                price = outcome['price']
                                if name == home:
                                    if price > best['Team_A_Win']['odds']:
                                        best['Team_A_Win'] = {'odds': price, 'platform': book['title']}
                                elif name == away:
                                    if price > best['Team_B_Win']['odds']:
                                        best['Team_B_Win'] = {'odds': price, 'platform': book['title']}
                                else:
                                    if price > best['Draw']['odds']:
                                        best['Draw'] = {'odds': price, 'platform': book['title']}
                return best
        return None

    def _get_default_odds(self):
        return {
            'Team_A_Win': {'odds': 2.10, 'platform': 'Market_Average'},
            'Draw': {'odds': 3.20, 'platform': 'Market_Average'},
            'Team_B_Win': {'odds': 3.80, 'platform': 'Market_Average'}
        }
