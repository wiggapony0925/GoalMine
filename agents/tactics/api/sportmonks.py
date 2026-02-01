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
        
        # 2. Get Live/Fixture Data (Check for TODAY's fixture)
        # We assume we hit the livescores/now endpoint or similar for the team
        live_status = "Pre-Match"
        minute = 0
        score = "0-0"
        
        try:
            live_url = f"https://api.sportmonks.com/v3/football/livescores/team/{team_id}" 
            live_resp = requests.get(live_url, headers=headers)
            live_data_arr = live_resp.json().get('data', [])
            
            if live_data_arr:
                game = live_data_arr[0]
                minute = game.get('minute', 0)
                scores = game.get('scores', {})
                score = f"{scores.get('localteam_score', 0)}-{scores.get('visitorteam_score', 0)}"
                state_id = game.get('state_id') 
                
                # HT is strictly ID 3 in SportMonks V3
                if state_id == 3: 
                    live_status = "HT"
                elif state_id in [2, 4]:
                    live_status = "LIVE"
                elif state_id == 5:
                    live_status = "FINISHED"
        except Exception:
            logger.warning(f"Could not fetch livescore for {team_name}, defaulting to Pre-Match")

        # 3. Get Deep Stats (Squad + Form)
        stats_url = f"https://api.sportmonks.com/v3/football/teams/{team_id}?include=squad.player,latest.fixtures"
        stats_resp = requests.get(stats_url, headers=headers)
        stats_data = stats_resp.json().get('data', {})
        
        squad_raw = stats_data.get('squad', [])
        roster = [p.get('player', {}).get('name') for p in squad_raw if p.get('player')]
        
        latest_fixtures = stats_data.get('latest', [])
        form = [f.get('result_info') for f in latest_fixtures[:5]]

        return {
            'name': stats_data.get('name'),
            'live_status': live_status,
            'minute': minute,
            'current_score': score,
            'roster_sample': roster[:5],
            'recent_form': form
        }

    except Exception as e:
        logger.error(f"SportMonks API Fail: {e}")
        raise e
