import requests
from bs4 import BeautifulSoup
from core.log import get_logger
from core.utils import DEFAULT_HEADERS

logger = get_logger("API.Scraper")


def extract_article_text(url):
    """
    Attempts to scrape the main text content from a sports news URL.
    """
    if not url or "reddit.com" in url:  # Reddit already handled via JSON
        return None

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=5)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text
        text = soup.get_text()

        # break into lines and remove leading and trailing whitespace
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = "\n".join(chunk for chunk in chunks if chunk)

        # Heuristic: Find long paragraphs or sections that look like content
        return text[:1500]  # Return first 1500 chars of "clean" text

    except Exception as e:
        logger.warning(f"Failed to scrape article {url}: {e}")
        return None
