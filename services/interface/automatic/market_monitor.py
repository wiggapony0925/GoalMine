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
        self.threshold = settings.get(
            "GLOBAL_APP_CONFIG.scheduling.sharp_move_threshold", 0.15
        )

    def _build_alert_message(self, home, away, team, old_price, new_price, move_pct):
        """Builds a formatted sharp money alert message."""
        direction = "⬆️ UP" if new_price > old_price else "⬇️ DOWN"
        return (
            f"🚨 *SHARP MONEY ALERT*\n\n"
            f"⚽ *{home} vs {away}*\n"
            f"📈 *{team}* line moved {direction}\n"
            f"   {old_price} → {new_price} ({move_pct:.1f}% shift)\n\n"
            f"💸 Significant money is hitting this market.\n"
            f"📊 This often signals professional bettor activity.\n\n"
            f"👉 Want a fresh tactical breakdown?\n\n"
            f"_GoalMine AI 🏆_"
        )

    async def check_for_line_moves(self):
        """Periodically checks for significant odds movements."""
        logger.info("🕵️ Checking for Market Movements...")

        try:
            current_odds = fetch_latest_odds()
            if not current_odds or "error" in current_odds:
                logger.warning(f"Could not fetch odds: {current_odds}")
                return

            alerts_triggered = 0

            for match in current_odds:
                match_id = match.get("id")
                home_team = match.get("home_team")
                away_team = match.get("away_team")

                if not match.get("bookmakers"):
                    continue

                bookie = match["bookmakers"][0]
                markets = bookie.get("markets", [])
                if not markets:
                    continue

                market = markets[0]
                outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}

                if not outcomes:
                    continue

                # Load previous odds from DB
                prev_odds = self.db.load_global_odds(match_id)

                if prev_odds:
                    for team, price in outcomes.items():
                        prev_price = prev_odds.get(team)
                        if prev_price and prev_price > 0:
                            move = abs(price - prev_price) / prev_price
                            if move >= self.threshold:
                                move_pct = round(move * 100, 1)
                                logger.info(
                                    f"🔥 Significant Move: {home_team} vs {away_team} "
                                    f"({team}) moved {move_pct}%"
                                )
                                await self._trigger_alerts(
                                    home_team, away_team, team,
                                    prev_price, price, move
                                )
                                alerts_triggered += 1

                # Save current odds for next comparison
                self.db.save_global_odds(match_id, outcomes)

            logger.info(
                f"✅ Market scan complete: {alerts_triggered} alert(s) triggered."
            )

        except Exception as e:
            logger.error(f"❌ Market Monitor failure: {e}")

    async def _trigger_alerts(self, home, away, team, old_price, new_price, move):
        """Sends the alert to all active users."""
        move_pct = round(move * 100, 1)
        alert_msg = self._build_alert_message(
            home, away, team, old_price, new_price, move_pct
        )

        try:
            users = self.db.get_all_active_users()
        except Exception as e:
            logger.error(f"❌ Market Alert: Failed to fetch users: {e}")
            return

        if not users:
            logger.info("📭 Market Alert: No active users to notify.")
            return

        logger.info(f"📢 Blasting Sharp Alert to {len(users)} users.")
        sent_count = 0
        fail_count = 0

        for user_phone in users:
            try:
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
                                "reply": {
                                    "id": "Show_MainMenu",
                                    "title": "🔙 Main Menu",
                                },
                            },
                        ]
                    },
                }

                if settings.get("GLOBAL_APP_CONFIG.whatsapp.use_templates"):
                    template_name = settings.get(
                        "GLOBAL_APP_CONFIG.whatsapp.templates.sharp_move",
                        "goalmine_sharp_move",
                    )
                    self.wa.send_template_message(
                        user_phone,
                        template_name,
                        [f"{home} vs {away} ({team})", str(move_pct)],
                        fallback_text=alert_msg,
                    )
                else:
                    self.wa.send_interactive_message(user_phone, interactive_obj)

                sent_count += 1
            except Exception as e:
                fail_count += 1
                logger.error(f"❌ Market Alert: Failed to send to {user_phone}: {e}")

            await asyncio.sleep(0.1)

        logger.info(
            f"✅ Market Alert complete: {sent_count} sent, {fail_count} failed."
        )
