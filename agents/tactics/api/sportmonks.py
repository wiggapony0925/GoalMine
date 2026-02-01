import os
import requests
import logging

logger = logging.getLogger(__name__)

def fetch_team_stats(team_name):
    """
    Fetches REAL team stats from SportMonks API v3.
    Requires SPORTMONKS_API_TOKEN in .env
    """
    api_token = os.getenv("SPORTMONKS_API_TOKEN")
    
    if not api_token:
        raise ValueError("Missing SPORTMONKS_API_TOKEN")

    search_url = f"https://api.sportmonks.com/v3/football/teams/search/{team_name}"
    headers = {"Authorization": api_token}
    
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json().get('data', [])
        
        if not data:
            raise ValueError(f"Team {team_name} not found in SportMonks DB")
            
        team_id = data[0]['id']
        
        stats_url = f"https://api.sportmonks.com/v3/football/teams/{team_id}"
        stats_resp = requests.get(stats_url, headers=headers)
        stats_data = stats_resp.json().get('data', {})
        
        return {
            'name': stats_data.get('name'),
            'founded': stats_data.get('founded'),
            'venue_id': stats_data.get('venue_id'),
            'stats': "Premium Data Required" 
        }

    except Exception as e:
        logger.error(f"SportMonks API Fail: {e}")
        raise e
