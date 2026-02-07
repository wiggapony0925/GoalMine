# ruff: noqa: E402
import unittest
from unittest.mock import patch, AsyncMock
from dotenv import load_dotenv

load_dotenv()

# Import Agents directly
from agents.gatekeeper.gatekeeper import Gatekeeper
from agents.tactics.tactics import TacticsAgent
from agents.market.market import MarketAgent


class TestGoalMineSystem(unittest.IsolatedAsyncioTestCase):
    # --- 1. GATEKEEPER TESTS ---
    async def test_gatekeeper_off_topic(self):
        """Test handling of non-betting prompts (Cooking/Coding)"""
        print("\n🔒 Testing Gatekeeper Firewall...")

        # We mock the internal Async classification strictly for the return value
        # But in a real Integration Test, this hits the LLM.
        # For unit testing speed, we assume the LLM works (tested via Prompt Engineering).
        # We manually verify the Logic flow.

        # Simulate LLM returning 'OFF_TOPIC' for "Bake a cake"
        with patch(
            "agents.gatekeeper.gatekeeper.query_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = "OFF_TOPIC"

            intent, _ = await Gatekeeper.classify_intent(
                "How do I bake a chocolate cake?"
            )
            # Strict mode: Off-topic -> SCHEDULE (Browser/Menu)
            self.assertEqual(intent, "SCHEDULE")
            print("✅ Gatekeeper correctly routed 'Cooking' request to SCHEDULE.")

    async def test_gatekeeper_betting(self):
        # The prompt "Analyze France vs USA" hits the regex, so it skips classification LLM
        # and goes straight to extraction LLM. We must mock the JSON response.
        with patch(
            "agents.gatekeeper.gatekeeper.query_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = '{"teams": ["France", "USA"]}'

            intent, extracted = await Gatekeeper.classify_intent(
                "Analyze France vs USA"
            )
            self.assertEqual(intent, "BETTING")
            self.assertEqual(extracted["teams"], ["France", "USA"])
            print("✅ Gatekeeper allowed 'Betting' request.")

    # --- 3. AGENT FALLBACKS (Unit Level) ---
    async def test_market_agent_fallback(self):
        """Test Market Agent handles API failure gracefully"""
        print("\n📉 Testing Market Agent Fallback...")
        agent = MarketAgent()

        # Force API Exception
        with patch(
            "agents.market.market.fetch_latest_odds", side_effect=Exception("API Down")
        ):
            with patch(
                "agents.market.market.query_llm", new_callable=AsyncMock
            ) as mock_llm:
                mock_llm.return_value = "Estimated Odds: France -150"

                res = await agent.analyze("France", "USA")
                self.assertEqual(res["data_source"], "VEGAS_ESTIMATOR_FALLBACK")
                print("✅ Market Agent switched to FALLBACK on API failure.")

    async def test_tactics_agent_live_awareness(self):
        """Test Tactics Agent identifies Half-Time context"""
        print("\n♟️ Testing Tactics Agent Live Logic...")
        agent = TacticsAgent()

        # Mocking the LLM response to confirm it sees the context
        with patch(
            "agents.tactics.tactics.query_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = '{"tactical_logic": "HT game state detected.", "ht_recommendation": "Bet Over"}'

            # We bypass the API call mock for this logic test and pass mock data directly if method allowed
            # Since analyze() calls API internally, we mock the API function
            mock_api_data = {
                "name": "France",
                "live_status": "HT",
                "minute": 45,
                "current_score": "0-1",
                "roster_sample": [],
                "recent_form": [],
            }

            with patch(
                "agents.tactics.tactics.fetch_team_stats", return_value=mock_api_data
            ):
                res = await agent.analyze("France", "Spain")
                self.assertIn("HT", res["tactical_analysis"])
                print("✅ Tactics Agent acknowledged Half-Time context.")


if __name__ == "__main__":
    unittest.main()
