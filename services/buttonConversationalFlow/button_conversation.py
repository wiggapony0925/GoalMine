import json
import asyncio
from core.log import get_logger
from services import orchestrator
from core.config import settings
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
             # Format: "Analyze TeamA"
             team_name = user_input.replace("Analyze", "").strip()
             await self._trigger_analysis(from_number, team_name)
             return

        elif user_input == "Show_Schedule":
            await self._send_schedule_list(from_number)
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

        elif user_input in ["Bets_1", "Bets_3", "Bets_5"]:
            count = int(user_input.split("_")[1])
            await self._trigger_bet_generation(from_number, count)
            return

        # 3. FALBACK: User Typed Text -> Send Main Menu
        logger.info(f"⛔ Strict Mode: Rejecting text ('{user_input}') -> Sending Menu.")
        await self._send_main_menu(from_number)
    async def _send_main_menu(self, to_number):
        """Sends the Main Menu interactive message."""
        content = ButtonResponses.MAIN_MENU
        
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

    async def _send_schedule_list(self, to_number):
        """
        Sends upcoming matches as an INTERACTIVE LIST MESSAGE.
        """
        from datetime import datetime
        
        # Get next 8 matches via Orchestrator (List allows up to 10 rows)
        upcoming = orchestrator.get_next_matches(limit=8)
        
        if not upcoming:
            self.wa.send_message(to_number, "📅 No upcoming matches found.")
            await self._send_main_menu(to_number)
            return

        # Build Rows
        rows = []
        for m in upcoming:
            home = m['team_home']
            away = m['team_away']
            dt = datetime.fromisoformat(m['date_iso'])
            time_str = dt.strftime("%I:%M %p").lstrip("0")
            venue = m.get('venue', 'Stadium')
            
            # Row ID: Triggers analysis
            row_id = f"Analyze {home}"
            
            # Title: Max 24 chars
            title = f"{home[:9]} vs {away[:9]}"
            
            # Description: Max 72 chars (Time + Venue)
            desc = f"{time_str} @ {venue}"[:72]
            
            rows.append({
                "id": row_id,
                "title": title,
                "description": desc
            })

        # Construct Interactive List Object
        interactive_obj = {
            "type": "list",
            "header": {
                "type": "text",
                "text": "⚽ Match Schedule"
            },
            "body": {
                "text": "Here are the upcoming matches. Select one to launch the GoalMine Swarm Analysis."
            },
            "footer": {
                "text": "GoalMine AI 🏆"
            },
            "action": {
                "button": "View Matches",
                "sections": [
                    {
                        "title": "Upcoming Fixtures",
                        "rows": rows
                    }
                ]
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

    async def _trigger_analysis(self, to_number, team_home):
        """Runs the Swarm and persists data to DB."""
        # Find the full match object
        match_info = orchestrator.find_match_by_home_team(team_home)
        
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
