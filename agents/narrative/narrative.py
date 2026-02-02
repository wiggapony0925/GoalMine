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
        # 1. Fetch Google News Headlines (Dual-Scan Strategy)
        # Scan for physical fitness/injuries
        injury_articles = fetch_headlines(team_name, query_type="injury", region="GB")
        # Scan for psychological/locker room drama
        drama_articles = fetch_headlines(team_name, query_type="narrative", region="GB")
        
        all_articles = injury_articles + drama_articles
        
        # 2. Scan Reddit
        reddit_data = await self.reddit.scan_team_sentiment(team_name)
        
        # 3. Deep Scan top News Link (New 'Link Look-In' Feature)
        deep_content = None
        if all_articles:
            from .api.web_scraper import extract_article_text
            # Scan the top article from EITHER category to get deep context
            top_link = all_articles[0].get('link')
            deep_content = extract_article_text(top_link)

        source = "GOOGLE NEWS (GB) + REDDIT (DEEP_SCAN_ENABLED)"
        if not all_articles and not reddit_data.get('headlines'):
             source = "INTERNAL_ARCHIVE_RECALL"

        # Combine Evidence
        news_entries = []
        for i, a in enumerate(all_articles):
            entry = f"- [NEWS ({a['type'].upper()})] {a['title']}"
            if i == 0 and deep_content:
                entry += f" | DEEP_ANALYSIS: {deep_content[:800]}" # Feed first 800 chars of article
            news_entries.append(entry)

        reddit_entries = []
        for h in reddit_data.get('headlines', []):
            entry = f"- [REDDIT] TITLE: {h['title']}"
            if h.get('body'):
                entry += f" | CONTENT: {h['body'][:400]}"
            if h.get('comments'):
                comment_text = " // ".join(h['comments'])
                entry += f" | TOP_COMMENTS: {comment_text}"
            reddit_entries.append(entry)
        
        evidence = "\n".join(news_entries + reddit_entries) or "No live data. Analyze based on historical reputation."
        
        from prompts.system_prompts import NARRATIVE_PROMPT
        
        user_prompt = f"Target Team: {team_name}\n\nEvidence:\n{evidence}\n\nInvestigate."
        
        llm_analysis = await query_llm(NARRATIVE_PROMPT.format(source=source), user_prompt, config_key="narrative")
        
        score = 5
        if "positive" in llm_analysis.lower() or "invincible" in llm_analysis.lower(): score = 8
        if "toxic" in llm_analysis.lower() or "crisis" in llm_analysis.lower(): score = 3
        
        return {
            "branch": self.branch_name,
            "source": source,
            "team": team_name,
            "score": score,
            "articles_scanned": len(all_articles),
            "summary": llm_analysis[:300] + "..." 
        }
