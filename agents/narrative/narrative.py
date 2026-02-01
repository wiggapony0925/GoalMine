from core.llm import query_llm
from .news_api import fetch_headlines

class NarrativeAgent:
    """
    PERSONA: Narrative Agent (AI)
    ROLE: Scrapes news and uses LLM to determine team morale/sentiment.
    """
    def __init__(self):
        self.branch_name = "narrative"

    async def analyze(self, team_name):
        articles = fetch_headlines(team_name)
        if not articles:
            return {"sentiment": "neutral", "score": 5, "summary": "No recent news found."}

        # Prepare context for LLM
        headlines_text = "\n".join([f"- {a['title']}: {a['description']}" for a in articles])
        
        system_prompt = """
        You are the Narrative Agent for a high-stakes betting syndicate.
        Analyze the following news headlines for a soccer team.
        Determine the 'Sentiment Score' (0=Crisis/Toxic, 5=Neutral, 10=Peak Morale/Invincible).
        Identify any 'Red Flags' (Injuries, Scandals, Manager Friction).
        Return a structured summary.
        """
        
        user_prompt = f"Team: {team_name}\n\nNews Headlines:\n{headlines_text}\n\nAnalysis:"
        
        # AI Analysis
        llm_analysis = await query_llm(system_prompt, user_prompt)
        
        # Simple parsing (In prod, ask for JSON response format)
        score = 5
        if "positive" in llm_analysis.lower(): score = 7
        if "crisis" in llm_analysis.lower() or "injury" in llm_analysis.lower(): score = 3
        if "peak" in llm_analysis.lower() or "invincible" in llm_analysis.lower(): score = 9
        
        return {
            "branch": self.branch_name,
            "team": team_name,
            "score": score,
            "summary": llm_analysis[:300] + "..." # Truncate for brevity
        }
