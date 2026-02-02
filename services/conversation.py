import re
import json
from core.log import get_logger
from services import orchestrator
from agents.gatekeeper.gatekeeper import Gatekeeper
from core.database import Database
from data.scripts.responses import Responses
from core.llm import query_llm

logger = get_logger("Conversation")

class ConversationHandler:
    """
    Natural Conversation Handler - The Ghost Logic.
    Handles conversations without menus, using context awareness and natural language.
    """
    def __init__(self, wa_client):
        self.wa = wa_client
        self.db = Database()

    async def handle_incoming_message(self, from_number, msg_body):
        """
        Pure Natural Language Processor with context awareness.
        """
        # 1. LOAD CONTEXT (Short-term memory)
        user_state = self.db.load_memory(from_number) or {}
        last_match = user_state.get('match')  # Last analyzed match
        
        logger.info(f"📨 Message from {from_number}: {msg_body[:50]}...")
        if last_match:
            # Handle both dict and string formats
            match_str = last_match.get('match', str(last_match)) if isinstance(last_match, dict) else str(last_match)
            logger.debug(f"Context: {match_str}")

        # 2. CLASSIFY INTENT & EXTRACT DATA
        intent, extracted_data = await Gatekeeper.classify_intent(msg_body)
        logger.info(f"🎯 Intent: {intent}, Extracted: {extracted_data}")
        
        # --- SCENARIO A: CONFIRMATION ("Yeah", "Do it", "Sure") ---
        # If we have an active match and user confirms, run analysis
        if last_match and self._is_confirmation(msg_body):
            logger.info("✅ Confirmation detected. Running analysis on active match.")
            await self._run_analysis(from_number, last_match, extracted_data)
            return

        # --- SCENARIO B: BETTING COMMAND WITH EXISTING GOD VIEW ---
        # If user already has analysis AND is asking about budget/bets, use Strategic Advisor
        god_view = user_state.get('god_view')
        if intent == "BETTING" and god_view:
            # User has existing analysis - they're asking follow-up betting question
            strategy_keywords = ["dollar", "$", "budget", "spend", "bet", "get on", "money", "stake",
                                 "parlay", "parley", "hedge", "split", "strategy", "should i"]
            if any(keyword in msg_body.lower() for keyword in strategy_keywords) and not self._mentions_new_teams(msg_body, last_match):
                logger.info("💰 Budget question with existing God View. Using Strategic Advisor.")
                # Pass the budget from extracted_data to the advisor
                if extracted_data and extracted_data.get('budget'):
                    god_view['user_budget'] = extracted_data['budget']
                answer = await self._strategic_betting_advisor(user_state, msg_body)
                self.wa.send_message(from_number, answer)
                return

        # --- SCENARIO C: NEW BETTING COMMAND ---
        if intent == "BETTING":
            await self._handle_betting_natural(from_number, msg_body, extracted_data)

        # --- SCENARIO D: SCHEDULE ---
        elif intent == "SCHEDULE":
            await self._handle_schedule(from_number, msg_body)

        # --- SCENARIO E: STRATEGIC BETTING QUESTIONS ---
        # Detect questions about betting strategy using God View
        elif intent == "CONV" and last_match:
            strategic_keywords = ["parlay", "parley", "split", "hedge", "strategy", "should i", 
                                 "multiple bets", "spread", "diversify", "allocate", "portfolio"]
            
            if any(keyword in msg_body.lower() for keyword in strategic_keywords):
                logger.info("💡 Strategic betting question detected.")
                answer = await self._strategic_betting_advisor(user_state, msg_body)
                self.wa.send_message(from_number, answer)
                return
            
            # Regular follow-up question about the match
            if "?" in msg_body:
                logger.info("❓ Follow-up question detected.")
                answer = await self._answer_contextual_question(user_state, msg_body)
                self.wa.send_message(from_number, answer)
            else:
                # General chat
                reply = await self._handle_general_conversation(msg_body)
                self.wa.send_message(from_number, reply)
        
        # --- SCENARIO F: GENERAL CONVERSATION ---
        elif intent == "CONV":
            reply = await self._handle_general_conversation(msg_body)
            self.wa.send_message(from_number, reply)

    async def _handle_betting_natural(self, from_number, msg_body, extracted_data):
        """
        Natural betting flow with entity extraction from Gatekeeper.
        """
        user_state = self.db.load_memory(from_number) or {}
        last_match = user_state.get('match')
        match_info = None
        
        # 1. Clean message for matching
        clean_msg = re.sub(r'[^\w\s]', '', msg_body.lower().strip())
        
        # 2. If Gatekeeper extracted teams, use them
        if extracted_data and extracted_data.get('teams'):
            teams = extracted_data['teams']
            match_info = await self._resolve_match_from_teams(teams)
            
            if match_info:
                # Add extracted budget/num_bets
                if 'budget' in extracted_data:
                    match_info['budget'] = extracted_data['budget']
                if 'num_bets' in extracted_data:
                    match_info['num_bets'] = extracted_data['num_bets']
                
                await self._run_analysis(from_number, match_info, extracted_data)
                return
            else:
                self.wa.send_message(from_number, Responses.UNKNOWN_TEAMS)
                return
        
        # 3. Context Context Context! 
        # If intent is BETTING and we have a last_match, and no new teams were found above,
        # we check if they are being vague or referring to "it/this/that game"
        vague_keywords = ["analyze", "analysis", "it", "that", "this", "game", "match", "run", "do it", "go"]
        is_vague = any(word in clean_msg.split() for word in vague_keywords)
        
        if is_vague and last_match:
            logger.info("Fuzzy context match: User is referring to last_match.")
            await self._run_analysis(from_number, last_match, extracted_data)
            return

        # 4. Fallback: Check for "next match" if no context
        vague_start_keywords = ["analyze", "run it", "show me a bet", "whats the move"]
        if any(keyword in clean_msg for keyword in vague_start_keywords):
            next_match = orchestrator.get_next_scheduled_match()
            if next_match:
                match_name = f"{next_match.get('home_team')} vs {next_match.get('away_team')}"
                resp = Responses.get_confirmation(match_name)
                self.db.save_memory(from_number, {'match': next_match})
                self.wa.send_message(from_number, resp)
                return
            else:
                self.wa.send_message(from_number, Responses.NO_MATCHES_TODAY)
                return
        
        # 5. Last resort: Try deep extraction
        self.wa.send_message(from_number, Responses.get_reading())
        match_info = await orchestrator.extract_match_details_from_text(msg_body)
        
        if match_info and match_info.get('home_team'):
            await self._run_analysis(from_number, match_info, extracted_data)
        elif last_match:
            logger.info("Extraction failed but last_match exists. Using it.")
            await self._run_analysis(from_number, last_match, extracted_data)
        else:
            self.wa.send_message(from_number, Responses.UNKNOWN_TEAMS)

    async def _run_analysis(self, user_phone, match_info, extracted_data=None):
        """
        Triggers the swarm and speaks the result.
        """
        # Extract parameters
        budget = extracted_data.get('budget', 100) if extracted_data else match_info.get('budget', 100)
        num_bets = extracted_data.get('num_bets', 1) if extracted_data else match_info.get('num_bets', 1)
        
        home = match_info.get('home_team', 'Team A')
        away = match_info.get('away_team', 'Team B')
        
        # 1. Acknowledge using Responses
        launch_msg = Responses.get_launch(f"{home} vs {away}")
        self.wa.send_message(user_phone, launch_msg)
        
        # 2. Run the Agents
        try:
            briefing = await orchestrator.generate_betting_briefing(match_info, user_budget=budget)
            
            # 3. Save to Memory (for follow-up questions)
            save_data = briefing.copy()
            save_data.update({
                'match': match_info, # Ensure this stays a dict
                'budget': budget,
                'num_bets': num_bets,
                'god_view': briefing
            })
            self.db.save_memory(user_phone, save_data)
            
            logger.info(f"🧠 Context saved for {user_phone}")
            
            # 4. The Closer speaks
            report = await orchestrator.format_the_closer_report(briefing, num_bets=num_bets)
            self.wa.send_message(user_phone, report)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.wa.send_message(user_phone, Responses.ANALYSIS_ERROR)

    async def _answer_contextual_question(self, user_state, question):
        """
        Answers questions about the last analysis using saved context.
        """
        from prompts.system_prompts import FOLLOW_UP_QA_PROMPT
        
        try:
            context_str = json.dumps(user_state, indent=2)
            formatted_prompt = FOLLOW_UP_QA_PROMPT.format(context=context_str)
            
            answer = await query_llm(formatted_prompt, question, temperature=0.7)
            return answer
        except Exception as e:
            logger.error(f"Contextual Q&A failed: {e}")
            return Responses.CONTEXT_ERROR

    async def _strategic_betting_advisor(self, user_state, question):
        """
        Advanced betting strategist using God View JSON.
        """
        from prompts.system_prompts import STRATEGIC_ADVISOR_PROMPT
        
        try:
            god_view_str = json.dumps(user_state, indent=2)
            formatted_prompt = STRATEGIC_ADVISOR_PROMPT.format(god_view=god_view_str)
            
            logger.info(f"💡 Strategic Advisor Query: {question[:100]}...")
            answer = await query_llm(formatted_prompt, question, temperature=0.7, config_key="closer")
            return answer
        except Exception as e:
            logger.error(f"Strategic Betting Advisor failed: {e}")
            return "I'm having trouble analyzing that strategy right now. Could you rephrase your question?"

    async def _handle_general_conversation(self, message):
        """
        Handles greetings and general chat.
        """
        from prompts.system_prompts import CONVERSATION_ASSISTANT_PROMPT
        
        try:
            reply = await query_llm(CONVERSATION_ASSISTANT_PROMPT, message, temperature=0.7)
            return reply
        except Exception as e:
            logger.error(f"General conversation failed: {e}")
            from core.responses import Responses
            return Responses.GENERAL_HELP

    async def _resolve_match_from_teams(self, teams):
        """
        Finds match info from schedule based on team names.
        """
        if not teams:
            return None
        
        from data.scripts.data import SCHEDULE
        
        team_a = teams[0].lower()
        team_b = teams[1].lower() if len(teams) > 1 else None
        
        for match in SCHEDULE:
            home = match.get('team_home', '').lower()
            away = match.get('team_away', '').lower()
            
            # Check if both teams match
            if team_b:
                if (team_a in home and team_b in away) or (team_a in away and team_b in home):
                    return {
                        'home_team': match.get('team_home'),
                        'away_team': match.get('team_away'),
                        'venue': match.get('venue'),
                        'date': match.get('date_iso')
                    }
            else:
                # Single team - find their next match
                if team_a in home or team_a in away:
                    return {
                        'home_team': match.get('team_home'),
                        'away_team': match.get('team_away'),
                        'venue': match.get('venue'),
                        'date': match.get('date_iso')
                    }
        
        return None

    async def _handle_schedule(self, from_number, msg_body):
        """Natural schedule responses."""
        low_msg = msg_body.lower()
        
        if any(w in low_msg for w in ["full", "all", "week"]):
            resp = orchestrator.get_schedule_brief()
        elif any(w in low_msg for w in ["4", "four", "menu", "list"]):
            resp = orchestrator.get_schedule_menu(limit=4)
        else:
            resp = orchestrator.get_next_match_content()
            
        self.wa.send_message(from_number, resp)

    def _is_confirmation(self, text):
        """
        Detects confirmations like 'Yes', 'Do it', 'Go ahead'.
        """
        affirmations = ["yes", "yeah", "yep", "do it", "go", "sure", "ok", "okay", 
                       "bet", "run it", "let's go", "yup", "absolutely", "please"]
        text_lower = text.lower().strip()
        
        # Exact match or contains affirmation
        return text_lower in affirmations or any(w in text_lower for w in affirmations)

    def _mentions_new_teams(self, text, current_match):
        """
        Check if user mentions different teams than the current match.
        Returns True if they're asking about a NEW match.
        """
        if not current_match:
            return False
            
        # Get current teams
        current_home = current_match.get('home_team', '').lower()
        current_away = current_match.get('away_team', '').lower()
        
        text_lower = text.lower()
        
        # List of common team name patterns that would indicate new match
        new_match_indicators = [" vs ", " versus ", " against ", " v "]
        
        # If message contains "vs" or similar, check if it's different teams
        if any(indicator in text_lower for indicator in new_match_indicators):
            # They're mentioning a matchup - is it the same one?
            if current_home in text_lower and current_away in text_lower:
                return False  # Same match
            else:
                return True  # New match mentioned
        
        return False  # No new match mentioned
