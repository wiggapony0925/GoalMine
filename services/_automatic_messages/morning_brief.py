from datetime import datetime
from core.log import get_logger
from services import orchestrator
from core.config import settings
from core.initializer.whatsapp import WhatsAppClient

logger = get_logger("MorningBrief")

class MorningBriefService:
    def __init__(self, wa: WhatsAppClient, db):
        self.wa = wa
        self.db = db

    def push_brief(self):
        """Daily Brief from settings"""
        logger.info("🌤️ Pushing Morning Brief...")
        
        # 1. Get raw data needed for template / text
        matches = orchestrator.get_todays_matches()
        num_edges = len(matches)
        today_str = datetime.now().strftime("%b %d")
        top_match = f"{matches[0]['team_home']} vs {matches[0]['team_away']}" if matches else "N/A"

        # Broadcast to all active users
        users = self.db.get_all_active_users()
        logger.info(f"📢 Blasting Morning Brief to {len(users)} users.")
        
        for target_user in users:
            # Generate Fallback Text
            fallback = orchestrator.get_schedule_brief(days=1)

            if settings.get('GLOBAL_APP_CONFIG.whatsapp.use_templates'):
                template_name = settings.get('GLOBAL_APP_CONFIG.whatsapp.templates.briefing', 'goalmine_alpha_briefing')
                self.wa.send_template_message(
                    target_user, 
                    template_name, 
                    [today_str, num_edges, top_match],
                    fallback_text=fallback
                )
            else:
                if fallback:
                    self.wa.send_message(target_user, fallback)
