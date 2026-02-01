import random

def fetch_team_stats(team_id):
    """
    Mock client for SportMonks API / API-Football.
    """
    # In a real implementation:
    # url = f"https://api.sportmonks.com/v3/football/teams/{team_id}"
    # response = requests.get(url, headers=...)
    
    return {
        'xG_for': random.uniform(1.1, 2.5),
        'xG_against': random.uniform(0.8, 1.9),
        'recent_form': ['W', 'D', 'W', 'L', 'W'],
        'key_injuries': [{'player': 'Star Striker', 'status': 'Doubtful'}]
    }
