import re
import json
import logging
from services import orchestrator
from agents.gatekeeper.gatekeeper import Gatekeeper
from core.responses import Responses

# Get logger from the central setup if possible, or just standard
logger = logging.getLogger("GoalMine")

class ConversationHandler:
    """
    Manages the logic flow for user interactions.
    Decouples app.py from business logic.
    """
    MEMORY_FILE = "data/memory.json"
    
    def __init__(self, wa_client, memory_store=None):
        self.wa = wa_client
        self.memory = self._load_memory()
        
    def _load_memory(self):
        try:
            with open(self.MEMORY_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _sync_memory(self):
        try:
            with open(self.MEMORY_FILE, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to sync memory: {e}")

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
        logger.info(f"Q&A Check for {from_number}: Memory={from_number in self.memory}, Intent={intent}")
        if from_number in self.memory and intent in ["CHIT_CHAT", "OFF_TOPIC", "BETTING"]:
            body_low = msg_body.lower()
            
            # STAKING UPDATE CHECK: "I have $50", "Budget is 100"
            budget_match = re.search(r'\$(\d+)', body_low) or re.search(r'(\d+)\s*(?:dollars|bucks|budget|amount)', body_low)
            if budget_match:
                new_budget = int(budget_match.group(1))
                self.wa.send_message(from_number, f"💰 *Budget Updated:* Recalculating for ${new_budget}...")
                
                # Re-run Quant & Format Report
                memory = self.memory[from_number]
                # Re-calculate quant (we didn't save final_xg as easy vars, but they are in memory)
                from agents.quant.quant import run_quant_engine
                
                # We need to pass the data back to the quant engine
                # For now, let's just use the LLM to 're-scale' it via Q&A prompt
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
                    self.memory[from_number], 
                    msg_body,
                    num_bets=num_bets
                )
                if answer:
                    self.wa.send_message(from_number, answer)
                    return True
        return False

    async def _handle_schedule(self, from_number):
        brief = orchestrator.get_morning_brief_content()
        if brief:
            self.wa.send_message(from_number, brief)
        else:
            self.wa.send_message(from_number, Responses.NO_MATCHES_TODAY)

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
            self.memory[from_number] = briefing
            self._sync_memory()
            logger.info(f"🧠 GOD VIEW JSON ({from_number}):\n{json.dumps(briefing, indent=2)}")
            
            # Generate Final Report
            final_report = await orchestrator.format_the_closer_report(briefing, num_bets=num_bets)
            self.wa.send_message(from_number, final_report)
