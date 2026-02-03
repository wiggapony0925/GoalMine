from core.log import get_logger
from services import orchestrator
from core.config import settings
from core.initializer.whatsapp import WhatsAppClient

logger = get_logger("KickoffAlerts")

class KickoffAlertService:
    def __init__(self, wa: WhatsAppClient, db):
        self.wa = wa
        self.db = db

    def check_and_send_alerts(self):
        """Runs based on settings interval for Kick-off Alerts"""
        logger.info("🏟️ Checking for upcoming kick-offs...")
        upcoming = orchestrator.get_upcoming_matches()
        
        # Broadcast to all users
        users = self.db.get_all_active_users()
        logger.info(f"📢 Checking kick-off alerts for {len(users)} users.")

        for target_user in users:
            for m in upcoming:
            # Generate Fallback Text
            fallback = f"🚨 KICK-OFF ALERT: {m['team_home']} vs {m['team_away']} starts in 1 hour!\nReply 'Analyze {m['team_home']}' for a last-minute edge."
            
            if settings.get('whatsapp.use_templates'):
                template_name = settings.get('whatsapp.templates.kickoff', 'goalmine_kickoff_alert')
                self.wa.send_template_message(
                    target_user, 
                    template_name, 
                    [m['team_home'], m['team_away']],
                    fallback_text=fallback
                )
            else:
                self.wa.send_message(target_user, fallback)
                
        if not upcoming:
            logger.info("✅ No matches starting in the next hour.")
