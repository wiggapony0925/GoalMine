import requests
from typing import List, Dict
from data.scripts.data import REDDIT_CONFIG
from core.log import get_logger

logger = get_logger("API.Reddit")


class RedditScanner:
    """
    Scans Reddit for live sentiments and breaking news WITHOUT API KEYS.
    Uses public JSON endpoints.
    """

    def __init__(self):
        # No keys required for public JSON access!
        self.config = REDDIT_CONFIG
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": self.user_agent, "Accept": "application/json"}
        )
        logger.info("✅ Reddit No-Key Scraper Initialized (Session Mode)")

    async def scan_team_sentiment(self, team_name: str) -> Dict:
        """
        Scans configured subreddits via public .json search endpoints.
        Optimized with multi-subreddit search to reduce request volume.
        """
        headlines = []
        logger.info(f"👽 Reddit Scan initiated for: {team_name}")

        subreddits = self.config.get("subreddits", ["soccer"])
        # Group subreddits to stay within Reddit's length limits for URI
        # r/soccer+worldcup... format reduces requests from 14 to 1 or 2.
        sub_string = "+".join(subreddits)

        # 1. Broad Search (General Sentiment)
        broad_query = f"{team_name} World Cup"
        queries = [broad_query]

        # 2. Targeted Search (Specific Signals)
        keywords_dict = self.config.get("keywords", {})
        if isinstance(keywords_dict, dict):
            all_keywords = [
                item for sublist in keywords_dict.values() for item in sublist
            ]
            import random

            selected = random.sample(all_keywords, min(len(all_keywords), 3))
            targeted_query = f"{team_name} (" + " OR ".join(selected) + ")"
            queries.append(targeted_query)

        try:
            for search_query in queries:
                import urllib.parse

                encoded_query = urllib.parse.quote(search_query)

                # Search across all subreddits at once
                url = f"https://www.reddit.com/r/{sub_string}/search.json?q={encoded_query}&restrict_sr=1&sort=relevance&t=month&limit=25"

                try:
                    import asyncio

                    # Small offset to avoid burst penalty
                    await asyncio.sleep(0.5)

                    response = await asyncio.to_thread(
                        self.session.get, url, timeout=15
                    )

                    if response.status_code == 200:
                        children = response.json().get("data", {}).get("children", [])

                        # Prepare list of tasks and posts for parallel execution
                        p_list = []
                        comment_tasks = []

                        for post in children:
                            p = post.get("data", {})
                            title = p.get("title", "")
                            body = p.get("selftext", "")
                            if (
                                team_name.lower() in title.lower()
                                or team_name.lower() in body.lower()
                            ):
                                p_list.append(p)
                                # Only deep-scan the top 2 overall for speed
                                if len(headlines) + len(comment_tasks) < 2:
                                    comment_tasks.append(
                                        self._fetch_top_comments(p.get("permalink"))
                                    )

                        # Run fetches in parallel
                        all_fetched_comments = (
                            await asyncio.gather(*comment_tasks)
                            if comment_tasks
                            else []
                        )

                        count = 0
                        for i, p in enumerate(p_list):
                            comments = (
                                all_fetched_comments[i]
                                if i < len(all_fetched_comments)
                                else []
                            )
                            headlines.append(
                                {
                                    "title": p.get("title"),
                                    "body": p.get("selftext", "")[:500],
                                    "comments": comments,
                                    "score": p.get("score"),
                                    "url": f"https://reddit.com{p.get('permalink')}",
                                    "subreddit": p.get("subreddit"),
                                }
                            )
                            count += 1
                        logger.info(
                            f"✅ Reddit Scan: Found {count} results for '{search_query}'"
                        )
                    elif response.status_code == 429:
                        logger.warning("Reddit Rate Limit (429) Hit. Throttling back.")
                        await asyncio.sleep(2)
                    else:
                        logger.warning(f"Reddit Search Failed: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Reddit Request Failed: {e}")

            logger.info(
                f"📊 Reddit Summary: Captured {len(headlines)} total evidence points for {team_name}"
            )

            return {
                "source": "reddit_search",
                "status": "success",
                "team": team_name,
                "headlines": headlines[:10],
                "mention_count": len(headlines),
            }
        except Exception as e:
            logger.error(f"Reddit No-Key Scrape Error: {e}")
            return {"source": "reddit", "status": "error", "headlines": []}

    async def _fetch_top_comments(self, permalink: str) -> List[str]:
        """Fetches top 3 comments for a post to gauge 'Public Pulse'."""
        if not permalink:
            return []
        url = f"https://www.reddit.com{permalink}.json?limit=5&depth=1"
        try:
            import asyncio

            response = await asyncio.to_thread(self.session.get, url, timeout=8)
            if response.status_code == 200:
                # Reddit structure: [post_data, comment_data]
                comment_data = response.json()[1]
                children = comment_data.get("data", {}).get("children", [])
                comments = []
                for child in children:
                    body = child.get("data", {}).get("body", "")
                    if body and body not in ["[deleted]", "[removed]"]:
                        comments.append(body[:300])  # Cap each comment length
                return comments[:3]
        except Exception:
            pass
        return []
