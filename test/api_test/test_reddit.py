import asyncio
import logging
import sys
import os

# Add the project root to sys.path so we can import agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.narrative.api.reddit_api import RedditScanner


async def test_reddit():
    # Setup basic logging to see what's happening
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("RedditTest")

    logger.info("🚀 Starting Reddit API/Scraper Test...")
    scanner = RedditScanner()

    # Test teams
    teams = ["Mexico", "Argentina", "France"]

    for team in teams:
        logger.info(f"🔍 Scanning sentiment for: {team}")
        result = await scanner.scan_team_sentiment(team)

        if result["status"] == "success":
            headlines = result.get("headlines", [])
            logger.info(f"✅ Success! Found {len(headlines)} headlines for {team}.")
            for h in headlines:
                logger.info(f"  - {h['title']} (Score: {h['score']})")
        else:
            logger.error(f"❌ Failed to scan {team}: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(test_reddit())
