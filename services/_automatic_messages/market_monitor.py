import asyncio
from core.log import get_logger
from agents.market.api.the_odds_api import fetch_latest_odds
from core.initializer.database import Database
from core.initializer.whatsapp import WhatsAppClient
from core.config import settings

logger = get_logger("MarketMonitor")


class MarketMonitor:
    def __init__(self, db: Database, wa: WhatsAppClient):
        self.db = db
        self.wa = wa
        self.threshold = 0.15  # 15% move threshold for "Sharp Money" alert

    async def check_for_line_moves(self):
        """
        Periodically checks for significant odds movements.
        """
        logger.info("🕵️ Checking for Market Movements...")

        try:
            current_odds = fetch_latest_odds()
            if not current_odds or "error" in current_odds:
                logger.warning(f"Could not fetch odds: {current_odds}")
                return

            for match in current_odds:
                match_id = match.get("id")
                home_team = match.get("home_team")
                away_team = match.get("away_team")

                # Get latest bookie's odds (first one for now)
                if not match.get("bookmakers"):
                    continue

                bookie = match["bookmakers"][0]
                market = bookie["markets"][0]
                outcomes = {o["name"]: o["price"] for o in market["outcomes"]}

                # Load previous odds from DB
                prev_odds = self.db.load_global_odds(match_id)

                if prev_odds:
                    # Compare
                    for team, price in outcomes.items():
                        prev_price = prev_odds.get(team)
                        if prev_price:
                            move = abs(price - prev_price) / prev_price
                            if move >= self.threshold:
                                logger.info(
                                    f"🔥 Significant Move Detected: {home_team} vs {away_team} ({team}) moved {round(move * 100, 1)}%"
                                )
                                await self._trigger_alerts(
                                    home_team, away_team, team, prev_price, price, move
                                )

                # Save current odds for next comparison
                self.db.save_global_odds(match_id, outcomes)

        except Exception as e:
            logger.error(f"Market Monitor Core Failure: {e}")

    async def _trigger_alerts(self, home, away, team, old_price, new_price, move):
        """Sends the alert to all active users."""
        alert_msg = (
            f"🚨 *Sharp Money Alert*\n\n"
            f"Market shift in *{home} vs {away}*\n"
            f"The line for *{team}* just moved from {old_price} to {new_price}.\n"
            f"Big money is hitting this match! 💸\n\n"
            f"Want me to re-analyze the tactical shift?"
        )

        users = self.db.get_all_active_users()
        logger.info(f"📢 Blasting Sharp Alert to {len(users)} users.")

        for user_phone in users:
            # Send as an interactive button message
            interactive_obj = {
                "type": "button",
                "header": {"type": "text", "text": "💹 Market Shift Detected"},
                "body": {"text": alert_msg},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"Analyze {home} vs {away}",
                                "title": "🔬 Re-Analyze",
                            },
                        },
                        {
                            "type": "reply",
                            "reply": {"id": "Show_MainMenu", "title": "🔙 Main Menu"},
                        },
                    ]
                },
            }

            # Use templates if enabled
            if settings.get("GLOBAL_APP_CONFIG.whatsapp.use_templates"):
                template_name = settings.get(
                    "GLOBAL_APP_CONFIG.whatsapp.templates.sharp_move",
                    "goalmine_sharp_move",
                )
                # Approved Template has 2 params: {{1}} = Match, {{2}} = % Change
                self.wa.send_template_message(
                    user_phone,
                    template_name,
                    [f"{home} vs {away} ({team})", str(round(move * 100, 1))],
                    fallback_text=alert_msg,
                )
            else:
                self.wa.send_interactive_message(user_phone, interactive_obj)

            await asyncio.sleep(0.1)
