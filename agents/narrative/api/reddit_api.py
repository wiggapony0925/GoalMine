import os
import json
import logging
import requests
from typing import List, Dict

logger = logging.getLogger("GoalMine")

class RedditScanner:
    """
    Scans Reddit for live sentiments and breaking news WITHOUT API KEYS.
    Uses public JSON endpoints.
    """
    CONFIG_FILE = "data/reddit_config.json"
    
    def __init__(self):
        # No keys required for public JSON access!
        self.config = self._load_config()
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        logger.info("✅ Reddit No-Key Scraper Initialized")

    def _load_config(self):
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load reddit config, using defaults: {e}")
            return {
                "subreddits": ["soccer", "worldcup"],
                "keywords": ["injury", "lineup", "morale"]
            }

    async def scan_team_sentiment(self, team_name: str) -> Dict:
        """
        Scans configured subreddits via public .json endpoints.
        """
        headlines = []
        try:
            keywords = " OR ".join(self.config.get("keywords", []))
            query = f"{team_name} ({keywords})"
            
            # We iterate through subreddits and fetch search results
            for sub in self.config.get("subreddits", ["soccer"]):
                # Using hot.json is MUCH more stable than search.json (avoids 403s)
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=50"
                
                headers = {
                    "User-Agent": f"GoalMineAnalysis/1.0 (Contact: intel@goalmine.ai)",
                    "Referer": "https://www.google.com/"
                }
                
                try:
                    response = requests.get(url, headers=headers, timeout=7)
                    if response.status_code == 200:
                        children = response.json().get("data", {}).get("children", [])
                        for post in children:
                            p = post.get("data", {})
                            title = p.get("title", "")
                            # Filter for team name in title
                            if team_name.lower() in title.lower():
                                headlines.append({
                                    "title": title,
                                    "score": p.get("score"),
                                    "url": f"https://reddit.com{p.get('permalink')}",
                                })
                    else:
                        logger.warning(f"Reddit Scrape Failed for r/{sub}: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Reddit Request Failed for r/{sub}: {e}")

            return {
                "source": "reddit_public",
                "status": "success",
                "team": team_name,
                "headlines": headlines[:10], # Keep top 10
                "mention_count": len(headlines)
            }
        except Exception as e:
            logger.error(f"Reddit No-Key Scrape Error: {e}")
            return {"source": "reddit", "status": "error", "headlines": []}
