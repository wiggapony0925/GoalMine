import json
import asyncio
from core.log import get_logger
from services import orchestrator
from core.config import settings
from agents.gatekeeper.gatekeeper import Gatekeeper
from data.scripts.responses import Responses, ButtonResponses
from core.generate_bets import generate_bet_recommendations

logger = get_logger("ButtonHandler")

class ButtonConversationHandler:
    """
    Strict Button Handler - The "App" Logic.
    Rejects text chat. Forces menu navigation via Interactive Messages.
    """
    def __init__(self, wa_client, db_client):
        self.wa = wa_client
        self.db = db_client

    async def handle_incoming_message(self, from_number, msg_body, extracted_data=None):
        """
        Entry point. 
        Note: extracted_data (Gatekeeper) is largely ignored here in favor of explicit payloads.
        """
        # 1. Check if message is a Payload (Button Click)
        # In this simplified architecture, we assume 'msg_body' contains the payload 
        # because the webhook parser (app.py) should extract body/payload uniformly.
        # If your app.py differentiates them, we might need to adjust.
        # For now, we assume msg_body IS the text/payload.
        
        user_input = msg_body.strip()
        
        # 2. MATCH PAYLOADS
        if user_input.startswith("Analyze"):
             # Format: "Analyze TeamA vs TeamB"
             query = user_input.replace("Analyze", "").strip()
             await self._trigger_analysis(from_number, query)
             return

        elif user_input == "Show_Schedule":
            await self._send_schedule_browser(from_number)
            return

        elif user_input.startswith("Group_"):
            group_name = user_input.replace("_", " ")
            await self._send_group_matches(from_number, group_name)
            return

        elif user_input.startswith("Stage_"):
            stage_name = user_input.replace("Stage_", "").replace("_", " ")
            await self._send_group_matches(from_number, stage_name, is_stage=True)
            return
            
        elif user_input == "Show_Help":
             await self._send_help_menu(from_number)
             return

        elif user_input == "Show_MainMenu":
            await self._send_main_menu(from_number)
            return

        elif user_input == "Generate_Bets":
            await self._send_bet_menu(from_number)
            return

        elif user_input == "Show_Groups_Menu":
            await self._send_groups_selection(from_number)
            return

        elif user_input == "Show_Groups_G_L":
            await self._send_groups_g_l(from_number)
            return

        elif user_input == "Show_Knockouts_Menu":
            await self._send_knockouts_selection(from_number)
            return

        elif user_input in ["Bets_1", "Bets_3", "Bets_5"]:
            count = int(user_input.split("_")[1])
            await self._trigger_bet_generation(from_number, count)
            return

        # 3. FALBACK: User Typed Text -> Try Intelligent Routing via Gatekeeper
        logger.info(f"📍 Strict Mode (Text Input): {user_input}")
        
        # Classify Intent
        intent, data = await Gatekeeper.classify_intent(user_input)
        
        if intent == "BETTING" and data and data.get('teams'):
            # User typed a team name or "Analyze Brazil"
            team_name = data['teams'][0]
            logger.info(f"🎯 Intelligent Routing: Triggering analysis for '{team_name}' based on text.")
            await self._trigger_analysis(from_number, team_name)
            return
            
        elif intent == "SCHEDULE":
            logger.info("📅 Intelligent Routing: Showing schedule browser based on text.")
            await self._send_schedule_browser(from_number)
            return

        # 4. FINAL FALLBACK: Unclear Input -> Polite Redirect to Menu
        logger.info(f"⛔ Unclear Input ('{user_input}') -> Sending Menu.")
        await self._send_main_menu(from_number, is_fallback=True)
    async def _send_main_menu(self, to_number, is_fallback=False):
        """Sends the Main Menu interactive message."""
        content = ButtonResponses.MAIN_MENU
        
        body_text = content["body"]
        if is_fallback:
            body_text = "I'm currently in Predictor Mode. Please use the buttons below to navigate, or just type the name of a team to start an analysis! 👇\n\n" + body_text

        interactive_obj = {
            "type": "button",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": body_text},
            "footer": {"text": content["footer"]},
            "action": {"buttons": [
                {"type": "reply", "reply": b} for b in content["buttons"]
            ]}
        }
        self.wa.send_interactive_message(to_number, interactive_obj)

    async def _send_schedule_browser(self, to_number):
        """Sends a high-level selection between Group Stage and Knockouts."""
        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": "📅 World Cup Schedule"},
            "body": {"text": "How would you like to browse the 2026 World Cup fixtures?"},
            "footer": {"text": "GoalMine AI 🏆"},
            "action": {
                "button": "Select Stage",
                "sections": [
                    {
                        "title": "Tournament Phases",
                        "rows": [
                            {"id": "Show_Groups_Menu", "title": "🌍 Group Stages", "description": "Browse Groups A-L"},
                            {"id": "Show_Knockouts_Menu", "title": "🏆 Knockout Rounds", "description": "Round of 32 to The Final"}
                        ]
                    }
                ]
            }
        }
        self.wa.send_interactive_message(to_number, interactive_obj)

    async def _send_groups_selection(self, to_number):
        """Deeper menu for Groups (Split into two messages if needed, or two sections)."""
        # We can use two sections, but 12 groups is still > 10 rows.
        # We'll split into A-F and G-L.
        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": "🌍 Group Stage Selector"},
            "body": {"text": "Select a group to see its matches and analysis options."},
            "action": {
                "button": "Choose Group",
                "sections": [
                    {
                        "title": "Groups A-F",
                        "rows": [{"id": f"Group_{g}", "title": f"Group {g}"} for g in ["A", "B", "C", "D", "E", "F"]]
                    },
                    {
                        "title": "Groups G-L",
                        "rows": [{"id": f"Group_{g}", "title": f"Group {g}"} for g in ["G", "H", "I", "J", "K", "L"]]
                    }
                ]
            }
        }
        # Wait, still 12 rows. Let's send two buttons instead? 
        # Actually, let's just show A-F and a row for "G-L Next ->"
        rows_1 = [{"id": f"Group_{g}", "title": f"Group {g}"} for g in ["A", "B", "C", "D", "E"]]
        rows_1.append({"id": "Show_Groups_G_L", "title": "Next: Groups G-L ➡️"})
        
        interactive_obj["action"]["sections"] = [{"title": "Select Group", "rows": rows_1}]
        self.wa.send_interactive_message(to_number, interactive_obj)

    async def _send_groups_g_l(self, to_number):
        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": "🌍 Group Stage Selector (G-L)"},
            "body": {"text": "Continuing the group stage fixtures..."},
            "action": {
                "button": "Choose Group",
                "sections": [
                    {
                        "title": "Groups G-L",
                        "rows": [{"id": f"Group_{g}", "title": f"Group {g}"} for g in ["G", "H", "I", "J", "K", "L"]]
                    },
                    {
                        "title": "Navigation",
                        "rows": [{"id": "Show_Groups_Menu", "title": "⬅️ Back to A-E"}]
                    }
                ]
            }
        }
        self.wa.send_interactive_message(to_number, interactive_obj)

    async def _send_knockouts_selection(self, to_number):
        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": "🏆 Knockout Stages"},
            "body": {"text": "The road to the trophy. Select a round to view upcoming knockout matches."},
            "action": {
                "button": "Choose Round",
                "sections": [
                    {
                        "title": "Knockout Brackets",
                        "rows": [
                            {"id": "Stage_Round_of_32", "title": "Round of 32"},
                            {"id": "Stage_Round_of_16", "title": "Round of 16"},
                            {"id": "Stage_Quarter-finals", "title": "Quarter-finals"},
                            {"id": "Stage_Semi-finals", "title": "Semi-finals"},
                            {"id": "Stage_Final", "title": "The Grand Final"}
                        ]
                    }
                ]
            }
        }
        self.wa.send_interactive_message(to_number, interactive_obj)

    async def _send_group_matches(self, to_number, filter_name, is_stage=False):
        """Sends matches for a specific group or stage, organized by 'Matchday'."""
        all_matches = orchestrator.SCHEDULE
        
        if is_stage:
            matches = [m for m in all_matches if m.get('stage') == filter_name]
        else:
            matches = [m for m in all_matches if m.get('group') == filter_name]

        if not matches:
            self.wa.send_message(to_number, f"⚠️ No matches found for {filter_name}.")
            await self._send_schedule_browser(to_number)
            return

        # Group matches into rounds/matchdays
        # For World Cup, usually 3 matchdays. We'll use the date to separate them or just count.
        rounds = {}
        for idx, m in enumerate(matches):
            date_str = m['date_iso'].split('T')[0]
            if date_str not in rounds:
                rounds[date_str] = []
            rounds[date_str].append(m)

        sections = []
        for i, (date, m_list) in enumerate(sorted(rounds.items())):
            round_label = f"Matchday {i+1} ({date})"
            rows = []
            for m in m_list:
                home = m['team_home']
                away = m['team_away']
                row_id = f"Analyze {home} vs {away}"
                title = f"{home[:9]} vs {away[:9]}"
                desc = f"{m['date_iso'].split('T')[1][:5]} @ {m.get('venue', 'Stadium')[:30]}"
                rows.append({"id": row_id, "title": title, "description": desc})
            
            sections.append({"title": round_label, "rows": rows})

        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": f"🏆 {filter_name}"},
            "body": {"text": f"Select a fixture from {filter_name} to launch the swarm intelligence analysis."},
            "footer": {"text": "GoalMine Tournament Browser"},
            "action": {
                "button": "View Fixtures",
                "sections": sections
            }
        }
        self.wa.send_interactive_message(to_number, interactive_obj)

    async def _send_help_menu(self, to_number):
        """Sends the Help/About info."""
        msg = (
            "🤖 *GoalMine AI Help*\n\n"
            "I am an advanced AI prediction engine for the 2026 World Cup.\n"
            "My Swarm of agents analyzes:\n"
            "• Performance Data (xG)\n"
            "• Market Odds\n"
            "• Tactical Matchups\n"
            "• Logistics (Weather/Travel)\n\n"
            "Tap *Analyze Matches* to start."
        )
        
        nav_obj = {
            "type": "button",
            "body": {"text": msg},
            "action": {"buttons": [
                {"type": "reply", "reply": {"id": "Show_MainMenu", "title": "🔙 Main Menu"}}
            ]}
        }
        self.wa.send_interactive_message(to_number, nav_obj)

    # ... (existing methods) ...

    async def _send_bet_menu(self, to_number):
        """Sends the Quantity Selection Menu."""
        content = ButtonResponses.BET_GENERATION_MENU
        
        interactive_obj = {
            "type": "button",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": content["body"]},
            "footer": {"text": content["footer"]},
            "action": {"buttons": [
                {"type": "reply", "reply": b} for b in content["buttons"]
            ]}
        }
        self.wa.send_interactive_message(to_number, interactive_obj)

    async def _trigger_bet_generation(self, to_number, count):
        """Generates the recommended bets using DB persistence."""
        self.wa.send_typing_indicator(to_number)
        
        try:
             recommendations = await generate_bet_recommendations(count, user_phone=to_number)
             self.wa.send_message(to_number, recommendations)
             
             await asyncio.sleep(1.0)
             await self._send_analysis_footer(to_number)
             
        except Exception as e:
            logger.error(f"Bet Gen failed: {e}")
            self.wa.send_message(to_number, "⚠️ Could not generate bets at this time.")
            await self._send_main_menu(to_number)

    async def _send_analysis_footer(self, to_number):
        """Sends the post-analysis navigation options."""
        interactive_obj = {
            "type": "button",
            "header": {"type": "text", "text": "📊 Analysis Complete"},
            "body": {"text": "What would you like to do next?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "Generate_Bets", "title": "🎲 Generate Bets"}},
                    {"type": "reply", "reply": {"id": "Show_Schedule", "title": "📅 More Matches"}},
                    {"type": "reply", "reply": {"id": "Show_MainMenu", "title": "🔙 Main Menu"}}
                ]
            }
        }
        self.wa.send_interactive_message(to_number, interactive_obj)

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

        home = match_info.get('home_team')
        away = match_info.get('away_team')
        venue_name = match_info.get('venue')

        # 1. Acknowledge & Typing
        self.wa.send_typing_indicator(to_number)
        ack_msg = ButtonResponses.ANALYSIS_START.format(home=home, away=away)
        self.wa.send_message(to_number, ack_msg)
        self.wa.send_typing_indicator(to_number) # Keep it alive

        # 2. Run Agents
        try:
            briefing = await orchestrator.generate_betting_briefing(match_info)
            
            # 2.1 [DATABASE PERSISTENCE] Save God View for future bet generation
            save_data = briefing.copy()
            save_data.update({
                'match': match_info,  # Store match info for context
                'budget': 100,  # Default, can be overridden later
                'num_bets': 1,  # Default
                'god_view': briefing
            })
            self.db.save_memory(to_number, save_data)
            logger.info(f"💾 God View saved to DB for {to_number}")
            
            # 3. Speak (The Closer)
            report = await orchestrator.format_the_closer_report(briefing)
            
            # Send chunks
            import asyncio
            import re
            parts = re.split(r'(?=# BET \d+)', report)
            for part in parts:
                if part.strip():
                    self.wa.send_typing_indicator(to_number)
                    await asyncio.sleep(0.5) # Simulate typing
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
                            venue_data['lat'], 
                            venue_data['lon'], 
                            name=venue_name, 
                            address=f"Official World Cup 2026 Venue • {venue_data.get('tz_offset', '')} UTC"
                        )
                except Exception as ve:
                    logger.warning(f"Could not load venue data: {ve}")

            # 5. Show Navigation Footer instead of auto-main menu
            await asyncio.sleep(1.0)
            await self._send_analysis_footer(to_number)

        except Exception as e:
            logger.error(f"Strict Analysis failed: {e}")
            self.wa.send_message(to_number, "⚠️ operational error.")
