from core.log import get_logger
from services import orchestrator
from core.config import settings
from core.initializer.whatsapp import WhatsAppClient

logger = get_logger("KickoffAlerts")


class KickoffAlertService:
    def __init__(self, wa: WhatsAppClient, db):
        self.wa = wa
        self.db = db

    def _build_kickoff_message(self, match, lead_time):
        """Builds a kickoff alert message for a single match."""
        home = match.get("team_home", "TBD")
        away = match.get("team_away", "TBD")
        venue = match.get("venue", "")
        venue_line = f"🏟️ *Venue:* {venue}\n" if venue else ""

        return (
            f"🚨 *KICK-OFF ALERT*\n\n"
            f"⚽ *{home} vs {away}*\n"
            f"{venue_line}"
            f"⏰ Starting in *{lead_time} minutes*!\n\n"
            f"📊 Want a last-minute tactical edge?\n"
            f"👉 Reply 'Analyze {home}' for a full swarm breakdown.\n\n"
            f"_GoalMine AI 🏆_"
        )

    def check_and_send_alerts(self):
        """Runs based on settings interval — checks for upcoming kick-offs and alerts users."""
        logger.info("🏟️ Checking for upcoming kick-offs...")

        lead_time = settings.get(
            "GLOBAL_APP_CONFIG.scheduling.alert_lead_time_mins", 60
        )

        try:
            upcoming = orchestrator.get_upcoming_matches()
        except Exception as e:
            logger.error(f"❌ Kickoff Alerts: Failed to fetch upcoming matches: {e}")
            return

        if not upcoming:
            logger.info(f"✅ No matches starting in the next {lead_time} minutes.")
            return

        try:
            users = self.db.get_all_active_users()
        except Exception as e:
            logger.error(f"❌ Kickoff Alerts: Failed to fetch active users: {e}")
            return

        if not users:
            logger.info("📭 Kickoff Alerts: No active users to notify.")
            return

        logger.info(
            f"📢 Sending {len(upcoming)} kickoff alert(s) to {len(users)} users."
        )
        sent_count = 0
        fail_count = 0

        for target_user in users:
            for m in upcoming:
                try:
                    home = m.get("team_home", "TBD")
                    away = m.get("team_away", "TBD")
                    fallback = self._build_kickoff_message(m, lead_time)

                    if settings.get("GLOBAL_APP_CONFIG.whatsapp.use_templates"):
                        template_name = settings.get(
                            "GLOBAL_APP_CONFIG.whatsapp.templates.kickoff",
                            "goalmine_kickoff_alert",
                        )
                        self.wa.send_template_message(
                            target_user,
                            template_name,
                            [home, away],
                            fallback_text=fallback,
                        )
                    else:
                        self.wa.send_message(target_user, fallback)

                    sent_count += 1
                except Exception as e:
                    fail_count += 1
                    logger.error(
                        f"❌ Kickoff Alert: Failed to send {home} vs {away} to {target_user}: {e}"
                    )

        logger.info(
            f"✅ Kickoff Alerts complete: {sent_count} sent, {fail_count} failed."
        )
