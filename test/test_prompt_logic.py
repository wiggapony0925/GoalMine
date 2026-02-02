import unittest
import asyncio
import json
import logging
import os
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PromptLogicTest")

from agents.gatekeeper.gatekeeper import Gatekeeper
from services.orchestrator import extract_match_details_from_text, answer_follow_up_question
from services.conversation import ConversationHandler

class TestPromptLogic(unittest.IsolatedAsyncioTestCase):
    """
    Tests the 'IQ' of the prompts and the logic of the LLM components.
    """

    async def test_gatekeeper_intent_classification(self):
        """Test if Gatekeeper can distinguish complex intents."""
        scenarios = [
            ("When does Mexico play?", "SCHEDULE"),
            ("Analyze Brazil vs France", "BETTING"),
            ("How do I make a parlay?", "BETTING"), # Strategy counts as betting
            ("Hi there, who are you?", "CONV"),
            ("What's the weather like in Tokyo?", "CONV"), # Off-topic redirection
        ]
        
        for msg, expected in scenarios:
            intent, _ = await Gatekeeper.classify_intent(msg)
            logger.info(f"Input: '{msg}' -> Intent: {intent}")
            self.assertEqual(intent, expected)

    async def test_team_extraction_accuracy(self):
        """Test if the extraction prompt handles nicknames and abbreviations."""
        scenarios = [
            ("Mex vs SA", ["Mexico", "South Africa"]),
            ("The Aztecs against the Bafana Bafana", ["Mexico", "South Africa"]),
            ("USA v Brazil", ["USA", "Brazil"]),
            ("Predict the Arg game", ["Argentina"]),
        ]
        
        for msg, expected_teams in scenarios:
            data = await extract_match_details_from_text(msg)
            # Extracted data now has home_team/away_team
            found_teams = [data.get('home_team'), data.get('away_team')]
            # Clean None
            found_teams = [t for t in found_teams if t and t != "Name"]
            
            logger.info(f"Input: '{msg}' -> Found: {found_teams}")
            for expected in expected_teams:
                self.assertTrue(any(expected.lower() in t.lower() for t in found_teams), f"Failed to find {expected} in {found_teams}")

    async def test_follow_up_qa_logic(self):
        """Test if the follow-up assistant correctly uses God View data."""
        mock_memory = {
            "match": "Mexico vs South Africa",
            "tactics": {"team_a_xg": 1.55, "team_b_xg": 1.25, "tactical_analysis": "Mexico creative midfield."},
            "logistics": {"fatigue_score": 7, "risk": "Altitude"},
            "quant": {"probabilities": {"draw": 28.3}}
        }
        
        question = "What is the fatigue risk?"
        answer = await answer_follow_up_question(mock_memory, question)
        
        logger.info(f"Q: '{question}' -> A: {answer}")
        self.assertIn("7", answer)
        # Case-insensitive check
        self.assertIn("altitude", answer.lower())

    async def test_strategic_advisor_parlay(self):
        """Test if the strategic advisor can handle parlay advice."""
        mock_user_state = {
            "match": "Mexico vs South Africa",
            "quant": {
                "top_plays": [
                    {"market": "Draw", "odds": 4.2, "edge_percent": 19.02}
                ]
            }
        }
        
        handler = ConversationHandler(MagicMock())
        question = "Should I parlay the draw with a Mexico win?"
        
        answer = await handler._strategic_betting_advisor(mock_user_state, question)
        
        logger.info(f"Q: '{question}' -> A: {answer}")
        # The answer should be analytical
        self.assertTrue(len(answer) > 20)
        self.assertIn("*", answer) # WhatsApp bolding check

    async def test_off_topic_graceful_denial(self):
        """Ensure the bot doesn't answer non-football questions."""
        handler = ConversationHandler(MagicMock())
        msg = "How do I fix a leaky faucet?"
        
        # Intent should be CONV
        intent, _ = await Gatekeeper.classify_intent(msg)
        self.assertEqual(intent, "CONV")
        
        # Response should be a polite decline
        reply = await handler._handle_general_conversation(msg)
        logger.info(f"Off-topic denial: {reply}")
        self.assertTrue(any(word in reply.lower() for word in ["football", "betting", "world cup", "sorry", "cannot", "don't", "match", "help"]))

if __name__ == "__main__":
    unittest.main()
