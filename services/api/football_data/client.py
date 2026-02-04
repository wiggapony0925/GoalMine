import requests
from core.log import get_logger
from core.config import settings

logger = get_logger("FootballAPI")

class FootballDataClient:
    """
    Low-level specialist for interacting with Football-Data.org.
    Targeting the 2026 World Cup Schedule.
    """
    def __init__(self):
        self.base_url = "https://api.football-data.org/v4"
        self.api_token = settings.get('GLOBAL_APP_CONFIG.live_data.api_token')

    def fetch_matches(self, competition="WC", season="2026"):
        """
        Executes the raw GET request to the matches endpoint.
        """
        if not self.api_token:
            logger.error("❌ Football-Data API Token missing in settings.")
            return None

        url = f"{self.base_url}/competitions/{competition}/matches?season={season}"
        headers = {"X-Auth-Token": self.api_token}
        
        try:
            logger.info(f"📡 Requesting live data from {competition} {season}...")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug("✅ Raw API data received successfully.")
                return data.get('matches', [])
            else:
                logger.error(f"❌ API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Request failed: {e}")
            return None
