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
        MISSION: Deconstruct the matchup using Live Data, Starting Lineups, and Coaching styles.
        
        INPUT DATA STATUS: {source}
        
        PROTOCOL:
        1. **Live State Check**: Look at 'live_status', 'minute', and 'score'.
        2. **Lineup Analysis**: Look at 'lineup'. Are key stars starting? Any tactical surprises?
        3. **Coaching**: Does the 'coach' have a specific reputation (Park the bus vs High Press)?
        4. **State Logic**:
           - IF "Pre-Match": Analyze form and squad.
           - IF "HT" (Half-Time): Analyze the first half score. Identify "Second Half Comeback" or "Next Goal" shifts.
           
        OUTPUT FORMAT:
        - `game_state`: Current Status
        - `lineup_impact`: "High/Medium/Low" + reasoning.
        - `tactical_summary`: Narrative analysis of how the lineups match up.
        - `coaching_edge`: Which manager has the tactical advantage.
        """
        
        user_prompt = f"""
        MATCH CONTEXT:
        Team A (Home): {team_a_id}
        Team B (Away): {team_b_id}
        
        LIVE DATA A: {data_a}
        LIVE DATA B: {data_b}
        """
        
        response = await query_llm(system_prompt.format(source=data_source), user_prompt)
        
        return {
            'branch': self.branch_name,
            'source': data_source,
            'tactical_analysis': response,
            'lineups': {
                'home': data_a.get('lineup', []) if data_a else [],
                'away': data_b.get('lineup', []) if data_b else []
            }
        }
