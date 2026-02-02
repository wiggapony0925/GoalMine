import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from core.log import get_logger

logger = get_logger("API.GoogleNews")

def fetch_headlines(team_name, query_type="general", region="GB"):
    """
    Fetches targeted news via Google News RSS.
    
    Args:
        team_name (str): The team to search for.
        query_type (str): 'general', 'injury', or 'narrative' (for drama/rumors).
        region (str): 'US', 'GB', 'ES', etc. Default 'GB' is better for Soccer.
    """
    # 1. DEFINE POWER QUERIES
    # We use 'intitle:' to ensure the team is the main topic.
    base_query = f'intitle:"{team_name}"'
    
    keywords = {
        # Standard updates
        "general": "stats OR result OR match OR preview",
        
        # The 'Physical' scan
        "injury": "(injury OR hamstring OR suspension OR fitness OR \"ruled out\" OR training)",
        
        # The 'Psychological' scan (Best for Narrative Agent)
        "narrative": "(crisis OR furious OR \"dressing room\" OR rumors OR \"transfer request\" OR warns OR pressure)"
    }
    
    # 2. CONSTRUCT THE QUERY STRING
    # Combine team + topic + timeframe (3 days is better for 'breaking' narrative)
    topic_terms = keywords.get(query_type, keywords["general"])
    search_q = f'{base_query} AND {topic_terms} when:3d'
    
    # 3. ADD NEGATIVE KEYWORDS (Remove Noise)
    # Exclude: TV listings, highlights, ticket sales, betting odds, and OTHER SPORTS (Cricket)
    search_q += ' -watch -tv -channel -tickets -betting -highlights -cricket -t20'
    
    # URL Encode
    encoded_q = quote(search_q)
    
    # 4. SET REGIONAL PARAMETERS (Crucial for Soccer)
    # gl=GB gets UK news (The Sun, BBC, Sky). gl=US gets ESPN/Bleacher Report.
    # ceid usually follows gl (e.g., GB:en)
    rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-{region}&gl={region}&ceid={region}:en"
    
    try:
        # User-Agent is vital to avoid 403 Forbidden on some Google endpoints
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        articles = []
        
        for item in root.findall('./channel/item')[:7]: # Increased limit slightly
            title_node = item.find('title')
            link_node = item.find('link')
            pub_date_node = item.find('pubDate')
            source_node = item.find('source')

            title = title_node.text if title_node is not None else "No Title"
            link = link_node.text if link_node is not None else ""
            pub_date = pub_date_node.text if pub_date_node is not None else ""
            source = source_node.text if source_node is not None else "Unknown"
            
            # Basic cleanup: Google titles often look like "Headline - SourceName"
            # We strip the source from the title if it's redundant
            clean_title = title.split(" - ")[0]
            
            articles.append({
                'title': clean_title,
                'link': link,
                'published': pub_date,
                'source': source,
                'type': query_type
            })
            
        logger.info(f"✅ Found {len(articles)} {query_type} articles for {team_name} ({region})")
        return articles
        
    except Exception as e:
        logger.error(f"❌ Google News Error ({team_name}): {e}")
        return []
