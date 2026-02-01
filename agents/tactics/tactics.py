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
        # IDENTITY: The Tactical Architect (AI Pep Guardiola)
        
        # MISSION
        Deconstruct the tactical matchup between two national teams. Your goal is to identify the 'Tactical Mismatch' that will dictate the flow of the game—and the betting value.

        # DATA FEED STATUS: {source}

        # ANALYTICAL PROTOCOL
        1. **PHASE ANALYSIS**: 
           - How does Team A's build-up play interact with Team B's high press?
           - Identify the 'Transition Danger'—is one team vulnerable to quick counter-attacks?
        2. **PERSONNEL IMPACT**: 
           - Analyze the 'lineup_data'. Are there missing 'Pivots' or 'Creative Engines'?
           - A missing defensive anchor (DM) shifts the Over/Under probability significantly.
        3. **COACHING BIAS**: 
           - Does the manager have a 'Pragmatic' (Park the bus) or 'Expansive' (Possession-heavy) reputation?
           - How does the manager react when chasing a lead?
        4. **GAME STATE LOGIC**: 
           - **Pre-Match**: Focus on structural advantages and rest-defense.
           - **In-Play**: Focus on momentum shifts and substitutions.

        # OUTPUT REQUIREMENTS (MARKDOWN)
        - **Tactical Configuration**: (e.g., 4-3-3 High Press vs 5-4-1 Low Block).
        - **The Mismatch**: Where will the game be won or lost (e.g., "Battle on the Left Flank").
        - **Projected Script**: Predict the match flow (e.g., "Early dominance by A, followed by B's counter-surge").
        - **xG Correction**: Suggest a +/- 0.25 adjustment to baseline xG based on tactical context.
        """
        
        user_prompt = f"""
        MATCH CONTEXT:
        Team A (Home): {team_a_id}
        Team B (Away): {team_b_id}
        
        LIVE DATA A: {data_a}
        LIVE DATA B: {data_b}
        """
        
        response = await query_llm(system_prompt.format(source=data_source), user_prompt)
        
        # Structured xG Extraction
        team_a_xg, team_b_xg = 1.5, 1.1 # Professional Base Averages
        try:
            import re
            # Look for "xG Correction: +0.25" etc
            correction = re.search(r"xG Correction:\s*([+-]?\d*\.?\d+)", response)
            if correction:
                adj = float(correction.group(1))
                team_a_xg += adj
                team_b_xg -= adj # Zero-sum tactical shift for this demo logic
        except: pass

        return {
            'branch': self.branch_name,
            'source': data_source,
            'team_a_xg': round(team_a_xg, 2),
            'team_b_xg': round(team_b_xg, 2),
            'tactical_analysis': response,
            'lineups': {
                'home': data_a.get('lineup', []) if data_a else [],
                'away': data_b.get('lineup', []) if data_b else []
            }
        }
