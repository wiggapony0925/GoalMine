from core.llm import query_llm
from .api.google_news import fetch_headlines

class NarrativeAgent:
    """
    PERSONA: Narrative Agent (AI)
    ROLE: Scrapes news and uses LLM to determine team morale/sentiment.
    """
    def __init__(self):
        self.branch_name = "narrative"

    async def analyze(self, team_name):
        articles = fetch_headlines(team_name)
        source = "LIVE_RSS_FEED"
        
        if not articles:
            source = "INTERNAL_ARCHIVE_RECALL"

        headlines_text = "\n".join([f"- {a['title']}" for a in articles]) if articles else "No live headlines available. Retrieve known status."
        
        system_prompt = """
        IDENTITY: You are a 'Top Investigative Sports Journalist' (like Fabrizio Romano).
        MISSION: Uncover the hidden psychological edges—Morale, Scandals, Locker Room Friction.
        
        SOURCE: {source}
        
        PROTOCOL:
        1. **Sentiment Analysis**: Score from 0 (Toxic/Crisis) to 10 (Invincible).
        2. **Red Flags**: Explicitly list any injuries, manager disputes, or fatigue rumors.
        3. **Context**: Rely on the team's historical reputation and recent form.
        
        OUTPUT:
        - Sentiment Score (float)
        - "The Scoop" (A 2-sentence insider summary)
        """
        
        user_prompt = f"Target Team: {team_name}\n\nEvidence:\n{headlines_text}\n\nInvestigate."
        
        llm_analysis = await query_llm(system_prompt.format(source=source), user_prompt)
        
        score = 5
        if "positive" in llm_analysis.lower() or "invincible" in llm_analysis.lower(): score = 8
        if "toxic" in llm_analysis.lower() or "crisis" in llm_analysis.lower(): score = 3
        
        return {
            "branch": self.branch_name,
            "source": source,
            "team": team_name,
            "score": score,
            "articles_scanned": len(articles) if articles else 0,
            "summary": llm_analysis[:300] + "..." 
        }
