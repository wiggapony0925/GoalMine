import os
import logging

logger = logging.getLogger(__name__)

# Fallback for simple keyword matching if OpenAI is not available/configured
CHIT_CHAT_KEYWORDS = ["hello", "hi", "hey", "thanks", "thank you", "good morning", "good evening", "goodbye"]
OFF_TOPIC_KEYWORDS = ["poem", "joke", "recipe", "code", "weather", "politics"]
BETTING_KEYWORDS = ["bet", "predict", "game", "match", "odds", "value", "won", "score", "schedule", "today", "tomorrow"]

class Gatekeeper:
    """
    PERSONA: The Gatekeeper
    ROLE: Intent classification and noise filtering.
    """
    
    @staticmethod
    def classify_intent(message_body):
        """
        Classifies the intent of the incoming message.
        Returns: 
           - 'BETTING': Proceed to Agent Swarm
           - 'CHIT_CHAT': Static friendly reply
           - 'OFF_TOPIC': Strict refusal
        """
        msg = message_body.lower().strip()
        
        # 1. Check for specific commands first
        if msg in ["1", "2", "analyze all"]:
            return "BETTING", None # Context implies a follow-up to Push

        # 2. Check Betting Intent (Prioritized)
        for word in BETTING_KEYWORDS:
            if word in msg:
                # Basic Entity Extraction (Simplified)
                # In a real app with LLM, we would extract "France", "Brazil", etc.
                return "BETTING", msg 

        # 3. Check Off Topic
        for word in OFF_TOPIC_KEYWORDS:
            if word in msg:
                return "OFF_TOPIC", None
                
        # 4. Check Chit Chat
        for word in CHIT_CHAT_KEYWORDS:
            if word in msg:
                return "CHIT_CHAT", None
        
        # Default to CHIT_CHAT or HELP if unsure
        return "CHIT_CHAT", None

    @staticmethod
    def get_response(intent):
        if intent == "CHIT_CHAT":
            return "Ready to win? Tell me a match or ask for the daily schedule."
        elif intent == "OFF_TOPIC":
            return "I focus only on World Cup alpha. Let's get back to business."
        return None
