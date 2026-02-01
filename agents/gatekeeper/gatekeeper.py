import re
import random

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
        # 1. COST SAVING: Regex Logic First (0ms, $0)
        msg = message_body.lower().strip()
        
        # Numeric Menu Selection
        if msg in ["1", "2", "3", "4", "5"]:
            return "BETTING", message_body

        # Schedule / Next Match
        if any(w in msg for w in ["schedule", "games", "today", "tomorrow", "next", "upcoming", "menu"]):
            return "SCHEDULE", None
            
        # Explicit Betting / Analysis (Detects "Team A vs Team B")
        if any(w in msg for w in [" vs ", " v ", "against", "analyze", "predict", "odds", "bet"]):
            return "BETTING", message_body
            
        # Chit Chat
        if any(w in msg for w in ["hi", "hello", "hola", "sup", "hey", "start", "yo"]):
            return "CHIT_CHAT", None

        # 2. FALLBACK: LLM for ambiguous queries (Cost incurred)
        system_prompt = """
        You are a Firewall AI for a World Cup Betting Engine.
        Global Rule: You ONLY authorize content related to Football (Soccer), Betting, Odds, or Match Schedules.
        
        STRICTLY CLASSIFY INPUT INTO ONE OF 4 CATEGORIES:
        
        1. "BETTING": 
           - Users asking for analysis ("Analyze France vs Brazil").
           - Users replying with numeric menu selections ("1", "2").
           
        2. "SCHEDULE":
           - Users asking "What's the schedule?", "Who plays today?".
           
        3. "CHIT_CHAT":
           - Simple greetings ("Hi", "Hello", "Hola").
           
        4. "OFF_TOPIC":
           - ANY request about cooking, recipes, coding, politics.
        
        OUTPUT ONLY THE CATEGORY NAME.
        """
        
        try:
            category = await query_llm(system_prompt, f"User Input: {message_body}", temperature=0.0)
            category = category.strip().upper().replace(".", "")
            
            if "SCHEDULE" in category: return "SCHEDULE", None
            if "BETTING" in category: return "BETTING", message_body
            if "CHIT" in category: return "CHIT_CHAT", None
            if "OFF" in category: return "OFF_TOPIC", None
            
            return "CHIT_CHAT", None
        except Exception:
            # Default safe fallback
            return "BETTING", message_body

    @staticmethod
    def get_response(intent):
        if intent == "CHIT_CHAT":
            greetings = [
                "👋 **GoalMine AI Online**\nReady to find an edge? Ask for the 'Schedule' or a specific match like 'France vs Brazil'.",
                "🤖 **System Ready.**\nI analyze World Cup data for alpha. What match are we targeting?",
                "🧠 **GoalMine Active.**\nThe swarm is standing by. Usage:\n- 'Schedule': See games\n- 'Analyze [Team]': Get report"
            ]
            return random.choice(greetings)
            
        elif intent == "OFF_TOPIC":
            errors = [
                "⚠️ I am strictly programmed for World Cup analysis. Please stick to football.",
                "🚫 **Out of Scope.**\nI handle Odds, Data, and Match Logic only.",
                "🤖 My algorithms are focused on the pitch. Ask me about the World Cup."
            ]
            return random.choice(errors)
        return None
