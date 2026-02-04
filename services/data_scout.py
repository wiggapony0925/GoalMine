from datetime import datetime
from core.log import get_logger
from core.config import settings
from data.scripts.data import SCHEDULE as STATIC_SCHEDULE
from services.api.football_data.client import FootballDataClient

logger = get_logger("DataScout")


class DataScoutService:
    """
    Live Data Sync Agent.
    Partners the Football-Data.org API with the local static schedule.
    Saves to Database for persistence across restarts.
    """

    def __init__(self, db_client=None):
        self.api = FootballDataClient()
        self.db = db_client
        self.cached_merged_schedule = []
        self.last_sync = None

        # Initial Load from DB if possible
        if self.db:
            db_data = self.db.load_live_schedule()
            if db_data:
                self.cached_merged_schedule = db_data
                logger.info("🛰️ Initialized schedule with data from Database.")

    async def sync_now(self):
        """Fetches live matches and merges them with the local schedule."""
        if not settings.get("GLOBAL_APP_CONFIG.live_data.enabled", True):
            logger.info("🚫 DataScout sync disabled in settings.")
            return

        logger.info("🛰️ Syncing Live World Cup Schedule...")

        try:
            active_matches = self.api.fetch_matches()

            if active_matches is not None:
                # Merge logic
                new_schedule = self._merge_schedules(active_matches)
                self.cached_merged_schedule = new_schedule
                self.last_sync = datetime.now().isoformat()

                # Persist to Database
                if self.db:
                    self.db.save_live_schedule(new_schedule)

                logger.info(
                    f"✅ Sync Successful: {len(active_matches)} matches retrieved and merged."
                )
                return new_schedule
            else:
                logger.error("❌ API Sync failed to return match data.")
                return None
        except Exception as e:
            logger.error(f"❌ DataScout Crash during sync: {e}")
            return None

    def _merge_schedules(self, live_matches):
        """
        Calculates the definitive schedule.
        Live API data takes priority for Teams/Scores,
        Static JSON provides Venues/Labels.
        """
        if not live_matches:
            return STATIC_SCHEDULE

        merged = []
        for static_m in STATIC_SCHEDULE:
            match_found = False
            for live_m in live_matches:
                # Match by Date (first 16 chars: 2026-06-11T15:00)
                static_date = static_m["date_iso"][:16]
                live_date = live_m["utcDate"].replace("Z", "")[:16]

                if static_date == live_date:
                    match_found = True
                    dynamic_m = static_m.copy()

                    # Update with Live Team Data
                    home = live_m.get("homeTeam", {})
                    away = live_m.get("awayTeam", {})

                    if home and home.get("name"):
                        dynamic_m["team_home"] = home.get("name")
                    if away and away.get("name"):
                        dynamic_m["team_away"] = away.get("name")

                    # Add Status and Score
                    dynamic_m["live_status"] = live_m.get(
                        "status"
                    )  # TIMED, LIVE, FINISHED, etc.
                    dynamic_m["score"] = live_m.get("score", {}).get("fullTime", {})

                    merged.append(dynamic_m)
                    break

            if not match_found:
                merged.append(static_m)

        return merged

    def get_merged_schedule(self):
        """Returns the current synchronized schedule."""
        if not self.cached_merged_schedule:
            return STATIC_SCHEDULE
        return self.cached_merged_schedule

    def set_database(self, db_client):
        """Injects the database client for persistence."""
        self.db = db_client
        # Try a fresh load now that we have the DB
        db_data = self.db.load_live_schedule()
        if db_data:
            self.cached_merged_schedule = db_data
            logger.info("🛰️ Schedule resynced from Database after DB injection.")


# Singleton Instance
data_scout = DataScoutService()
