# ruff: noqa: E402
import unittest
import logging
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PromptLogicTest")

from agents.gatekeeper.gatekeeper import Gatekeeper
from services import GoalMineHandler


class TestPromptLogic(unittest.IsolatedAsyncioTestCase):
    """
    Tests the 'IQ' of the prompts and the logic of the LLM components.
    """

    async def test_gatekeeper_intent_classification(self):
        """Test if Gatekeeper can distinguish complex intents."""
        scenarios = [
            ("When does Mexico play?", "SCHEDULE"),
            ("Analyze Brazil vs France", "BETTING"),
            ("How do I make a parlay?", "SCHEDULE"),  # Fallback -> Schedule
            ("Hi there, who are you?", "SCHEDULE"), # Chatter -> Schedule/Browser
            ("What's the weather like in Tokyo?", "SCHEDULE"),  # Off-topic -> Schedule/Browser
        ]

        for msg, expected in scenarios:
            intent, _ = await Gatekeeper.classify_intent(msg)
            logger.info(f"Input: '{msg}' -> Intent: {intent}")
            self.assertEqual(intent, expected)

    @patch("services.interface.message_handler.generate_strategic_advice")
    async def test_strategic_advisor_parlay(self, mock_advice):
        """Test if the strategic advisor can handle parlay advice."""
        mock_advice.return_value = "*Strategic Advice:* Consider a parlay..."
        mock_user_state = {
            "match": "Mexico vs South Africa",
            "quant": {
                "top_plays": [{"market": "Draw", "odds": 4.2, "edge_percent": 19.02}]
            },
        }

        handler = GoalMineHandler(MagicMock(), MagicMock())
        question = "Should I parlay the draw with a Mexico win?"

        answer = await handler._strategic_betting_advisor(mock_user_state, question, "12345")

        logger.info(f"Q: '{question}' -> A: {answer}")
        # The answer should be analytical
        self.assertTrue(len(answer) > 10)
        self.assertIn("*", answer)  # WhatsApp bolding check



if __name__ == "__main__":
    unittest.main()
