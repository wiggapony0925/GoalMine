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

    def _build_brief_message(self, matches, today_str):
        """Builds the morning briefing message from today's match data."""
        num_matches = len(matches)

        if num_matches == 0:
            return (
                f"🌤️ *GOALMINE DAILY BRIEF — {today_str}*\n\n"
                "📭 No matches scheduled for today.\n"
                "Stay sharp — the next fixtures are loading soon.\n\n"
                "_GoalMine AI 🏆_"
            )

        top_match = f"{matches[0]['team_home']} vs {matches[0]['team_away']}"
        match_lines = []
        for m in matches[:5]:
            home = m.get("team_home", "TBD")
            away = m.get("team_away", "TBD")
            kick = m.get("kickoff", "")
            time_str = f" ({kick})" if kick else ""
            match_lines.append(f"  ⚽ {home} vs {away}{time_str}")

        fixture_block = "\n".join(match_lines)
        remaining = f"\n  _...and {num_matches - 5} more_" if num_matches > 5 else ""

        return (
            f"🌤️ *GOALMINE DAILY BRIEF — {today_str}*\n\n"
            f"📊 *{num_matches} match{'es' if num_matches != 1 else ''}* on the board today.\n"
            f"🔥 *Featured:* {top_match}\n\n"
            f"📅 *Today's Fixtures:*\n{fixture_block}{remaining}\n\n"
            "👉 Reply to analyze any fixture and find your edge.\n\n"
            "_GoalMine AI 🏆_"
        )

    def push_brief(self):
        """Daily Brief — sends scheduled morning briefing to all active users."""
        logger.info("🌤️ Pushing Morning Brief...")

        try:
            matches = orchestrator.get_todays_matches()
        except Exception as e:
            logger.error(f"❌ Morning Brief: Failed to fetch today's matches: {e}")
            return

        num_edges = len(matches)
        today_str = datetime.now().strftime("%b %d, %Y")
        top_match = (
            f"{matches[0]['team_home']} vs {matches[0]['team_away']}"
            if matches
            else "No matches today"
        )

        try:
            users = self.db.get_all_active_users()
        except Exception as e:
            logger.error(f"❌ Morning Brief: Failed to fetch active users: {e}")
            return

        if not users:
            logger.info("📭 Morning Brief: No active users to notify.")
            return

        logger.info(f"📢 Blasting Morning Brief to {len(users)} users.")
        sent_count = 0
        fail_count = 0

        for target_user in users:
            try:
                fallback = self._build_brief_message(matches, today_str)

                if settings.get("GLOBAL_APP_CONFIG.whatsapp.use_templates"):
                    template_name = settings.get(
                        "GLOBAL_APP_CONFIG.whatsapp.templates.briefing",
                        "goalmine_alpha_briefing",
                    )
                    self.wa.send_template_message(
                        target_user,
                        template_name,
                        [today_str, str(num_edges), top_match],
                        fallback_text=fallback,
                    )
                else:
                    self.wa.send_message(target_user, fallback)

                sent_count += 1
            except Exception as e:
                fail_count += 1
                logger.error(
                    f"❌ Morning Brief: Failed to send to {target_user}: {e}"
                )

        logger.info(
            f"✅ Morning Brief complete: {sent_count} sent, {fail_count} failed."
        )
