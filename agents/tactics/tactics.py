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
        MISSION: Deconstruct the upcoming matchup into a predictive tactical narrative.
        
        INPUT DATA STATUS: {source}
        
        PROTOCOL:
        1. **xG Analysis**: If live data is present, use it. If MISSING, estimate realistic xG based on team tiers.
        2. **Game Flow simulation**: Visualize the 90 minutes. Who holds possession? Who plays the low block?
        3. **Injury Impact**: Call upon your knowledge base for player fitness.
        
        OUTPUT FORMAT (JSON-style text):
        - `dominance_score` (0-100 scale for Home Team)
        - `projected_xg`: {{"home": float, "away": float}}
        - `tactical_summary`: "One sentence on the winning condition."
        - `confidence`: "High" or "Low"
        """
        
        user_prompt = f"""
        MATCHDYA CONTEXT:
        Team A (Home): {team_a_id}
        Team B (Away): {team_b_id}
        
        LIVE STATS PAYLOAD:
        A: {data_a}
        B: {data_b}
        
        Execute Tactical Analysis.
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
