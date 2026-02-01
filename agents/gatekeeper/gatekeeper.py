import re
import random

from core.llm import query_llm

class Gatekeeper:
    """
    PERSONA: The Gatekeeper
    ROLE: Intent classification and noise filtering.
    """
    
    @staticmethod
    async def classify_intent(message_body):
        return await Gatekeeper._classify_async(message_body)

    @staticmethod
    async def _classify_async(message_body):
        # 1. Regex Logic (Cost saving)
        msg = message_body.lower().strip()
        
        # Numeric Menu Selection
        if msg in ["1", "2", "3", "4", "5"]:
            return "BETTING", message_body

        # Schedule / Next Match
        if any(w in msg for w in ["schedule", "games", "today", "tomorrow", "next", "upcoming", "menu", "list"]):
            return "SCHEDULE", None
            
        # Explicit Betting / Analysis
        if any(w in msg for w in [" vs ", " v ", "against", "analyze", "predict", "odds", "bet", "staking", "budget"]):
            return "BETTING", message_body
            
        # Conversation / Greetings
        if any(w in msg for w in ["hi", "hello", "hola", "sup", "hey", "start", "yo", "who are you", "what are you"]):
            return "CONV", None

        # 2. FALLBACK: LLM for ambiguous queries
        system_prompt = """
        # IDENTITY: GoalMine Security Firewall (Gatekeeper AI)
        
        # MISSION
        You are the first line of defense for a high-frequency World Cup Betting Engine. Your sole priority is to classify incoming user packets into one of three operational channels.

        # OPERATIONAL CHANNELS:
        1. **BETTING**: Requests for match analysis, specific odds, staking advice, or "$X on Team A" style queries.
        2. **SCHEDULE**: Inquiries about kickoff times, dates, group standings, or game lists ("Who plays today?").
        3. **CONV**: Human-like greetings, general World Cup history, bot capability questions, or non-actionable chatter.

        # CLASSIFICATION LOGIC:
        - If the packet mentions TWO TEAMS and a request for insight -> **BETTING**.
        - If the packet asks about TIME or LISTS -> **SCHEDULE**.
        - If the packet is VAGUE or GREETING-based -> **CONV**.
        - **OFF-TOPIC POLICY**: If a packet is non-football or non-betting related, force-classify as **CONV** for graceful redirection.

        # OUTPUT STRICTION
        - OUTPUT ONLY THE CHANNEL NAME (e.g., BETTING).
        - ZERO NARRATIVE. ZERO EXPLANATION.
        """
        
        try:
            category = await query_llm(system_prompt, f"User Input: {message_body}", config_key="gatekeeper")
            category = category.strip().upper()
            
            if "SCHEDULE" in category: return "SCHEDULE", None
            if "BETTING" in category: return "BETTING", message_body
            return "CONV", None
        except Exception:
            return "CONV", None
