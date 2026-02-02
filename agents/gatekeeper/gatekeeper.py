import re
from core.log import get_logger
from core.initializer.llm import query_llm

logger = get_logger("Gatekeeper")

class Gatekeeper:
    """
    PERSONA: The Gatekeeper
    ROLE: Intent classification, entity extraction, and noise filtering.
    """
    
    @staticmethod
    async def classify_intent(message_body):
        """
        Classifies intent and extracts relevant data.
        
        Returns:
            tuple: (intent, extracted_data)
            - intent: "BETTING" | "SCHEDULE" | "CONV"
            - extracted_data: Dict with teams, budget, etc. or None
        """
        return await Gatekeeper._classify_async(message_body)

    @staticmethod
    async def _classify_async(message_body):
        # 1. Regex Logic (Cost saving)
        msg = message_body.lower().strip()
        
        # Numeric Menu Selection
        if msg in ["1", "2", "3", "4", "5"]:
            return "BETTING", {"selection": message_body}

        # Schedule / Next Match
        if any(w in msg for w in ["schedule", "squedule", "sqedule", "games", "today", "tomorrow", "next", "upcoming", "menu", "list", "when", "what time", "fixtures", "fixture", "who plays"]):
            # For schedule, try to extract a number (e.g. "next 5 matches")
            limit_match = re.search(r'(\d+)', msg)
            limit = int(limit_match.group(1)) if limit_match else None
            return "SCHEDULE", {"limit": limit}
            
        # Explicit Betting / Analysis (including standalone "analyze")
        if any(w in msg for w in [" vs ", " v ", "against", "odds", "bet", "staking", "budget"]) or msg in ["analyze", "analyse", "run it", "do it"]:
            # Extract match details immediately
            extracted = await Gatekeeper._extract_match_details(message_body)
            return "BETTING", extracted
            
        # "Analyze [Team]" or "Predict [Team]"
        if msg.startswith("analyze") or msg.startswith("analyse") or msg.startswith("predict"):
            extracted = await Gatekeeper._extract_match_details(message_body)
            return "BETTING", extracted
            
        # Conversation / Greetings
        if any(w in msg for w in ["hi", "hello", "hola", "sup", "hey", "start", "yo", "who are you", "what are you", "help"]):
            return "CONV", None

        # 2. FALLBACK: LLM for ambiguous queries
        from prompts.system_prompts import GATEKEEPER_INTENT_PROMPT
        
        try:
            category = await query_llm(GATEKEEPER_INTENT_PROMPT, f"User Input: {message_body}", config_key="gatekeeper", temperature=0.3)
            category = category.strip().upper()
            
            if "SCHEDULE" in category: 
                limit_match = re.search(r'(\d+)', msg)
                limit = int(limit_match.group(1)) if limit_match else None
                return "SCHEDULE", {"limit": limit}
            if "BETTING" in category:
                extracted = await Gatekeeper._extract_match_details(message_body)
                return "BETTING", extracted
            return "CONV", None
        except Exception as e:
            logger.warning(f"Gatekeeper LLM failed: {e}")
            return "CONV", None

    @staticmethod
    async def _extract_match_details(message_body):
        """
        Extracts team names, budget, and other betting parameters from text.
        
        Returns:
            dict: {
                'teams': ['Brazil', 'France'],
                'budget': 100,
                'num_bets': 1
            } or None
        """
        # Quick regex extraction for common patterns
        extracted = {}
        
        # Extract budget: "$100", "100 dollars", "budget 50"
        budget_match = re.search(r'\$(\d+)', message_body) or re.search(r'(\d+)\s*(?:dollars|bucks|budget)', message_body.lower())
        if budget_match:
            extracted['budget'] = int(budget_match.group(1))
        
        # Extract number of bets: "3 bets", "top 5 plays"
        num_bets_match = re.search(r'(\d+)\s*(?:bets?|plays?)', message_body.lower())
        if num_bets_match:
            extracted['num_bets'] = int(num_bets_match.group(1))
        
        # Extract teams using LLM for better accuracy
        from prompts.system_prompts import TEAM_EXTRACTION_PROMPT
        
        try:
            response = await query_llm(TEAM_EXTRACTION_PROMPT, message_body, json_mode=True, temperature=0.3)
            import json
            teams_data = json.loads(response)
            
            if teams_data.get('teams'):
                extracted['teams'] = teams_data['teams']
                logger.debug(f"Extracted teams: {extracted['teams']}")
        except Exception as e:
            logger.warning(f"Team extraction failed: {e}")
        
        return extracted if extracted else None
