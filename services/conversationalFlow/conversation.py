import re
import json
import asyncio
from core.log import get_logger
from services import orchestrator
from agents.gatekeeper.gatekeeper import Gatekeeper
from core.initializer.database import Database
from prompts.messages_prompts import Responses
from core.initializer.llm import query_llm
from core.config import settings

logger = get_logger("Conversation")


class ConversationHandler:
    """
    Nat
    ural Conversation Handler - The Ghost Logic.
    Handles conversations without menus, using context awareness and natural language.
    """

    def __init__(self, wa_client):
        self.wa = wa_client
        self.db = Database()

    async def handle_incoming_message(self, from_number, msg_body):
        """
        Pure Natural Language Processor with context awareness.
        """
        # Track current user for unified bet generation
        self._current_user_phone = from_number

        # 1. LOAD CONTEXT (Short-term memory)
        user_state = self.db.load_memory(from_number) or {}
        last_match = user_state.get("match")  # Last analyzed match

        logger.info(f"📨 Message from {from_number}: {msg_body[:50]}...")
        if last_match:
            # Handle both dict and string formats
            match_str = (
                last_match.get("match", str(last_match))
                if isinstance(last_match, dict)
                else str(last_match)
            )
            logger.debug(f"Context: {match_str}")

        # 2. CLASSIFY INTENT & EXTRACT DATA
        intent, extracted_data = await Gatekeeper.classify_intent(msg_body)
        extracted_data = extracted_data or {}
        logger.info(f"🎯 Intent: {intent}, Extracted: {extracted_data}")

        # 2.1 SESSION TIMING & GREETING
        # Check session age for context-awareness (Cold Start vs mid-convo)
        session_info = self.db.get_session_info(from_number)
        age_mins = session_info.get("age_minutes", 9999)
        warm_start_limit = settings.get(
            "GLOBAL_APP_CONFIG.retention.session_warm_start_mins", 45
        )
        is_cold_start = age_mins > warm_start_limit

        words = set(msg_body.lower().split())
        greeting_words = {
            "hi",
            "hello",
            "hola",
            "hey",
            "sup",
            "yo",
            "start",
            "help",
            "rules",
        }
        is_greeting = not (words.isdisjoint(greeting_words))
        has_seen_rules = user_state.get("has_seen_v2_rules", False)
        manual_rules = "help" in words or "rules" in words

        if is_cold_start or (is_greeting and not has_seen_rules) or manual_rules:
            logger.info(
                f"👋 Cold Start / Greeting detected ({age_mins} mins). Initializing Context."
            )

            # Wipe logs and session if cold start
            if is_cold_start:
                from core.log import clear_log

                clear_log()
                user_state = {"has_seen_v2_rules": True}  # Start fresh context

            # MODE CHECK: If Button-Strict, use Template
            if settings.get(
                "GLOBAL_APP_CONFIG.app.interaction_mode"
            ) == "BUTTON_STRICT" and settings.get(
                "GLOBAL_APP_CONFIG.whatsapp.use_templates"
            ):
                template_name = settings.get(
                    "BUTTON_FLOW_APP_CONFIG.welcome_template", "goalmine_welcome"
                )
                self.wa.send_template_message(
                    from_number,
                    template_name,
                    [],
                    fallback_text=Responses.get_greeting(),
                )
            else:
                self.wa.send_message(from_number, Responses.get_greeting())

            # Mark that they've seen this version of the rules
            user_state["has_seen_v2_rules"] = True
            self.db.save_memory(from_number, user_state)
            return

        # --- SCENARIO A: SCHEDULE ---
        if intent == "SCHEDULE":
            logger.info("📅 Scenario A: Schedule query.")
            await self._handle_schedule(from_number, msg_body, extracted_data)
            return

        # --- SCENARIO B: NEW BETTING COMMAND ---
        if intent == "BETTING":
            logger.info("🎯 Scenario B: New Betting command.")
            await self._handle_betting_natural(from_number, msg_body, extracted_data)
            return

        # --- SCENARIO C: CONFIRMATION ("Yeah", "Do it", "Sure") ---
        # If we have an active match and user confirms, run analysis
        if last_match and self._is_confirmation(msg_body):
            logger.info("✅ Scenario C: Confirmation detected.")
            await self._run_analysis(from_number, last_match, extracted_data)
            return

        # --- SCENARIO D: STRATEGIC ADVICE ---
        # If user already has analysis AND is asking about budget/bets, use Strategic Advisor
        god_view = user_state.get("god_view")
        if god_view and not self._mentions_new_teams(msg_body, last_match):
            strategy_keywords = [
                "dollar", "$", "budget", "spend", "bet", "get on", "money", "stake",
                "parlay", "parley", "hedge", "split", "strategy", "should i",
                "more", "other", "another", "else", "alternative",
            ]

            is_strategy_ask = any(keyword in msg_body.lower() for keyword in strategy_keywords)

            # If they are asking for "more" or "other" games, but intent is CONV (not strategy),
            # they might want the schedule. But strategy ask is stricter here.
            if is_strategy_ask:
                logger.info("💰 Strategy/Follow-up detected with existing God View. Using Strategic Advisor.")
                if extracted_data and extracted_data.get("budget"):
                    god_view["user_budget"] = extracted_data["budget"]
                answer = await self._strategic_betting_advisor(user_state, msg_body)
                await self._send_multi(from_number, answer)
                return

        # --- SCENARIO E: STRATEGIC BETTING QUESTIONS ---
        # Detect questions about betting strategy using God View
        elif intent == "CONV" and last_match:
            strategic_keywords = [
                "parlay",
                "parley",
                "split",
                "hedge",
                "strategy",
                "should i",
                "multiple bets",
                "spread",
                "diversify",
                "allocate",
                "portfolio",
            ]

            if any(keyword in msg_body.lower() for keyword in strategic_keywords):
                logger.info("💡 Strategic betting question detected.")
                answer = await self._strategic_betting_advisor(user_state, msg_body)
                await self._send_multi(from_number, answer)
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
            logger.info("💬 Scenario F: General conversation.")
            reply = await self._handle_general_conversation(msg_body)
            self.wa.send_message(from_number, reply)
            return

    async def _handle_betting_natural(self, from_number, msg_body, extracted_data):
        """
        Natural betting flow with entity extraction from Gatekeeper.
        """
        user_state = self.db.load_memory(from_number) or {}
        last_match = user_state.get("match")
        match_info = None

        # 1. Clean message for matching
        clean_msg = re.sub(r"[^\w\s]", "", msg_body.lower().strip())

        # 2. If Gatekeeper extracted teams, use them
        if extracted_data and extracted_data.get("teams"):
            teams = extracted_data["teams"]
            match_info = await self._resolve_match_from_teams(teams)

            if match_info:
                # Add extracted budget/num_bets
                if "budget" in extracted_data:
                    match_info["budget"] = extracted_data["budget"]
                if "num_bets" in extracted_data:
                    match_info["num_bets"] = extracted_data["num_bets"]

                await self._run_analysis(from_number, match_info, extracted_data)
                return
            else:
                self.wa.send_message(from_number, Responses.UNKNOWN_TEAMS)
                return

        # 3. Context Context Context!
        # If intent is BETTING and we have a last_match, and no new teams were found above,
        # we check if they are being vague or referring to "it/this/that game"
        vague_keywords = [
            "analyze",
            "analysis",
            "it",
            "that",
            "this",
            "game",
            "match",
            "run",
            "do it",
            "go",
        ]
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
                match_name = (
                    f"{next_match.get('home_team')} vs {next_match.get('away_team')}"
                )
                resp = Responses.get_confirmation(match_name)
                self.db.save_memory(from_number, {"match": next_match})
                self.wa.send_message(from_number, resp)
                return
            else:
                self.wa.send_message(from_number, Responses.NO_MATCHES_TODAY)
                return

        # 5. Last resort: Try deep extraction
        self.wa.send_message(from_number, Responses.get_reading())
        match_info = await orchestrator.extract_match_details_from_text(msg_body)

        if match_info and match_info.get("home_team"):
            await self._run_analysis(from_number, match_info, extracted_data)
        elif last_match and is_vague:
            # Only use last_match if there was SOME intent to refer to it, processed in step 3.
            # If we are here, step 3 failed or wasn't triggered?
            # Actually step 3 returns. So if we are here, is_vague was false or processed.
            # This fallback (lines 193-195 previously) is dangerous.
            # If extraction failed and it wasn't vague, we should ask for clarification, NOT guess the last match.
            self.wa.send_message(from_number, Responses.UNKNOWN_TEAMS)
        else:
            self.wa.send_message(from_number, Responses.UNKNOWN_TEAMS)

    async def _run_analysis(self, user_phone, match_info, extracted_data=None):
        """
        Triggers the swarm and speaks the result.
        """
        # Extract parameters
        default_budget = settings.get("GLOBAL_APP_CONFIG.strategy.default_budget", 100)
        budget = (
            extracted_data.get("budget", default_budget)
            if extracted_data
            else match_info.get("budget", default_budget)
        )
        num_bets = (
            extracted_data.get("num_bets", 1)
            if extracted_data
            else match_info.get("num_bets", 1)
        )

        home = match_info.get("home_team", "Team A")
        away = match_info.get("away_team", "Team B")

        # 1. TBD PROTECTION: Check if teams are confirmed
        if "TBD" in home.upper() or "TBD" in away.upper():
            logger.info(
                f"🔒 TBD Block: User tried to analyze {home} vs {away} via Chat."
            )
            self.wa.send_message(
                user_phone,
                "🔓 *Match Locked:* This fixture is still 'To Be Determined'.\n\nI can only analyze matches once the official teams are confirmed. Please check back after the previous round is complete! 🏆",
            )
            return

        # 2. Acknowledge using Responses
        launch_msg = Responses.get_launch(f"{home} vs {away}")
        self.wa.send_message(user_phone, launch_msg)

        # 2. Run the Agents
        try:
            briefing = await orchestrator.generate_betting_briefing(
                match_info, user_budget=budget
            )
            briefing["user_phone"] = user_phone  # Inject for logging

            # 3. Save to Memory (for follow-up questions)
            save_data = briefing.copy()
            save_data.update(
                {
                    "match": match_info,  # Ensure this stays a dict
                    "budget": budget,
                    "num_bets": num_bets,
                    "god_view": briefing,
                }
            )
            self.db.save_memory(user_phone, save_data)

            logger.info(f"🧠 Context saved for {user_phone}")

            # 4. The Closer speaks
            report = await orchestrator.format_the_closer_report(
                briefing, num_bets=num_bets
            )
            await self._send_multi(user_phone, report)

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
        Now uses the UNIFIED bet generation engine.
        """
        from core.generate_bets import generate_strategic_advice

        try:
            # Extract user phone from state if available, or use a default approach
            # In practice, this should be passed from handle_incoming_message
            # For now, we'll need to refactor to pass user_phone down
            # Temporary: Extract from the flow
            logger.warning(
                "⚠️ user_phone not available in current flow. Using unified engine requires phone."
            )

            # Use the unified engine with conversational mode
            answer = await generate_strategic_advice(
                user_phone=self._current_user_phone,  # Will need to be set in handle_incoming_message
                question=question,
            )
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
            reply = await query_llm(
                CONVERSATION_ASSISTANT_PROMPT, message, temperature=0.7
            )
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
            home = match.get("team_home", "").lower()
            away = match.get("team_away", "").lower()

            # Check if both teams match
            if team_b:
                if (team_a in home and team_b in away) or (
                    team_a in away and team_b in home
                ):
                    return {
                        "home_team": match.get("team_home"),
                        "away_team": match.get("team_away"),
                        "venue": match.get("venue"),
                        "date": match.get("date_iso"),
                    }
            else:
                # Single team - find their next match
                if team_a in home or team_a in away:
                    return {
                        "home_team": match.get("team_home"),
                        "away_team": match.get("team_away"),
                        "venue": match.get("venue"),
                        "date": match.get("date_iso"),
                    }

        return None

    async def _handle_schedule(self, from_number, msg_body, extracted_data=None):
        """Natural schedule responses."""
        low_msg = msg_body.lower()
        limit = extracted_data.get("limit") if extracted_data else None

        # 1. Determine the content (resp)
        if any(w in low_msg for w in ["full", "all", "week"]):
            resp = orchestrator.get_schedule_brief()
        elif limit:
            logger.info(f"📊 Custom schedule limit detected: {limit}")
            resp = orchestrator.get_schedule_menu(limit=limit)
        elif any(w in low_msg for w in ["menu", "list"]):
            resp = orchestrator.get_schedule_menu(limit=4)
        else:
            resp = orchestrator.get_next_match_content()

        # 2. deciding how to send it based on Mode
        # 2. deciding how to send it based on Mode
        if settings.get("GLOBAL_APP_CONFIG.app.interaction_mode") == "BUTTON_STRICT":
            # [INTERACTIVE LIST] Dynamic Schedule Menu
            # Fetch real upcoming matches to populate the list
            upcoming = orchestrator.get_upcoming_matches()[:8]  # Max 10 rows allow

            if upcoming:
                rows = []
                for m in upcoming:
                    # Row ID format: "Analyze {Home}" to trigger existing flow
                    row_id = f"Analyze {m['team_home']}"
                    rows.append(
                        {
                            "id": row_id[:200],  # ID limit
                            "title": f"{m['team_home']} vs {m['team_away']}"[
                                :24
                            ],  # Title max 24 chars
                            "description": f"{m['date_iso'][:10]} @ {m['venue']}"[:72],
                        }
                    )

                interactive_obj = {
                    "type": "list",
                    "header": {"type": "text", "text": "📅 Match Schedule"},
                    "body": {
                        "text": "Select a match below to launch the GoalMine Swarm:"
                    },
                    "footer": {"text": "GoalMine AI v2.0"},
                    "action": {
                        "button": "View Matches",
                        "sections": [{"title": "Upcoming Fixtures", "rows": rows}],
                    },
                }
                self.wa.send_interactive_message(from_number, interactive_obj)
            else:
                # Fallback if no games
                self.wa.send_message(
                    from_number, "No matches found in the immediate schedule."
                )
        else:
            self.wa.send_message(from_number, resp)

    async def _send_multi(self, to_number, text):
        """
        Sends long messages split by '# BET' as separate WhatsApp messages.
        This provides a cleaner, professional 'bet receipt' feel.
        """
        if not text:
            logger.warning(f"Attempted to send empty multi-part message to {to_number}")
            return

        logger.info(
            f"📤 Preparing to send multi-part message to {to_number} ({len(text)} chars)"
        )

        # Check if '# BET' is present
        if "# BET" in text:
            # Split by '# BET' but keep the delimiter for each segment
            # Pattern matches '# BET' followed by something, but we just use split and add it back
            parts = re.split(r"(?=# BET \d+)", text)

            for part in parts:
                clean_part = part.strip()
                if clean_part:
                    self.wa.send_message(to_number, clean_part)
                    # Tiny sleep to ensure message order in WhatsApp (sometimes they flip)
                    await asyncio.sleep(0.3)
        else:
            # Fallback for messages without BET headers
            self.wa.send_message(to_number, text)

    def _is_confirmation(self, text):
        """
        Detects confirmations like 'Yes', 'Do it', 'Go ahead'.
        Refined to avoid false positives on 'bet' or 'okay' in intent-rich sentences.
        """
        affirmations = [
            "yes", "yeah", "yep", "do it", "go", "sure", "ok", "okay",
            "run it", "let's go", "yup", "absolutely", "please", "confirm",
        ]
        text_lower = text.lower().strip()

        # Standalone "bet" or "okay" counts as confirmation
        if text_lower in ["bet", "okay", "ok", "yes", "yeah"]:
            return True

        # If the text is short (<= 3 words) and contains an affirmation
        words = text_lower.split()
        if len(words) <= 3 and any(w in words for w in affirmations):
            return True

        return False

    def _mentions_new_teams(self, text, current_match):
        """
        Check if user mentions different teams than the current match.
        Returns True if they're asking about a NEW match.
        """
        if not current_match:
            return False

        # Get current teams
        current_home = current_match.get("home_team", "").lower()
        current_away = current_match.get("away_team", "").lower()

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
