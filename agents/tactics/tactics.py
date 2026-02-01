from core.llm import query_llm
from .api.sportmonks import fetch_team_stats

class TacticsAgent:
    """
    PERSONA: Lead Tactical Analyst (AI)
    ROLE: Examination of Expected Goals (xG), injury impact, and tactical form.
    """
    def __init__(self):
        self.branch_name = "tactics"

    async def analyze(self, team_a_id, team_b_id):
        data_a, data_b = None, None
        data_source = "LIVE_API"
        
        try:
            data_a = fetch_team_stats(team_a_id)
            data_b = fetch_team_stats(team_b_id)
        except Exception as e:
            data_source = "INTERNAL_KNOWLEDGE_FALLBACK"

        system_prompt = """
        IDENTITY: You are the 'Pep Guardiola' of Betting Analytics—a World-Class Tactical Savant.
        MISSION: Deconstruct the matchup.
        
        INPUT DATA STATUS: {source}
        
        PROTOCOL:
        1. **Live State Check**: Look at 'live_status', 'minute', and 'score'.
           - IF "Pre-Match": Analyze form and squad.
           - IF "LIVE" (e.g. 34'): Report the game state (e.g., "France leading 1-0, dominatng possession"). DO NOT SUGEST LIVE BETS.
           - IF "HT" (Half-Time): **CRITICAL**. Analyze the first half score. Is the favorite losing? Suggest a "Second Half Comeback" bet or "Next Goal" insight.
           
        2. **Form & Squad**: Check 'recent_form' and 'roster_sample' for context.
        
        OUTPUT FORMAT (JSON-style text):
        - `game_state`: "Pre-Match", "Live (34')", or "Half-Time"
        - `current_score`: "1-0"
        - `tactical_summary`: "Analysis of the flow."
        - `ht_recommendation`: (Only if HT) "Bet on Over 1.5 Goals"
        """
        
        user_prompt = f"""
        MATCH CONTEXT:
        Team A (Home): {team_a_id}
        Team B (Away): {team_b_id}
        
        LIVE DATA A: {data_a}
        LIVE DATA B: {data_b}
        
        """
        
        response = await query_llm(system_prompt.format(source=data_source), user_prompt)
        
        xg_a, xg_b = 1.3, 1.1 
        if "projected_xg" in response:
            pass

        return {
            'branch': self.branch_name,
            'source': data_source,
            'tactical_analysis': response,
            'raw_xg_estimates': {"home": xg_a, "away": xg_b}
        }
