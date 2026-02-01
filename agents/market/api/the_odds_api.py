import os
import requests

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

def fetch_latest_odds(sport_key='soccer_fifa_world_cup'):
    if not ODDS_API_KEY:
        return {"error": "Missing API Key"}
    
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?regions=us&markets=h2h&apiKey={ODDS_API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            raise ValueError("No odds data found for this market.")
            
        return data
    except Exception as e:
        raise e
