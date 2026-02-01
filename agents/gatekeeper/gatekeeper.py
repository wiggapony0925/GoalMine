import os
import logging
import asyncio
from core.llm import query_llm

logger = logging.getLogger(__name__)

class Gatekeeper:
    """
    PERSONA: The Gatekeeper
    ROLE: Intent classification and noise filtering.
    """
    
    @staticmethod
    def classify_intent(message_body):
        return asyncio.run(Gatekeeper._classify_async(message_body))

    @staticmethod
    async def _classify_async(message_body):
        system_prompt = """
        You are a Firewall AI for a World Cup Betting Engine.
        Global Rule: You ONLY authorize content related to Football (Soccer), Betting, Odds, or Match Schedules.
        
        STRICTLY CLASSIFY INPUT INTO ONE OF 3 CATEGORIES:
        
        1. "BETTING": 
           - Users asking for match analysis ("Analyze France vs Brazil").
           - Users asking for odds, predictions, or lineups.
           - Users replying with menu numbers ("1", "2").
           
        2. "CHIT_CHAT":
           - Simple greetings ("Hi", "Hello", "Thanks").
           
        3. "OFF_TOPIC":
           - ANY request about cooking, recipes, coding, politics, weather (non-match), history, or general knowledge.
           - Example: "How do I bake a cake?" -> OFF_TOPIC
           - Example: "Write me a python script" -> OFF_TOPIC
        
        OUTPUT ONLY THE CATEGORY NAME (BETTING, CHIT_CHAT, OFF_TOPIC).
        """
        
        try:
            category = await query_llm(system_prompt, f"User Input: {message_body}", temperature=0.0)
            category = category.strip().upper().replace(".", "")
            
            if "BETTING" in category: return "BETTING", message_body
            if "CHIT" in category: return "CHIT_CHAT", None
            if "OFF" in category: return "OFF_TOPIC", None
            
            return "CHIT_CHAT", None
        except Exception:
            return "BETTING", message_body

    @staticmethod
    def get_response(intent):
        if intent == "CHIT_CHAT":
            return "Ready to win? Tell me a match (e.g., 'France vs Brazil') or ask for the schedule."
        elif intent == "OFF_TOPIC":
            return "I focus only on World Cup alpha. Let's get back to business."
        return None
