import json
import re
import asyncio
from core.log import get_logger
from services import orchestrator
from core.config import settings
from agents.gatekeeper.gatekeeper import Gatekeeper
from prompts.messages_prompts import ButtonResponses
from core.generate_bets import generate_bet_recommendations, generate_strategic_advice
from .ui_manager import GoalMineUI

logger = get_logger("ButtonHandler")


class GoalMineHandler:
    """
    Strict Button Handler - The "App" Logic.
    Rejects text chat. Forces menu navigation via Interactive Messages.
    """

    def __init__(self, wa_client, db_client):
        self.wa = wa_client
        self.db = db_client
        self.ui = GoalMineUI(wa_client, db_client)

    async def handle_incoming_message(self, from_number, msg_body, extracted_data=None):
        """
        Entry point.
        """
        user_input = msg_body.strip()
        logger.info(f"🕹️ [Routing] Received: '{user_input}' from {from_number}")

        # 2. MATCH PAYLOADS
        if user_input.startswith("Analyze"):
            # Format: "Analyze TeamA vs TeamB"
            query = user_input.replace("Analyze", "").strip()
            await self._trigger_analysis(from_number, query)
            return

        elif user_input.startswith("LOCKED_TBD"):
            logger.info("🔒 User attempted to select a TBD match.")
            self.wa.send_message(
                from_number,
                "🔓 *Match Locked:* This fixture is still 'To Be Determined'.\n\nI can only analyze matches once the official teams are confirmed. Please check back after the previous round is complete! 🏆",
            )
            return

        elif user_input == "Show_Schedule":
            logger.info("📅 User requested Schedule Browser.")
            await self.ui.send_schedule_browser(from_number)
            return

        elif user_input.startswith("Group_"):
            group_name = user_input.replace("_", " ")
            await self.ui.send_group_matches(from_number, group_name)
            return

        elif user_input.startswith("Stage_"):
            stage_name = user_input.replace("Stage_", "").replace("_", " ")
            await self.ui.send_group_matches(from_number, stage_name, is_stage=True)
            return

        elif user_input == "Show_Help":
            await self.ui.send_help_menu(from_number)
            return

        elif user_input == "Show_MainMenu":
            logger.info("🏠 User requested Main Menu.")
            await self.ui.send_main_menu(from_number)
            return

        elif user_input == "Generate_Bets":
            logger.info("🎲 User requested Bet Generation Menu.")
            await self.ui.send_bet_menu(from_number)
            return

        elif user_input == "Show_Groups_Menu":
            await self.ui.send_groups_selection(from_number)
            return

        elif user_input == "Show_Groups_G_L":
            await self.ui.send_groups_g_l(from_number)
            return

        elif user_input == "Show_Knockouts_Menu":
            await self.ui.send_knockouts_selection(from_number)
            return

        elif user_input == "Generate_More":
            # Load context
            user_state = self.db.load_memory(from_number) or {}
            
            # Default to 3 if not found, or use last requested count
            count = user_state.get("last_bet_count", 3)
            previous_bets = user_state.get("last_bet_response", "")

            logger.info(f"🔄 User requested MORE bets (Count: {count}). Excluding previous.")
            await self._trigger_bet_generation(from_number, count, exclude_text=previous_bets)
            return

        elif user_input in ["Bets_1", "Bets_3", "Bets_5"]:
            count = int(user_input.split("_")[1])
            await self._trigger_bet_generation(from_number, count)
            return

        # 3. FALBACK: User Typed Text
        logger.info(f"📍 Strict Mode (Text Input): {user_input}")

        # Classify Intent
        intent, data = await Gatekeeper.classify_intent(user_input)

        if intent == "BETTING":
            if data and data.get("teams"):
                # User typed a team name or "Analyze Brazil"
                team_name = data["teams"][0]
                logger.info(f"🎯 Text-to-Analysis Routing: '{team_name}'")
                await self._trigger_analysis(from_number, team_name)
                return
            else:
                user_state = self.db.load_memory(from_number) or {}
                if user_state.get("god_view"):
                    logger.info("💰 Strategy ask detected via text.")
                    # Strategy questions are still text-based but handled professionally
                    answer = await self._strategic_betting_advisor(user_state, user_input, from_number)
                    await self._send_multi(from_number, answer)
                    return
                else:
                    await self.ui.send_schedule_browser(from_number)
                    return

        elif intent == "SCHEDULE":
            logger.info("📅 Text-to-Schedule Routing.")
            await self.ui.send_schedule_browser(from_number)
            return

        # 4. FINAL FALLBACK: Profanity Check & Professional Rejection
        await self._force_button_navigation(from_number, user_input)

    async def _force_button_navigation(self, from_number, user_input):
        """Standard professional rejection with Profanity Filter."""
        logger.info(f"⛔ Unsupported Pure Text ('{user_input}') -> Forcing Menu.")

        # Profanity Filter (Basic list - can be expanded via settings)
        BAD_WORDS = ["fuck", "shit", "bitch", "cunt", "asshole", "stupid"]
        if any(w in user_input.lower() for w in BAD_WORDS):
            logger.warning(f"⚠️ Profanity detected from {from_number}")
            self.wa.send_message(from_number, ButtonResponses.REJECT_PROFANITY)
        else:
            # Standard Rejection
            self.wa.send_message(from_number, ButtonResponses.REJECT_TEXT)

        # Always offer the path back
        last_state = self.db.load_button_state(from_number)
        if last_state:
            self.wa.send_interactive_message(from_number, last_state)
        else:
            await self.ui.send_main_menu(from_number)

    async def _trigger_bet_generation(self, to_number, count, exclude_text=None):
        """Generates the recommended bets using DB persistence."""
        self.wa.send_typing_indicator(to_number)

        try:
            recommendations = await generate_bet_recommendations(
                count, user_phone=to_number, exclude_history=exclude_text
            )
            self.wa.send_message(to_number, recommendations)

            # SAVE CONTEXT FOR 'GENERATE MORE'
            # We append if there is existing history so we exclude ALL previous
            new_history = exclude_text + "\n" + recommendations if exclude_text else recommendations
            
            self.db.save_memory(to_number, {
                "last_bet_count": count,
                "last_bet_response": new_history
            })

            await asyncio.sleep(1.0)
            # Show specific Bet Footer (Generate More) instead of general analysis footer
            await self.ui.send_bet_footer(to_number)

        except Exception as e:
            logger.error(f"Bet Gen failed: {type(e).__name__}: {e}")
            self.wa.send_message(
                to_number,
                "⚠️ Could not generate bets at this time.\n\n"
                "If this persists, please contact the administrator:\n"
                "👤 *Jeffrey Fernandez*\n"
                "📱 9294255178\n"
                "📧 ninjeff06@gmail.com\n"
                "💼 capital.jfm@gmail.com",
            )
            await self.ui.send_main_menu(to_number)

    async def _trigger_analysis(self, to_number, match_query):
        """Runs the Swarm and persists data to DB."""
        # Find the full match object
        if " vs " in match_query:
            home_q, away_q = match_query.split(" vs ")
            match_info = orchestrator.find_match_by_teams(home_q, away_q)
        else:
            match_info = orchestrator.find_match_by_home_team(match_query)

        if not match_info:
            self.wa.send_message(to_number, ButtonResponses.MATCH_NOT_FOUND)
            return

        home = match_info.get("home_team")
        away = match_info.get("away_team")
        venue_name = match_info.get("venue")

        # 1. Acknowledge & Typing
        self.wa.send_typing_indicator(to_number)
        ack_msg = ButtonResponses.ANALYSIS_START.format(home=home, away=away)
        self.wa.send_message(to_number, ack_msg)
        self.wa.send_typing_indicator(to_number)  # Keep it alive

        # 2. Run Agents
        try:
            briefing = await orchestrator.generate_betting_briefing(match_info)
            briefing["user_phone"] = to_number  # Inject phone for logging

            # 2.1 [DATABASE PERSISTENCE] Save God View for future bet generation
            save_data = briefing.copy()
            save_data.update(
                {
                    "match": match_info,  # Store match info for context
                    "budget": settings.get(
                        "GLOBAL_APP_CONFIG.strategy.default_budget", 100
                    ),  # Use setting instead of hardcoded 100
                    "num_bets": 1,  # Default
                    "god_view": briefing,
                }
            )
            self.db.save_memory(to_number, save_data)
            logger.info(f"💾 God View saved to DB for {to_number}")

            # 3. Speak (The Closer)
            report = await orchestrator.format_the_closer_report(briefing)

            # Send chunks
            parts = re.split(r"(?=# BET \d+)", report)
            for part in parts:
                if part.strip():
                    self.wa.send_typing_indicator(to_number)
                    await asyncio.sleep(0.5)  # Simulate typing
                    self.wa.send_message(to_number, part.strip())

            # 4. Location Drop (Venue Pin)
            if venue_name:
                try:
                    with open("data/venues.json", "r") as f:
                        venues_db = json.load(f)

                    venue_data = venues_db.get(venue_name)
                    if venue_data:
                        logger.info(f"📍 Sending venue pin for {venue_name}")
                        self.wa.send_location_message(
                            to_number,
                            venue_data["lat"],
                            venue_data["lon"],
                            name=venue_name,
                            address=f"Official World Cup 2026 Venue • {venue_data.get('tz_offset', '')} UTC",
                        )
                except Exception as ve:
                    logger.warning(f"Could not load venue data: {ve}")

            # 5. Show Navigation Footer instead of auto-main menu
            await asyncio.sleep(1.0)
            await self.ui.send_analysis_footer(to_number)

        except Exception as e:
            logger.error(f"Strict Analysis failed: {type(e).__name__}: {e}")
            self.wa.send_message(
                to_number, ButtonResponses.ANALYSIS_ERROR
            )

    async def _strategic_betting_advisor(self, user_state, question, user_phone):
        """
        Advanced betting strategist using God View JSON.
        """
        try:
            answer = await generate_strategic_advice(
                user_phone=user_phone,
                question=question,
            )
            return answer
        except Exception as e:
            logger.error(f"Strategic Betting Advisor failed: {e}")
            return "I'm having trouble analyzing that strategy right now. Could you rephrase your question? 🎲"
            
    async def _send_multi(self, to_number, text):
        """
        Sends long messages split by '# BET' as separate WhatsApp messages.
        """
        if not text:
            return

        if "# BET" in text:
            parts = re.split(r"(?=# BET \d+)", text)
            for part in parts:
                clean_part = part.strip()
                if clean_part:
                    self.wa.send_message(to_number, clean_part)
                    await asyncio.sleep(0.3)
        else:
            self.wa.send_message(to_number, text)
