"""
Free sports data APIs for enriching narrative intelligence.
No API keys required.
"""

import requests
import time
from core.log import get_logger
from core.utils import DEFAULT_HEADERS

logger = get_logger("API.FreeSports")


def fetch_team_wikipedia_summary(team_name: str) -> dict:
    """
    Fetches a brief team summary from Wikipedia's free API.
    Useful for historical context, rivalries, and recent form narrative.

    Args:
        team_name: National team name (e.g., "Brazil national football team").

    Returns:
        dict: Summary with title, extract, and thumbnail URL.
    """
    search_term = f"{team_name} national football team"
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(
        search_term
    )

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=12)
            if response.status_code == 200:
                data = response.json()
                return {
                    "source": "wikipedia",
                    "title": data.get("title", ""),
                    "summary": data.get("extract", ""),
                    "thumbnail": data.get("thumbnail", {}).get("source", ""),
                }
            # Try simpler search term if full name fails
            url_simple = (
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + requests.utils.quote(team_name)
            )
            response = requests.get(url_simple, headers=DEFAULT_HEADERS, timeout=12)
            if response.status_code == 200:
                data = response.json()
                return {
                    "source": "wikipedia",
                    "title": data.get("title", ""),
                    "summary": data.get("extract", ""),
                    "thumbnail": data.get("thumbnail", {}).get("source", ""),
                }
            break  # Non-timeout HTTP error, no need to retry
        except requests.exceptions.Timeout:
            logger.warning(
                f"Wikipedia API timeout for {team_name} (attempt {attempt}/{max_retries})"
            )
            if attempt < max_retries:
                time.sleep(2 * attempt)
        except Exception as e:
            logger.warning(f"Wikipedia API failed for {team_name}: {e}")
            break

    return {"source": "wikipedia", "title": team_name, "summary": "", "thumbnail": ""}


def fetch_football_rankings() -> list:
    """
    Fetches current FIFA rankings from a free public endpoint.
    Uses football-data.org's free tier (no key needed for basic data).

    Returns:
        list: Top team rankings or empty list on failure.
    """
    url = "https://www.football-data.org/v4/competitions/WC/standings"
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            standings = data.get("standings", [])
            return standings
    except Exception as e:
        logger.debug(f"Football rankings fetch skipped: {e}")
    return []
