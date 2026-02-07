import asyncio
import json
from core.log import get_logger
from core.initializer.llm import query_llm
from .api.google_news import fetch_headlines
from .api.reddit_api import RedditScanner
from .api.free_sports import fetch_team_wikipedia_summary

logger = get_logger("Narrative")


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
        injury_articles = await asyncio.to_thread(
            fetch_headlines, team_name, query_type="injury", region="GB"
        )
        # Scan for psychological/locker room drama
        drama_articles = await asyncio.to_thread(
            fetch_headlines, team_name, query_type="narrative", region="GB"
        )

        all_articles = injury_articles + drama_articles

        # 2. Scan Reddit
        reddit_data = await self.reddit.scan_team_sentiment(team_name)

        # 3. Deep Scan top News Link ('Link Look-In' Feature)
        deep_content = None
        if all_articles:
            from .api.web_scraper import extract_article_text

            # Scan the top article from EITHER category to get deep context
            top_link = all_articles[0].get("link")
            deep_content = await asyncio.to_thread(extract_article_text, top_link)

        # 4. Wikipedia context for historical/background enrichment
        wiki_data = await asyncio.to_thread(
            fetch_team_wikipedia_summary, team_name
        )

        source = "GOOGLE NEWS (GB) + REDDIT + WIKIPEDIA (DEEP_SCAN_ENABLED)"
        if not all_articles and not reddit_data.get("headlines"):
            source = "WIKIPEDIA + INTERNAL_ARCHIVE_RECALL"

        # Combine Evidence
        news_entries = []
        for i, a in enumerate(all_articles):
            entry = f"- [NEWS ({a['type'].upper()})] {a['title']}"
            if i == 0 and deep_content:
                entry += f" | DEEP_ANALYSIS: {deep_content[:800]}"  # Feed first 800 chars of article
            news_entries.append(entry)

        reddit_entries = []
        for h in reddit_data.get("headlines", []):
            sub_info = f" (r/{h['subreddit']})" if h.get("subreddit") else ""
            entry = f"- [REDDIT{sub_info}] TITLE: {h['title']}"
            if h.get("body"):
                entry += f" | CONTENT: {h['body'][:400]}"
            if h.get("comments"):
                comment_text = " // ".join(h["comments"])
                entry += f" | TOP_COMMENTS: {comment_text}"
            reddit_entries.append(entry)

        # Wikipedia background context
        wiki_entries = []
        wiki_summary = wiki_data.get("summary", "")
        if wiki_summary:
            wiki_entries.append(
                f"- [WIKIPEDIA] BACKGROUND: {wiki_summary[:600]}"
            )

        evidence = (
            "\n".join(news_entries + reddit_entries + wiki_entries)
            or "No live data. Analyze based on historical reputation."
        )

        # [DETAILED LOGGING] Raw Data Dump (Developer Only)
        logger.debug(
            f"📰 GOOGLE RAW ({team_name}): {json.dumps(all_articles, indent=2)}"
        )
        logger.debug(
            f"👽 REDDIT RAW ({team_name}): {json.dumps(reddit_data, indent=2)}"
        )
        if deep_content:
            logger.debug(f"🕵️ DEEP SCAN CONTENT ({team_name}): {deep_content[:500]}...")

        from prompts.system_prompts import NARRATIVE_PROMPT

        user_prompt = (
            f"Target Team: {team_name}\n\nEvidence:\n{evidence}\n\nInvestigate."
        )

        llm_response = await query_llm(
            NARRATIVE_PROMPT.format(
                team_name=team_name,
                opponent_name="Opponent",
                stage="Group Stage",
                source=source,
            ),
            user_prompt,
            config_key="narrative",
            json_mode=True,
        )

        try:
            analysis_json = json.loads(llm_response)
        except Exception:
            analysis_json = {
                "sentiment_score": 5.0,
                "headline_scoop": "Narrative Agent failed to parse data.",
                "morale_impact": "Stable",
                "narrative_adjustment": 0.0,
                "insider_summary": llm_response[:200],
            }

        return {
            "branch": self.branch_name,
            "source": source,
            "team": team_name,
            "score": analysis_json.get("sentiment_score", 5.0),
            "morale": analysis_json.get("morale_impact", "Stable"),
            "adjustment": analysis_json.get("narrative_adjustment", 0.0),
            "headline": analysis_json.get("headline_scoop", "N/A"),
            "summary": analysis_json.get("insider_summary", "N/A"),
            "mention_count": reddit_data.get(
                "mention_count", 0
            ),  # Pass through to logger
            "raw_analysis": analysis_json,
        }
