from services import orchestrator
from agents.gatekeeper.gatekeeper import Gatekeeper
import json
import logging

# Get logger from the central setup if possible, or just standard
logger = logging.getLogger("GoalMine")

class ConversationHandler:
    """
    Manages the logic flow for user interactions.
    Decouples app.py from business logic.
    """
    
    def __init__(self, wa_client, memory_store):
        self.wa = wa_client
        self.memory = memory_store

    async def handle_incoming_message(self, from_number, msg_body):
        """
        Main entry point for message processing.
        """
        # 1. Classify Intent
        intent, _ = await Gatekeeper.classify_intent(msg_body)
        
        # 2. Q&A Interception (Cost efficient check)
        if await self._try_handle_qa(from_number, msg_body, intent):
            return

        # 3. Route by Intent
        if intent == "CHIT_CHAT" or intent == "OFF_TOPIC":
            resp = Gatekeeper.get_response(intent)
            self.wa.send_message(from_number, resp)

        elif intent == "SCHEDULE":
            await self._handle_schedule(from_number)

        elif intent == "BETTING":
            await self._handle_betting(from_number, msg_body)

    async def _try_handle_qa(self, from_number, msg_body, intent):
        """
        Checks if the user is asking a question about active context.
        Returns True if handled.
        """
        if from_number in self.memory and intent in ["CHIT_CHAT", "OFF_TOPIC", "BETTING"]:
            # Heuristic: Is it a question?
            if "?" in msg_body or any(w in msg_body.lower() for w in ["why", "how", "what", "explain", "detail"]):
                answer = await orchestrator.answer_follow_up_question(self.memory[from_number], msg_body)
                if answer:
                    self.wa.send_message(from_number, answer)
                    return True
        return False

    async def _handle_schedule(self, from_number):
        brief = orchestrator.get_morning_brief_content()
        if brief:
            self.wa.send_message(from_number, brief)
        else:
            self.wa.send_message(from_number, "⛔ No World Cup matches scheduled for today within the system.")

    async def _handle_betting(self, from_number, msg_body):
        todays_games = orchestrator.get_todays_matches()
        match_info = None

        # A. Quick Menu Selection ("1", "2")
        if msg_body.strip() in ["1", "2", "3", "4", "5"] and todays_games:
            try:
                idx = int(msg_body.strip()) - 1
                match_info = orchestrator.get_match_info_from_selection(idx)
                if match_info:
                    self.wa.send_message(from_number, f"🎯 Targeting {match_info['home_team']} vs {match_info['away_team']}...")
            except ValueError:
                pass 
        
        # B. Natural Language Extraction
        if not match_info:
            self.wa.send_message(from_number, "🤖 Reading match details...")
            match_info = await orchestrator.extract_match_details_from_text(msg_body)
            
            if not match_info:
                if not todays_games:
                    self.wa.send_message(from_number, "⛔ No matches today.\nTry 'Analyze France vs Brazil'.")
                else:
                    self.wa.send_message(from_number, "❓ I couldn't identify the teams. Please specify them clearly.")
                return 

            # Validation
            is_valid = orchestrator.validate_match_request(match_info)
            if not is_valid:
                 self.wa.send_message(from_number, f"⚠️ Match not found in World Cup 2026 Schedule.\nI only track official tournament fixtures.")
                 return

        # C. Execute Swarm
        if match_info:
            self.wa.send_message(from_number, f"🕵️ Identified: {match_info['home_team']} vs {match_info['away_team']}. Launching Swarm...")
            
            # Run Analysis
            briefing = await orchestrator.generate_betting_briefing(match_info)
            
            # Save Context (God View)
            self.memory[from_number] = briefing
            logger.info(f"🧠 GOD VIEW JSON ({from_number}):\n{json.dumps(briefing, indent=2)}")
            
            # Generate Final Report
            final_report = await orchestrator.format_the_closer_report(briefing)
            self.wa.send_message(from_number, final_report)
