import os
import requests

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_headlines(team_name):
    if not NEWS_API_KEY:
        return []
    url = f"https://newsapi.org/v2/everything?q={team_name} soccer&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=en"
    try:
        r = requests.get(url)
        return r.json().get('articles', [])[:5] 
    except:
        return []
