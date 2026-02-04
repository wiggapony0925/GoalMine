# ruff: noqa: E402
import unittest
import logging
from unittest.mock import MagicMock
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PromptLogicTest")

from agents.gatekeeper.gatekeeper import Gatekeeper
from services import ConversationHandler


class TestPromptLogic(unittest.IsolatedAsyncioTestCase):
    """
    Tests the 'IQ' of the prompts and the logic of the LLM components.
    """

    async def test_gatekeeper_intent_classification(self):
        """Test if Gatekeeper can distinguish complex intents."""
        scenarios = [
            ("When does Mexico play?", "SCHEDULE"),
            ("Analyze Brazil vs France", "BETTING"),
            ("How do I make a parlay?", "BETTING"),  # Strategy counts as betting
            ("Hi there, who are you?", "CONV"),
            ("What's the weather like in Tokyo?", "CONV"),  # Off-topic redirection
        ]

        for msg, expected in scenarios:
            intent, _ = await Gatekeeper.classify_intent(msg)
            logger.info(f"Input: '{msg}' -> Intent: {intent}")
            self.assertEqual(intent, expected)

    async def test_strategic_advisor_parlay(self):
        """Test if the strategic advisor can handle parlay advice."""
        mock_user_state = {
            "match": "Mexico vs South Africa",
            "quant": {
                "top_plays": [{"market": "Draw", "odds": 4.2, "edge_percent": 19.02}]
            },
        }

        handler = ConversationHandler(MagicMock())
        question = "Should I parlay the draw with a Mexico win?"

        answer = await handler._strategic_betting_advisor(mock_user_state, question)

        logger.info(f"Q: '{question}' -> A: {answer}")
        # The answer should be analytical
        self.assertTrue(len(answer) > 20)
        self.assertIn("*", answer)  # WhatsApp bolding check

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
        self.assertTrue(
            any(
                word in reply.lower()
                for word in [
                    "football",
                    "betting",
                    "world cup",
                    "sorry",
                    "cannot",
                    "don't",
                    "match",
                    "help",
                ]
            )
        )


if __name__ == "__main__":
    unittest.main()
