import logging
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

def fetch_headlines(team_name):
    """
    Fetches news from Google News RSS Feed using standard libraries.
    (Fixes Python 3.14 compatibility by removing feedparser which relies on deprecated 'cgi')
    """
    # URL encode the team name
    query = team_name.replace(" ", "%20")
    rss_url = f"https://news.google.com/rss/search?q={query}+stats+OR+injury+when:7d&hl=en-US&gl=US&ceid=US:en"
    
    try:
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        articles = []
        # Google News RSS structure: channel -> item
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            articles.append({
                'title': title,
                'description': title, # Google News often mirrors title/desc in this feed
                'link': link,
                'published': pub_date
            })
            
        logger.info(f"Fetched {len(articles)} articles for {team_name} from Google News.")
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching Google News for {team_name}: {e}")
        return []
