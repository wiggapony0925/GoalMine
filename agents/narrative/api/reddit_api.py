import os
import json
import logging
import requests
from typing import List, Dict
from data.scripts.data import REDDIT_CONFIG

logger = logging.getLogger("GoalMine")

class RedditScanner:
    """
    Scans Reddit for live sentiments and breaking news WITHOUT API KEYS.
    Uses public JSON endpoints.
    """
    def __init__(self):
        # No keys required for public JSON access!
        self.config = REDDIT_CONFIG
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        logger.info("✅ Reddit No-Key Scraper Initialized")

    async def scan_team_sentiment(self, team_name: str) -> Dict:
        """
        Scans configured subreddits via public .json search endpoints.
        """
        headlines = []
        
        # 1. Flatten keywords from structured config
        keywords_dict = self.config.get("keywords", {})
        if isinstance(keywords_dict, dict):
            all_keywords = [item for sublist in keywords_dict.values() for item in sublist]
        else:
            all_keywords = keywords_dict # Fallback if already a list

        # 2. Build targeted search query (Limit keywords to avoid 414 URI Too Long)
        import random
        selected_keywords = random.sample(all_keywords, min(len(all_keywords), 5))
        search_query = f"{team_name} (" + " OR ".join(selected_keywords) + ")"
        
        try:
            for sub in self.config.get("subreddits", ["soccer"]):
                # search.json allows targeted keyword search
                url = f"https://www.reddit.com/r/{sub}/search.json?q={search_query}&restrict_sr=1&sort=relevance&t=week&limit=25"
                
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "application/json",
                    "Referer": "https://www.google.com/"
                }
                
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        children = response.json().get("data", {}).get("children", [])
                        for post in children:
                            p = post.get("data", {})
                            title = p.get("title", "")
                            
                            # Double check team name is in title or body for relevance
                            body = p.get("selftext", "")
                            if team_name.lower() in title.lower() or team_name.lower() in body.lower():
                                permalink = p.get('permalink')
                                comments = []
                                if len(headlines) < 3: 
                                    comments = self._fetch_top_comments(permalink)

                                headlines.append({
                                    "title": title,
                                    "body": body[:500],
                                    "comments": comments,
                                    "score": p.get("score"),
                                    "url": f"https://reddit.com{permalink}",
                                })
                    else:
                        logger.warning(f"Reddit Search Failed for r/{sub}: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Reddit Request Failed for r/{sub}: {e}")

            return {
                "source": "reddit_search",
                "status": "success",
                "team": team_name,
                "headlines": headlines[:10],
                "mention_count": len(headlines)
            }
        except Exception as e:
            logger.error(f"Reddit No-Key Scrape Error: {e}")
            return {"source": "reddit", "status": "error", "headlines": []}

    def _fetch_top_comments(self, permalink: str) -> List[str]:
        """Fetches top 3 comments for a post to gauge 'Public Pulse'."""
        if not permalink: return []
        url = f"https://www.reddit.com{permalink}.json?limit=5&depth=1"
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                # Reddit structure: [post_data, comment_data]
                comment_data = response.json()[1]
                children = comment_data.get("data", {}).get("children", [])
                comments = []
                for child in children:
                    body = child.get("data", {}).get("body", "")
                    if body and body not in ["[deleted]", "[removed]"]:
                        comments.append(body[:300]) # Cap each comment length
                return comments[:3]
        except Exception:
            pass
        return []
