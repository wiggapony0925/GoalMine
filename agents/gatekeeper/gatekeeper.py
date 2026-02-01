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
        You are a Firewall AI.
        Classify the user's message into exactly one category:
        1. BETTING: User wants analysis, odds, predictions, schedule, or match info.
        2. CHIT_CHAT: Greetings, thanks, or small talk.
        3. OFF_TOPIC: Politics, coding, weather (unrelated to football), jokes.
        
        OUTPUT ONLY THE CATEGORY NAME.
        """
        
        try:
            category = await query_llm(system_prompt, f"User Input: {message_body}", temperature=0.1)
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
