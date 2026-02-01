from core.llm import query_llm
from .sportmonks import fetch_team_stats

class TacticsAgent:
    """
    PERSONA: Lead Tactical Analyst (AI)
    ROLE: Examination of Expected Goals (xG), injury impact, and tactical form.
    """
    def __init__(self):
        self.branch_name = "tactics"

    async def analyze(self, team_a_id, team_b_id):
        # Fetch stats using the partnered API
        data_a = fetch_team_stats(team_a_id)
        data_b = fetch_team_stats(team_b_id)
        
        system_prompt = """
        You are a World Class Football Tactician (like Pep Guardiola).
        Analyze the stats provided for two teams.
        1. Compare xG (Expected Goals) to determine offensive dominance.
        2. Assess the impact of any listed injuries.
        3. Predict the 'flow' of the game (e.g., Team A dominates possession, Team B counters).
        """
        
        user_prompt = f"""
        Team A Stats: {data_a}
        Team B Stats: {data_b}
        """
        
        llm_tactic = await query_llm(system_prompt, user_prompt)
        
        # Calculate crude xG numbers for the Quant engine to still use
        xg_a = data_a['xG_for']
        xg_b = data_b['xG_for']

        return {
            'branch': self.branch_name,
            'team_a_xg': round(xg_a, 2),
            'team_b_xg': round(xg_b, 2),
            'tactical_analysis': llm_tactic,
            'recommendation': llm_tactic[:150] + "..."
        }
