import re
import logging
from services import orchestrator
from agents.gatekeeper.gatekeeper import Gatekeeper
from core.database import Database
from core.responses import Responses

# Get logger from the central setup if possible, or just standard
logger = logging.getLogger("GoalMine")

class ConversationHandler:
    """
    Manages the logic flow for user interactions.
    Decouples app.py from business logic.
    """
    def __init__(self, wa_client):
        self.wa = wa_client
        self.db = Database()

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
        if intent == "CONV":
            resp = await orchestrator.handle_general_conversation(msg_body)
            self.wa.send_message(from_number, resp)

        elif intent == "SCHEDULE":
            await self._handle_schedule(from_number, msg_body)

        elif intent == "BETTING":
            await self._handle_betting(from_number, msg_body)

    async def _try_handle_qa(self, from_number, msg_body, intent):
        """
        Checks if the user is asking a question about active context.
        Returns True if handled.
        """
        memory = self.db.load_memory(from_number)
        logger.info(f"Q&A Check for {from_number}: Memory={'Found' if memory else 'None'}, Intent={intent}")
        
        if memory and intent in ["CONV", "BETTING"]:
            body_low = msg_body.lower()
            
            # STAKING UPDATE CHECK: "I have $50", "Budget is 100"
            budget_match = re.search(r'\$(\d+)', body_low) or re.search(r'(\d+)\s*(?:dollars|bucks|budget|amount)', body_low)
            if budget_match:
                new_budget = int(budget_match.group(1))
                self.wa.send_message(from_number, f"💰 *Budget Updated:* Recalculating for ${new_budget}...")
                
                # Re-calculate quant via Q&A prompt
                answer = await orchestrator.answer_follow_up_question(
                    memory, 
                    f"Update staking for a ${new_budget} budget. Show me the specific bets and amounts."
                )
                if answer:
                    self.wa.send_message(from_number, answer)
                    return True

            # Heuristic: Is it a question?
            qa_keywords = ["why", "how", "what", "explain", "detail", "weather", "location", "prediction", "bets", "play", "who", "when"]
            if "?" in msg_body or any(w in body_low for w in qa_keywords):
                
                # Check for "3 bets" style requests
                num_bets_match = re.search(r'(\d+)\s*bets?', body_low)
                num_bets = int(num_bets_match.group(1)) if num_bets_match else 1
                
                answer = await orchestrator.answer_follow_up_question(
                    memory, 
                    msg_body,
                    num_bets=num_bets
                )
                if answer:
                    self.wa.send_message(from_number, answer)
                    return True
        return False

    async def _handle_schedule(self, from_number, msg_body):
        low_msg = msg_body.lower()
        
        if any(w in low_msg for w in ["full", "all", "week"]):
            resp = orchestrator.get_schedule_brief()
        elif any(w in low_msg for w in ["4", "four", "menu", "list"]):
            resp = orchestrator.get_schedule_menu(limit=4)
        else:
            # Default to the "Next Match" view you had before
            resp = orchestrator.get_next_match_content()
            
        self.wa.send_message(from_number, resp)

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
            # CHECK FOR SIMPLE "Analyze" ON ITS OWN
            if msg_body.lower().strip() == "analyze":
                 fallback_match = orchestrator.get_next_scheduled_match()
                 if fallback_match:
                      match_info = fallback_match
                      self.wa.send_message(from_number, f"🔮 *Next Match Found:* Analyzing *{match_info['home_team']} vs {match_info['away_team']}*")

            if not match_info:
                self.wa.send_message(from_number, Responses.get_reading())
                match_info = await orchestrator.extract_match_details_from_text(msg_body)
            
            # SMART DEFAULT: If extraction fails but user mentioned "Analyze" among other words
            if not match_info and "analyze" in msg_body.lower():
                 fallback_match = orchestrator.get_next_scheduled_match()
                 if fallback_match:
                      match_info = fallback_match
                      self.wa.send_message(from_number, f"🔮 *Assumption:* Analyzing next match *{match_info['home_team']} vs {match_info['away_team']}*")

            if not match_info:
                if not todays_games:
                    self.wa.send_message(from_number, Responses.NO_MATCHES_TODAY)
                else:
                    self.wa.send_message(from_number, Responses.UNKNOWN_TEAMS)
                return 

            # Validation
            is_valid = orchestrator.validate_match_request(match_info)
            if not is_valid:
                 self.wa.send_message(from_number, Responses.INVALID_SCHEDULE)
                 return

        # C. Staking Extraction
        budget_match = re.search(r'\$(\d+)', msg_body) or re.search(r'(\d+)\s*(?:dollars|bucks)', msg_body.lower())
        user_budget = int(budget_match.group(1)) if budget_match else 100
        
        num_bets_match = re.search(r'(\d+)\s*bets?', msg_body.lower())
        num_bets = int(num_bets_match.group(1)) if num_bets_match else 1

        # D. Execute Swarm
        if match_info:
            launch_msg = Responses.get_launch(f"{match_info['home_team']} vs {match_info['away_team']}")
            self.wa.send_message(from_number, launch_msg)
            
            # Run Analysis
            briefing = await orchestrator.generate_betting_briefing(match_info, user_budget=user_budget)
            
            # Save Context (God View)
            self.db.save_memory(from_number, briefing)
            logger.info(f"🧠 GOD VIEW PERSISTED ({from_number})")
            
            # Generate Final Report
            final_report = await orchestrator.format_the_closer_report(briefing, num_bets=num_bets)
            self.wa.send_message(from_number, final_report)
