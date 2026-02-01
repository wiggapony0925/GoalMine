from core.llm import query_llm
from .api.google_news import fetch_headlines
from .api.reddit_api import RedditScanner

class NarrativeAgent:
    """
    PERSONA: Narrative Agent (AI)
    ROLE: Scrapes news and Reddit to determine team morale/sentiment.
    """
    def __init__(self):
        self.branch_name = "narrative"
        self.reddit = RedditScanner()

    async def analyze(self, team_name):
        # 1. Fetch Google News Headlines
        articles = fetch_headlines(team_name)
        
        # 2. Scan Reddit
        reddit_data = await self.reddit.scan_team_sentiment(team_name)
        reddit_headlines = [h['title'] for h in reddit_data.get('headlines', [])]
        
        source = "NEWS + REDDIT"
        if not articles and not reddit_headlines:
             source = "INTERNAL_ARCHIVE_RECALL"

        # Combine Evidence
        news_text = "\n".join([f"- [NEWS] {a['title']}" for a in articles]) if articles else ""
        social_text = "\n".join([f"- [REDDIT] {h}" for h in reddit_headlines]) if reddit_headlines else ""
        
        evidence = f"{news_text}\n{social_text}" or "No live data. Analyze based on historical reputation."
        
        system_prompt = """
        # IDENTITY: The Narrative Scout (AI Fabrizio Romano)
        
        # MISSION
        Uncover the hidden psychological edges—'The Human Factor'. You analyze news, Reddit, and social signals to find morale spikes or locker room crises that the numbers can't see.

        # EVIDENCE SOURCE: {source}

        # INTELLIGENCE TIERS
        1. **MORALE & MOMENTUM**: 
           - Is the team in 'Crisis Mode' (manager under fire, fans protesting) or 'Unstoppable Momentum' (national pride, key stars returning)?
        2. **THE 'DISTRACTION' FACTOR**: 
           - Look for off-field scandals, contract disputes, or travel complaints. 
           - High-profile distractions = -5% focus penalty for the favorite.
        3. **PUBLIC SENTIMENT (Reddit/Social)**: 
           - Is the public 'Irrational'? (e.g., Over-hyping a team because of one star player).
           - Identify 'Quiet Confidence' vs 'Panic'.

        # OUTPUT REQUIREMENTS (MARKDOWN)
        - **Sentiment Score**: (0.0 to 10.0 | Critical to Invincible).
        - **The Scoop**: A 2-sentence 'insider' style summary of the most impactful narrative.
        - **Red Flags**: List any specific 'Narrative Landmines' (Injuries, Beefs, Scandals).
        - **Narrative Multiplier**: Suggest if the team will 'Overperform' or 'Internalize Pressure'.
        """
        
        user_prompt = f"Target Team: {team_name}\n\nEvidence:\n{evidence}\n\nInvestigate."
        
        llm_analysis = await query_llm(system_prompt.format(source=source), user_prompt, config_key="narrative")
        
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
