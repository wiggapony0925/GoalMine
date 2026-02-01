import os
import requests
import logging

logger = logging.getLogger("GoalMine")

def fetch_team_stats(team_name):
    """
    Fetches REAL team stats and STARTING LINEUPS from SportMonks API v3.
    """
    api_token = os.getenv("SPORTMONKS_API_TOKEN")
    
    if not api_token:
        raise ValueError("Missing SPORTMONKS_API_TOKEN")

    headers = {"Authorization": api_token}
    
    try:
        # 1. Search for Team ID
        search_url = f"https://api.sportmonks.com/v3/football/teams/search/{team_name}"
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json().get('data', [])
        
        if not data:
            raise ValueError(f"Team {team_name} not found in SportMonks DB")
            
        team_id = data[0]['id']
        team_display_name = data[0]['name']

        # 2. Get Fixture Data (Today/Upcoming) with Lineups
        # We include 'lineups.player' and 'coach' to see who is leading and playing.
        fixtures_url = f"https://api.sportmonks.com/v3/football/fixtures/between/2026-01-01/2026-12-31/{team_id}?include=lineups.player,coaches.coach,venue"
        fixture_resp = requests.get(fixtures_url, headers=headers)
        fixture_data = fixture_resp.json().get('data', [])
        
        # Sort by date to find the most relevant (upcoming or live)
        # For simplicity, we grab the first one found or a live one if exists
        target_fixture = None
        if fixture_data:
            # Prefer 'Live' status (state_id in [2, 3, 4])
            live_fixtures = [f for f in fixture_data if f.get('state_id') in [2, 3, 4]]
            target_fixture = live_fixtures[0] if live_fixtures else fixture_data[0]

        lineup = []
        coach_name = "Unknown"
        live_status = "Pre-Match"
        score = "0-0"
        venue_name = "Unknown Venue"

        if target_fixture:
            # Extract Lineup (Starters only)
            raw_lineups = target_fixture.get('lineups', [])
            lineup = [
                l.get('player', {}).get('name') 
                for l in raw_lineups 
                if l.get('team_id') == team_id and l.get('type_id') == 11 # 11 is 'Starting' in V3
            ]
            
            # Extract Coach
            coaches = target_fixture.get('coaches', [])
            for c in coaches:
                if c.get('team_id') == team_id:
                    coach_name = c.get('coach', {}).get('name', "Unknown")

            # Status & Score
            state_id = target_fixture.get('state_id')
            if state_id == 3: live_status = "HT"
            elif state_id in [2, 4]: live_status = "LIVE"
            elif state_id == 5: live_status = "FINISHED"

            scores = target_fixture.get('scores', [])
            # In V3, scores are usually in a list or object depending on nesting
            # This is a simplified extraction
            score = "Check God View" 

            venue_name = target_fixture.get('venue', {}).get('name', venue_name)

        return {
            'name': team_display_name,
            'id': team_id,
            'live_status': live_status,
            'current_score': score,
            'lineup': lineup if lineup else ["Lineup not released"],
            'coach': coach_name,
            'venue': venue_name
        }

    except Exception as e:
        logger.error(f"SportMonks API Fail for {team_name}: {e}")
        return {
            'name': team_name,
            'live_status': "Offline",
            'lineup': ["Error fetching data"],
            'coach': "N/A"
        }
