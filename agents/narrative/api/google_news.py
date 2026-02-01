import logging
import feedparser

logger = logging.getLogger(__name__)

def fetch_headlines(team_name):
    """
    Fetches news from Google News RSS Feed (Free, No API Key).
    """
    # URL encode the team name
    query = team_name.replace(" ", "%20")
    rss_url = f"https://news.google.com/rss/search?q={query}+stats+OR+injury+when:7d&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(rss_url)
        articles = []
        
        # Extract top 5 entries
        for entry in feed.entries[:5]:
            articles.append({
                'title': entry.title,
                'description': entry.title, # Google News often puts the title in description or snippet
                'link': entry.link,
                'published': entry.published
            })
            
        logger.info(f"Fetched {len(articles)} articles for {team_name} from Google News.")
        return articles
    except Exception as e:
        logger.error(f"Error fetching Google News: {e}")
        return []
